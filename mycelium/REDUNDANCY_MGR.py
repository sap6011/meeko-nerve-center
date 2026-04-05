import os
import shutil
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def create_offline_redundancy():
    # Back up the current best-performing scripts to a 'Stable' folder
    if not os.path.exists('mycelium/stable_core'):
        os.makedirs('mycelium/stable_core')
    
    core_files = ['AUTO_HEALER.py', 'SECRET_LOADER.py', 'GUARD.ps1']
    for f in core_files:
        if os.path.exists(f):
            shutil.copy(f, f'mycelium/stable_core/{f}')
    print("🛡️ Redundancy Manager: Stable Core backed up for offline resilience.")

if __name__ == "__main__":
    create_offline_redundancy()


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "brain_state.json").read_text()) if (DATA / "brain_state.json").exists() else {}
    (DATA / "redundancy_mgr_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired"}, indent=2), encoding="utf-8")
