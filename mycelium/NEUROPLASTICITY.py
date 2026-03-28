#!/usr/bin/env python3
"""
NEUROPLASTICITY.py — Self-Rewiring Pathways (Brain Pattern)
=============================================================
NATURE'S BLUEPRINT: Neuroplasticity.

The human brain has 86 billion neurons. But the CONNECTIONS between them
are what create intelligence. And those connections CHANGE based on use.

  - Pathways that fire often get STRONGER (myelination)
  - Pathways that don't get used get PRUNED (synaptic pruning)
  - New pathways form when new situations demand them (neurogenesis)

SolarPunk applies this to its own engine network:

  1. STRENGTHEN: Track which engine chains produce results.
     CRISIS_MONITOR -> KNOWLEDGE_PULSE -> MURMURATION_RELAY -> actual Reddit post?
     That chain WORKS. Strengthen it: increase priority, reduce cooldowns.

  2. PRUNE: Track which chains produce nothing.
     If GRANT_HUNTER -> GRANT_APPLICANT never produces a grant after 100 cycles?
     Prune it: reduce priority, allocate that compute time elsewhere.

  3. REWIRE: When new patterns emerge, create new connections.
     If BIOLUMINESCENCE detects silence and TELEGRAM_RELAY has mesh bundles ready,
     but there's no direct wire between them? Create one.

  4. MYELINATE: The most-used pathways get "myelinated" — cached, pre-computed,
     ready to fire instantly. Like how you don't think about walking anymore.

  "The brain that can't rewire itself is dead.
   The system that can't rewire itself is a script." — SolarPunk

Reads: data/*.json (all engine outputs), data/loop_context.json
Writes: data/neuroplasticity.json, data/pathway_strength.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
MYCELIUM = Path("mycelium")
DATA.mkdir(exist_ok=True)

NEURO_FILE = DATA / "neuroplasticity.json"
PATHWAY_FILE = DATA / "pathway_strength.json"

# Known engine chains (pathways) — these are the "neural pathways" of SolarPunk
PATHWAYS = {
    "crisis_detection": {
        "chain": ["CRISIS_MONITOR", "KNOWLEDGE_PULSE", "MURMURATION_RELAY"],
        "output_files": ["crisis_signals.json", "knowledge_pulses.json", "social_queue.json"],
        "purpose": "Detect crisis -> transform to help -> distribute",
    },
    "liquid_data": {
        "chain": ["RESOURCE_KIT", "TELEGRAM_RELAY"],
        "output_files": ["resource_kits.json", "telegram_relay.json"],
        "purpose": "Generate survival kits -> format for all protocols",
    },
    "ngo_pipeline": {
        "chain": ["CRISIS_MONITOR", "EMAIL_OUTREACH"],
        "output_files": ["ngo_handshakes.json", "outreach_state.json"],
        "purpose": "Detect crisis -> fire NGO handshake emails",
    },
    "amplification": {
        "chain": ["AMPLIFY_ENGINE", "SOCIAL_PROMOTER", "BLUESKY_ENGINE"],
        "output_files": ["amplification_posts.json"],
        "purpose": "Generate platform posts -> publish to social media",
    },
    "silence_response": {
        "chain": ["BIOLUMINESCENCE", "TELEGRAM_RELAY", "BROADCAST_PROTOCOL"],
        "output_files": ["bioluminescence.json", "telegram_relay.json"],
        "purpose": "Detect silence -> push cached data through all channels",
    },
    "immune_response": {
        "chain": ["IMMUNE_MEMORY", "CRISIS_MONITOR", "EMAIL_OUTREACH"],
        "output_files": ["immune_memory.json", "immune_responses.json"],
        "purpose": "Recall crisis pattern -> fast-track response",
    },
    "dispersal": {
        "chain": ["SPORE_DISPERSAL", "MURMURATION_RELAY", "SOCIAL_PROMOTER"],
        "output_files": ["spore_dispersal.json", "social_queue.json"],
        "purpose": "Saturate all channels with help content",
    },
    "void_filling": {
        "chain": ["OSMOSIS_ROUTER", "AMPLIFY_ENGINE", "CONTENT_HARVESTER"],
        "output_files": ["osmosis_routing.json", "amplification_posts.json"],
        "purpose": "Detect under-covered crises -> route attention there",
    },
    "public_record": {
        "chain": ["SIGNAL_BOOST", "CRISIS_MONITOR"],
        "output_files": ["signal_boost_log.json", "crisis_signals.json"],
        "purpose": "Create permanent GitHub Issues for CRITICAL signals",
    },
    "collective_decision": {
        "chain": ["QUORUM_SENSE", "CRISIS_MONITOR", "BIOLUMINESCENCE"],
        "output_files": ["quorum_state.json"],
        "purpose": "Collective signal threshold triggers coordinated response",
    },
    "revenue_engine": {
        "chain": ["INCOME_ARCHITECT", "GUMROAD_AUTO_QUEUE", "STOREFRONT_BUILDER"],
        "output_files": ["revenue_state.json", "proof_ledger.json"],
        "purpose": "Generate revenue -> track -> route to Gaza fund",
    },
    "self_build": {
        "chain": ["KNOWLEDGE_WEAVER", "SELF_BUILDER", "ENGINE_INTEGRITY"],
        "output_files": ["knowledge_weaver_state.json"],
        "purpose": "Discover new capabilities -> build new engines",
    },
    "health_monitor": {
        "chain": ["HOMEOSTASIS", "WORKTREE_ANCHOR", "DARK_WATCH"],
        "output_files": ["homeostasis.json", "worktree_anchor.json"],
        "purpose": "Monitor system health -> detect degradation -> alert",
    },
}


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def load_neuro_state():
    data = load_json(NEURO_FILE)
    if not data:
        data = {
            "version": "1.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "pathway_scores": {},  # pathway_name -> strength score
            "strengthened": [],
            "pruned": [],
            "rewired": [],
            "myelinated": [],
            "total_adaptations": 0,
        }
    return data


def measure_pathway_strength(pathway_name, pathway_def):
    """Measure how well a pathway is functioning based on its output files."""
    strength = 0
    max_strength = 100
    checks = []

    chain = pathway_def["chain"]
    output_files = pathway_def["output_files"]

    # Check 1: Do all engines in the chain exist? (30 points)
    engines_exist = 0
    for engine in chain:
        if (MYCELIUM / f"{engine}.py").exists():
            engines_exist += 1
    engine_score = int((engines_exist / max(len(chain), 1)) * 30)
    strength += engine_score
    checks.append(f"Engines: {engines_exist}/{len(chain)} exist ({engine_score}/30)")

    # Check 2: Do output files exist and have recent data? (40 points)
    outputs_alive = 0
    for ofile in output_files:
        fpath = DATA / ofile
        if fpath.exists():
            try:
                data = json.loads(fpath.read_text())
                ts = data.get("timestamp", "")
                if ts:
                    # Check if data is from last 24 hours
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                        if age_hours < 24:
                            outputs_alive += 1
                        elif age_hours < 72:
                            outputs_alive += 0.5  # Stale but exists
                    except Exception:
                        outputs_alive += 0.3  # Has timestamp but can't parse
                else:
                    outputs_alive += 0.2  # File exists but no timestamp
            except Exception:
                outputs_alive += 0.1  # File exists but not valid JSON

    output_score = int((outputs_alive / max(len(output_files), 1)) * 40)
    strength += output_score
    checks.append(f"Outputs: {outputs_alive:.1f}/{len(output_files)} alive ({output_score}/40)")

    # Check 3: Does the output contain meaningful data? (30 points)
    meaningful = 0
    for ofile in output_files:
        fpath = DATA / ofile
        if fpath.exists():
            try:
                data = json.loads(fpath.read_text())
                # Check if there's actual content, not just empty structures
                size = fpath.stat().st_size
                if size > 100:
                    meaningful += 1
                elif size > 20:
                    meaningful += 0.5
            except Exception:
                pass

    meaning_score = int((meaningful / max(len(output_files), 1)) * 30)
    strength += meaning_score
    checks.append(f"Content: {meaningful:.1f}/{len(output_files)} meaningful ({meaning_score}/30)")

    return min(strength, max_strength), checks


def classify_pathway(name, strength, state):
    """Classify pathway and recommend action based on strength."""
    prev_strength = state.get("pathway_scores", {}).get(name, {}).get("strength", 50)

    if strength >= 80:
        action = "MYELINATE"
        reason = "Strong pathway — cache and prioritize"
    elif strength >= 60:
        action = "STRENGTHEN"
        reason = "Good pathway — increase priority"
    elif strength >= 40:
        action = "MONITOR"
        reason = "Adequate but needs attention"
    elif strength >= 20:
        action = "INVESTIGATE"
        reason = "Weak pathway — check for broken links"
    else:
        action = "PRUNE_CANDIDATE"
        reason = "Very weak — consider pruning or rewiring"

    # Detect trends
    trend = "stable"
    if strength > prev_strength + 10:
        trend = "improving"
    elif strength < prev_strength - 10:
        trend = "degrading"

    return action, reason, trend


def suggest_new_pathways(state):
    """Neurogenesis — suggest new connections that don't exist yet."""
    suggestions = []

    # Check if BIOLUMINESCENCE -> TELEGRAM_RELAY is strong
    bio = load_json(DATA / "bioluminescence.json")
    silence_events = [e for e in bio.get("silence_events", []) if not e.get("resolved")]
    if silence_events:
        suggestions.append({
            "name": "emergency_mesh_relay",
            "chain": ["BIOLUMINESCENCE", "RESOURCE_KIT", "TELEGRAM_RELAY", "SPORE_DISPERSAL"],
            "trigger": f"{len(silence_events)} active silence events detected",
            "purpose": "Silence -> generate kits -> format for mesh -> disperse through all channels",
        })

    # Check if OSMOSIS found voids that AMPLIFY isn't targeting
    osmosis = load_json(DATA / "osmosis_routing.json")
    voids = osmosis.get("information_voids", [])
    if len(voids) > 5:
        suggestions.append({
            "name": "void_saturation",
            "chain": ["OSMOSIS_ROUTER", "SPORE_DISPERSAL", "AMPLIFY_ENGINE"],
            "trigger": f"{len(voids)} information voids detected",
            "purpose": "Direct all dispersal energy toward forgotten crises",
        })

    # Check if IMMUNE_MEMORY has patterns that QUORUM_SENSE could use
    immune = load_json(DATA / "immune_memory.json")
    patterns = immune.get("patterns", {})
    if len(patterns) >= 3:
        suggestions.append({
            "name": "immune_quorum_feedback",
            "chain": ["IMMUNE_MEMORY", "QUORUM_SENSE", "CRISIS_MONITOR"],
            "trigger": f"{len(patterns)} immune patterns could inform quorum thresholds",
            "purpose": "Use immune memory to dynamically adjust quorum thresholds per region",
        })

    return suggestions


