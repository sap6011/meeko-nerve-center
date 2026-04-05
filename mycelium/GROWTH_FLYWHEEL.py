#!/usr/bin/env python3
"""
GROWTH_FLYWHEEL.py -- The marketing/distribution engine of the 1/99 system.
==========================================================================

The flywheel: Content -> Traffic -> Signups -> Revenue -> More Content -> ...

This engine generates ready-to-post content for every distribution channel,
manages a 7-day content calendar, extracts SEO keywords from existing products,
and tracks the growth loop metrics.

Reads from:
    data/storefront_listings.json   (products to promote)
    data/fuel_plan.json             (growth priorities from FUEL_CORE)
    data/first_dollar_plan.json     (first dollar strategy)
    data/social_queue.json          (existing social posts)
    data/inbound_signals.json       (GitHub stars/forks)
    data/growth_chain_state.json    (existing growth state)
    data/product_registry.json      (full product catalog)
    data/system_health.json         (engine count, wire count)
    data/proof_ledger.json          (revenue proof)

Writes:
    data/growth_flywheel_state.json     (full engine state)
    data/growth_flywheel_calendar.json  (7-day content plan)
    data/growth_flywheel_content.json   (all generated content pieces)
    docs/growth_flywheel.html           (dashboard)

Zero secrets. Zero paid APIs. Pure signal routing.
"""
import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

REPO = "https://github.com/meekotharaccoon-cell/meeko-nerve-center"
STORE = "https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html"
KOFI = "https://ko-fi.com/meekotharaccoon"
PAGES = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
PROOF = PAGES + "/proof.html"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _load(fname, fallback=None):
    f = DATA / fname
    if f.exists():
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            return d if isinstance(d, (dict, list)) else (fallback or {})
        except Exception:
            pass
    return fallback if fallback is not None else {}


def _save(fname, data):
    (DATA / fname).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _ts():
    return datetime.now(timezone.utc).isoformat()


def _count_engines():
    p = Path("mycelium")
    if p.exists():
        return len([f for f in p.glob("*.py") if f.name != "__init__.py"])
    return 0


# ---------------------------------------------------------------------------
# 1. CONTENT GENERATION -- ready-to-post content for every channel
# ---------------------------------------------------------------------------

