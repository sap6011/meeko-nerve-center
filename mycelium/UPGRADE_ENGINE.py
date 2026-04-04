import os
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def check_for_upgrades():
    # If the system detects a 401 Unauthorized or 'API Missing' in logs
    log_path = 'logs/heartbeat.log'
    if not os.path.exists(log_path): return

    with open(log_path, 'r') as f:
        logs = f.read()

    if "API Missing" in logs or "Revoked" in logs:
        print("🔧 Upgrade Engine: API failure detected. Attempting to pivot to Open Source alternative...")
        # Here the AI would trigger the ARCHITECT to rewrite the broken script
        # to use a local library instead of a paid API.
        os.system("python mycelium/AUTO_ARCHITECT.py")

if __name__ == "__main__":
    check_for_upgrades()


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "live_wire_report.json").read_text()) if (DATA / "live_wire_report.json").exists() else {}
    (DATA / "upgrade_engine_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired"}, indent=2))
