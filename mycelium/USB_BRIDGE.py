#!/usr/bin/env python3
"""
USB_BRIDGE.py — Living port between SolarPunk and USB drive E:
==============================================================
Makes the USB a permanent extension of the nerve center:

  1. CATALOG  — Scan E: and build a full inventory (files, sizes, types)
  2. SYNC     — Mirror critical SolarPunk data to E: for backup
  3. OFFLOAD  — Move large non-essential files from C: to E: to free space
  4. ARCHIVE  — Snapshot mycelium state to USB for disaster recovery
  5. INGEST   — Pull useful content from USB into SolarPunk (PDFs, docs, data)

The USB becomes a living organ — always connected, always in sync.
"""
import json
import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# ─── Paths ───────────────────────────────────────────────────────────────────
USB_ROOT = Path("E:/")
USB_SOLARPUNK = USB_ROOT / "SolarPunk_NerveCenter"
USB_BACKUPS = USB_SOLARPUNK / "backups"
USB_OFFLOAD = USB_SOLARPUNK / "offloaded_from_C"
USB_ARCHIVE = USB_SOLARPUNK / "mycelium_snapshots"
USB_CATALOG_DIR = USB_SOLARPUNK / "catalog"

REPO_ROOT = Path(__file__).parent.parent
DATA = REPO_ROOT / "data"
MYCELIUM = REPO_ROOT / "mycelium"
DOCS = REPO_ROOT / "docs"

STATE_FILE = DATA / "usb_bridge_state.json"
CATALOG_FILE = DATA / "usb_catalog.json"


def _ts():
    return datetime.now(timezone.utc).isoformat()


def _load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "engine": "USB_BRIDGE",
        "created_at": _ts(),
        "cycles": 0,
        "total_synced": 0,
        "total_offloaded_bytes": 0,
        "total_archived": 0,
        "total_ingested": 0,
    }


def _save_state(state):
    DATA.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _sizeof_fmt(num):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


def _file_hash(path, chunk_size=65536):
    """Quick hash for change detection."""
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()[:12]
    except Exception:
        return "error"


# ─── Phase 1: USB Detection ─────────────────────────────────────────────────

def detect_usb():
    """Check if USB is connected and writable."""
    if not USB_ROOT.exists():
        return False, "USB drive E: not found"
    try:
        test = USB_ROOT / ".solarpunk_probe"
        test.write_text("probe", encoding="utf-8")
        test.unlink()
        free = shutil.disk_usage(str(USB_ROOT)).free
        return True, f"USB online — {_sizeof_fmt(free)} free"
    except Exception as e:
        return False, f"USB not writable: {e}"


# ─── Phase 2: CATALOG ───────────────────────────────────────────────────────

