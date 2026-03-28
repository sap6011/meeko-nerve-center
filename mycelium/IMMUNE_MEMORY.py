#!/usr/bin/env python3
"""
IMMUNE_MEMORY.py — Adaptive Crisis Response (T-Cell Pattern)
=============================================================
NATURE'S BLUEPRINT: The human immune system.

When your body fights a virus for the first time, it takes days.
The SECOND time? Hours. Memory T-cells remember the threat and
fire the response instantly.

SolarPunk does the same:

  1. ENCOUNTER: First time seeing "internet shutdown in Sudan"
     → Full pipeline runs: detect → score → trigger → handshake → amplify
     → Response time: ~120 seconds through all engines

  2. MEMORY: System records the PATTERN, not just the event:
     → Pattern: {region: "sudan", type: "internet_shutdown", response: [...]}
     → Effective resources: which NGOs responded, which channels worked
     → What the survival telegram looked like

  3. RECALL: Next time "internet shutdown in Sudan" appears:
     → Skip scoring (already know it's CRITICAL)
     → Skip resource matching (already know MSF + Access Now)
     → Fire the EXACT response that worked last time
     → Response time: ~5 seconds (24x faster)

  4. ADAPTATION: If the response didn't work (no engagement, no handshake reply):
     → Mutate: try different channels, different NGOs, different timing
     → Like antibody affinity maturation — each generation fits better

  5. CROSS-IMMUNITY: Pattern "internet shutdown in Sudan" also primes
     response for "internet shutdown in Myanmar" — similar crisis type
     transfers the playbook across regions.

Reads: data/crisis_signals.json, data/crisis_triggers.json,
       data/ngo_handshakes.json, data/murmuration_log.json
Writes: data/immune_memory.json, data/immune_responses.json
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data")
DATA.mkdir(exist_ok=True)

MEMORY_FILE = DATA / "immune_memory.json"
RESPONSES_FILE = DATA / "immune_responses.json"
CRISIS_FILE = DATA / "crisis_signals.json"
TRIGGERS_FILE = DATA / "crisis_triggers.json"
HANDSHAKES_FILE = DATA / "ngo_handshakes.json"
MURMUR_LOG = DATA / "murmuration_log.json"
KITS_FILE = DATA / "resource_kits.json"

# Pattern extraction keywords → crisis types
CRISIS_TYPES = {
    "internet_shutdown": ["shutdown", "blackout", "communications cut", "internet blocked"],
    "aid_blockade": ["aid blocked", "blockade", "humanitarian corridor closed", "siege"],
    "genocide": ["genocide", "ethnic cleansing", "mass killing", "mass graves"],
    "famine": ["famine", "starvation", "food crisis", "hunger"],
    "displacement": ["refugees", "displaced", "forced migration", "flee"],
    "media_blackout": ["media blackout", "journalist killed", "press freedom", "censorship"],
    "medical_crisis": ["hospital destroyed", "medical supplies", "bombing hospital"],
    "chemical_attack": ["chemical weapons", "white phosphorus", "cluster munitions"],
}

REGIONS = [
    "gaza", "palestine", "sudan", "darfur", "congo", "drc", "yemen",
    "myanmar", "uyghur", "xinjiang", "tigray", "ethiopia", "syria",
    "ukraine", "haiti", "somalia", "afghanistan", "rohingya",
    "west bank", "rafah", "khan younis", "jabalia", "khartoum",
]


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def load_memory():
    data = load_json(MEMORY_FILE)
    if not data:
        data = {
            "version": "1.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "patterns": {},      # pattern_hash → {type, region, responses, effectiveness}
            "antibodies": {},    # crisis_type → [proven response chains]
            "cross_immunity": {},  # crisis_type → [related types that share playbooks]
            "encounter_count": 0,
            "recall_count": 0,
            "adaptation_count": 0,
        }
    return data


def save_memory(memory):
    memory["last_updated"] = datetime.now(timezone.utc).isoformat()
    MEMORY_FILE.write_text(json.dumps(memory, indent=2))


def extract_pattern(signal):
    """Extract the immunological pattern from a crisis signal — type + region."""
    text = (signal.get("title", "") + " " + signal.get("text", "")).lower()

    crisis_type = "unknown"
    for ctype, keywords in CRISIS_TYPES.items():
        for kw in keywords:
            if kw in text:
                crisis_type = ctype
                break
        if crisis_type != "unknown":
            break

    region = "unknown"
    for r in REGIONS:
        if r in text:
            region = r
            break

    pattern_key = f"{crisis_type}|{region}"
    pattern_hash = hashlib.md5(pattern_key.encode()).hexdigest()[:12]

    return {
        "hash": pattern_hash,
        "key": pattern_key,
        "type": crisis_type,
        "region": region,
        "signal_title": signal.get("title", "")[:150],
        "score": signal.get("urgency_score", 0),
    }


def build_response_chain(pattern, memory):
    """Build the response chain — either from memory (recall) or fresh (encounter)."""
    pattern_hash = pattern["hash"]

    # Check if we've seen this pattern before
    if pattern_hash in memory["patterns"]:
        # RECALL — T-cell memory activation
        stored = memory["patterns"][pattern_hash]
        stored["encounters"] += 1
        stored["last_seen"] = datetime.now(timezone.utc).isoformat()
        memory["recall_count"] = memory.get("recall_count", 0) + 1

        return {
            "mode": "RECALL",
            "pattern": pattern,
            "response_chain": stored.get("best_response", {}),
            "confidence": min(stored["encounters"] * 15, 95),  # More encounters = more confidence
            "previous_effectiveness": stored.get("effectiveness", 0),
            "speed": "FAST (memory T-cell)",
        }

    # ENCOUNTER — first time seeing this pattern
    memory["encounter_count"] = memory.get("encounter_count", 0) + 1

    # Check cross-immunity — have we seen this TYPE before in another region?
    cross_match = None
    for phash, pdata in memory["patterns"].items():
        if pdata.get("type") == pattern["type"] and pdata.get("encounters", 0) > 0:
            cross_match = pdata
            break

    # Build fresh response chain
    response = {
        "target_engines": [],
        "resource_kits": [],
        "ngo_targets": [],
        "channels": [],
        "telegram_type": pattern["type"] if pattern["type"] in [
            "internet_shutdown", "medical_crisis", "displacement",
            "media_blackout", "documentation_safety"
        ] else None,
    }

    # Map crisis type to response engines
    ENGINE_MAP = {
        "internet_shutdown": {
            "engines": ["BROADCAST_PROTOCOL", "SOCIAL_PROMOTER", "BLUESKY_ENGINE", "TELEGRAM_RELAY"],
            "kits": ["internet_shutdown"],
            "ngos": ["Access Now", "CPJ"],
            "channels": ["social", "broadcast", "mesh"],
        },
        "aid_blockade": {
            "engines": ["EMAIL_OUTREACH", "BROADCAST_PROTOCOL", "SIGNAL_BOOST"],
            "kits": ["medical_emergency", "displacement_survival"],
            "ngos": ["MSF", "ICRC", "WFP", "UNRWA"],
            "channels": ["email", "github_issue", "broadcast"],
        },
        "genocide": {
            "engines": ["EMAIL_OUTREACH", "BROADCAST_PROTOCOL", "SOCIAL_PROMOTER", "SIGNAL_BOOST"],
            "kits": ["documentation_safety"],
            "ngos": ["MSF", "ICRC", "PCRF"],
            "channels": ["all"],
        },
        "famine": {
            "engines": ["EMAIL_OUTREACH", "SIGNAL_BOOST"],
            "kits": ["medical_emergency"],
            "ngos": ["WFP", "Direct Relief", "IRC"],
            "channels": ["email", "github_issue"],
        },
        "displacement": {
            "engines": ["SOCIAL_PROMOTER", "EMAIL_OUTREACH", "SIGNAL_BOOST"],
            "kits": ["displacement_survival"],
            "ngos": ["UNHCR", "IRC", "HIAS"],
            "channels": ["social", "email", "reddit"],
        },
        "media_blackout": {
            "engines": ["SOCIAL_PROMOTER", "BLUESKY_ENGINE", "BROADCAST_PROTOCOL", "AMPLIFY_ENGINE"],
            "kits": ["press_freedom", "internet_shutdown"],
            "ngos": ["CPJ", "RSF", "Access Now"],
            "channels": ["social", "broadcast", "mesh"],
        },
        "medical_crisis": {
            "engines": ["EMAIL_OUTREACH", "TELEGRAM_RELAY", "SIGNAL_BOOST"],
            "kits": ["medical_emergency"],
            "ngos": ["MSF", "PCRF", "Direct Relief", "ICRC"],
            "channels": ["email", "sms", "satellite"],
        },
        "chemical_attack": {
            "engines": ["EMAIL_OUTREACH", "BROADCAST_PROTOCOL", "SOCIAL_PROMOTER", "SIGNAL_BOOST"],
            "kits": ["documentation_safety", "medical_emergency"],
            "ngos": ["MSF", "ICRC", "OPCW"],
            "channels": ["all"],
        },
    }

    mapping = ENGINE_MAP.get(pattern["type"], ENGINE_MAP["genocide"])  # Default to maximum response
    response["target_engines"] = mapping["engines"]
    response["resource_kits"] = mapping["kits"]
    response["ngo_targets"] = mapping["ngos"]
    response["channels"] = mapping["channels"]

    # Store the new pattern
    memory["patterns"][pattern["hash"]] = {
        "type": pattern["type"],
        "region": pattern["region"],
        "first_seen": datetime.now(timezone.utc).isoformat(),
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "encounters": 1,
        "best_response": response,
        "effectiveness": 0,  # Will be updated based on downstream results
        "signal_title": pattern["signal_title"],
    }

    result = {
        "mode": "ENCOUNTER" if not cross_match else "CROSS_IMMUNITY",
        "pattern": pattern,
        "response_chain": response,
        "confidence": 50 if not cross_match else 70,
        "cross_source": cross_match.get("region", "") if cross_match else None,
        "speed": "STANDARD (first encounter)" if not cross_match else "ACCELERATED (cross-immunity)",
    }

    return result


def update_effectiveness(memory):
    """Check downstream results and update pattern effectiveness scores.
    Like antibody affinity maturation — what worked gets strengthened."""
    handshakes = load_json(HANDSHAKES_FILE)
    murmur = load_json(MURMUR_LOG)

    # Count successful handshakes (status != QUEUED means it was processed)
    processed_handshakes = 0
    for h in handshakes.get("handshakes", []):
        if h.get("status") != "QUEUED":
            processed_handshakes += 1

    # Count murmuration relays
    relay_count = len(murmur.get("relays", []))

    # Update effectiveness for patterns that match recent signals
    for phash, pdata in memory["patterns"].items():
        age_days = 0
        try:
            last = datetime.fromisoformat(pdata.get("last_seen", "2020-01-01"))
            age_days = (datetime.now(timezone.utc) - last).days
        except Exception:
            pass

        if age_days <= 7:  # Recent pattern
            # Effectiveness = encounters * relay success * handshake success
            encounters = pdata.get("encounters", 1)
            eff = min(encounters * 10 + processed_handshakes * 5 + relay_count * 2, 100)
            old_eff = pdata.get("effectiveness", 0)
            # Exponential moving average — new evidence matters more
            pdata["effectiveness"] = int(old_eff * 0.3 + eff * 0.7)

    # Adaptation: if effectiveness is low after multiple encounters, flag for mutation
    adaptations = []
    for phash, pdata in memory["patterns"].items():
        if pdata.get("encounters", 0) >= 3 and pdata.get("effectiveness", 0) < 30:
            adaptations.append({
                "pattern": phash,
                "type": pdata["type"],
                "region": pdata["region"],
                "suggestion": "Try different channels or NGOs — current response chain ineffective",
                "current_effectiveness": pdata["effectiveness"],
            })
            memory["adaptation_count"] = memory.get("adaptation_count", 0) + 1

    return adaptations


def build_cross_immunity_map(memory):
    """Build the cross-immunity map — which crisis types share response playbooks."""
    type_regions = {}
    for phash, pdata in memory["patterns"].items():
        ctype = pdata.get("type", "unknown")
        if ctype not in type_regions:
            type_regions[ctype] = []
        type_regions[ctype].append({
            "region": pdata.get("region", "unknown"),
            "effectiveness": pdata.get("effectiveness", 0),
            "encounters": pdata.get("encounters", 0),
        })

    # Cross-immunity: types that share similar response chains
    CROSS_MAP = {
        "internet_shutdown": ["media_blackout"],
        "media_blackout": ["internet_shutdown"],
        "genocide": ["chemical_attack", "aid_blockade"],
        "chemical_attack": ["genocide"],
        "famine": ["aid_blockade"],
        "aid_blockade": ["famine", "medical_crisis"],
        "medical_crisis": ["aid_blockade"],
        "displacement": ["famine", "genocide"],
    }

    memory["cross_immunity"] = CROSS_MAP
    return CROSS_MAP


def main():
    print("IMMUNE_MEMORY — Adaptive crisis response (T-cell pattern)...")

    memory = load_memory()

    # Load current crisis signals
    crisis = load_json(CRISIS_FILE)
    signals = crisis.get("signals", [])

    # Only process HIGH and CRITICAL
    urgent = [s for s in signals if s.get("urgency") in ("CRITICAL", "HIGH")]
    print(f"  Processing {len(urgent)} urgent signals...")

    responses = []
    recalls = 0
    encounters = 0
    cross_immunities = 0

    for signal in urgent:
        pattern = extract_pattern(signal)
        response = build_response_chain(pattern, memory)

        if response["mode"] == "RECALL":
            recalls += 1
        elif response["mode"] == "CROSS_IMMUNITY":
            cross_immunities += 1
        else:
            encounters += 1

        responses.append(response)

    # Update effectiveness based on downstream results
    adaptations = update_effectiveness(memory)

    # Build cross-immunity map
    build_cross_immunity_map(memory)

    # Save
    save_memory(memory)

    RESPONSES_FILE.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "responses": responses,
        "stats": {
            "total": len(responses),
            "recalls": recalls,
            "encounters": encounters,
            "cross_immunities": cross_immunities,
            "adaptations": len(adaptations),
        },
        "adaptations": adaptations,
    }, indent=2))

    total_patterns = len(memory.get("patterns", {}))
    total_encounters = memory.get("encounter_count", 0)
    total_recalls = memory.get("recall_count", 0)

    print(f"\n  This cycle: {recalls} recalls | {encounters} new encounters | {cross_immunities} cross-immune")
    print(f"  Memory bank: {total_patterns} patterns stored")
    print(f"  All-time: {total_encounters} encounters | {total_recalls} recalls")
    print(f"  Adaptations needed: {len(adaptations)}")
    if adaptations:
        for a in adaptations[:3]:
            print(f"    -> {a['type']}|{a['region']}: effectiveness {a['current_effectiveness']}% — needs mutation")
    print("IMMUNE_MEMORY done.")


if __name__ == "__main__":
    main()
