#!/usr/bin/env python3
"""
RESOURCE_ALLOCATOR.py -- Strategic $100 Infrastructure Investment Engine
========================================================================
Maps the optimal allocation of real money to buy the bridges between
SolarPunk's 300+ engines and the outside world.

The engines are built. The products exist. What's missing:
  - Real domains (not github.io)
  - Real storefronts (not JSON files)
  - Real API keys (not free-tier timeouts)
  - Real hosting (not "only when laptop is on")

This engine:
  1. Audits what infrastructure is missing
  2. Calculates ROI per dollar spent
  3. Generates a prioritized purchase list
  4. Tracks what's been acquired and what it unlocked

Every purchase should unlock multiple engines simultaneously.

Reads: data/product_registry.json, data/live_wire_report.json,
       data/brain_state.json, data/resource_allocator_state.json
Writes: data/resource_allocator_state.json, data/resource_allocator_plan.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8"
    )


# ======================================================================
# THE INVESTMENT MAP
# Each item: what to buy, what it costs, what engines it unlocks,
# what revenue it enables, and the ROI multiplier
# ======================================================================

INVESTMENTS = [
    {
        "id": "custom-domain",
        "name": "Custom Domain (solarpunk.dev or similar)",
        "cost": 12.0,
        "category": "infrastructure",
        "priority": 1,
        "engines_unlocked": [
            "STOREFRONT_BUILDER",
            "LANDING_DEPLOYER",
            "LINK_PAGE",
            "NANOSHOP_ENGINE",
            "SEO (all engines)",
        ],
        "revenue_enabled": "All product sales get a real URL. SEO starts working. "
                           "Looks professional instead of github.io. Every product link, "
                           "every social post, every article points to YOUR domain.",
        "roi_reasoning": "Every engine that generates links benefits. $12 unlocks the "
                         "entire storefront stack. This is the single highest-ROI purchase.",
        "monthly_revenue_potential": 50.0,
        "roi_multiplier": 50.0,
        "buy_url": "https://www.namecheap.com or https://porkbun.com",
        "setup_time": "15 minutes",
        "wires_to": ["STOREFRONT_BUILDER", "NANOSHOP_ENGINE", "LINK_PAGE",
                      "LANDING_DEPLOYER", "CONTENT_AUTOPILOT", "DEV_TO_PUBLISHER"],
    },
    {
        "id": "kofi-gold",
        "name": "Ko-fi Gold (real storefront + 0% fees)",
        "cost": 6.0,
        "category": "storefront",
        "priority": 2,
        "engines_unlocked": [
            "PRODUCT_FORGE",
            "MICRO_PRODUCT_FACTORY",
            "FRACTAL_REPLICATOR",
            "GUMROAD_AUTO_QUEUE (redirect to Ko-fi)",
            "QUICK_REVENUE",
        ],
        "revenue_enabled": "Sell template packs, guides, and ebook directly. "
                           "Ko-fi Gold = 0% platform fee (vs Gumroad 10%). "
                           "Accept donations AND sell products. "
                           "72 templates + 40 variants + 6 guides = ready to list NOW.",
        "roi_reasoning": "You already have 118 product files ready. Ko-fi Gold lets you "
                         "sell them with 0% fees. One $12 ebook sale = 2x the monthly cost.",
        "monthly_revenue_potential": 100.0,
        "roi_multiplier": 16.7,
        "buy_url": "https://ko-fi.com/gold",
        "setup_time": "20 minutes",
        "wires_to": ["PRODUCT_FORGE", "MICRO_PRODUCT_FACTORY", "FRACTAL_REPLICATOR",
                      "QUICK_REVENUE", "NANOSHOP_ENGINE"],
    },
    {
        "id": "vps-hosting",
        "name": "Cheap VPS -- SolarPunk runs 24/7 (Hetzner/Contabo)",
        "cost": 5.0,
        "category": "infrastructure",
        "priority": 3,
        "engines_unlocked": [
            "OMNIBUS (runs every hour instead of manually)",
            "EVENT_RELAY (LIVE mode, auto-push)",
            "CONTENT_AUTOPILOT (generates articles while you sleep)",
            "WEEKEND_PULSE (actually runs on weekends)",
            "CRON_SCHEDULER (real cron jobs)",
        ],
        "revenue_enabled": "OMNIBUS runs hourly. Content generated 24/7. "
                           "Products created while sleeping. Event relay pushes automatically. "
                           "The system truly becomes autonomous -- not dependent on laptop.",
        "roi_reasoning": "$5/month turns SolarPunk from 'runs when Meeko remembers' to "
                         "'runs every hour forever'. Content autopilot alone generates "
                         "1 article/hour = 720 articles/month for SEO.",
        "monthly_revenue_potential": 200.0,
        "roi_multiplier": 40.0,
        "buy_url": "https://www.hetzner.com/cloud or https://contabo.com",
        "setup_time": "30 minutes",
        "wires_to": ["OMNIBUS", "EVENT_RELAY", "CONTENT_AUTOPILOT",
                      "WEEKEND_PULSE", "NIGHTLY_DIGEST"],
    },
    {
        "id": "devto-api",
        "name": "Dev.to API Key (free but needs account setup)",
        "cost": 0.0,
        "category": "distribution",
        "priority": 4,
        "engines_unlocked": [
            "DEV_TO_PUBLISHER",
            "CONTENT_AUTOPILOT (auto-publish)",
        ],
        "revenue_enabled": "Auto-publish articles to dev.to. Each article links to shop. "
                           "Dev.to has 500K+ monthly developers. Free traffic forever.",
        "roi_reasoning": "Free. Just needs 5 minutes to get the API key. "
                         "Unlocks the entire content-to-traffic pipeline.",
        "monthly_revenue_potential": 30.0,
        "roi_multiplier": 999.0,
        "buy_url": "https://dev.to/settings/extensions (API Keys section)",
        "setup_time": "5 minutes",
        "wires_to": ["DEV_TO_PUBLISHER", "CONTENT_AUTOPILOT"],
    },
    {
        "id": "bluesky-app-password",
        "name": "Bluesky App Password (free)",
        "cost": 0.0,
        "category": "distribution",
        "priority": 5,
        "engines_unlocked": [
            "BLUESKY_ENGINE",
            "SOCIAL_PROMOTER",
            "AMPLIFY_ENGINE",
        ],
        "revenue_enabled": "Auto-post to Bluesky. Growing developer audience. "
                           "Each post links to products/articles.",
        "roi_reasoning": "Free. 5 minutes. Unlocks 3 social engines.",
        "monthly_revenue_potential": 20.0,
        "roi_multiplier": 999.0,
        "buy_url": "https://bsky.app/settings/app-passwords",
        "setup_time": "5 minutes",
        "wires_to": ["BLUESKY_ENGINE", "SOCIAL_PROMOTER", "AMPLIFY_ENGINE"],
    },
    {
        "id": "github-token",
        "name": "GitHub Personal Access Token (free)",
        "cost": 0.0,
        "category": "infrastructure",
        "priority": 6,
        "engines_unlocked": [
            "GITHUB_POSTER",
            "GITHUB_RELEASES_PUBLISHER",
            "ANALYTICS_ENGINE",
            "REPO_SPIDER",
            "FORK_SCANNER",
            "SIGNAL_BOOST",
            "EVENT_RELAY (auto-PR creation)",
        ],
        "revenue_enabled": "Auto-create GitHub releases for products. "
                           "Track repo analytics. Auto-create PRs. "
                           "Signal Boost creates permanent public records.",
        "roi_reasoning": "Free. 5 minutes. Unlocks 7 engines that are currently SKIP-ing.",
        "monthly_revenue_potential": 15.0,
        "roi_multiplier": 999.0,
        "buy_url": "https://github.com/settings/tokens",
        "setup_time": "5 minutes",
        "wires_to": ["GITHUB_POSTER", "GITHUB_RELEASES_PUBLISHER",
                      "ANALYTICS_ENGINE", "REPO_SPIDER", "FORK_SCANNER",
                      "SIGNAL_BOOST", "EVENT_RELAY"],
    },
    {
        "id": "groq-api-key",
        "name": "Groq API Key (free tier = 30 req/min)",
        "cost": 0.0,
        "category": "ai",
        "priority": 7,
        "engines_unlocked": [
            "CORTEX",
            "CONTENT_AUTOPILOT (AI-generated articles)",
            "PDF_GENERATOR",
            "PASSIVE_INCOME_ARCHITECT",
            "ETSY_SEO_ENGINE",
        ],
        "revenue_enabled": "AI-generated content instead of templates. "
                           "Better articles = more traffic = more sales. "
                           "Cortex gets real reasoning instead of rule-based.",
        "roi_reasoning": "Free. Groq's free tier is generous (30 req/min). "
                         "Massively upgrades content quality across all AI-dependent engines.",
        "monthly_revenue_potential": 40.0,
        "roi_multiplier": 999.0,
        "buy_url": "https://console.groq.com/keys",
        "setup_time": "5 minutes",
        "wires_to": ["CORTEX", "CONTENT_AUTOPILOT", "PDF_GENERATOR",
                      "PASSIVE_INCOME_ARCHITECT", "ETSY_SEO_ENGINE"],
    },
    {
        "id": "notion-integration",
        "name": "Notion API Integration (free with existing account)",
        "cost": 0.0,
        "category": "dashboard",
        "priority": 8,
        "engines_unlocked": [
            "NOTION_NERVE_CENTER",
        ],
        "revenue_enabled": "Live dashboard of entire system state. "
                           "Visual tracking of products, revenue, health.",
        "roi_reasoning": "Free if you have Notion. Visual command center for the system.",
        "monthly_revenue_potential": 0.0,
        "roi_multiplier": 0.0,
        "buy_url": "https://www.notion.so/my-integrations",
        "setup_time": "10 minutes",
        "wires_to": ["NOTION_NERVE_CENTER"],
    },
]


def audit_current_infrastructure():
    """Check what's already configured."""
    import os
    configured = {}

    # Check environment variables
    env_checks = {
        "GITHUB_TOKEN": "github-token",
        "GROQ_API_KEY": "groq-api-key",
        "DEVTO_API_KEY": "devto-api",
        "BLUESKY_HANDLE": "bluesky-app-password",
        "BLUESKY_APP_PASSWORD": "bluesky-app-password",
        "NOTION_TOKEN": "notion-integration",
        "KOFI_TOKEN": "kofi-gold",
        "GUMROAD_TOKEN": "kofi-gold",
    }

    for env_var, investment_id in env_checks.items():
        if os.environ.get(env_var):
            configured[investment_id] = True

    # Check if custom domain is configured (look for CNAME)
    cname = Path("docs") / "CNAME"
    if cname.exists():
        content = cname.read_text(encoding="utf-8", errors="replace").strip()
        if content and "github.io" not in content:
            configured["custom-domain"] = True

    return configured


