import json
import os
from datetime import datetime
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)


def run():
    # Read brain state for daily context
    ctx = json.loads((DATA / "brain_state.json").read_text()) if (DATA / "brain_state.json").exists() else {}

    print("--- Generating Solarpunk Daily Pulse Report ---")
    intel_path = DATA / "harvested_knowledge.json"
    draft_path = DATA / "active_outreach_draft.json"

    summary = {
        "date": str(datetime.now().date()),
        "nodes_scouted": 0,
        "high_value_opportunities": [],
        "outreach_ready": False
    }

    if intel_path.exists():
        data = json.loads(intel_path.read_text())
        if isinstance(data, list):
            summary["nodes_scouted"] = len(data)
            summary["high_value_opportunities"] = [
                i['title'] for i in data if i.get('category') in ['GRANT', 'LEGAL']
            ]

    if draft_path.exists():
        summary["outreach_ready"] = True

    # Save pulse report
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    summary["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    (DATA / f"pulse_{summary['date']}.json").write_text(json.dumps(summary, indent=4), encoding="utf-8")

    print(f"Report Generated: {summary['nodes_scouted']} nodes found today.")
    if summary["outreach_ready"]:
        print("Outreach Nanobots: DRAFTS PREPARED AND READY FOR REVIEW.")

    # Write engine state for LIVE_WIRE detection
    (DATA / "daily_pulse_state.json").write_text(json.dumps({
        "last_run": datetime.now().isoformat(),
        "status": "completed",
        "nodes_scouted": summary["nodes_scouted"],
        "opportunities": len(summary["high_value_opportunities"])
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    run()
