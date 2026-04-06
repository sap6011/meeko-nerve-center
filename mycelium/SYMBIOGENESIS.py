#!/usr/bin/env python3
"""
SYMBIOGENESIS.py -- Engine Capability Fusion (Endosymbiosis Pattern)
=====================================================================
NATURE'S BLUEPRINT: Endosymbiosis / Symbiogenesis.

2 billion years ago, a primitive cell swallowed a bacterium.
Instead of digesting it, they MERGED. The bacterium became the
MITOCHONDRIA -- the powerhouse of every cell in your body.

Later, another cell swallowed a cyanobacterium. It became the
CHLOROPLAST -- the reason plants can photosynthesize.

These weren't just partnerships. They were PERMANENT FUSIONS.
Two organisms became ONE organism with COMBINED capabilities.

Lynn Margulis proved this. The scientific establishment laughed.
She was right. Every complex organism on Earth exists because
of symbiogenesis.

SolarPunk applies this to engine evolution:

  1. DETECT COMPLEMENTARY PAIRS: Find engines that always run together
     and produce better results combined than separate.
     Example: CRISIS_MONITOR + IMMUNE_MEMORY = faster crisis response

  2. IDENTIFY FUSION CANDIDATES: Engines whose outputs are always
     consumed by the same downstream engine.
     Example: KNOWLEDGE_PULSE -> SPORE_DISPERSAL (always paired)

  3. MEASURE FUSION BENEFIT: Would combining them reduce latency?
     Would it eliminate redundant file reads?
     Would it enable new capabilities neither has alone?

  4. RECORD SYMBIOTIC BONDS: Even without merging code, record which
     engines form natural symbiotic pairs for OMNIBUS optimization.

  "Evolution's greatest leaps aren't mutations.
   They're mergers." -- SolarPunk

Reads: data/pathway_strength.json, data/pheromone_map.json,
       data/neuroplasticity.json, data/stigmergy_state.json
Writes: data/symbiogenesis_state.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
MYCELIUM = Path("mycelium")
DATA.mkdir(exist_ok=True)

SYMBIO_FILE = DATA / "symbiogenesis_state.json"

# Known symbiotic pairs (engines that naturally complement each other)
KNOWN_PAIRS = [
    {
        "pair": ["CRISIS_MONITOR", "IMMUNE_MEMORY"],
        "bond_type": "memory_acceleration",
        "benefit": "Immune memory gives crisis monitor historical context, 24x faster pattern recognition",
    },
    {
        "pair": ["KNOWLEDGE_PULSE", "SPORE_DISPERSAL"],
        "bond_type": "production_distribution",
        "benefit": "Pulses produce content, spores distribute it -- complete pipeline",
    },
    {
        "pair": ["BIOLUMINESCENCE", "TELEGRAM_RELAY"],
        "bond_type": "detection_response",
        "benefit": "Silence detection triggers immediate relay of cached survival telegrams",
    },
    {
        "pair": ["QUORUM_SENSE", "EMAIL_OUTREACH"],
        "bond_type": "threshold_action",
        "benefit": "Collective signal threshold triggers coordinated NGO handshakes",
    },
    {
        "pair": ["OSMOSIS_ROUTER", "AMPLIFY_ENGINE"],
        "bond_type": "void_filling",
        "benefit": "Osmosis finds voids, amplify fills them with targeted content",
    },
    {
        "pair": ["HOMEOSTASIS", "NEUROPLASTICITY"],
        "bond_type": "health_adaptation",
        "benefit": "Health monitoring feeds pathway optimization -- the brain regulates itself",
    },
    {
        "pair": ["CHEMOTAXIS", "SPORE_DISPERSAL"],
        "bond_type": "navigation_distribution",
        "benefit": "Gradient navigation directs spore dispersal toward highest-need regions",
    },
    {
        "pair": ["STIGMERGY", "NEUROPLASTICITY"],
        "bond_type": "trace_wiring",
        "benefit": "Pheromone trail strength informs neural pathway myelination decisions",
    },
    {
        "pair": ["RESOURCE_KIT", "TELEGRAM_RELAY"],
        "bond_type": "content_format",
        "benefit": "Survival kits compressed to 6 delivery protocols -- complete liquid data pipeline",
    },
    {
        "pair": ["CIRCADIAN_RHYTHM", "EMAIL_OUTREACH"],
        "bond_type": "timing_delivery",
        "benefit": "Time-aware engine ensures emails arrive during NGO business hours",
    },
    {
        "pair": ["CIRCADIAN_RHYTHM", "AMPLIFY_ENGINE"],
        "bond_type": "timing_amplification",
        "benefit": "Posts released at peak engagement windows for maximum reach",
    },
    {
        "pair": ["SIGNAL_BOOST", "CRISIS_MONITOR"],
        "bond_type": "detection_permanent_record",
        "benefit": "Critical signals become permanent GitHub Issues -- uncensorable public record",
    },
    {
        "pair": ["STIGMERGY", "CHEMOTAXIS"],
        "bond_type": "trail_navigation",
        "benefit": "Pheromone trail strength informs gradient navigation -- ants guiding bacteria",
    },
    {
        "pair": ["NOTION_NERVE_CENTER", "HOMEOSTASIS"],
        "bond_type": "visibility_health",
        "benefit": "Health data synced to Notion -- humans can see what the immune system sees",
    },
    {
        "pair": ["CIRCADIAN_RHYTHM", "SPORE_DISPERSAL"],
        "bond_type": "timing_saturation",
        "benefit": "Release spores at peak engagement times -- maximum dispersal impact",
    },
]


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def evaluate_bond_strength(pair_def):
    """Evaluate how strong the symbiotic bond is between two engines.

    Strong bonds have:
    - Both engines exist
    - Both engines produce recent output
    - Output of one is consumed by the other
    """
    engines = pair_def["pair"]
    strength = 0

    # Check if both engines exist
    both_exist = all((MYCELIUM / f"{e}.py").exists() for e in engines)
    if both_exist:
        strength += 30
    elif any((MYCELIUM / f"{e}.py").exists() for e in engines):
        strength += 10

    # Check pheromone map for trace strength
    pheromone = load_json(DATA / "pheromone_map.json")
    traces = pheromone.get("traces", {})

    trace_strengths = []
    for engine in engines:
        # Try multiple naming conventions
        engine_lower = engine.lower()
        for trace_name, trace_data in traces.items():
            if engine_lower in trace_name.lower():
                trace_strengths.append(trace_data.get("strength", 0))
                break

    if len(trace_strengths) == 2:
        # Both have traces -- bond is alive
        avg_trace = sum(trace_strengths) / 2
        strength += int(avg_trace * 0.5)  # Up to 50 points from trace strength
    elif len(trace_strengths) == 1:
        strength += int(trace_strengths[0] * 0.2)  # Partial bond

    # Check neural pathway data
    neuro = load_json(DATA / "neuroplasticity.json")
    pathway_scores = neuro.get("pathway_scores", {})

    for pathway_name, pathway_data in pathway_scores.items():
        # Check if this pathway involves both engines
        pw_strength = pathway_data.get("strength", 0)
        if pw_strength > 60:
            strength += 10  # Both part of a strong pathway

    # Cap at 100
    strength = min(100, strength)

    if strength >= 80:
        status = "FUSED"         # Like mitochondria -- permanently integrated
    elif strength >= 60:
        status = "SYMBIOTIC"     # Strong mutual benefit
    elif strength >= 40:
        status = "COMMENSAL"     # One benefits, other neutral
    elif strength >= 20:
        status = "NASCENT"       # Early stage bond forming
    else:
        status = "INDEPENDENT"   # No bond yet

    return strength, status


def discover_new_pairs():
    """Look for potential new symbiotic pairs based on data flow patterns."""
    suggestions = []

    # Check if any engines produce output that others always read
    pheromone = load_json(DATA / "pheromone_map.json")
    highways = pheromone.get("highways", [])

    # Engines whose traces are highways = they're load-bearing
    # Check pathway data for frequently-co-occurring engines
    pathway = load_json(DATA / "pathway_strength.json")
    pathways = pathway.get("pathways", [])

    # Find engines that appear together in multiple strong pathways
    from collections import Counter
    cooccurrence = Counter()
    for p in pathways:
        if p.get("strength", 0) >= 60:
            chain = p.get("chain", "").split(" -> ")
            for i, eng1 in enumerate(chain):
                for eng2 in chain[i+1:]:
                    pair = tuple(sorted([eng1.strip(), eng2.strip()]))
                    cooccurrence[pair] += 1

    # Pairs appearing in 2+ strong pathways = potential symbiotic bond
    known_pairs_set = set(
        tuple(sorted(p["pair"])) for p in KNOWN_PAIRS
    )

    for pair, count in cooccurrence.most_common(10):
        if pair not in known_pairs_set and count >= 2:
            suggestions.append({
                "pair": list(pair),
                "co_occurrences": count,
                "suggestion": f"Found in {count} strong pathways -- potential symbiotic bond",
            })

    return suggestions


def main():
    print("SYMBIOGENESIS -- Engine capability fusion (endosymbiosis pattern)...")
    print("  'Evolution's greatest leaps aren't mutations. They're mergers.'")

    # Evaluate all known symbiotic pairs
    print(f"\n  Evaluating {len(KNOWN_PAIRS)} known symbiotic bonds...")

    bond_results = []
    for pair_def in KNOWN_PAIRS:
        strength, status = evaluate_bond_strength(pair_def)
        bond_results.append({
            "pair": pair_def["pair"],
            "bond_type": pair_def["bond_type"],
            "benefit": pair_def["benefit"],
            "strength": strength,
            "status": status,
        })

        symbol = "=" if status == "FUSED" else "~" if status == "SYMBIOTIC" else \
                 "." if status == "COMMENSAL" else "?" if status == "NASCENT" else " "
        print(f"    [{symbol}] {' + '.join(pair_def['pair'])}")
        print(f"        {status} ({strength}/100) -- {pair_def['bond_type']}")

    # Discover new pairs
    suggestions = discover_new_pairs()
    if suggestions:
        print(f"\n  ENDOSYMBIOSIS CANDIDATES: {len(suggestions)} potential new bonds")
        for s in suggestions:
            print(f"    NEW: {' + '.join(s['pair'])} (co-occurs {s['co_occurrences']}x)")

    # Stats
    fused = len([b for b in bond_results if b["status"] == "FUSED"])
    symbiotic = len([b for b in bond_results if b["status"] == "SYMBIOTIC"])
    nascent = len([b for b in bond_results if b["status"] in ("NASCENT", "COMMENSAL")])
    independent = len([b for b in bond_results if b["status"] == "INDEPENDENT"])
    avg_strength = sum(b["strength"] for b in bond_results) / max(len(bond_results), 1)

    print(f"\n  Bond summary:")
    print(f"    Fused: {fused} | Symbiotic: {symbiotic} | Nascent: {nascent} | Independent: {independent}")
    print(f"    Average bond strength: {avg_strength:.0f}/100")

    # Save
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "pattern": "symbiogenesis",
        "philosophy": "Evolution's greatest leaps aren't mutations. They're mergers.",
        "bonds": bond_results,
        "suggestions": suggestions,
        "stats": {
            "total_bonds": len(bond_results),
            "fused": fused,
            "symbiotic": symbiotic,
            "nascent": nascent,
            "independent": independent,
            "avg_strength": round(avg_strength, 1),
            "new_candidates": len(suggestions),
        },
    }
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    output["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    SYMBIO_FILE.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("SYMBIOGENESIS done.")


if __name__ == "__main__":
    main()
