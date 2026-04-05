# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
FUEL_CORE.py -- The 1/99 Revenue Growth Engine.

The INVERSE of SolarPunk's 99/1 aid system.

    The 99/1 system GIVES. The 1/99 system GROWS.
    Both serve the same mission.

While the 99/1 system routes 99% of revenue to mutual aid and 1% to
infrastructure, the 1/99 system is the REVENUE GENERATOR:
    1%  --> immediate aid (direct to PCRF while building)
    99% --> growing the machine that will eventually feed the 99/1 system

Split (hardcoded, non-negotiable):
    1%  --> immediate_aid      (PCRF -- Palestinian Children's Relief Fund)
   35%  --> product_development (new products, better products)
   25%  --> storefront_infra    (Ko-fi, Gumroad, domains)
   20%  --> marketing_growth    (SEO, social, outreach)
   10%  --> api_keys_tools      (Anthropic API, hosting, services)
    9%  --> legal_runway        (DBA, trademark, LLC)

The 1% is the reminder. Every cent of growth fuel remembers WHY.

Zero secrets needed. Zero paid APIs. Pure signal routing.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# The 1/99 routing table -- every dollar of GROWTH fuel splits this way
# ---------------------------------------------------------------------------
FUEL_ROUTES = {
    "immediate_aid": {
        "pct": 0.01,
        "label": "Immediate Aid (PCRF)",
        "purpose": "1% reminder -- every growth dollar remembers why we build",
        "recipient": "Palestinian Children's Relief Fund (EIN: 93-1057665)",
    },
    "product_development": {
        "pct": 0.35,
        "label": "Product Development",
        "purpose": "New products, better products, more value per dollar",
    },
    "storefront_infra": {
        "pct": 0.25,
        "label": "Storefront Infrastructure",
        "purpose": "Ko-fi, Gumroad, domains, payment rails -- the bridges buyers cross",
    },
    "marketing_growth": {
        "pct": 0.20,
        "label": "Marketing & Growth",
        "purpose": "SEO, social media, outreach, distribution -- eyeballs to buy buttons",
    },
    "api_keys_tools": {
        "pct": 0.10,
        "label": "API Keys & Tools",
        "purpose": "Anthropic API, hosting, services -- the engine's fuel",
    },
    "legal_runway": {
        "pct": 0.09,
        "label": "Legal Runway",
        "purpose": "DBA, trademark, LLC -- the armor that protects the mission",
    },
}

# ---------------------------------------------------------------------------
# Infrastructure buy list -- ranked by ROI for $0 -> $1 -> $100 journey
# ---------------------------------------------------------------------------
INFRA_PRIORITIES = [
    {
        "id": "kofi_product_listing",
        "name": "List first product on Ko-fi shop",
        "cost": 0.00,
        "route": "storefront_infra",
        "roi_rank": 1,
        "time_to_revenue": "1 hour",
        "impact": "UNLOCKS first sale -- Ko-fi is live, shop is live, product is ready",
        "blocking": True,
        "status_check": lambda prods: any(p.get("kofi_url") for p in prods.values()),
    },
    {
        "id": "fix_buy_links",
        "name": "Fix broken buy links (Gumroad typos in art.html)",
        "cost": 0.00,
        "route": "storefront_infra",
        "roi_rank": 2,
        "time_to_revenue": "30 minutes",
        "impact": "7 buy buttons currently 404 -- fixing = 7 new sales channels",
        "blocking": True,
        "status_check": lambda _: False,  # checked via revenue_audit
    },
    {
        "id": "gumroad_account",
        "name": "Create/activate Gumroad storefront",
        "cost": 0.00,
        "route": "storefront_infra",
        "roi_rank": 3,
        "time_to_revenue": "2 hours",
        "impact": "Second payment rail -- diversifies revenue, captures different buyers",
        "blocking": False,
        "status_check": lambda _: False,  # checked via revenue_audit
    },
    {
        "id": "social_first_post",
        "name": "Post product link on Bluesky/Mastodon",
        "cost": 0.00,
        "route": "marketing_growth",
        "roi_rank": 4,
        "time_to_revenue": "1 day",
        "impact": "First eyeballs that are not bots -- real humans see real products",
        "blocking": False,
        "status_check": lambda _: False,
    },
    {
        "id": "seo_meta_tags",
        "name": "Add SEO meta tags to store/product pages",
        "cost": 0.00,
        "route": "marketing_growth",
        "roi_rank": 5,
        "time_to_revenue": "2 weeks",
        "impact": "Organic search discovery -- passive traffic that compounds",
        "blocking": False,
        "status_check": lambda _: False,
    },
    {
        "id": "custom_domain",
        "name": "Buy a custom domain (solarpunk.shop or similar)",
        "cost": 12.00,
        "route": "storefront_infra",
        "roi_rank": 6,
        "time_to_revenue": "1 week",
        "impact": "Trust signal -- real domain = real business in buyer minds",
        "blocking": False,
        "status_check": lambda _: False,
    },
    {
        "id": "anthropic_api_key",
        "name": "Anthropic API credits for smarter engines",
        "cost": 20.00,
        "route": "api_keys_tools",
        "roi_rank": 7,
        "time_to_revenue": "1 month",
        "impact": "Better product generation, smarter outreach, faster iteration",
        "blocking": False,
        "status_check": lambda _: False,
    },
    {
        "id": "dba_filing",
        "name": "File DBA (Doing Business As) for SolarPunk",
        "cost": 50.00,
        "route": "legal_runway",
        "roi_rank": 8,
        "time_to_revenue": "3 months",
        "impact": "Legal identity -- required for business bank account and trademark",
        "blocking": False,
        "status_check": lambda _: False,
    },
]

# ---------------------------------------------------------------------------
# Product development pipeline -- what to build next
# ---------------------------------------------------------------------------
PRODUCT_IDEAS = [
    {
        "id": "free_lead_magnet",
        "name": "Free art lead magnet (download 1 print free, upsell pack)",
        "effort": "low",
        "time_to_build": "1 hour",
        "expected_revenue": 0.00,
        "purpose": "Capture emails, build trust, convert to paid later",
        "priority": 1,
    },
    {
        "id": "bundle_sampler",
        "name": "$3 SolarPunk Sampler (best bits from all products)",
        "effort": "low",
        "time_to_build": "2 hours",
        "expected_revenue": 3.00,
        "purpose": "Mid-price entry point -- $1 too cheap for some, $12 too steep for first buy",
        "priority": 2,
    },
    {
        "id": "video_walkthrough",
        "name": "Screen recording: building a SolarPunk engine live",
        "effort": "medium",
        "time_to_build": "4 hours",
        "expected_revenue": 5.00,
        "purpose": "Video content sells differently than text -- new audience segment",
        "priority": 3,
    },
    {
        "id": "discord_community",
        "name": "Paid Discord community ($5/month)",
        "effort": "medium",
        "time_to_build": "1 day",
        "expected_revenue": 5.00,
        "purpose": "Recurring revenue -- one subscriber at $5/month = $60/year forever",
        "priority": 4,
    },
    {
        "id": "consulting_page",
        "name": "AI automation consulting landing page",
        "effort": "low",
        "time_to_build": "3 hours",
        "expected_revenue": 100.00,
        "purpose": "High-ticket -- one consulting gig funds months of infrastructure",
        "priority": 5,
    },
]


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


# ---------------------------------------------------------------------------
# revenue signal aggregation
# ---------------------------------------------------------------------------

def _gather_revenue_signals():
    """Pull every revenue signal from every source. Return unified dict."""
    economy   = _load("economy_chain_ledger.json", {})
    kofi      = _load("kofi_tracker_state.json", {})
    audit     = _load("revenue_audit.json", {})
    first_dol = _load("first_dollar_plan.json", {})
    registry  = _load("product_registry.json", {})
    gumroad   = _load("gumroad_listings.json", {})
    proof     = _load("proof_ledger.json", {})
    quick_rev = _load("quick_revenue.json", {})
    rev_flow  = _load("revenue_flow.json", {})

    products = registry.get("products", {})

    total_earned = max(
        float(economy.get("total_earned", 0)),
        float(kofi.get("total_verified", 0)),
        float(proof.get("total_sales", 0)),
        float(quick_rev.get("total_revenue", 0)),
        float(rev_flow.get("total_unified", 0)),
        0.0,
    )

    return {
        "total_earned": total_earned,
        "economy_cycles": economy.get("cycles", 0),
        "kofi_alive": audit.get("kofi_alive", False),
        "gumroad_alive": audit.get("gumroad_alive", False),
        "products_count": len(products),
        "products_ready": sum(1 for p in products.values() if p.get("content_ready")),
        "products_listed_kofi": sum(1 for p in products.values() if p.get("kofi_url")),
        "products_listed_gumroad": sum(1 for p in products.values() if p.get("gumroad_url")),
        "first_dollar_earned": first_dol.get("first_dollar_earned", False),
        "revenue_blockers": audit.get("revenue_blockers", []),
        "buy_link_issues": audit.get("buy_link_issues", 0),
        "loop_closed": economy.get("loop_closed", False),
        "products": products,
        "gumroad_products": gumroad.get("products", []),
        "recommended_fixes": audit.get("recommended_fixes", []),
    }


# ---------------------------------------------------------------------------
# fuel routing -- how growth dollars split
# ---------------------------------------------------------------------------

def _route_fuel(total_earned, state):
    """Route accumulated earnings through 1/99 split. Return route totals."""
    routes = state.get("fuel_routes", {})
    for key in FUEL_ROUTES:
        if key not in routes:
            routes[key] = {"total": 0.0, "events": []}

    previously_routed = state.get("total_fuel_routed", 0.0)
    new_fuel = round(total_earned - previously_routed, 6)

    if new_fuel > 0:
        for key, route in FUEL_ROUTES.items():
            amount = round(new_fuel * route["pct"], 6)
            routes[key]["total"] = round(routes[key]["total"] + amount, 6)
            routes[key]["events"].append({"ts": _ts(), "amount": amount})
            routes[key]["events"] = routes[key]["events"][-50:]

    return routes, new_fuel


# ---------------------------------------------------------------------------
# blocker analysis
# ---------------------------------------------------------------------------

def _analyze_blockers(signals):
    """Identify what is actively blocking revenue RIGHT NOW."""
    blockers = []

    # Blocker 1: No products listed on any live platform
    if signals["products_listed_kofi"] == 0 and signals["products_listed_gumroad"] == 0:
        blockers.append({
            "id": "no_live_listings",
            "severity": "critical",
            "message": "%d products ready but ZERO listed on any platform" % signals["products_ready"],
            "fix": "List top-scored product on Ko-fi shop RIGHT NOW",
            "time_to_fix": "1 hour",
        })

    # Blocker 2: Gumroad is dead
    if not signals["gumroad_alive"]:
        blockers.append({
            "id": "gumroad_404",
            "severity": "high",
            "message": "Gumroad storefront returns 404 -- all Gumroad buy buttons are dead",
            "fix": "Create Gumroad account OR redirect all buy buttons to Ko-fi",
            "time_to_fix": "30 minutes",
        })

    # Blocker 3: Buy link typos
    if signals["buy_link_issues"] > 0:
        blockers.append({
            "id": "broken_buy_links",
            "severity": "high",
            "message": "%d buy links broken (typos/dead URLs)" % signals["buy_link_issues"],
            "fix": "Fix URLs in art.html and store pages",
            "time_to_fix": "20 minutes",
        })

    # Blocker 4: No social posts
    blockers.append({
        "id": "zero_distribution",
        "severity": "medium",
        "message": "Products exist but no evidence of social distribution",
        "fix": "Post product links on Bluesky, Mastodon, or any social channel",
        "time_to_fix": "10 minutes",
    })

    # Blocker 5: First dollar not earned
    if not signals["first_dollar_earned"]:
        blockers.append({
            "id": "no_revenue",
            "severity": "critical",
            "message": "Total revenue: $0.00 -- the growth loop has not started",
            "fix": "Fix blockers above, then the first sale unlocks everything",
            "time_to_fix": "depends on above",
        })

    return blockers


# ---------------------------------------------------------------------------
# fuel plan generation
# ---------------------------------------------------------------------------

def _build_fuel_plan(signals, blockers):
    """Generate the actionable FUEL PLAN -- what to do next, in order."""
    products = signals.get("products", {})

    # Rank infrastructure buys by ROI
    infra_actions = []
    for item in INFRA_PRIORITIES:
        # Skip lambda status_check -- serialize cleanly
        infra_actions.append({
            "id": item["id"],
            "name": item["name"],
            "cost": item["cost"],
            "route": item["route"],
            "roi_rank": item["roi_rank"],
            "time_to_revenue": item["time_to_revenue"],
            "impact": item["impact"],
            "blocking": item["blocking"],
        })

    # Product development recommendations
    product_actions = []
    for idea in PRODUCT_IDEAS:
        product_actions.append({
            "id": idea["id"],
            "name": idea["name"],
            "effort": idea["effort"],
            "time_to_build": idea["time_to_build"],
            "expected_revenue": idea["expected_revenue"],
            "purpose": idea["purpose"],
            "priority": idea["priority"],
        })

    # Build the "next 3 actions" -- the critical path
    critical_path = []

    # Action 1: always fix the most severe blocker first
    critical_blockers = [b for b in blockers if b["severity"] == "critical"]
    if critical_blockers:
        b = critical_blockers[0]
        critical_path.append({
            "priority": 1,
            "action": b["fix"],
            "reason": b["message"],
            "time": b["time_to_fix"],
            "category": "blocker_fix",
        })

    # Action 2: list a product if none listed
    if signals["products_listed_kofi"] == 0:
        critical_path.append({
            "priority": 2,
            "action": "List 'Build Your Own SolarPunk' ($1) on Ko-fi shop",
            "reason": "Highest scored product, lowest price, Ko-fi is live -- path of least resistance",
            "time": "1 hour",
            "category": "storefront_infra",
        })

    # Action 3: share it
    critical_path.append({
        "priority": len(critical_path) + 1,
        "action": "Post the Ko-fi shop link on at least 1 social platform",
        "reason": "Zero eyeballs = zero sales, no matter how good the product",
        "time": "10 minutes",
        "category": "marketing_growth",
    })

    # Revenue projections (conservative)
    projections = {
        "if_1_sale_per_week": {
            "monthly": 4.00,
            "yearly": 48.00,
            "aid_yearly_1pct": 0.48,
            "note": "1 sale/week at $1 average -- extremely conservative",
        },
        "if_1_sale_per_day": {
            "monthly": 30.00,
            "yearly": 365.00,
            "aid_yearly_1pct": 3.65,
            "note": "1 sale/day at $1 -- achievable with basic social presence",
        },
        "if_5_sales_per_day": {
            "monthly": 150.00,
            "yearly": 1825.00,
            "aid_yearly_1pct": 18.25,
            "note": "5 sales/day mixed pricing -- requires SEO + social + email",
        },
        "when_99_1_activates": {
            "note": "When revenue is self-sustaining, the 1/99 flips to 99/1 -- "
                    "99%% goes to aid. That is the endgame.",
        },
    }

    plan = {
        "generated_at": _ts(),
        "engine": "FUEL_CORE",
        "mantra": "The 99/1 system GIVES. The 1/99 system GROWS. Both serve the same mission.",
        "current_revenue": signals["total_earned"],
        "first_dollar_earned": signals["first_dollar_earned"],
        "products_ready": signals["products_ready"],
        "products_listed": signals["products_listed_kofi"] + signals["products_listed_gumroad"],
        "platforms": {
            "kofi": {"alive": signals["kofi_alive"], "products_listed": signals["products_listed_kofi"]},
            "gumroad": {"alive": signals["gumroad_alive"], "products_listed": signals["products_listed_gumroad"]},
        },
        "critical_path": critical_path,
        "blockers": blockers,
        "infrastructure_queue": infra_actions,
        "product_pipeline": product_actions,
        "fuel_split": {k: {"pct": int(v["pct"] * 100), "purpose": v["purpose"]} for k, v in FUEL_ROUTES.items()},
        "projections": projections,
    }

    return plan


# ---------------------------------------------------------------------------
# HTML dashboard
# ---------------------------------------------------------------------------

def _build_html(plan, state):
    """Generate docs/fuel.html -- the FUEL CORE dashboard."""
    now = plan.get("generated_at", "")[:16]
    revenue = plan.get("current_revenue", 0)
    earned = plan.get("first_dollar_earned", False)

    # Critical path steps
    cp_html = ""
    for step in plan.get("critical_path", []):
        cp_html += (
            '<div class="step">'
            '<span class="num">%d</span>'
            '<div class="body"><strong>%s</strong>'
            '<p>%s</p>'
            '<span class="time">%s</span>'
            '</div></div>\n'
        ) % (step["priority"], step["action"], step["reason"], step["time"])

    # Blockers
    blocker_html = ""
    for b in plan.get("blockers", []):
        sev_class = "critical" if b["severity"] == "critical" else (
            "high" if b["severity"] == "high" else "medium"
        )
        blocker_html += (
            '<div class="blocker %s">'
            '<strong>[%s]</strong> %s'
            '<div class="fix">Fix: %s (%s)</div>'
            '</div>\n'
        ) % (sev_class, b["severity"].upper(), b["message"], b["fix"], b["time_to_fix"])

    # Fuel split table
    split_rows = ""
    routes = state.get("fuel_routes", {})
    for key, route in FUEL_ROUTES.items():
        routed = routes.get(key, {}).get("total", 0)
        split_rows += "<tr><td>%d%%</td><td>%s</td><td>$%.4f</td><td>%s</td></tr>\n" % (
            int(route["pct"] * 100), route["label"], routed, route["purpose"]
        )

    # Infrastructure queue
    infra_rows = ""
    for item in plan.get("infrastructure_queue", [])[:6]:
        cost_str = "FREE" if item["cost"] == 0 else "$%.2f" % item["cost"]
        block_badge = ' <span class="blocking">BLOCKING</span>' if item.get("blocking") else ""
        infra_rows += "<tr><td>%d</td><td>%s%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n" % (
            item["roi_rank"], item["name"], block_badge, cost_str,
            item["time_to_revenue"], item["impact"][:80],
        )

    # Product pipeline
    prod_rows = ""
    for idea in plan.get("product_pipeline", [])[:5]:
        prod_rows += "<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>$%.2f</td></tr>\n" % (
            idea["priority"], idea["name"], idea["effort"],
            idea["time_to_build"], idea["expected_revenue"],
        )

    if earned:
        banner = '<div class="banner earned">FUEL CORE ACTIVE -- Revenue loop is ALIVE. Growing the machine.</div>'
    else:
        banner = '<div class="banner pending">FUEL CORE STANDING BY -- $0 earned. Follow the critical path below.</div>'

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FUEL CORE -- SolarPunk 1/99 Growth Engine</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0a0a0a;color:#d4d4d4;padding:24px;max-width:900px;margin:0 auto}
h1{color:#f59e0b;margin-bottom:4px;font-size:1.8em}
h2{color:#fbbf24;margin:28px 0 12px;font-size:1.2em;border-bottom:1px solid #332200;padding-bottom:6px}
.subtitle{color:#888;margin-bottom:20px;font-size:0.9em;font-style:italic}
.mantra{color:#f59e0b;font-weight:700;text-align:center;padding:12px;margin:16px 0;border:1px solid #664400;border-radius:6px;background:#1a1200}
.banner{padding:14px 20px;border-radius:8px;font-weight:bold;margin-bottom:24px;text-align:center}
.banner.earned{background:#14532d;color:#4ade80;border:1px solid #22c55e}
.banner.pending{background:#1c1200;color:#f59e0b;border:1px solid #d97706}
.step{display:flex;gap:14px;margin-bottom:12px;background:#111;border:1px solid #222;border-radius:6px;padding:14px}
.step .num{background:#f59e0b;color:#0a0a0a;width:32px;height:32px;border-radius:50%%;display:flex;align-items:center;justify-content:center;font-weight:bold;flex-shrink:0}
.step .body{flex:1}
.step .body p{color:#999;font-size:0.85em;margin-top:4px}
.step .time{color:#666;font-size:0.75em}
.blocker{padding:10px 14px;border-radius:6px;margin-bottom:8px;font-size:0.85em}
.blocker.critical{background:#1a0000;border:1px solid #dc2626;color:#fca5a5}
.blocker.high{background:#1a0a00;border:1px solid #ea580c;color:#fdba74}
.blocker.medium{background:#1a1a00;border:1px solid #ca8a04;color:#fde68a}
.blocker .fix{color:#888;font-size:0.8em;margin-top:4px}
table{width:100%%;border-collapse:collapse;font-size:0.82em;margin-top:8px}
th{text-align:left;color:#f59e0b;border-bottom:1px solid #333;padding:6px}
td{border-bottom:1px solid #1a1a1a;padding:6px;color:#aaa}
.blocking{background:#dc2626;color:#fff;font-size:0.7em;padding:2px 6px;border-radius:3px;margin-left:6px}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:16px 0}
.stat{background:#111;border:1px solid #222;border-radius:6px;padding:12px;text-align:center}
.stat .val{font-size:1.4em;font-weight:700;color:#f59e0b}
.stat .lbl{font-size:0.75em;color:#666;margin-top:4px}
.pcrf{margin-top:32px;padding:12px;background:#0a1a0a;border:1px solid #334433;border-radius:6px;color:#86efac;font-size:0.82em;text-align:center}
.ts{color:#444;font-size:0.7em;margin-top:20px;text-align:center}
</style>
</head>
<body>
<h1>FUEL CORE</h1>
<p class="subtitle">The 1/99 Revenue Growth Engine</p>
<div class="mantra">The 99/1 system GIVES. The 1/99 system GROWS. Both serve the same mission.</div>

%s

<div class="stat-grid">
<div class="stat"><div class="val">$%.2f</div><div class="lbl">Total Revenue</div></div>
<div class="stat"><div class="val">%d</div><div class="lbl">Products Ready</div></div>
<div class="stat"><div class="val">%d</div><div class="lbl">Listed on Platforms</div></div>
<div class="stat"><div class="val">%d</div><div class="lbl">Blockers</div></div>
</div>

<h2>Critical Path -- Do These NOW</h2>
%s

<h2>Revenue Blockers</h2>
%s

<h2>1/99 Fuel Split</h2>
<table>
<tr><th>%%</th><th>Route</th><th>Routed</th><th>Purpose</th></tr>
%s
</table>

<h2>Infrastructure Queue (by ROI)</h2>
<table>
<tr><th>#</th><th>Action</th><th>Cost</th><th>Time to Revenue</th><th>Impact</th></tr>
%s
</table>

<h2>Product Pipeline</h2>
<table>
<tr><th>#</th><th>Idea</th><th>Effort</th><th>Build Time</th><th>Expected $/sale</th></tr>
%s
</table>

<div class="pcrf">1%% of all growth fuel goes to PCRF (EIN: 93-1057665) -- the reminder that never sleeps.</div>
<div class="ts">Generated %s UTC by FUEL_CORE</div>
</body>
</html>""" % (
        banner,
        revenue,
        plan.get("products_ready", 0),
        plan.get("products_listed", 0),
        len(plan.get("blockers", [])),
        cp_html,
        blocker_html,
        split_rows,
        infra_rows,
        prod_rows,
        now,
    )
    return html


# ---------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------

def run():
    print("=" * 60)
    print("FUEL CORE -- The 1/99 Revenue Growth Engine")
    print("=" * 60)
    print()
    print("  The 99/1 system GIVES. The 1/99 system GROWS.")
    print("  Both serve the same mission.")
    print()

    # 1. Gather all revenue signals
    signals = _gather_revenue_signals()
    print("[signals] Revenue: $%.2f | Products: %d ready, %d listed" % (
        signals["total_earned"],
        signals["products_ready"],
        signals["products_listed_kofi"] + signals["products_listed_gumroad"],
    ))
    print("[signals] Ko-fi: %s | Gumroad: %s | First dollar: %s" % (
        "ALIVE" if signals["kofi_alive"] else "DEAD",
        "ALIVE" if signals["gumroad_alive"] else "DEAD",
        "YES" if signals["first_dollar_earned"] else "NO",
    ))

    # 2. Load or init state
    state = _load("fuel_core_state.json", {
        "engine": "FUEL_CORE",
        "created_at": _ts(),
        "total_fuel_routed": 0.0,
        "fuel_routes": {},
        "cycles": 0,
    })

    # 3. Route fuel through 1/99 split
    routes, new_fuel = _route_fuel(signals["total_earned"], state)
    state["fuel_routes"] = routes
    state["total_fuel_routed"] = round(
        state.get("total_fuel_routed", 0) + max(new_fuel, 0), 6
    )
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = _ts()

    if new_fuel > 0:
        print()
        print("[fuel] New fuel this cycle: $%.4f" % new_fuel)
        for key, route in FUEL_ROUTES.items():
            amount = round(new_fuel * route["pct"], 6)
            print("  %s (%d%%): +$%.6f -> total $%.4f" % (
                route["label"], int(route["pct"] * 100),
                amount, routes[key]["total"],
            ))
    else:
        print()
        print("[fuel] No new revenue to route. Standing by.")
        print("       The machine is built. It needs its first drop of fuel.")

    # 4. Analyze blockers
    blockers = _analyze_blockers(signals)
    print()
    print("[blockers] %d identified:" % len(blockers))
    for b in blockers:
        severity_marker = "!!!" if b["severity"] == "critical" else (
            "!!" if b["severity"] == "high" else "!"
        )
        print("  %s [%s] %s" % (severity_marker, b["severity"].upper(), b["message"]))

    # 5. Build the fuel plan
    plan = _build_fuel_plan(signals, blockers)
    print()
    print("[plan] Critical path (%d steps):" % len(plan["critical_path"]))
    for step in plan["critical_path"]:
        print("  %d. %s (%s)" % (step["priority"], step["action"], step["time"]))

    # 6. Save state
    state["signals_snapshot"] = {
        "total_earned": signals["total_earned"],
        "products_ready": signals["products_ready"],
        "products_listed": signals["products_listed_kofi"] + signals["products_listed_gumroad"],
        "kofi_alive": signals["kofi_alive"],
        "gumroad_alive": signals["gumroad_alive"],
        "first_dollar_earned": signals["first_dollar_earned"],
        "blockers_count": len(blockers),
    }
    state["status"] = "fueling" if signals["first_dollar_earned"] else "ignition_pending"
    _save("fuel_core_state.json", state)
    print()
    print("[write] data/fuel_core_state.json")

    # 7. Save plan
    _save("fuel_plan.json", plan)
    print("[write] data/fuel_plan.json")

    # 8. Build HTML dashboard
    html = _build_html(plan, state)
    (DOCS / "fuel.html").write_text(html, encoding="utf-8")
    print("[write] docs/fuel.html")

    # 9. Summary
    print()
    print("=" * 60)
    if signals["first_dollar_earned"]:
        print("FUEL CORE: ACTIVE. Revenue loop is alive.")
        print("  Routing $%.2f through 1/99 split." % signals["total_earned"])
        print("  Aid routed (1%%): $%.4f" % routes.get("immediate_aid", {}).get("total", 0))
    else:
        print("FUEL CORE: IGNITION PENDING. $0 earned.")
        print("  %d products ready. %d blockers to fix." % (
            signals["products_ready"], len(blockers),
        ))
        print("  Next action: %s" % (
            plan["critical_path"][0]["action"] if plan["critical_path"] else "unknown",
        ))
    print()
    print("  1%% of every growth dollar remembers why we build.")
    print("  PCRF EIN: 93-1057665")
    print("=" * 60)

    return {
        "engine": "FUEL_CORE",
        "status": state["status"],
        "total_earned": signals["total_earned"],
        "total_fuel_routed": state["total_fuel_routed"],
        "products_ready": signals["products_ready"],
        "blockers": len(blockers),
        "critical_path_steps": len(plan["critical_path"]),
        "first_dollar_earned": signals["first_dollar_earned"],
        "ts": _ts(),
    }


if __name__ == "__main__":
    run()
