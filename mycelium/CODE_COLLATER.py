import os
import re
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def collate_legacy_logic():
    """DISABLED: SWARM_TOOLBOX v3 is now a clean engine registry.
    CODE_COLLATER's regex-based extraction produced broken triple-quote
    cascades in the 8000-line output. The new SWARM_TOOLBOX uses AST
    parsing to build a live registry instead of concatenating raw code.
    """
    print("CODE_COLLATER: Disabled. SWARM_TOOLBOX v3 uses AST-based registry now.")
    print("  Run: python mycelium/SWARM_TOOLBOX.py  to update the registry.")

if __name__ == "__main__":
    collate_legacy_logic()


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "live_wire_report.json").read_text()) if (DATA / "live_wire_report.json").exists() else {}
    (DATA / "code_collater_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired"}, indent=2), encoding="utf-8")