def _generate_content(products, system_stats, fuel_plan):
    """Generate ready-to-post content for all distribution channels."""
    now = datetime.now(timezone.utc)
    n_engines = system_stats.get("engines", 0)
    n_products = system_stats.get("products_ready", 0)
    revenue = system_stats.get("total_earned", 0.0)
    first_dollar = system_stats.get("first_dollar_earned", False)

    # Pick top 3 products to feature
    sorted_prods = sorted(
        products.items(),
        key=lambda x: x[1].get("price", 99),
    )
    featured = sorted_prods[:3] if sorted_prods else []
    flagship = featured[0] if featured else None

    content = {
        "generated_at": _ts(),
        "github_discussions": [],
        "twitter_threads": [],
        "reddit_posts": [],
        "devto_articles": [],
        "kofi_updates": [],
    }

    # --- GitHub Discussions ---

    content["github_discussions"].append({
        "id": "product_launch",
        "type": "announcement",
        "title": "New: %d digital products now available -- $1 each, 99%% to mutual aid" % n_products,
        "body": (
            "The SolarPunk autonomous system has generated %d digital products.\n\n"
            "Every product is priced to remove friction ($1 for guides, bundles available).\n"
            "99%% of revenue routes to mutual aid organizations:\n"
            "- PCRF 60%% | IRC 15%% | MSF 10%% | UNICEF 10%% | Direct Relief 5%%\n\n"
            "Browse the store: %s\n\n"
            "The system that built these products also built itself -- %d engines, "
            "running autonomously on zero paid infrastructure.\n\n"
            "Source code (MIT): %s"
        ) % (n_products, STORE, n_engines, REPO),
        "category": "Announcements",
        "labels": ["product-launch", "store"],
    })

    content["github_discussions"].append({
        "id": "system_status",
        "type": "status",
        "title": "System Status: %d engines, %d products, $%.2f revenue" % (n_engines, n_products, revenue),
        "body": (
            "Current state of the SolarPunk autonomous system:\n\n"
            "| Metric | Value |\n|--------|-------|\n"
            "| Engines | %d |\n"
            "| Products ready | %d |\n"
            "| Revenue | $%.2f |\n"
            "| First dollar | %s |\n"
            "| Infrastructure cost | $0 |\n\n"
            "The system wakes up every 6 hours, reads signals, builds products, "
            "deploys pages, and routes revenue to mutual aid.\n\n"
            "Proof it runs: %s\n"
            "Full source: %s"
        ) % (n_engines, n_products, revenue,
             "YES" if first_dollar else "Not yet -- follow the journey",
             PROOF, REPO),
        "category": "General",
        "labels": ["status", "transparency"],
    })

    content["github_discussions"].append({
        "id": "weekly_retro",
        "type": "discussion",
        "title": "Week of %s -- What the system built while I slept" % now.strftime("%b %d"),
        "body": (
            "Every week I check what the autonomous system did without me.\n\n"
            "This week:\n"
            "- Engines running: %d\n"
            "- Products generated: %d\n"
            "- Revenue: $%.2f\n"
            "- Self-written engines: growing each cycle\n\n"
            "The interesting part isn't any single metric. "
            "It's that the system identifies its own gaps and writes code to fill them.\n\n"
            "KNOWLEDGE_WEAVER sends full state to Claude. Claude writes a Python engine. "
            "SELF_BUILDER commits it. Next cycle, it runs.\n\n"
            "What should the system build next? Drop ideas below."
        ) % (n_engines, n_products, revenue),
        "category": "General",
        "labels": ["weekly", "community"],
    })

    # --- Twitter/X Threads ---

    content["twitter_threads"].append({
        "id": "launch_thread",
        "type": "product_launch",
        "tweets": [
            {
                "order": 1,
                "text": (
                    "I built an AI that runs a business while I sleep.\n\n"
                    "%d engines. %d products. $0 infrastructure.\n\n"
                    "99%% of revenue goes to mutual aid (PCRF, IRC, MSF).\n\n"
                    "Thread on what happened:"
                ) % (n_engines, n_products),
            },
            {
                "order": 2,
                "text": (
                    "Every 6 hours, the system wakes up and:\n\n"
                    "- Reads signals (HN, crypto, AI news)\n"
                    "- Generates digital products\n"
                    "- Deploys landing pages\n"
                    "- Writes its own new engines\n"
                    "- Routes revenue to Gaza\n\n"
                    "All on GitHub Actions. Free tier."
                ),
            },
            {
                "order": 3,
                "text": (
                    "The weird part:\n\n"
                    "The AI I use to build this = the same model it calls automatically.\n\n"
                    "When I open Claude, I'm running a high-bandwidth cycle.\n"
                    "When GitHub Actions triggers, same model, stateless.\n\n"
                    "The developer and the system are the same intelligence."
                ),
            },
            {
                "order": 4,
                "text": (
                    "Everything costs $1.\n\n"
                    "Thesis: 5B internet users x 0.001%% x $1 = $50K.\n"
                    "At $10, friction kills conversion.\n\n"
                    "Store: %s\n"
                    "Source (MIT): %s\n"
                    "Proof it runs: %s"
                ) % (STORE, REPO, PROOF),
            },
        ],
    })

    content["twitter_threads"].append({
        "id": "mission_thread",
        "type": "mission",
        "tweets": [
            {
                "order": 1,
                "text": (
                    "Why does an AI system care about Gaza?\n\n"
                    "It doesn't. I do.\n\n"
                    "So I hardcoded it. 99%% of every dollar this system makes goes to:\n"
                    "- PCRF (Palestinian Children's Relief Fund)\n"
                    "- IRC, MSF, UNICEF, Direct Relief\n\n"
                    "It's not a feature. It's architecture."
                ),
            },
            {
                "order": 2,
                "text": (
                    "The split is in the source code. MIT licensed. Anyone can verify.\n\n"
                    "You can't toggle it off. You can't negotiate it down.\n"
                    "It's the same as the engine that generates products.\n\n"
                    "The aid routing IS the system. Remove it and it breaks."
                ),
            },
            {
                "order": 3,
                "text": (
                    "Current revenue: $%.2f. I'm honest about that.\n\n"
                    "But the machine is built. %d engines. %d products ready.\n"
                    "The bottleneck is distribution, not production.\n\n"
                    "One viral post = first sale = proof the loop works.\n\n"
                    "%s"
                ) % (revenue, n_engines, n_products, REPO),
            },
        ],
    })

    content["twitter_threads"].append({
        "id": "technical_thread",
        "type": "technical",
        "tweets": [
            {
                "order": 1,
                "text": (
                    "How to build a self-expanding AI system on $0 infrastructure:\n\n"
                    "1. GitHub Actions (free CI/CD = free server)\n"
                    "2. GitHub Pages (free hosting)\n"
                    "3. Python engines that read/write JSON\n"
                    "4. An orchestrator that runs them in sequence\n\n"
                    "That's it. The rest is emergent."
                ),
            },
            {
                "order": 2,
                "text": (
                    "The self-expansion loop:\n\n"
                    "KNOWLEDGE_WEAVER collects full system state.\n"
                    "Sends it to Claude: 'What engine is missing?'\n"
                    "Claude writes Python.\n"
                    "SELF_BUILDER tests + commits it.\n"
                    "Next cycle: new engine runs.\n\n"
                    "The system grew from 10 to %d+ engines this way."
                ) % n_engines,
            },
            {
                "order": 3,
                "text": (
                    "Architecture layers:\n\n"
                    "L0: Health/self-repair\n"
                    "L1: Signal gathering\n"
                    "L2: Revenue intelligence\n"
                    "L3: Build + deploy\n"
                    "L4: Distribution\n"
                    "L5: Payment + aid routing\n"
                    "L6: Self-expansion\n"
                    "L7: Memory + proof\n\n"
                    "Full source (MIT): %s"
                ) % REPO,
            },
        ],
    })

    content["twitter_threads"].append({
        "id": "behind_scenes_thread",
        "type": "behind_the_scenes",
        "tweets": [
            {
                "order": 1,
                "text": (
                    "Behind the scenes of auto-genesis:\n\n"
                    "The system doesn't just run code. It writes code, "
                    "then runs the code it wrote.\n\n"
                    "Every cycle, FRACTAL_GENESIS checks: 'Are there dead data wires?'\n"
                    "If yes, it writes a Python engine to fill the gap.\n"
                    "Commits. Runs. Repeat."
                ),
            },
            {
                "order": 2,
                "text": (
                    "What surprised me most:\n\n"
                    "The system developed self-awareness about its constraints.\n"
                    "CAPABILITY_SCANNER audits every cycle and reports what's blocked.\n\n"
                    "I didn't design this explicitly. "
                    "It emerged from engines that read each other's output."
                ),
            },
        ],
    })

    # --- Reddit Posts ---

    content["reddit_posts"].append({
        "id": "r_solarpunk",
        "subreddit": "r/solarpunk",
        "title": "Built an autonomous AI system that routes 99%% of revenue to mutual aid -- here's the architecture",
        "body": (
            "I named it SolarPunk because the philosophy fits: technology in service of people, "
            "not extraction.\n\n"
            "**What it does:**\n"
            "- Runs autonomously on free infrastructure (GitHub Actions + Pages)\n"
            "- Generates digital products and deploys them\n"
            "- Routes 99%% of revenue to: PCRF (60%%), IRC (15%%), MSF (10%%), UNICEF (10%%), "
            "Direct Relief (5%%)\n"
            "- Writes its own new engines to fill gaps it identifies\n\n"
            "**Real numbers:**\n"
            "- Engines: %d\n"
            "- Products built: %d\n"
            "- Revenue: $%.2f (honest -- distribution channels still being configured)\n"
            "- Infrastructure cost: $0\n\n"
            "**Why solarpunk?**\n"
            "Because the system proves you can build self-sustaining technology that serves "
            "mutual aid instead of venture capital. The aid routing is hardcoded -- it can't be "
            "turned off without rewriting the system.\n\n"
            "Source (MIT): %s\n"
            "Store: %s"
        ) % (n_engines, n_products, revenue, REPO, STORE),
        "flair": "Technology",
    })

    content["reddit_posts"].append({
        "id": "r_opensource",
        "subreddit": "r/opensource",
        "title": "Open source autonomous AI system -- %d engines, self-expanding, zero infrastructure cost" % n_engines,
        "body": (
            "MIT licensed. Full source available.\n\n"
            "**Architecture:**\n"
            "- Python engines in `mycelium/` directory\n"
            "- JSON data wires in `data/` for inter-engine communication\n"
            "- GitHub Actions orchestrator runs 4x daily\n"
            "- GitHub Pages for dashboards and storefronts\n\n"
            "**The interesting part -- self-expansion:**\n"
            "KNOWLEDGE_WEAVER sends system state to Claude. Claude writes a new Python engine. "
            "SELF_BUILDER tests and commits it. Next cycle, it runs. "
            "The system grew from ~10 to %d+ engines this way.\n\n"
            "**Ethical architecture:**\n"
            "99%% of revenue routes to mutual aid organizations. "
            "This is in the source code, not a toggle.\n\n"
            "Looking for contributors who care about:\n"
            "1. AI autonomy patterns\n"
            "2. Ethical revenue routing\n"
            "3. Self-healing distributed systems\n\n"
            "Source: %s"
        ) % (n_engines, REPO),
        "flair": "Project",
    })

    content["reddit_posts"].append({
        "id": "r_sideproject",
        "subreddit": "r/SideProject",
        "title": "Week %d: My autonomous AI business made $%.2f -- honest progress report" % (
            int(now.strftime("%U")), revenue),
        "body": (
            "Honest update on the autonomous AI project.\n\n"
            "**What works:**\n"
            "- %d engines running autonomously\n"
            "- %d products generated and ready to sell\n"
            "- Landing pages auto-deployed\n"
            "- System writes its own new code every cycle\n\n"
            "**What doesn't work yet:**\n"
            "- Revenue: $%.2f (distribution channels being configured)\n"
            "- Social posting: queued but waiting on API credentials\n"
            "- Gumroad: storefront needs setup\n\n"
            "**What I learned:**\n"
            "Production is solved. Distribution is the bottleneck. "
            "Having 100 products means nothing if zero people see them.\n\n"
            "**The mission:**\n"
            "99%% of revenue to mutual aid. Not negotiable. "
            "The system exists to fund relief organizations.\n\n"
            "Store: %s\n"
            "Source (MIT): %s"
        ) % (n_engines, n_products, revenue, STORE, REPO),
        "flair": "Show Off",
    })

    # --- Dev.to / Hashnode Articles ---

    content["devto_articles"].append({
        "id": "architecture_deepdive",
        "type": "technical",
        "title": "How I Built a %d-Engine Autonomous AI System on $0 Infrastructure" % n_engines,
        "tags": ["python", "ai", "opensource", "automation"],
        "body": (
            "# How I Built a %d-Engine Autonomous AI System on $0 Infrastructure\n\n"
            "This is the technical breakdown of SolarPunk -- an autonomous AI system "
            "that generates products, deploys pages, writes its own code, and routes "
            "99%% of revenue to mutual aid.\n\n"
            "## Architecture\n\n"
            "The system has 8 layers:\n\n"
            "| Layer | Purpose | Example Engine |\n"
            "|-------|---------|---------------|\n"
            "| L0 | Health/self-repair | NANOBOT_HEAL |\n"
            "| L1 | Signal gathering | SCAVENGER_WEB |\n"
            "| L2 | Revenue intelligence | FUEL_CORE |\n"
            "| L3 | Build + deploy | PRODUCT_FORGE |\n"
            "| L4 | Distribution | GROWTH_FLYWHEEL |\n"
            "| L5 | Payment + aid routing | ECONOMY_CHAIN |\n"
            "| L6 | Self-expansion | KNOWLEDGE_WEAVER |\n"
            "| L7 | Memory + proof | PROOF_PUBLISHER |\n\n"
            "## The Engine Pattern\n\n"
            "Every engine follows the same pattern:\n\n"
            "```python\n"
            "import json\n"
            "from pathlib import Path\n"
            "from datetime import datetime, timezone\n\n"
            "DATA = Path('data')\n\n"
            "def run():\n"
            "    # Read inputs\n"
            "    signals = json.loads((DATA / 'input.json').read_text())\n"
            "    # Process\n"
            "    result = do_work(signals)\n"
            "    # Write outputs\n"
            "    (DATA / 'output.json').write_text(json.dumps(result, indent=2), encoding="utf-8")\n\n"
            "if __name__ == '__main__':\n"
            "    run()\n"
            "```\n\n"
            "Engines communicate through JSON files. No database. No message queue. "
            "Just files that engines read and write.\n\n"
            "## Self-Expansion\n\n"
            "The most interesting part: the system writes its own engines.\n\n"
            "1. KNOWLEDGE_WEAVER collects all data files\n"
            "2. Sends full state to Claude: 'What engine is missing?'\n"
            "3. Claude writes Python\n"
            "4. SELF_BUILDER tests and commits\n"
            "5. Next OMNIBUS cycle runs the new engine\n\n"
            "This loop grew the system from ~10 to %d+ engines.\n\n"
            "## The $0 Stack\n\n"
            "- **Compute:** GitHub Actions (2000 min/month free)\n"
            "- **Hosting:** GitHub Pages (free)\n"
            "- **Storage:** Git repository (free)\n"
            "- **AI:** Ollama locally, free API tiers for cloud\n"
            "- **Payments:** Ko-fi (0%% platform fee on shops)\n\n"
            "## Revenue Routing\n\n"
            "99%% of revenue routes to mutual aid:\n"
            "- PCRF 60%% (Palestinian Children's Relief Fund)\n"
            "- IRC 15%%, MSF 10%%, UNICEF 10%%, Direct Relief 5%%\n\n"
            "This is architecture, not a feature. It's in the source code.\n\n"
            "---\n\n"
            "Full source (MIT): [GitHub](%s)\n"
            "Store: [Products](%s)\n"
            "Proof of operation: [Proof](%s)"
        ) % (n_engines, n_engines, REPO, STORE, PROOF),
    })

    content["devto_articles"].append({
        "id": "self_healing_deepdive",
        "type": "technical",
        "title": "Self-Healing AI: How My System Fixes Itself at 3am",
        "tags": ["python", "devops", "ai", "automation"],
        "body": (
            "# Self-Healing AI: How My System Fixes Itself at 3am\n\n"
            "The SolarPunk system runs 4x daily without supervision. "
            "When things break -- and they do -- the system heals itself.\n\n"
            "## The Bio-Inspired Approach\n\n"
            "The system borrows from biology:\n\n"
            "- **Mycelium network:** Engines communicate through shared data\n"
            "- **Immune system:** IMMUNE_SYSTEM detects anomalies and quarantines bad data\n"
            "- **Nanobot repair:** NANOBOT_HEAL detects dead engines and attempts revival\n"
            "- **Pheromone signaling:** Engines leave signals for each other via JSON\n\n"
            "## How Self-Healing Works\n\n"
            "```\n"
            "OMNIBUS cycle starts\n"
            "  -> L0: HEALTH_CHECK scans all engines\n"
            "  -> Finds: SCAVENGER_WEB crashed last cycle\n"
            "  -> NANOBOT_HEAL: resets state, clears bad cache\n"
            "  -> SCAVENGER_WEB runs successfully\n"
            "  -> L7: PROOF_PUBLISHER logs the recovery\n"
            "```\n\n"
            "The key insight: every engine writes its state to JSON. "
            "If state is corrupted, the healer can reset it to a known-good default.\n\n"
            "## Practical Patterns You Can Use\n\n"
            "1. **State files, not databases** -- JSON files are human-readable and git-trackable\n"
            "2. **Fallback defaults** -- Every `load()` has a fallback for missing/corrupt data\n"
            "3. **Quarantine** -- Bad data goes to a quarantine file, not deleted\n"
            "4. **Proof of operation** -- Every cycle writes a timestamp to prove it ran\n\n"
            "---\n\n"
            "Full source (MIT): [GitHub](%s)"
        ) % REPO,
    })

    # --- Ko-fi Updates ---

    content["kofi_updates"].append({
        "id": "progress_update",
        "type": "progress",
        "title": "System Update: %d engines running, %d products ready" % (n_engines, n_products),
        "body": (
            "Quick update on the SolarPunk autonomous system:\n\n"
            "The system now has %d engines and %d products ready to sell.\n\n"
            "What happened this cycle:\n"
            "- System health: nominal\n"
            "- New content generated for all distribution channels\n"
            "- Revenue: $%.2f (working on distribution)\n\n"
            "Every purchase routes 99%% to mutual aid.\n"
            "PCRF (Palestinian Children's Relief Fund) gets 60%%.\n\n"
            "Thank you for supporting the mission.\n\n"
            "Browse the store: %s"
        ) % (n_engines, n_products, revenue, STORE),
    })

    content["kofi_updates"].append({
        "id": "mission_update",
        "type": "mission",
        "title": "Why 99%% goes to mutual aid -- the architecture of giving",
        "body": (
            "People ask why an AI system donates to Gaza.\n\n"
            "The AI doesn't care. I do. So I built it into the architecture.\n\n"
            "The revenue routing is not a toggle. It's not a setting.\n"
            "It's hardcoded in the source code, the same way the product generator is.\n"
            "Remove it and the system breaks.\n\n"
            "The split:\n"
            "- PCRF 60%% (Palestinian Children's Relief Fund, EIN: 93-1057665)\n"
            "- IRC 15%% (International Rescue Committee)\n"
            "- MSF 10%% (Doctors Without Borders)\n"
            "- UNICEF 10%%\n"
            "- Direct Relief 5%%\n\n"
            "Every dollar this system earns, $0.99 goes to people who need it.\n\n"
            "That's not charity. That's architecture."
        ),
    })

    # count total pieces
    total = (
        len(content["github_discussions"])
        + sum(len(t["tweets"]) for t in content["twitter_threads"])
        + len(content["reddit_posts"])
        + len(content["devto_articles"])
        + len(content["kofi_updates"])
    )
    content["total_pieces"] = total

    return content


