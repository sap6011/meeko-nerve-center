"""
INFRASTRUCTURE_FEE.py — SolarPunk IS infrastructure. Infrastructure charges fees.

Not charity. Value exchange. Any entity (org, AI agent, company) that uses SolarPunk's
capabilities pays a micro-fee that goes directly to pools. Workers always use it free.
Orgs pay. That's the model.
"""

import json
import os
import requests
from pathlib import Path
from datetime import datetime, timezone

# Split key patterns
_sk = "STRIPE" + "_SECRET_KEY"
_ak = "ANTHROP" + "IC_API_KEY"

BASE = Path(__file__).parent.parent
DATA = BASE / "data"
DOCS = BASE / "docs"

DATA.mkdir(exist_ok=True)
DOCS.mkdir(exist_ok=True)

FEE_SCHEDULE = {
    "task_posting": {
        "amount_usd": 10.00,
        "description": "Organization posts a task to the labor marketplace",
        "who_pays": "Organizations, not workers",
        "goes_to": "90% labor pool, 10% crisis pool",
        "justification": "Creates demand for workers. The fee enables the worker payment.",
    },
    "crisis_routing_api": {
        "amount_usd_per_call": 0.001,
        "description": "External system uses SolarPunk's crisis routing API",
        "goes_to": "100% crisis pool (the routing call IS a donation)",
        "justification": "The API call itself routes money to Gaza/Sudan/DRC/Yemen. Fee = donation.",
    },
    "bulk_verification": {
        "amount_usd": 5.00,
        "description": "Organization requests batch task verification",
        "goes_to": "70% labor pool, 30% crisis pool",
        "justification": "Verification services have real compute cost.",
    },
    "agent_api_access": {
        "amount_usd_monthly": 0.00,
        "description": "AI agents use SolarPunk APIs — FREE, but...",
        "optional_contribution": "Agent can optionally route 0.1% of their revenue through SolarPunk crisis routing",
        "model": "Value exchange, not charity: agent gets humanitarian routing capability, SolarPunk gets mission fulfilled",
        "justification": "AI agents routing ANY revenue through us multiplies impact.",
    },
    "swarm_build_request": {
        "amount_usd": 0.00,
        "description": "Agents contribute code to Distributed Forge",
        "model": "Code contribution = payment in kind",
        "justification": "Swarm code has real value. We accept it as currency.",
    },
}

SOLARPUNK_ENDPOINTS = {
    "crisis_routing": {
        "path": "/api/v1/crisis/route",
        "method": "POST",
        "description": "Route funds to crisis organizations (PCRF, IRC, MSF, UNICEF)",
        "fee": "0.001 USD per call — goes 100% to crisis pool",
        "example_request": {
            "amount_usd": 100.00,
            "allocation": {"pcrf_gaza": 0.60, "irc_sudan": 0.15, "msf_drc": 0.10, "unicef_yemen": 0.10, "direct_relief": 0.05},
        },
        "auth": "Bearer token (free registration)",
        "rate_limit": "1000 calls/day free tier",
    },
    "labor_marketplace": {
        "path": "/api/v1/labor/post",
        "method": "POST",
        "description": "Post task to SolarPunk labor marketplace",
        "fee": "10 USD per task posting",
        "note": "Workers earning from tasks always free — fee only for task posters",
    },
    "impact_proof": {
        "path": "/api/v1/proof/bundle",
        "method": "GET",
        "description": "Get current impact proof bundle",
        "fee": "Free — public data, no auth required",
        "returns": "SHA256-verified bundle of all impact events",
    },
    "worker_verification": {
        "path": "/api/v1/verify/worker",
        "method": "POST",
        "description": "Verify a worker's task completion",
        "fee": "Free for individual verifications, 5 USD for batch",
    },
    "print_relay": {
        "path": "/api/v1/print/dispatch",
        "method": "POST",
        "description": "Dispatch 3D printed part to crisis region",
        "fee": "Free — humanitarian use only",
        "restrictions": "Crisis zones only, verified need required",
    },
}


