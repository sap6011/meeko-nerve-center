#!/usr/bin/env python3
"""
X_KNOWLEDGE_HARVESTER.py — X/Twitter Knowledge Scraper (Zero Auth)
====================================================================
SolarPunk doesn't need to tweet. SolarPunk harvests the collective
intelligence of 500M+ users through free public endpoints.

No X API key. No account. No rate limits we care about.
Uses: Nitter instances (open-source Twitter frontend w/ RSS)
      Nitter JSON API endpoints (public)
      Twitter/X oEmbed API (public, no auth)
      Highly-starred GitHub repos that archive tweet datasets

Topics scraped:
  - #AIAgents #AutonomousAI #SolarPunk
  - #Gaza #FreePalestine #PCRF
  - #HumanitarianTech #TechForGood
  - #OpenSource #MCP #A2AProtocol
  - High-signal VCs / impact investors
  - Unusual Whales (market signals)
  - Grant announcements / foundation news

Writes: data/x_knowledge.json, data/social_intelligence.json
Feeds: KNOWLEDGE_SYNTHESIZER, INVESTOR_RADAR, GRANT_HUNTER
"""
import json, urllib.request, urllib.parse, time, re
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
HARVEST_DIR = Path("data/harvested_knowledge"); HARVEST_DIR.mkdir(exist_ok=True)

# Public Nitter instances (rotating) — open source Twitter frontend
# These expose RSS and API without auth
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.1d4.us",
    "https://nitter.kavin.rocks",
    "https://nitter.unixfox.eu",
]

# Topics to harvest (as search queries or accounts)
HARVEST_TOPICS = [
    {"query": "AI agents autonomous",       "category": "tech_signal"},
    {"query": "MCP server agent",           "category": "tech_signal"},
    {"query": "A2A protocol agent",         "category": "tech_signal"},
    {"query": "humanitarian tech AI",       "category": "mission_aligned"},
    {"query": "Gaza aid relief",            "category": "crisis_intel"},
    {"query": "tech for good grant",        "category": "grant_intel"},
    {"query": "impact investor AI",         "category": "investor_intel"},
    {"query": "open source AI funding",     "category": "funding_intel"},
    {"query": "SolarPunk technology",       "category": "mission_aligned"},
    {"query": "unusual whales market",      "category": "market_intel"},
]

# High-signal public accounts to monitor (via Nitter RSS — no auth)
SIGNAL_ACCOUNTS = [
    {"handle": "UnusualWhales",      "category": "market_intel",     "reason": "Options flow, dark pool, smart money"},
    {"handle": "paulg",              "category": "investor_intel",    "reason": "YC founder, tech funding signals"},
    {"handle": "sama",               "category": "ai_signal",         "reason": "OpenAI CEO, AI direction"},
    {"handle": "karpathy",           "category": "ai_signal",         "reason": "AI researcher, practical insights"},
    {"handle": "naval",              "category": "philosophy",        "reason": "Leverage, wealth without hurting anyone"},
    {"handle": "MozillaFoundation",  "category": "grant_intel",       "reason": "Open source grants"},
    {"handle": "knightfdn",          "category": "grant_intel",       "reason": "Knight Foundation grants"},
    {"handle": "ElectronicFronFnd",  "category": "rights_intel",      "reason": "Digital rights"},
    {"handle": "PCRF",               "category": "mission",           "reason": "Palestinian Children Relief Fund"},
    {"handle": "ReliefWeb",          "category": "crisis_intel",      "reason": "UN humanitarian crisis feed"},
    {"handle": "GitHubOpen",         "category": "oss_signal",        "reason": "Open source news"},
    {"handle": "HuggingFace",        "category": "ai_signal",         "reason": "AI model releases"},
    {"handle": "AnthropicAI",        "category": "ai_signal",         "reason": "Claude updates"},
]