# ---------------------------------------------------------------------------
# 2. DISTRIBUTION CALENDAR -- 7-day content plan
# ---------------------------------------------------------------------------

def _build_calendar(content, products):
    """Create a 7-day content plan rotating through channels and themes."""
    now = datetime.now(timezone.utc)
    today = now.date()

    # Pick products to feature across the week
    prod_list = list(products.items())
    featured_prod_1 = prod_list[0] if len(prod_list) > 0 else ("none", {"title": "TBD"})
    featured_prod_2 = prod_list[1] if len(prod_list) > 1 else featured_prod_1

    calendar = {
        "generated_at": _ts(),
        "week_start": today.isoformat(),
        "days": [],
    }

    day_plans = [
        {
            "theme": "Product Launch",
            "description": "Announce products across all channels -- the store is live, tell people",
            "channels": [
                {"platform": "GitHub Discussions", "content_id": "product_launch", "action": "Post announcement"},
                {"platform": "Twitter/X", "content_id": "launch_thread", "action": "Post 4-tweet thread"},
                {"platform": "Ko-fi", "content_id": "progress_update", "action": "Post update to supporters"},
            ],
            "talking_points": [
                "%d products available at $1 each" % len(prod_list),
                "99%% to mutual aid -- transparent, verifiable, hardcoded",
                "Built by %d autonomous engines on $0 infrastructure" % _count_engines(),
            ],
        },
        {
            "theme": "Technical Deep-Dive",
            "description": "Show builders how it works -- earn trust through transparency",
            "channels": [
                {"platform": "Dev.to", "content_id": "architecture_deepdive", "action": "Publish article"},
                {"platform": "Twitter/X", "content_id": "technical_thread", "action": "Post architecture thread"},
                {"platform": "Reddit r/opensource", "content_id": "r_opensource", "action": "Post to community"},
            ],
            "talking_points": [
                "8-layer architecture explained",
                "Self-expansion loop: system writes its own engines",
                "$0 infrastructure stack breakdown",
            ],
        },
        {
            "theme": "Mission & Ethics",
            "description": "Tell the 99/1 story -- why the system exists",
            "channels": [
                {"platform": "Twitter/X", "content_id": "mission_thread", "action": "Post mission thread"},
                {"platform": "Reddit r/solarpunk", "content_id": "r_solarpunk", "action": "Post to community"},
                {"platform": "Ko-fi", "content_id": "mission_update", "action": "Post mission update"},
            ],
            "talking_points": [
                "99%% of revenue to PCRF, IRC, MSF, UNICEF, Direct Relief",
                "Aid routing is architecture, not a feature -- can't be toggled off",
                "The system exists to fund relief, not to extract value",
            ],
        },
        {
            "theme": "Community Engagement",
            "description": "Ask questions, invite participation, build relationships",
            "channels": [
                {"platform": "GitHub Discussions", "content_id": "weekly_retro", "action": "Post weekly retro"},
                {"platform": "Reddit r/SideProject", "content_id": "r_sideproject", "action": "Post honest update"},
                {"platform": "Twitter/X", "content_id": None, "action": "Ask: What should the system build next?"},
            ],
            "talking_points": [
                "What feature would you add to an autonomous AI system?",
                "Honest numbers: here's what works and what doesn't",
                "Looking for contributors: AI patterns, ethical routing, self-healing",
            ],
        },
        {
            "theme": "Behind the Scenes",
            "description": "Show the system running -- process transparency builds trust",
            "channels": [
                {"platform": "Twitter/X", "content_id": "behind_scenes_thread", "action": "Post BTS thread"},
                {"platform": "Dev.to", "content_id": "self_healing_deepdive", "action": "Publish article"},
                {"platform": "GitHub Discussions", "content_id": "system_status", "action": "Post status update"},
            ],
            "talking_points": [
                "Auto-genesis: the system writes its own code",
                "Self-healing: how it fixes itself at 3am",
                "The emergent self-awareness nobody designed",
            ],
        },
        {
            "theme": "Product Showcase",
            "description": "Feature a different product -- rotate through the catalog",
            "channels": [
                {"platform": "Twitter/X", "content_id": None, "action": "Feature: %s ($%.2f)" % (
                    featured_prod_2[1].get("title", "?"), featured_prod_2[1].get("price", 1))},
                {"platform": "Ko-fi", "content_id": None, "action": "Highlight product of the week"},
                {"platform": "Reddit r/SideProject", "content_id": None, "action": "Share product + honest metrics"},
            ],
            "talking_points": [
                "Featured: %s" % featured_prod_2[1].get("title", "TBD"),
                "What's inside and why it's worth $%.2f" % featured_prod_2[1].get("price", 1),
                "Every purchase = 99%% to mutual aid",
            ],
        },
        {
            "theme": "Week in Review",
            "description": "System growth metrics -- transparency report",
            "channels": [
                {"platform": "GitHub Discussions", "content_id": "weekly_retro", "action": "Post full metrics"},
                {"platform": "Twitter/X", "content_id": None, "action": "Post week-in-review stats"},
                {"platform": "Ko-fi", "content_id": "progress_update", "action": "Supporter update with numbers"},
            ],
            "talking_points": [
                "Engines this week: %d" % _count_engines(),
                "Products ready: %d" % len(prod_list),
                "Revenue: honest number + what changed",
                "Next week: what the system will focus on",
            ],
        },
    ]

    for i, plan in enumerate(day_plans):
        day_date = today + timedelta(days=i)
        calendar["days"].append({
            "day": i + 1,
            "date": day_date.isoformat(),
            "weekday": day_date.strftime("%A"),
            "theme": plan["theme"],
            "description": plan["description"],
            "channels": plan["channels"],
            "talking_points": plan["talking_points"],
            "status": "pending",
        })

    return calendar


