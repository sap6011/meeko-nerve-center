# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""FIRST_DOLLAR_ENGINE — Find the single fastest path to $1 revenue.

Reads every product, every listing, every signal. Scores them all.
Picks ONE winner and writes a step-by-step instruction set so precise
that a human (or a future browser-automation engine) can follow it
blindly. Also generates a dark-themed HTML dashboard at docs/first_dollar.html.

When the first dollar lands in proof_ledger.json, it celebrates.

15%% of all revenue goes to Palestinian Children's Relief Fund
(PCRF, EIN: 93-1057665).
"""
import os
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

KOFI_SHOP = "https://ko-fi.com/meekotharaccoon"
KOFI_POST = "https://ko-fi.com/meekotharaccoon/shop"
PCRF_LINE = "15%% of all revenue goes to Palestinian Children's Relief Fund (PCRF, EIN: 93-1057665)"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _rj(name, fallback=None):
    """Read a JSON file from DATA, return fallback on any failure."""
    p = DATA / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return fallback if fallback is not None else {}


def _ts():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------

def _score_product(pid, prod, listings, signals):
    """Return a numeric score. Higher = more likely to earn the first dollar.

    Scoring axes (all 0-100, then weighted):
      - price_score:    lower price -> higher score (1$ = 100)
      - copy_score:     has kofi listing copy ready -> +40
      - platform_score: kofi_url already set -> +30, or shop listing exists -> +20
      - content_score:  content_ready + file exists -> +20
      - signal_score:   any inbound traffic for this product -> +10
    """
    price = float(prod.get("price", 99))
    # price_score: $1 = 100, $5 = 60, $12 = 28, $25 = 4
    price_score = max(0, 100 - (price - 1) * 4)

    listing = listings.get(pid, {})
    has_kofi_copy = bool(listing.get("kofi", ""))
    copy_score = 40 if has_kofi_copy else 0

    has_kofi_url = bool(prod.get("kofi_url"))
    platform_score = 30 if has_kofi_url else (20 if has_kofi_copy else 0)

    content_ready = prod.get("content_ready", False)
    file_path = prod.get("file_path", "")
    file_exists = Path(file_path).exists() if file_path else False
    content_score = 20 if (content_ready and file_exists) else (10 if content_ready else 0)

    signal_hits = 0
    for sig in signals:
        ref = sig.get("product_id", "") or sig.get("url", "") or ""
        if pid in ref:
            signal_hits += 1
    signal_score = min(10, signal_hits * 2)

    total = price_score + copy_score + platform_score + content_score + signal_score
    breakdown = {
        "price_score": price_score,
        "copy_score": copy_score,
        "platform_score": platform_score,
        "content_score": content_score,
        "signal_score": signal_score,
        "total": total,
    }
    return total, breakdown


# ---------------------------------------------------------------------------
# instruction builder
# ---------------------------------------------------------------------------

def _build_instructions(pid, prod, listing):
    """Return a list of step dicts — the exact clicks/pastes to list on Ko-fi."""
    kofi_copy = listing.get("kofi", "")
    # parse TITLE / DESCRIPTION / PRICE / TAGS from kofi copy block
    title = prod.get("title", pid)
    description = ""
    price = "$%.2f" % float(prod.get("price", 1))
    tags = ""
    for line in kofi_copy.split("\n"):
        stripped = line.strip()
        if stripped.startswith("TITLE:"):
            title = stripped.replace("TITLE:", "").strip()
        elif stripped.startswith("PRICE:"):
            price = stripped.replace("PRICE:", "").strip()
        elif stripped.startswith("TAGS:"):
            tags = stripped.replace("TAGS:", "").strip()
    # description is everything between DESCRIPTION: and PRICE:
    if "DESCRIPTION:" in kofi_copy:
        desc_block = kofi_copy.split("DESCRIPTION:")[1]
        if "PRICE:" in desc_block:
            desc_block = desc_block.split("PRICE:")[0]
        description = desc_block.strip()

    file_path = prod.get("file_path", "")
    download_url = prod.get("download_url", "")

    steps = [
        {
            "step": 1,
            "action": "Open Ko-fi shop dashboard",
            "url": "https://ko-fi.com/manage/shop",
            "detail": "Log in as meekotharaccoon if not already logged in.",
        },
        {
            "step": 2,
            "action": "Click 'Add New Item' (or '+ New Product')",
            "url": "https://ko-fi.com/manage/shop",
            "detail": "Look for the blue button to add a new digital product.",
        },
        {
            "step": 3,
            "action": "Set product title",
            "paste": title,
            "detail": "Paste this exact text into the Title field.",
        },
        {
            "step": 4,
            "action": "Set product description",
            "paste": description,
            "detail": "Paste this into the Description field. Includes PCRF disclosure.",
        },
        {
            "step": 5,
            "action": "Set price",
            "paste": price,
            "detail": "Enter this amount in the Price field.",
        },
        {
            "step": 6,
            "action": "Upload the product file",
            "file": file_path,
            "fallback_url": download_url,
            "detail": "Upload '%s'. If the file is not on disk, download from: %s" % (file_path, download_url) if download_url else "Upload '%s' from local disk." % file_path,
        },
        {
            "step": 7,
            "action": "Add tags",
            "paste": tags,
            "detail": "Add each tag separated by commas.",
        },
        {
            "step": 8,
            "action": "Publish the listing",
            "url": "https://ko-fi.com/manage/shop",
            "detail": "Click 'Publish' or 'Save'. The product goes live immediately.",
        },
        {
            "step": 9,
            "action": "Verify the live listing",
            "url": KOFI_POST,
            "detail": "Visit the public shop and confirm the product appears.",
        },
        {
            "step": 10,
            "action": "Share the link",
            "url": KOFI_SHOP,
            "detail": "Post this link on Bluesky / Mastodon / social queue. The first dollar is one share away.",
        },
    ]
    return steps


# ---------------------------------------------------------------------------
# HTML dashboard
# ---------------------------------------------------------------------------

def _build_html(plan):
    """Generate docs/first_dollar.html -- dark-themed plan dashboard."""
    winner = plan.get("winner", {})
    steps = plan.get("steps", [])
    scored = plan.get("scored_products", [])
    earned = plan.get("first_dollar_earned", False)

    step_rows = ""
    for s in steps:
        link = ""
        if s.get("url"):
            link = '<a href="%s" target="_blank">%s</a>' % (s.get("url"), s.get("url"))
        paste_block = ""
        if s.get("paste"):
            paste_block = '<pre class="paste">%s</pre>' % s.get("paste", "").replace("<", "&lt;").replace(">", "&gt;")
        step_rows += """<div class="step">
  <span class="num">%s</span>
  <div class="body">
    <strong>%s</strong>
    <p>%s</p>%s%s
  </div>
