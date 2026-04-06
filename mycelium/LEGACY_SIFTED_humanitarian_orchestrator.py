"""
HUMANITARIAN ORCHESTRATOR - PAUSED MODE
Waiting for 501(c)(3) status. No funds are being transferred.
"""
import json
import logging
from datetime import datetime
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)


def run():
    """Main entry point with data I/O wiring."""
    humanitarian_state = json.loads((DATA / "humanitarian_state.json").read_text()) if (DATA / "humanitarian_state.json").exists() else {}

    print(" HUMANITARIAN SYSTEM - PAUSED")
    print("="*50)
    print("Status: Waiting for EIN and 501(c)(3) approval")
    print("No funds are being transferred to any crisis zone.")
    print("All revenue continues to be generated normally.")
    print("="*50)

    # Log that system is paused
    import os
    os.makedirs("humanitarian_logs", exist_ok=True)
    with open("humanitarian_logs/system_paused.log", "a") as f:
        f.write(f"{datetime.now()} - System paused. Waiting for nonprofit status.\n")

    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    (DATA / "legacy_sifted_humanitarian_orchestrator_state.json").write_text(json.dumps({"last_run": datetime.now().isoformat(), "status": "ok", "mode": "paused","nervous_system":{"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    run()
