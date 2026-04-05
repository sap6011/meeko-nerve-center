import subprocess
import threading
import sys
from pathlib import Path
import json

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def agent_task(name, query):
    print(f"[AGENT: {name}] Initializing hunt for: {query}")
    # Launching the base scout as a sub-process
    subprocess.run(["python", "C:/Solarpunk-Prime/mycelium/scout_bot.py", query])

if __name__ == '__main__':
    targets = [
        ("GRANT_SEEKER", "2026 solarpunk grants"),
        ("HARDWARE_HUNTER", "open source hardware bounties"),
        ("LEGAL_SHIELD", "DAO legal precedents 2026")
    ]
    threads = []
    for name, query in targets:
        t = threading.Thread(target=agent_task, args=(name, query))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    print("--- SWARM COMPLETE: ALL INTELLIGENCE SYNCED ---")


# LIVE_WIRE: topology state tracking
def _write_wire_state():
    _ctx = json.loads((DATA / "brain_state.json").read_text()) if (DATA / "brain_state.json").exists() else {}
    (DATA / "swarm_scout_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "ok"}, indent=2), encoding="utf-8")