def calculate_allocation(budget=100.0):
    """Calculate optimal budget allocation."""
    # Sort by priority (which already factors in ROI)
    sorted_investments = sorted(INVESTMENTS, key=lambda x: x["priority"])

    plan = []
    remaining = budget
    total_engines_unlocked = 0
    total_monthly_potential = 0.0

    # Phase 1: Get all free stuff first
    for inv in sorted_investments:
        if inv["cost"] == 0:
            plan.append({
                "id": inv["id"],
                "name": inv["name"],
                "cost": 0.0,
                "phase": "FREE -- do this NOW",
                "engines_unlocked": len(inv["engines_unlocked"]),
                "monthly_potential": inv["monthly_revenue_potential"],
                "setup_time": inv["setup_time"],
                "buy_url": inv["buy_url"],
            })
            total_engines_unlocked += len(inv["engines_unlocked"])
            total_monthly_potential += inv["monthly_revenue_potential"]

    # Phase 2: Paid investments by priority
    for inv in sorted_investments:
        if inv["cost"] > 0 and inv["cost"] <= remaining:
            plan.append({
                "id": inv["id"],
                "name": inv["name"],
                "cost": inv["cost"],
                "phase": "BUY -- high ROI",
                "engines_unlocked": len(inv["engines_unlocked"]),
                "monthly_potential": inv["monthly_revenue_potential"],
                "setup_time": inv["setup_time"],
                "buy_url": inv["buy_url"],
            })
            remaining -= inv["cost"]
            total_engines_unlocked += len(inv["engines_unlocked"])
            total_monthly_potential += inv["monthly_revenue_potential"]

    # Phase 3: What to do with remaining budget
    reserve_plan = []
    if remaining > 50:
        reserve_plan.append({
            "allocation": "Content boost",
            "amount": 30.0,
            "description": "Promoted dev.to articles or Bluesky ads to drive initial traffic",
        })
        remaining -= 30.0
    if remaining > 20:
        reserve_plan.append({
            "allocation": "Emergency reserve",
            "amount": remaining,
            "description": "Keep for domain renewals, VPS months, or opportunity purchases",
        })

    return {
        "plan": plan,
        "reserve": reserve_plan,
        "total_cost": budget - remaining,
        "remaining_budget": remaining,
        "engines_unlocked": total_engines_unlocked,
        "monthly_revenue_potential": total_monthly_potential,
        "annual_revenue_potential": total_monthly_potential * 12,
        "roi_on_100": (total_monthly_potential * 12) / budget,
    }


