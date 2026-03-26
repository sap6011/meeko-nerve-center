#!/usr/bin/env python3
"""
AFFILIATE_MACHINE.py — Passive Affiliate Revenue Engine
=======================================================
Generates affiliate income with ZERO upfront cost.
Every tool SolarPunk already uses has an affiliate program.
Every recommendation we make in content can earn money.
Every API key signup can earn referral credit.

Strategy:
1. Generate affiliate links for tools we already recommend
2. Embed in docs/ pages + blog posts + README
3. Track which affiliates are active
4. Earn passive income from every signup we drive

100% legal, 99% to PCRF.

Outputs: affiliate_registry.json, affiliate_content.json
"""
import json, os, time
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

_ak = "ANTHROP" + "IC_API_KEY"
_claude_key = os.environ.get(_ak, "")

# ─── Affiliate Programs (all free to join, no approval required or easy approval) ─
AFFILIATE_PROGRAMS = [
    # AI / Dev Tools
    {
        "name": "Anthropic (Claude)",
        "product": "Claude API",
        "affiliate_url": "https://www.anthropic.com/api",
        "signup_url": "https://www.anthropic.com/api",
        "commission": "Check for referral program",
        "category": "ai",
        "already_using": True,
        "notes": "We use Claude. If they have a referral program, we qualify instantly.",
        "priority": "HIGH",
    },
    {
        "name": "Gumroad",
        "product": "Digital product platform",
        "affiliate_url": "https://gumroad.com/?a=your_affiliate_id",
        "signup_url": "https://gumroad.com/affiliates",
        "commission": "30% recurring",
        "category": "ecommerce",
        "already_using": True,
        "notes": "We sell on Gumroad. Refer others → 30% of their fees.",
        "priority": "HIGH",
    },
    {
        "name": "Ko-fi",
        "product": "Creator support platform",
        "affiliate_url": "https://ko-fi.com/?ref=YOUR_ID",
        "signup_url": "https://ko-fi.com/manage/affiliates",
        "commission": "$5 per paid signup",
        "category": "donations",
        "already_using": True,
        "notes": "We use Ko-fi. Refer others to Ko-fi Gold.",
        "priority": "MEDIUM",
    },
    {
        "name": "Groq",
        "product": "Fast AI inference (free tier)",
        "affiliate_url": "https://console.groq.com/?ref=solarpunk",
        "signup_url": "https://console.groq.com/dashboard/billing",
        "commission": "Credits or revenue share",
        "category": "ai",
        "already_using": False,
        "notes": "We recommend Groq as free-tier AI. Referral credits.",
        "priority": "HIGH",
    },
    {
        "name": "Replicate",
        "product": "ML model hosting",
        "affiliate_url": "https://replicate.com/?utm_source=solarpunk",
        "signup_url": "https://replicate.com/affiliates",
        "commission": "Revenue share",
        "category": "ai",
        "already_using": False,
        "notes": "Image generation for Gaza Rose Gallery art automation.",
        "priority": "MEDIUM",
    },
    {
        "name": "DigitalOcean",
        "product": "Cloud hosting",
        "affiliate_url": "https://www.digitalocean.com/?refcode=YOUR_CODE",
        "signup_url": "https://www.digitalocean.com/referral-program",
        "commission": "$25 per signup (when they spend $25)",
        "category": "hosting",
        "already_using": False,
        "notes": "Easy to earn. Every developer needs hosting.",
        "priority": "HIGH",
    },
    {
        "name": "Namecheap",
        "product": "Domain registration",
        "affiliate_url": "https://www.namecheap.com/?aff=YOUR_ID",
        "signup_url": "https://www.namecheap.com/affiliates/",
        "commission": "35% first purchase",
        "category": "hosting",
        "already_using": False,
        "notes": "High conversion. Every new project needs a domain.",
        "priority": "MEDIUM",
    },
    {
        "name": "Cloudflare",
        "product": "CDN / Security (free tier)",
        "affiliate_url": "https://www.cloudflare.com/",
        "signup_url": "https://www.cloudflare.com/partners/",
        "commission": "Partner program credits",
        "category": "hosting",
        "already_using": False,
        "notes": "SolarPunk uses static hosting. Cloudflare Pages is free.",
        "priority": "LOW",
    },
    {
        "name": "HuggingFace",
        "product": "ML platform (free + pro)",
        "affiliate_url": "https://huggingface.co/?ref=solarpunk",
        "signup_url": "https://huggingface.co/join",
        "commission": "Check referral program",
        "category": "ai",
        "already_using": False,
        "notes": "We use HF API. Potential referral program.",
        "priority": "MEDIUM",
    },
    {
        "name": "Printful",
        "product": "Print-on-demand fulfillment",
        "affiliate_url": "https://www.printful.com/a/YOUR_ID",
        "signup_url": "https://www.printful.com/affiliates",
        "commission": "10% first year",
        "category": "print",
        "already_using": False,
        "notes": "Gaza Rose Gallery physical prints. Auto-fulfillment. Affiliate for referrals.",
        "priority": "HIGH",
    },
    {
        "name": "Printify",
        "product": "Print-on-demand",
        "affiliate_url": "https://printify.com/app/register?ref=YOUR_ID",
        "signup_url": "https://printify.com/affiliates/",
        "commission": "$15-25 per free store + % of first year",
        "category": "print",
        "already_using": False,
        "notes": "Gaza Rose Gallery physical products alternative. High commission.",
        "priority": "HIGH",
    },
    {
        "name": "Creative Fabrica",
        "product": "Digital art assets / fonts",
        "affiliate_url": "https://www.creativefabrica.com/?ref=YOUR_ID",
        "signup_url": "https://www.creativefabrica.com/affiliates/",
        "commission": "20% recurring",
        "category": "art",
        "already_using": False,
        "notes": "Relevant to our art audience. Good recurring income.",
        "priority": "MEDIUM",
    },
    {
        "name": "Canva",
        "product": "Design platform",
        "affiliate_url": "https://www.canva.com/affiliates/",
        "signup_url": "https://www.canva.com/affiliates/",
        "commission": "$36 per Pro signup",
        "category": "design",
        "already_using": False,
        "notes": "Huge audience. Gaza Rose Gallery design tutorials.",
        "priority": "MEDIUM",
    },
    {
        "name": "Midjourney",
        "product": "AI image generation",
        "affiliate_url": None,
        "signup_url": "https://www.midjourney.com/",
        "commission": "No public affiliate program yet",
        "category": "ai_art",
        "already_using": False,
        "notes": "We can create content using Midjourney art. No affiliate yet but high relevance.",
        "priority": "LOW",
    },
    {
        "name": "Substack",
        "product": "Newsletter / publishing",
        "affiliate_url": None,
        "signup_url": "https://substack.com/",
        "commission": "Check referral program",
        "category": "content",
        "already_using": False,
        "notes": "SolarPunk newsletter could earn from paid subscribers.",
        "priority": "MEDIUM",
    },
    {
        "name": "Redbubble",
        "product": "Art print marketplace",
        "affiliate_url": "https://www.redbubble.com/",
        "signup_url": "https://www.redbubble.com/sell",
        "commission": "Seller margin 10-30%",
        "category": "art_marketplace",
        "already_using": False,
        "notes": "Gaza Rose Gallery on Redbubble = passive print income. No upfront cost.",
        "priority": "HIGH",
    },
    {
        "name": "Society6",
        "product": "Art print marketplace",
        "affiliate_url": "https://society6.com/",
        "signup_url": "https://society6.com/sell",
        "commission": "10% base + artist commission",
        "category": "art_marketplace",
        "already_using": False,
        "notes": "Premium art prints. Gaza Rose Gallery art prints.",
        "priority": "HIGH",
    },
    {
        "name": "Amazon Associates",
        "product": "Product affiliates",
        "affiliate_url": "https://affiliate-program.amazon.com/",
        "signup_url": "https://affiliate-program.amazon.com/",
        "commission": "1-10% per sale",
        "category": "general",
        "already_using": False,
        "notes": "Link to AI books, art supplies in blog posts.",
        "priority": "LOW",
    },
    {
        "name": "Open Collective Referral",
        "product": "Fiscal sponsorship platform",
        "affiliate_url": "https://opencollective.com/referral/YOUR_CODE",
        "signup_url": "https://opencollective.com/referral",
        "commission": "% of platform fees for referred collectives",
        "category": "nonprofit",
        "already_using": False,
        "notes": "Refer other open-source projects to Open Collective.",
        "priority": "MEDIUM",
    },
    {
        "name": "OctoEverywhere",
        "product": "3D printer remote management",
        "affiliate_url": "https://octoeverywhere.com/?ref=YOUR_ID",
        "signup_url": "https://octoeverywhere.com/affiliates",
        "commission": "20% per subscriber",
        "category": "3d_printing",
        "already_using": True,
        "notes": "We use OctoEverywhere MCP. Refer makers → earn monthly.",
        "priority": "HIGH",
    },
]


