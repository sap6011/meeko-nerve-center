import json
from datetime import datetime
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def aggregate_fuel():
    # Simulated connections to your passive loops
    # In a real setup, these would be API calls to your digital credit sources
    streams = {
        "digital_referrals": 15.50,
        "automation_yield": 42.00,
        "surplus_credits": 10.25
    }
    
    total = sum(streams.values())
    
    report = {
        "timestamp": str(datetime.now()),
        "total_fuel": total,
        "allocation": {
            "Agency_Ops": "20%",
            "Youth_Starter_Kits": "80%"
        }
    }
    
    with open('C:/Solarpunk-Prime/vault/community_fund.json', 'w') as f:
        try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
        except: _h={}
        try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
        except: _c={}
        report["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
        json.dump(report, f, indent=4)
    
    print(f"Revenue Pulse:  aggregated and allocated to the Youth Mycelium.")

if __name__ == "__main__":
    aggregate_fuel()


# LIVE_WIRE: topology state tracking
def _write_wire_state():
    _ctx = json.loads((DATA / "revenue_data.json").read_text()) if (DATA / "revenue_data.json").exists() else {}
    (DATA / "revenue_aggregator_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "ok"}, indent=2), encoding="utf-8")
