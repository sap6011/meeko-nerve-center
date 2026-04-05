#!/usr/bin/env python3
"""
WORKTREE_ANCHOR.py — Prevents Claude Session Desync
====================================================
On 2026-03-27, a Claude session spawned in a shallow worktree branch,
saw "1 engine on main," and tried to rebuild the entire 251-engine system
from scratch. This engine exists to prevent that from ever happening again.

What it does:
  1. Writes data/worktree_anchor.json with the REAL system state
  2. Counts actual engines in mycelium/
  3. Lists key sovereign files and their hashes
  4. Records the current git branch and latest commit
  5. Any Claude session that reads this file knows the real state

This file is the "ground truth beacon." If a Claude session sees
an empty branch, it should check worktree_anchor.json FIRST before
assuming the system needs rebuilding.

Zero secrets. Pure filesystem audit.
"""
import hashlib
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
ANCHOR_FILE = DATA / "worktree_anchor.json"

# Key sovereign files that MUST exist
SOVEREIGN_FILES = [
    "mycelium/CORRUPTION_SENTINEL.py",
    "mycelium/SOVEREIGNTY_ENGINE.py",
    "mycelium/LIVE_WIRE.py",
    "mycelium/BRIDGE_BUILDER.py",
    "mycelium/CONTENT_HARVESTER.py",
    "mycelium/CRISIS_MONITOR.py",
    "mycelium/BROADCAST_PROTOCOL.py",
    "mycelium/OUTREACH_ENGINE.py",
    "data/identity_manifest.json",
]


def file_hash(path):
    """SHA256 of a file, or None if missing."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
    except Exception:
        return None


def git_info():
    """Get current branch and latest commit."""
    info = {}
    try:
        info["branch"] = subprocess.check_output(
            ["git", "branch", "--show-current"], text=True, timeout=5
        ).strip()
    except Exception:
        info["branch"] = "unknown"
    try:
        info["commit"] = subprocess.check_output(
            ["git", "log", "-1", "--format=%H %s"], text=True, timeout=5
        ).strip()
    except Exception:
        info["commit"] = "unknown"
    return info


def main():
    print("WORKTREE_ANCHOR — Recording ground truth...")

    # Count real engines
    engines = sorted([f.name for f in MYCELIUM.glob("*.py")])
    engine_count = len(engines)

    # Check sovereign files
    sovereign_status = {}
    for sf in SOVEREIGN_FILES:
        h = file_hash(sf)
        sovereign_status[sf] = {"exists": h is not None, "hash": h}

    missing = [sf for sf, v in sovereign_status.items() if not v["exists"]]

    # Git state
    git = git_info()

    # Build anchor
    anchor = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine_count": engine_count,
        "engines": engines,
        "sovereign_files": sovereign_status,
        "missing_sovereign": missing,
        "git_branch": git["branch"],
        "git_latest_commit": git["commit"],
        "health": "SOVEREIGN" if not missing else f"DEGRADED ({len(missing)} missing)",
        "warning_to_claude": (
            "DO NOT attempt to rebuild or recreate engines if you see an empty branch. "
            "You are likely in a shallow worktree. The real system has "
            f"{engine_count} engines on the '{git['branch']}' branch. "
            "Run 'find . -name worktree_anchor.json' to locate the real codebase. "
            "Check .claude/worktrees/ for the worktree that is on 'main'."
        ),
    }

    ANCHOR_FILE.write_text(json.dumps(anchor, indent=2), encoding="utf-8")

    print(f"  Engines: {engine_count}")
    print(f"  Branch: {git['branch']}")
    print(f"  Sovereign: {'ALL PRESENT' if not missing else f'{len(missing)} MISSING: {missing}'}")
    print(f"  Health: {anchor['health']}")
    print(f"  Anchor written to {ANCHOR_FILE}")

    if missing:
        print(f"\n  WARNING: Missing sovereign files: {missing}")
        print(f"  The system may be degraded. Check git log for when these were lost.")


if __name__ == "__main__":
    main()