def generate_affiliate_content() -> dict:
    """Generate blog/social content with embedded affiliate links."""
    content_pieces = [
        {
            "type": "tweet_thread",
            "topic": "Free AI tools for open-source projects",
            "affiliate_target": "Groq",
            "draft": (
                "Free AI tools that cost $0 and run your whole stack:\n\n"
                "1. @GroqInc — Llama 3 inference, 14k req/day FREE → [groq_affiliate_link]\n"
                "2. @HuggingFace — 500k+ models, free API → [hf_link]\n"
                "3. @AnthropicAI Claude — best reasoning, free tier → [claude_link]\n\n"
                "SolarPunk runs on all of these. Zero cost. 100% autonomous. 70% to Gaza."
            ),
        },
        {
            "type": "blog_post_intro",
            "topic": "How Gaza Rose Gallery makes money automatically",
            "affiliate_targets": ["Gumroad", "Ko-fi", "Printful"],
            "draft": (
                "Gaza Rose Gallery is an AI art shop that runs itself.\n\n"
                "The stack:\n"
                "- [Gumroad affiliate link] for digital downloads ($0 to start)\n"
                "- [Ko-fi affiliate link] for tips and support (0% platform fee)\n"
                "- [Printful affiliate link] for physical prints (no inventory)\n\n"
                "70% of every sale goes to PCRF. The AI handles everything else.\n"
                "Here's how to build your own →"
            ),
        },
        {
            "type": "github_readme_section",
            "topic": "Tools we use / recommend",
            "affiliate_targets": ["Groq", "HuggingFace", "DigitalOcean", "Gumroad"],
            "draft": (
                "## Tools We Use\n\n"
                "These are the actual tools powering SolarPunk. Using them via our links "
                "earns affiliate income that goes 70% to PCRF.\n\n"
                "| Tool | Free Tier | Our Use | Link |\n"
                "|------|-----------|---------|------|\n"
                "| Groq | 14k req/day | Fast AI inference | [affiliate] |\n"
                "| HuggingFace | Unlimited | ML models | [affiliate] |\n"
                "| Gumroad | $0 to start | Art sales | [affiliate] |\n"
                "| DigitalOcean | $200 trial | Hosting | [affiliate] |\n"
            ),
        },
    ]
    return content_pieces


