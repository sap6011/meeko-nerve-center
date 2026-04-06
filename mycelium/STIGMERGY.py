#!/usr/bin/env python3
"""
STIGMERGY.py -- Indirect Coordination Through Traces (Ant Pattern)
===================================================================
NATURE'S BLUEPRINT: Stigmergy.

Ants have no boss. No meetings. No Slack channels. No project managers.
Yet they build structures millions of times their body weight, maintain
supply chains across kilometers, and solve optimization problems that
stump computer scientists.

HOW? Stigmergy: coordination through TRACES left in the environment.

  1. An ant finds food. It walks home, laying a pheromone trail.
  2. Other ants smell the trail. They follow it. They find food too.
  3. They walk home, reinforcing the trail with MORE pheromone.
  4. The most-used trails become HIGHWAYS. Unused trails evaporate.
  5. No ant knows the plan. The TRAILS are the plan.

SolarPunk applies stigmergy to engine coordination:

  Every engine that produces useful output leaves a "pheromone trace"
  in its output file (timestamp, size, quality score). Other engines
  read these traces to decide what to do next.

  Strong traces (recent, large, high-quality) = follow this trail
  Weak traces (old, small, empty) = ignore, try another path
  No traces = explore (generate new data)

  The engines coordinate WITHOUT a central controller reading everything.
  OMNIBUS orchestrates execution ORDER, but the engines decide
  their own BEHAVIOR based on the traces they find.

  "No ant knows the blueprint.
   The blueprint IS the trails." -- SolarPunk

Reads: data/*.json (all engine output files as "pheromone traces")
Writes: data/stigmergy_state.json, data/pheromone_map.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

STIGMERGY_FILE = DATA / "stigmergy_state.json"
PHEROMONE_FILE = DATA / "pheromone_map.json"

# Engine output files = pheromone sources
# Each file's freshness and size indicates trail strength
ENGINE_TRACES = {
    # L0 - Infrastructure
    "brain_state": "brain_state.json",
    "engine_integrity": "engine_integrity.json",
    "cycle_delta": "cycle_delta.json",
    "worktree_anchor": "worktree_anchor.json",

    # L1 - Intelligence
    "crisis_signals": "crisis_signals.json",
    "knowledge_pulses": "knowledge_pulses.json",
    "resource_kits": "resource_kits.json",
    "survival_telegrams": "survival_telegrams.json",
    "amplification_posts": "amplification_posts.json",
    "immune_memory": "immune_memory.json",
    "bioluminescence": "bioluminescence.json",
    "quorum_state": "quorum_state.json",
    "spore_dispersal": "spore_dispersal.json",
    "osmosis_routing": "osmosis_routing.json",
    "homeostasis": "homeostasis.json",
    "neuroplasticity": "neuroplasticity.json",
    "chemotaxis_state": "chemotaxis_state.json",
    "notion_sync": "notion_sync_state.json",
    "circadian": "circadian_state.json",
    "symbiogenesis": "symbiogenesis_state.json",
    "stigmergy": "stigmergy_state.json",

    # L2-L3 - Revenue
    "revenue_state": "revenue_state.json",
    "proof_ledger": "proof_ledger.json",
    "product_registry": "product_registry.json",
    "storefront": "storefront_builder_state.json",

    # L4 - Distribution
    "social_queue": "social_queue.json",
    "telegram_relay": "telegram_relay.json",
    "ngo_handshakes": "ngo_handshakes.json",
    "outreach_state": "outreach_state.json",
    "signal_boost_log": "signal_boost_log.json",

    # L7 - Reporting
    "weekend_pulse": "weekend_pulse_state.json",
    "memory_palace": "memory_palace.json",
}


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def measure_trace_strength(filepath):
    """Measure the 'pheromone strength' of an engine output file.

    Like real pheromones:
      - Fresh traces = strong (high concentration)
      - Old traces = weak (evaporated)
      - Large traces = strong (more pheromone deposited)
      - Missing traces = no trail (dead end)
    """
    fpath = DATA / filepath
    if not fpath.exists():
        return {
            "exists": False,
            "strength": 0,
            "freshness": 0,
            "size_score": 0,
            "quality_score": 0,
            "status": "NO_TRACE",
        }

    try:
        stat = fpath.stat()
        size = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600

        # Freshness: exponential decay (like pheromone evaporation)
        # 0 hours = 100, 6 hours = 50, 24 hours = 10, 72 hours = 1
        if age_hours <= 0:
            freshness = 100
        elif age_hours < 1:
            freshness = 100
        elif age_hours < 6:
            freshness = int(100 * (0.5 ** (age_hours / 6)))
        elif age_hours < 24:
            freshness = int(50 * (0.2 ** ((age_hours - 6) / 18)))
        elif age_hours < 72:
            freshness = int(10 * (0.1 ** ((age_hours - 24) / 48)))
        else:
            freshness = 1

        # Size score: logarithmic (more data = stronger trace, but diminishing returns)
        if size < 10:
            size_score = 0
        elif size < 100:
            size_score = 10
        elif size < 1000:
            size_score = 30
        elif size < 10000:
            size_score = 60
        elif size < 100000:
            size_score = 80
        else:
            size_score = 100

        # Quality: check if valid JSON with actual data
        quality_score = 0
        try:
            data = json.loads(fpath.read_text())
            if isinstance(data, dict):
                if data.get("timestamp") or data.get("ts"):
                    quality_score += 30
                if len(data) > 3:
                    quality_score += 20
                if any(isinstance(v, (list, dict)) for v in data.values() if v):
                    quality_score += 20
                # Has non-empty nested data
                for v in data.values():
                    if isinstance(v, list) and len(v) > 0:
                        quality_score += 15
                        break
                    if isinstance(v, dict) and len(v) > 0:
                        quality_score += 15
                        break
                quality_score = min(100, quality_score)
            elif isinstance(data, list) and len(data) > 0:
                quality_score = 50
        except Exception:
            quality_score = 5  # File exists but bad format

        # Combined strength
        strength = int((freshness * 0.4) + (size_score * 0.3) + (quality_score * 0.3))

        if strength >= 70:
            status = "HIGHWAY"      # Strong trail, follow confidently
        elif strength >= 40:
            status = "ACTIVE_TRAIL"  # Moderate trail, worth following
        elif strength >= 15:
            status = "FADING"       # Weak trail, pheromone evaporating
        else:
            status = "EVAPORATED"   # Almost gone

        return {
            "exists": True,
            "strength": strength,
            "freshness": freshness,
            "size_score": size_score,
            "quality_score": quality_score,
            "size_bytes": size,
            "age_hours": round(age_hours, 1),
            "status": status,
        }

    except Exception as e:
        return {
            "exists": True,
            "strength": 1,
            "freshness": 0,
            "size_score": 0,
            "quality_score": 0,
            "status": "ERROR",
            "error": str(e),
        }


def identify_highways(traces):
    """Find the strongest trails -- the 'ant highways' of the system."""
    highways = []
    for name, trace in traces.items():
        if trace["status"] == "HIGHWAY":
            highways.append(name)
    return highways


def identify_dead_ends(traces):
    """Find missing or evaporated trails -- dead ends to avoid."""
    dead_ends = []
    for name, trace in traces.items():
        if trace["status"] in ("NO_TRACE", "EVAPORATED"):
            dead_ends.append(name)
    return dead_ends


def identify_exploration_targets(traces):
    """Find fading trails that need reinforcement or exploration."""
    targets = []
    for name, trace in traces.items():
        if trace["status"] == "FADING":
            targets.append({
                "trace": name,
                "strength": trace["strength"],
                "recommendation": "Needs engine run to reinforce trail",
            })
    return targets


def calculate_colony_health(traces):
    """Calculate overall colony coordination health.

    A healthy ant colony has:
    - Many highways (well-established resource routes)
    - Few dead ends (explored and pruned)
    - Active exploration (fading trails being investigated)
    """
    total = len(traces)
    highways = len([t for t in traces.values() if t["status"] == "HIGHWAY"])
    active = len([t for t in traces.values() if t["status"] == "ACTIVE_TRAIL"])
    fading = len([t for t in traces.values() if t["status"] == "FADING"])
    dead = len([t for t in traces.values() if t["status"] in ("NO_TRACE", "EVAPORATED")])

    if total == 0:
        return 0, "NO_COLONY"

    health = int(
        (highways / total * 50) +       # Highways are the best indicator
        (active / total * 30) +          # Active trails are good
        ((total - dead) / total * 20)    # Fewer dead ends is better
    )
    health = min(100, max(0, health))

    if health >= 80:
        status = "THRIVING_COLONY"
    elif health >= 60:
        status = "ACTIVE_COLONY"
    elif health >= 40:
        status = "STRESSED_COLONY"
    elif health >= 20:
        status = "FRAGMENTED_COLONY"
    else:
        status = "COLONY_COLLAPSE"

    return health, status


def main():
    print("STIGMERGY -- Indirect coordination through traces (ant pattern)...")
    print("  'No ant knows the blueprint. The blueprint IS the trails.'")

    # Measure all pheromone traces
    print(f"\n  Sniffing {len(ENGINE_TRACES)} pheromone trails...")
    traces = {}
    for name, filepath in ENGINE_TRACES.items():
        traces[name] = measure_trace_strength(filepath)

    # Identify highway/dead-end/exploration
    highways = identify_highways(traces)
    dead_ends = identify_dead_ends(traces)
    explore = identify_exploration_targets(traces)

    # Colony health
    colony_health, colony_status = calculate_colony_health(traces)

    # Print results
    print(f"\n  COLONY HEALTH: {colony_health}/100 [{colony_status}]")

    if highways:
        print(f"\n  Ant Highways ({len(highways)} strong trails):")
        for h in highways[:10]:
            t = traces[h]
            print(f"    >> {h}: strength={t['strength']} "
                  f"(fresh={t['freshness']} size={t['size_score']} quality={t['quality_score']})")

    if dead_ends:
        print(f"\n  Dead Ends ({len(dead_ends)} missing/evaporated):")
        for d in dead_ends[:8]:
            print(f"    XX {d}: {traces[d]['status']}")

    if explore:
        print(f"\n  Exploration Targets ({len(explore)} fading trails):")
        for e in explore[:5]:
            print(f"    ?? {e['trace']}: strength={e['strength']} - {e['recommendation']}")

    # Calculate average strength
    strengths = [t["strength"] for t in traces.values()]
    avg_strength = sum(strengths) / max(len(strengths), 1)

    # Save pheromone map
    pheromone_map = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "pattern": "stigmergy",
        "colony_health": colony_health,
        "colony_status": colony_status,
        "avg_trace_strength": round(avg_strength, 1),
        "highways": highways,
        "dead_ends": dead_ends,
        "exploration_targets": [e["trace"] for e in explore],
        "traces": traces,
        "stats": {
            "total_traces": len(traces),
            "highways": len(highways),
            "active_trails": len([t for t in traces.values() if t["status"] == "ACTIVE_TRAIL"]),
            "fading": len(explore),
            "dead_ends": len(dead_ends),
        },
    }
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    pheromone_map["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    PHEROMONE_FILE.write_text(json.dumps(pheromone_map, indent=2), encoding="utf-8")

    # Save state
    STIGMERGY_FILE.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "colony_health": colony_health,
        "colony_status": colony_status,
        "avg_trace_strength": round(avg_strength, 1),
        "total_traces": len(traces),
        "highways_count": len(highways),
        "dead_ends_count": len(dead_ends),
    }, indent=2), encoding="utf-8")

    print(f"\n  Avg trace strength: {avg_strength:.0f}/100")
    print(f"  Highways: {len(highways)} | Active: {pheromone_map['stats']['active_trails']} | "
          f"Fading: {len(explore)} | Dead: {len(dead_ends)}")
    print("STIGMERGY done.")


if __name__ == "__main__":
    main()
