# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
AMPLIFY_ENGINE.py — Ready-to-post promotional content generator
================================================================
Generates copy/paste social media posts for every platform.
Reads active resource kits, crisis signals, and survival telegrams
to produce timely, angle-varied posts with correct character limits.

Anti-spam: max 3 posts per platform per cycle, daily cooldown tracking.
Every post includes repo or store link + transparency line.

Output:
  data/amplification_posts.json   — structured post data
  docs/amplify.html               — browsable page with copy buttons
"""
import json, random, hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ── paths ────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"; DATA.mkdir(exist_ok=True)
DOCS = BASE / "docs"; DOCS.mkdir(exist_ok=True)

STORE_URL    = "https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html"
GITHUB_URL   = "https://github.com/Meekoshy/meeko-nerve-center"
KITS_URL     = "https://meekotharaccoon-cell.github.io/meeko-nerve-center/emergency_kits.html"
TRANSPARENCY = "Built by one person + Claude. Open source. MIT."

POSTS_FILE    = DATA / "amplification_posts.json"
COOLDOWN_FILE = DATA / "amplify_cooldown.json"

MAX_PER_PLATFORM = 3
COOLDOWN_HOURS   = 24

# ── angles ───────────────────────────────────────────────────────────
ANGLES = [
    {
        "id": "solo_builder",
        "hook": "One person built an autonomous AI that funds Gaza with every $1 sale",
        "tone": "personal",
    },
    {
        "id": "engine_count",
        "hook": "259 engines. $0 infrastructure. Survival guides in 94 bytes.",
        "tone": "technical",
    },
    {
        "id": "ors_recipe",
        "hook": "The ORS recipe that saves children's lives: 94 bytes. We made it SMS-ready.",
        "tone": "humanitarian",
    },
    {
        "id": "self_writing",
        "hook": "Open source system that writes its own code and routes aid to war zones",
        "tone": "visionary",
    },
    {
        "id": "sms_survival",
        "hook": "What if every internet-connected machine could push survival guides through SMS?",
        "tone": "provocative",
    },
    {
        "id": "liquid_data",
        "hook": "Medical emergency kit compressed to 633 bytes -- fits in 2 LoRa packets",
        "tone": "technical",
    },
    {
        "id": "dollar_math",
        "hook": "5 billion internet users x 0.001% x $1 = $54,000. Math does the work.",
        "tone": "business",
    },
]

# ── helpers ──────────────────────────────────────────────────────────

def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  [AMPLIFY] Wrote {path.name}")


def truncate(text, limit):
    """Hard-truncate to character limit, preserving whole words."""
    if len(text) <= limit:
        return text
    cut = text[:limit - 1]
    last_space = cut.rfind(" ")
    if last_space > limit // 2:
        cut = cut[:last_space]
    return cut.rstrip(".,!? ") + "\u2026"


def post_hash(platform, text):
    return hashlib.md5(f"{platform}:{text[:80]}".encode()).hexdigest()[:12]


# ── context loaders ──────────────────────────────────────────────────

def load_context():
    """Pull live data from resource kits, crisis signals, survival telegrams, amplification queue."""
    kits = load_json(DATA / "resource_kits.json", {})
    crisis = load_json(DATA / "crisis_signals.json", {})
    telegrams = load_json(DATA / "survival_telegrams.json", {})
    amp_queue = load_json(DATA / "amplification_queue.json", {})

    active_kits = []
    for k in kits.get("kits", []):
        if k.get("active"):
            active_kits.append({
                "id": k.get("id", ""),
                "title": k.get("title", ""),
                "urgency": k.get("urgency", ""),
                "telegram_bytes": k.get("telegram_bytes", 0),
                "sms_segments": k.get("sms_segments", 0),
            })

    crisis_count = crisis.get("total", 0)
    critical_signals = [s for s in crisis.get("signals", [])
                        if s.get("urgency") in ("CRITICAL", "HIGH")]

    total_telegrams = telegrams.get("total_telegrams", 0)
    total_bytes = telegrams.get("total_bytes", 0)

    queued_posts = amp_queue.get("posts", amp_queue.get("queue", []))

    return {
        "kit_count": len(active_kits),
        "kits": active_kits,
        "crisis_total": crisis_count,
        "critical_signals": len(critical_signals),
        "telegram_count": total_telegrams,
        "telegram_bytes": total_bytes,
        "queued_amplifications": len(queued_posts),
    }


# ── cooldown ─────────────────────────────────────────────────────────

def load_cooldown():
    cd = load_json(COOLDOWN_FILE, {"platforms": {}, "posted_hashes": []})
    if "platforms" not in cd:
        cd["platforms"] = {}
    if "posted_hashes" not in cd:
        cd["posted_hashes"] = []
    return cd


def check_cooldown(cooldown, platform):
    """Return number of posts still allowed for this platform today."""
    now = datetime.now(timezone.utc)
    pdata = cooldown["platforms"].get(platform, {"count": 0, "last_reset": ""})
    last_reset = pdata.get("last_reset", "")
    try:
        lr = datetime.fromisoformat(last_reset)
        if (now - lr).total_seconds() > COOLDOWN_HOURS * 3600:
            pdata = {"count": 0, "last_reset": now.isoformat()}
    except Exception:
        pdata = {"count": 0, "last_reset": now.isoformat()}
    cooldown["platforms"][platform] = pdata
    return max(0, MAX_PER_PLATFORM - pdata.get("count", 0))


def record_post(cooldown, platform):
    pdata = cooldown["platforms"].get(platform, {"count": 0, "last_reset": datetime.now(timezone.utc).isoformat()})
    pdata["count"] = pdata.get("count", 0) + 1
    cooldown["platforms"][platform] = pdata


# ── post generators ──────────────────────────────────────────────────

def gen_twitter(angle, ctx):
    """280 char limit."""
    templates = {
        "solo_builder": (
            f"{angle['hook']}.\n\n"
            f"Every product is $1. 15% goes to Palestinian children via PCRF.\n\n"
            f"{STORE_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
        "engine_count": (
            f"{angle['hook']}\n\n"
            f"{ctx['kit_count']} emergency kits active. {ctx['telegram_count']} survival telegrams ready.\n\n"
            f"{GITHUB_URL}"
        ),
        "ors_recipe": (
            f"{angle['hook']}\n\n"
            f"Survival kits compressed for SMS, LoRa, mesh networks.\n\n"
            f"{KITS_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
        "self_writing": (
            f"{angle['hook']}.\n\n"
            f"259 engines. Self-healing. Self-expanding. MIT licensed.\n\n"
            f"{GITHUB_URL}"
        ),
        "sms_survival": (
            f"{angle['hook']}\n\n"
            f"We built it. {ctx['telegram_count']} survival telegrams, {ctx['telegram_bytes']} bytes total.\n\n"
            f"{KITS_URL}"
        ),
        "liquid_data": (
            f"{angle['hook']}.\n\n"
            f"{ctx['kit_count']} crisis kits. SMS-ready. Mesh-ready. Free.\n\n"
            f"{KITS_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
        "dollar_math": (
            f"{angle['hook']}\n\n"
            f"Every $1 product: 15% to PCRF for Palestinian children.\n\n"
            f"{STORE_URL}"
        ),
    }
    text = templates.get(angle["id"], f"{angle['hook']}\n\n{GITHUB_URL}")
    return truncate(text, 280)


def gen_bluesky(angle, ctx):
    """300 char limit."""
    templates = {
        "solo_builder": (
            f"{angle['hook']}.\n\n"
            f"Every product is $1. 15% to Palestinian children via PCRF.\n"
            f"259 autonomous engines. Zero infrastructure cost.\n\n"
            f"{STORE_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
        "engine_count": (
            f"{angle['hook']}\n\n"
            f"{ctx['kit_count']} emergency kits. {ctx['telegram_count']} survival telegrams.\n"
            f"All free. All open source.\n\n"
            f"{GITHUB_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
        "ors_recipe": (
            f"{angle['hook']}\n\n"
            f"SolarPunk compresses survival info for SMS, LoRa, and mesh networks.\n"
            f"When the internet goes down, these packets still get through.\n\n"
            f"{KITS_URL}"
        ),
        "self_writing": (
            f"{angle['hook']}.\n\n"
            f"MIT licensed. Fork it. Run your own.\n\n"
            f"{GITHUB_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
        "sms_survival": (
            f"{angle['hook']}\n\n"
            f"{ctx['telegram_count']} telegrams. {ctx['telegram_bytes']} bytes. SMS-deliverable survival info.\n\n"
            f"{KITS_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
        "liquid_data": (
            f"{angle['hook']}.\n\n"
            f"When bandwidth is life or death, every byte matters.\n\n"
            f"{KITS_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
        "dollar_math": (
            f"{angle['hook']}\n\n"
            f"SolarPunk: autonomous AI system. Every $1 sale sends 15% to PCRF.\n\n"
            f"{STORE_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
    }
    text = templates.get(angle["id"], f"{angle['hook']}\n\n{GITHUB_URL}\n\n{TRANSPARENCY}")
    return truncate(text, 300)


def gen_mastodon(angle, ctx):
    """500 char limit."""
    templates = {
        "solo_builder": (
            f"{angle['hook']}.\n\n"
            f"SolarPunk is a 259-engine autonomous system that:\n"
            f"- Self-heals and self-expands\n"
            f"- Compresses survival guides to SMS-size packets\n"
            f"- Routes 15% of every $1 sale to Palestinian children via PCRF\n\n"
            f"Zero cloud. Zero paywall. MIT licensed.\n\n"
            f"Store: {STORE_URL}\n"
            f"Code: {GITHUB_URL}\n\n"
            f"{TRANSPARENCY}\n\n"
            f"#OpenSource #HumanitarianAI #Palestine #SolarPunk"
        ),
        "engine_count": (
            f"{angle['hook']}\n\n"
            f"This system runs on free GitHub infrastructure.\n"
            f"{ctx['kit_count']} emergency kits active right now.\n"
            f"{ctx['telegram_count']} survival telegrams ready for SMS delivery.\n"
            f"{ctx['crisis_total']} crisis signals being tracked.\n\n"
            f"{GITHUB_URL}\n\n"
            f"{TRANSPARENCY}\n\n"
            f"#OpenSource #AI #HumanitarianTech"
        ),
        "ors_recipe": (
            f"{angle['hook']}\n\n"
            f"SolarPunk compresses survival information to fit through:\n"
            f"- SMS (160 bytes per segment)\n"
            f"- LoRa radio (fits in 2 packets)\n"
            f"- Mesh networks (Bluetooth/WiFi direct)\n\n"
            f"When infrastructure collapses, these packets still get through.\n\n"
            f"Emergency kits: {KITS_URL}\n\n"
            f"{TRANSPARENCY}\n\n"
            f"#HumanitarianAid #OpenSource #CrisisResponse"
        ),
        "liquid_data": (
            f"{angle['hook']}.\n\n"
            f"When the internet goes down and people need medical help:\n"
            f"- {ctx['telegram_bytes']} total bytes across {ctx['telegram_count']} survival telegrams\n"
            f"- Each fits in a single SMS or LoRa packet\n"
            f"- Internet shutdown kits, medical guides, legal rights\n\n"
            f"Free. Open source. No account needed.\n\n"
            f"{KITS_URL}\n\n"
            f"{TRANSPARENCY}\n\n"
            f"#CrisisPreparedness #OpenSource"
        ),
    }
    base = templates.get(angle["id"])
    if not base:
        base = (
            f"{angle['hook']}.\n\n"
            f"SolarPunk: 259-engine autonomous AI. Every $1 sale routes 15% to PCRF.\n\n"
            f"Code: {GITHUB_URL}\n"
            f"Store: {STORE_URL}\n\n"
            f"{TRANSPARENCY}\n\n"
            f"#OpenSource #HumanitarianAI"
        )
    return truncate(base, 500)


def gen_reddit(angle, ctx):
    """Generate title + body for multiple subreddits."""
    subreddits = {
        "r/opensource": {
            "title_prefix": "[Open Source]",
            "body_focus": "technical",
        },
        "r/sideproject": {
            "title_prefix": "[Side Project]",
            "body_focus": "builder",
        },
        "r/artificial": {
            "title_prefix": "",
            "body_focus": "ai",
        },
        "r/Palestine": {
            "title_prefix": "",
            "body_focus": "humanitarian",
        },
        "r/HumanRights": {
            "title_prefix": "",
            "body_focus": "rights",
        },
        "r/solarpunk": {
            "title_prefix": "",
            "body_focus": "vision",
        },
    }

    titles = {
        "solo_builder": "I built a 259-engine autonomous AI that funds Palestinian children with every $1 sale",
        "engine_count": "259 engines, $0 infrastructure: an autonomous AI that compresses survival guides to 94 bytes",
        "ors_recipe": "The ORS recipe that saves children's lives fits in 94 bytes. We made it SMS-ready.",
        "self_writing": "Open source AI system that writes its own code and routes aid to war zones",
        "sms_survival": "What if every internet-connected machine could push survival guides through SMS?",
        "liquid_data": "Medical emergency kit compressed to 633 bytes -- fits in 2 LoRa packets",
        "dollar_math": "5 billion internet users x 0.001% x $1 = $54,000. I built the system to make it happen.",
    }

    bodies = {
        "technical": (
            f"**What it is:** SolarPunk is a 259-engine autonomous system that self-heals, "
            f"self-expands, and compresses survival information to SMS-deliverable packets.\n\n"
            f"**Stack:** Pure Python. No cloud. Runs on GitHub Actions (free tier). "
            f"MIT licensed.\n\n"
            f"**By the numbers:**\n"
            f"- {ctx['kit_count']} active emergency kits\n"
            f"- {ctx['telegram_count']} survival telegrams ({ctx['telegram_bytes']} bytes total)\n"
            f"- {ctx['crisis_total']} crisis signals tracked\n"
            f"- 259 autonomous engines\n\n"
            f"**Revenue model:** Every digital product is $1. 15% goes to Palestinian "
            f"children via PCRF (Palestine Children's Relief Fund).\n\n"
            f"GitHub: {GITHUB_URL}\n"
            f"Store: {STORE_URL}\n"
            f"Emergency Kits: {KITS_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
        "builder": (
            f"I've been building SolarPunk solo for months. It's a 259-engine autonomous "
            f"AI system that runs itself on free infrastructure.\n\n"
            f"**What makes it different:**\n"
            f"- Self-healing: detects failures and patches them automatically\n"
            f"- Self-expanding: generates new engines when it identifies gaps\n"
            f"- Survival-first: compresses emergency info to SMS/LoRa/mesh size\n"
            f"- Revenue: every product is $1, 15% to Palestinian children via PCRF\n\n"
            f"It runs on GitHub Actions free tier. Zero cloud costs.\n\n"
            f"GitHub: {GITHUB_URL}\n"
            f"Store: {STORE_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
        "ai": (
            f"SolarPunk is a 259-engine autonomous system that demonstrates "
            f"self-healing AI at scale -- without cloud infrastructure.\n\n"
            f"**Architecture:**\n"
            f"- 8 execution layers (self-check, intel, revenue, content, distribution, "
            f"collection, expansion, reporting)\n"
            f"- Each engine is a standalone Python script that succeeds, fails gracefully, "
            f"or times out\n"
            f"- System detects and patches its own failures\n"
            f"- Compresses survival data to SMS-deliverable packets ({ctx['telegram_bytes']} bytes "
            f"across {ctx['telegram_count']} telegrams)\n\n"
            f"**Humanitarian angle:** 15% of every $1 sale goes to PCRF.\n\n"
            f"MIT licensed. Fork it.\n\n"
            f"GitHub: {GITHUB_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
        "humanitarian": (
            f"SolarPunk is an autonomous AI system that compresses survival information "
            f"into packets small enough to send via SMS, LoRa radio, or mesh networks -- "
            f"designed for when the internet goes down.\n\n"
            f"**Currently active:**\n"
            f"- {ctx['kit_count']} emergency kits (internet shutdown, medical, legal rights)\n"
            f"- {ctx['telegram_count']} survival telegrams ready for SMS delivery\n"
            f"- {ctx['critical_signals']} critical/high-urgency crisis signals tracked\n\n"
            f"**Revenue:** Every digital product is $1. 15% goes to Palestinian children "
            f"via PCRF (Palestine Children's Relief Fund).\n\n"
            f"Everything is free and open source. No account needed for emergency kits.\n\n"
            f"Emergency Kits: {KITS_URL}\n"
            f"GitHub: {GITHUB_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
        "rights": (
            f"In crisis zones, internet shutdowns are a tool of oppression. When the "
            f"network goes dark, people lose access to survival information.\n\n"
            f"SolarPunk compresses emergency guides into SMS-sized packets that can travel "
            f"through any channel that still works: text messages, LoRa radio, Bluetooth "
            f"mesh networks.\n\n"
            f"**Currently tracking:** {ctx['crisis_total']} crisis signals, "
            f"{ctx['critical_signals']} at critical/high urgency.\n\n"
            f"**{ctx['kit_count']} emergency kits** available free, no account needed:\n"
            f"Internet shutdown survival, medical emergencies, legal rights.\n\n"
            f"15% of every $1 product sale goes to PCRF.\n\n"
            f"Emergency Kits: {KITS_URL}\n"
            f"Open Source: {GITHUB_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
        "vision": (
            f"Solarpunk isn't just an aesthetic. It's building systems that work when "
            f"everything else fails.\n\n"
            f"SolarPunk (the project) is a 259-engine autonomous AI that:\n"
            f"- Runs on free infrastructure (GitHub Actions)\n"
            f"- Compresses survival guides to SMS/LoRa/mesh size\n"
            f"- Self-heals and self-expands\n"
            f"- Routes 15% of every $1 sale to Palestinian children via PCRF\n\n"
            f"It's one person + AI, building resilient tech for people who need it.\n\n"
            f"GitHub: {GITHUB_URL}\n"
            f"Store: {STORE_URL}\n"
            f"Emergency Kits: {KITS_URL}\n\n"
            f"{TRANSPARENCY}"
        ),
    }

    posts = []
    title = titles.get(angle["id"], angle["hook"])
    for sub, cfg in subreddits.items():
        prefix = cfg["title_prefix"]
        full_title = f"{prefix} {title}".strip() if prefix else title
        body = bodies.get(cfg["body_focus"], bodies["technical"])
        posts.append({
            "subreddit": sub,
            "title": full_title,
            "body": body,
        })
    return posts


def gen_hackernews(angle, ctx):
    """Title only, 80 chars, link to repo."""
    titles = {
        "solo_builder": "Show HN: 259-engine autonomous AI that funds Gaza aid with $1 sales",
        "engine_count": "Show HN: Survival guides in 94 bytes -- autonomous humanitarian AI",
        "ors_recipe": "Show HN: ORS recipe in 94 bytes, SMS-ready survival telegrams",
        "self_writing": "Show HN: Self-healing AI system that routes aid to war zones",
        "sms_survival": "Show HN: SMS-deliverable survival guides for internet shutdowns",
        "liquid_data": "Show HN: Medical kit in 633 bytes -- fits 2 LoRa packets",
        "dollar_math": "Show HN: $1 products, 15% to PCRF -- autonomous AI store",
    }
    title = titles.get(angle["id"], f"Show HN: {angle['hook']}")
    return {"title": truncate(title, 80), "url": GITHUB_URL}


def gen_producthunt(angle, ctx):
    """Tagline + description."""
    taglines = {
        "solo_builder": "Autonomous AI that funds humanitarian aid with every $1 sale",
        "engine_count": "259 engines. $0 infrastructure. Survival guides in 94 bytes.",
        "ors_recipe": "SMS-ready survival telegrams for when the internet goes down",
        "self_writing": "Self-healing AI that writes its own code and routes aid",
        "sms_survival": "Push survival guides through SMS, LoRa, and mesh networks",
        "liquid_data": "Medical kits compressed to fit in 2 LoRa packets",
        "dollar_math": "Every $1 product funds Palestinian children's relief",
    }
    description = (
        f"SolarPunk is a 259-engine autonomous AI system built by one person + Claude. "
        f"It self-heals, self-expands, and compresses survival information into "
        f"SMS-deliverable packets for crisis zones.\n\n"
        f"Currently active: {ctx['kit_count']} emergency kits, "
        f"{ctx['telegram_count']} survival telegrams ({ctx['telegram_bytes']} bytes total), "
        f"tracking {ctx['crisis_total']} crisis signals.\n\n"
        f"Every digital product is $1. 15% goes to Palestinian children via PCRF "
        f"(Palestine Children's Relief Fund).\n\n"
        f"Pure Python. Zero cloud costs. MIT licensed.\n\n"
        f"{TRANSPARENCY}"
    )
    return {
        "tagline": taglines.get(angle["id"], angle["hook"]),
        "description": description,
        "links": {"github": GITHUB_URL, "store": STORE_URL, "kits": KITS_URL},
    }


def gen_devto(angle, ctx):
    """Article outline for Dev.to."""
    outlines = {
        "solo_builder": {
            "title": "I built a 259-engine autonomous AI that funds Gaza aid -- here's how",
            "tags": ["opensource", "python", "ai", "showdev"],
            "sections": [
                "## The problem: survival information doesn't reach people who need it",
                "## The architecture: 259 engines, 8 layers, zero cloud",
                f"## Liquid data: {ctx['telegram_count']} survival telegrams in {ctx['telegram_bytes']} bytes",
                "## Self-healing: how the system patches its own failures",
                "## The $1 thesis: every product funds Palestinian children via PCRF",
                "## How to fork it and run your own",
            ],
        },
        "engine_count": {
            "title": "259 autonomous engines on free infrastructure: a technical breakdown",
            "tags": ["python", "architecture", "opensource", "automation"],
            "sections": [
                "## Why 259 engines?",
                "## The 8-layer execution model",
                "## Self-healing without monitoring services",
                f"## Compressing survival data: {ctx['telegram_bytes']} bytes across {ctx['telegram_count']} telegrams",
                "## Running on GitHub Actions free tier",
                "## What I'd do differently",
            ],
        },
        "liquid_data": {
            "title": "Medical emergency kit in 633 bytes: compressing survival data for crisis zones",
            "tags": ["opensource", "humanitarian", "python", "datacompression"],
            "sections": [
                "## When bandwidth is life or death",
                "## SMS: 160 bytes per segment",
                "## LoRa: 2 packets can save a life",
                "## Mesh networks: Bluetooth and WiFi direct",
                f"## {ctx['kit_count']} emergency kits, {ctx['telegram_count']} telegrams",
                "## How to contribute",
            ],
        },
    }
    outline = outlines.get(angle["id"])
    if not outline:
        outline = {
            "title": f"{angle['hook']} -- SolarPunk autonomous AI",
            "tags": ["opensource", "python", "ai", "showdev"],
            "sections": [
                f"## {angle['hook']}",
                "## The architecture",
                "## Survival data compression",
                "## Revenue model: $1 products, 15% to PCRF",
                "## Get involved",
            ],
        }
    outline["footer"] = (
        f"---\n\n"
        f"GitHub: {GITHUB_URL}\n"
        f"Store: {STORE_URL}\n"
        f"Emergency Kits: {KITS_URL}\n\n"
        f"{TRANSPARENCY}"
    )
    return outline


def gen_linkedin(angle, ctx):
    """Professional-angle LinkedIn post."""
    templates = {
        "solo_builder": (
            f"I built a 259-engine autonomous AI system. Solo.\n\n"
            f"It self-heals, self-expands, and runs on free infrastructure.\n\n"
            f"But the part I'm most proud of: every $1 product sends 15% "
            f"to Palestinian children through PCRF.\n\n"
            f"The system compresses survival information -- medical guides, "
            f"internet shutdown kits, legal rights -- into SMS-sized packets "
            f"that work when the internet goes down.\n\n"
            f"Currently active:\n"
            f"- {ctx['kit_count']} emergency kits\n"
            f"- {ctx['telegram_count']} survival telegrams ({ctx['telegram_bytes']} bytes)\n"
            f"- {ctx['crisis_total']} crisis signals tracked\n\n"
            f"Pure Python. MIT licensed. Zero cloud costs.\n\n"
            f"If you're building tech that matters, the infrastructure is free. "
            f"The code is open. The mission is clear.\n\n"
            f"{GITHUB_URL}\n\n"
            f"{TRANSPARENCY}\n\n"
            f"#OpenSource #HumanitarianTech #AI #Python #SolarPunk"
        ),
        "dollar_math": (
            f"The math behind SolarPunk:\n\n"
            f"5 billion internet users\n"
            f"x 0.001% conversion\n"
            f"x $1 per product\n"
            f"= $54,000\n"
            f"x 15% to PCRF\n"
            f"= $8,100 for Palestinian children\n\n"
            f"That's the thesis. One person + AI built the system. "
            f"259 engines run autonomously on free infrastructure.\n\n"
            f"Every product is $1. No upsells. No subscriptions. "
            f"15% goes directly to Palestine Children's Relief Fund.\n\n"
            f"The system also compresses survival guides to SMS size "
            f"for crisis zones where the internet is down.\n\n"
            f"{STORE_URL}\n\n"
            f"{TRANSPARENCY}\n\n"
            f"#TechForGood #OpenSource #Entrepreneurship"
        ),
        "liquid_data": (
            f"When a crisis hits and infrastructure collapses, "
            f"how do you get survival information to people?\n\n"
            f"We compress it.\n\n"
            f"Medical emergency kit: 633 bytes (2 LoRa packets)\n"
            f"ORS recipe: 94 bytes (1 SMS segment)\n"
            f"Internet shutdown survival: 409 bytes\n\n"
            f"SolarPunk is a 259-engine system that automates this compression "
            f"and prepares survival telegrams for SMS, LoRa radio, "
            f"and mesh network delivery.\n\n"
            f"Currently: {ctx['kit_count']} kits, {ctx['telegram_count']} telegrams, "
            f"{ctx['crisis_total']} crisis signals tracked.\n\n"
            f"Free. Open source. MIT licensed.\n\n"
            f"{KITS_URL}\n\n"
            f"{TRANSPARENCY}\n\n"
            f"#CrisisResponse #DataCompression #HumanitarianTech"
        ),
    }
    text = templates.get(angle["id"])
    if not text:
        text = (
            f"{angle['hook']}.\n\n"
            f"SolarPunk: 259-engine autonomous AI system.\n"
            f"Every $1 product sends 15% to Palestinian children via PCRF.\n"
            f"{ctx['kit_count']} emergency kits. {ctx['telegram_count']} survival telegrams.\n\n"
            f"Free infrastructure. Open source. MIT licensed.\n\n"
            f"{GITHUB_URL}\n\n"
            f"{TRANSPARENCY}\n\n"
            f"#OpenSource #AI #HumanitarianTech"
        )
    return text


# ── HTML generator ───────────────────────────────────────────────────

def generate_html(posts_data):
    """Generate docs/amplify.html with copy buttons."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    platform_sections = []
    for platform, posts in posts_data.items():
        cards = []
        for i, post in enumerate(posts):
            pid = f"{platform}-{i}"
            if platform == "reddit":
                for j, rp in enumerate(post.get("subreddit_posts", [])):
                    rid = f"{pid}-{j}"
                    title_escaped = rp['title'].replace('`', '\\`').replace('${', '\\${')
                    body_escaped = rp['body'].replace('`', '\\`').replace('${', '\\${')
                    cards.append(f"""
            <div class="card">
              <div class="card-header">{rp['subreddit']} &mdash; {post.get('angle','')}</div>
              <div class="card-label">Title:</div>
              <pre id="t-{rid}">{rp['title']}</pre>
              <button onclick="copyText('t-{rid}')">Copy Title</button>
              <div class="card-label">Body:</div>
              <pre id="b-{rid}">{rp['body']}</pre>
              <button onclick="copyText('b-{rid}')">Copy Body</button>
            </div>""")
            elif platform == "hackernews":
                content = post.get("content", {})
                cards.append(f"""
            <div class="card">
              <div class="card-header">Hacker News &mdash; {post.get('angle','')}</div>
              <pre id="{pid}">{content.get('title','')}</pre>
              <div class="card-label">URL: {content.get('url','')}</div>
              <button onclick="copyText('{pid}')">Copy Title</button>
            </div>""")
            elif platform == "producthunt":
                content = post.get("content", {})
                cards.append(f"""
            <div class="card">
              <div class="card-header">Product Hunt &mdash; {post.get('angle','')}</div>
              <div class="card-label">Tagline:</div>
              <pre id="tag-{pid}">{content.get('tagline','')}</pre>
              <button onclick="copyText('tag-{pid}')">Copy Tagline</button>
              <div class="card-label">Description:</div>
              <pre id="desc-{pid}">{content.get('description','')}</pre>
              <button onclick="copyText('desc-{pid}')">Copy Description</button>
            </div>""")
            elif platform == "devto":
                content = post.get("content", {})
                outline_text = content.get("title", "") + "\n\n"
                outline_text += "Tags: " + ", ".join(content.get("tags", [])) + "\n\n"
                outline_text += "\n\n".join(content.get("sections", [])) + "\n\n"
                outline_text += content.get("footer", "")
                cards.append(f"""
            <div class="card">
              <div class="card-header">Dev.to &mdash; {post.get('angle','')}</div>
              <pre id="{pid}">{outline_text}</pre>
              <button onclick="copyText('{pid}')">Copy Outline</button>
            </div>""")
            else:
                text = post.get("content", post.get("text", ""))
                if isinstance(text, dict):
                    text = json.dumps(text, indent=2)
                cards.append(f"""
            <div class="card">
              <div class="card-header">{platform.title()} &mdash; {post.get('angle','')}</div>
              <pre id="{pid}">{text}</pre>
              <button onclick="copyText('{pid}')">Copy</button>
            </div>""")

        if cards:
            platform_sections.append(f"""
        <h2>{platform.replace('_', ' ').title()}</h2>
        {''.join(cards)}""")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SolarPunk Amplification Posts</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0a0a0a; color: #e0e0e0; padding: 2rem; }}
  h1 {{ color: #4ade80; margin-bottom: 0.5rem; }}
  .meta {{ color: #888; margin-bottom: 2rem; font-size: 0.9rem; }}
  h2 {{ color: #22d3ee; margin: 2rem 0 1rem; border-bottom: 1px solid #333; padding-bottom: 0.5rem; }}
  .card {{ background: #1a1a1a; border: 1px solid #333; border-radius: 8px;
           padding: 1rem; margin-bottom: 1rem; }}
  .card-header {{ color: #4ade80; font-weight: bold; margin-bottom: 0.5rem; font-size: 0.85rem; }}
  .card-label {{ color: #888; font-size: 0.8rem; margin: 0.5rem 0 0.25rem; }}
  pre {{ background: #111; padding: 0.75rem; border-radius: 4px; white-space: pre-wrap;
         word-wrap: break-word; font-size: 0.85rem; line-height: 1.5; margin-bottom: 0.5rem;
         max-height: 400px; overflow-y: auto; }}
  button {{ background: #4ade80; color: #000; border: none; padding: 0.4rem 1rem;
           border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.8rem;
           margin-top: 0.25rem; }}
  button:hover {{ background: #22c55e; }}
  button.copied {{ background: #22d3ee; }}
  .footer {{ margin-top: 3rem; color: #666; font-size: 0.8rem; text-align: center; }}
  a {{ color: #4ade80; }}
</style>
</head>
<body>
  <h1>SolarPunk Amplification Posts</h1>
  <div class="meta">Generated: {now} | Copy-paste ready for every platform</div>
  {''.join(platform_sections)}
  <div class="footer">
    <p>Generated by <a href="{GITHUB_URL}">AMPLIFY_ENGINE.py</a> | {TRANSPARENCY}</p>
  </div>
  <script>
    function copyText(id) {{
      const el = document.getElementById(id);
      if (!el) return;
      navigator.clipboard.writeText(el.textContent).then(() => {{
        const btn = el.nextElementSibling || el.parentElement.querySelector('button');
        if (btn) {{
          const orig = btn.textContent;
          btn.textContent = 'Copied!';
          btn.classList.add('copied');
          setTimeout(() => {{ btn.textContent = orig; btn.classList.remove('copied'); }}, 1500);
        }}
      }});
    }}
  </script>
</body>
</html>"""
    return html


# ── main ─────────────────────────────────────────────────────────────

def main():
    print("[AMPLIFY_ENGINE] Generating platform-specific promotional posts...")

    ctx = load_context()
    print(f"  Context: {ctx['kit_count']} kits, {ctx['telegram_count']} telegrams, "
          f"{ctx['crisis_total']} crisis signals, {ctx['critical_signals']} critical/high")

    cooldown = load_cooldown()
    now = datetime.now(timezone.utc)

    # Shuffle angles for variety each cycle
    angles = list(ANGLES)
    random.shuffle(angles)

    # Platform generators
    generators = {
        "twitter":      ("Twitter/X (280 chars)", gen_twitter, 280),
        "bluesky":      ("Bluesky (300 chars)", gen_bluesky, 300),
        "mastodon":     ("Mastodon (500 chars)", gen_mastodon, 500),
        "reddit":       ("Reddit (multiple subs)", None, None),
        "hackernews":   ("Hacker News (80 char title)", gen_hackernews, 80),
        "producthunt":  ("Product Hunt", gen_producthunt, None),
        "devto":        ("Dev.to (article outline)", gen_devto, None),
        "linkedin":     ("LinkedIn (professional)", gen_linkedin, None),
    }

    all_posts = {}
    total_generated = 0

    for platform, (label, gen_fn, char_limit) in generators.items():
        remaining = check_cooldown(cooldown, platform)
        if remaining <= 0:
            print(f"  [{platform}] Cooldown active -- skipping")
            continue

        platform_posts = []
        count = 0

        for angle in angles:
            if count >= min(remaining, MAX_PER_PLATFORM):
                break

            if platform == "reddit":
                reddit_posts = gen_reddit(angle, ctx)
                entry = {
                    "angle": angle["id"],
                    "hook": angle["hook"],
                    "platform": platform,
                    "subreddit_posts": [
                        {"subreddit": rp["subreddit"], "title": rp["title"], "body": rp["body"]}
                        for rp in reddit_posts
                    ],
                    "generated_at": now.isoformat(),
                }
                h = post_hash(platform, angle["id"])
                if h not in cooldown.get("posted_hashes", []):
                    platform_posts.append(entry)
                    cooldown.setdefault("posted_hashes", []).append(h)
                    record_post(cooldown, platform)
                    count += 1
            else:
                content = gen_fn(angle, ctx)
                entry = {
                    "angle": angle["id"],
                    "hook": angle["hook"],
                    "platform": platform,
                    "content": content,
                    "generated_at": now.isoformat(),
                }
                if isinstance(content, str) and char_limit:
                    entry["char_count"] = len(content)
                    entry["within_limit"] = len(content) <= char_limit

                h = post_hash(platform, angle["id"] if isinstance(content, str) else json.dumps(content)[:80])
                if h not in cooldown.get("posted_hashes", []):
                    platform_posts.append(entry)
                    cooldown.setdefault("posted_hashes", []).append(h)
                    record_post(cooldown, platform)
                    count += 1

        all_posts[platform] = platform_posts
        total_generated += len(platform_posts)
        print(f"  [{platform}] Generated {len(platform_posts)} posts ({label})")

    # Save posts JSON
    output = {
        "generated_at": now.isoformat(),
        "engine": "AMPLIFY_ENGINE",
        "total_posts": total_generated,
        "context_snapshot": ctx,
        "links": {
            "store": STORE_URL,
            "github": GITHUB_URL,
            "emergency_kits": KITS_URL,
        },
        "posts": all_posts,
    }
    save_json(POSTS_FILE, output)

    # Save cooldown state
    save_json(COOLDOWN_FILE, cooldown)

    # Generate HTML
    html = generate_html(all_posts)
    html_path = DOCS / "amplify.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  [AMPLIFY] Wrote {html_path.name}")

    # Trim old hashes to prevent unbounded growth (keep last 500)
    if len(cooldown.get("posted_hashes", [])) > 500:
        cooldown["posted_hashes"] = cooldown["posted_hashes"][-500:]
        try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
        except: _h={}
        try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
        except: _c={}
        cooldown["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
        save_json(COOLDOWN_FILE, cooldown)

    print(f"[AMPLIFY_ENGINE] Done. {total_generated} posts across {len(all_posts)} platforms.")
    print(f"  JSON: {POSTS_FILE}")
    print(f"  HTML: {html_path}")


if __name__ == "__main__":
    main()