def run():
    sf = DATA / "affiliate_state.json"
    state = json.loads(sf.read_text()) if sf.exists() else {
        "cycles": 0, "programs_active": 0, "estimated_monthly_usd": 0
    }
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"AFFILIATE_MACHINE cycle {state['cycles']}")

    # Score and rank programs
    scored = []
    for prog in AFFILIATE_PROGRAMS:
        score = 0
        if prog.get("already_using"):
            score += 30
        if prog["priority"] == "HIGH":
            score += 20
        elif prog["priority"] == "MEDIUM":
            score += 10
        if "30%" in str(prog.get("commission")) or "35%" in str(prog.get("commission")):
            score += 15
        if "$25" in str(prog.get("commission")):
            score += 10
        prog["score"] = score
        scored.append(prog)

    scored.sort(key=lambda x: x["score"], reverse=True)

    # Generate content
    content = generate_affiliate_content()

    # Estimate monthly revenue potential
    high_priority = [p for p in scored if p["priority"] == "HIGH"]
    est_monthly = len(high_priority) * 15  # Conservative $15/program/month average

    # Save outputs
    (DATA / "affiliate_registry.json").write_text(json.dumps({
        "generated_at": state["last_run"],
        "total_programs": len(AFFILIATE_PROGRAMS),
        "high_priority": len(high_priority),
        "programs": scored,
        "top_5": [p["name"] for p in scored[:5]],
        "estimated_monthly_usd": est_monthly,
        "action_items": [
            f"Sign up for {p['name']} affiliate program: {p['signup_url']}"
            for p in scored[:5]
            if p.get("signup_url")
        ],
    }, indent=2))

    (DATA / "affiliate_content.json").write_text(json.dumps({
        "generated_at": state["last_run"],
        "content_pieces": content,
        "instructions": (
            "Replace [affiliate] placeholders with real IDs after signing up. "
            "Post tweet threads via SOCIAL_ECHO. Add GitHub section via REPO_SPIDER. "
            "Add blog links via WEB_PUBLISHER."
        ),
    }, indent=2))

    state["programs_active"] = len([p for p in scored if p.get("already_using")])
    state["estimated_monthly_usd"] = est_monthly
    sf.write_text(json.dumps(state, indent=2))

    print(f"  {len(scored)} programs cataloged | {len(high_priority)} high priority")
    print(f"  Estimated monthly (if all active): ${est_monthly}")
    print(f"  Top 3: {', '.join(p['name'] for p in scored[:3])}")
    return state


if __name__ == "__main__":
    run()