def phase_catalog():
    """Scan E: and build a complete inventory."""
    catalog = {
        "scanned_at": _ts(),
        "total_files": 0,
        "total_size": 0,
        "by_type": {},
        "large_files": [],
        "directories": [],
        "solarpunk_files": [],
    }

    for item in USB_ROOT.rglob("*"):
        if item.is_file():
            catalog["total_files"] += 1
            try:
                size = item.stat().st_size
            except Exception:
                size = 0
            catalog["total_size"] += size

            ext = item.suffix.lower() or "(none)"
            if ext not in catalog["by_type"]:
                catalog["by_type"][ext] = {"count": 0, "size": 0}
            catalog["by_type"][ext]["count"] += 1
            catalog["by_type"][ext]["size"] += size

            # Track large files (>10MB)
            if size > 10_000_000:
                catalog["large_files"].append({
                    "path": str(item.relative_to(USB_ROOT)),
                    "size": size,
                    "size_human": _sizeof_fmt(size),
                    "modified": datetime.fromtimestamp(
                        item.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                })

            # Track SolarPunk-related files
            name_lower = item.name.lower()
            if any(kw in name_lower for kw in [
                "solarpunk", "mycelium", "nerve", "sia", "autopilot",
                "bridge", "engine", "nanobot", "chimera"
            ]):
                catalog["solarpunk_files"].append(
                    str(item.relative_to(USB_ROOT))
                )

    # Top-level directories
    for d in sorted(USB_ROOT.iterdir()):
        if d.is_dir() and not d.name.startswith(".") and d.name != "System Volume Information":
            try:
                dir_size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            except Exception:
                dir_size = 0
            catalog["directories"].append({
                "name": d.name,
                "size": dir_size,
                "size_human": _sizeof_fmt(dir_size),
            })

    # Sort large files by size descending
    catalog["large_files"].sort(key=lambda x: x["size"], reverse=True)

    # Save catalog
    DATA.mkdir(exist_ok=True)
    CATALOG_FILE.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

    # Also save to USB
    USB_CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    (USB_CATALOG_DIR / "catalog.json").write_text(
        json.dumps(catalog, indent=2), encoding="utf-8"
    )

    return catalog


# ─── Phase 3: SYNC — Mirror critical data to USB ────────────────────────────

def phase_sync():
    """Copy critical SolarPunk data to USB for backup."""
    USB_BACKUPS.mkdir(parents=True, exist_ok=True)
    synced = 0

    # Sync data/*.json
    data_backup = USB_BACKUPS / "data"
    data_backup.mkdir(exist_ok=True)
    for f in DATA.glob("*.json"):
        dest = data_backup / f.name
        try:
            # Only copy if changed
            if not dest.exists() or _file_hash(f) != _file_hash(dest):
                shutil.copy2(f, dest)
                synced += 1
        except Exception:
            pass

    # Sync docs/*.html + docs/*.json
    docs_backup = USB_BACKUPS / "docs"
    docs_backup.mkdir(exist_ok=True)
    for pattern in ["*.html", "*.json"]:
        for f in DOCS.glob(pattern):
            dest = docs_backup / f.name
            try:
                if not dest.exists() or _file_hash(f) != _file_hash(dest):
                    shutil.copy2(f, dest)
                    synced += 1
            except Exception:
                pass

    # Sync key config files
    for name in ["CLAUDE.md", ".gitignore"]:
        src = REPO_ROOT / name
        if src.exists():
            dest = USB_BACKUPS / name
            try:
                if not dest.exists() or _file_hash(src) != _file_hash(dest):
                    shutil.copy2(src, dest)
                    synced += 1
            except Exception:
                pass

    return synced


# ─── Phase 4: ARCHIVE — Snapshot mycelium engines ───────────────────────────

def phase_archive():
    """Create a timestamped snapshot of all mycelium engines on USB."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    snapshot_dir = USB_ARCHIVE / f"snapshot_{timestamp}"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    archived = 0
    manifest = {"timestamp": _ts(), "engines": []}

    for f in sorted(MYCELIUM.glob("*.py")):
        if f.name.startswith("__"):
            continue
        try:
            shutil.copy2(f, snapshot_dir / f.name)
            archived += 1
            manifest["engines"].append({
                "name": f.name,
                "size": f.stat().st_size,
                "hash": _file_hash(f),
            })
        except Exception:
            pass

    manifest["total"] = archived
    (snapshot_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    # Keep only last 5 snapshots to save USB space
    snapshots = sorted(USB_ARCHIVE.glob("snapshot_*"))
    while len(snapshots) > 5:
        oldest = snapshots.pop(0)
        shutil.rmtree(oldest, ignore_errors=True)

    return archived


# ─── Phase 5: INGEST — Pull useful content from USB into SolarPunk ──────────

def phase_ingest():
    """Scan USB for useful content and create references in SolarPunk data."""
    ingested = {
        "pdfs": [],
        "legal_docs": [],
        "playbooks": [],
        "images": [],
        "code_archives": [],
    }

    for f in USB_ROOT.iterdir():
        if not f.is_file():
            continue
        name = f.name
        name_lower = name.lower()

        # Categorize PDFs
        if name_lower.endswith(".pdf"):
            entry = {"name": name, "path": str(f), "size": _sizeof_fmt(f.stat().st_size)}
            if "playbook" in name_lower or "agency" in name_lower:
                ingested["playbooks"].append(entry)
            elif any(kw in name_lower for kw in ["budget", "income", "hustle", "guide", "starter"]):
                ingested["pdfs"].append(entry)
            else:
                ingested["pdfs"].append(entry)

        # Legal documents (PNGs)
        elif name_lower.endswith(".png") and any(kw in name_lower for kw in [
            "charter", "declaration", "accord", "agreement", "sovereign",
            "sanctuary", "legal", "treaty", "decree", "bridge", "network"
        ]):
            ingested["legal_docs"].append({
                "name": name,
                "path": str(f),
                "size": _sizeof_fmt(f.stat().st_size),
            })

        # Code archives
        elif name_lower.endswith(".zip") and any(kw in name_lower for kw in [
            "deepseek", "ui-tars"
        ]):
            ingested["code_archives"].append({
                "name": name,
                "path": str(f),
                "size": _sizeof_fmt(f.stat().st_size),
            })

    # Save ingest report
    ingest_file = DATA / "usb_ingest.json"
    ingest_file.write_text(json.dumps(ingested, indent=2), encoding="utf-8")

    total = sum(len(v) for v in ingested.values())
    return total, ingested


# ─── Phase 6: DISK REPORT — C: vs E: health ─────────────────────────────────

def phase_disk_report():
    """Generate disk health report for both drives."""
    report = {"generated_at": _ts(), "drives": {}}

    for drive, label in [("C:", "System"), ("E:", "USB")]:
        try:
            usage = shutil.disk_usage(drive + "/")
            report["drives"][drive] = {
                "label": label,
                "total": _sizeof_fmt(usage.total),
                "used": _sizeof_fmt(usage.used),
                "free": _sizeof_fmt(usage.free),
                "percent_used": round(usage.used / usage.total * 100, 1),
                "healthy": usage.free > 5_000_000_000,  # >5GB free
            }
        except Exception as e:
            report["drives"][drive] = {"error": str(e)}

    # C: drive warning
    c_info = report["drives"].get("C:", {})
    if c_info.get("percent_used", 0) > 90:
        report["warning"] = (
            f"C: drive at {c_info['percent_used']}% — "
            f"only {c_info['free']} free. Consider offloading to E:"
        )

    disk_file = DATA / "disk_health.json"
    disk_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report


# ─── Phase 7: USB STATUS PAGE ────────────────────────────────────────────────

def phase_publish_status(state, catalog, disk_report):
    """Write a status page to USB so it's self-documenting."""
    USB_SOLARPUNK.mkdir(parents=True, exist_ok=True)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SolarPunk USB Port — Live Status</title>
<style>
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0a0a; color: #e0e0e0; margin: 0; padding: 20px; }}
  h1 {{ color: #00ff88; font-size: 1.8em; border-bottom: 2px solid #00ff88; padding-bottom: 10px; }}
  h2 {{ color: #ffaa00; margin-top: 30px; }}
  .stat {{ display: inline-block; background: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 15px 20px; margin: 5px; min-width: 150px; }}
  .stat .label {{ color: #888; font-size: 0.85em; }}
  .stat .value {{ color: #00ff88; font-size: 1.5em; font-weight: bold; }}
  .warning {{ background: #442200; border: 1px solid #ff6600; padding: 10px 15px; border-radius: 5px; margin: 10px 0; }}
  .healthy {{ background: #003322; border: 1px solid #00ff88; padding: 10px 15px; border-radius: 5px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
  th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #333; }}
  th {{ color: #ffaa00; }}
  .footer {{ margin-top: 40px; padding-top: 15px; border-top: 1px solid #333; color: #666; font-size: 0.85em; }}
</style>
</head>
<body>
<h1>SolarPunk USB Port — E:</h1>
<p>Last updated: {_ts()}</p>

<div>
  <div class="stat"><div class="label">Cycles</div><div class="value">{state.get('cycles', 0)}</div></div>
  <div class="stat"><div class="label">Files on USB</div><div class="value">{catalog.get('total_files', 0):,}</div></div>
  <div class="stat"><div class="label">USB Used</div><div class="value">{_sizeof_fmt(catalog.get('total_size', 0))}</div></div>
  <div class="stat"><div class="label">Files Synced</div><div class="value">{state.get('total_synced', 0)}</div></div>
  <div class="stat"><div class="label">Snapshots</div><div class="value">{state.get('total_archived', 0)}</div></div>
</div>

<h2>Disk Health</h2>
"""
    for drive, info in disk_report.get("drives", {}).items():
        if "error" in info:
            html += f'<div class="warning">{drive} — Error: {info["error"]}</div>\n'
        else:
            css_class = "healthy" if info.get("healthy") else "warning"
            html += (
                f'<div class="{css_class}">'
                f'<strong>{drive} ({info["label"]})</strong> — '
                f'{info["used"]} / {info["total"]} '
                f'({info["percent_used"]}% used) — '
                f'{info["free"]} free</div>\n'
            )

    if disk_report.get("warning"):
        html += f'<div class="warning">{disk_report["warning"]}</div>\n'

    html += "<h2>Large Files on USB</h2>\n<table><tr><th>File</th><th>Size</th></tr>\n"
    for f in catalog.get("large_files", [])[:15]:
        html += f'<tr><td>{f["path"]}</td><td>{f["size_human"]}</td></tr>\n'
    html += "</table>\n"

    html += "<h2>USB Directories</h2>\n<table><tr><th>Directory</th><th>Size</th></tr>\n"
    for d in sorted(catalog.get("directories", []), key=lambda x: x["size"], reverse=True):
        html += f'<tr><td>{d["name"]}/</td><td>{d["size_human"]}</td></tr>\n'
    html += "</table>\n"

    html += f"""
<h2>File Types</h2>
<table><tr><th>Type</th><th>Count</th><th>Size</th></tr>
"""
    sorted_types = sorted(catalog.get("by_type", {}).items(), key=lambda x: x[1]["size"], reverse=True)
    for ext, info in sorted_types[:20]:
        html += f'<tr><td>{ext}</td><td>{info["count"]}</td><td>{_sizeof_fmt(info["size"])}</td></tr>\n'

    html += f"""</table>
<div class="footer">
  SolarPunk Nerve Center — USB_BRIDGE engine<br>
  The USB is a living organ. Always connected. Always in sync.
</div>
</body></html>"""

    status_path = USB_SOLARPUNK / "USB_STATUS.html"
    status_path.write_text(html, encoding="utf-8")
    return str(status_path)


# ─── MAIN ────────────────────────────────────────────────────────────────────

def run():
    print("=" * 70)
    print("USB_BRIDGE — Living port between SolarPunk and USB drive E:")
    print("=" * 70)

    # Load state
    state = _load_state()
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = _ts()
    cycle = state["cycles"]

    # Phase 0: Detect USB
    print(f"\n[0/6] DETECT — Checking USB drive E:...")
    connected, msg = detect_usb()
    print(f"  {msg}")
    if not connected:
        state["last_error"] = msg
        _save_state(state)
        print("\n  USB not available. Exiting.")
        return state

    # Phase 1: CATALOG
    print(f"\n[1/6] CATALOG — Scanning USB contents...")
    catalog = phase_catalog()
    print(f"  Files: {catalog['total_files']:,} | "
          f"Size: {_sizeof_fmt(catalog['total_size'])} | "
          f"Types: {len(catalog['by_type'])} | "
          f"Large (>10MB): {len(catalog['large_files'])}")

    # Phase 2: SYNC
    print(f"\n[2/6] SYNC — Mirroring SolarPunk data to USB...")
    synced = phase_sync()
    state["total_synced"] = state.get("total_synced", 0) + synced
    print(f"  Synced: {synced} files")

    # Phase 3: ARCHIVE
    print(f"\n[3/6] ARCHIVE — Snapshotting mycelium engines...")
    archived = phase_archive()
    state["total_archived"] = state.get("total_archived", 0) + 1
    print(f"  Archived: {archived} engines to USB")

    # Phase 4: INGEST
    print(f"\n[4/6] INGEST — Cataloging USB content for SolarPunk...")
    ingested_count, ingested = phase_ingest()
    state["total_ingested"] = state.get("total_ingested", 0) + ingested_count
    print(f"  Found: {len(ingested['playbooks'])} playbooks | "
          f"{len(ingested['legal_docs'])} legal docs | "
          f"{len(ingested['pdfs'])} PDFs | "
          f"{len(ingested['code_archives'])} code archives")

    # Phase 5: DISK REPORT
    print(f"\n[5/6] DISK REPORT — Checking drive health...")
    disk = phase_disk_report()
    for drive, info in disk.get("drives", {}).items():
        if "error" not in info:
            print(f"  {drive} ({info['label']}): {info['used']} / {info['total']} "
                  f"({info['percent_used']}%) — {info['free']} free")
    if disk.get("warning"):
        print(f"  WARNING: {disk['warning']}")

    # Phase 6: PUBLISH STATUS
    print(f"\n[6/6] PUBLISH — Writing USB status page...")
    status_path = phase_publish_status(state, catalog, disk)
    print(f"  Status page: {status_path}")

    # Save state
    _save_state(state)

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  USB_BRIDGE CYCLE {cycle} COMPLETE")
    print(f"  USB: {catalog['total_files']:,} files, {_sizeof_fmt(catalog['total_size'])}")
    print(f"  Synced: {synced} | Archived: {archived} engines | Ingested: {ingested_count}")
    for drive, info in disk.get("drives", {}).items():
        if "error" not in info:
            status = "HEALTHY" if info.get("healthy") else "WARNING"
            print(f"  {drive}: {info['free']} free [{status}]")
    print(f"{'=' * 70}")

    return state


if __name__ == "__main__":
    run()
