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
    (DATA / "auto_runner_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired"}, indent=2), encoding="utf-8")
