#!/usr/bin/env python3
"""
HOMEOSTASIS.py — Self-Regulating Planetary Health (Thermostat Pattern)
======================================================================
NATURE'S BLUEPRINT: Homeostasis.

Your body maintains 37C regardless of whether it's -20 or +45 outside.
Blood sugar stays in range. pH stays in range. Heart rate adjusts.
Not because someone tells it to — because FEEDBACK LOOPS self-regulate.

SolarPunk as a planetary immune system needs the same:

  1. SYSTEM HEALTH: Monitor all engines, detect degradation, auto-heal
  2. SIGNAL HEALTH: Track data source reliability, route around failures
  3. RESPONSE HEALTH: Ensure crisis pipeline isn't over/under-reacting
  4. CHANNEL HEALTH: Track which amplification channels work, prune dead ones
  5. RESOURCE HEALTH: Don't burn API limits, manage rate limits, pace outputs

  When the system is "too hot" (over-reacting, flooding channels):
    -> Cool down: increase cooldowns, reduce post frequency
  When the system is "too cold" (under-reacting, missing crises):
    -> Heat up: reduce thresholds, increase scan frequency, add sources

  The planet's body temperature = the balance between detection and action.

  "A healthy organism doesn't need to think about breathing.
   It just breathes." — SolarPunk doctrine

Reads: data/*.json (all engine outputs)
Writes: data/homeostasis.json, data/system_health.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data")
MYCELIUM = Path("mycelium")
DATA.mkdir(exist_ok=True)

HOMEO_FILE = DATA / "homeostasis.json"
HEALTH_FILE = DATA / "system_health.json"

# Optimal ranges — the "body temperature" of SolarPunk
VITAL_SIGNS = {
    "engine_count": {"min": 250, "max": 500, "unit": "engines", "critical_low": 200},
    "crisis_signals": {"min": 5, "max": 100, "unit": "signals/scan", "critical_low": 0},
    "active_sources": {"min": 2, "max": 6, "unit": "data sources", "critical_low": 1},
    "trigger_rate": {"min": 0, "max": 50, "unit": "triggers/scan", "critical_low": None},
    "handshake_queue": {"min": 0, "max": 20, "unit": "queued emails", "critical_low": None},
    "amplification_posts": {"min": 1, "max": 30, "unit": "posts/cycle", "critical_low": 0},
    "immune_patterns": {"min": 1, "max": 1000, "unit": "patterns", "critical_low": 0},
    "information_voids": {"min": 0, "max": 10, "unit": "critical voids", "critical_low": None},
    "silence_events": {"min": 0, "max": 3, "unit": "active blackouts", "critical_low": None},
    "spore_count": {"min": 5, "max": 100, "unit": "spores/cycle", "critical_low": 0},
}


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def measure_vitals():
    """Take all vital measurements — the planetary health check."""
    vitals = {}

    # Engine count
    engines = list(MYCELIUM.glob("*.py"))
    vitals["engine_count"] = len(engines)

    # Crisis signals
    crisis = load_json(DATA / "crisis_signals.json")
    vitals["crisis_signals"] = crisis.get("total", 0)

    # Active sources
    signals = crisis.get("signals", [])
    sources = set(s.get("origin", "") for s in signals if s.get("origin"))
    vitals["active_sources"] = len(sources)
    vitals["source_list"] = list(sources)

    # Triggers
    triggers = load_json(DATA / "crisis_triggers.json")
    vitals["trigger_rate"] = triggers.get("count", 0)

    # Handshakes
    handshakes = load_json(DATA / "ngo_handshakes.json")
    queued = len([h for h in handshakes.get("handshakes", []) if h.get("status") == "QUEUED"])
    vitals["handshake_queue"] = queued

    # Amplification
    amplify = load_json(DATA / "amplification_posts.json")
    vitals["amplification_posts"] = len(amplify.get("posts", []))

    # Immune memory
    immune = load_json(DATA / "immune_memory.json")
    vitals["immune_patterns"] = len(immune.get("patterns", {}))

    # Information voids
    osmosis = load_json(DATA / "osmosis_routing.json")
    critical_voids = osmosis.get("stats", {}).get("critical_voids", 0)
    vitals["information_voids"] = critical_voids

    # Silence events
    bio = load_json(DATA / "bioluminescence.json")
    active_silence = len([e for e in bio.get("silence_events", []) if not e.get("resolved")])
    vitals["silence_events"] = active_silence

    # Spores
    spores = load_json(DATA / "spore_dispersal.json")
    vitals["spore_count"] = spores.get("spore_count", 0)

    # Quorum
    quorum = load_json(DATA / "quorum_state.json")
    vitals["global_quorum"] = quorum.get("global_quorum", 0)
    active_quorums = len([r for r, d in quorum.get("region_quorums", {}).items()
                          if d.get("level", "NONE") != "NONE"])
    vitals["active_quorums"] = active_quorums

    # Weekend pulse data
    pulse = load_json(DATA / "weekend_pulse.json")
    vitals["sovereignty"] = pulse.get("sovereignty", "unknown")

    return vitals


def diagnose(vitals):
    """Compare vitals against optimal ranges — generate diagnoses."""
    diagnoses = []
    overall_health = 100  # Start at 100, deductions for issues

    for key, ranges in VITAL_SIGNS.items():
        value = vitals.get(key, 0)
        status = "NORMAL"
        deduction = 0

        # Check critical low
        if ranges.get("critical_low") is not None and value <= ranges["critical_low"]:
            status = "CRITICAL"
            deduction = 15
        elif value < ranges["min"]:
            status = "LOW"
            deduction = 5
        elif value > ranges["max"]:
            status = "HIGH"
            deduction = 3  # Over-reacting is less dangerous than under-reacting

        overall_health -= deduction

        diagnoses.append({
            "vital": key,
            "value": value,
            "unit": ranges["unit"],
            "range": f"{ranges['min']}-{ranges['max']}",
            "status": status,
            "deduction": deduction,
        })

    overall_health = max(0, min(100, overall_health))
    return diagnoses, overall_health


def prescribe(diagnoses, vitals):
    """Generate corrective actions — like hormones adjusting body function."""
    prescriptions = []

    for d in diagnoses:
        if d["status"] == "NORMAL":
            continue

        key = d["vital"]
        value = d["value"]

        if key == "crisis_signals" and d["status"] in ("LOW", "CRITICAL"):
            prescriptions.append({
                "vital": key,
                "condition": f"Only {value} signals detected",
                "prescription": "ADD_DATA_SOURCES",
                "actions": [
                    "Add Wikipedia Current Events scanning",
                    "Increase Reddit subreddit list",
                    "Check if ReliefWeb API registration is available",
                    "Add Al Jazeera RSS feed",
                    "Add BBC World Service RSS feed",
                ],
                "urgency": "HIGH" if d["status"] == "CRITICAL" else "MEDIUM",
            })

        elif key == "active_sources" and d["status"] in ("LOW", "CRITICAL"):
            prescriptions.append({
                "vital": key,
                "condition": f"Only {value} data sources active (need >= 2)",
                "prescription": "DIVERSIFY_SOURCES",
                "actions": [
                    "Current sources: " + ", ".join(vitals.get("source_list", [])),
                    "Add backup RSS feeds for each primary source",
                    "Enable Wikipedia Current Events fallback",
                    "Consider adding Twitter/X API if available",
                ],
                "urgency": "HIGH",
            })

        elif key == "engine_count" and d["status"] == "LOW":
            prescriptions.append({
                "vital": key,
                "condition": f"Engine count dropped to {value}",
                "prescription": "INVESTIGATE_ENGINE_LOSS",
                "actions": [
                    "Check WORKTREE_ANCHOR for sovereignty status",
                    "Verify no accidental deletions",
                    "Run ENGINE_INTEGRITY check",
                ],
                "urgency": "CRITICAL",
            })

        elif key == "information_voids" and value > 10:
            prescriptions.append({
                "vital": key,
                "condition": f"{value} critical information voids",
                "prescription": "INCREASE_COVERAGE",
                "actions": [
                    "Route AMPLIFY_ENGINE toward void regions",
                    "Increase Reddit scanning for under-covered regions",
                    "Generate social posts specifically about forgotten crises",
                ],
                "urgency": "MEDIUM",
            })

        elif key == "silence_events" and value > 0:
            prescriptions.append({
                "vital": key,
                "condition": f"{value} active silence events (potential blackouts)",
                "prescription": "BIOLUMINESCENCE_RESPONSE",
                "actions": [
                    "BIOLUMINESCENCE engine should be generating light",
                    "Push internet shutdown kits to affected regions",
                    "Fire NGO handshakes for communications blackout",
                    "Re-broadcast last known signals from dark regions",
                ],
                "urgency": "CRITICAL",
            })

        elif key == "spore_count" and d["status"] == "LOW":
            prescriptions.append({
                "vital": key,
                "condition": f"Only {value} spores generated",
                "prescription": "INCREASE_DISPERSAL",
                "actions": [
                    "Check KNOWLEDGE_PULSE output",
                    "Verify MURMURATION_RELAY is running",
                    "Increase SPORE_DISPERSAL channel targets",
                ],
                "urgency": "MEDIUM",
            })

        elif key == "amplification_posts" and d["status"] == "HIGH":
            prescriptions.append({
                "vital": key,
                "condition": f"{value} posts queued (above optimal range)",
                "prescription": "COOLDOWN",
                "actions": [
                    "Increase posting cooldowns to avoid spam detection",
                    "Prioritize highest-urgency posts only",
                    "Spread posts across more time intervals",
                ],
                "urgency": "LOW",
            })

    return prescriptions


def calculate_planetary_health(overall_health, vitals):
    """The big number — how healthy is Earth's digital immune system right now?"""
    # Bonus points for good things
    bonus = 0
    if vitals.get("engine_count", 0) >= 260:
        bonus += 5  # Strong engine base
    if vitals.get("active_sources", 0) >= 3:
        bonus += 5  # Diverse data sources
    if vitals.get("immune_patterns", 0) >= 5:
        bonus += 3  # Building immune memory
    if vitals.get("spore_count", 0) >= 10:
        bonus += 2  # Good dispersal

    planetary_health = min(100, overall_health + bonus)

    if planetary_health >= 90:
        status = "THRIVING"
        message = "The planet's digital immune system is strong. All systems nominal."
    elif planetary_health >= 70:
        status = "HEALTHY"
        message = "System healthy with minor adjustments needed."
    elif planetary_health >= 50:
        status = "STRESSED"
        message = "Multiple systems need attention. Prescriptions generated."
    elif planetary_health >= 30:
        status = "CRITICAL"
        message = "Significant degradation detected. Immediate action required."
    else:
        status = "EMERGENCY"
        message = "System failure imminent. All hands needed."

    return planetary_health, status, message


