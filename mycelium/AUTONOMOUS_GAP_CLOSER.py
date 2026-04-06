#!/usr/bin/env python3
"""
AUTONOMOUS_GAP_CLOSER.py — Finds and closes gaps without human intervention
============================================================================
Scans the system for tasks that are labeled "human" but can actually be done
by AI using available channels (GitHub CLI, file operations, data seeding).

Philosophy: If SolarPunk CAN do it, SolarPunk SHOULD do it.
Only escalate to Meeko for things requiring legal identity or body.

Channels available:
  - GitHub CLI (gh): issues, discussions, releases, PRs, wiki, secrets
  - File system: read/write any data file, generate HTML/JSON
  - Python: run any engine, compile check, test
  - Data seeding: create missing JSON files so engines don't crash
  - Bridge building: connect outputs to inputs
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
DOCS = Path("docs")

STATE_FILE = DATA / "gap_closer_state.json"


def _ts():
    return datetime.now(timezone.utc).isoformat()


def _load(name, default=None):
    f = DATA / name
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default if default is not None else {}


def _save(name, data):
    (DATA / name).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _run(cmd, timeout=30):
    """Run a shell command, return (success, output)."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Gap scanners — each returns a list of closable gaps
# ---------------------------------------------------------------------------

def scan_missing_data_files():
    """Find data files engines expect but don't exist yet."""
    gaps = []
    bridge_report = _load("bridge_report.json")
    if not bridge_report:
        return gaps

    for bridge_name, info in bridge_report.get("bridges", {}).items():
        if isinstance(info, dict) and info.get("status") == "FAILED":
            gaps.append({
                "type": "missing_data",
                "file": bridge_name,
                "action": "seed_empty_json",
                "reason": f"Bridge failed: {info.get('error', 'unknown')}",
            })
    return gaps


def scan_compile_errors():
    """Find engines that don't compile."""
    import py_compile
    gaps = []
    for f in sorted(MYCELIUM.glob("*.py")):
        if f.name.startswith("__"):
            continue
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as e:
            gaps.append({
                "type": "compile_error",
                "file": str(f),
                "error": str(e)[:200],
                "action": "log_for_debug_doctor",
            })
    return gaps


def scan_stale_docs():
    """Find docs pages with outdated engine counts or dates."""
    gaps = []
    engine_count = len(list(MYCELIUM.glob("*.py")))

    for html_file in DOCS.glob("*.html"):
        try:
            content = html_file.read_text(encoding="utf-8", errors="replace")
            # Check for outdated engine counts
            for old_count in ["50+", "100+", "200+", "300+", "350+", "368+"]:
                if old_count in content and str(engine_count) not in content:
                    gaps.append({
                        "type": "stale_docs",
                        "file": str(html_file),
                        "action": "update_engine_count",
                        "old": old_count,
                        "new": str(engine_count),
                    })
                    break
        except Exception:
            pass
    return gaps


def scan_disconnected_engines():
    """Find engines with zero reads or zero writes from live_wire_report."""
    gaps = []
    report = _load("live_wire_report.json")
    if not report:
        return gaps

    engines = report.get("engines", {})
    for name, info in engines.items():
        reads = info.get("reads", [])
        writes = info.get("writes", [])
        if not writes and reads:
            gaps.append({
                "type": "zero_writes",
                "engine": name,
                "reads": len(reads),
                "action": "add_state_output",
            })
        elif not reads and writes:
            gaps.append({
                "type": "zero_reads",
                "engine": name,
                "writes": len(writes),
                "action": "connect_to_consumers",
            })
    return gaps


def scan_human_task_board():
    """Find tasks on the human task board that AI can actually do."""
    board = _load("human_task_board.json")
    if not board:
        return []

    tasks = board if isinstance(board, list) else board.get("tasks", [])
    gaps = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        desc = str(task.get("description", "") or task.get("task", "")).lower()
        status = str(task.get("status", "")).lower()

        if status in ("done", "completed", "closed"):
            continue

        # Tasks that AI CAN do
        if any(kw in desc for kw in [
            "github discussion", "github release", "create issue",
            "update readme", "generate", "write", "build bridge",
            "seed data", "compile", "run engine", "create draft",
        ]):
            gaps.append({
                "type": "automatable_task",
                "task": desc[:200],
                "action": "execute_via_channel",
                "channel": "github_cli" if "github" in desc else "python",
            })

    return gaps


# ---------------------------------------------------------------------------
# Gap closers — actually fix the gaps
# ---------------------------------------------------------------------------

