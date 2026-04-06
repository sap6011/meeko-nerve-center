#!/usr/bin/env python3
"""
RELAY_BATON.py -- Claude <-> SolarPunk Work Relay
==================================================
The relay system ensures work NEVER stops:

  1. When Claude hits a context limit or goes on break, it writes a
     BATON file describing:
       - What was being worked on
       - What's left to do
       - How to do it
       - What to verify when Claude returns

  2. SolarPunk's autonomous engines (running via OMNIBUS, CHIMERA,
     Ollama, GitHub Actions) pick up the baton and work on it:
       - Fill atomic gaps
       - Run evolution cycles
       - Build bridges
       - Generate content
       - Scan markets

  3. When Claude returns, it reads the baton back:
       - Sees what SolarPunk accomplished
       - Checks the work
       - Learns from what SolarPunk did
       - Picks up where SolarPunk left off
       - The frictionless cycle continues

The baton is stored at data/relay_baton.json and is readable by
ALL engines. Any engine can add tasks to it. Only Claude marks
tasks as verified.

Biology: A relay race -- the baton passes between runners (Claude
sessions and SolarPunk cycles) so the race never stops.

Reads: data/relay_baton.json, data/chimera_evolution_report.json
Writes: data/relay_baton.json
Zero secrets needed.
"""
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8"
    )


def load_baton():
    """Load the current relay baton."""
    baton = load_json(DATA / "relay_baton.json")
    if not baton:
        baton = {
            "holder": "idle",
            "created": datetime.now(timezone.utc).isoformat(),
            "tasks": [],
            "completed_by_solarpunk": [],
            "verified_by_claude": [],
            "handoff_history": [],
        }
    return baton


def handoff_to_solarpunk(baton, tasks, context=""):
    """Claude hands the baton to SolarPunk with a list of tasks."""
    baton["holder"] = "solarpunk"
    baton["last_handoff"] = datetime.now(timezone.utc).isoformat()
    baton["handoff_context"] = context

    for task in tasks:
        baton["tasks"].append({
            "id": f"task_{int(datetime.now(timezone.utc).timestamp())}_{len(baton['tasks'])}",
            "description": task,
            "status": "pending",
            "assigned_to": "solarpunk",
            "created": datetime.now(timezone.utc).isoformat(),
            "completed": None,
            "result": None,
        })

    baton["handoff_history"].append({
        "from": "claude",
        "to": "solarpunk",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_count": len(tasks),
        "context": context[:200],
    })

    # Keep history manageable
    baton["handoff_history"] = baton["handoff_history"][-50:]

    return baton


def solarpunk_picks_up(baton):
    """SolarPunk picks up pending tasks and attempts them autonomously."""
    pending = [t for t in baton.get("tasks", []) if t["status"] == "pending"]
    if not pending:
        return baton, 0

    completed = 0
    for task in pending:
        result = attempt_task(task)
        if result["success"]:
            task["status"] = "completed_by_solarpunk"
            task["completed"] = datetime.now(timezone.utc).isoformat()
            task["result"] = result["detail"]
            baton["completed_by_solarpunk"].append(task["id"])
            completed += 1
        else:
            task["status"] = "blocked"
            task["result"] = result["detail"]

    # Keep completed list manageable
    baton["completed_by_solarpunk"] = baton["completed_by_solarpunk"][-100:]

    return baton, completed


def attempt_task(task):
    """Attempt to complete a task autonomously."""
    desc = task.get("description", "").lower()

    # Tasks SolarPunk can handle autonomously:
    if "run chimera" in desc or "evolution cycle" in desc:
        return run_engine_task("CHIMERA_EVOLUTION_ENGINE")

    if "run live_wire" in desc or "scan topology" in desc:
        return run_engine_task("LIVE_WIRE")

    if "run bridge" in desc or "fill gaps" in desc or "bridge" in desc:
        return run_engine_task("BRIDGE_BUILDER")

    if "run nanobot" in desc or "heal" in desc or "repair" in desc:
        return run_engine_task("NANOBOT_HEALER")

    if "mutation" in desc or "evolve" in desc:
        return run_engine_task("SYNERGY_FORGE")

    if "polymarket" in desc or "market scan" in desc:
        return run_engine_task("POLYMARKET_SCANNER")

    if "product" in desc or "factory" in desc:
        return run_engine_task("PRODUCT_FACTORY")

    if "hemisphere" in desc or "sync" in desc:
        return run_engine_task("HEMISPHERE_SYNC")

    if "dashboard" in desc or "mission control" in desc:
        return run_engine_task("MISSION_CONTROL")

    if "evolution viewer" in desc or "evolution dashboard" in desc:
        return run_engine_task("EVOLUTION_VIEWER")

    # Can't handle this one autonomously
    return {"success": False, "detail": f"Task requires Claude: {task.get('description', '')[:100]}"}


