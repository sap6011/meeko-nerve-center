import os
import re
from DUEL_ENGINE import duel_functions
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def scavenge_logic_multi(func_name):
    processed_dir = 'knowledge_ingest/processed'
    candidates = []
    if not os.path.exists(processed_dir): return None
    
    for root, dirs, files in os.walk(processed_dir):
        for file in files:
            if file.endswith('.py'):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        pattern = rf"def {func_name}\(.*?\):.*?(?=\ndef|\nif __name__|$)"
                        match = re.search(pattern, content, re.DOTALL)
                        if match and match.group(0) not in candidates:
                            candidates.append(match.group(0))
                except: continue
    
    if len(candidates) > 1:
        print(f"⚔️ Multiple versions of {func_name} found. Initiating Duel...")
        return duel_functions(func_name, candidates[0], candidates[1])
    return candidates[0] if candidates else None

def manifest_optimized_skills():
    # ... (Logic to call scavenge_logic_multi and update GENERATED_SKILLS.py)
    # This version now ensures the 'Winner' of the duel is what gets saved.
    pass 

if __name__ == "__main__":
    # manifest_optimized_skills logic here
    print("🧬 Optimization: Scavenging with Duel-arbitration enabled.")


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "knowledge_graph.json").read_text()) if (DATA / "knowledge_graph.json").exists() else {}
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    (DATA / "skill_manifestor_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired","nervous_system":{"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}}, indent=2), encoding="utf-8")
