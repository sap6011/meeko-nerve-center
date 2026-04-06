#!/usr/bin/env python3
"""
GIT_GATEKEEPER.py — The Single Point of Truth for All Git Operations
=====================================================================
PROBLEM:
  8+ engines (DESKTOP_DAEMON, DIRECT_WIRE, EVENT_RELAY, GUARDIAN,
  SOLARPUNK_AUTOPILOT, SYNTHESIS_FACTORY, WEB_PUBLISHER, COMMAND_CENTER)
  all do their own git add/commit/push INDEPENDENTLY. This causes:
    - index.lock files from concurrent git processes
    - Push rejections (remote contains work you don't have)
    - Rebase hell (unstaged changes blocking pull)
    - Lock files requiring manual kill+delete every time

SOLUTION:
  ONE engine owns ALL git operations. File-locked. Queue-based.
  Every other engine that wants to commit drops a request into
  data/git_queue.json. GIT_GATEKEEPER processes them one at a time.

  Like a traffic light at an intersection — everyone gets through,
  nobody crashes.

HOW IT WORKS:
  1. Acquires a file lock (data/.git_gatekeeper.lock)
  2. Reads data/git_queue.json for pending commit requests
  3. Stages the requested files
  4. Commits with the requested message
  5. Pushes to remote (with retry on rejection)
  6. Clears processed requests from queue
  7. Reports to data/git_gatekeeper_state.json

USAGE BY OTHER ENGINES:
  from GIT_GATEKEEPER import queue_commit, sync_now

  # Queue a commit (processed on next gatekeeper cycle):
  queue_commit(files=["mycelium/MY_ENGINE.py"], message="update MY_ENGINE")

  # Or sync immediately (blocking, acquires lock):
  sync_now(files=["docs/index.html"], message="deploy landing page")

SAFETY:
  - File lock prevents concurrent git operations
  - Lock auto-expires after 120 seconds (dead process recovery)
  - Never force-pushes
  - Never touches data/ files (they're .gitignored now)
  - Retries push up to 3 times with pull --rebase between

Reports to: data/git_gatekeeper_state.json
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA = REPO_ROOT / "data"
DATA.mkdir(exist_ok=True)

LOCK_FILE = DATA / ".git_gatekeeper.lock"
QUEUE_FILE = DATA / "git_queue.json"
STATE_FILE = DATA / "git_gatekeeper_state.json"
LOCK_TIMEOUT = 120  # seconds before stale lock is broken


def _git(*args, timeout=60):
    """Run a git command in the repo root. Returns (success, stdout, stderr)."""
    try:
        r = subprocess.run(
            ["git", "-C", str(REPO_ROOT)] + list(args),
            capture_output=True, text=True, timeout=timeout
        )
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except Exception as e:
        return False, "", str(e)


def acquire_lock():
    """Acquire file lock. Returns True if acquired."""
    # Check for stale lock
    if LOCK_FILE.exists():
        try:
            lock_data = json.loads(LOCK_FILE.read_text())
            lock_time = lock_data.get("acquired", 0)
            if time.time() - lock_time > LOCK_TIMEOUT:
                print(f"  Breaking stale lock (age: {time.time() - lock_time:.0f}s)")
                LOCK_FILE.unlink()
            else:
                return False
        except Exception:
            LOCK_FILE.unlink(missing_ok=True)

    try:
        LOCK_FILE.write_text(json.dumps({
            "acquired": time.time(),
            "pid": os.getpid(),
            "ts": datetime.now(timezone.utc).isoformat()
        }))
        return True
    except Exception:
        return False


def release_lock():
    """Release the file lock."""
    LOCK_FILE.unlink(missing_ok=True)


def _clear_git_locks():
    """Remove any stale git index.lock files."""
    git_dir = REPO_ROOT / ".git"
    if git_dir.is_file():
        # worktree — read the gitdir path
        gitdir_text = git_dir.read_text().strip()
        if gitdir_text.startswith("gitdir:"):
            git_dir = Path(gitdir_text.split(":", 1)[1].strip())

    for lock in git_dir.rglob("*.lock"):
        try:
            lock.unlink()
        except Exception:
            pass


def load_queue():
    """Load the commit queue."""
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_queue(q):
    """Save the commit queue."""
    QUEUE_FILE.write_text(json.dumps(q, indent=2, default=str), encoding="utf-8")


def queue_commit(files=None, message="auto-commit", source="unknown"):
    """
    Queue a commit request. Non-blocking — just writes to queue file.
    Other engines call this instead of running git directly.
    """
    q = load_queue()
    q.append({
        "files": files or [],
        "message": message,
        "source": source,
        "queued_at": datetime.now(timezone.utc).isoformat()
    })
    save_queue(q)
    return True


def _do_commit_and_push(files, message, retries=3):
    """
    Stage, commit, and push. With retry on push rejection.
    Returns (success, detail).
    """
    # Clear any stale git locks first
    _clear_git_locks()

    # Stage files
    if files:
        for f in files:
            ok, out, err = _git("add", f)
            if not ok and "did not match any files" not in err:
                return False, f"stage failed: {err[:80]}"
    else:
        # Stage all tracked changes (not data/ since it's gitignored)
        _git("add", "-A")

    # Check if there's anything to commit
    ok, out, _ = _git("diff", "--cached", "--quiet")
    if ok:
        return True, "nothing to commit"

    # Commit
    ok, out, err = _git("commit", "-m", message)
    if not ok:
        return False, f"commit failed: {err[:80]}"

    # Push with retry
    for attempt in range(retries):
        ok, out, err = _git("push", "origin", "main", timeout=30)
        if ok:
            return True, f"pushed (attempt {attempt + 1})"

        if "rejected" in err or "fetch first" in err:
            # Pull --rebase and retry
            _clear_git_locks()
            ok2, _, err2 = _git("pull", "--rebase", "origin", "main", timeout=30)
            if not ok2:
                # If rebase fails, abort and try again
                _git("rebase", "--abort")
                _clear_git_locks()
                time.sleep(2)
                continue
        else:
            return False, f"push failed: {err[:80]}"

    return False, f"push failed after {retries} retries"


def sync_now(files=None, message="auto-commit", source="unknown"):
    """
    Immediate sync — acquires lock, commits, pushes, releases.
    Blocking call. Use queue_commit() for async.
    """
    # Wait for lock (up to 30 seconds)
    for _ in range(15):
        if acquire_lock():
            break
        time.sleep(2)
    else:
        return False, "could not acquire lock"

    try:
        return _do_commit_and_push(files, message)
    finally:
        release_lock()


def process_queue():
    """Process all pending commit requests in the queue."""
    q = load_queue()
    if not q:
        return 0, []

    results = []
    # Merge all files and messages into one commit (batch efficiency)
    all_files = []
    sources = set()
    for item in q:
        all_files.extend(item.get("files", []))
        sources.add(item.get("source", "unknown"))

    # Deduplicate files
    all_files = list(set(all_files)) if all_files else None

    msg_parts = [item.get("message", "update") for item in q[:5]]
    if len(q) > 5:
        msg_parts.append(f"(+{len(q)-5} more)")
    message = " | ".join(msg_parts)

    ok, detail = _do_commit_and_push(all_files, message)
    results.append({"ok": ok, "detail": detail, "items": len(q), "sources": list(sources)})

    # Clear queue on success
    if ok:
        save_queue([])

    return len(q), results


def run():
    ts = datetime.now(timezone.utc).isoformat()
    print("GIT_GATEKEEPER -- Single Point of Truth for Git Ops")
    print("=" * 55)

    # Acquire lock
    if not acquire_lock():
        print("  Lock held by another process. Skipping cycle.")
        return {"status": "locked", "ts": ts}

    try:
        # Process queue
        count, results = process_queue()

        if count:
            print(f"  Processed {count} queued commits")
            for r in results:
                status = "OK" if r["ok"] else "FAIL"
                print(f"    [{status}] {r['detail']} (from: {', '.join(r['sources'])})")
        else:
            print("  Queue empty. Nothing to sync.")

        # Read nervous system state
        try:
            _h = json.loads((DATA / "homeostasis_state.json").read_text(encoding="utf-8"))
        except Exception:
            _h = {}
        try:
            _c = json.loads((DATA / "neural_cortex_state.json").read_text(encoding="utf-8"))
        except Exception:
            _c = {}

        state = {
            "last_run": ts,
            "queue_processed": count,
            "results": results,
            "status": "ok",
            "nervous_system": {
                "equilibrium": _h.get("equilibrium", 0),
                "trend": _h.get("trend", "unknown"),
                "brain_confidence": _c.get("decision_confidence", 0),
            },
        }
        STATE_FILE.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")

        print(f"\n  State: {STATE_FILE.name}")
        return state

    finally:
        release_lock()


if __name__ == "__main__":
    run()
