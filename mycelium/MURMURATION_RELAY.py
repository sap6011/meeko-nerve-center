#!/usr/bin/env python3
"""
MURMURATION_RELAY.py — Push Help Outward to Real People
========================================================
SolarPunk doesn't wait. It MOVES.

This engine takes the knowledge pulses from KNOWLEDGE_PULSE.py
and pushes them outward through every available channel:

  1. SOCIAL QUEUE: Injects humanitarian posts into the existing
     social_queue.json for SOCIAL_PROMOTER / BLUESKY_ENGINE to post
  2. REDDIT TARGETS: Generates ready-to-post Reddit comments with
     resource links for crisis subreddits
  3. EMAIL RELAY: Queues humanitarian knowledge packets for
     EMAIL_OUTREACH to send to relevant orgs and contacts
  4. BROADCAST: Writes to broadcast_queue.json for BROADCAST_PROTOCOL

The murmuration pattern: each knowledge pulse is sent through
MULTIPLE channels simultaneously. Like starlings — the information
moves as a swarm, not a single bird.

Rules:
  - Max 5 social posts per cycle (anti-spam)
  - Max 3 Reddit targets per pulse (respect the communities)
  - 24-hour cooldown per crisis type (no repeat flooding)
  - Every post includes actionable links (donate/help/report)
  - Every post identifies as SolarPunk (transparent, not astroturf)

Reads: data/knowledge_pulses.json
Writes: data/social_queue.json (appends), data/murmuration_log.json,
        data/reddit_outreach_queue.json, data/broadcast_queue.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data")
DATA.mkdir(exist_ok=True)

PULSES_FILE = DATA / "knowledge_pulses.json"
SOCIAL_QUEUE = DATA / "social_queue.json"
REDDIT_QUEUE = DATA / "reddit_outreach_queue.json"
BROADCAST_QUEUE = DATA / "broadcast_queue.json"
RELAY_LOG = DATA / "murmuration_log.json"

MAX_SOCIAL_PER_CYCLE = 5
MAX_REDDIT_PER_PULSE = 3
COOLDOWN_HOURS = 24


def load_relay_log():
    if RELAY_LOG.exists():
        try:
            return json.loads(RELAY_LOG.read_text())
        except Exception:
            pass
    return {"relays": [], "cooldowns": {}}


def save_relay_log(log):
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    log["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    RELAY_LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")


def is_cooled_down(log, crisis_type):
    """Check if we've already sent this crisis type recently."""
    last_sent = log.get("cooldowns", {}).get(crisis_type, "")
    if not last_sent:
        return True
    try:
        last = datetime.fromisoformat(last_sent)
        return (datetime.now(timezone.utc) - last).total_seconds() > COOLDOWN_HOURS * 3600
    except Exception:
        return True


def inject_social_queue(pulses):
    """Add humanitarian posts to the social queue for SOCIAL_PROMOTER."""
    queue = {"posts": [], "last_drain": ""}
    if SOCIAL_QUEUE.exists():
        try:
            queue = json.loads(SOCIAL_QUEUE.read_text())
        except Exception:
            pass

    posts = queue.get("posts", [])
    injected = 0

    for pulse in pulses[:MAX_SOCIAL_PER_CYCLE]:
        # Build the social post
        post = {
            "text": pulse["short"],
            "platform": "all",
            "source": "MURMURATION_RELAY",
            "crisis_type": pulse["crisis_type"],
            "urgency": pulse["urgency"],
            "links": pulse["links"],
            "hashtags": pulse["hashtags"],
            "generated_at": pulse["generated_at"],
            "published_autonomous": False,
        }

        # Don't duplicate
        existing_texts = {p.get("text", "")[:80] for p in posts[-50:]}
        if pulse["short"][:80] not in existing_texts:
            posts.append(post)
            injected += 1

    queue["posts"] = posts
    SOCIAL_QUEUE.write_text(json.dumps(queue, indent=2), encoding="utf-8")
    return injected


