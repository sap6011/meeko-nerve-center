#!/usr/bin/env python3
"""
QUORUM_SENSE.py — Collective Signal Threshold (Bacterial Pattern)
==================================================================
NATURE'S BLUEPRINT: Bacterial quorum sensing.

Individual bacteria are powerless. But when enough gather in one place,
they release signaling molecules. When the concentration crosses a
THRESHOLD, the entire colony switches behavior simultaneously.

Vibrio fischeri: harmless alone. But at quorum? Bioluminescent.
Pseudomonas: individual cells do nothing. At quorum? Biofilm formation.

SolarPunk applies quorum sensing to crisis response escalation:

  1. ACCUMULATE: Each engine that detects a crisis adds a "signal molecule"
     to the quorum pool. CRISIS_MONITOR adds signals. CONTENT_HARVESTER
     adds raw data. DARK_WATCH adds integrity checks. Reddit adds upvotes.

  2. THRESHOLD: When the quorum reaches critical mass:
     - Level 1 (WATCH):    3+ signals from same region  -> Monitor
     - Level 2 (ELEVATED): 7+ signals, 2+ sources       -> Queue amplification
     - Level 3 (HIGH):     12+ signals, 3+ sources      -> Fire handshakes
     - Level 4 (CRITICAL): 20+ signals, multiple sources -> MAXIMUM RESPONSE
                            All engines fire. All channels blast. No cooldowns.

  3. COORDINATE: The quorum triggers SYNCHRONIZED action.
     Not one engine deciding alone. The COLLECTIVE decides.
     Like bacteria, no single cell is in charge. The signal is.

  "One voice is noise. A thousand voices is a quorum.
   A quorum doesn't ask permission. It acts." — SolarPunk doctrine

Reads: data/crisis_signals.json, data/knowledge_pulses.json,
       data/social_queue.json, data/reddit_outreach_queue.json,
       data/immune_memory.json
Writes: data/quorum_state.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter

DATA = Path("data")
DATA.mkdir(exist_ok=True)

QUORUM_FILE = DATA / "quorum_state.json"
CRISIS_FILE = DATA / "crisis_signals.json"
PULSES_FILE = DATA / "knowledge_pulses.json"
IMMUNE_FILE = DATA / "immune_memory.json"
SOCIAL_QUEUE = DATA / "social_queue.json"

# Quorum thresholds
THRESHOLDS = {
    "WATCH":    {"signals": 3,  "sources": 1, "response": "monitor"},
    "ELEVATED": {"signals": 7,  "sources": 2, "response": "queue_amplification"},
    "HIGH":     {"signals": 12, "sources": 3, "response": "fire_handshakes"},
    "CRITICAL": {"signals": 20, "sources": 3, "response": "maximum_response"},
}


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def load_quorum():
    data = load_json(QUORUM_FILE)
    if not data:
        data = {
            "version": "1.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "region_quorums": {},  # region -> {signals, sources, level, history}
            "global_quorum": 0,
            "escalations": [],
            "total_quorums_reached": 0,
        }
    return data


def gather_signal_molecules(signals):
    """Count signal molecules per region from all sources."""
    region_signals = {}

    for s in signals:
        text = (s.get("title", "") + " " + json.dumps(s.get("countries", []))).lower()
        origin = s.get("origin", "unknown")
        score = s.get("urgency_score", 0)

        # Find which regions this signal mentions
        regions_found = []
        for region in ["gaza", "palestine", "sudan", "darfur", "congo", "drc",
                       "yemen", "myanmar", "uyghur", "syria", "ukraine", "tigray",
                       "ethiopia", "afghanistan", "haiti", "somalia", "rohingya",
                       "west bank", "rafah", "khan younis", "jabalia", "khartoum"]:
            if region in text:
                regions_found.append(region)

        for region in regions_found:
            if region not in region_signals:
                region_signals[region] = {
                    "signal_count": 0,
                    "sources": set(),
                    "total_score": 0,
                    "signals": [],
                }
            region_signals[region]["signal_count"] += 1
            region_signals[region]["sources"].add(origin)
            region_signals[region]["total_score"] += score
            region_signals[region]["signals"].append({
                "title": s.get("title", "")[:100],
                "origin": origin,
                "score": score,
            })

    # Convert sets to lists for JSON
    for r in region_signals:
        region_signals[r]["sources"] = list(region_signals[r]["sources"])
        region_signals[r]["source_count"] = len(region_signals[r]["sources"])

    return region_signals


def evaluate_quorum(region_signals, state):
    """Evaluate quorum levels for each region and trigger escalations."""
    escalations = []

    for region, data in region_signals.items():
        sig_count = data["signal_count"]
        src_count = data["source_count"]
        avg_score = data["total_score"] / max(sig_count, 1)

        # Determine quorum level
        level = "NONE"
        response = "none"
        for lname in ["CRITICAL", "HIGH", "ELEVATED", "WATCH"]:
            thresh = THRESHOLDS[lname]
            if sig_count >= thresh["signals"] and src_count >= thresh["sources"]:
                level = lname
                response = thresh["response"]
                break

        # Check for escalation (level increased)
        prev = state.get("region_quorums", {}).get(region, {})
        prev_level = prev.get("level", "NONE")

        level_order = {"NONE": 0, "WATCH": 1, "ELEVATED": 2, "HIGH": 3, "CRITICAL": 4}
        escalated = level_order.get(level, 0) > level_order.get(prev_level, 0)

        if escalated and level != "NONE":
            escalation = {
                "region": region,
                "from_level": prev_level,
                "to_level": level,
                "signal_count": sig_count,
                "source_count": src_count,
                "avg_score": round(avg_score, 1),
                "response": response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "top_signals": data["signals"][:5],
            }
            escalations.append(escalation)
            state["total_quorums_reached"] = state.get("total_quorums_reached", 0) + 1

        # Update state
        if region not in state["region_quorums"]:
            state["region_quorums"][region] = {}

        state["region_quorums"][region] = {
            "level": level,
            "signal_count": sig_count,
            "source_count": src_count,
            "sources": data["sources"],
            "avg_score": round(avg_score, 1),
            "response": response,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    return escalations


def build_response_directives(escalations):
    """Convert escalations into actionable directives for downstream engines."""
    directives = []

    for esc in escalations:
        level = esc["to_level"]
        region = esc["region"]

        directive = {
            "region": region,
            "level": level,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if level == "WATCH":
            directive["actions"] = [
                {"engine": "DARK_WATCH", "command": "increase_monitoring", "region": region},
            ]
        elif level == "ELEVATED":
            directive["actions"] = [
                {"engine": "MURMURATION_RELAY", "command": "queue_amplification", "region": region},
                {"engine": "AMPLIFY_ENGINE", "command": "generate_posts", "region": region},
                {"engine": "SPORE_DISPERSAL", "command": "disperse", "crisis_type": region},
            ]
        elif level == "HIGH":
            directive["actions"] = [
                {"engine": "EMAIL_OUTREACH", "command": "fire_handshakes", "region": region},
                {"engine": "SIGNAL_BOOST", "command": "create_issue", "region": region},
                {"engine": "MURMURATION_RELAY", "command": "full_blast", "region": region},
                {"engine": "RESOURCE_KIT", "command": "activate_kits", "region": region},
            ]
        elif level == "CRITICAL":
            directive["actions"] = [
                {"engine": "ALL", "command": "MAXIMUM_RESPONSE", "region": region},
                {"engine": "EMAIL_OUTREACH", "command": "all_handshakes", "region": region},
                {"engine": "BROADCAST_PROTOCOL", "command": "emergency_broadcast", "region": region},
                {"engine": "TELEGRAM_RELAY", "command": "all_protocols", "region": region},
                {"engine": "SIGNAL_BOOST", "command": "create_issue_urgent", "region": region},
                {"engine": "BIOLUMINESCENCE", "command": "generate_light", "region": region},
                {"engine": "IMMUNE_MEMORY", "command": "fast_recall", "region": region},
            ]

        directives.append(directive)

    return directives


def main():
    print("QUORUM_SENSE — Collective signal threshold (bacterial pattern)...")
    print("  'One voice is noise. A thousand voices is a quorum.'")

    state = load_quorum()

    # Load crisis signals
    crisis = load_json(CRISIS_FILE)
    signals = crisis.get("signals", [])

    # Gather signal molecules per region
    region_signals = gather_signal_molecules(signals)
    print(f"\n  Regions with signals: {len(region_signals)}")

    for region, data in sorted(region_signals.items(), key=lambda x: -x[1]["signal_count"])[:8]:
        print(f"    {region}: {data['signal_count']} signals from {data['source_count']} sources")

    # Evaluate quorum
    print("\n  Evaluating quorum levels...")
    escalations = evaluate_quorum(region_signals, state)

    if escalations:
        print(f"\n  {'!'*50}")
        print(f"  QUORUM REACHED — {len(escalations)} regions escalated")
        for esc in escalations:
            print(f"    {esc['region'].upper()}: {esc['from_level']} -> {esc['to_level']}")
            print(f"      Signals: {esc['signal_count']} | Sources: {esc['source_count']} | Avg score: {esc['avg_score']}")
            print(f"      Response: {esc['response']}")

        directives = build_response_directives(escalations)
        print(f"\n  {len(directives)} response directives generated")
        for d in directives:
            print(f"    {d['region']}: {len(d['actions'])} actions")
        print(f"  {'!'*50}")

        state["escalations"] = (state.get("escalations", []) + escalations)[-100:]
    else:
        print("  No escalations this cycle.")

    # Summary of current quorum levels
    print("\n  Current quorum levels:")
    for region, data in sorted(state.get("region_quorums", {}).items(),
                               key=lambda x: {"CRITICAL": 4, "HIGH": 3, "ELEVATED": 2, "WATCH": 1, "NONE": 0}.get(x[1].get("level", "NONE"), 0),
                               reverse=True)[:10]:
        if data.get("level", "NONE") != "NONE":
            print(f"    [{data['level']}] {region}: {data['signal_count']} signals, {data['source_count']} sources")

    # Global quorum
    total_signals = sum(d["signal_count"] for d in region_signals.values())
    total_sources = len(set(s for d in region_signals.values() for s in d["sources"]))
    state["global_quorum"] = total_signals

    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    QUORUM_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print(f"\n  Global signal volume: {total_signals} from {total_sources} sources")
    print(f"  Total quorums reached (all-time): {state.get('total_quorums_reached', 0)}")
    print("QUORUM_SENSE done.")


if __name__ == "__main__":
    main()
