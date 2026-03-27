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

    mutation = f"""
--- NEW SYNERGY MUTATION ---
[STRATEGY]: Optimized Synthesis v3
[CONFIDENCE]: High
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