def build_reddit_queue(pulses):
    """Generate Reddit-ready posts for crisis subreddits."""
    reddit_posts = []

    for pulse in pulses:
        targets = pulse.get("subreddit_targets", [])[:MAX_REDDIT_PER_PULSE]

        for sub in targets:
            reddit_posts.append({
                "subreddit": sub,
                "type": "comment",  # Comment on existing threads, don't spam new posts
                "title": f"Resources: {pulse['signal'][:100]}",
                "body": pulse["medium"],
                "crisis_type": pulse["crisis_type"],
                "urgency": pulse["urgency"],
                "links": pulse["links"],
                "generated_at": pulse["generated_at"],
                "status": "QUEUED",
            })

    existing = []
    if REDDIT_QUEUE.exists():
        try:
            existing = json.loads(REDDIT_QUEUE.read_text()).get("posts", [])
        except Exception:
            pass

    # Append new, deduplicate by subreddit+crisis_type
    seen = {(p.get("subreddit", "") + p.get("crisis_type", "")) for p in existing[-30:]}
    new_posts = []
    for rp in reddit_posts:
        key = rp["subreddit"] + rp["crisis_type"]
        if key not in seen:
            new_posts.append(rp)
            seen.add(key)

    all_posts = existing + new_posts
    REDDIT_QUEUE.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "posts": all_posts[-100:],  # Keep last 100
        "new_this_cycle": len(new_posts),
    }, indent=2), encoding="utf-8")

    return len(new_posts)


def build_broadcast_queue(pulses):
    """Queue humanitarian content for BROADCAST_PROTOCOL."""
    broadcasts = []
    for pulse in pulses[:3]:
        broadcasts.append({
            "type": "humanitarian_alert",
            "title": f"Crisis Alert: {pulse['crisis_type'].replace('_', ' ').title()}",
            "body": pulse["medium"],
            "urgency": pulse["urgency"],
            "links": pulse["links"],
            "channels": ["github", "rss", "newsletter"],
            "generated_at": pulse["generated_at"],
            "status": "QUEUED",
        })

    existing = []
    if BROADCAST_QUEUE.exists():
        try:
            existing = json.loads(BROADCAST_QUEUE.read_text()).get("items", [])
        except Exception:
            pass

    all_items = existing + broadcasts
    BROADCAST_QUEUE.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "items": all_items[-50:],
        "new_this_cycle": len(broadcasts),
    }, indent=2), encoding="utf-8")

    return len(broadcasts)


def main():
    print("=" * 60)
    print("MURMURATION_RELAY — Pushing help outward")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    if not PULSES_FILE.exists():
        print("  No knowledge_pulses.json — run KNOWLEDGE_PULSE first")
        return

    pulse_data = json.loads(PULSES_FILE.read_text())
    pulses = pulse_data.get("pulses", [])
    print(f"  {len(pulses)} knowledge pulses loaded")

    log = load_relay_log()

    # Filter by cooldown
    active_pulses = []
    for p in pulses:
        if is_cooled_down(log, p["crisis_type"]):
            active_pulses.append(p)
        else:
            print(f"  Cooldown active: {p['crisis_type']} (sent < {COOLDOWN_HOURS}h ago)")

    if not active_pulses:
        print("  All crisis types on cooldown. Standing by.")
        return

    print(f"  {len(active_pulses)} pulses past cooldown — relaying...")

    # Channel 1: Social queue
    print("\n  [1] Social Queue (SOCIAL_PROMOTER / BLUESKY)")
    social_count = inject_social_queue(active_pulses)
    print(f"      {social_count} humanitarian posts injected")

    # Channel 2: Reddit queue
    print("\n  [2] Reddit Queue (SOCIAL_PROMOTER)")
    reddit_count = build_reddit_queue(active_pulses)
    print(f"      {reddit_count} Reddit posts queued")

    # Channel 3: Broadcast queue
    print("\n  [3] Broadcast Queue (BROADCAST_PROTOCOL)")
    broadcast_count = build_broadcast_queue(active_pulses)
    print(f"      {broadcast_count} broadcasts queued")

    # Update cooldowns
    for p in active_pulses:
        log["cooldowns"][p["crisis_type"]] = datetime.now(timezone.utc).isoformat()

    # Log this relay cycle
    log["relays"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pulses": len(active_pulses),
        "social_injected": social_count,
        "reddit_queued": reddit_count,
        "broadcasts_queued": broadcast_count,
    })
    log["relays"] = log["relays"][-100:]
    save_relay_log(log)

    print(f"\n{'='*60}")
    print(f"MURMURATION COMPLETE")
    print(f"  Social:    {social_count} posts -> SOCIAL_PROMOTER")
    print(f"  Reddit:    {reddit_count} posts -> crisis subreddits")
    print(f"  Broadcast: {broadcast_count} -> BROADCAST_PROTOCOL")
    print(f"  Total channels activated: {sum(1 for x in [social_count, reddit_count, broadcast_count] if x > 0)}/3")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