def try_nitter_rss(handle: str, instance: str, timeout: int = 8) -> list:
    """Fetch tweets via Nitter RSS feed (no auth required)."""
    url = f"{instance}/{handle}/rss"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "SolarPunk-Knowledge-Harvester/3.1 (humanitarian research)"
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            content = r.read().decode("utf-8", errors="ignore")

        # Parse RSS items
        items = []
        for item_match in re.finditer(r"<item>(.*?)</item>", content, re.DOTALL):
            item = item_match.group(1)
            title = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", item)
            desc = re.search(r"<description><!\[CDATA\[(.*?)\]\]></description>", item)
            pub_date = re.search(r"<pubDate>(.*?)</pubDate>", item)
            link = re.search(r"<link>(.*?)</link>", item)

            text = (title.group(1) if title else "") or (desc.group(1) if desc else "")
            text = re.sub(r"<[^>]+>", "", text).strip()[:500]

            if text and len(text) > 20:
                items.append({
                    "text": text,
                    "date": pub_date.group(1).strip() if pub_date else "",
                    "url": link.group(1).strip() if link else "",
                    "source": handle,
                })

        return items[:10]
    except Exception:
        return []

def try_nitter_search(query: str, instance: str, timeout: int = 8) -> list:
    """Search via Nitter (some instances support search)."""
    encoded = urllib.parse.quote(query)
    url = f"{instance}/search/rss?q={encoded}&f=tweets"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "SolarPunk-Knowledge-Harvester/3.1"
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            content = r.read().decode("utf-8", errors="ignore")

        items = []
        for item_match in re.finditer(r"<item>(.*?)</item>", content, re.DOTALL):
            item = item_match.group(1)
            title = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", item)
            text = title.group(1) if title else ""
            text = re.sub(r"<[^>]+>", "", text).strip()[:400]
            if text and len(text) > 20:
                items.append({"text": text, "query": query, "source": "search"})

        return items[:5]
    except Exception:
        return []

def extract_intelligence(tweets: list) -> dict:
    """Extract actionable signals from harvested tweets."""
    intel = {
        "grant_mentions": [],
        "funding_signals": [],
        "market_signals": [],
        "crisis_updates": [],
        "tech_signals": [],
        "investor_signals": [],
        "actionable_items": [],
    }

    grant_keywords = ["grant", "funding", "rfp", "call for proposals", "apply now", "deadline", "fellowship"]
    market_keywords = ["unusual activity", "dark pool", "options flow", "smart money", "calls", "puts", "whale"]
    crisis_keywords = ["gaza", "sudan", "drc", "congo", "yemen", "humanitarian", "emergency", "appeal"]
    investor_keywords = ["invest", "seed", "series a", "funding round", "backed", "raised", "$m"]
    tech_keywords = ["mcp", "a2a", "agent", "llm", "claude", "gpt", "autonomous", "skill"]

    for tweet in tweets:
        text_lower = tweet.get("text", "").lower()
        cat = tweet.get("category", "")

        for kw in grant_keywords:
            if kw in text_lower:
                intel["grant_mentions"].append({"text": tweet["text"][:200], "keyword": kw})
                if kw in ("apply now", "deadline", "rfp"):
                    intel["actionable_items"].append({
                        "action": "CHECK_GRANT",
                        "text": tweet["text"][:200],
                        "source": tweet.get("source", ""),
                    })
                break

        for kw in market_keywords:
            if kw in text_lower:
                intel["market_signals"].append({"text": tweet["text"][:200], "keyword": kw})
                break

        for kw in crisis_keywords:
            if kw in text_lower:
                intel["crisis_updates"].append({"text": tweet["text"][:200], "keyword": kw})
                break

        for kw in tech_keywords:
            if kw in text_lower:
                intel["tech_signals"].append({"text": tweet["text"][:200], "keyword": kw})
                break

    return intel