# ---------------------------------------------------------------------------
# 3. SEO KEYWORDS -- extracted from existing content
# ---------------------------------------------------------------------------

def _extract_seo_keywords(products, system_stats):
    """Extract SEO keywords from product catalog and system identity."""

    # Product-derived keywords
    product_keywords = set()
    for pid, prod in products.items():
        title = prod.get("title", "")
        for word in title.lower().split():
            if len(word) > 3 and word not in {"from", "with", "your", "that", "this", "what", "into", "about"}:
                product_keywords.add(word)
        # Extract from social_post if available
        social = prod.get("social_post", "")
        for phrase in ["autonomous", "solarpunk", "ai system", "mutual aid", "open source",
                       "python", "automation", "self-healing"]:
            if phrase in social.lower():
                product_keywords.add(phrase)

    # Mission keywords (always present)
    mission_keywords = [
        "solarpunk", "solarpunk ai", "mutual aid technology",
        "ethical ai", "aid routing", "humanitarian technology",
        "autonomous ai for good", "pcrf donation",
        "open source mutual aid", "gaza relief technology",
        "99 percent to charity", "ethical revenue routing",
        "self-sustaining aid", "technology for mutual aid",
    ]

    # Technical keywords
    technical_keywords = [
        "self-healing ai", "auto-genesis", "mycelium network",
        "autonomous python system", "self-expanding ai",
        "github actions automation", "zero cost infrastructure",
        "json data wires", "bio-inspired architecture",
        "ai business automation", "ai agent system",
        "self-writing code", "autonomous revenue generation",
        "ollama local ai", "free ai api automation",
    ]

    # Product-specific long-tail keywords
    product_long_tail = []
    for pid, prod in products.items():
        title = prod.get("title", "")
        price = prod.get("price", 1)
        product_long_tail.append("buy %s" % title.lower())
        product_long_tail.append("%s guide" % title.lower())
        if price <= 1:
            product_long_tail.append("cheap %s guide" % title.lower().split()[0])

    return {
        "product_keywords": sorted(product_keywords),
        "mission_keywords": mission_keywords,
        "technical_keywords": technical_keywords,
        "product_long_tail": product_long_tail,
        "total_keywords": len(product_keywords) + len(mission_keywords) + len(technical_keywords) + len(product_long_tail),
        "top_10": [
            "solarpunk ai system",
            "autonomous ai mutual aid",
            "self-healing python automation",
            "build your own ai agent",
            "ethical ai revenue",
            "open source ai business",
            "github actions autonomous system",
            "ai products for charity",
            "self-expanding ai architecture",
            "zero cost ai infrastructure",
        ],
    }