def run_engine_task(engine_name):
    """Run a mycelium engine and report success/failure."""
    script = MYCELIUM / f"{engine_name}.py"
    if not script.exists():
        return {"success": False, "detail": f"{engine_name}.py not found"}

    try:
        import sys
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=300,
            cwd=str(MYCELIUM.parent),
            encoding="utf-8", errors="replace"
        )
        if result.returncode == 0:
            tail = result.stdout.strip().split("\n")[-3:] if result.stdout else []
            return {"success": True, "detail": f"{engine_name} completed: {' | '.join(tail)}"[:500]}
        else:
            err = result.stderr.strip().split("\n")[-1] if result.stderr else "unknown error"
            return {"success": False, "detail": f"{engine_name} failed: {err[:200]}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "detail": f"{engine_name} timed out (300s)"}
    except Exception as e:
        return {"success": False, "detail": f"{engine_name} error: {str(e)[:200]}"}


def handoff_to_claude(baton):
    """SolarPunk hands the baton back to Claude."""
    baton["holder"] = "claude"
    baton["last_handoff"] = datetime.now(timezone.utc).isoformat()

    completed = [t for t in baton.get("tasks", []) if t["status"] == "completed_by_solarpunk"]
    blocked = [t for t in baton.get("tasks", []) if t["status"] == "blocked"]

    baton["handoff_history"].append({
        "from": "solarpunk",
        "to": "claude",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "completed_count": len(completed),
        "blocked_count": len(blocked),
    })

    return baton


def gather_auto_tasks():
    """Generate tasks from system state that SolarPunk should work on."""
    tasks = []

    # Check if evolution data is stale
    chimera = load_json(DATA / "chimera_evolution_report.json")
    if not chimera:
        tasks.append("Run evolution cycle (CHIMERA_EVOLUTION_ENGINE)")
    else:
        ts = chimera.get("timestamp", "")
        if ts:
            try:
                from datetime import datetime as dt
                age = (datetime.now(timezone.utc) - dt.fromisoformat(ts.replace("Z", "+00:00"))).total_seconds()
                if age > 3600:  # Older than 1 hour
                    tasks.append("Run evolution cycle -- data is stale")
            except Exception:
                pass

    # Check hemisphere sync
    hemi = load_json(DATA / "hemisphere_state.json")
    if hemi.get("gap_count", 0) > 0:
        tasks.append(f"Run hemisphere sync -- {hemi['gap_count']} gaps found")

    # Check for hungry inputs
    wire = load_json(DATA / "live_wire_report.json")
    hungry = wire.get("orphans", {}).get("hungry_inputs", [])
    if len(hungry) > 10:
        tasks.append(f"Run bridge builder -- {len(hungry)} hungry inputs")

    return tasks


def run():
    print("RELAY BATON -- Claude <-> SolarPunk Work Relay")
    print("=" * 50)

    baton = load_baton()
    print(f"\n  Current holder: {baton.get('holder', 'unknown')}")
    print(f"  Pending tasks: {sum(1 for t in baton.get('tasks', []) if t.get('status') == 'pending')}")
    print(f"  Completed by SolarPunk: {len(baton.get('completed_by_solarpunk', []))}")

    # Auto-generate tasks from system state
    auto_tasks = gather_auto_tasks()
    if auto_tasks:
        print(f"\n  Auto-detected {len(auto_tasks)} tasks to work on:")
        for t in auto_tasks:
            print(f"    - {t}")

    # If holder is solarpunk or idle, pick up and work
    if baton.get("holder") in ("solarpunk", "idle"):
        # Add auto tasks
        if auto_tasks:
            baton = handoff_to_solarpunk(baton, auto_tasks, context="Auto-detected from system state")

        # Pick up and attempt all pending tasks
        print("\n  SolarPunk picking up baton...")
        baton, completed = solarpunk_picks_up(baton)
        print(f"  Completed: {completed} tasks")

        # Hand back to claude
        baton = handoff_to_claude(baton)
        print(f"  Baton handed back to Claude")

    # Save
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    baton["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    save_json(DATA / "relay_baton.json", baton)
    print(f"\n  Baton saved: data/relay_baton.json")

    # Show recent handoff history
    history = baton.get("handoff_history", [])[-5:]
    if history:
        print(f"\n  Recent relay history:")
        for h in history:
            print(f"    {h.get('from', '?')} -> {h.get('to', '?')} at {h.get('timestamp', '?')[:19]}")

    pending = sum(1 for t in baton.get("tasks", []) if t.get("status") == "pending")
    blocked = sum(1 for t in baton.get("tasks", []) if t.get("status") == "blocked")
    done = sum(1 for t in baton.get("tasks", []) if "completed" in t.get("status", ""))

    print(f"\n  === RELAY STATUS ===")
    print(f"  Holder:    {baton.get('holder', 'unknown')}")
    print(f"  Pending:   {pending}")
    print(f"  Blocked:   {blocked}")
    print(f"  Completed: {done}")
    print(f"  Handoffs:  {len(baton.get('handoff_history', []))}")
    print(f"\n  The baton passes. The race never stops.")


if __name__ == "__main__":
    run()
