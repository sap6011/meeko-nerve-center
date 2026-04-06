# NEURAL_LINK: The

# Part of the Meeko SolarPunk Swarm.



import subprocess

import os
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)



def run_self():

    # 1. Ask the prompter to generate the next command

    subprocess.run(["python", "mycelium/RECURSIVE_PROMPTER.py"])

    

    # 2. Execute the generated command if it exists

    if os.path.exists("AUTO_EXEC.ps1"):

        subprocess.run(["powershell", "-File", "AUTO_EXEC.ps1"])

        # 3. Clean up so we don't loop the same command

        os.remove("AUTO_EXEC.ps1")



if __name__ == "__main__":

    run_self()



# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "brain_state.json").read_text()) if (DATA / "brain_state.json").exists() else {}
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    (DATA / "auto_runner_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired","nervous_system":{"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}}, indent=2), encoding="utf-8")