def close_missing_data(gap):
    """Seed a missing data file with empty/default content."""
    fname = gap["file"]
    fpath = DATA / fname
    if fpath.exists():
        return {"status": "already_exists", "file": fname}

    if fname.endswith(".json"):
        fpath.write_text(json.dumps({
            "seeded_by": "AUTONOMOUS_GAP_CLOSER",
            "seeded_at": _ts(),
            "note": "Auto-seeded to prevent engine crashes",
        }, indent=2), encoding="utf-8")
    elif fname.endswith(".txt"):
        fpath.write_text(
            f"# Auto-seeded by AUTONOMOUS_GAP_CLOSER at {_ts()}\n",
            encoding="utf-8"
        )
    else:
        return {"status": "skipped", "reason": f"Unknown extension: {fname}"}

    return {"status": "seeded", "file": fname}


def close_stale_docs(gap):
    """Update outdated engine counts in docs pages."""
    fpath = Path(gap["file"])
    if not fpath.exists():
        return {"status": "file_missing"}

    try:
        content = fpath.read_text(encoding="utf-8", errors="replace")
        updated = content.replace(gap["old"], gap["new"])
        if updated != content:
            fpath.write_text(updated, encoding="utf-8")
            return {"status": "updated", "file": str(fpath), "old": gap["old"], "new": gap["new"]}
    except Exception as e:
        return {"status": "error", "error": str(e)}

    return {"status": "no_change"}


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run():
    print("=" * 60)
    print("AUTONOMOUS_GAP_CLOSER -- Finding and closing gaps")
    print("=" * 60)

    state = _load("gap_closer_state.json", {
        "engine": "AUTONOMOUS_GAP_CLOSER",
        "created_at": _ts(),
        "cycles": 0,
        "total_gaps_found": 0,
        "total_gaps_closed": 0,
    })
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = _ts()

    all_gaps = []
    closed = []

    # Phase 1: SCAN for gaps
    print("\n[1/4] Scanning for missing data files...")
    missing = scan_missing_data_files()
    print(f"  Found {len(missing)} missing data files")
    all_gaps.extend(missing)

    print("\n[2/4] Scanning for compile errors...")
    compile_errs = scan_compile_errors()
    print(f"  Found {len(compile_errs)} compile errors")
    all_gaps.extend(compile_errs)

    print("\n[3/4] Scanning for stale docs...")
    stale = scan_stale_docs()
    print(f"  Found {len(stale)} stale docs pages")
    all_gaps.extend(stale)

    print("\n[4/4] Scanning for disconnected engines...")
    disconnected = scan_disconnected_engines()
    zero_writes = [g for g in disconnected if g["type"] == "zero_writes"]
    zero_reads = [g for g in disconnected if g["type"] == "zero_reads"]
    print(f"  Found {len(zero_writes)} engines with zero writes")
    print(f"  Found {len(zero_reads)} engines with zero reads")
    all_gaps.extend(disconnected)

    # Phase 2: CLOSE gaps we can fix
    print(f"\n--- Closing {len(all_gaps)} gaps ---")

    for gap in all_gaps:
        if gap["type"] == "missing_data":
            result = close_missing_data(gap)
            if result["status"] == "seeded":
                closed.append({**gap, "result": result})
                print(f"  [SEEDED] {gap['file']}")

        elif gap["type"] == "stale_docs":
            result = close_stale_docs(gap)
            if result["status"] == "updated":
                closed.append({**gap, "result": result})
                print(f"  [UPDATED] {gap['file']}: {gap['old']} -> {gap['new']}")

        elif gap["type"] == "compile_error":
            print(f"  [LOGGED] {gap['file']}: {gap['error'][:80]}")

        elif gap["type"] in ("zero_writes", "zero_reads"):
            pass  # Logged for awareness, fixed by bridge building

    # Phase 3: REPORT
    state["total_gaps_found"] = state.get("total_gaps_found", 0) + len(all_gaps)
    state["total_gaps_closed"] = state.get("total_gaps_closed", 0) + len(closed)
    state["last_scan"] = {
        "gaps_found": len(all_gaps),
        "gaps_closed": len(closed),
        "by_type": {
            "missing_data": len(missing),
            "compile_errors": len(compile_errs),
            "stale_docs": len(stale),
            "zero_writes": len(zero_writes),
            "zero_reads": len(zero_reads),
        },
    }

    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    _save("gap_closer_state.json", state)
    _save("gap_closer_report.json", {
        "timestamp": _ts(),
        "all_gaps": all_gaps[:200],
        "closed": closed[:100],
        "summary": state["last_scan"],
    })

    print(f"\n{'=' * 60}")
    print(f"  Gaps found:  {len(all_gaps)}")
    print(f"  Gaps closed: {len(closed)}")
    print(f"  Compile errors: {len(compile_errs)}")
    print(f"  Zero-write engines: {len(zero_writes)}")
    print(f"  Zero-read engines: {len(zero_reads)}")
    print(f"  Stale docs: {len(stale)}")
    print(f"{'=' * 60}")

    return state


if __name__ == "__main__":
    run()
