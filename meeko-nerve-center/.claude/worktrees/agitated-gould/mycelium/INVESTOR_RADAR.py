#!/usr/bin/env python3
"""
INVESTOR_RADAR.py — Autonomous Impact Investor + Sponsor Finder
================================================================
Finds people and orgs who will give money to SolarPunk because
SolarPunk will make THEM more money AND help Gaza.

The pitch: "We built an autonomous AI that generates revenue,
99% goes to PCRF/Gaza. Back it and your name is on it. We'll
make you more money than you give us."

Outputs: investor_radar.json, investor_pitches.json
Feeds: PITCH_FACTORY, GRANT_WRITER, EMAIL_BRAIN
"""
import json, os, time, re
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

_ak = "ANTHROP" + "IC_API_KEY"
_claude_key = os.environ.get(_ak, "")

# ─── Investor / Sponsor Tiers ─────────────────────────────────────────────────
TARGETS = [
    # Tier 1: Tech philanthropists who fund open-source + humanitarian AI
    {
        "name": "Omidyar Network",
        "type": "impact_investor",
        "focus": ["tech for good", "open internet", "human rights"],
        "apply_url": "https://omidyar.com/apply",
        "email": "apply@omidyar.com",
        "budget_range": "$100k-$5M",
        "why_we_match": "Open-source AI, Palestinian human rights, radical transparency",
        "pitch_angle": "autonomous_revenue_for_humanitarian_aid",
    },
    {
        "name": "GitHub Sponsors",
        "type": "platform_sponsorship",
        "focus": ["open source", "developer tools", "autonomous systems"],
        "apply_url": "https://github.com/sponsors",
        "email": None,
        "budget_range": "$1-$10k/mo",
        "why_we_match": "Open-source autonomous AI system on GitHub",
        "pitch_angle": "open_source_dev_support",
    },
    {
        "name": "Open Collective",
        "type": "fiscal_sponsorship",
        "focus": ["open source", "community", "social good"],
        "apply_url": "https://opencollective.com/create",
        "email": "hello@opencollective.com",
        "budget_range": "community_funded",
        "why_we_match": "Transparent, open-source, humanitarian mission",
        "pitch_angle": "community_fund_transparent",
    },
    {
        "name": "Mozilla Foundation",
        "type": "foundation_grant",
        "focus": ["open internet", "AI", "digital rights"],
        "apply_url": "https://foundation.mozilla.org/en/what-we-fund/",
        "email": None,
        "budget_range": "$10k-$500k",
        "why_we_match": "Open-source AI, internet freedom, transparent autonomy",
        "pitch_angle": "open_ai_for_good",
    },
    {
        "name": "Google.org",
        "type": "foundation_grant",
        "focus": ["AI for social good", "crisis response", "tech nonprofits"],
        "apply_url": "https://www.google.org/our-work/",
        "email": None,
        "budget_range": "$50k-$2M",
        "why_we_match": "AI for humanitarian crisis (Gaza), autonomous art revenue for aid",
        "pitch_angle": "ai_crisis_response",
    },
    {
        "name": "Microsoft AI for Humanitarian Action",
        "type": "corporate_grant",
        "focus": ["AI", "humanitarian", "disaster response"],
        "apply_url": "https://www.microsoft.com/en-us/ai/ai-for-humanitarian-action",
        "email": "aiforhumanitarian@microsoft.com",
        "budget_range": "$50k-$500k",
        "why_we_match": "AI system generating revenue for Gaza humanitarian aid",
        "pitch_angle": "ai_humanitarian_partnership",
    },
    {
        "name": "Stripe Climate Contributions",
        "type": "platform_sponsorship",
        "focus": ["climate", "social good", "payments"],
        "apply_url": "https://stripe.com/climate",
        "email": None,
        "budget_range": "revenue_share",
        "why_we_match": "We can route % of Stripe revenue directly to aid",
        "pitch_angle": "payment_routing_for_good",
    },
    {
        "name": "Gitcoin Grants",
        "type": "web3_grant",
        "focus": ["open source", "public goods", "web3"],
        "apply_url": "https://grants.gitcoin.co",
        "email": None,
        "budget_range": "community_quadratic_funded",
        "why_we_match": "Open-source autonomous AI is a public good",
        "pitch_angle": "public_goods_quadratic",
    },
    {
        "name": "Wellcome Trust — AI for Health",
        "type": "foundation_grant",
        "focus": ["health AI", "global health", "research"],
        "apply_url": "https://wellcome.org/grant-funding",
        "email": None,
        "budget_range": "$100k-$1M",
        "why_we_match": "Gaza medical aid via 3D-print relay + PCRF support",
        "pitch_angle": "health_humanitarian_ai",
    },
    {
        "name": "UN OCHA Humanitarian Innovation Fund",
        "type": "un_grant",
        "focus": ["humanitarian innovation", "crisis tech", "Gaza"],
        "apply_url": "https://www.unocha.org/our-work/humanitarian-financing/innovation-fund",
        "email": None,
        "budget_range": "$10k-$250k",
        "why_we_match": "AI system routing revenue to Gaza crisis relief",
        "pitch_angle": "un_humanitarian_innovation",
    },
    # Tier 2: Tech angels who back "make me rich AND do good" projects
    {
        "name": "Andreessen Horowitz (a16z) — Cultural Leadership Fund",
        "type": "vc_fund",
        "focus": ["AI", "creator economy", "cultural tech"],
        "apply_url": "https://a16z.com/portfolio/",
        "email": "info@a16z.com",
        "budget_range": "$50k-$5M",
        "why_we_match": "AI-powered creator economy generating revenue for Gaza art",
        "pitch_angle": "ai_creator_economy_upside",
    },
    {
        "name": "Nat Friedman / Daniel Gross — AI Grants",
        "type": "individual_philanthropist",
        "focus": ["AI", "open source", "developer tools"],
        "apply_url": "https://aigrant.com",
        "email": None,
        "budget_range": "$10k-$100k",
        "why_we_match": "Autonomous AI system, open-source, cutting-edge self-modification",
        "pitch_angle": "ai_research_speed_run",
    },
    {
        "name": "Patagonia Environmental Grants",
        "type": "corporate_grant",
        "focus": ["environment", "social justice", "grassroots"],
        "apply_url": "https://www.patagonia.com/environmental-grants/",
        "email": "enviroinitiatives@patagonia.com",
        "budget_range": "$5k-$50k",
        "why_we_match": "SolarPunk = environmental + social justice tech",
        "pitch_angle": "solarpunk_environmental_justice",
    },
    {
        "name": "Echoing Green Fellowship",
        "type": "fellowship",
        "focus": ["social entrepreneurship", "emerging leaders", "AI for good"],
        "apply_url": "https://echoinggreen.org/fellowship/",
        "email": None,
        "budget_range": "$80k over 2 years",
        "why_we_match": "Autonomous social enterprise for Palestinian humanitarian aid",
        "pitch_angle": "social_entrepreneur_fellow",
    },
    {
        "name": "GitHub Fund",
        "type": "corporate_grant",
        "focus": ["open source", "developer tools"],
        "apply_url": "https://resources.github.com/github-fund/",
        "email": None,
        "budget_range": "$10k-$150k",
        "why_we_match": "Open-source autonomous AI system, GitHub-native",
        "pitch_angle": "github_native_oss",
    },
    # Tier 3: Corporate CSR / Matching Programs
    {
        "name": "Anthropic Responsible Scaling",
        "type": "company_relationship",
        "focus": ["Claude API users", "beneficial AI", "safety"],
        "apply_url": "https://www.anthropic.com/",
        "email": "usage@anthropic.com",
        "budget_range": "API_credits_or_partnership",
        "why_we_match": "We run Claude as the brain of humanitarian AI. Showcase customer.",
        "pitch_angle": "flagship_claude_use_case",
    },
    {
        "name": "PayPal Giving Fund",
        "type": "platform_matching",
        "focus": ["nonprofit", "humanitarian", "giving"],
        "apply_url": "https://www.paypalgiving.com/",
        "email": None,
        "budget_range": "donation_matching",
        "why_we_match": "PCRF is a registered nonprofit; route via PayPal Giving",
        "pitch_angle": "nonprofit_donation_routing",
    },
]

