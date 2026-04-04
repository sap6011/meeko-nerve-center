#!/usr/bin/env python3
"""
AUTO_EXECUTOR.py -- Execute Autonomous Tasks Without Human Input
=================================================================
Reads the task queue from TASK_FACTORY and executes every task
marked as autonomous=True. This is the hands-off loop:

  TASK_FACTORY generates tasks -> AUTO_EXECUTOR runs them
  -> results feed back into system state -> TASK_FACTORY
  generates new tasks based on results -> AUTO_EXECUTOR
  runs those -> forever

The cycle:
  1. Read task_queue.json
  2. Filter for autonomous=True tasks
  3. Sort by priority (P1 first)
  4. Execute each task's command
  5. Log results
  6. Re-run TASK_FACTORY to generate follow-up tasks

No API keys. No human input. Just files and Python.

Reads: data/task_queue.json, data/auto_executor_state.json
Writes: data/auto_executor_state.json, data/auto_executor_log.json
"""
import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

TASK_TIMEOUT = 120  # seconds per task
MAX_TASKS_PER_RUN = 10  # don't overwhelm the machine


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


def execute_command(command, timeout=TASK_TIMEOUT):
    """Execute a shell command and return results."""
    start = time.time()
    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        # Handle compound commands (&&)
        if "&&" in command:
            parts = [p.strip() for p in command.split("&&")]
        else:
            parts = [command]

        all_output = []
        all_ok = True

        for part in parts:
            if part.startswith("#"):
                # Comment, skip
                continue
            if part.startswith("python "):
                script = part.replace("python ", "")
                result = subprocess.run(
                    [sys.executable, script],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(Path.cwd()),
                    env=env,
                    errors="replace",
                )
                output_lines = [l for l in result.stdout.split("\n") if l.strip()]
                all_output.extend(output_lines[-3:])
                if result.returncode != 0:
                    all_ok = False
                    if result.stderr:
                        all_output.append("STDERR: %s" % result.stderr[:100])

        elapsed = time.time() - start
        return {
            "status": "OK" if all_ok else "FAIL",
            "elapsed": round(elapsed, 1),
            "output": "\n".join(all_output[-5:]),
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "elapsed": timeout,
            "output": "Timed out after %ds" % timeout,
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "elapsed": time.time() - start,
            "output": str(e)[:200],
        }


def run():
    print("AUTO EXECUTOR -- Autonomous Task Runner")
    print("=" * 50)

    state = load_json(DATA / "auto_executor_state.json")
    if not state:
        state = {"runs": 0, "tasks_completed": 0, "tasks_failed": 0, "last_run": None}

    # Load task queue
    print("\n  [1/4] Loading task queue...")
    queue = load_json(DATA / "task_queue.json")
    all_tasks = queue.get("tasks", [])
    print("    Total tasks: %d" % len(all_tasks))

    # Filter autonomous tasks
    auto_tasks = [t for t in all_tasks if t.get("autonomous")]
    auto_tasks.sort(key=lambda t: t.get("priority", 5))
    print("    Autonomous:  %d" % len(auto_tasks))

    if not auto_tasks:
        print("    No autonomous tasks to execute. Run TASK_FACTORY first.")
        state["last_run"] = datetime.now(timezone.utc).isoformat()
        save_json(DATA / "auto_executor_state.json", state)
        return

    # Limit batch
    batch = auto_tasks[:MAX_TASKS_PER_RUN]
    print("    Batch size:  %d" % len(batch))

    # Execute
    print("\n  [2/4] Executing autonomous tasks...")
    results = []
    ok_count = 0
    fail_count = 0

    for i, task in enumerate(batch):
        title = task.get("title", "unknown")
        command = task.get("command", "")
        priority = task.get("priority", 5)

        if command.startswith("#") or not command:
            print("    [%d/%d] SKIP P%d %s (no executable command)" % (
                i + 1, len(batch), priority, title[:50]))
            continue

        print("    [%d/%d] P%d %s" % (i + 1, len(batch), priority, title[:50]))
        print("           cmd: %s" % command[:60])

        r = execute_command(command)

        if r["status"] == "OK":
            ok_count += 1
            print("           -> OK (%.1fs)" % r["elapsed"])
        else:
            fail_count += 1
            print("           -> %s (%.1fs) %s" % (r["status"], r["elapsed"], r["output"][:60]))

        results.append({
            "task": title,
            "type": task.get("type", ""),
            "priority": priority,
            "command": command,
            "status": r["status"],
            "elapsed": r["elapsed"],
            "output": r["output"][:500],
            "executed_at": datetime.now(timezone.utc).isoformat(),
        })

    # Re-generate tasks based on new state
    print("\n  [3/4] Regenerating task queue from new state...")
    regen = execute_command("python mycelium/TASK_FACTORY.py", timeout=30)
    print("    Task factory: %s" % regen["status"])

    # Save
    print("\n  [4/4] Saving execution log...")
    state["runs"] = state.get("runs", 0) + 1
    state["tasks_completed"] = state.get("tasks_completed", 0) + ok_count
    state["tasks_failed"] = state.get("tasks_failed", 0) + fail_count
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["last_batch"] = len(batch)
    state["last_ok"] = ok_count
    state["last_fail"] = fail_count
    save_json(DATA / "auto_executor_state.json", state)

    # Append to execution log
    log = load_json(DATA / "auto_executor_log.json")
    if not isinstance(log, dict):
        log = {"executions": []}
    if "executions" not in log:
        log["executions"] = []
    log["executions"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "batch_size": len(batch),
        "ok": ok_count,
        "fail": fail_count,
        "results": results,
    })
    log["executions"] = log["executions"][-50:]  # keep last 50 runs
    save_json(DATA / "auto_executor_log.json", log)

    print("\n  === AUTO EXECUTOR SUMMARY ===")
    print("  Tasks executed: %d" % len(batch))
    print("  OK:             %d" % ok_count)
    print("  FAIL:           %d" % fail_count)
    print("  Total lifetime: %d completed, %d failed" % (
        state["tasks_completed"], state["tasks_failed"]))
    print("\n  No keys. No humans. Just execute.")


if __name__ == "__main__":
    run()
