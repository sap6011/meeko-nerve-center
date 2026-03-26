#!/usr/bin/env python3
"""
FREE_API_CONNECTOR.py — Zero-Auth API Live Connector
=====================================================
Actually CALLS all the free APIs that need zero authentication.
Harvests live data from: arXiv, ReliefWeb, OpenAlex, HN, Reddit,
DuckDuckGo, Wikipedia, Met Museum, Open Library, Nominatim,
and more — then feeds that live intelligence into the SolarPunk
knowledge base and revenue engines.

This is the engine that makes SECRET_BOOTSTRAP's "zero auth"
APIs actually DO things, not just be catalogued.

Outputs: free_api_harvest.json, new harvested_knowledge/ files
Feeds: KNOWLEDGE_SYNTHESIZER, NEWS_HARVESTER, GRANT_HUNTER
"""
import json, os, time
import urllib.request, urllib.error, urllib.parse
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data"); DATA.mkdir(exist_ok=True)
HARVESTED = Path("data/harvested_knowledge"); HARVESTED.mkdir(exist_ok=True)

def safe_get(url: str, label: str, timeout: int = 10) -> dict | list | None:
    """Fetch a URL with error handling."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "SolarPunk-FreeAPIConnector/1.0 (github.com/meekoenergy/meeko-nerve-center)",
                "Accept": "application/json, text/plain, */*",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()
            if "json" in content_type or raw.strip().startswith(b"{") or raw.strip().startswith(b"["):
                return json.loads(raw)
            return {"text": raw.decode("utf-8", errors="ignore")[:2000]}
    except Exception as e:
        return {"error": str(e)[:80], "url": url}


def fetch_arxiv_papers(query: str, max_results: int = 5) -> list:
    """Fetch papers from arXiv API (completely free, no auth)."""
    encoded = urllib.parse.quote(query)
    url = f"https://export.arxiv.org/api/query?search_query=all:{encoded}&start=0&max_results={max_results}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SolarPunk/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml = resp.read().decode("utf-8", errors="ignore")
        # Parse titles and summaries from XML
        import re
        titles = re.findall(r"<title>(.*?)</title>", xml, re.DOTALL)
        summaries = re.findall(r"<summary>(.*?)</summary>", xml, re.DOTALL)
        links = re.findall(r'href="(https://arxiv\.org/abs/[^"]+)"', xml)
        papers = []
        for i, (title, summary) in enumerate(zip(titles[1:], summaries)):  # Skip feed title
            papers.append({
                "title": title.strip(),
                "summary": summary.strip()[:300],
                "url": links[i] if i < len(links) else "",
            })
        return papers[:max_results]
    except Exception as e:
        return [{"error": str(e)}]


def fetch_reliefweb(country: str = "PSE", limit: int = 5) -> list:
    """Fetch humanitarian reports from ReliefWeb (UN, free, no auth)."""
    url = (
        f"https://api.reliefweb.int/v1/reports?"
        f"appname=solarpunk&filter[field]=country.iso3&filter[value]={country}"
        f"&limit={limit}&fields[include][]=title&fields[include][]=body-html"
    )
    data = safe_get(url, "reliefweb")
    if isinstance(data, dict) and "data" in data:
        return [
            {"title": item.get("fields", {}).get("title", ""), "id": item.get("id", "")}
            for item in data["data"]
        ]
    return []


def fetch_openalex(query: str, limit: int = 5) -> list:
    """Fetch academic works from OpenAlex (open knowledge graph, free)."""
    encoded = urllib.parse.quote(query)
    url = f"https://api.openalex.org/works?search={encoded}&per-page={limit}&select=title,abstract_inverted_index,cited_by_count,publication_year"
    data = safe_get(url, "openalex")
    if isinstance(data, dict) and "results" in data:
        results = []
        for work in data["results"]:
            title = work.get("title", "")
            cited = work.get("cited_by_count", 0)
            year = work.get("publication_year", "")
            results.append({"title": title, "cited_by": cited, "year": year})
        return results
    return []


def fetch_hackernews_top(n: int = 10) -> list:
    """Fetch top HN stories (free, no auth)."""
    top_ids = safe_get("https://hacker-news.firebaseio.com/v0/topstories.json", "hn_top")
    if not isinstance(top_ids, list):
        return []
    stories = []
    for story_id in top_ids[:n]:
        story = safe_get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", f"hn_{story_id}")
        if isinstance(story, dict) and story.get("title"):
            stories.append({
                "title": story.get("title", ""),
                "url": story.get("url", ""),
                "score": story.get("score", 0),
                "type": story.get("type", ""),
            })
        time.sleep(0.1)
    return stories


def fetch_metmuseum_art() -> list:
    """Fetch public domain art from Met Museum (free, no auth)."""
    # Search for Palestinian/Middle Eastern art
    search_url = "https://collectionapi.metmuseum.org/public/collection/v1/search?q=Islamic+art&hasImages=true&isPublicDomain=true"
    search_data = safe_get(search_url, "met_search")
    if not isinstance(search_data, dict) or "objectIDs" not in search_data:
        return []
    object_ids = search_data.get("objectIDs", [])[:5]
    artworks = []
    for obj_id in object_ids:
        obj_data = safe_get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{obj_id}", f"met_{obj_id}")
        if isinstance(obj_data, dict) and obj_data.get("title"):
            artworks.append({
                "title": obj_data.get("title", ""),
                "artist": obj_data.get("artistDisplayName", "Unknown"),
                "date": obj_data.get("objectDate", ""),
                "image_url": obj_data.get("primaryImageSmall", ""),
                "department": obj_data.get("department", ""),
                "culture": obj_data.get("culture", ""),
            })
        time.sleep(0.2)
    return artworks


def fetch_devto_articles(tag: str = "ai", per_page: int = 8) -> list:
    """Fetch DEV.to articles (free, no auth needed)."""
    data = safe_get(f"https://dev.to/api/articles?tag={tag}&per_page={per_page}", f"devto_{tag}")
    if not isinstance(data, list):
        return []
    return [
        {
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "reactions": a.get("positive_reactions_count", 0),
            "tags": a.get("tag_list", []),
            "published": a.get("published_at", ""),
        }
        for a in data[:per_page]
    ]


def fetch_semantic_scholar(query: str, limit: int = 5) -> list:
    """Fetch papers from Semantic Scholar (free, no auth)."""
    encoded = urllib.parse.quote(query)
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded}&limit={limit}&fields=title,year,citationCount,abstract"
    data = safe_get(url, "semantic_scholar")
    if isinstance(data, dict) and "data" in data:
        return [
            {
                "title": p.get("title", ""),
                "year": p.get("year", ""),
                "citations": p.get("citationCount", 0),
                "abstract": (p.get("abstract") or "")[:200],
            }
            for p in data["data"]
        ]
    return []


def fetch_coingecko_trending() -> dict:
    """Fetch crypto trending from CoinGecko (free tier, no auth)."""
    coins = safe_get("https://api.coingecko.com/api/v3/search/trending", "coingecko_trending")
    if isinstance(coins, dict) and "coins" in coins:
        return {
            "trending_coins": [
                c.get("item", {}).get("name", "") for c in coins["coins"][:5]
            ]
        }
    return {}


def fetch_nominatim_humanitarian() -> dict:
    """Fetch geo data for Gaza from Nominatim/OpenStreetMap (free, no auth)."""
    data = safe_get(
        "https://nominatim.openstreetmap.org/search?q=Gaza+Strip&format=json&limit=1&addressdetails=1",
        "nominatim_gaza"
    )
    if isinstance(data, list) and data:
        g = data[0]
        return {
            "name": g.get("display_name", "Gaza"),
            "lat": g.get("lat", ""),
            "lon": g.get("lon", ""),
            "type": g.get("type", ""),
        }
    return {}


def run():
    sf = DATA / "free_api_connector_state.json"
    state = json.loads(sf.read_text()) if sf.exists() else {"cycles": 0, "items_harvested": 0}
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"FREE_API_CONNECTOR cycle {state['cycles']}")

    harvest = {
        "generated_at": state["last_run"],
        "sources": {},
    }

    # arXiv — autonomous AI papers
    print("  Fetching: arXiv (autonomous AI agents)")
    papers = fetch_arxiv_papers("autonomous ai agent revenue humanitarian", max_results=5)
    harvest["sources"]["arxiv_ai_agents"] = papers
    state["items_harvested"] = state.get("items_harvested", 0) + len(papers)
    time.sleep(1)

    # ReliefWeb — Gaza humanitarian reports
    print("  Fetching: ReliefWeb (Gaza humanitarian data)")
    relief = fetch_reliefweb("PSE", limit=5)
    harvest["sources"]["reliefweb_gaza"] = relief
    state["items_harvested"] += len(relief)
    time.sleep(1)

    # HackerNews — tech trends
    print("  Fetching: HackerNews (top stories)")
    hn_stories = fetch_hackernews_top(8)
    harvest["sources"]["hackernews_top"] = hn_stories
    state["items_harvested"] += len(hn_stories)
    time.sleep(0.5)

    # DEV.to — AI articles
    print("  Fetching: DEV.to (AI articles)")
    devto_ai = fetch_devto_articles("ai", per_page=6)
    harvest["sources"]["devto_ai"] = devto_ai
    devto_oss = fetch_devto_articles("opensource", per_page=4)
    harvest["sources"]["devto_opensource"] = devto_oss
    state["items_harvested"] += len(devto_ai) + len(devto_oss)
    time.sleep(0.5)

    # Semantic Scholar — AI research
    print("  Fetching: Semantic Scholar (AI autonomous agents)")
    ss_papers = fetch_semantic_scholar("autonomous ai agent self-improving", limit=5)
    harvest["sources"]["semantic_scholar_ai"] = ss_papers
    state["items_harvested"] += len(ss_papers)
    time.sleep(1)

    # Met Museum — public domain art for Gaza Rose Gallery
    print("  Fetching: Met Museum (public domain Islamic art)")
    artworks = fetch_metmuseum_art()
    harvest["sources"]["met_museum_art"] = artworks
    state["items_harvested"] += len(artworks)
    time.sleep(0.5)

    # OpenAlex — academic papers on humanitarian AI
    print("  Fetching: OpenAlex (humanitarian AI research)")
    oa_papers = fetch_openalex("humanitarian artificial intelligence automation", limit=5)
    harvest["sources"]["openalex_humanitarian"] = oa_papers
    state["items_harvested"] += len(oa_papers)
    time.sleep(0.5)

    # CoinGecko — crypto trends (for CRYPTO_WATCHER)
    print("  Fetching: CoinGecko (trending)")
    crypto = fetch_coingecko_trending()
    harvest["sources"]["coingecko"] = crypto

    # Nominatim — Gaza geo data
    print("  Fetching: Nominatim (Gaza geo)")
    geo = fetch_nominatim_humanitarian()
    harvest["sources"]["nominatim_gaza"] = geo

    # Write main output
    (DATA / "free_api_harvest.json").write_text(json.dumps(harvest, indent=2))

    # Write individual harvested files for knowledge pipeline
    for source_name, source_data in harvest["sources"].items():
        if source_data:
            fname = HARVESTED / f"free_api_{source_name}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
            fname.write_text(json.dumps({
                "source": source_name,
                "harvested_at": state["last_run"],
                "data": source_data,
            }, indent=2))

    # Extract lessons for lessons.json
    new_lessons = []
    # From arXiv papers
    for paper in papers[:3]:
        if paper.get("title") and not paper.get("error"):
            new_lessons.append({
                "source": "arxiv",
                "category": "ai_research",
                "insight": f"Research: {paper['title'][:100]}",
                "url": paper.get("url", ""),
            })
    # From HN
    for story in hn_stories[:3]:
        if story.get("score", 0) > 100:
            new_lessons.append({
                "source": "hackernews",
                "category": "tech_trends",
                "insight": f"Trending ({story['score']} pts): {story['title'][:100]}",
                "url": story.get("url", ""),
            })
    # From ReliefWeb
    for report in relief[:2]:
        if report.get("title"):
            new_lessons.append({
                "source": "reliefweb",
                "category": "humanitarian",
                "insight": f"UN Report: {report['title'][:100]}",
            })

    if new_lessons:
        lessons_file = DATA / "lessons.json"
        existing = json.loads(lessons_file.read_text()) if lessons_file.exists() else []
        existing_insights = {l.get("insight", "")[:80] for l in existing}
        new_unique = [l for l in new_lessons if l.get("insight", "")[:80] not in existing_insights]
        combined = (existing + new_unique)[-50:]
        lessons_file.write_text(json.dumps(combined, indent=2))
        print(f"  Added {len(new_unique)} lessons to lessons.json")

    # Save state
    sf.write_text(json.dumps(state, indent=2))
    total = sum(len(v) if isinstance(v, list) else 1 for v in harvest["sources"].values())
    print(f"  Harvested {total} items from {len(harvest['sources'])} sources")
    print(f"  Total items harvested all time: {state['items_harvested']}")
    return state


if __name__ == "__main__":
    run()