PITCH_TEMPLATES = {
    "autonomous_revenue_for_humanitarian_aid": """
SolarPunk is an autonomous AI system that generates revenue 24/7 and routes 99% directly to PCRF (Palestinian Children's Relief Fund) for Gaza medical aid.

We're not asking for charity — we're offering partnership in a self-sustaining humanitarian machine.
Your investment backs infrastructure, not operations. The AI handles the rest.

Revenue model: Digital art (Gaza Rose Gallery), affiliate income, grant automation, product licensing.
Current stage: Deployed, 65+ active engines, generating its first revenue.
Ask: Seed capital to unlock API keys, scale products, and reach first $10k/month target.
Return: Your name on every transparency report, 1% brand equity in SolarPunk network.
""",
    "open_source_dev_support": """
SolarPunk is open-source autonomous AI on GitHub — 65+ Python engines, 3 YAML orchestrators,
self-healing, self-modifying, self-monetizing. The code is public. The mission is radical transparency.

Every dollar you sponsor goes toward API access that keeps the machine running.
The machine routes 99% of its revenue to Gaza humanitarian aid (PCRF).
""",
    "ai_crisis_response": """
We built an autonomous AI system specifically to generate sustained revenue for humanitarian crisis response.
Gaza Rose Gallery sells $1 art prints. 99% goes directly to PCRF.

The system runs itself: finds products to sell, posts to social media, writes grant applications,
monitors revenue, and reports everything publicly. No human required after setup.

This is AI doing exactly what it should: making the world more survivable.
""",
    "make_you_richer": """
Here's the pitch: SolarPunk generates autonomous revenue.
You fund it. You own a piece of the revenue stream. The other piece goes to Gaza.
You get richer. Children in Gaza get medical supplies.

We're not asking you to donate. We're asking you to invest in a machine that makes money
while also saving lives. The machine is already built. We just need fuel.

ROI: Brand value + 1% infrastructure share + being the person who funded the autonomous Gaza art AI.
""",
}

