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
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    (DATA / "swarm_scout_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "ok","nervous_system":{"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}}, indent=2), encoding="utf-8")
