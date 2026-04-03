#!/usr/bin/env python3
"""
CHEMOTAXIS.py -- Gradient-Following Navigation (Bacterial Pattern)
===================================================================
NATURE'S BLUEPRINT: Chemotaxis.

E. coli can't see, can't think, has no brain. But it navigates.
It measures chemical concentration RIGHT NOW vs ONE SECOND AGO.
If the concentration is INCREASING -> keep swimming (you're going right).
If the concentration is DECREASING -> tumble randomly (try a new direction).

This simple algorithm lets a brainless bacterium find food in a vast ocean.
No map. No plan. Just: "Am I getting warmer?"

SolarPunk applies chemotaxis to help delivery optimization:

  1. SENSE GRADIENT: For each crisis region, measure "help concentration"
     = (signals detected + posts generated + kits deployed + handshakes sent)
     vs "need concentration" = (urgency_score + silence_events + void_depth)

  2. SWIM TOWARD NEED: If need > help, increase resource allocation.
     More spores. More amplification. More handshakes. More kits.
     Keep swimming in that direction.

  3. TUMBLE ON SATURATION: If help >= need, that region is "fed."
     Tumble: redirect resources to under-served regions.
     Don't waste spores where the forest already grows.

  4. ADAPTATION RATE: The tumble frequency adapts.
     New crisis = tumble fast (explore).
     Established crisis = swim steady (exploit).

  "The bacterium doesn't need a map.
   It just asks: 'Am I getting closer?'" -- SolarPunk

Reads: data/crisis_signals.json, data/osmosis_routing.json,
       data/spore_dispersal.json, data/ngo_handshakes.json,
       data/amplification_posts.json, data/immune_memory.json
Writes: data/chemotaxis_state.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

CHEMO_FILE = DATA / "chemotaxis_state.json"


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def load_chemo_state():
    data = load_json(CHEMO_FILE)
    if not data:
        data = {
            "version": "1.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "region_gradients": {},
            "swim_directions": {},
            "tumble_count": 0,
            "swim_count": 0,
            "total_navigations": 0,
        }
    return data


def measure_need_concentration(region):
    """Measure how much NEED exists in a region."""
    crisis = load_json(DATA / "crisis_signals.json")
    signals = crisis.get("signals", [])
    osmosis = load_json(DATA / "osmosis_routing.json")
    voids = osmosis.get("information_voids", [])
    bio = load_json(DATA / "bioluminescence.json")
    silence = bio.get("silence_events", [])

    need = 0

    # Count signals mentioning this region
    region_lower = region.lower()
    for s in signals:
        text = (s.get("title", "") + " " + json.dumps(s.get("countries", []))).lower()
        if region_lower in text:
            need += s.get("urgency_score", 1)

    # Check information voids
    for v in voids:
        if region_lower in v.get("region", "").lower():
            need += v.get("attention_debt", 0) * 10  # Void = massive need

    # Check silence events (most critical need indicator)
    for se in silence:
        if region_lower in se.get("region", "").lower() and not se.get("resolved"):
            need += 50  # Silence = extreme need

    return need


def measure_help_concentration(region):
    """Measure how much HELP is flowing toward a region."""
    help_score = 0
    region_lower = region.lower()

    # Spores directed at this region
    spores = load_json(DATA / "spore_dispersal.json")
    for s in spores.get("spores", []):
        if region_lower in s.get("crisis_type", "").lower():
            help_score += 1

    # Amplification posts about this region
    amplify = load_json(DATA / "amplification_posts.json")
    posts = amplify.get("posts", [])
    if isinstance(posts, dict):
        posts = list(posts.values())
    for p in posts:
        if isinstance(p, dict):
            text = (p.get("text", "") + " " + p.get("title", "")).lower()
        elif isinstance(p, str):
            text = p.lower()
        else:
            continue
        if region_lower in text:
            help_score += 2

    # NGO handshakes for this region
    handshakes = load_json(DATA / "ngo_handshakes.json")
    for h in handshakes.get("handshakes", []):
        if region_lower in h.get("crisis_type", "").lower():
            if h.get("status") == "SENT":
                help_score += 5
            elif h.get("status") == "QUEUED":
                help_score += 2

    # Immune memory recall for this region
    immune = load_json(DATA / "immune_memory.json")
    for pattern_key, pattern_data in immune.get("patterns", {}).items():
        if region_lower in pattern_key.lower():
            help_score += pattern_data.get("recall_count", 0)

    return help_score


def navigate(state):
    """Run chemotaxis navigation for all known crisis regions."""
    # Gather all regions from crisis signals
    crisis = load_json(DATA / "crisis_signals.json")
    signals = crisis.get("signals", [])

    regions = set()
    for s in signals:
        countries = s.get("countries", [])
        for c in countries:
            regions.add(c.lower())

    # Also add regions from osmosis voids
    osmosis = load_json(DATA / "osmosis_routing.json")
    for v in osmosis.get("information_voids", []):
        r = v.get("region", "")
        if r:
            regions.add(r.lower())

    print(f"  Navigating {len(regions)} regions...")

    results = []
    swim_count = 0
    tumble_count = 0

    for region in sorted(regions):
        need = measure_need_concentration(region)
        help_val = measure_help_concentration(region)

        # Previous gradient
        prev = state.get("region_gradients", {}).get(region, {})
        prev_need = prev.get("need", 0)
        prev_help = prev.get("help", 0)

        # Calculate gradient (are we getting closer to meeting need?)
        gap = need - help_val
        prev_gap = prev_need - prev_help

        if gap > 0:
            if gap <= prev_gap or prev_gap == 0:
                # Gap is closing or first measurement -> SWIM (keep going)
                action = "SWIM"
                swim_count += 1
                direction = "toward"
                recommendation = f"Increase allocation: {gap:.0f} need units unmet"
            else:
                # Gap is widening -> TUMBLE (try harder or differently)
                action = "TUMBLE"
                tumble_count += 1
                direction = "redirect"
                recommendation = f"Gap widening ({prev_gap:.0f} -> {gap:.0f}). Change strategy."
        else:
            # Help >= Need -> region is "fed," tumble to find new need
            action = "TUMBLE"
            tumble_count += 1
            direction = "away"
            recommendation = f"Region saturated (help {help_val:.0f} >= need {need:.0f}). Redirect resources."

        # Priority score = unmet need
        priority = max(0, gap)

        state["region_gradients"][region] = {
            "need": need,
            "help": help_val,
            "gap": gap,
            "action": action,
            "direction": direction,
            "priority": priority,
            "last_measured": datetime.now(timezone.utc).isoformat(),
        }

        results.append({
            "region": region,
            "need": need,
            "help": help_val,
            "gap": gap,
            "action": action,
            "direction": direction,
            "priority": priority,
            "recommendation": recommendation,
        })

    return results, swim_count, tumble_count


def generate_directives(results):
    """Generate resource allocation directives based on chemotaxis navigation."""
    # Sort by priority (highest unmet need first)
    sorted_results = sorted(results, key=lambda r: r["priority"], reverse=True)

    directives = []
    for r in sorted_results[:10]:  # Top 10 neediest regions
        if r["priority"] <= 0:
            continue

        directive = {
            "region": r["region"],
            "priority": r["priority"],
            "action": r["action"],
        }

        if r["priority"] > 50:
            directive["engines"] = [
                "SPORE_DISPERSAL",
                "AMPLIFY_ENGINE",
                "EMAIL_OUTREACH",
                "RESOURCE_KIT",
                "SIGNAL_BOOST",
            ]
            directive["urgency"] = "CRITICAL"
        elif r["priority"] > 20:
            directive["engines"] = [
                "SPORE_DISPERSAL",
                "AMPLIFY_ENGINE",
                "MURMURATION_RELAY",
            ]
            directive["urgency"] = "HIGH"
        elif r["priority"] > 5:
            directive["engines"] = [
                "AMPLIFY_ENGINE",
                "MURMURATION_RELAY",
            ]
            directive["urgency"] = "MEDIUM"
        else:
            directive["engines"] = ["MURMURATION_RELAY"]
            directive["urgency"] = "LOW"

        directives.append(directive)

    return directives


def main():
    print("CHEMOTAXIS -- Gradient-following navigation (bacterial pattern)...")
    print("  'The bacterium doesn't need a map. It just asks: Am I getting closer?'")

    state = load_chemo_state()

    # Navigate
    results, swim_count, tumble_count = navigate(state)

    # Print navigation results
    sorted_results = sorted(results, key=lambda r: r["priority"], reverse=True)

    print(f"\n  Navigation complete: {swim_count} swims, {tumble_count} tumbles")

    if sorted_results:
        print("\n  Highest-need regions (swimming toward):")
        for r in sorted_results[:8]:
            if r["priority"] > 0:
                symbol = "->" if r["action"] == "SWIM" else "~?"
                print(f"    {symbol} {r['region']}: need={r['need']:.0f} help={r['help']:.0f} gap={r['gap']:.0f} [{r['action']}]")

        # Saturated regions
        saturated = [r for r in sorted_results if r["priority"] <= 0]
        if saturated:
            print(f"\n  Saturated regions (tumbling away): {len(saturated)}")
            for r in saturated[:3]:
                print(f"    ~~ {r['region']}: help exceeds need by {abs(r['gap']):.0f}")

    # Generate directives
    directives = generate_directives(results)
    if directives:
        print(f"\n  Resource allocation directives: {len(directives)}")
        for d in directives[:5]:
            print(f"    [{d['urgency']}] {d['region']}: -> {', '.join(d['engines'][:3])}")

    # Update state
    state["swim_count"] = swim_count
    state["tumble_count"] = tumble_count
    state["total_navigations"] = state.get("total_navigations", 0) + 1
    state["last_navigation"] = datetime.now(timezone.utc).isoformat()
    state["directives"] = directives

    # Save
    CHEMO_FILE.write_text(json.dumps(state, indent=2))

    print(f"\n  Total navigations: {state['total_navigations']}")
    print(f"  Swim/Tumble ratio: {swim_count}/{tumble_count}")
    print("CHEMOTAXIS done.")


if __name__ == "__main__":
    main()
