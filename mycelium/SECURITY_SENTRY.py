import re
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def audit_code(code, context="Scavenged"):
    # High-risk patterns that could compromise the host
    blacklist = [
        r"os\.system\(['\"]rm ", r"shutil\.rmtree", r"os\.remove\(['\"]C:\\Windows", 
        r"format ", r"subprocess\.run\(['\"]powershell", r"registry", r"socket\.bind"
    ]
    
    for pattern in blacklist:
        if re.search(pattern, code, re.IGNORECASE):
            print(f"⚠️ SECURITY ALERT: Blocked {context} code containing pattern: {pattern}")
            return False, pattern
            
    return True, "Safe"

if __name__ == "__main__":
    print("🛡️ Security Sentry: Active and auditing buffers.")


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "sentinel_report.json").read_text()) if (DATA / "sentinel_report.json").exists() else {}
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    (DATA / "security_sentry_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired","nervous_system":{"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}}, indent=2), encoding="utf-8")
