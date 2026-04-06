import os
import json
import sys
sys.path.insert(0, os.path.dirname(__file__))

def forge_smart_mutation():
    """Use SWARM_TOOLBOX v3 registry to build smarter mutations."""
    try:
        from SWARM_TOOLBOX import viable_skills, list_engines
    except ImportError:
        print("SYNERGY_FORGE: SWARM_TOOLBOX not available")
        return

    skills = viable_skills(max_failures=3)
    engines = list_engines()

    # Read nervous system health for mutation context
    try:
        _h = json.loads(open('data/homeostasis_state.json', encoding='utf-8').read())
        eq = _h.get("equilibrium", 0)
        trend = _h.get("trend", "unknown")
    except Exception:
        eq, trend = 0, "unknown"

    mutation = f"""
--- NEW SYNERGY MUTATION ---
[STRATEGY]: Optimized Synthesis v3
[CONFIDENCE]: High
[NERVOUS_SYSTEM]: equilibrium={eq}, trend={trend}
[REASONING]: {len(engines)} engines scanned, {len(skills)} viable skills found.
"""
    for skill in skills[:10]:
        mutation += f"[SKILL]: def {skill}\n"

    os.makedirs("data", exist_ok=True)
    with open('data/synergy_mutations.txt', 'a', encoding='utf-8') as f:
        f.write(mutation)
    print(f"Forge: Mutation built from {len(skills)} viable skills across {len(engines)} engines.")

if __name__ == "__main__":
    forge_smart_mutation()