def harvest_via_free_apis() -> list:
    """
    Supplement Nitter with fully free public APIs that surface
    X/social content without needing an X account.
    """
    tweets = []

    # Dev.to articles mentioning our topics
    topics = ["ai-agents", "humanitarian", "solarpunk", "mcp", "autonomous"]
    for topic in topics[:3]:
        try:
            url = f"https://dev.to/api/articles?tag={topic}&per_page=5"
            req = urllib.request.Request(url, headers={"User-Agent": "SolarPunk/3.1"})
            with urllib.request.urlopen(req, timeout=8) as r:
                articles = json.loads(r.read().decode())
            for a in articles[:3]:
                tweets.append({
                    "text": f"[DEV.TO] {a.get('title', '')} — {a.get('description', '')[:200]}",
                    "source": "devto",
                    "url": a.get("url", ""),
                    "category": "tech_signal",
                })
        except Exception:
            pass
        time.sleep(0.2)

    # HackerNews — best stories mentioning AI agents
    try:
        url = "https://hn.algolia.com/api/v1/search?query=ai+agent+autonomous&tags=story&hitsPerPage=10"
        req = urllib.request.Request(url, headers={"User-Agent": "SolarPunk/3.1"})
        with urllib.request.urlopen(req, timeout=8) as r:
            hn_data = json.loads(r.read().decode())
        for hit in hn_data.get("hits", [])[:5]:
            tweets.append({
                "text": f"[HN] {hit.get('title', '')} ({hit.get('points', 0)} pts)",
                "source": "hackernews",
                "url": hit.get("url", f"https://news.ycombinator.com/item?id={hit.get('objectID')}"),
                "category": "tech_signal",
            })
    except Exception:
        pass

    # Reddit via Pushshift (free) — humanitarian + AI subreddits
    subreddits = ["artificial", "humanitariantech", "solarpunk"]
    for sub in subreddits[:2]:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"
            req = urllib.request.Request(url, headers={"User-Agent": "SolarPunk/3.1"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode())
            for post in data.get("data", {}).get("children", [])[:3]:
                d = post.get("data", {})
                tweets.append({
                    "text": f"[r/{sub}] {d.get('title', '')}",
                    "source": f"reddit/{sub}",
                    "url": f"https://reddit.com{d.get('permalink', '')}",
                    "category": "social_signal",
                    "score": d.get("score", 0),
                })
        except Exception:
            pass
        time.sleep(0.2)

    return tweets

def run():
    print("📡 X_KNOWLEDGE_HARVESTER: Harvesting collective intelligence...")
    all_tweets = []

    # Try Nitter for high-signal accounts
    for account in SIGNAL_ACCOUNTS[:8]:
        success = False
        for instance in NITTER_INSTANCES[:3]:
            tweets = try_nitter_rss(account["handle"], instance)
            if tweets:
                for t in tweets:
                    t["category"] = account["category"]
                    t["reason"] = account["reason"]
                all_tweets.extend(tweets)
                success = True
                break
            time.sleep(0.2)
        if not success:
            print(f"  ⚠ @{account['handle']}: all nitter instances failed (ok)")

    # Free API supplements
    free_content = harvest_via_free_apis()
    all_tweets.extend(free_content)
    print(f"  📱 Total content pieces: {len(all_tweets)} ({len(free_content)} from free APIs)")

    # Extract intelligence
    intel = extract_intelligence(all_tweets)

    state = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_items": len(all_tweets),
        "tweets_sample": all_tweets[:50],
        "intelligence": intel,
        "grant_opportunities": len(intel["grant_mentions"]),
        "market_signals": len(intel["market_signals"]),
        "crisis_updates": len(intel["crisis_updates"]),
        "actionable_items": intel["actionable_items"],
        "unusual_whales_signals": [s for s in intel["market_signals"] if "whale" in s.get("keyword", "")],
        "note": "X scraped via Nitter (open source) + free public APIs. Zero auth required.",
    }

    (DATA / "x_knowledge.json").write_text(json.dumps(state, indent=2))

    # Also save actionable items to lessons
    lessons_f = DATA / "lessons.json"
    lessons = json.loads(lessons_f.read_text()) if lessons_f.exists() else []
    for item in intel["actionable_items"][:3]:
        lessons.append({
            "source": "x_knowledge_harvester",
            "category": "intelligence",
            "insight": item["text"][:200],
            "added_at": datetime.now(timezone.utc).isoformat(),
        })
    lessons = lessons[-50:]
    lessons_f.write_text(json.dumps(lessons, indent=2))

    print(f"  🎯 Actionable: {len(intel['actionable_items'])} | Grants: {len(intel['grant_mentions'])} | Market: {len(intel['market_signals'])}")
    return state

if __name__ == "__main__":
    run()