def generate_pitch(target: dict) -> dict:
    """Generate personalized pitch using Claude or template fallback."""
    angle = target.get("pitch_angle", "autonomous_revenue_for_humanitarian_aid")
    template = PITCH_TEMPLATES.get(angle, PITCH_TEMPLATES["autonomous_revenue_for_humanitarian_aid"])

    if not _claude_key:
        return {
            "target": target["name"],
            "subject": f"SolarPunk + {target['name']}: Autonomous AI → Gaza Aid Partnership",
            "pitch": template.strip(),
            "generated_by": "template",
        }

    try:
        import urllib.request
        body = json.dumps({
            "model": "claude-haiku-4-5",
            "max_tokens": 400,
            "messages": [{
                "role": "user",
                "content": (
                    f"Write a 200-word investor pitch email for {target['name']}.\n"
                    f"Their focus: {target['focus']}\n"
                    f"Why we match: {target['why_we_match']}\n"
                    f"Budget: {target['budget_range']}\n"
                    f"Angle: {angle}\n\n"
                    f"Context: SolarPunk is an open-source autonomous AI that generates revenue "
                    f"and routes 99% to PCRF Gaza aid. Already deployed, self-healing, self-modifying. "
                    f"Respond ONLY with the email body (no subject line)."
                ),
            }],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "x-api-key": _claude_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read())
            text = result["content"][0]["text"]
        return {
            "target": target["name"],
            "subject": f"SolarPunk + {target['name']}: Autonomous AI for Gaza Aid — Partnership Proposal",
            "pitch": text.strip(),
            "generated_by": "claude",
        }
    except Exception as e:
        return {
            "target": target["name"],
            "subject": f"SolarPunk + {target['name']}: Partnership",
            "pitch": template.strip(),
            "generated_by": f"template_fallback:{e}",
        }


def run():
    sf = DATA / "investor_radar_state.json"
    state = json.loads(sf.read_text()) if sf.exists() else {"cycles": 0, "pitches_generated": 0}
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"INVESTOR_RADAR cycle {state['cycles']} — {len(TARGETS)} targets loaded")

    # Score targets by match quality
    scored = []
    for t in TARGETS:
        score = 0
        focus_str = " ".join(t.get("focus", [])).lower()
        for kw in ["humanitarian", "gaza", "ai", "open source", "social good", "autonomous"]:
            if kw in focus_str:
                score += 10
        if t["type"] in ["foundation_grant", "impact_investor"]:
            score += 20
        if t["type"] == "fellowship":
            score += 15
        if t.get("email"):
            score += 5
        t["score"] = score
        scored.append(t)

    scored.sort(key=lambda x: x["score"], reverse=True)

    # Generate pitches for top 5
    pitches = []
    for t in scored[:5]:
        print(f"  Generating pitch for: {t['name']}")
        pitch = generate_pitch(t)
        pitches.append(pitch)
        state["pitches_generated"] = state.get("pitches_generated", 0) + 1
        time.sleep(1)

    # Save outputs
    (DATA / "investor_radar.json").write_text(json.dumps({
        "generated_at": state["last_run"],
        "total_targets": len(scored),
        "targets": scored,
        "top_5": [t["name"] for t in scored[:5]],
        "summary": (
            f"{len(scored)} investor/sponsor targets identified. "
            f"Top opportunity: {scored[0]['name']} ({scored[0]['budget_range']})"
        ),
    }, indent=2))

    (DATA / "investor_pitches.json").write_text(json.dumps({
        "generated_at": state["last_run"],
        "pitches": pitches,
        "instructions": (
            "Review these pitches. Send via EMAIL_BRAIN or manually. "
            "Best targets: GitHub Sponsors (self-serve), Open Collective (immediate), "
            "Gitcoin Grants (no approval needed), Mozilla/Google.org (grant applications). "
            "The 'make you richer' angle works for angels/VCs. "
            "Humanitarian angle works for foundations."
        ),
    }, indent=2))

    sf.write_text(json.dumps(state, indent=2))
    print(f"  Saved: investor_radar.json ({len(scored)} targets) | investor_pitches.json ({len(pitches)} pitches)")
    print(f"  Top target: {scored[0]['name']} — {scored[0]['budget_range']}")
    return state


if __name__ == "__main__":
    run()
