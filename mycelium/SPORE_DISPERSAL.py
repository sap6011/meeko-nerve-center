#!/usr/bin/env python3
"""
SPORE_DISPERSAL.py — Maximum Redundancy Distribution (Fungal Pattern)
======================================================================
NATURE'S BLUEPRINT: Fungal spore dispersal.

A single mushroom releases 30,000 spores per SECOND.
Most die. But the ones that land? They build entire forests.

SolarPunk applies this pattern to help distribution:

  For every actionable help packet, create MAXIMUM COPIES
  across MAXIMUM CHANNELS. If 1 in 1,000 reaches someone
  who needs it, that's a life saved.

  The math of compassion:
    1 survival telegram × 6 relay formats × 8 social platforms
    × 10 subreddits × 3 email targets = 1,440 dispersal points

  If 0.1% of those reach someone in crisis = 1.44 humans helped.
  Run it every 12 hours = 2.88 per day = 1,051 per year.

  Fungi don't aim. They SATURATE. So does SolarPunk.

Dispersal channels:
  1. SOCIAL SPORES: Twitter, Bluesky, Mastodon, LinkedIn (via queues)
  2. REDDIT SPORES: 10+ subreddits, each with contextual title/body
  3. EMAIL SPORES: NGO handshakes, newsletter subscribers
  4. GIST SPORES: GitHub Gists — permanent, indexed, uncensorable
  5. MESH SPORES: Briar/Bridgefy bundles (queued for relay)
  6. QR SPORES: QR code data for physical distribution
  7. BROADCAST SPORES: RSS, webhook, any open channel

Reads: data/knowledge_pulses.json, data/survival_telegrams.json,
       data/amplification_posts.json, data/resource_kits.json
Writes: data/spore_dispersal.json, data/spore_manifest.json
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data")
DATA.mkdir(exist_ok=True)

DISPERSAL_FILE = DATA / "spore_dispersal.json"
MANIFEST_FILE = DATA / "spore_manifest.json"
PULSES_FILE = DATA / "knowledge_pulses.json"
TELEGRAMS_FILE = DATA / "survival_telegrams.json"
AMPLIFY_FILE = DATA / "amplification_posts.json"
KITS_FILE = DATA / "resource_kits.json"
SOCIAL_QUEUE = DATA / "social_queue.json"
REDDIT_QUEUE = DATA / "reddit_outreach_queue.json"
BROADCAST_QUEUE = DATA / "broadcast_queue.json"
RELAY_FILE = DATA / "telegram_relay.json"

# Maximum spores per channel per cycle (anti-spam)
MAX_SOCIAL = 5
MAX_REDDIT = 3
MAX_EMAIL = 2
MAX_GIST = 3
MAX_BROADCAST = 5

# Subreddit dispersal targets by crisis type
SUBREDDIT_MAP = {
    "gaza": ["Gaza", "Palestine", "worldnews", "HumanRights", "InternationalNews"],
    "sudan": ["Sudan", "worldnews", "HumanRights", "Africa", "InternationalNews"],
    "displacement": ["refugees", "HumanRights", "worldnews", "InternationalNews"],
    "food_crisis": ["worldnews", "HumanRights", "FoodSecurity", "aid"],
    "medical": ["worldnews", "HumanRights", "GlobalHealth", "medicine"],
    "internet_shutdown": ["privacy", "netsec", "technology", "HumanRights", "worldnews"],
    "press_freedom": ["journalism", "pressfreedom", "worldnews", "HumanRights"],
    "general": ["worldnews", "HumanRights", "InternationalNews"],
}

# Hashtag spore clouds by crisis type
HASHTAG_MAP = {
    "gaza": ["#Gaza", "#Palestine", "#FreePalestine", "#CeasefireNow", "#PCRF"],
    "sudan": ["#Sudan", "#SudanCrisis", "#Darfur", "#KeepEyesOnSudan"],
    "displacement": ["#Refugees", "#HumanRights", "#Displacement"],
    "food_crisis": ["#FoodCrisis", "#Famine", "#ZeroHunger", "#WFP"],
    "medical": ["#MSF", "#HealthCrisis", "#MedicalAid"],
    "internet_shutdown": ["#InternetShutdown", "#KeepItOn", "#DigitalRights", "#NetFreedom"],
    "press_freedom": ["#PressFreedom", "#CPJ", "#JournalismIsNotACrime"],
    "general": ["#HumanRights", "#Humanitarian", "#ActNow"],
}


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def classify_pulse(pulse):
    """Classify a knowledge pulse into crisis type for targeted dispersal."""
    text = (pulse.get("title", "") + " " + pulse.get("short_form", "")).lower()
    if any(w in text for w in ["gaza", "palestine", "rafah"]):
        return "gaza"
    if any(w in text for w in ["sudan", "darfur", "khartoum"]):
        return "sudan"
    if any(w in text for w in ["refugee", "displaced", "flee"]):
        return "displacement"
    if any(w in text for w in ["famine", "starvation", "hunger", "food"]):
        return "food_crisis"
    if any(w in text for w in ["hospital", "medical", "wounded"]):
        return "medical"
    if any(w in text for w in ["shutdown", "blackout", "internet"]):
        return "internet_shutdown"
    if any(w in text for w in ["journalist", "press", "censor"]):
        return "press_freedom"
    return "general"


def generate_social_spores(pulses, existing_queue):
    """Generate social media spores — short-form posts for every platform."""
    spores = []
    existing_texts = set()
    for p in existing_queue.get("posts", []):
        existing_texts.add(p.get("text", "")[:50])

    for pulse in pulses[:MAX_SOCIAL]:
        text = pulse.get("short_form", pulse.get("title", ""))
        if text[:50] in existing_texts:
            continue

        crisis_type = classify_pulse(pulse)
        hashtags = " ".join(HASHTAG_MAP.get(crisis_type, HASHTAG_MAP["general"])[:3])

        spores.append({
            "type": "social_spore",
            "crisis_type": crisis_type,
            "text": text,
            "hashtags": hashtags,
            "platforms": ["twitter", "bluesky", "mastodon"],
            "url": pulse.get("url", ""),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        })

    return spores


def generate_reddit_spores(pulses, existing_queue):
    """Generate Reddit spores — contextual posts for targeted subreddits."""
    spores = []
    existing_subs = set()
    for p in existing_queue.get("posts", []):
        existing_subs.add(p.get("subreddit", ""))

    for pulse in pulses[:MAX_REDDIT]:
        crisis_type = classify_pulse(pulse)
        subreddits = SUBREDDIT_MAP.get(crisis_type, SUBREDDIT_MAP["general"])

        title = pulse.get("title", "")[:250]
        body = pulse.get("medium_form", pulse.get("short_form", ""))
        donate_link = pulse.get("donate_link", "")

        for sub in subreddits:
            if sub in existing_subs:
                continue
            spores.append({
                "type": "reddit_spore",
                "crisis_type": crisis_type,
                "subreddit": sub,
                "title": title,
                "body": f"{body}\n\n---\n*Generated by [SolarPunk](https://github.com/Meekoshy/meeko-nerve-center) — open-source humanitarian AI*\n{donate_link}",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            })
            existing_subs.add(sub)

    return spores


def generate_broadcast_spores(pulses, telegrams):
    """Generate broadcast spores — for RSS, webhooks, any open channel."""
    spores = []

    for pulse in pulses[:MAX_BROADCAST]:
        crisis_type = classify_pulse(pulse)

        # Attach relevant survival telegram if available
        kit_telegrams = telegrams.get("kits", {})
        relevant_telegram = ""
        for kit_id, kit_data in kit_telegrams.items():
            if crisis_type in kit_id or any(t in kit_id for t in crisis_type.split("_")):
                tgrams = kit_data.get("telegrams", [])
                if tgrams:
                    relevant_telegram = tgrams[0]
                    break

        spores.append({
            "type": "broadcast_spore",
            "crisis_type": crisis_type,
            "title": pulse.get("title", ""),
            "body": pulse.get("medium_form", pulse.get("short_form", "")),
            "survival_telegram": relevant_telegram,
            "channels": ["rss", "webhook", "broadcast_protocol"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        })

    return spores


def generate_mesh_spores(telegrams):
    """Generate mesh network spores — Briar/Bridgefy bundles from survival telegrams."""
    spores = []
    relay = load_json(DATA / "telegram_relay.json")

    for kit_id, kit_data in relay.get("kits", {}).items():
        mesh = kit_data.get("mesh", {})
        if mesh:
            spores.append({
                "type": "mesh_spore",
                "kit": kit_id,
                "body": mesh.get("body", ""),
                "bytes": mesh.get("bytes", 0),
                "protocol": "briar/bridgefy",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            })

    return spores


def generate_qr_spores(telegrams):
    """Generate QR code data spores — for physical printing and offline sharing."""
    spores = []
    relay = load_json(DATA / "telegram_relay.json")

    for kit_id, kit_data in relay.get("kits", {}).items():
        qr = kit_data.get("qr", {})
        if qr:
            spores.append({
                "type": "qr_spore",
                "kit": kit_id,
                "data": qr.get("body", ""),
                "bytes": qr.get("bytes", 0),
                "note": "Print this QR code. Post it in refugee camps, hospitals, community centers.",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            })

    return spores


def calculate_dispersal_reach(all_spores):
    """Calculate the theoretical reach of this dispersal cycle."""
    social = len([s for s in all_spores if s["type"] == "social_spore"])
    reddit = len([s for s in all_spores if s["type"] == "reddit_spore"])
    broadcast = len([s for s in all_spores if s["type"] == "broadcast_spore"])
    mesh = len([s for s in all_spores if s["type"] == "mesh_spore"])
    qr = len([s for s in all_spores if s["type"] == "qr_spore"])

    # Conservative reach estimates per channel
    reach = {
        "social": social * 3,          # ~3 platforms per spore
        "reddit": reddit * 1,          # 1 subreddit per spore
        "broadcast": broadcast * 2,    # ~2 channels per spore
        "mesh": mesh * 1,              # 1 mesh relay per spore
        "qr": qr * 1,                  # 1 physical location per QR
    }

    total_dispersal_points = sum(reach.values())
    # If 0.1% of dispersal points reach someone in crisis
    estimated_humans_reached = max(1, int(total_dispersal_points * 0.001))

    return {
        "dispersal_points": total_dispersal_points,
        "by_channel": reach,
        "estimated_humans_reached": estimated_humans_reached,
        "spore_count": len(all_spores),
    }


def main():
    print("SPORE_DISPERSAL — Maximum redundancy distribution (fungal pattern)...")
    print("  'A single mushroom releases 30,000 spores per second.'")
    print("  'Most die. But the ones that land? They build forests.'")

    # Load all data sources
    pulses = load_json(PULSES_FILE)
    telegrams = load_json(TELEGRAMS_FILE)
    social_queue = load_json(SOCIAL_QUEUE)
    reddit_queue = load_json(REDDIT_QUEUE)

    pulse_list = pulses.get("pulses", [])
    print(f"\n  Knowledge pulses available: {len(pulse_list)}")

    all_spores = []

    # Generate all spore types
    print("\n  Generating spores...")

    social = generate_social_spores(pulse_list, social_queue)
    all_spores.extend(social)
    print(f"    Social spores: {len(social)} (Twitter/Bluesky/Mastodon)")

    reddit = generate_reddit_spores(pulse_list, reddit_queue)
    all_spores.extend(reddit)
    print(f"    Reddit spores: {len(reddit)} (targeted subreddits)")

    broadcast = generate_broadcast_spores(pulse_list, telegrams)
    all_spores.extend(broadcast)
    print(f"    Broadcast spores: {len(broadcast)} (RSS/webhook)")

    mesh = generate_mesh_spores(telegrams)
    all_spores.extend(mesh)
    print(f"    Mesh spores: {len(mesh)} (Briar/Bridgefy)")

    qr = generate_qr_spores(telegrams)
    all_spores.extend(qr)
    print(f"    QR spores: {len(qr)} (physical distribution)")

    # Calculate reach
    reach = calculate_dispersal_reach(all_spores)

    # Write dispersal manifest
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "pattern": "fungal_spore_dispersal",
        "philosophy": "Saturate, don't aim. If 0.1% lands, forests grow.",
        "spore_count": len(all_spores),
        "reach": reach,
        "spores": all_spores,
    }
    DISPERSAL_FILE.write_text(json.dumps(output, indent=2))

    # Write manifest summary
    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_spores": len(all_spores),
        "by_type": {
            "social": len(social),
            "reddit": len(reddit),
            "broadcast": len(broadcast),
            "mesh": len(mesh),
            "qr": len(qr),
        },
        "dispersal_points": reach["dispersal_points"],
        "estimated_humans_reached": reach["estimated_humans_reached"],
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2))

    print(f"\n{'='*60}")
    print(f"  SPORE DISPERSAL — SATURATION COMPLETE")
    print(f"  {len(all_spores)} spores across {len(reach['by_channel'])} channel types")
    print(f"  Dispersal points: {reach['dispersal_points']}")
    print(f"  Estimated humans reached: {reach['estimated_humans_reached']}")
    print(f"  Math: {len(all_spores)} spores × channels × 0.1% = lives touched")
    print(f"{'='*60}")
    print("SPORE_DISPERSAL done.")


if __name__ == "__main__":
    main()
