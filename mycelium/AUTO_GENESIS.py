#!/usr/bin/env python3
"""
AUTO_GENESIS.py -- The Self-Starting Perpetual Loop
=====================================================
The cycle that launches itself and never stops:

  1. LIVE_WIRE scans topology
  2. BRIDGE_BUILDER fills gaps
  3. ZERO_SECRET_ARMY fires all engines
  4. GAP_FILLER seeds missing data files
  5. DEBUG_DOCTOR diagnoses failures
  6. CHIMERA scores the cycle
  7. TASK_FACTORY generates next tasks
  8. AUTO_EXECUTOR runs autonomous tasks
  9. SYNERGY_FORGE mutates new connections
  10. RE-SCAN to measure improvement
  11. IF improvement > 0: GOTO 1

Each cycle produces data that the next cycle consumes.
Each engine's output is another engine's input.
The system feeds itself. Forever.

Reads: data/auto_genesis_state.json, data/live_wire_report.json
Writes: data/auto_genesis_state.json, data/auto_genesis_log.json
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

MAX_CYCLES = 3  # per invocation (prevents runaway)
IMPROVEMENT_THRESHOLD = 0  # continue if any metric improves
ENGINE_TIMEOUT = 600  # seconds per phase (army needs time for 85+ engines w/ Ollama)


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
except: _h={}
try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
except: _c={}
data["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8"
    )


def run_engine(name, timeout=ENGINE_TIMEOUT):
    """Run a mycelium engine and return (ok, elapsed, last_line)."""
    path = MYCELIUM / ("%s.py" % name)
    if not path.exists():
        return False, 0, "NOT FOUND"
    start = time.time()
    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(Path.cwd()),
            env=env,
            errors="replace",
        )
        elapsed = time.time() - start
        lines = [l.strip() for l in result.stdout.split("\n") if l.strip()]
        last = lines[-1] if lines else ""
        last = last.encode("ascii", errors="replace").decode("ascii")
        return result.returncode == 0, round(elapsed, 1), last
    except subprocess.TimeoutExpired:
        return False, timeout, "TIMEOUT"
    except Exception as e:
        return False, time.time() - start, str(e)[:100]


def get_metrics():
    """Read current system metrics for comparison."""
    wire = load_json(DATA / "live_wire_report.json")
    stats = wire.get("stats", wire)
    army = load_json(DATA / "zero_secret_army_report.json")
    chimera = load_json(DATA / "chimera_evolution_report.json")
    return {
        "engines": stats.get("total_engines", 0),
        "wires": stats.get("total_wires_discovered", 0),
        "zs_chains": stats.get("zero_secret_chains", 0),
        "army_ok": army.get("ok", 0),
        "army_fail": army.get("fail", 0),
        "chimera_score": chimera.get("composite_score", 0),
        "data_files": army.get("data_produced", 0),
    }


def run_cycle(cycle_num):
    """Run one full genesis cycle. Returns (metrics_before, metrics_after, phase_results)."""
    phases = []
    ts = datetime.now(timezone.utc).isoformat()
    print("\n  === GENESIS CYCLE %d ===" % cycle_num)
    print("  Time: %s" % ts)

    # Snapshot before
    before = get_metrics()
    print("  Before: %d engines, %d wires, chimera %d/100" % (
        before["engines"], before["wires"], before["chimera_score"]))

    # Phase 1: Scan
    print("\n  [1/9] LIVE_WIRE -- Scanning topology...")
    ok, elapsed, line = run_engine("LIVE_WIRE", timeout=120)
    phases.append({"phase": "LIVE_WIRE", "ok": ok, "elapsed": elapsed, "detail": line})
    print("    %s (%.1fs)" % ("OK" if ok else "FAIL", elapsed))

    # Phase 2: Bridge
    print("  [2/9] BRIDGE_BUILDER -- Filling gaps...")
    ok, elapsed, line = run_engine("BRIDGE_BUILDER", timeout=60)
    phases.append({"phase": "BRIDGE_BUILDER", "ok": ok, "elapsed": elapsed, "detail": line})
    print("    %s (%.1fs)" % ("OK" if ok else "FAIL", elapsed))

    # Phase 3: Army
    print("  [3/9] ZERO_SECRET_ARMY -- Deploying all engines...")
    ok, elapsed, line = run_engine("ZERO_SECRET_ARMY", timeout=ENGINE_TIMEOUT)
    phases.append({"phase": "ZERO_SECRET_ARMY", "ok": ok, "elapsed": elapsed, "detail": line})
    print("    %s (%.1fs)" % ("OK" if ok else "FAIL", elapsed))

    # Phase 4: Gap fill
    print("  [4/9] GAP_FILLER -- Seeding missing data...")
    ok, elapsed, line = run_engine("GAP_FILLER", timeout=30)
    phases.append({"phase": "GAP_FILLER", "ok": ok, "elapsed": elapsed, "detail": line})
    print("    %s (%.1fs)" % ("OK" if ok else "FAIL", elapsed))

    # Phase 5: Debug
    print("  [5/9] DEBUG_DOCTOR -- Diagnosing failures...")
    ok, elapsed, line = run_engine("DEBUG_DOCTOR", timeout=ENGINE_TIMEOUT)
    phases.append({"phase": "DEBUG_DOCTOR", "ok": ok, "elapsed": elapsed, "detail": line})
    print("    %s (%.1fs)" % ("OK" if ok else "FAIL", elapsed))

    # Phase 6: Evolve
    print("  [6/9] CHIMERA -- Scoring evolution...")
    ok, elapsed, line = run_engine("CHIMERA_EVOLUTION_ENGINE", timeout=ENGINE_TIMEOUT)
    phases.append({"phase": "CHIMERA", "ok": ok, "elapsed": elapsed, "detail": line})
    print("    %s (%.1fs)" % ("OK" if ok else "FAIL", elapsed))

    # Phase 7: Task generation
    print("  [7/9] TASK_FACTORY -- Generating tasks...")
    ok, elapsed, line = run_engine("TASK_FACTORY", timeout=30)
    phases.append({"phase": "TASK_FACTORY", "ok": ok, "elapsed": elapsed, "detail": line})
    print("    %s (%.1fs)" % ("OK" if ok else "FAIL", elapsed))

    # Phase 8: Auto-execute
    print("  [8/9] AUTO_EXECUTOR -- Running autonomous tasks...")
    ok, elapsed, line = run_engine("AUTO_EXECUTOR", timeout=ENGINE_TIMEOUT)
    phases.append({"phase": "AUTO_EXECUTOR", "ok": ok, "elapsed": elapsed, "detail": line})
    print("    %s (%.1fs)" % ("OK" if ok else "FAIL", elapsed))

    # Phase 9: Mutate
    print("  [9/9] SYNERGY_FORGE -- Generating mutations...")
    ok, elapsed, line = run_engine("SYNERGY_FORGE", timeout=30)
    phases.append({"phase": "SYNERGY_FORGE", "ok": ok, "elapsed": elapsed, "detail": line})
    print("    %s (%.1fs)" % ("OK" if ok else "FAIL", elapsed))

    # Snapshot after
    after = get_metrics()
    print("\n  After:  %d engines, %d wires, chimera %d/100" % (
        after["engines"], after["wires"], after["chimera_score"]))

    # Delta
    delta = {
        "engines": after["engines"] - before["engines"],
        "wires": after["wires"] - before["wires"],
        "army_ok": after["army_ok"] - before["army_ok"],
        "chimera": after["chimera_score"] - before["chimera_score"],
    }
    improved = any(v > 0 for v in delta.values())
    print("  Delta:  engines %+d, wires %+d, army %+d, chimera %+d" % (
        delta["engines"], delta["wires"], delta["army_ok"], delta["chimera"]))
    print("  Improved: %s" % ("YES -- loop continues" if improved else "NO -- stabilized"))

    return before, after, phases, delta, improved


def run():
    print("AUTO GENESIS -- The Self-Starting Perpetual Loop")
    print("=" * 55)

    state = load_json(DATA / "auto_genesis_state.json")
    if not state:
        state = {"total_cycles": 0, "total_improvements": 0, "last_run": None}

    log_entries = []

    for cycle_num in range(1, MAX_CYCLES + 1):
        before, after, phases, delta, improved = run_cycle(cycle_num)

        state["total_cycles"] = state.get("total_cycles", 0) + 1
        if improved:
            state["total_improvements"] = state.get("total_improvements", 0) + 1

        log_entries.append({
            "cycle": cycle_num,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "before": before,
            "after": after,
            "delta": delta,
            "improved": improved,
            "phases": phases,
        })

        if not improved:
            print("\n  System stabilized at cycle %d. No further improvement." % cycle_num)
            break

    # Save state
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["last_metrics"] = after if log_entries else {}
    save_json(DATA / "auto_genesis_state.json", state)

    # Append to log
    log = load_json(DATA / "auto_genesis_log.json")
    if not isinstance(log, dict):
        log = {"runs": []}
    if "runs" not in log:
        log["runs"] = []
    log["runs"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cycles": log_entries,
        "total_cycles_this_run": len(log_entries),
    })
    log["runs"] = log["runs"][-20:]  # keep last 20 runs
    save_json(DATA / "auto_genesis_log.json", log)

    print("\n  === AUTO GENESIS SUMMARY ===")
    print("  Cycles this run: %d" % len(log_entries))
    print("  Total lifetime:  %d cycles, %d improvements" % (
        state["total_cycles"], state["total_improvements"]))
    if log_entries:
        final = log_entries[-1]["after"]
        print("  Final state:     %d engines, %d wires, chimera %d/100" % (
            final["engines"], final["wires"], final["chimera_score"]))
    print("\n  The system births itself. Over and over. Forever.")


if __name__ == "__main__":
    run()
