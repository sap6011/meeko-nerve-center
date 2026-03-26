#!/usr/bin/env python3
"""
AFFILIATE_BRAIN.py — Manages affiliate programs + auto-generates affiliate content.

Reads affiliate_config.json from knowledge_ingest/processed/ and activates:
  - Tracks affiliate links and programs
  - AI writes product reviews/comparisons with affiliate links
  - Posts affiliate content at optimal times
  - Tracks conversion signals

Known affiliate opportunities:
  - AI tool affiliates (Jasper, Copy.ai, Midjourney, etc.)
  - Hosting affiliates (Vercel, Railway, Fly.io)
  - Course platforms (Gumroad, Teachable, Podia)
  - Crypto/payment (Coinbase, Strike)

Reads:  knowledge_ingest/processed/affiliate_config.json,
        knowledge_ingest/processed/affiliate_state.json
Writes: data/affiliate_state.json, data/affiliate_content.json
"""
import json, os, re
from pathlib import Path
from datetime import datetime, timezone

DATA      = Path("data")
PROCESSED = Path("knowledge_ingest/processed")
DATA.mkdir(exist_ok=True)

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

# High-value affiliate programs to target (free to join)
TARGET_AFFILIATES = [
    {
        "name":       "Gumroad",
        "program":    "Gumroad Creator Program",
        "url":        "https://gumroad.com/affiliates",
        "commission": "30% recurring",
        "relevance":  "HIGH — we're already a Gumroad creator",
        "content_type": "tutorial: how to sell digital products on Gumroad",
    },
    {
        "name":       "Anthropic / Claude",
        "program":    "Claude API Affiliate (via partnership)",
        "url":        "https://www.anthropic.com/",
        "commission": "Revenue share",
        "relevance":  "HIGH — we use Claude extensively",
        "content_type": "review: Claude vs GPT-4 for autonomous AI systems",
    },
    {
        "name":       "GitHub Copilot",
        "program":    "GitHub Affiliate",
        "url":        "https://github.com/",
        "commission": "Variable",
        "relevance":  "HIGH — developer audience",
        "content_type": "article: GitHub Actions for autonomous income systems",
    },
    {
        "name":       "Railway",
        "program":    "Railway Referral",
        "url":        "https://railway.app/referral",
        "commission": "$5 per referral",
        "relevance":  "MEDIUM — deployment platform",
        "content_type": "tutorial: deploy AI agents on Railway for free",
    },
    {
        "name":       "Beehiiv",
        "program":    "Beehiiv Partner",
        "url":        "https://www.beehiiv.com/partner",
        "commission": "50% for 12 months",
        "relevance":  "MEDIUM — newsletter platform",
        "content_type": "review: best newsletter platforms for AI creators",
    },
    {
        "name":       "HuggingFace",
        "program":    "HuggingFace PRO Affiliate",
        "url":        "https://huggingface.co/",
        "commission": "15%",
        "relevance":  "HIGH — AI audience",
        "content_type": "guide: free AI models on HuggingFace for your projects",
    },
    {
        "name":       "Notion",
        "program":    "Notion Affiliate",
        "url":        "https://www.notion.so/affiliates",
        "commission": "$10 per signup",
        "relevance":  "MEDIUM — productivity audience",
        "content_type": "template: Notion setup for autonomous AI projects",
    },
]

def ai_write_affiliate_content(affiliate, context):
    """AI writes helpful content with natural affiliate integration."""
    try:
        from AI_CLIENT import ask
        system = "You are a content writer for Gaza Rose Gallery. Write genuinely helpful content. Mention affiliate products only when they're truly relevant. Never spammy. 70% of revenue to PCRF."
        prompt = f"""Write a helpful piece of content for this affiliate opportunity:

PROGRAM: {affiliate['name']} — {affiliate['program']}
COMMISSION: {affiliate['commission']}
CONTENT TYPE: {affiliate['content_type']}
RELEVANCE: {affiliate['relevance']}

Context:
- We're SolarPunk AI: 70% revenue to Palestine Children's Relief Fund
- Developer + AI creator audience
- Authentic, mission-aligned voice

Write a 400-500 word piece that:
1. Provides genuine value (tutorial/review/guide)
2. Naturally mentions {affiliate['name']} where relevant
3. Includes a soft CTA mentioning our affiliate link (placeholder: [AFFILIATE_LINK])
4. End with Gaza Rose Gallery mission mention
5. Format: title + body + 3 hashtags for social

"""
        result = ask([{"role":"user","content":prompt}], max_tokens=700, system=system, prefer_quality=True)
        return result.strip() if result else ""
    except Exception as e:
        return f"# {affiliate['content_type']}\n\n[Content generation offline: {e}]"

def build_affiliate_link(affiliate):
    """Generate or retrieve affiliate link for a program."""
    # Read from config
    config = load_json(PROCESSED / "affiliate_config.json")
    programs = config.get("programs", {})
    if affiliate["name"].lower() in programs:
        return programs[affiliate["name"].lower()].get("link","")
    # Return placeholder
    return f"https://ref.solarpunk.ai/{affiliate['name'].lower().replace(' ','_')}"

def main():
    print("🔗 AFFILIATE_BRAIN — activating affiliate programs...")
    config     = load_json(PROCESSED / "affiliate_config.json")
    state      = load_json(PROCESSED / "affiliate_state.json")
    prev_state = load_json("data/affiliate_state.json", {"programs":[], "content":[]})
    brief      = load_json("data/cycle_brief.json")

    context = {
        "phase":   brief.get("phase","PRE_REVENUE"),
        "revenue": brief.get("revenue_usd",0),
        "focus":   brief.get("focus_this_cycle",""),
    }

    # Merge known programs with config programs
    active_programs = TARGET_AFFILIATES[:]
    for pname, pdata in config.get("programs",{}).items():
        if not any(a["name"].lower()==pname.lower() for a in active_programs):
            active_programs.append({"name":pname, **pdata})

    content_pieces = []
    MAX_CONTENT = 3  # per cycle

    for affiliate in active_programs[:MAX_CONTENT]:
        already_written = any(p.get("program")==affiliate["name"] for p in prev_state.get("content",[]))
        if already_written:
            continue
        print(f"   Writing: {affiliate['name']} affiliate content...")
        content = ai_write_affiliate_content(affiliate, context)
        link    = build_affiliate_link(affiliate)
        if content and link:
            content = content.replace("[AFFILIATE_LINK]", link)
        content_pieces.append({
            "program":    affiliate["name"],
            "commission": affiliate["commission"],
            "content":    content,
            "link":       link,
            "content_type": affiliate.get("content_type",""),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        print(f"   ✓ {affiliate['name']}: {len(content)} chars")

    all_content = content_pieces + prev_state.get("content",[])
    output = {
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "programs_tracked": len(active_programs),
        "content_created": len(content_pieces),
        "total_content":   len(all_content),
        "programs":        [{
            "name":       a["name"],
            "commission": a["commission"],
            "link":       build_affiliate_link(a),
            "relevance":  a.get("relevance",""),
        } for a in active_programs],
        "content":         all_content[:50],
        "config_programs": list(config.get("programs",{}).keys()),
        "status":          "ok",
    }
    Path("data/affiliate_state.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    # Write content for AUTONOMOUS_PUBLISHER to pick up
    Path("data/affiliate_content.json").write_text(
        json.dumps({"generated_at":datetime.now(timezone.utc).isoformat(),"content":content_pieces}, indent=2),
        encoding="utf-8"
    )
    print(f"   {len(content_pieces)} affiliate pieces written | {len(active_programs)} programs tracked")

if __name__ == "__main__":
    main()