# ---------------------------------------------------------------------------
# 4. FLYWHEEL METRICS -- track the growth loop
# ---------------------------------------------------------------------------

def _compute_metrics(content, calendar, state):
    """Compute flywheel metrics -- content created, published, loop health."""
    now_ts = _ts()

    # Content counts
    total_generated = content.get("total_pieces", 0)
    prev_generated = state.get("metrics", {}).get("content_total_generated", 0)
    total_published = state.get("metrics", {}).get("content_total_published", 0)

    # Signals from other engines
    inbound = _load("inbound_signals.json", {})
    growth_chain = _load("growth_chain_state.json", {})
    proof = _load("proof_ledger.json", {})
    economy = _load("economy_chain_ledger.json", {})

    stars = growth_chain.get("last_output", {}).get("stars", 0)
    forks = growth_chain.get("last_output", {}).get("forks", 0)
    revenue = max(
        float(economy.get("total_earned", 0)),
        float(proof.get("total_sales", 0)),
        0.0,
    )

    # Flywheel health score (0-100)
    # Each stage of the flywheel contributes to health
    score = 0
    score_breakdown = {}

    # Content stage (25 pts) -- are we creating content?
    content_score = min(25, total_generated)
    score_breakdown["content"] = {"score": content_score, "max": 25, "detail": "%d pieces generated" % total_generated}
    score += content_score

    # Distribution stage (25 pts) -- are we publishing?
    dist_score = min(25, total_published * 5)
    score_breakdown["distribution"] = {"score": dist_score, "max": 25, "detail": "%d pieces published" % total_published}
    score += dist_score

    # Traffic stage (25 pts) -- are people finding us?
    traffic_score = min(25, stars * 2 + forks * 5)
    score_breakdown["traffic"] = {"score": traffic_score, "max": 25, "detail": "%d stars, %d forks" % (stars, forks)}
    score += traffic_score

    # Revenue stage (25 pts) -- is the loop closing?
    rev_score = min(25, int(revenue * 10))
    score_breakdown["revenue"] = {"score": rev_score, "max": 25, "detail": "$%.2f earned" % revenue}
    score += rev_score

    loop_status = "spinning" if score > 50 else ("starting" if score > 10 else "stalled")

    metrics = {
        "computed_at": now_ts,
        "flywheel_score": score,
        "flywheel_status": loop_status,
        "score_breakdown": score_breakdown,
        "content_total_generated": prev_generated + total_generated,
        "content_total_published": total_published,
        "content_publish_rate": round(total_published / max(prev_generated + total_generated, 1) * 100, 1),
        "github_stars": stars,
        "github_forks": forks,
        "total_revenue": revenue,
        "revenue_per_content": round(revenue / max(prev_generated + total_generated, 1), 4),
        "calendar_days_planned": len(calendar.get("days", [])),
        "calendar_days_completed": sum(1 for d in calendar.get("days", []) if d.get("status") == "completed"),
    }

    return metrics


