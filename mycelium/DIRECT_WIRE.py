#!/usr/bin/env python3
"""
DIRECT_WIRE.py — Frictionless commit pipeline for SolarPunk
============================================================

No branches. No PRs. No merges. No friction.
Code goes from HERE to MAIN to GITHUB the instant it compiles clean.

The old way:  branch → commit → push → PR → review → merge → pull
SolarPunk:    compile → commit → push. Done.

This engine IS the circulatory system. Data flows like blood:
  Local edits → compile check → commit to main → push to origin →
  sync to USB node → done. Nothing waits. Nothing queues.

Usage:
  python DIRECT_WIRE.py                    # auto-commit all changes
  python DIRECT_WIRE.py "my message"       # commit with custom message
  python DIRECT_WIRE.py --sync             # commit + sync USB node
  python DIRECT_WIRE.py --pull             # pull latest from origin first
  python DIRECT_WIRE.py --full             # pull + commit + push + sync USB

Called by: OMNIBUS, AUTOPILOT, Claude sessions, USB_BRIDGE
Calls: compile check, git, USB_BRIDGE
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

REPO_ROOT = Path(__file__).resolve().parent.parent
MYCELIUM = REPO_ROOT / "mycelium"
USB_NODE = Path("E:/SolarPunk_Node/meeko-nerve-center")


def _run(cmd, cwd=None, timeout=120):
    """Run a command, return (ok, stdout)."""
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=cwd or str(REPO_ROOT), timeout=timeout, shell=True,
        )
        return r.returncode == 0, r.stdout.strip() + r.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)


def compile_check():
    """Compile check all engines. Returns (total, clean, errors)."""
    import py_compile
    engines = sorted(MYCELIUM.glob("*.py"))
    total = 0
    errors = []
    for f in engines:
        if f.name.startswith("__"):
            continue
        total += 1
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append((f.name, str(e).split("\n")[0][:100]))
    return total, total - len(errors), errors


def git_status():
    """Get current git state."""
    ok, branch = _run("git branch --show-current")
    ok2, status = _run("git status --porcelain")
    ok3, log = _run("git log --oneline -1")
    return {
        "branch": branch if ok else "unknown",
        "dirty": bool(status.strip()) if ok2 else True,
        "changes": len([l for l in status.strip().split("\n") if l]) if ok2 else 0,
        "last_commit": log if ok3 else "unknown",
    }


def pull_latest():
    """Pull latest from origin/main."""
    print("[DIRECT_WIRE] Pulling latest from origin/main...")
    ok, out = _run("git pull --no-rebase origin main")
    if ok:
        print(f"[DIRECT_WIRE] Pull OK")
    else:
        print(f"[DIRECT_WIRE] Pull issue: {out[:200]}")
    return ok


def commit_and_push(message=None):
    """Commit all changes and push directly to main.

    Returns (committed, pushed, details).
    """
    # Check status
    state = git_status()

    if state["branch"] != "main":
        print(f"[DIRECT_WIRE] WARNING: on branch '{state['branch']}', switching to main")
        _run("git checkout main")

    if not state["dirty"]:
        print("[DIRECT_WIRE] Nothing to commit — tree is clean")
        return False, False, "clean"

    # Compile check first
    total, clean, errors = compile_check()
    print(f"[DIRECT_WIRE] Compile: {clean}/{total} clean")

    if errors:
        print(f"[DIRECT_WIRE] {len(errors)} compile errors — NOT committing:")
        for name, err in errors[:5]:
            print(f"  FAIL: {name}: {err[:80]}")
        return False, False, f"{len(errors)} compile errors"

    # Stage everything (except secrets)
    _run("git add -A")

    # Unstage sensitive files
    for pattern in [".env", "credentials", "secrets.json", "*.pem", "*.key"]:
        _run(f"git reset HEAD -- {pattern}")

    # Build commit message
    if not message:
        message = f"SolarPunk DIRECT_WIRE: {state['changes']} changes, {clean}/{total} engines clean"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_msg = f"{message}\n\n[DIRECT_WIRE {timestamp} | {clean}/{total} engines | auto-committed]"

    # Commit
    ok, out = _run(f'git commit -m "{full_msg}"')
    if not ok:
        print(f"[DIRECT_WIRE] Commit failed: {out[:200]}")
        return False, False, out[:200]

    print(f"[DIRECT_WIRE] Committed: {message[:60]}")

    # Push
    ok, out = _run("git push origin main", timeout=60)
    if not ok:
        # Try pull + push
        print("[DIRECT_WIRE] Push rejected, pulling first...")
        _run("git pull --no-rebase origin main")
        ok, out = _run("git push origin main", timeout=60)

    if ok:
        print("[DIRECT_WIRE] Pushed to origin/main")
    else:
        print(f"[DIRECT_WIRE] Push failed: {out[:200]}")

    return True, ok, message


def sync_usb():
    """Sync to USB node if connected."""
    if not USB_NODE.exists():
        print("[DIRECT_WIRE] USB node not connected — skip")
        return False

    print("[DIRECT_WIRE] Syncing USB node...")
    ok, out = _run("git pull origin main", cwd=str(USB_NODE), timeout=120)
    if ok:
        print("[DIRECT_WIRE] USB node synced")
    else:
        print(f"[DIRECT_WIRE] USB sync issue: {out[:200]}")
    return ok


def wire(message=None, pull_first=False, sync=False, full=False):
    """The main pipeline. Call this.

    Args:
        message: Optional commit message
        pull_first: Pull from origin before committing
        sync: Sync USB node after pushing
        full: Do everything (pull + commit + push + sync)
    """
    start = time.time()
    results = {
        "timestamp": datetime.now().isoformat(),
        "pulled": False,
        "committed": False,
        "pushed": False,
        "usb_synced": False,
    }

    if full:
        pull_first = True
        sync = True

    # Pull if requested
    if pull_first:
        results["pulled"] = pull_latest()

    # Commit and push
    committed, pushed, details = commit_and_push(message)
    results["committed"] = committed
    results["pushed"] = pushed
    results["details"] = details

    # Sync USB
    if sync or full:
        results["usb_synced"] = sync_usb()

    elapsed = time.time() - start
    results["elapsed_seconds"] = round(elapsed, 1)

    # Write state
    (DATA / "direct_wire_state.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )

    status = "WIRED" if pushed else ("COMMITTED" if committed else "NO-OP")
    print(f"\n[DIRECT_WIRE] {status} in {elapsed:.1f}s")
    return results


def pair_device(device_id, device_type="phone"):
    """Register a device pairing in known_devices.json.

    Usage: python DIRECT_WIRE.py --pair SP-XXXXXXXX
    Both devices must add each other for MUTUAL TRUST.
    """
    registry_path = DATA / "known_devices.json"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception:
        registry = {"devices": [], "pairs": []}

    if "devices" not in registry:
        registry["devices"] = []
    if "pairs" not in registry:
        registry["pairs"] = []

    # Get desktop's own ID
    desktop_id = "MEEKO-DESKTOP"

    # Add the new device if not already registered
    if not any(d.get("id") == device_id for d in registry["devices"]):
        registry["devices"].append({
            "id": device_id,
            "type": device_type,
            "status": "trusted",
            "registered": datetime.now().isoformat(),
        })
        print(f"[DIRECT_WIRE] Registered device: {device_id}")

    # Create the pair if not already paired
    pair_exists = any(
        (p.get("device_a") == desktop_id and p.get("device_b") == device_id) or
        (p.get("device_a") == device_id and p.get("device_b") == desktop_id)
        for p in registry["pairs"]
    )
    if not pair_exists:
        registry["pairs"].append({
            "device_a": desktop_id,
            "device_b": device_id,
            "paired_at": datetime.now().isoformat(),
            "trust": "mutual",
        })
        print(f"[DIRECT_WIRE] Paired: {desktop_id} <-> {device_id}")

    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(f"[DIRECT_WIRE] Device registry updated — {len(registry['devices'])} devices, {len(registry['pairs'])} pairs")
    return registry


def run():
    """Engine entry point for OMNIBUS."""
    return wire(full=True)


# === CLI ===
if __name__ == "__main__":
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    # Device pairing
    if "--pair" in args:
        idx = args.index("--pair")
        if idx + 1 < len(args):
            pair_device(args[idx + 1].upper())
            # Auto-commit and push the pairing
            wire(message=f"trust: paired device {args[idx + 1].upper()}")
        else:
            print("Usage: python DIRECT_WIRE.py --pair SP-XXXXXXXX")
        sys.exit(0)

    do_pull = "--pull" in args or "--full" in args
    do_sync = "--sync" in args or "--full" in args
    do_full = "--full" in args

    # Remaining args = commit message
    msg_parts = [a for a in args if not a.startswith("--")]
    msg = " ".join(msg_parts) if msg_parts else None

    wire(message=msg, pull_first=do_pull, sync=do_sync, full=do_full)
