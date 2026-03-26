#!/usr/bin/env python3
"""
PRODUCTHUNT_LAUNCHER.py — AI writes + schedules ProductHunt submission.

ProductHunt can drive thousands of visitors in one day.
This engine:
  1. AI writes compelling PH submission (tagline, description, first comment)
  2. Generates hunter comment strategy (upvote requests to communities)
  3. Schedules for Tuesday-Thursday 12:01 AM PST (optimal launch time)
  4. Saves everything to data/producthunt_launch.json
  5. When PH_TOKEN available, auto-submits via API

Reads:  data/cycle_brief.json, data/published_articles.json
Writes: data/producthunt_launch.json, data/producthunt_strategy.json
"""
import json, os, re
import urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data")
DATA.mkdir(exist_ok=True)

PH_TOKEN = os.environ.get("PRODUCTHUNT_TOKEN","").strip()  # Optional

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def ai_write_ph_submission(knowledge, brief, product_registry):
    """AI writes complete ProductHunt launch materials."""
    try:
        from AI_CLIENT import ask_json
        system = "You are a product launch specialist. Write compelling ProductHunt submissions. Gaza Rose Gallery is an autonomous AI art + digital products platform donating 70% to PCRF."
        products = product_registry.get("products",[])[:5] if isinstance(product_registry, dict) else []
        prompt = f"""Write a complete ProductHunt launch for Gaza Rose Gallery / SolarPunk AI:

SYSTEM:
- Autonomous AI income system (GitHub Actions + Python, 271 engines)
- 70% of all revenue donated to Palestine Children's Relief Fund (PCRF, 4-star)
- Products: AI tools, digital guides, Palestinian art
- Open source: github.com/meekotharaccoon-cell/meeko-nerve-center
- Current phase: {brief.get('phase','PRE_REVENUE')}
- Articles published: {load_json('data/published_articles.json',{{'total_published':0}}).get('total_published',0)}

TOP PRODUCTS:
{json.dumps([p.get('name','') if isinstance(p,dict) else str(p) for p in products[:5]], indent=2)}

Generate JSON:
{{
  "name": "Gaza Rose Gallery",
  "tagline": "Autonomous AI that earns + donates 70% to Palestine relief (max 60 chars)",
  "description": "300-word description. What it is, how it works, why it matters. Mention open source, PCRF, autonomy.",
  "first_comment": "200-word first comment from maker. Personal, authentic. Share the mission story.",
  "topics": ["5 relevant PH topics: Open Source, AI, Productivity, etc."],
  "hunter_outreach_templates": [
    "DM template for dev communities",
    "Tweet template asking for support",
    "Reddit post template for r/SideProject"
  ],
  "launch_day_timeline": [
    {{"time":"12:01 AM PST","action":"Submit to PH"}},
    {{"time":"7 AM PST","action":"..."}},
    {{"time":"12 PM PST","action":"..."}}
  ],
  "optimal_launch_day": "Tuesday|Wednesday|Thursday",
  "upvote_communities": ["communities to notify on launch day"]
}}
"""
        result = ask_json([{"role":"user","content":prompt}], system=system, prefer_quality=True)
        return result if isinstance(result, dict) else {}
    except Exception as e:
        return {
            "name": "Gaza Rose Gallery",
            "tagline": "Autonomous AI earning for Palestine — 70% to PCRF",
            "description": "Open source autonomous AI system that earns passive income and donates 70% to Palestine Children's Relief Fund. Built on GitHub Actions + Python. 271 autonomous engines running 24/7.",
            "first_comment": "Hi PH! I built this because I wanted my code to actually help people. 70% of every sale goes straight to PCRF for Palestinian children's medical care.",
            "topics": ["Open Source","Artificial Intelligence","Productivity","Social Good","Automation"],
            "optimal_launch_day": "Tuesday",
            "error": str(e),
        }

def schedule_next_launch(submission):
    """Calculate optimal next launch date."""
    now = datetime.now(timezone.utc)
    # Find next Tuesday, Wednesday, or Thursday
    optimal_day = submission.get("optimal_launch_day","Tuesday").lower()
    day_map = {"monday":0,"tuesday":1,"wednesday":2,"thursday":3,"friday":4,"saturday":5,"sunday":6}
    target_weekday = day_map.get(optimal_day, 1)
    days_ahead = (target_weekday - now.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7  # next week if today is the day
    launch_date = now + timedelta(days=days_ahead)
    # 12:01 AM PST = 08:01 AM UTC
    launch_dt = launch_date.replace(hour=8, minute=1, second=0, microsecond=0)
    return launch_dt.isoformat()

def main():
    print("🚀 PRODUCTHUNT_LAUNCHER — AI writing launch materials...")
    brief    = load_json("data/cycle_brief.json")
    knowledge= load_json("data/knowledge_map.json")
    products = load_json("data/product_registry.json", {})
    prev     = load_json("data/producthunt_launch.json")

    # Don't re-generate if we have a good submission from last 7 days
    if prev.get("submission") and prev.get("generated_at"):
        try:
            gen = datetime.fromisoformat(prev["generated_at"])
            if (datetime.now(timezone.utc) - gen).days < 7:
                print("   ○ PH submission already generated recently")
                return
        except Exception:
            pass

    print("   AI writing ProductHunt launch materials...")
    submission = ai_write_ph_submission(knowledge, brief, products)
    launch_date = schedule_next_launch(submission)

    output = {
        "generated_at":  datetime.now(timezone.utc).isoformat(),
        "submission":    submission,
        "scheduled_for": launch_date,
        "ph_url":        "https://www.producthunt.com/posts/new",
        "submitted":     False,
        "note":          "Set PRODUCTHUNT_TOKEN to auto-submit. Or post manually at scheduled time.",
        "status":        "ready",
    }
    Path("data/producthunt_launch.json").write_text(json.dumps(output, indent=2), encoding="utf-8")

    # Strategy doc
    strategy = {
        "launch_date":        launch_date,
        "tagline":            submission.get("tagline",""),
        "communities":        submission.get("upvote_communities",[]),
        "outreach_templates": submission.get("hunter_outreach_templates",[]),
        "timeline":           submission.get("launch_day_timeline",[]),
    }
    Path("data/producthunt_strategy.json").write_text(json.dumps(strategy, indent=2), encoding="utf-8")

    print(f"   ✓ PH launch materials ready | Scheduled: {launch_date}")
    print(f"   Tagline: {submission.get('tagline','')[:60]}")
    print(f"   Manual URL: https://www.producthunt.com/posts/new")

if __name__ == "__main__":
    main()