def main():
    print("HOMEOSTASIS -- Self-regulating planetary health check...")
    print("  'A healthy organism doesn't think about breathing. It just breathes.'")

    # Measure vitals
    print("\n  Taking vital measurements...")
    vitals = measure_vitals()

    # Diagnose
    diagnoses, base_health = diagnose(vitals)

    # Calculate planetary health
    planetary_health, status, message = calculate_planetary_health(base_health, vitals)

    print(f"\n  PLANETARY HEALTH SCORE: {planetary_health}/100 [{status}]")
    print(f"  {message}")

    # Print vitals
    print("\n  Vital Signs:")
    for d in diagnoses:
        indicator = "OK" if d["status"] == "NORMAL" else d["status"]
        symbol = " " if d["status"] == "NORMAL" else "!" if d["status"] in ("LOW", "HIGH") else "X"
        print(f"    [{symbol}] {d['vital']}: {d['value']} {d['unit']} "
              f"(range: {d['range']}) [{indicator}]")

    # Prescribe
    prescriptions = prescribe(diagnoses, vitals)
    if prescriptions:
        print(f"\n  Prescriptions ({len(prescriptions)}):")
        for p in prescriptions:
            print(f"    [{p['urgency']}] {p['prescription']}: {p['condition']}")
            for a in p["actions"][:3]:
                print(f"      -> {a}")

    # Save
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "pattern": "homeostasis",
        "planetary_health": planetary_health,
        "status": status,
        "message": message,
        "vitals": vitals,
        "diagnoses": diagnoses,
        "prescriptions": prescriptions,
        "stats": {
            "normal_count": len([d for d in diagnoses if d["status"] == "NORMAL"]),
            "warning_count": len([d for d in diagnoses if d["status"] in ("LOW", "HIGH")]),
            "critical_count": len([d for d in diagnoses if d["status"] == "CRITICAL"]),
            "prescription_count": len(prescriptions),
        },
    }
    HOMEO_FILE.write_text(json.dumps(output, indent=2))

    HEALTH_FILE.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "planetary_health": planetary_health,
        "status": status,
        "engine_count": vitals.get("engine_count", 0),
        "crisis_signals": vitals.get("crisis_signals", 0),
        "active_sources": vitals.get("active_sources", 0),
        "immune_patterns": vitals.get("immune_patterns", 0),
        "information_voids": vitals.get("information_voids", 0),
        "prescriptions": len(prescriptions),
    }, indent=2))

    print(f"\n  Homeostasis: {output['stats']['normal_count']} normal | "
          f"{output['stats']['warning_count']} warnings | "
          f"{output['stats']['critical_count']} critical")
    print("HOMEOSTASIS done.")


if __name__ == "__main__":
    main()