</div>\n""" % (s.get("step", ""), s.get("action", ""), s.get("detail", ""), link, paste_block)

    rank_rows = ""
    for i, sp in enumerate(scored[:10]):
        rank_rows += "<tr><td>%d</td><td>%s</td><td>$%.2f</td><td>%s</td></tr>\n" % (
            i + 1, sp.get("title", ""), sp.get("price", 0), sp.get("score", 0)
        )

    if earned:
        banner = '<div class="banner earned">FIRST DOLLAR EARNED. The loop is alive.</div>'
    else:
        banner = '<div class="banner pending">First dollar: PENDING. Follow the steps below.</div>'

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>First Dollar Plan -- SolarPunk</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0a0a0a;color:#d4d4d4;padding:24px;max-width:800px;margin:0 auto}
h1{color:#4ade80;margin-bottom:8px;font-size:1.8em}
h2{color:#86efac;margin:28px 0 12px;font-size:1.2em}
.subtitle{color:#666;margin-bottom:20px;font-size:0.9em}
.banner{padding:14px 20px;border-radius:8px;font-weight:bold;margin-bottom:24px;text-align:center}
.banner.earned{background:#14532d;color:#4ade80;border:1px solid #22c55e}
.banner.pending{background:#1c1917;color:#fb923c;border:1px solid #f97316}
.winner{background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:16px;margin-bottom:24px}
.winner h3{color:#4ade80;margin-bottom:4px}
.winner .price{color:#fbbf24;font-size:1.4em;font-weight:bold}
.winner .reason{color:#888;font-size:0.85em;margin-top:6px}
.step{display:flex;gap:14px;margin-bottom:16px;background:#111;border:1px solid #222;border-radius:6px;padding:14px}
.step .num{background:#4ade80;color:#0a0a0a;width:32px;height:32px;border-radius:50%%;display:flex;align-items:center;justify-content:center;font-weight:bold;flex-shrink:0}
.step .body{flex:1}
.step .body p{color:#999;font-size:0.85em;margin-top:4px}
.step .body a{color:#60a5fa;font-size:0.82em;word-break:break-all}
.paste{background:#0d1117;border:1px solid #30363d;border-radius:4px;padding:10px;font-size:0.78em;color:#c9d1d9;white-space:pre-wrap;margin-top:6px;max-height:160px;overflow-y:auto}
table{width:100%%;border-collapse:collapse;font-size:0.85em}
th{text-align:left;color:#4ade80;border-bottom:1px solid #333;padding:6px}
td{border-bottom:1px solid #1a1a1a;padding:6px;color:#aaa}
.pcrf{margin-top:32px;padding:12px;background:#1a1a0a;border:1px solid #444;border-radius:6px;color:#fbbf24;font-size:0.82em;text-align:center}
.ts{color:#444;font-size:0.7em;margin-top:20px;text-align:center}
</style>
</head>
<body>
<h1>First Dollar Plan</h1>
<p class="subtitle">SolarPunk Autonomous Revenue -- the shortest path to $1</p>

%s

<div class="winner">
  <h3>%s</h3>
  <div class="price">%s</div>
  <div class="reason">Score: %s / 200 -- %s</div>
</div>

<h2>Step-by-Step Instructions</h2>
%s

<h2>Product Rankings</h2>
<table>
<tr><th>#</th><th>Product</th><th>Price</th><th>Score</th></tr>
%s
</table>

<div class="pcrf">%s</div>
<div class="ts">Generated %s by FIRST_DOLLAR_ENGINE</div>
</body>
</html>""" % (
        banner,
        winner.get("title", "?"),
        "$%.2f" % winner.get("price", 0),
        winner.get("score", "?"),
        winner.get("reason", ""),
        step_rows,
        rank_rows,
        PCRF_LINE.replace("%%", "%"),
        plan.get("generated_at", ""),
    )
    return html


