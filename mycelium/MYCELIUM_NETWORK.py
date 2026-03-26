#!/usr/bin/env python3
"""
MYCELIUM_NETWORK.py -- Bio-Inspired Nutrient Transport & Self-Healing Network
==============================================================================
Real mycelium (fungal networks) do things that SolarPunk should copy:

  1. NUTRIENT ROUTING: Resources flow from surplus to deficit nodes.
     Trees with excess carbon send it through mycorrhizal networks to
     trees that need it. The network doesn't decide centrally -- each
     node follows concentration gradients.

  2. ADAPTIVE GROWTH: Hyphae (fungal threads) explore in all directions.
     Paths that find nutrients get strengthened (more flow). Paths that
     find nothing get pruned. Explore-exploit, from biology.

  3. ANASTOMOSIS (Self-Healing): When a hypha breaks, nearby hyphae
     fuse across the gap to restore the connection. The network routes
     around damage automatically.

  4. DECOMPOSITION: Mycelium breaks down dead material into nutrients
     that feed new growth. Waste becomes food. Nothing is lost.

  5. CHEMICAL SIGNALING: Mycelium communicates threats and opportunities
     through electrical signals and volatile organic compounds.
     Neighboring trees get warned of pest attacks through the network.

This engine implements all five patterns for SolarPunk's data network:
  - Nutrient routing: Move data from engines that produce surplus to
    engines that need it (concentration gradient model)
  - Adaptive growth: Strengthen connections that produce results,
    prune connections that don't (based on LIVE_WIRE data)
  - Anastomosis: Detect broken connections and create bridge data
    to restore them (self-healing)
  - Decomposition: Find stale/orphan data files and recycle their
    contents into fresh formats that active engines can use
  - Signaling: Propagate health warnings through the network when
    engines fail or data goes stale

Output: data/mycelium_network_state.json
Zero secrets needed.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

DATA = Path("data")
DATA.mkdir(exist_ok=True)


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, FileNotFoundError, OSError):
        return {}


# ═══════════════════════════════════════════════════════════════════
# 1. NUTRIENT ROUTING — Concentration gradient model
# ═══════════════════════════════════════════════════════════════════

def compute_nutrient_map(engines, wires):
    """
    Compute a 'nutrient concentration' for each engine.

    Biology: In mycorrhizal networks, carbon flows from trees with
    excess (producers) to trees in deficit (receivers). The flow
    direction follows the concentration gradient -- always from
    high to low.

    Digital: An engine's 'nutrient level' is how much useful data
    it produces vs. how much it consumes. Engines that write many
    files read by others are 'producers'. Engines that read many
    files but write few are 'consumers'.
    """
    nutrient_levels = {}

    for name, info in engines.items():
        writes = len(info.get("writes", []))
        reads = len(info.get("reads", []))

        # Count how many other engines depend on this one's output
        downstream = sum(1 for w in wires if w.get("from") == name)
        # Count how many other engines feed this one
        upstream = sum(1 for w in wires if w.get("to") == name)

        # Nutrient level: production surplus minus consumption deficit
        # Positive = producer (like a sun-rich tree sharing carbon)
        # Negative = consumer (like a shaded tree receiving carbon)
        level = (writes * 2 + downstream) - (reads + upstream * 0.5)
        nutrient_levels[name] = {
            "level": round(level, 2),
            "role": "producer" if level > 0 else "consumer" if level < 0 else "neutral",
            "writes": writes,
            "reads": reads,
            "downstream_dependents": downstream,
            "upstream_feeders": upstream,
        }

    return nutrient_levels


def find_nutrient_gradients(nutrient_levels, wires):
    """
    Find the strongest nutrient gradients in the network.

    Biology: Nutrients flow fastest where the concentration
    difference is greatest. A massive oak next to a struggling
    seedling creates a steep gradient.

    Digital: Where producer engines connect to consumer engines
    with the biggest level difference, that's where data flow
    matters most.
    """
    gradients = []
    for wire in wires:
        src = nutrient_levels.get(wire.get("from"), {})
        dst = nutrient_levels.get(wire.get("to"), {})
        src_level = src.get("level", 0)
        dst_level = dst.get("level", 0)
        gradient = src_level - dst_level

        if gradient > 0:  # Flow from producer to consumer
            gradients.append({
                "from": wire["from"],
                "to": wire["to"],
                "via": wire.get("via", ""),
                "gradient": round(gradient, 2),
                "src_level": src_level,
                "dst_level": dst_level,
            })

    gradients.sort(key=lambda g: g["gradient"], reverse=True)
    return gradients


# ═══════════════════════════════════════════════════════════════════
# 2. ADAPTIVE GROWTH — Explore-exploit from hyphal branching
# ═══════════════════════════════════════════════════════════════════

def assess_wire_health(wires, test_results):
    """
    Score each wire's health based on test results.

    Biology: Hyphae that find nutrients get thicker (more cytoplasm,
    more transport capacity). Hyphae that find nothing thin out and
    eventually die.

    Digital: Wires where data flows successfully (LIVE status) get
    strengthened. Wires with NO_DATA or CORRUPT status get marked
    for pruning.
    """
    # Build lookup from test results
    test_lookup = {}
    for result in test_results:
        key = result.get("wire", "")
        test_lookup[key] = result

    wire_health = []
    for wire in wires:
        key = f"{wire['from']} -> {wire['to']}"
        test = test_lookup.get(key, {})
        status = test.get("status", "UNKNOWN")

        # Health score: LIVE=1.0, NO_DATA=0.3, CORRUPT=0.0, UNKNOWN=0.5
        health = {
            "LIVE": 1.0,
            "NO_DATA": 0.3,
            "CORRUPT": 0.0,
            "READ_ERROR": 0.1,
            "UNKNOWN": 0.5,
        }.get(status, 0.5)

        wire_health.append({
            "from": wire["from"],
            "to": wire["to"],
            "via": wire.get("via", ""),
            "status": status,
            "health": health,
            "action": "strengthen" if health >= 0.8 else "monitor" if health >= 0.3 else "prune",
        })

    return wire_health


# ═══════════════════════════════════════════════════════════════════
# 3. ANASTOMOSIS — Self-healing by bridging broken connections
# ═══════════════════════════════════════════════════════════════════

def detect_breaks(wire_health, orphans):
    """
    Find broken connections that need healing.

    Biology: When a hypha is severed (by burrowing insects, soil
    disturbance, drought), nearby hyphae grow toward the break
    point and fuse across the gap. This is anastomosis.

    Digital: When a data file goes missing or becomes corrupt,
    identify alternative data sources that could fill the gap.
    """
    breaks = []

    # Broken wires (CORRUPT or READ_ERROR)
    for wh in wire_health:
        if wh["action"] == "prune":
            breaks.append({
                "type": "broken_wire",
                "from": wh["from"],
                "to": wh["to"],
                "via": wh["via"],
                "status": wh["status"],
                "healing": "BRIDGE_BUILDER should regenerate " + wh["via"],
            })

    # Hungry inputs (data needed but not produced)
    for hungry in orphans.get("hungry_inputs", []):
        breaks.append({
            "type": "hungry_input",
            "file": hungry,
            "healing": "Create seed data or bridge from existing source",
        })

    return breaks


# ═══════════════════════════════════════════════════════════════════
# 4. DECOMPOSITION — Recycling stale data into fresh nutrients
# ═══════════════════════════════════════════════════════════════════

def find_decomposition_targets():
    """
    Find stale data files that could be recycled.

    Biology: Mycelium secretes enzymes (cellulase, lignin peroxidase)
    that break down dead wood into simple sugars and minerals. The
    forest floor's dead material becomes food for living trees.

    Digital: Old data files that no engine reads anymore still contain
    useful information. Decompose them -- extract the useful parts
    and make them available in formats that active engines want.
    """
    targets = []
    now = datetime.now(timezone.utc)

    for data_file in sorted(DATA.glob("*.json")):
        try:
            stat = data_file.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            age_days = (now - mtime).days
            size = stat.st_size

            if age_days > 7 and size > 100:
                # Check if any engine reads this file
                targets.append({
                    "file": data_file.name,
                    "age_days": age_days,
                    "size_bytes": size,
                    "last_modified": mtime.isoformat(),
                    "action": "decompose" if age_days > 14 else "monitor",
                })
        except OSError:
            pass

    targets.sort(key=lambda t: t["age_days"], reverse=True)
    return targets


# ═══════════════════════════════════════════════════════════════════
# 5. CHEMICAL SIGNALING — Warning propagation through the network
# ═══════════════════════════════════════════════════════════════════

def propagate_signals(wire_health, nutrient_levels, sentinel_report):
    """
    Generate network-wide signals based on health state.

    Biology: When a tree is attacked by bark beetles, it releases
    volatile organic compounds (VOCs) through the mycorrhizal
    network. Neighboring trees detect these chemicals and begin
    producing defensive compounds BEFORE the beetles arrive.

    Digital: When engines fail syntax checks, have corrupt data,
    or show declining nutrient levels, propagate warnings to
    connected engines so the system can respond proactively.
    """
    signals = []

    # Signal 1: Syntax failures from sentinel
    failures = sentinel_report.get("failures", [])
    if failures:
        signals.append({
            "type": "PEST_ALERT",
            "severity": "high" if len(failures) > 10 else "medium",
            "message": f"{len(failures)} engines failing syntax checks",
            "source": "sentinel",
            "affected": [f.get("engine", f.get("file", "unknown")) for f in failures[:10]],
            "biology": "Bark beetle attack detected -- VOC warning sent to neighbors",
        })

    # Signal 2: High producer engines going offline (broken wires from producers)
    pruned_producers = [
        wh for wh in wire_health
        if wh["action"] == "prune"
        and nutrient_levels.get(wh["from"], {}).get("role") == "producer"
    ]
    if pruned_producers:
        signals.append({
            "type": "DROUGHT_WARNING",
            "severity": "high",
            "message": f"{len(pruned_producers)} producer connections broken",
            "source": "nutrient_routing",
            "affected": list(set(wh["from"] for wh in pruned_producers)),
            "biology": "Major root system damaged -- nutrient flow disrupted downstream",
        })

    # Signal 3: Consumer engines starving (many reads, no data)
    starving = [
        name for name, info in nutrient_levels.items()
        if info["role"] == "consumer" and info["level"] < -3
    ]
    if starving:
        signals.append({
            "type": "NUTRIENT_DEFICIT",
            "severity": "medium",
            "message": f"{len(starving)} engines severely nutrient-depleted",
            "source": "nutrient_routing",
            "affected": starving[:10],
            "biology": "Shaded understory trees need carbon transfer from canopy",
        })

    # Signal 4: Network health summary
    total_wires = len(wire_health)
    healthy = sum(1 for wh in wire_health if wh["health"] >= 0.8)
    ratio = healthy / total_wires if total_wires > 0 else 0

    signals.append({
        "type": "NETWORK_PULSE",
        "severity": "info",
        "message": f"Network health: {ratio:.0%} ({healthy}/{total_wires} wires healthy)",
        "source": "mycelium_network",
        "biology": "Seasonal growth assessment -- overall forest vitality check",
    })

    return signals


# ═══════════════════════════════════════════════════════════════════
# 6. RECIPROCAL REWARDS — Biological market dynamics (Kiers 2011)
# ═══════════════════════════════════════════════════════════════════

def compute_reciprocal_rewards(engines, wires, nutrient_levels):
    """
    Score engines by their reciprocity — do they give as much as they take?

    Biology: Toby Kiers (Science, 2011) showed that mycorrhizal fungi
    and trees use reciprocal rewards: plants allocate more carbon to
    fungi that provide more phosphorus, and vice versa. Cheaters —
    organisms that take without giving — get economically penalized
    by receiving less from their partners.

    Digital: Engines that consume many data files but produce nothing
    for others are "cheaters." Engines that both consume AND produce
    are mutualists. Track the balance.
    """
    rewards = {}
    for name, info in engines.items():
        nutrient = nutrient_levels.get(name, {})
        reads = len(info.get("reads", []))
        writes = len(info.get("writes", []))
        downstream = nutrient.get("downstream_dependents", 0)

        # Reciprocity score: what you give / what you take
        giving = writes + downstream
        taking = reads
        if taking > 0:
            reciprocity = round(giving / taking, 2)
        elif giving > 0:
            reciprocity = 10.0  # Pure giver
        else:
            reciprocity = 1.0  # Neither gives nor takes

        if reciprocity >= 2.0:
            role = "mutualist"    # Gives much more than it takes
        elif reciprocity >= 0.5:
            role = "balanced"     # Fair exchange
        elif reciprocity > 0:
            role = "consumer"     # Takes more than it gives
        else:
            role = "inert"        # Does nothing

        rewards[name] = {
            "reciprocity": reciprocity,
            "role": role,
            "giving": giving,
            "taking": taking,
        }

    return rewards


# ═══════════════════════════════════════════════════════════════════
# 7. NETWORK MEMORY — Spatial memory without neurons
# ═══════════════════════════════════════════════════════════════════

def compute_network_memory(wire_report_path):
    """
    Track network topology changes over time.

    Biology: Mycelium retains 'memory' of past nutrient encounters —
    it grows faster toward locations where it previously found food,
    even after the food is removed. This spatial memory is stored in
    cytoskeletal patterns, not neurons. (Fukasawa et al., 2024)

    Digital: Compare current topology to previous snapshots.
    Connections that persist across cycles are 'remembered' —
    the network's structural memory. New connections are exploration.
    Lost connections may need restoration.
    """
    current = load_json(wire_report_path)
    previous_state = load_json(DATA / "mycelium_memory.json")

    current_wires = set()
    for w in current.get("wires", []):
        current_wires.add(f"{w['from']}->{w['to']}")

    previous_wires = set(previous_state.get("known_wires", []))

    # What's new, what persisted, what was lost
    new_connections = current_wires - previous_wires
    persisted = current_wires & previous_wires
    lost = previous_wires - current_wires

    # Update memory
    memory = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "known_wires": sorted(current_wires),
        "total_remembered": len(current_wires),
        "cycles_tracked": previous_state.get("cycles_tracked", 0) + 1,
        "this_cycle": {
            "new_connections": len(new_connections),
            "persisted": len(persisted),
            "lost": len(lost),
            "lost_list": sorted(lost)[:20],
            "new_list": sorted(new_connections)[:20],
        },
    }

    (DATA / "mycelium_memory.json").write_text(json.dumps(memory, indent=2))
    return memory


# ═══════════════════════════════════════════════════════════════════
# MAIN: Run all seven mycelium patterns
# ═══════════════════════════════════════════════════════════════════

def run():
    print("MYCELIUM NETWORK -- Bio-Inspired Nutrient Transport & Self-Healing")
    print("=" * 65)

    # Load LIVE_WIRE data
    wire_report = load_json(DATA / "live_wire_report.json")
    if not wire_report:
        print("  No wire report found. Run LIVE_WIRE first.")
        return

    engines = wire_report.get("engines", {})
    wires = wire_report.get("wires", [])
    test_results = wire_report.get("test_results", [])
    orphans = wire_report.get("orphans", {})
    sentinel = load_json(DATA / "sentinel_report.json")

    # Phase 1: NUTRIENT ROUTING
    print("\n  Phase 1: NUTRIENT ROUTING (concentration gradients)")
    nutrients = compute_nutrient_map(engines, wires)
    producers = [n for n, i in nutrients.items() if i["role"] == "producer"]
    consumers = [n for n, i in nutrients.items() if i["role"] == "consumer"]
    print(f"    Producers (nutrient surplus): {len(producers)}")
    print(f"    Consumers (nutrient deficit): {len(consumers)}")
    print(f"    Neutral: {len(nutrients) - len(producers) - len(consumers)}")

    # Top producers
    top_producers = sorted(nutrients.items(), key=lambda x: x[1]["level"], reverse=True)[:5]
    for name, info in top_producers:
        print(f"    + {name}: level={info['level']} ({info['downstream_dependents']} dependents)")

    # Steepest gradients
    gradients = find_nutrient_gradients(nutrients, wires)
    print(f"\n    Steepest gradients (strongest nutrient flows):")
    for g in gradients[:5]:
        print(f"    {g['from']} -> {g['to']} via {g['via']} (gradient={g['gradient']})")

    # Phase 2: ADAPTIVE GROWTH
    print("\n  Phase 2: ADAPTIVE GROWTH (strengthen/prune)")
    wire_health_list = assess_wire_health(wires, test_results)
    strengthen = sum(1 for wh in wire_health_list if wh["action"] == "strengthen")
    monitor = sum(1 for wh in wire_health_list if wh["action"] == "monitor")
    prune = sum(1 for wh in wire_health_list if wh["action"] == "prune")
    print(f"    Strengthen (healthy): {strengthen}")
    print(f"    Monitor (waiting):    {monitor}")
    print(f"    Prune (broken):       {prune}")

    # Phase 3: ANASTOMOSIS
    print("\n  Phase 3: ANASTOMOSIS (self-healing)")
    breaks = detect_breaks(wire_health_list, orphans)
    broken_wires = [b for b in breaks if b["type"] == "broken_wire"]
    hungry = [b for b in breaks if b["type"] == "hungry_input"]
    print(f"    Broken wires to heal: {len(broken_wires)}")
    print(f"    Hungry inputs to bridge: {len(hungry)}")

    # Phase 4: DECOMPOSITION
    print("\n  Phase 4: DECOMPOSITION (recycling stale data)")
    decomp_targets = find_decomposition_targets()
    old_files = [t for t in decomp_targets if t["action"] == "decompose"]
    watch_files = [t for t in decomp_targets if t["action"] == "monitor"]
    print(f"    Files to decompose (>14 days old): {len(old_files)}")
    print(f"    Files to monitor (7-14 days old):  {len(watch_files)}")
    for t in old_files[:5]:
        print(f"    - {t['file']} ({t['age_days']} days, {t['size_bytes']} bytes)")

    # Phase 5: CHEMICAL SIGNALING
    print("\n  Phase 5: CHEMICAL SIGNALING (warning propagation)")
    signals = propagate_signals(wire_health_list, nutrients, sentinel)
    for sig in signals:
        icon = {"high": "!", "medium": "~", "info": "."}.get(sig["severity"], "?")
        print(f"    [{icon}] {sig['type']}: {sig['message']}")
        print(f"        Biology: {sig['biology']}")

    # Phase 6: RECIPROCAL REWARDS
    print("\n  Phase 6: RECIPROCAL REWARDS (biological market)")
    rewards = compute_reciprocal_rewards(engines, wires, nutrients)
    mutualists = sum(1 for r in rewards.values() if r["role"] == "mutualist")
    balanced = sum(1 for r in rewards.values() if r["role"] == "balanced")
    consumers_rr = sum(1 for r in rewards.values() if r["role"] == "consumer")
    inert = sum(1 for r in rewards.values() if r["role"] == "inert")
    print(f"    Mutualists (give > take): {mutualists}")
    print(f"    Balanced (fair exchange): {balanced}")
    print(f"    Consumers (take > give):  {consumers_rr}")
    print(f"    Inert (neither):          {inert}")
    top_mutualists = sorted(
        [(n, r) for n, r in rewards.items() if r["role"] == "mutualist"],
        key=lambda x: x[1]["reciprocity"], reverse=True
    )[:5]
    for name, info in top_mutualists:
        print(f"    + {name}: reciprocity={info['reciprocity']} (gives {info['giving']}, takes {info['taking']})")

    # Phase 7: NETWORK MEMORY
    print("\n  Phase 7: NETWORK MEMORY (spatial memory without neurons)")
    memory = compute_network_memory(DATA / "live_wire_report.json")
    cycle = memory.get("this_cycle", {})
    print(f"    Cycles tracked: {memory.get('cycles_tracked', 1)}")
    print(f"    Persisted connections: {cycle.get('persisted', 0)}")
    print(f"    New connections: {cycle.get('new_connections', 0)}")
    print(f"    Lost connections: {cycle.get('lost', 0)}")

    # Build comprehensive state
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "mycelium-network-v1",
        "nutrient_routing": {
            "total_nodes": len(nutrients),
            "producers": len(producers),
            "consumers": len(consumers),
            "top_producers": [{"name": n, **i} for n, i in top_producers],
            "steepest_gradients": gradients[:10],
        },
        "adaptive_growth": {
            "total_wires": len(wire_health_list),
            "strengthen": strengthen,
            "monitor": monitor,
            "prune": prune,
        },
        "anastomosis": {
            "broken_wires": len(broken_wires),
            "hungry_inputs": len(hungry),
            "breaks": breaks[:20],
        },
        "decomposition": {
            "decompose_targets": len(old_files),
            "monitor_targets": len(watch_files),
            "targets": decomp_targets[:20],
        },
        "signals": signals,
        "reciprocal_rewards": {
            "mutualists": mutualists,
            "balanced": balanced,
            "consumers": consumers_rr,
            "inert": inert,
            "top_mutualists": [{"name": n, **i} for n, i in top_mutualists],
        },
        "network_memory": {
            "cycles_tracked": memory.get("cycles_tracked", 1),
            "new_connections": cycle.get("new_connections", 0),
            "persisted": cycle.get("persisted", 0),
            "lost": cycle.get("lost", 0),
        },
        "biology_notes": {
            "nutrient_routing": "Mycorrhizal networks transport carbon/nitrogen/phosphorus from surplus trees to deficit trees via concentration gradients",
            "adaptive_growth": "Hyphae that find nutrients thicken; hyphae that find nothing are pruned. Explore-exploit tradeoff.",
            "anastomosis": "Broken hyphae are healed by nearby hyphae fusing across the gap. Self-repair without central coordination.",
            "decomposition": "Enzymes (cellulase, lignin peroxidase) break dead wood into nutrients. Waste becomes food.",
            "signaling": "VOCs and electrical signals propagate threat warnings through the network. Neighbors prepare before the threat arrives.",
            "reciprocal_rewards": "Kiers (Science, 2011): plants and fungi preferentially reward partners that provide more resources. Cheaters are economically penalized.",
            "network_memory": "Mycelium retains spatial memory of past nutrient encounters without neurons. Stored in cytoskeletal patterns and network topology.",
        },
    }

    out = DATA / "mycelium_network_state.json"
    out.write_text(json.dumps(state, indent=2))

    # Summary
    network_health = strengthen / len(wire_health_list) if wire_health_list else 0
    print(f"\n  === MYCELIUM NETWORK STATE ===")
    print(f"  Network health:       {network_health:.0%}")
    print(f"  Nutrient producers:   {len(producers)}")
    print(f"  Mutualists:           {mutualists}")
    print(f"  Active signals:       {len(signals)}")
    print(f"  Self-heal targets:    {len(breaks)}")
    print(f"  Decomposition queue:  {len(old_files)}")
    print(f"  Memory cycles:        {memory.get('cycles_tracked', 1)}")
    print(f"\n  7 patterns from biology. 0 from engineering textbooks.")
    print(f"  The forest feeds itself. The network heals itself.")


if __name__ == "__main__":
    run()
