#!/usr/bin/env python3
"""
ARXIV_HARVESTER.py — Free Academic Knowledge from arXiv
========================================================
arXiv has 2M+ papers. Zero auth required. Free forever.
SolarPunk harvests cutting-edge AI agent research here.

Topics:
  - Multi-agent systems
  - Autonomous AI agents
  - Humanitarian AI applications
  - AI for social good
  - A2A protocols
  - Knowledge synthesis

Writes: data/arxiv_harvest.json
Feeds: KNOWLEDGE_SYNTHESIZER
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime
import time

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
HARVEST_FILE = os.path.join(DATA_DIR, "arxiv_harvest.json")

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"

# Search queries — no auth required, 100% free
SEARCH_QUERIES = [
    {
        "name": "multi_agent_autonomous",
        "query": "multi-agent autonomous AI systems",
        "max_results": 10,
    },
    {
        "name": "humanitarian_ai",
        "query": "humanitarian AI applications aid",
        "max_results": 10,
    },
    {
        "name": "knowledge_graph_agents",
        "query": "knowledge graph autonomous agents",
        "max_results": 10,
    },
    {
        "name": "ai_for_good",
        "query": "artificial intelligence social good crisis response",
        "max_results": 10,
    },
    {
        "name": "a2a_protocols",
        "query": "agent to agent communication protocol AI",
        "max_results": 8,
    },
    {
        "name": "self_improving_ai",
        "query": "self-improving autonomous AI agent architecture",
        "max_results": 8,
    },
]


def fetch_papers(query: str, max_results: int = 10) -> list[dict]:
    """Fetch papers from arXiv for a given query. No auth required."""
    params = urllib.parse.urlencode(
        {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    url = f"{ARXIV_API}?{params}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "SolarPunk-ArXiv-Harvester/1.0 (humanitarian AI research)"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_data = resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        print(f"  [arXiv] Network error: {e}")
        return []
    except Exception as e:
        print(f"  [arXiv] Error fetching '{query}': {e}")
        return []

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"  [arXiv] XML parse error: {e}")
        return []

    papers = []
    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        def _text(tag):
            el = entry.find(f"{{{ATOM_NS}}}{tag}")
            return el.text.strip() if el is not None and el.text else ""

        title = _text("title").replace("\n", " ").replace("  ", " ")
        abstract = _text("summary").replace("\n", " ").replace("  ", " ")
        published = _text("published")

        authors = []
        for author in entry.findall(f"{{{ATOM_NS}}}author"):
            name_el = author.find(f"{{{ATOM_NS}}}name")
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        link = ""
        for lnk in entry.findall(f"{{{ATOM_NS}}}link"):
            if lnk.get("rel") == "alternate" or lnk.get("type") == "text/html":
                link = lnk.get("href", "")
                break
        if not link:
            id_el = entry.find(f"{{{ATOM_NS}}}id")
            if id_el is not None and id_el.text:
                link = id_el.text.strip()

        if title:
            papers.append(
                {
                    "title": title,
                    "abstract": abstract[:500] + ("..." if len(abstract) > 500 else ""),
                    "authors": authors[:5],
                    "link": link,
                    "published": published,
                    "query": query,
                }
            )

    return papers


def run():
    """Main entry — harvest all query topics, deduplicate, write state."""
    os.makedirs(DATA_DIR, exist_ok=True)

    print("[ARXIV_HARVESTER] Starting — no API key required")
    print(f"  Source: {ARXIV_API}")
    print(f"  Topics: {len(SEARCH_QUERIES)}")

    all_papers = []
    seen_titles = set()
    results_by_topic = {}

    for topic in SEARCH_QUERIES:
        name = topic["name"]
        query = topic["query"]
        max_r = topic["max_results"]

        print(f"  Fetching: {name} ({max_r} papers)...")
        papers = fetch_papers(query, max_r)

        new_papers = []
        for p in papers:
            if p["title"] not in seen_titles:
                seen_titles.add(p["title"])
                all_papers.append(p)
                new_papers.append(p)

        results_by_topic[name] = {
            "query": query,
            "fetched": len(papers),
            "new_unique": len(new_papers),
        }
        print(f"    Got {len(papers)} papers, {len(new_papers)} new unique")

        # Be polite to arXiv — rate limit to 1 req/sec
        time.sleep(1)

    # Extract key insights for the knowledge synthesizer
    key_insights = []
    for paper in all_papers[:20]:
        if paper["abstract"]:
            key_insights.append(
                {
                    "title": paper["title"],
                    "insight": paper["abstract"][:200],
                    "link": paper["link"],
                    "topic": paper["query"],
                }
            )

    harvest = {
        "engine": "ARXIV_HARVESTER",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_papers": len(all_papers),
        "topics_searched": len(SEARCH_QUERIES),
        "results_by_topic": results_by_topic,
        "papers": all_papers,
        "key_insights_for_synthesizer": key_insights,
        "next_run": "Every 24 hours recommended",
        "feeds_into": ["KNOWLEDGE_SYNTHESIZER", "GROQ_ENGINE (summarization)"],
        "why_arxiv": [
            "2M+ papers — cutting edge AI research",
            "Zero auth required — always free",
            "New AI agent papers daily",
            "Informs SolarPunk's own architecture improvements",
            "Humanitarian AI research directly applicable to the mission",
        ],
        "solarpunk_mission": "99% to crisis zones / 1% infrastructure",
    }

    with open(HARVEST_FILE, "w") as f:
        json.dump(harvest, f, indent=2)

    print(f"[ARXIV_HARVESTER] Harvested {len(all_papers)} unique papers")
    print(f"[ARXIV_HARVESTER] Written to {HARVEST_FILE}")

    return harvest


if __name__ == "__main__":
    run()
