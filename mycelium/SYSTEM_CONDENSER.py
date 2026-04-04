# NEURAL_LINK: The

# Part of the Meeko SolarPunk Swarm.



import os

import shutil

import time
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)



def condense():

    # 1. Clear Python Caches

    for root, dirs, files in os.walk("."):

        if "__pycache__" in dirs:

            shutil.rmtree(os.path.join(root, "__pycache__"))

            print("🧹 Cleared __pycache__")



    # 2. Clean old logs

    log_dir = "logs"

    if os.path.exists(log_dir):

        now = time.time()

        for f in os.listdir(log_dir):

            f_path = os.path.join(log_dir, f)

            if os.path.getmtime(f_path) < (now - (2 * 86400)): # 2 days

                os.remove(f_path)

                print(f"🗑 Deleted old log: {f}")



if __name__ == "__main__":

    condense()



# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "live_wire_report.json").read_text()) if (DATA / "live_wire_report.json").exists() else {}
    (DATA / "system_condenser_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired"}, indent=2))