# ---------------------------------------------------------------------------
# celebration check
# ---------------------------------------------------------------------------

def _check_first_dollar():
    """Check proof_ledger.json for any sale >= $1. Return True if earned."""
    ledger = _rj("proof_ledger.json", {})
    total = float(ledger.get("total_sales", 0))
    if total >= 1.0:
        return True
    sales = ledger.get("sales", [])
    if len(sales) > 0:
        return True
    # also check quick_revenue
    qr = _rj("quick_revenue.json", {})
    if float(qr.get("total_revenue", 0)) >= 1.0:
        return True
    return False


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def run():
    print("=" * 60)
    print("FIRST_DOLLAR_ENGINE -- finding the fastest path to $1")
    print("=" * 60)

    # 1. Load all data sources
    registry = _rj("product_registry.json", {})
    products = registry.get("products", {})
    print("[load] product_registry: %d products" % len(products))

    listings_data = _rj("storefront_listings.json", {})
    listings = listings_data.get("listings", {})
    print("[load] storefront_listings: %d listings" % len(listings))

    quick_rev = _rj("quick_revenue.json", {})
    print("[load] quick_revenue: total=$%.2f" % float(quick_rev.get("total_revenue", 0)))

    signals_data = _rj("inbound_signals.json", {"signals": []})
    signals = signals_data.get("signals", [])
    print("[load] inbound_signals: %d signals" % len(signals))

    if not products:
        print("[WARN] No products in registry. Nothing to score.")
        return

    # 2. Score every product
    scored = []
    for pid, prod in products.items():
        score, breakdown = _score_product(pid, prod, listings, signals)
        scored.append({
            "id": pid,
            "title": prod.get("title", pid),
            "price": float(prod.get("price", 0)),
            "score": score,
            "breakdown": breakdown,
            "content_ready": prod.get("content_ready", False),
            "has_listing": pid in listings,
        })
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)

    for i, s in enumerate(scored[:5]):
        print("[rank %d] %s -- $%.2f -- score %s" % (i + 1, s.get("title"), s.get("price"), s.get("score")))

    # 3. Pick the winner
    winner_entry = scored[0]
    winner_pid = winner_entry.get("id")
    winner_prod = products.get(winner_pid, {})
    winner_listing = listings.get(winner_pid, {})

    # Build reason string
    bd = winner_entry.get("breakdown", {})
    reasons = []
    if bd.get("price_score", 0) >= 80:
        reasons.append("lowest price")
    if bd.get("copy_score", 0) > 0:
        reasons.append("ko-fi copy ready")
    if bd.get("content_score", 0) > 0:
        reasons.append("content verified")
    if bd.get("platform_score", 0) > 0:
        reasons.append("platform listing exists")
    reason = ", ".join(reasons) if reasons else "best overall score"

    print("")
    print(">>> WINNER: %s ($%.2f) -- %s" % (winner_entry.get("title"), winner_entry.get("price"), reason))

    # 4. Build step-by-step instructions
    steps = _build_instructions(winner_pid, winner_prod, winner_listing)

    # 5. Check first dollar status
    earned = _check_first_dollar()
    if earned:
        print("")
        print("*" * 60)
        print("*** FIRST DOLLAR EARNED! The revenue loop is ALIVE. ***")
        print("*** %s ***" % PCRF_LINE.replace("%%", "%"))
        print("*" * 60)
    else:
        print("")
        print("[status] First dollar: NOT YET. Follow the steps above.")

    # 6. Build the plan object
    plan = {
        "generated_at": _ts(),
        "engine": "FIRST_DOLLAR_ENGINE",
        "first_dollar_earned": earned,
        "winner": {
            "id": winner_pid,
            "title": winner_entry.get("title"),
            "price": winner_entry.get("price"),
            "score": winner_entry.get("score"),
            "reason": reason,
            "kofi_shop": KOFI_SHOP,
            "file_path": winner_prod.get("file_path", ""),
            "download_url": winner_prod.get("download_url", ""),
        },
        "steps": steps,
        "scored_products": scored,
        "pcrf": PCRF_LINE.replace("%%", "%"),
        "quick_revenue_total": float(quick_rev.get("total_revenue", 0)),
    }

    # 7. Write data/first_dollar_plan.json
    plan_path = DATA / "first_dollar_plan.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print("[write] %s" % plan_path)

    # 8. Write docs/first_dollar.html
    html = _build_html(plan)
    html_path = DOCS / "first_dollar.html"
    html_path.write_text(html, encoding="utf-8")
    print("[write] %s" % html_path)

    # 9. Write state for LIVE_WIRE
    state = {
        "engine": "FIRST_DOLLAR_ENGINE",
        "ts": _ts(),
        "status": "celebrated" if earned else "hunting",
        "winner_id": winner_pid,
        "winner_title": winner_entry.get("title"),
        "winner_price": winner_entry.get("price"),
        "winner_score": winner_entry.get("score"),
        "products_scored": len(scored),
        "first_dollar_earned": earned,
        "quick_revenue_total": float(quick_rev.get("total_revenue", 0)),
    }
    # Nervous system awareness
    try:
        _h = json.loads((DATA / "homeostasis_state.json").read_text(encoding="utf-8"))
    except Exception:
        _h = {}
    try:
        _c = json.loads((DATA / "neural_cortex_state.json").read_text(encoding="utf-8"))
    except Exception:
        _c = {}
    state["nervous_system"] = {
        "equilibrium": _h.get("equilibrium", 0),
        "brain_confidence": _c.get("decision_confidence", 0),
    }
    (DATA / "first_dollar_engine_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    print("[write] data/first_dollar_engine_state.json")

    print("")
    print("FIRST_DOLLAR_ENGINE complete. %d products scored." % len(scored))
    return plan


if __name__ == "__main__":
    run()