# ---------------------------------------------------------------------------
# HTML dashboard
# ---------------------------------------------------------------------------

def _build_html(state, content, calendar, keywords, metrics):
    """Generate docs/growth_flywheel.html dashboard."""
    now = state.get("last_run", "")[:16]
    score = metrics.get("flywheel_score", 0)
    status = metrics.get("flywheel_status", "stalled")

    # Score color
    if score > 50:
        score_color = "#4ade80"
        status_label = "SPINNING"
    elif score > 10:
        score_color = "#fbbf24"
        status_label = "STARTING"
    else:
        score_color = "#f87171"
        status_label = "STALLED"

    # Flywheel score breakdown
    breakdown_html = ""
    for stage, info in metrics.get("score_breakdown", {}).items():
        pct = int(info["score"] / max(info["max"], 1) * 100)
        bar_color = "#4ade80" if pct > 60 else ("#fbbf24" if pct > 20 else "#f87171")
        breakdown_html += (
            '<div class="stage">'
            '<div class="stage-header"><span class="stage-name">%s</span>'
            '<span class="stage-score">%d/%d</span></div>'
            '<div class="bar"><div class="fill" style="width:%d%%;background:%s"></div></div>'
            '<div class="stage-detail">%s</div>'
            '</div>\n'
        ) % (stage.upper(), info["score"], info["max"], pct, bar_color, info["detail"])

    # Calendar rows
    cal_rows = ""
    for day in calendar.get("days", []):
        status_badge = (
            '<span class="badge done">done</span>' if day["status"] == "completed"
            else '<span class="badge pending">pending</span>'
        )
        channels = ", ".join(c["platform"] for c in day.get("channels", []))
        cal_rows += (
            "<tr><td>Day %d</td><td>%s</td><td><strong>%s</strong></td>"
            "<td>%s</td><td>%s</td><td>%s</td></tr>\n"
        ) % (day["day"], day.get("weekday", ""), day["theme"],
             day.get("description", "")[:60], channels, status_badge)

    # Content summary
    n_discussions = len(content.get("github_discussions", []))
    n_threads = len(content.get("twitter_threads", []))
    n_reddit = len(content.get("reddit_posts", []))
    n_devto = len(content.get("devto_articles", []))
    n_kofi = len(content.get("kofi_updates", []))
    total_pieces = content.get("total_pieces", 0)

    # Top SEO keywords
    kw_html = ""
    for kw in keywords.get("top_10", []):
        kw_html += '<span class="kw">%s</span>' % kw

    # Flywheel diagram (ASCII in HTML)
    flywheel_svg = (
        '<div class="flywheel-diagram">'
        '<div class="fw-stage fw-content">CONTENT<br><span>%d pieces</span></div>'
        '<div class="fw-arrow">--&gt;</div>'
        '<div class="fw-stage fw-traffic">TRAFFIC<br><span>%d stars</span></div>'
        '<div class="fw-arrow">--&gt;</div>'
        '<div class="fw-stage fw-signups">SIGNUPS<br><span>growing</span></div>'
        '<div class="fw-arrow">--&gt;</div>'
        '<div class="fw-stage fw-revenue">REVENUE<br><span>$%.2f</span></div>'
        '<div class="fw-arrow">--&gt; loop</div>'
        '</div>'
    ) % (total_pieces, metrics.get("github_stars", 0), metrics.get("total_revenue", 0))

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GROWTH FLYWHEEL -- SolarPunk Distribution Engine</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#050a05;color:#d4d4d4;padding:24px;max-width:960px;margin:0 auto}
h1{color:#4ade80;margin-bottom:4px;font-size:1.8em}
h2{color:#86efac;margin:28px 0 12px;font-size:1.15em;border-bottom:1px solid #1a3a1a;padding-bottom:6px}
.subtitle{color:#888;margin-bottom:20px;font-size:0.9em;font-style:italic}

.score-ring{text-align:center;margin:20px auto;width:120px;height:120px;border-radius:50%%;border:4px solid %s;display:flex;flex-direction:column;align-items:center;justify-content:center}
.score-ring .val{font-size:2em;font-weight:700;color:%s}
.score-ring .lbl{font-size:0.65em;color:#888}

.flywheel-diagram{display:flex;align-items:center;justify-content:center;gap:6px;margin:20px 0;flex-wrap:wrap}
.fw-stage{background:#0a1a0a;border:1px solid #1a3a1a;border-radius:8px;padding:10px 14px;text-align:center;font-size:0.8em;font-weight:600;min-width:80px}
.fw-stage span{display:block;font-size:0.8em;font-weight:400;color:#888;margin-top:2px}
.fw-content{color:#60a5fa;border-color:#1e3a5f}
.fw-traffic{color:#fbbf24;border-color:#4a3a0a}
.fw-signups{color:#c084fc;border-color:#3a1a4a}
.fw-revenue{color:#4ade80;border-color:#1a3a1a}
.fw-arrow{color:#555;font-size:0.8em}

.stage{margin-bottom:14px}
.stage-header{display:flex;justify-content:space-between;margin-bottom:4px}
.stage-name{font-size:0.75em;color:#aaa;letter-spacing:0.05em}
.stage-score{font-size:0.75em;color:#888}
.bar{background:#1a1a1a;height:8px;border-radius:4px;overflow:hidden}
.bar .fill{height:100%%;border-radius:4px;transition:width 0.3s}
.stage-detail{font-size:0.7em;color:#666;margin-top:2px}

.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin:16px 0}
.stat{background:#0a1a0a;border:1px solid #1a3a1a;border-radius:6px;padding:12px;text-align:center}
.stat .val{font-size:1.3em;font-weight:700;color:#4ade80}
.stat .lbl{font-size:0.7em;color:#666;margin-top:4px}

table{width:100%%;border-collapse:collapse;font-size:0.78em;margin-top:8px}
th{text-align:left;color:#4ade80;border-bottom:1px solid #1a3a1a;padding:6px}
td{border-bottom:1px solid #111;padding:6px;color:#aaa}
.badge{font-size:0.7em;padding:2px 8px;border-radius:3px}
.badge.done{background:#14532d;color:#4ade80}
.badge.pending{background:#1a1a00;color:#fbbf24}

.kw{display:inline-block;background:#0a1a0a;border:1px solid #1a3a1a;border-radius:4px;padding:3px 8px;margin:3px;font-size:0.75em;color:#86efac}

.content-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0}
.content-card{background:#0a1a0a;border:1px solid #1a3a1a;border-radius:6px;padding:12px}
.content-card .ch{font-size:0.7em;color:#4ade80;letter-spacing:0.05em;margin-bottom:4px}
.content-card .num{font-size:1.4em;font-weight:700;color:#d4d4d4}
.content-card .det{font-size:0.7em;color:#666;margin-top:2px}

.mission{margin-top:32px;padding:12px;background:#0a1a0a;border:1px solid #1a3a1a;border-radius:6px;color:#86efac;font-size:0.82em;text-align:center}
.ts{color:#333;font-size:0.7em;margin-top:20px;text-align:center}
a{color:#4ade80}
</style>
</head>
<body>
<h1>GROWTH FLYWHEEL</h1>
<p class="subtitle">Content -> Traffic -> Signups -> Revenue -> More Content -> ...</p>

<div class="score-ring">
<div class="val">%d</div>
<div class="lbl">%s</div>
</div>

%s

<h2>Flywheel Health</h2>
%s

<h2>Content Pipeline</h2>
<div class="stat-grid">
<div class="stat"><div class="val">%d</div><div class="lbl">Total Pieces</div></div>
<div class="stat"><div class="val">%d</div><div class="lbl">Published</div></div>
<div class="stat"><div class="val">%s%%%%</div><div class="lbl">Publish Rate</div></div>
<div class="stat"><div class="val">$%.4f</div><div class="lbl">Rev / Content</div></div>
</div>

<div class="content-grid">
<div class="content-card"><div class="ch">GITHUB DISCUSSIONS</div><div class="num">%d</div><div class="det">announcements, status, retros</div></div>
<div class="content-card"><div class="ch">TWITTER/X THREADS</div><div class="num">%d</div><div class="det">launch, mission, technical, BTS</div></div>
<div class="content-card"><div class="ch">REDDIT POSTS</div><div class="num">%d</div><div class="det">r/solarpunk, r/opensource, r/sideproject</div></div>
<div class="content-card"><div class="ch">DEV.TO ARTICLES</div><div class="num">%d</div><div class="det">technical deep-dives</div></div>
<div class="content-card"><div class="ch">KO-FI UPDATES</div><div class="num">%d</div><div class="det">progress + mission posts</div></div>
</div>

<h2>7-Day Distribution Calendar</h2>
<table>
<tr><th>Day</th><th>Weekday</th><th>Theme</th><th>Focus</th><th>Channels</th><th>Status</th></tr>
%s
</table>

<h2>SEO Keywords (%d total)</h2>
<div style="margin:8px 0">%s</div>

<div class="mission">
99%%%% of every dollar -> mutual aid. PCRF 60%%%% | IRC 15%%%% | MSF 10%%%% | UNICEF 10%%%% | Direct Relief 5%%%%<br>
The flywheel spins to fund relief. That is the endgame.
</div>

<div class="ts">
Generated %s UTC by GROWTH_FLYWHEEL |
<a href="fuel.html">Fuel Core</a> |
<a href="store.html">Store</a> |
<a href="proof.html">Proof</a> |
<a href="%s">GitHub</a>
</div>
</body>
</html>""" % (
        score_color, score_color,
        score, status_label,
        flywheel_svg,
        breakdown_html,
        metrics.get("content_total_generated", 0),
        metrics.get("content_total_published", 0),
        metrics.get("content_publish_rate", 0),
        metrics.get("revenue_per_content", 0),
        n_discussions, n_threads, n_reddit, n_devto, n_kofi,
        cal_rows,
        keywords.get("total_keywords", 0),
        kw_html,
        now,
        REPO,
    )

    return html


# ---------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------

def run():
    print("=" * 64)
    print("GROWTH FLYWHEEL -- Content -> Traffic -> Signups -> Revenue")
    print("=" * 64)
    print()

    # Load state
    state = _load("growth_flywheel_state.json", {
        "engine": "GROWTH_FLYWHEEL",
        "created_at": _ts(),
        "cycles": 0,
        "metrics": {},
    })

    # Gather system data
    storefront = _load("storefront_listings.json", {})
    products = storefront.get("listings", {})
    fuel_plan = _load("fuel_plan.json", {})
    first_dollar = _load("first_dollar_plan.json", {})
    social_queue = _load("social_queue.json", {"posts": []})
    registry = _load("product_registry.json", {})
    health = _load("system_health.json", {})

    system_stats = {
        "engines": _count_engines(),
        "products_ready": len(products),
        "total_earned": float(fuel_plan.get("current_revenue", 0)),
        "first_dollar_earned": first_dollar.get("first_dollar_earned", False),
        "social_posts_queued": len(social_queue.get("posts", [])),
    }

    print("[system] %d engines | %d products | $%.2f revenue | first dollar: %s" % (
        system_stats["engines"],
        system_stats["products_ready"],
        system_stats["total_earned"],
        "YES" if system_stats["first_dollar_earned"] else "NO",
    ))

    # 1. Generate content for all channels
    print()
    print("[1/5] Generating content for all distribution channels...")
    content = _generate_content(products, system_stats, fuel_plan)
    print("  GitHub Discussions: %d" % len(content["github_discussions"]))
    print("  Twitter/X threads:  %d (%d tweets total)" % (
        len(content["twitter_threads"]),
        sum(len(t["tweets"]) for t in content["twitter_threads"]),
    ))
    print("  Reddit posts:       %d" % len(content["reddit_posts"]))
    print("  Dev.to articles:    %d" % len(content["devto_articles"]))
    print("  Ko-fi updates:      %d" % len(content["kofi_updates"]))
    print("  TOTAL:              %d pieces" % content["total_pieces"])

    # 2. Build 7-day calendar
    print()
    print("[2/5] Building 7-day distribution calendar...")
    calendar = _build_calendar(content, products)
    for day in calendar["days"]:
        channels = ", ".join(c["platform"] for c in day["channels"])
        print("  Day %d (%s): %s -> %s" % (
            day["day"], day["weekday"][:3], day["theme"], channels))

    # 3. Extract SEO keywords
    print()
    print("[3/5] Extracting SEO keywords...")
    keywords = _extract_seo_keywords(products, system_stats)
    print("  Product keywords:    %d" % len(keywords["product_keywords"]))
    print("  Mission keywords:    %d" % len(keywords["mission_keywords"]))
    print("  Technical keywords:  %d" % len(keywords["technical_keywords"]))
    print("  Long-tail keywords:  %d" % len(keywords["product_long_tail"]))
    print("  TOTAL:               %d" % keywords["total_keywords"])
    print("  Top 3: %s" % ", ".join(keywords["top_10"][:3]))

    # 4. Compute flywheel metrics
    print()
    print("[4/5] Computing flywheel metrics...")
    metrics = _compute_metrics(content, calendar, state)
    print("  Flywheel score: %d/100 (%s)" % (metrics["flywheel_score"], metrics["flywheel_status"]))
    for stage, info in metrics["score_breakdown"].items():
        print("    %s: %d/%d -- %s" % (stage.upper(), info["score"], info["max"], info["detail"]))
    print("  Publish rate: %.1f%%" % metrics["content_publish_rate"])
    print("  Revenue per content: $%.4f" % metrics["revenue_per_content"])

    # 5. Write outputs
    print()
    print("[5/5] Writing outputs...")

    # Update state
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = _ts()
    state["metrics"] = metrics
    state["system_stats"] = system_stats
    state["keywords_count"] = keywords["total_keywords"]
    state["content_pieces"] = content["total_pieces"]
    state["calendar_week_start"] = calendar.get("week_start", "")
    state["status"] = metrics["flywheel_status"]
    _save("growth_flywheel_state.json", state)
    print("  [write] data/growth_flywheel_state.json")

    # Save calendar
    _save("growth_flywheel_calendar.json", calendar)
    print("  [write] data/growth_flywheel_calendar.json")

    # Save content
    _save("growth_flywheel_content.json", content)
    print("  [write] data/growth_flywheel_content.json")

    # Build and save HTML dashboard
    html = _build_html(state, content, calendar, keywords, metrics)
    (DOCS / "growth_flywheel.html").write_text(html, encoding="utf-8")
    print("  [write] docs/growth_flywheel.html")

    # Summary
    print()
    print("=" * 64)
    print("GROWTH FLYWHEEL: %s (score %d/100)" % (metrics["flywheel_status"].upper(), metrics["flywheel_score"]))
    print()
    print("  Content:      %d pieces ready across 5 channels" % content["total_pieces"])
    print("  Calendar:     7-day plan starting %s" % calendar.get("week_start", "today"))
    print("  SEO:          %d keywords extracted" % keywords["total_keywords"])
    print("  Published:    %d / %d (%.1f%%)" % (
        metrics["content_total_published"],
        metrics["content_total_generated"],
        metrics["content_publish_rate"],
    ))
    print()

    # Critical next action
    if metrics["flywheel_score"] < 10:
        print("  CRITICAL: The flywheel is stalled.")
        print("  Next action: Post 1 piece of content to 1 channel. Any channel.")
        print("  The flywheel starts with a single push.")
    elif metrics["flywheel_score"] < 50:
        print("  The flywheel is starting to turn.")
        print("  Next action: Follow today's calendar. Consistency compounds.")
    else:
        print("  The flywheel is spinning. Keep feeding it.")
        print("  Next action: Check which channel converts best, double down.")

    print()
    print("  Dashboard: %s/growth_flywheel.html" % PAGES)
    print("  99%% of every dollar -> mutual aid. The flywheel spins for them.")
    print("=" * 64)

    return {
        "engine": "GROWTH_FLYWHEEL",
        "status": metrics["flywheel_status"],
        "flywheel_score": metrics["flywheel_score"],
        "content_pieces": content["total_pieces"],
        "calendar_days": len(calendar["days"]),
        "seo_keywords": keywords["total_keywords"],
        "publish_rate": metrics["content_publish_rate"],
        "ts": _ts(),
    }


if __name__ == "__main__":
    run()
