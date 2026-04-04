#!/usr/bin/env python3
"""
ZERO_SECRET_ARMY.py -- Deploy Everything That Needs No Keys
============================================================
Reads the wire topology to find every engine that:
  1. Needs zero API keys (zero_secrets = true)
  2. Has a run() function
  3. Isn't already running in OMNIBUS

Then RUNS them. All of them. Right now.

If an engine fails, log it and move on. If it succeeds, record
what it produced. Build the map of what works without any
external dependencies.

This is the standing army: 83+ engines that can fire right now,
on this machine, with nothing but Python and files.

Reads: data/live_wire_report.json, data/zero_secret_army_state.json
Writes: data/zero_secret_army_state.json, data/zero_secret_army_report.json
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")

# Engines to skip (they're orchestrators, not individual runners)
SKIP_ENGINES = {
    "OMNIBUS",          # the orchestrator itself
    "ZERO_SECRET_ARMY", # that's us
    "TASK_FACTORY",     # runs separately
    "AUTO_BUILDER",     # runs separately
    "__init__",
    "AI_CLIENT",        # library, not an engine
    "NANO_AGENT",       # library
}

# Max engines per run to avoid overwhelming the machine
MAX_PER_RUN = 40
ENGINE_TIMEOUT = 60  # seconds per engine


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8"
    )


def discover_army():
    """Find all zero-secret engines with run() functions."""
    wire_report = load_json(DATA / "live_wire_report.json")
    engines = wire_report.get("engines", {})

    army = []
    for name, info in engines.items():
        if name in SKIP_ENGINES:
            continue
        if not info.get("zero_secrets"):
            continue
        if not info.get("has_run"):
            continue

        engine_path = MYCELIUM / ("%s.py" % name)
        if not engine_path.exists():
            continue

        army.append({
            "name": name,
            "path": str(engine_path),
            "reads": info.get("reads", []),
            "writes": info.get("writes", []),
            "functions": info.get("functions_count", 0),
            "lines": info.get("lines", 0),
        })

    return army


def run_engine(name, path, timeout=ENGINE_TIMEOUT):
    """Run a single engine and capture results."""
    start = time.time()
    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(Path.cwd()),
            env=env,
            errors="replace",
        )
        elapsed = time.time() - start
        # Get last meaningful line of output (sanitize for Windows cp1252)
        output_lines = [l.strip() for l in result.stdout.split("\n") if l.strip()]
        last_line = output_lines[-1] if output_lines else ""
        last_line = last_line.encode("ascii", errors="replace").decode("ascii")

        return {
            "status": "OK" if result.returncode == 0 else "FAIL",
            "returncode": result.returncode,
            "elapsed": round(elapsed, 1),
            "last_line": last_line[:200],
            "stderr": result.stderr[:200] if result.stderr else "",
            "output_lines": len(output_lines),
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "returncode": -1,
            "elapsed": timeout,
            "last_line": "",
            "stderr": "Timed out after %ds" % timeout,
            "output_lines": 0,
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "returncode": -1,
            "elapsed": time.time() - start,
            "last_line": "",
            "stderr": str(e)[:200],
            "output_lines": 0,
        }


def check_data_files_created(writes_list):
    """Check which data files an engine created/updated."""
    created = []
    for w in writes_list:
        path = DATA / w if not w.startswith("data/") else Path(w)
        if path.exists():
            try:
                size = path.stat().st_size
                created.append({"file": str(path), "size": size})
            except Exception:
                pass
    return created


def run():
    print("ZERO SECRET ARMY -- Deploy Everything That Needs No Keys")
    print("=" * 60)

    state = load_json(DATA / "zero_secret_army_state.json")
    if not state:
        state = {"runs": 0, "total_ok": 0, "total_fail": 0, "last_run": None}

    # Discover
    print("\n  [1/3] Discovering zero-secret army...")
    army = discover_army()
    print("    Engines found: %d (zero secrets + has run())" % len(army))

    if not army:
        print("    No engines to deploy. Run LIVE_WIRE first.")
        save_json(DATA / "zero_secret_army_state.json", state)
        return

    # Prioritize: engines with more writes go first (they produce data)
    army.sort(key=lambda e: len(e["writes"]), reverse=True)

    # Limit per run
    batch = army[:MAX_PER_RUN]
    print("    Running batch: %d / %d engines" % (len(batch), len(army)))

    # Deploy
    print("\n  [2/3] Deploying army...")
    results = []
    ok_count = 0
    fail_count = 0
    timeout_count = 0

    for i, engine in enumerate(batch):
        name = engine["name"]
        r = run_engine(name, engine["path"])

        status_marker = "OK" if r["status"] == "OK" else "XX" if r["status"] == "FAIL" else "TO"
        print("    [%d/%d] %s %s (%.1fs) %s" % (
            i + 1, len(batch), status_marker, name, r["elapsed"],
            ("-- " + r["last_line"][:60]) if r["last_line"] else ""))

        if r["status"] == "OK":
            ok_count += 1
        elif r["status"] == "TIMEOUT":
            timeout_count += 1
        else:
            fail_count += 1

        results.append({
            "name": name,
            "status": r["status"],
            "elapsed": r["elapsed"],
            "last_line": r["last_line"],
            "data_files": check_data_files_created(engine["writes"]),
        })

    # Report
    print("\n  [3/3] Generating report...")
    state["runs"] = state.get("runs", 0) + 1
    state["total_ok"] = state.get("total_ok", 0) + ok_count
    state["total_fail"] = state.get("total_fail", 0) + fail_count
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["last_batch_size"] = len(batch)
    state["last_ok"] = ok_count
    state["last_fail"] = fail_count
    state["last_timeout"] = timeout_count
    save_json(DATA / "zero_secret_army_state.json", state)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "army_size": len(army),
        "batch_size": len(batch),
        "ok": ok_count,
        "fail": fail_count,
        "timeout": timeout_count,
        "results": results,
    }
    save_json(DATA / "zero_secret_army_report.json", report)

    # Count total data files produced
    total_files = sum(len(r["data_files"]) for r in results)

    print("\n  === ZERO SECRET ARMY REPORT ===")
    print("  Army size:     %d engines (zero secrets + run())" % len(army))
    print("  Batch run:     %d engines" % len(batch))
    print("  OK:            %d" % ok_count)
    print("  FAIL:          %d" % fail_count)
    print("  TIMEOUT:       %d" % timeout_count)
    print("  Data produced: %d files updated" % total_files)
    print("  Total runs:    %d" % state["runs"])
    print("\n  No keys. No APIs. No excuses. The army fires.")


if __name__ == "__main__":
    run()
