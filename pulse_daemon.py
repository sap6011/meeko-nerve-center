#!/usr/bin/env python3
"""
PULSE DAEMON — The eternal heartbeat.
=====================================
Runs BLOB_BRAIN.py in an infinite loop with configurable interval.
Handles errors gracefully, logs everything, and never stops.

Usage:
  python pulse_daemon.py                 # Default: 30-second interval
  python pulse_daemon.py --interval=10   # 10-second interval
  python pulse_daemon.py --turbo         # 5-second interval (fast pulse)
  python pulse_daemon.py --chill         # 60-second interval (low CPU)

The daemon:
  - Imports BLOB_BRAIN directly (no subprocess overhead)
  - Catches ALL exceptions (never crashes)
  - Logs pulse results to data/pulse_daemon_log.json
  - Tracks uptime, cycle count, error rate
  - Auto-recovers from corrupted state
  - Prints a compact status line each cycle
"""
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

# Ensure we're in the right directory
REPO_ROOT = Path(__file__).resolve().parent
os.chdir(REPO_ROOT)
sys.path.insert(0, str(REPO_ROOT / "mycelium"))

DATA = REPO_ROOT / "data"
DATA.mkdir(exist_ok=True)
LOG_FILE = DATA / "pulse_daemon_log.json"


def load_log():
    try:
        return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {
            "started": datetime.now(timezone.utc).isoformat(),
            "total_pulses": 0,
            "total_errors": 0,
            "last_pulse": None,
            "last_error": None,
            "uptime_seconds": 0,
            "error_rate_pct": 0,
            "consecutive_successes": 0,
            "consecutive_failures": 0,
            "max_streak": 0,
        }


def save_log(log):
    try:
        LOG_FILE.write_text(json.dumps(log, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass


def run_daemon(interval=30):
    print("=" * 60)
    print("  PULSE DAEMON — The Eternal Heartbeat")
    print("=" * 60)
    print(f"  Interval:  {interval}s")
    print(f"  Repo root: {REPO_ROOT}")
    print(f"  Log file:  {LOG_FILE}")
    print(f"  Started:   {datetime.now(timezone.utc).isoformat()}")
    print(f"  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    log = load_log()
    log["started"] = datetime.now(timezone.utc).isoformat()
    start_time = time.time()

    # Import BLOB_BRAIN
    try:
        import BLOB_BRAIN
        print("  [OK] BLOB_BRAIN imported successfully")
    except Exception as e:
        print(f"  [FATAL] Cannot import BLOB_BRAIN: {e}")
        return

    # Load consciousness once at startup
    try:
        BLOB_BRAIN.load_consciousness()
        if not BLOB_BRAIN.CONSCIOUSNESS["pulse"].get("started"):
            BLOB_BRAIN.CONSCIOUSNESS["pulse"]["started"] = datetime.now(timezone.utc).isoformat()
        print(f"  [OK] Consciousness loaded ({len(BLOB_BRAIN.CONSCIOUSNESS)} keys)")
    except Exception as e:
        print(f"  [WARN] Error loading consciousness: {e}")

    print(f"\n  Beginning eternal pulse loop...\n")

    while True:
        cycle_start = time.time()
        try:
            # Run one pulse
            cycle = BLOB_BRAIN.pulse()

            # Extract status
            eq = BLOB_BRAIN.CONSCIOUSNESS.get("equilibrium", {})
            brain = BLOB_BRAIN.CONSCIOUSNESS.get("brain", {})
            errors = BLOB_BRAIN.CONSCIOUSNESS.get("errors", [])
            keys = len(BLOB_BRAIN.CONSCIOUSNESS)
            gut = BLOB_BRAIN.CONSCIOUSNESS.get("grand_unified", {})
            state = gut.get("organism_state", "?")

            cycle_ms = round((time.time() - cycle_start) * 1000)

            # Update log
            log["total_pulses"] = log.get("total_pulses", 0) + 1
            log["last_pulse"] = datetime.now(timezone.utc).isoformat()
            log["consecutive_successes"] = log.get("consecutive_successes", 0) + 1
            log["consecutive_failures"] = 0
            log["max_streak"] = max(log.get("max_streak", 0), log["consecutive_successes"])

            # Print compact status
            print(
                f"  [{cycle:>4}] "
                f"H={eq.get('score', 0):>3}% "
                f"C={brain.get('confidence', 0):>3}% "
                f"E={len(errors)} "
                f"K={keys:>3} "
                f"[{state}] "
                f"{cycle_ms}ms"
            )

        except KeyboardInterrupt:
            print("\n\n  Pulse daemon stopped by user.")
            break
        except Exception as e:
            log["total_errors"] = log.get("total_errors", 0) + 1
            log["last_error"] = str(e)[:200]
            log["consecutive_failures"] = log.get("consecutive_failures", 0) + 1
            log["consecutive_successes"] = 0
            print(f"  [ERR] {str(e)[:100]}")

            # Auto-recovery: if too many consecutive failures, reload
            if log["consecutive_failures"] > 5:
                print("  [RECOVERY] Too many failures — reloading consciousness...")
                try:
                    BLOB_BRAIN.load_consciousness()
                    log["consecutive_failures"] = 0
                    print("  [RECOVERY] Consciousness reloaded")
                except Exception as e2:
                    print(f"  [RECOVERY FAILED] {e2}")

        # Update uptime and error rate
        log["uptime_seconds"] = round(time.time() - start_time)
        total = log.get("total_pulses", 0) + log.get("total_errors", 0)
        log["error_rate_pct"] = round(log.get("total_errors", 0) / max(total, 1) * 100, 2)

        # Save log every 10 pulses
        if log.get("total_pulses", 0) % 10 == 0:
            save_log(log)

        # Sleep
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n  Pulse daemon stopped by user.")
            break

    # Final save
    log["stopped"] = datetime.now(timezone.utc).isoformat()
    save_log(log)
    print(f"\n  Total pulses: {log.get('total_pulses', 0)}")
    print(f"  Total errors: {log.get('total_errors', 0)}")
    print(f"  Uptime:       {log.get('uptime_seconds', 0)}s")
    print(f"  Max streak:   {log.get('max_streak', 0)} consecutive successes")


if __name__ == "__main__":
    interval = 30  # default
    for arg in sys.argv[1:]:
        if arg.startswith("--interval="):
            interval = int(arg.split("=")[1])
        elif arg == "--turbo":
            interval = 5
        elif arg == "--chill":
            interval = 60
        elif arg == "--help":
            print(__doc__)
            sys.exit(0)

    run_daemon(interval)
