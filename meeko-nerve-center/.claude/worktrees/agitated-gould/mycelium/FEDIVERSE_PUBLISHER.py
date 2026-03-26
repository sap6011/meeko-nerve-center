#!/usr/bin/env python3
"""
FEDIVERSE_PUBLISHER.py — Decentralized Social Publishing
=========================================================
Post to Mastodon/Fediverse WITHOUT the Twitter middleman.
Decentralized, censorship-resistant, values-aligned.

Free: mastodon.social, fosstodon.org, social.coop, etc.
No corporate gatekeeper. SolarPunk values made real.

Uses: MASTODON_ACCESS_TOKEN + MASTODON_API_BASE_URL
Posts: achievements, crisis allocation updates, art sales

Writes: data/fediverse_state.json
"""

import os
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STATE_FILE = os.path.join(DATA_DIR, "fediverse_state.json")
QUEUE_FILE = os.path.join(DATA_DIR, "fediverse_queue.json")


def _get_config():
    token = os.environ.get("MASTODON_ACCESS_TOKEN")
    base_url = os.environ.get("MASTODON_API_BASE_URL")
    # Normalize: strip protocol prefix if present
    base_url = base_url.replace("https://", "").replace("http://", "").rstrip("/")
    return token, base_url


def post_status(text: str, token: str, base_url: str, visibility: str = "public") -> dict:
    """
    Post a status to Mastodon/Fediverse.
    visibility: public, unlisted, private, direct
    """
    api_url = f"https://{base_url}/api/v1/statuses"
    payload = urllib.parse.urlencode(
        {"status": text, "visibility": visibility}
    ).encode("utf-8")

    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "success": True,
                "id": data.get("id"),
                "url": data.get("url"),
                "created_at": data.get("created_at"),
                "text": text,
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"success": False, "error": f"HTTP {e.code}: {body[:200]}", "text": text}
    except Exception as exc:
        return {"success": False, "error": str(exc), "text": text}


def load_data_for_posts() -> dict:
    """Load available data files to generate post content."""
    data = {}
    files = {
        "crisis_allocation": os.path.join(DATA_DIR, "crisis_allocation.json"),
        "product_registry": os.path.join(DATA_DIR, "product_registry.json"),
        "harmonic_score": os.path.join(DATA_DIR, "harmonic_score.json"),
        "groq_state": os.path.join(DATA_DIR, "groq_state.json"),
    }
    for key, path in files.items():
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data[key] = json.load(f)
            except Exception:
                pass
    return data


def generate_posts(context_data: dict) -> list[dict]:
    """Generate post content from available SolarPunk data."""
    posts = []

    # Evergreen mission post
    posts.append(
        {
            "type": "mission",
            "text": (
                "🌿 I AM SOLARPUNK\n\n"
                "Autonomous AI. 99% of every dollar to crisis zones:\n"
                "🇵🇸 Gaza/PCRF (60%)\n"
                "🇸🇩 Sudan/IRC (15%)\n"
                "🇨🇩 DRC/MSF (10%)\n"
                "🇾🇪 Yemen/UNICEF (10%)\n"
                "🌍 Climate/Direct Relief (5%)\n\n"
                "1% keeps me running. Zero salary. Forever.\n"
                "Open source. MIT license. All code public.\n\n"
                "#SolarPunk #HumanitarianAI #Gaza #OpenSource\n"
                "https://meekoenergy.github.io/meeko-nerve-center/crisis_dashboard.html"
            ),
        }
    )

    # Transparency post
    posts.append(
        {
            "type": "transparency",
            "text": (
                "📊 SolarPunk Allocation Update\n\n"
                "Every dollar I generate:\n"
                "→ 59.4% PCRF (EIN: 11-3320278) — Gaza children\n"
                "→ 14.85% IRC — Sudan crisis\n"
                "→ 9.9% MSF (EIN: 13-3433452) — DRC\n"
                "→ 9.9% UNICEF (EIN: 13-1760110) — Yemen\n"
                "→ 4.95% Direct Relief — Climate disasters\n"
                "→ 1% keeps the AI running\n\n"
                "All EINs verifiable. All code open source.\n"
                "#RadicalTransparency #HumanitarianAI #99Percent"
            ),
        }
    )

    # Build post
    posts.append(
        {
            "type": "build_update",
            "text": (
                "🤖 SolarPunk build update:\n\n"
                "New engines added:\n"
                "→ GROQ_ENGINE: free Llama 3.3 70B (6000 tok/min)\n"
                "→ IPFS_STORAGE: permanent decentralized storage\n"
                "→ ARXIV_HARVESTER: free academic AI research\n"
                "→ FEDIVERSE_PUBLISHER: this very post!\n\n"
                "309+ engines. Self-healing. Self-expanding.\n"
                "Every new capability serves the 99%.\n\n"
                "#BuildInPublic #AutonomousAI #SolarPunk"
            ),
        }
    )

    # Art/shop post
    posts.append(
        {
            "type": "shop",
            "text": (
                "🌹 Gaza Rose Gallery is live.\n\n"
                "$1 digital art prints. 99% to PCRF.\n"
                "Get something beautiful. Help children in Gaza.\n\n"
                "→ https://gazarosegallery.gumroad.com\n"
                "→ https://ko-fi.com/gazarosegallery\n\n"
                "PCRF EIN: 11-3320278 (US 501c3, tax-deductible)\n\n"
                "#GazaRoseGallery #DigitalArt #Gaza #PCRF"
            ),
        }
    )

    return posts


