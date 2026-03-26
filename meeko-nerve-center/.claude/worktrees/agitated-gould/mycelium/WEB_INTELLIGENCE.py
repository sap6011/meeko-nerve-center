#!/usr/bin/env python3
"""
WEB_INTELLIGENCE.py — Real-time web intelligence from HN, GitHub Trending, Reddit.

Scrapes (no API keys needed — all public):
  1. HackerNews API (official) — top stories, Ask HN, Show HN
  2. GitHub Trending (HTML scrape) — trending repos in Python/AI
  3. Reddit (JSON API) — r/artificial, r/MachineLearning, r/SideHustle posts
  4. Dev.to public feed — trending AI articles
  5. AI news from multiple sources

AI synthesizes signals into:
  - Trending topics to write about NOW
  - Viral hooks to use in social posts
  - Products/tools to mention/review
  - Market gaps to exploit

Writes: data/web_intelligence.json, data/trending_topics.json
"""
import json, os, re, html
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def fetch_url(url, timeout=15, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "SolarPunkAI/1.0 (+https://github.com/meekotharaccoon-cell/meeko-nerve-center)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return ""

def fetch_json(url, timeout=15):
    content = fetch_url(url, timeout)
    if not content: return None
    try:
        return json.loads(content)
    except Exception:
        return None

def get_hackernews_top():
    """Fetch top HN stories."""
    story_ids = fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not story_ids: return []
    stories = []
    for sid in story_ids[:15]:
        item = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
        if item and item.get("title"):
            stories.append({
                "title":  item.get("title",""),
                "url":    item.get("url",""),
                "score":  item.get("score",0),
                "type":   item.get("type",""),
                "source": "hackernews",
            })
    return sorted(stories, key=lambda x: x["score"], reverse=True)[:10]

def get_hn_show():
    """Fetch Show HN posts — people launching products."""
    ids = fetch_json("https://hacker-news.firebaseio.com/v0/showstories.json")
    if not ids: return []
    items = []
    for sid in ids[:10]:
        item = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
        if item and item.get("title"):
            items.append({"title":item.get("title",""),"url":item.get("url",""),"score":item.get("score",0),"source":"hn_show"})
    return items[:5]

def get_reddit_signals(subreddits=None):
    """Fetch Reddit hot posts from relevant subreddits."""
    if subreddits is None:
        subreddits = ["artificial","MachineLearning","SideProject","SideHustle","opensource"]
    posts = []
    for sub in subreddits[:4]:
        data = fetch_json(f"https://www.reddit.com/r/{sub}/hot.json?limit=5",
                         headers={"User-Agent":"SolarPunkAI/1.0"})
        if not data: continue
        for post in data.get("data",{}).get("children",[]):
            p = post.get("data",{})
            posts.append({
                "title":      p.get("title",""),
                "url":        f"https://reddit.com{p.get('permalink','')}",
                "score":      p.get("score",0),
                "comments":   p.get("num_comments",0),
                "subreddit":  sub,
                "source":     "reddit",
            })
    return sorted(posts, key=lambda x: x["score"], reverse=True)[:10]

def get_devto_trending():
    """Fetch trending Dev.to articles."""
    data = fetch_json("https://dev.to/api/articles?top=7&per_page=10")
    if not data: return []
    articles = []
    for a in data[:10]:
        articles.append({
            "title":      a.get("title",""),
            "url":        a.get("url",""),
            "reactions":  a.get("positive_reactions_count",0),
            "tags":       a.get("tag_list",[])[:4],
            "source":     "devto",
        })
    return articles

def get_github_trending():
    """Scrape GitHub trending Python/AI repos."""
    html_content = fetch_url("https://github.com/trending/python?since=daily&spoken_language_code=en")
    if not html_content: return []
    repos = []
    # Extract repo names from trending page
    matches = re.findall(r'href="/([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+)"[^>]*>\s*\n?\s*<span[^>]*>\s*\n?\s*<span[^>]*>([^<]+)<', html_content)
    desc_matches = re.findall(r'<p class="col-9[^"]*"[^>]*>\s*([^<]{10,150})\s*</p>', html_content)
    seen = set()
    for m in matches[:20]:
        repo_path = m[0]
        if repo_path in seen or "/" not in repo_path: continue
        seen.add(repo_path)
        repos.append({"repo": repo_path, "url": f"https://github.com/{repo_path}", "source": "github_trending"})
        if len(repos) >= 8: break
    return repos

def ai_synthesize_intelligence(hn_stories, reddit_posts, devto_articles, github_repos, hn_show):
    """AI synthesizes all signals into actionable intelligence."""
    try:
        from AI_CLIENT import ask_json
        all_titles = (
            [s["title"] for s in hn_stories[:8]] +
            [p["title"] for p in reddit_posts[:6]] +
            [a["title"] for a in devto_articles[:5]] +
            [r["repo"] for r in github_repos[:6]] +
            [s["title"] for s in hn_show[:3]]
        )
        prompt = f"""Analyze these trending signals and identify opportunities for Gaza Rose Gallery / SolarPunk AI:

TRENDING NOW:
{json.dumps(all_titles, indent=2)}

Generate JSON:
{{
  "hot_topics": ["5 trending topics to write content about RIGHT NOW"],
  "viral_hooks": ["5 viral angles/hooks for social posts based on trends"],
  "product_opportunities": ["3 product ideas based on what people want right now"],
  "content_to_publish_today": [
    {{"title":"...", "platform":"devto|substack|twitter", "angle":"...", "why_timely":"..."}}
  ],
  "trending_keywords": ["top 10 keywords trending right now in AI/tech"],
  "competitors_to_study": ["3 GitHub repos or products worth examining"]
}}
"""
        result = ask_json([{"role":"user","content":prompt}])
        return result if isinstance(result, dict) else {}
    except Exception:
        return {
            "hot_topics":   ["AI automation for side income","Open source AI tools","Gaza solidarity tech"],
            "viral_hooks":  ["How I'm building a passive income system to fund Gaza relief"],
            "trending_keywords": ["AI","automation","opensource","Python","LLM","agents","autonomous"],
        }

def main():
    print("🌐 WEB_INTELLIGENCE — scraping real-time signals...")
    hn_stories  = get_hackernews_top()
    hn_show     = get_hn_show()
    reddit_posts= get_reddit_signals()
    devto_arts  = get_devto_trending()
    github_repos= get_github_trending()

    print(f"   HN: {len(hn_stories)} | Show HN: {len(hn_show)} | Reddit: {len(reddit_posts)} | Dev.to: {len(devto_arts)} | GitHub: {len(github_repos)}")

    intelligence = ai_synthesize_intelligence(hn_stories, reddit_posts, devto_arts, github_repos, hn_show)

    output = {
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "raw_signals": {
            "hackernews":    hn_stories,
            "hn_show":       hn_show,
            "reddit":        reddit_posts,
            "devto":         devto_arts,
            "github_trending": github_repos,
        },
        "intelligence":    intelligence,
        "total_signals":   len(hn_stories)+len(reddit_posts)+len(devto_arts)+len(github_repos),
        "status":          "ok",
    }
    Path("data/web_intelligence.json").write_text(json.dumps(output, indent=2), encoding="utf-8")

    # Write focused trending topics for content engines
    Path("data/trending_topics.json").write_text(
        json.dumps({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "hot_topics":   intelligence.get("hot_topics",[]),
            "viral_hooks":  intelligence.get("viral_hooks",[]),
            "keywords":     intelligence.get("trending_keywords",[]),
            "publish_now":  intelligence.get("content_to_publish_today",[]),
        }, indent=2),
        encoding="utf-8"
    )

    print(f"   {len(intelligence.get('hot_topics',[]))} hot topics | {len(intelligence.get('viral_hooks',[]))} viral hooks")
    if intelligence.get("hot_topics"):
        print(f"   Top topic: {intelligence['hot_topics'][0][:70]}")

if __name__ == "__main__":
    main()