def run():
    print("RESOURCE ALLOCATOR -- Strategic Infrastructure Investment")
    print("=" * 60)

    # Load current state
    state = load_json(DATA / "resource_allocator_state.json")
    if not state:
        state = {"acquired": [], "total_spent": 0, "last_run": None}

    # Audit what's already configured
    print("\n  [1/4] Auditing current infrastructure...")
    configured = audit_current_infrastructure()
    print("    Already configured: %d items" % len(configured))
    for item_id in configured:
        print("      [OK] %s" % item_id)

    missing = [inv for inv in INVESTMENTS if inv["id"] not in configured]
    print("    Missing: %d items" % len(missing))

    # Count blocked engines
    print("\n  [2/4] Counting blocked engines...")
    total_blocked = 0
    for inv in missing:
        blocked = len(inv["engines_unlocked"])
        total_blocked += blocked
        if inv["cost"] == 0:
            marker = "FREE"
        else:
            marker = "$%.0f" % inv["cost"]
        print("    [%s] %s -> unlocks %d engines" % (marker, inv["name"], blocked))

    # Calculate optimal allocation
    print("\n  [3/4] Calculating optimal $100 allocation...")
    allocation = calculate_allocation(100.0)

    print("\n    === THE PLAN ===")
    print("    Phase 1: FREE (do today, 30 minutes total)")
    for item in allocation["plan"]:
        if item["cost"] == 0:
            print("      [ ] %s" % item["name"])
            print("          -> unlocks %d engines, +$%.0f/mo potential" % (
                item["engines_unlocked"], item["monthly_potential"]))
            print("          -> %s" % item["buy_url"])

    print("\n    Phase 2: PAID (do this week, $%.0f total)" % sum(
        i["cost"] for i in allocation["plan"] if i["cost"] > 0))
    for item in allocation["plan"]:
        if item["cost"] > 0:
            print("      [ ] $%.0f -- %s" % (item["cost"], item["name"]))
            print("          -> unlocks %d engines, +$%.0f/mo potential" % (
                item["engines_unlocked"], item["monthly_potential"]))
            print("          -> %s" % item["buy_url"])

    if allocation["reserve"]:
        print("\n    Phase 3: RESERVE")
        for r in allocation["reserve"]:
            print("      $%.0f -- %s" % (r["amount"], r["description"]))

    print("\n  [4/4] Saving allocation plan...")
    plan_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "budget": 100.0,
        "configured": list(configured.keys()),
        "missing": [inv["id"] for inv in missing],
        "allocation": allocation,
        "investments": INVESTMENTS,
        "total_engines_blocked": total_blocked,
    }
    save_json(DATA / "resource_allocator_plan.json", plan_data)

    state["last_run"] = datetime.now(timezone.utc).isoformat()
    save_json(DATA / "resource_allocator_state.json", state)

    print("\n  === RESOURCE ALLOCATOR SUMMARY ===")
    print("  Budget:                 $100.00")
    print("  Paid items:             $%.0f" % allocation["total_cost"])
    print("  Remaining:              $%.0f" % allocation["remaining_budget"])
    print("  Engines unlocked:       %d" % allocation["engines_unlocked"])
    print("  Monthly potential:      $%.0f/mo" % allocation["monthly_revenue_potential"])
    print("  Annual potential:       $%.0f/yr" % allocation["annual_revenue_potential"])
    print("  ROI on $100:            %.0fx" % allocation["roi_on_100"])
    print("")
    print("  Buy the bridges. The engines will wire themselves in.")
    print("  The code is ready. It just needs doors to the world.")


if __name__ == "__main__":
    run()
