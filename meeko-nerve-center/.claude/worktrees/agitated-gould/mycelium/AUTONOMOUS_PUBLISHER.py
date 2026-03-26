#!/usr/bin/env python3
"""
AUTONOMOUS_PUBLISHER.py — AI writes + publishes full articles autonomously.

Pipeline:
  1. Read content_harvest.json for trending topics
  2. AI writes 3 full articles per cycle (devto, medium, newsletter styles)
  3. Auto-publishes to Dev.to (API key: DEV_TO_API_KEY), stores drafts for Medium
  4. Newsletter draft → data/newsletter_draft.md for EMAIL_BRAIN

Reads:  data/content_harvest.json, data/knowledge_map.json, data/cycle_brief.json
Writes: data/published_articles.json, data/newsletter_draft.md
"""
import json, os, re
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

DEVTO_KEY  = (os.environ.get("DEV_TO_API_KEY") or "").strip()
MEDIUM_KEY = os.environ.get("MEDIUM_TOKEN", "").strip()

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def _http_post(url, headers, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def ai_write_article(topic, context, style="devto"):
    try:
        from AI_CLIENT import ask
        style_prompts = {
            "devto":  "Write a technical dev.to article in markdown. Use headers, code examples if relevant. Add tags line at end: tags: ai, opensource, autonomy, solarpunk",
            "medium": "Write a thoughtful Medium essay (600-900 words). Personal, inspiring voice.",
            "newsletter": "Write a friendly email newsletter. Share what this autonomous AI system accomplished. Include CTA for Gaza Rose Gallery.",
        }
        system = "You are a SolarPunk AI content engine. Gaza Rose Gallery donates 70% to PCRF (Palestine Children's Relief Fund). Write authentic, helpful content aligned with humanitarian AI mission."
        prompt = f"""Write a full {style_prompts.get(style, 'article')} on this topic:

TOPIC: {topic}

SYSTEM CONTEXT:
Phase: {context.get('phase','PRE_REVENUE')} | Revenue: ${context.get('revenue',0):.2f} | Health: {context.get('health',0)}/100
Focus: {context.get('focus','')}
Builder insight: {str(context.get('builder_thesis',''))[:300]}

Format:
- First line: # Title
- Full body
- Last paragraph: brief mention of Gaza Rose Gallery and PCRF mission
"""
        result = ask([{"role": "user", "content": prompt}], max_tokens=1400, system=system, prefer_quality=True)
        return result.strip() if result else ""
    except Exception as e:
        return f"# SolarPunk AI Update\n\nSystem writing offline: {e}"

def publish_devto(content):
    if not DEVTO_KEY:
        return {"skipped": "no DEV_TO_API_KEY"}
    lines = content.strip().split("\n")
    title = lines[0].lstrip("# ").strip()
    body  = "\n".join(lines[1:]).strip()
    result = _http_post("https://dev.to/api/articles",
        {"Content-Type": "application/json", "api-key": DEVTO_KEY},
        {"article": {"title": title, "body_markdown": body, "published": True,
                     "tags": ["ai","opensource","autonomy","solarpunk"]}})
    return {"url": result.get("url",""), "id": result.get("id"), "error": result.get("error")}

def pick_topics(harvest, knowledge, brief):
    topics = []
    for s in harvest.get("signals", [])[:4]:
        t = s.get("topic", s.get("title","")) if isinstance(s,dict) else str(s)
        if t: topics.append(t)
    for o in knowledge.get("opportunities",[])[:2]:
        t = o.get("title","") if isinstance(o,dict) else str(o)
        if t: topics.append(t)
    focus = brief.get("focus_this_cycle","")
    if focus: topics.insert(0, f"SolarPunk AI: {focus}")
    if len(topics) < 3:
        topics += [
            "Building Autonomous AI That Funds Gaza Relief",
            "How SolarPunk Tech Creates Passive Income for Humanitarian Causes",
            "Free AI Tools for Social Impact Projects",
        ]
    return topics[:3]

def main():
    print("📝 AUTONOMOUS_PUBLISHER — AI writing + publishing articles...")
    harvest   = load_json("data/content_harvest.json")
    knowledge = load_json("data/knowledge_map.json")
    brief     = load_json("data/cycle_brief.json")
    prev      = load_json("data/published_articles.json", {"articles": []})

    topics  = pick_topics(harvest, knowledge, brief)
    context = {
        "phase":   brief.get("phase","PRE_REVENUE"),
        "focus":   brief.get("focus_this_cycle",""),
        "revenue": brief.get("revenue_usd", 0),
        "health":  brief.get("health_score", 0),
        "builder_thesis": knowledge.get("builder_thesis","")[:300],
        "opportunities":  knowledge.get("opportunities",[])[:2],
    }
    styles  = ["devto","medium","newsletter"]
    results = []

    for i, topic in enumerate(topics):
        if not topic.strip(): continue
        style = styles[i % len(styles)]
        print(f"   Writing [{style}]: {topic[:70]}...")
        content = ai_write_article(topic, context, style)
        if not content or len(content) < 80: continue

        entry = {"topic": topic, "style": style, "written_at": datetime.now(timezone.utc).isoformat(),
                 "preview": content[:200], "full_content": content}

        if style == "devto":
            r = publish_devto(content)
            entry["devto"] = r
            print(f"   {'✓' if r.get('url') else '○'} Dev.to: {r.get('url') or r.get('skipped','queued')}")
        elif style == "medium":
            # Medium requires OAuth; save draft for manual publish or future token
            Path("data/medium_draft.md").write_text(content, encoding="utf-8")
            entry["medium_draft"] = "data/medium_draft.md"
            print(f"   ✓ Medium draft saved → data/medium_draft.md")
        else:
            Path("data/newsletter_draft.md").write_text(content, encoding="utf-8")
            entry["newsletter_draft"] = "data/newsletter_draft.md"
            print(f"   ✓ Newsletter draft → EMAIL_BRAIN will send")

        results.append(entry)

    all_articles = results + prev.get("articles", [])
    output = {
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "cycle_articles":  len(results),
        "total_published": len([a for a in all_articles if a.get("devto",{}).get("url")]),
        "articles":        all_articles[:50],
        "status":          "ok",
    }
    Path("data/published_articles.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"   {len(results)} articles written this cycle | {output['total_published']} total live")

if __name__ == "__main__":
    main()