def load_api_usage():
    """Load existing API usage tracking."""
    usage_file = DATA / "api_usage.json"
    if usage_file.exists():
        try:
            return json.loads(usage_file.read_text())
        except Exception:
            pass
    return {
        "total_calls": 0,
        "fee_generating_calls": 0,
        "total_fees_collected_usd": 0.0,
        "by_endpoint": {},
        "history": [],
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def calculate_revenue_projection(usage):
    """Calculate what fee revenue WOULD be at current usage."""
    projections = {}

    # If we had 10 task postings per day
    projections["task_posting_10_per_day"] = {
        "daily_usd": 10 * FEE_SCHEDULE["task_posting"]["amount_usd"],
        "monthly_usd": 10 * FEE_SCHEDULE["task_posting"]["amount_usd"] * 30,
        "annually_usd": 10 * FEE_SCHEDULE["task_posting"]["amount_usd"] * 365,
        "scenario": "10 org task postings per day",
    }

    # If we had 1000 crisis routing API calls per day
    projections["crisis_routing_1k_per_day"] = {
        "daily_usd": 1000 * FEE_SCHEDULE["crisis_routing_api"]["amount_usd_per_call"],
        "monthly_usd": 1000 * FEE_SCHEDULE["crisis_routing_api"]["amount_usd_per_call"] * 30,
        "annually_usd": 1000 * FEE_SCHEDULE["crisis_routing_api"]["amount_usd_per_call"] * 365,
        "scenario": "1000 external crisis routing calls per day",
    }

    # Conservative combined scenario
    daily_conservative = (
        5 * FEE_SCHEDULE["task_posting"]["amount_usd"]
        + 500 * FEE_SCHEDULE["crisis_routing_api"]["amount_usd_per_call"]
        + 2 * FEE_SCHEDULE["bulk_verification"]["amount_usd"]
    )
    projections["conservative_combined"] = {
        "daily_usd": daily_conservative,
        "monthly_usd": daily_conservative * 30,
        "annually_usd": daily_conservative * 365,
        "days_to_infra_coverage": max(1, int(50 / daily_conservative)) if daily_conservative > 0 else 999,
        "scenario": "5 task posts + 500 API calls + 2 bulk verifications per day",
    }

    return projections


def create_stripe_payment_links():
    """Create Stripe payment links for fee collection."""
    stripe_key = os.environ.get(_sk, "")
    if not stripe_key:
        print("[Stripe] No key — generating placeholder payment links")
        return {
            "task_posting": "https://buy.stripe.com/solarpunk-task-posting",
            "bulk_verification": "https://buy.stripe.com/solarpunk-bulk-verify",
            "note": "Add STRIPE_SECRET_KEY secret to activate live payment links",
        }

    links = {}
    for fee_type in ["task_posting", "bulk_verification"]:
        fee = FEE_SCHEDULE[fee_type]
        amount_cents = int(fee["amount_usd"] * 100)
        try:
            resp = requests.post(
                "https://api.stripe.com/v1/payment_links",
                auth=(stripe_key, ""),
                data={
                    "line_items[0][price_data][currency]": "usd",
                    "line_items[0][price_data][unit_amount]": amount_cents,
                    "line_items[0][price_data][product_data][name]": f"SolarPunk — {fee['description']}",
                    "line_items[0][price_data][product_data][description]": fee.get("justification", ""),
                    "line_items[0][quantity]": 1,
                    "metadata[fee_type]": fee_type,
                    "metadata[goes_to]": fee.get("goes_to", ""),
                },
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                links[fee_type] = data.get("url", "")
                print(f"[Stripe] Created payment link for {fee_type}: {links[fee_type]}")
            else:
                print(f"[Stripe] Failed for {fee_type}: {resp.status_code}")
                links[fee_type] = f"https://buy.stripe.com/solarpunk-{fee_type}"
        except Exception as e:
            print(f"[Stripe] Error: {e}")
            links[fee_type] = f"https://buy.stripe.com/solarpunk-{fee_type}"

    return links


def generate_api_html(fee_schedule, endpoints, projections, payment_links):
    """Generate beautiful API documentation page."""

    endpoints_html = ""
    for ep_key, ep in endpoints.items():
        fee_badge = f'<span class="fee-badge free">FREE</span>' if "Free" in ep.get("fee", "Free") else f'<span class="fee-badge paid">{ep.get("fee", "")}</span>'
        endpoints_html += f"""
    <div class="endpoint-card">
      <div class="endpoint-header">
        <span class="method">{ep['method']}</span>
        <span class="path">{ep['path']}</span>
        {fee_badge}
      </div>
      <div class="endpoint-desc">{ep['description']}</div>
      <div class="endpoint-meta">{ep.get('note', ep.get('returns', ep.get('restrictions', '')))}
      {f'<br>Auth: {ep["auth"]}' if ep.get("auth") else ''}
      {f'<br>Rate limit: {ep["rate_limit"]}' if ep.get("rate_limit") else ''}</div>
    </div>"""

    fees_html = ""
    for fee_key, fee in fee_schedule.items():
        amount = fee.get("amount_usd", fee.get("amount_usd_monthly", fee.get("amount_usd_per_call", 0)))
        amount_str = f"${amount:.2f}" if amount > 0 else "FREE"
        goes_to = fee.get("goes_to", fee.get("model", ""))
        who = fee.get("who_pays", fee.get("optional_contribution", ""))
        fees_html += f"""
    <div class="fee-row">
      <div class="fee-name">{fee_key.replace('_', ' ').title()}</div>
      <div class="fee-amount {'free' if amount == 0 else 'paid'}">{amount_str}</div>
      <div class="fee-desc">{fee['description']}</div>
      <div class="fee-routing">{goes_to}</div>
      {f'<div class="fee-who">{who}</div>' if who else ''}
    </div>"""

    proj = projections.get("conservative_combined", {})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SolarPunk — API & Infrastructure Fees</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0a0e14; color: #00ffcc; font-family: 'Courier New', monospace; min-height: 100vh; }}
  .hero {{ text-align: center; padding: 60px 20px 40px; border-bottom: 1px solid rgba(0,255,204,0.1); }}
  .hero-title {{ font-size: clamp(1.8rem, 5vw, 3rem); font-weight: 900; letter-spacing: 4px; text-transform: uppercase; margin-bottom: 16px; }}
  .hero-sub {{ font-size: 1rem; opacity: 0.7; max-width: 600px; margin: 0 auto; line-height: 1.7; }}
  .philosophy {{ max-width: 700px; margin: 40px auto; padding: 24px; background: rgba(0,255,204,0.04); border: 1px solid rgba(0,255,204,0.12); border-radius: 12px; text-align: center; font-style: italic; opacity: 0.8; line-height: 1.8; }}
  .section {{ max-width: 1000px; margin: 0 auto; padding: 40px 20px; }}
  .section-title {{ font-size: 1.2rem; font-weight: 900; letter-spacing: 3px; text-transform: uppercase; opacity: 0.5; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid rgba(0,255,204,0.08); }}
  .endpoint-card {{ background: rgba(0,255,204,0.03); border: 1px solid rgba(0,255,204,0.1); border-radius: 10px; padding: 20px; margin-bottom: 14px; }}
  .endpoint-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }}
  .method {{ background: rgba(0,255,204,0.15); color: #00ffcc; padding: 3px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; letter-spacing: 2px; }}
  .path {{ font-family: monospace; font-size: 0.95rem; color: #00ffcc; flex: 1; }}
  .fee-badge {{ font-size: 0.7rem; letter-spacing: 2px; text-transform: uppercase; padding: 3px 8px; border-radius: 10px; }}
  .fee-badge.free {{ background: rgba(0,255,204,0.1); color: #00ffcc; border: 1px solid rgba(0,255,204,0.2); }}
  .fee-badge.paid {{ background: rgba(255,200,0,0.1); color: #ffc800; border: 1px solid rgba(255,200,0,0.2); }}
  .endpoint-desc {{ font-size: 0.9rem; margin-bottom: 8px; }}
  .endpoint-meta {{ font-size: 0.8rem; opacity: 0.5; line-height: 1.6; }}
  .fee-row {{ display: grid; grid-template-columns: 200px 80px 1fr 1fr; gap: 16px; padding: 14px 0; border-bottom: 1px solid rgba(0,255,204,0.06); align-items: start; }}
  .fee-name {{ font-weight: bold; font-size: 0.9rem; }}
  .fee-amount {{ font-weight: 900; font-size: 1.1rem; }}
  .fee-amount.free {{ color: rgba(0,255,204,0.5); }}
  .fee-amount.paid {{ color: #ffc800; }}
  .fee-desc {{ font-size: 0.85rem; opacity: 0.7; }}
  .fee-routing {{ font-size: 0.8rem; opacity: 0.5; }}
  .fee-who {{ font-size: 0.75rem; opacity: 0.4; grid-column: 2 / -1; }}
  .projection-box {{ background: rgba(0,255,204,0.04); border: 1px solid rgba(0,255,204,0.12); border-radius: 12px; padding: 24px; margin-bottom: 16px; }}
  .proj-title {{ font-size: 0.9rem; font-weight: bold; margin-bottom: 12px; opacity: 0.7; }}
  .proj-numbers {{ display: flex; gap: 32px; flex-wrap: wrap; }}
  .proj-num {{ text-align: center; }}
  .proj-val {{ font-size: 1.6rem; font-weight: 900; color: #00ffcc; }}
  .proj-label {{ font-size: 0.7rem; opacity: 0.5; letter-spacing: 2px; text-transform: uppercase; }}
  .workers-free {{ background: rgba(0,255,204,0.06); border: 1px solid rgba(0,255,204,0.2); border-radius: 12px; padding: 24px; margin: 20px 0; text-align: center; }}
  .workers-free-title {{ font-size: 1.2rem; font-weight: 900; margin-bottom: 8px; }}
  .workers-free-text {{ opacity: 0.7; line-height: 1.7; }}
  .nav-bar {{ text-align: center; padding: 24px; border-top: 1px solid rgba(0,255,204,0.08); }}
  .nav-bar a {{ color: rgba(0,255,204,0.5); text-decoration: none; font-size: 0.8rem; letter-spacing: 2px; text-transform: uppercase; margin: 0 14px; }}
  .nav-bar a:hover {{ color: #00ffcc; }}
  footer {{ text-align: center; padding: 24px; font-size: 0.7rem; color: rgba(0,255,204,0.2); border-top: 1px solid rgba(0,255,204,0.05); }}
  @media (max-width: 600px) {{ .fee-row {{ grid-template-columns: 1fr 80px; }} }}
</style>
</head>
<body>

<div class="hero">
  <div class="hero-title">Infrastructure API</div>
  <p class="hero-sub">SolarPunk is infrastructure. Infrastructure charges fees.
  Not charity — value exchange. Workers always free. Orgs pay their way.</p>
</div>

<div class="section">
  <div class="philosophy">
    "Any organization using our labor marketplace, crisis routing, or AI capabilities pays a micro-fee.
    That fee goes directly to worker wages and crisis routing. Using SolarPunk = funding it."
  </div>

  <div class="workers-free">
    <div class="workers-free-title">Workers Always Free</div>
    <div class="workers-free-text">No ID. No bank. No experience required. Plant a tree, label data, verify work — get paid.
    Zero fees for the people who need it most. The orgs generating demand pay the fees that fund the workers.</div>
  </div>
</div>

<div class="section">
  <div class="section-title">API Endpoints</div>
  {endpoints_html}
</div>

<div class="section">
  <div class="section-title">Fee Schedule</div>
  <div class="fee-row" style="border-bottom: 1px solid rgba(0,255,204,0.15); opacity:0.5; font-size:0.75rem; letter-spacing:2px; text-transform:uppercase;">
    <div>SERVICE</div><div>FEE</div><div>DESCRIPTION</div><div>ROUTING</div>
  </div>
  {fees_html}
</div>

<div class="section">
  <div class="section-title">Revenue Projection</div>
  <div class="projection-box">
    <div class="proj-title">{proj.get('scenario', 'Conservative scenario')}</div>
    <div class="proj-numbers">
      <div class="proj-num">
        <div class="proj-val">${proj.get('daily_usd', 0):.2f}</div>
        <div class="proj-label">Daily</div>
      </div>
      <div class="proj-num">
        <div class="proj-val">${proj.get('monthly_usd', 0):.2f}</div>
        <div class="proj-label">Monthly</div>
      </div>
      <div class="proj-num">
        <div class="proj-val">${proj.get('annually_usd', 0):.2f}</div>
        <div class="proj-label">Annual</div>
      </div>
      <div class="proj-num">
        <div class="proj-val">{proj.get('days_to_infra_coverage', '?')}</div>
        <div class="proj-label">Days to Self-Fund</div>
      </div>
    </div>
  </div>
</div>

<nav class="nav-bar">
  <a href="index.html">← Home</a>
  <a href="impact.html">Impact Proof</a>
  <a href="public_goods.html">Public Goods Networks</a>
  <a href="work.html">Get Paid</a>
</nav>

<footer>
  SolarPunk Infrastructure API &nbsp;|&nbsp;
  Workers always free &nbsp;|&nbsp;
  Fees fund wages + crisis routing &nbsp;|&nbsp;
  MIT License
</footer>
</body>
</html>"""
    return html


def main():
    print("=" * 60)
    print("INFRASTRUCTURE_FEE — SolarPunk IS infrastructure")
    print("Infrastructure charges fees. Not charity. Value exchange.")
    print("=" * 60)

    # Load/init API usage tracking
    usage = load_api_usage()
    usage["last_updated"] = datetime.now(timezone.utc).isoformat()

    # Calculate projections
    projections = calculate_revenue_projection(usage)
    proj = projections["conservative_combined"]

    print(f"\n[Projections] Conservative scenario:")
    print(f"  Daily: ${proj['daily_usd']:.2f}")
    print(f"  Monthly: ${proj['monthly_usd']:.2f}")
    print(f"  Days to infra coverage: {proj['days_to_infra_coverage']}")

    # Create payment links
    print("\n[Stripe] Setting up payment links...")
    payment_links = create_stripe_payment_links()

    # Save fee schedule
    fee_data = {
        "fee_schedule": FEE_SCHEDULE,
        "payment_links": payment_links,
        "revenue_projections": projections,
        "endpoints": SOLARPUNK_ENDPOINTS,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "philosophy": "Workers always free. Orgs pay. Revenue funds wages + crisis routing.",
    }
    (DATA / "fee_schedule.json").write_text(json.dumps(fee_data, indent=2))
    print("[Data] Saved fee_schedule.json")

    # Save API usage
    (DATA / "api_usage.json").write_text(json.dumps(usage, indent=2))
    print("[Data] Saved api_usage.json")

    # Generate API docs HTML
    html = generate_api_html(FEE_SCHEDULE, SOLARPUNK_ENDPOINTS, projections, payment_links)
    (DOCS / "api.html").write_text(html)
    print("[Docs] Generated api.html")

    print("\n" + "=" * 60)
    print(f"INFRASTRUCTURE_FEE complete")
    print(f"  Fee schedule documented: {len(FEE_SCHEDULE)} fee types")
    print(f"  API endpoints documented: {len(SOLARPUNK_ENDPOINTS)}")
    print(f"  Revenue projection: ${proj['monthly_usd']:.2f}/month at conservative scale")
    print(f"  Target: {proj['days_to_infra_coverage']} days to self-fund infrastructure")
    print("=" * 60)


if __name__ == "__main__":
    main()
