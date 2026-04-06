import json
import os
from datetime import datetime
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def archive_state():
    summary = {
        "date": str(datetime.now()),
        "mission": "Grow SolarPunk autonomously, convert money to energy, support Youth Nodes.",
        "status": "Active",
        "last_actions": "Legal Shield Deployed, Treasury Rebalanced."
    }
    with open("C:/Solarpunk-Prime/docs/AGENCY_MEMORY.md", "a") as f:
        f.write(f"\\n## State Brief: {summary['date']}\\n{summary['mission']}\\n")
    print("SIA: Memory persisted to AGENCY_MEMORY.md")

if __name__ == "__main__":
    archive_state()


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "brain_state.json").read_text()) if (DATA / "brain_state.json").exists() else {}
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    (DATA / "archivist_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired","nervous_system":{"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}}, indent=2), encoding="utf-8")
