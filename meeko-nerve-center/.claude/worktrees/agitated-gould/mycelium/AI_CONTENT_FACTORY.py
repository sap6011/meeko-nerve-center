#!/usr/bin/env python3
"""
AI_CONTENT_FACTORY.py — Generates 10+ pieces of content per cycle using AI.

Creates:
  - Substack post drafts (long-form, thoughtful)
  - Tweet threads (5-tweet story arcs)
  - LinkedIn posts (professional + impact)
  - YouTube script outlines (3-5 min videos)
  - Product launch copy (for each pending product)
  - Email sequences (welcome, nurture, offer)

All generated content is saved to data/content_factory/ and picked up by
AUTONOMOUS_PUBLISHER, SOCIAL_BRAIN, NEWSLETTER_AUTOMATOR automatically.

Reads:  data/cycle_brief.json, data/optimization_queue.json, data/seo_recommendations.json
Writes: data/content_factory/<type>_<date>_<n>.md, data/content_factory_state.json
"""
import json, os, re
from pathlib import Path
from datetime import datetime, timezone

DATA    = Path("data")
FACTORY = DATA / "content_factory"
DATA.mkdir(exist_ok=True)
FACTORY.mkdir(exist_ok=True)

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def ai_create_content(content_type, topic, context):
    try:
        from AI_CLIENT import ask
        system = "You are a content factory AI for Gaza Rose Gallery. Create authentic, mission-driven content. 70% of revenue to PCRF. Never salesy. Always valuable."
        prompts = {
            "substack": f"Write a compelling Substack newsletter post about: {topic}\n\nContext: {context}\n\nFormat: catchy title, personal hook, 3 main points, call to action. 500-700 words.",
            "thread": f"Write a 5-tweet thread about: {topic}\n\nContext: {context}\n\nFormat: Tweet 1 (hook), Tweets 2-4 (insights/story), Tweet 5 (CTA). Each tweet max 270 chars. Separate with ---",
            "linkedin": f"Write a LinkedIn post about: {topic}\n\nContext: {context}\n\nFormat: bold first line, 3-4 short paragraphs, hashtags at end. Professional but human. Max 600 chars.",
            "youtube_script": f"Write a YouTube script outline for a 3-5 minute video about: {topic}\n\nContext: {context}\n\nFormat: Hook (15s), Intro (30s), Main content (3 sections x 45s), CTA (30s). Include specific talking points.",
            "email_sequence": f"Write a 3-email welcome sequence for Gaza Rose Gallery subscribers.\n\nContext: {context}\n\nEmail 1: Welcome + mission (immediate). Email 2: Best content (day 3). Email 3: First offer (day 7). Each email: subject line + body.",
            "product_copy": f"Write compelling product launch copy for this product: {topic}\n\nContext: {context}\n\nInclude: email announcement, social post, product description (for Gumroad), 3 benefits bullets.",
        }
        prompt = prompts.get(content_type, prompts["substack"])
        result = ask([{"role":"user","content":prompt}], max_tokens=1000, system=system, prefer_quality=True)
        return result.strip() if result else ""
    except Exception as e:
        return f"# Content Offline\n\n{e}"

def get_topics(brief, seo_recs, opt_queue):
    """Build topic list from cycle data."""
    topics = []

    # From SEO content gaps (highest opportunity)
    for gap in seo_recs.get("gaps",[])[:3]:
        topics.append({"topic": gap, "type": "substack"})

    # From optimization queue recommendations
    for rec in opt_queue.get("content_recommendations",[])[:3]:
        topics.append({"topic": rec, "type": "thread"})

    # Phase-based topics
    phase = brief.get("phase","PRE_REVENUE")
    focus = brief.get("focus_this_cycle","")
    if focus:
        topics.append({"topic": focus, "type": "linkedin"})
        topics.append({"topic": f"How we built: {focus}", "type": "youtube_script"})

    # Always include: Gaza Rose Gallery mission story
    topics.append({"topic": "Gaza Rose Gallery: AI building income for Palestinian children", "type": "substack"})
    topics.append({"topic": "SolarPunk AI income system — what happened this week", "type": "email_sequence"})

    return topics[:8]  # max 8 per cycle

def main():
    print("🏭 AI_CONTENT_FACTORY — generating content library...")

    brief    = load_json("data/cycle_brief.json")
    seo_recs = load_json("data/seo_recommendations.json")
    opt_queue= load_json("data/optimization_queue.json")
    prev     = load_json("data/content_factory_state.json", {"pieces": 0, "files": []})

    context = f"""
Phase: {brief.get('phase','PRE_REVENUE')}
Revenue: ${brief.get('revenue_usd',0):.2f} raised | 70% to PCRF
Health: {brief.get('health_score',0)}/100
Focus: {brief.get('focus_this_cycle','')}
Top actions: {json.dumps(brief.get('top_actions',[])[:3])}
""".strip()

    topics  = get_topics(brief, seo_recs, opt_queue)
    today   = datetime.now(timezone.utc).strftime("%Y%m%d")
    created = []

    for i, item in enumerate(topics):
        topic   = item["topic"]
        ctype   = item["type"]
        print(f"   Creating [{ctype}]: {topic[:60]}...")

        content = ai_create_content(ctype, topic, context)
        if not content or len(content) < 80:
            print(f"   ⚠ Empty content for {topic[:40]}")
            continue

        # Save to file
        safe_topic = re.sub(r'[^a-z0-9]+', '_', topic.lower())[:30]
        filename   = f"{ctype}_{today}_{i:02d}_{safe_topic}.md"
        filepath   = FACTORY / filename
        filepath.write_text(f"---\ntype: {ctype}\ntopic: {topic}\ncreated: {datetime.now(timezone.utc).isoformat()}\n---\n\n{content}", encoding="utf-8")
        created.append({"file": filename, "type": ctype, "topic": topic, "chars": len(content)})
        print(f"   ✓ {filename} ({len(content)} chars)")

    total_pieces = prev.get("pieces",0) + len(created)
    all_files    = created + prev.get("files",[])

    output = {
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "cycle_pieces":    len(created),
        "total_pieces":    total_pieces,
        "factory_dir":     str(FACTORY),
        "this_cycle":      created,
        "files":           all_files[:200],
        "status":          "ok",
    }
    Path("data/content_factory_state.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"   {len(created)} content pieces created | {total_pieces} total in factory")

if __name__ == "__main__":
    main()
