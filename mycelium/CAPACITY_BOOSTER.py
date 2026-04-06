import os
import time
import subprocess
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def get_idle_time():
    # USES Windows 'User32.dll' to find how long since last input
    try:
        from ctypes import Structure, windll, c_uint, sizeof, byref
        class LASTINPUTINFO(Structure):
            _fields_ = [("cbSize", c_uint), ("dwTime", c_uint)]
        
        lii = LASTINPUTINFO()
        lii.cbSize = sizeof(lii)
        windll.user32.GetLastInputInfo(byref(lii))
        millis = windll.kernel32.GetTickCount() - lii.dwTime
        return millis / 1000.0
    except:
        return 0

def regulate_swarm():
    idle_seconds = get_idle_time()
    
    if idle_seconds > 300: # 5 Minutes
        print(f"🌙 System Idle ({int(idle_seconds)}s). Activating TURBO MODE.")
        # Trigger heavy tasks
        os.environ["SWARM_MODE"] = "TURBO"
        # Example: start local LLM or heavy data crunching
    else:
        print("👤 User Active. Throttling Swarm to background priority.")
        os.environ["SWARM_MODE"] = "STEALTH"
        # Lower process priority of other python scripts
        pid = os.getpid()
        os.system(f"wmic process where ProcessId={pid} CALL setpriority 'low priority'")

if __name__ == "__main__":
    regulate_swarm()


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "live_wire_report.json").read_text()) if (DATA / "live_wire_report.json").exists() else {}
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    (DATA / "capacity_booster_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired","nervous_system":{"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}}, indent=2), encoding="utf-8")
