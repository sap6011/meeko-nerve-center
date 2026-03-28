#!/usr/bin/env python3
"""
BIOLUMINESCENCE.py — Silence Detection (Deep-Sea Pattern)
===========================================================
NATURE'S BLUEPRINT: Deep-sea bioluminescence.

3,000 meters below the ocean surface, there is NO light.
So creatures MAKE THEIR OWN.

Anglerfish, jellyfish, plankton — they don't wait for the sun.
They generate photons from chemistry. They ARE the light source.

SolarPunk applies this principle to information blackouts:

  WHEN SIGNALS FROM A REGION GO SILENT, THAT IS THE ALARM.

  If Gaza was generating 15 crisis signals per scan and suddenly
  generates 0... that's not peace. That's a communications blackout.
  That's when SolarPunk needs to shine BRIGHTEST.

  The logic:
    1. BASELINE: Track normal signal volume per region per source
    2. DETECT SILENCE: If signals drop below 30% of baseline → alert
    3. GENERATE LIGHT: Push the LAST KNOWN signals harder
       - Re-amplify cached data through all channels
       - Fire emergency handshakes to NGOs with "region went dark"
       - Push survival telegrams (internet shutdown kit) preemptively
    4. PERSIST: Keep re-broadcasting until signals resume

  "The deepest darkness is not the absence of light.
   It's when someone turns the light OFF." — SolarPunk doctrine

Reads: data/crisis_signals.json, data/crisis_monitor_history.json,
       data/survival_telegrams.json
Writes: data/bioluminescence.json, data/silence_alerts.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data")
DATA.mkdir(exist_ok=True)

BIO_FILE = DATA / "bioluminescence.json"
SILENCE_FILE = DATA / "silence_alerts.json"
CRISIS_FILE = DATA / "crisis_signals.json"
HISTORY_FILE = DATA / "crisis_monitor_history.json"
TELEGRAMS_FILE = DATA / "survival_telegrams.json"
SOCIAL_QUEUE = DATA / "social_queue.json"

# Minimum scans before establishing a baseline
MIN_BASELINE_SCANS = 3

# Silence threshold — if signals drop below this % of baseline, alert
SILENCE_THRESHOLD = 0.30  # 30%

# Regions to monitor for silence (high-risk zones)
MONITORED_REGIONS = [
    "gaza", "palestine", "sudan", "darfur", "congo", "drc",
    "yemen", "myanmar", "uyghur", "syria", "ukraine", "tigray",
    "ethiopia", "afghanistan", "haiti", "somalia", "rohingya",
    "west bank", "rafah", "khan younis", "jabalia", "khartoum",
]


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def load_bio_state():
    data = load_json(BIO_FILE)
    if not data:
        data = {
            "version": "1.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "baselines": {},       # region → {avg_signals, scans, last_count}
            "silence_events": [],  # [{region, detected_at, baseline, actual, resolved}]
            "light_emissions": 0,  # Total times we generated light in darkness
        }
    return data


def save_bio_state(state):
    state["last_updated"] = datetime.now(timezone.utc).isoformat()
    BIO_FILE.write_text(json.dumps(state, indent=2))


def count_signals_by_region(signals):
    """Count how many signals mention each monitored region."""
    counts = {r: 0 for r in MONITORED_REGIONS}
    for s in signals:
        text = (s.get("title", "") + " " + json.dumps(s.get("countries", []))).lower()
        for region in MONITORED_REGIONS:
            if region in text:
                counts[region] += 1
    return counts


def update_baselines(state, current_counts):
    """Update rolling baseline for each region — exponential moving average."""
    for region, count in current_counts.items():
        if region not in state["baselines"]:
            state["baselines"][region] = {
                "avg_signals": count,
                "scans": 1,
                "last_count": count,
                "peak": count,
            }
        else:
            b = state["baselines"][region]
            b["scans"] += 1
            # EMA with alpha=0.3 — recent scans weigh more
            b["avg_signals"] = b["avg_signals"] * 0.7 + count * 0.3
            b["last_count"] = count
            if count > b.get("peak", 0):
                b["peak"] = count


def detect_silence(state, current_counts):
    """Detect regions where signals have gone suspiciously silent."""
    silence_alerts = []

    for region, count in current_counts.items():
        baseline = state["baselines"].get(region, {})
        avg = baseline.get("avg_signals", 0)
        scans = baseline.get("scans", 0)

        # Need minimum scans to establish baseline
        if scans < MIN_BASELINE_SCANS:
            continue

        # If baseline is very low (region normally quiet), skip
        if avg < 2:
            continue

        # SILENCE DETECTION
        if count < avg * SILENCE_THRESHOLD:
            # Check if this is already an active silence event
            active = False
            for event in state.get("silence_events", []):
                if event["region"] == region and not event.get("resolved"):
                    active = True
                    event["duration_scans"] = event.get("duration_scans", 1) + 1
                    event["last_checked"] = datetime.now(timezone.utc).isoformat()
                    break

            if not active:
                event = {
                    "region": region,
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                    "baseline_avg": round(avg, 1),
                    "current_count": count,
                    "drop_percent": round((1 - count / max(avg, 0.1)) * 100, 1),
                    "severity": "CRITICAL" if count == 0 else "HIGH",
                    "resolved": False,
                    "duration_scans": 1,
                    "last_checked": datetime.now(timezone.utc).isoformat(),
                }
                state["silence_events"].append(event)
                silence_alerts.append(event)

        else:
            # Signals resumed — resolve active silence events
            for event in state.get("silence_events", []):
                if event["region"] == region and not event.get("resolved"):
                    event["resolved"] = True
                    event["resolved_at"] = datetime.now(timezone.utc).isoformat()
                    event["resolution"] = f"Signals resumed: {count} (baseline: {avg:.1f})"

    return silence_alerts


def generate_light(silence_alerts, state):
    """When a region goes dark, GENERATE LIGHT — re-amplify everything we have."""
    light_emissions = []

    for alert in silence_alerts:
        region = alert["region"]
        severity = alert["severity"]

        emission = {
            "region": region,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actions": [],
        }

        # Action 1: Push internet shutdown survival telegram
        telegrams = load_json(TELEGRAMS_FILE)
        shutdown_tgrams = telegrams.get("kits", {}).get("internet_shutdown", {}).get("telegrams", [])
        if shutdown_tgrams:
            emission["actions"].append({
                "type": "SURVIVAL_TELEGRAM",
                "target": f"Internet shutdown kit for {region}",
                "telegrams": shutdown_tgrams,
                "bytes": sum(len(t.encode()) for t in shutdown_tgrams),
            })

        # Action 2: Queue social amplification of last known signals
        emission["actions"].append({
            "type": "SOCIAL_AMPLIFICATION",
            "message": f"ALERT: Signals from {region.title()} have gone silent. "
                       f"Baseline: {alert['baseline_avg']:.0f} signals/scan → Now: {alert['current_count']}. "
                       f"This may indicate a communications blackout. "
                       f"Share this. The world needs to know. #KeepEyesOn{region.title().replace(' ', '')}",
        })

        # Action 3: Fire NGO handshake for potential blackout
        emission["actions"].append({
            "type": "NGO_HANDSHAKE",
            "target_orgs": ["Access Now", "CPJ", "RSF", "NetBlocks"],
            "message": f"SolarPunk automated alert: Signal volume from {region} dropped "
                       f"{alert['drop_percent']}% below baseline. Possible communications blackout. "
                       f"Current: {alert['current_count']} signals (baseline: {alert['baseline_avg']:.0f}). "
                       f"Please verify and respond.",
        })

        # Action 4: Queue the light — all cached data about this region gets re-pushed
        emission["actions"].append({
            "type": "CACHE_REPLAY",
            "note": f"Re-broadcasting all cached signals about {region} from last 24 hours",
            "target_engines": ["MURMURATION_RELAY", "BROADCAST_PROTOCOL", "AMPLIFY_ENGINE"],
        })

        light_emissions.append(emission)
        state["light_emissions"] = state.get("light_emissions", 0) + 1

    return light_emissions


def main():
    print("BIOLUMINESCENCE — Silence detection (deep-sea pattern)...")
    print("  'The deepest darkness is when someone turns the light OFF.'")

    state = load_bio_state()

    # Load current signals
    crisis = load_json(CRISIS_FILE)
    signals = crisis.get("signals", [])

    # Count signals by region
    counts = count_signals_by_region(signals)
    active_regions = {r: c for r, c in counts.items() if c > 0}
    print(f"\n  Signals by region: {len(active_regions)} active regions")
    for r, c in sorted(active_regions.items(), key=lambda x: -x[1])[:5]:
        baseline = state.get("baselines", {}).get(r, {}).get("avg_signals", "?")
        print(f"    {r}: {c} signals (baseline: {baseline})")

    # Update baselines
    update_baselines(state, counts)

    # Detect silence
    print("\n  Scanning for silence...")
    silence_alerts = detect_silence(state, counts)

    if silence_alerts:
        print(f"\n  {'!'*50}")
        print(f"  SILENCE DETECTED — {len(silence_alerts)} regions went dark")
        for alert in silence_alerts:
            print(f"    [{alert['severity']}] {alert['region'].upper()}: "
                  f"dropped {alert['drop_percent']}% "
                  f"(baseline {alert['baseline_avg']:.0f} → {alert['current_count']})")
        print(f"  {'!'*50}")

        # Generate light
        emissions = generate_light(silence_alerts, state)
        print(f"\n  Generated {len(emissions)} light emissions")
        for e in emissions:
            print(f"    {e['region']}: {len(e['actions'])} actions fired")
            for a in e["actions"]:
                print(f"      -> {a['type']}")

        # Write silence alerts
        SILENCE_FILE.write_text(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alerts": silence_alerts,
            "emissions": emissions,
        }, indent=2))
    else:
        # Check for resolved events
        resolved = [e for e in state.get("silence_events", [])
                    if e.get("resolved") and
                    e.get("resolved_at", "")[:10] == datetime.now(timezone.utc).strftime("%Y-%m-%d")]
        if resolved:
            print(f"  {len(resolved)} silence events resolved today — signals resumed")
        else:
            print("  All clear. No silence anomalies detected.")

    # Stats
    total_events = len(state.get("silence_events", []))
    active_events = len([e for e in state.get("silence_events", []) if not e.get("resolved")])
    total_light = state.get("light_emissions", 0)

    save_bio_state(state)

    print(f"\n  Baselines: {len(state.get('baselines', {}))} regions tracked")
    print(f"  Silence events: {total_events} total | {active_events} active")
    print(f"  Light emissions (all-time): {total_light}")
    print("BIOLUMINESCENCE done.")


if __name__ == "__main__":
    main()