def main():
    print("NEUROPLASTICITY -- Self-rewiring pathways (brain pattern)...")
    print("  'The brain that can't rewire itself is dead.'")

    state = load_neuro_state()

    # Measure all pathways
    print(f"\n  Evaluating {len(PATHWAYS)} neural pathways...")
    pathway_results = []

    for name, pdef in PATHWAYS.items():
        strength, checks = measure_pathway_strength(name, pdef)
        action, reason, trend = classify_pathway(name, strength, state)

        state["pathway_scores"][name] = {
            "strength": strength,
            "action": action,
            "trend": trend,
            "last_measured": datetime.now(timezone.utc).isoformat(),
        }

        pathway_results.append({
            "name": name,
            "chain": " -> ".join(pdef["chain"]),
            "purpose": pdef["purpose"],
            "strength": strength,
            "action": action,
            "reason": reason,
            "trend": trend,
            "checks": checks,
        })

        symbol = "M" if action == "MYELINATE" else "+" if action == "STRENGTHEN" else \
                 " " if action == "MONITOR" else "?" if action == "INVESTIGATE" else "X"
        trend_arrow = "^" if trend == "improving" else "v" if trend == "degrading" else "="
        print(f"    [{symbol}] {name}: {strength}/100 {trend_arrow} ({action})")

    # Neurogenesis — suggest new pathways
    suggestions = suggest_new_pathways(state)
    if suggestions:
        print(f"\n  NEUROGENESIS: {len(suggestions)} new pathway suggestions")
        for s in suggestions:
            print(f"    NEW: {s['name']}")
            print(f"         {' -> '.join(s['chain'])}")
            print(f"         Trigger: {s['trigger']}")

    # Summary stats
    myelinated = [p for p in pathway_results if p["action"] == "MYELINATE"]
    strong = [p for p in pathway_results if p["action"] == "STRENGTHEN"]
    weak = [p for p in pathway_results if p["action"] in ("INVESTIGATE", "PRUNE_CANDIDATE")]
    avg_strength = sum(p["strength"] for p in pathway_results) / max(len(pathway_results), 1)

    state["myelinated"] = [p["name"] for p in myelinated]
    state["strengthened"] = [p["name"] for p in strong]
    state["total_adaptations"] = state.get("total_adaptations", 0) + len(suggestions)
    state["last_updated"] = datetime.now(timezone.utc).isoformat()

    # Save
    NEURO_FILE.write_text(json.dumps(state, indent=2))

    PATHWAY_FILE.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pathways": pathway_results,
        "suggestions": suggestions,
        "stats": {
            "total_pathways": len(pathway_results),
            "myelinated": len(myelinated),
            "strong": len(strong),
            "weak": len(weak),
            "avg_strength": round(avg_strength, 1),
            "new_suggestions": len(suggestions),
        },
    }, indent=2))

    print(f"\n  Network health: avg {avg_strength:.0f}/100")
    print(f"  Myelinated: {len(myelinated)} | Strong: {len(strong)} | Weak: {len(weak)}")
    print(f"  New pathways suggested: {len(suggestions)}")
    print("NEUROPLASTICITY done.")


if __name__ == "__main__":
    main()
