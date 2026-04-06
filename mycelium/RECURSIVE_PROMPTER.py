import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def run():
    # Read orchestration context
    ctx = json.loads((DATA / "orchestration_queue.json").read_text()) if (DATA / "orchestration_queue.json").exists() else {}

    cmds = [
        "Write-Host '--- SOLARPUNK SINGULARITY: CIRCULAR ECONOMY ACTIVE ---' -ForegroundColor Green",
        "python mycelium/SOLAR_OVERSEER.py",    # Bots monitoring bots
        "python mycelium/EXTERNAL_HANDSHAKE.py",
        "python mycelium/REVENUE_ENGINE.py",
        "python mycelium/REVENUE_RECYCLER.py",  # Reinvesting profit
        "python mycelium/SCAVENGER_WEB.py",
        "python mycelium/SKILL_MANIFESTOR.py",
        "python mycelium/AUTO_ARCHITECT.py",
        "python mycelium/MISSION_CONTROL.py"
    ]
    ps_content = "$cmds = " + str(cmds).replace("[", "@(").replace("]", ")") + "\nforeach ($c in $cmds) { iex $c }"
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print("🌀 Sovereign Architect: CIRCULAR MYCELIUM ONLINE.")

    # Write engine state for LIVE_WIRE detection
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    (DATA / "recursive_prompter_state.json").write_text(json.dumps({
        "last_run": __import__("datetime").datetime.now().isoformat(),
        "status": "completed",
        "commands_generated": len(cmds),
        "nervous_system":{"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)},
    }, indent=2), encoding="utf-8")

if __name__ == '__main__':
    run()
