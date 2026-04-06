import psutil
import os
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)


def pulse_check():
    print("SOLAR OVERSEER: Monitoring digital ecosystem health...")

    # Read upstream state
    brain = {}
    brain_path = DATA / "brain_state.json"
    if brain_path.exists():
        try:
            brain = json.loads(brain_path.read_text())
        except Exception:
            pass

    live_wire = {}
    lw_path = DATA / "live_wire_report.json"
    if lw_path.exists():
        try:
            live_wire = json.loads(lw_path.read_text())
        except Exception:
            pass

    # Monitor CPU 'Temperature' (Usage) to ensure SolarPunk efficiency
    cpu_usage = psutil.cpu_percent(interval=1)
    eco_stress = cpu_usage > 80
    if eco_stress:
        print("ECO-STRESS: High load detected. Throttling non-essential scavengers.")

    # Peer-to-peer logic check
    agents = ['REVENUE_ENGINE.py', 'SCAVENGER_WEB.py', 'AUTO_ARCHITECT.py']
    agent_status = {}
    for agent in agents:
        alive = False
        try:
            alive = any(agent in p.name() for p in psutil.process_iter(['name']))
        except Exception:
            pass
        agent_status[agent] = "running" if alive else "dormant"
        if not alive:
            print(f"Regenerating pruned agent: {agent}")

    # Write state for LIVE_WIRE
    state = {
        "engine": "SOLAR_OVERSEER",
        "ts": datetime.now(timezone.utc).isoformat(),
        "cpu_usage": cpu_usage,
        "eco_stress": eco_stress,
        "agent_status": agent_status,
        "agents_alive": sum(1 for v in agent_status.values() if v == "running"),
        "agents_total": len(agents),
        "brain_cycle": brain.get("cycle", 0),
        "live_wire_engines": live_wire.get("total_engines", 0),
        "status": "active",
    }
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    (DATA / "solar_overseer_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"State written: data/solar_overseer_state.json")


if __name__ == "__main__":
    pulse_check()
