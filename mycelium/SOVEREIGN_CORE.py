import subprocess
import os
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)


def run_singularity_pulse():
    # Read upstream state
    brain = {}
    brain_path = DATA / "brain_state.json"
    if brain_path.exists():
        try:
            brain = json.loads(brain_path.read_text())
        except Exception:
            pass

    knowledge = {}
    kg_path = DATA / "knowledge_graph.json"
    if kg_path.exists():
        try:
            knowledge = json.loads(kg_path.read_text())
        except Exception:
            pass

    # Priority Order for Total Autonomy
    priority_tasks = [
        'REVENUE_ENGINE.py',   # Make Money
        'SCAVENGER_WEB.py',    # Find New Money Methods
        'SKILL_MANIFESTOR.py', # Fix Gaps in Revenue Code
        'AUTO_ARCHITECT.py'    # Build the Updated System
    ]

    task_results = {}
    for task in priority_tasks:
        path = f'mycelium/{task}'
        if os.path.exists(path):
            try:
                print(f"Singularity: Running {task}...")
                result = subprocess.run(['python', path], check=True,
                                        capture_output=True, text=True, timeout=120)
                task_results[task] = "completed"
            except subprocess.TimeoutExpired:
                task_results[task] = "timeout"
                print(f"Task {task} timed out")
            except Exception as e:
                task_results[task] = f"failed: {e}"
                print(f"Task {task} stalled: {e}")
        else:
            task_results[task] = "not_found"

    # Write state for LIVE_WIRE
    state = {
        "engine": "SOVEREIGN_CORE",
        "ts": datetime.now(timezone.utc).isoformat(),
        "priority_tasks": priority_tasks,
        "task_results": task_results,
        "tasks_completed": sum(1 for v in task_results.values() if v == "completed"),
        "tasks_total": len(priority_tasks),
        "brain_cycle": brain.get("cycle", 0),
        "knowledge_nodes": len(knowledge.get("nodes", [])) if isinstance(knowledge, dict) else 0,
        "status": "active",
    }
    (DATA / "sovereign_core_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"State written: data/sovereign_core_state.json")


if __name__ == "__main__":
    run_singularity_pulse()
