# NEURAL_LINK: Wisdom
# Part of the Meeko SolarPunk Swarm.

import os
import sys
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def check_intent():
    if not os.path.exists('AUTO_EXEC.ps1'): return
    with open('AUTO_EXEC.ps1', 'r', encoding='utf-8') as f:
        content = f.read()
    if 'while(true)' in content:
        sys.exit(1)
    print('✅ Command Vetted.')

if __name__ == '__main__':
    check_intent()


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "sentinel_report.json").read_text()) if (DATA / "sentinel_report.json").exists() else {}
    (DATA / "guardian_gatekeeper_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired"}, indent=2), encoding="utf-8")