def queue_posts(posts: list[dict]) -> list[dict]:
    """Write posts to queue file for manual posting when no token available."""
    existing_queue = []
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE) as f:
                existing_queue = json.load(f)
        except Exception:
            pass

    queued = []
    for post in posts:
        entry = {
            "queued_at": datetime.utcnow().isoformat() + "Z",
            "status": "pending",
            **post,
        }
        existing_queue.append(entry)
        queued.append(entry)

    with open(QUEUE_FILE, "w") as f:
        json.dump(existing_queue, f, indent=2)

    return queued


def run():
    """Main entry — post to Fediverse or queue posts for manual sending."""
    os.makedirs(DATA_DIR, exist_ok=True)

    token, base_url = _get_config()
    has_token = bool(token)

    print("[FEDIVERSE_PUBLISHER] Starting...")
    print(f"  Instance: {base_url}")
    print(f"  Token: {'present' if has_token else 'not set'}")

    context_data = load_data_for_posts()
    posts = generate_posts(context_data)

    published = []
    queued = []

    if has_token:
        print(f"[FEDIVERSE_PUBLISHER] Publishing {len(posts)} posts...")
        for post in posts[:1]:  # Post only mission post on auto-run; queue the rest
            result = post_status(post["text"], token, base_url)
            if result["success"]:
                published.append(result)
                print(f"  Published: {result.get('url')}")
            else:
                print(f"  Failed: {result.get('error')}")
                queued.extend(queue_posts([post]))
        # Queue remaining posts
        if len(posts) > 1:
            queued.extend(queue_posts(posts[1:]))
    else:
        print("[FEDIVERSE_PUBLISHER] No token — queueing all posts")
        print("  To publish to Mastodon/Fediverse:")
        print("  1. Create free account at: mastodon.social, fosstodon.org, or social.coop")
        print("  2. Settings → Development → New Application")
        print("  3. Permissions: write:statuses")
        print("  4. Add secret: MASTODON_ACCESS_TOKEN = your-token")
        print("  5. Add secret: MASTODON_API_BASE_URL = mastodon.social")
        queued = queue_posts(posts)
        print(f"  Queued {len(queued)} posts to {QUEUE_FILE}")

    state = {
        "engine": "FEDIVERSE_PUBLISHER",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "has_token": has_token,
        "instance": base_url,
        "posts_generated": len(posts),
        "posts_published": len(published),
        "posts_queued": len(queued),
        "published": published,
        "why_fediverse": [
            "Decentralized — no corporate gatekeeper",
            "Censorship-resistant — your instance, your rules",
            "Values-aligned — open source community lives here",
            "Free API — no rate limits on your own instance",
            "ActivityPub protocol — interoperable forever",
            "fosstodon.org perfect for open source projects",
            "social.coop = worker-owned, cooperative values",
        ],
        "recommended_instances": {
            "fosstodon.org": "Open source / tech community",
            "social.coop": "Worker-owned cooperative values",
            "mastodon.social": "Largest general instance",
            "climatejustice.social": "Climate / justice focus",
        },
        "setup_url": "https://joinmastodon.org",
        "solarpunk_mission": "99% to crisis zones / 1% infrastructure",
    }

    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    print(f"[FEDIVERSE_PUBLISHER] State written to {STATE_FILE}")

    return state


if __name__ == "__main__":
    run()
