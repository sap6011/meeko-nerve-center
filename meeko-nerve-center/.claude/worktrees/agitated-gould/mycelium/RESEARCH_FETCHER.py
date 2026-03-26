#!/usr/bin/env python3
"""
RESEARCH_FETCHER.py — Knowledge Gap Research Engine
════════════════════════════════════════════════════
Reads open gaps from data/knowledge_gaps.json.
Searches the web for each gap using DuckDuckGo (no API key needed).
Parses results, structures them, writes candidates to data/research_candidates.json.
KNOWLEDGE_LOOP then validates and ingests confirmed candidates.

RUNS: called by KNOWLEDGE_LOOP.py each cycle, or standalone:
      python mycelium/RESEARCH_FETCHER.py
      python mycelium/RESEARCH_FETCHER.py --gap geographic.africa
      python mycelium/RESEARCH_FETCHER.py --limit 5
"""

import json
import time
import re
import sys
import urllib.request
import urllib.parse
import urllib.error
import datetime
from pathlib import Path

ROOT            = Path(__file__).resolve().parent.parent
GAPS_FILE       = ROOT / "data" / "knowledge_gaps.json"
CANDIDATES_FILE = ROOT / "data" / "research_candidates.json"
KB_FILE         = ROOT / "data" / "solarpunk_knowledge.json"

# Project type keywords to look for in search results
SOLARPUNK_KEYWORDS = [
    "community solar", "community energy", "indigenous solar", "solar cooperative",
    "community land trust", "food forest", "urban farm", "community garden",
    "worker cooperative", "worker co-op", "mutual aid", "community mesh",
    "biochar", "rainwater harvesting", "seed library", "tool library",
    "repair cafe", "time bank", "community currency", "solidarity economy",
    "renewable energy cooperative", "microgrid", "off-grid", "energy sovereignty",
    "food sovereignty", "community composting", "community biogas",
    "agroforestry", "permaculture", "community land", "community broadband",
]

# Verifiability signals — results must contain at least one
VERIFY_SIGNALS = [
    r"\d+\s*(MW|kW|GWh|MWh)",           # energy capacity
    r"\$[\d,]+",                          # dollar amounts
    r"\d+\s*(homes|households|families)", # homes served
    r"\d+\s*(acres|hectares|ha)",         # land area
    r"\d+\s*(members|people|residents)",  # people count
    r"(20\d{2}|19\d{2})",               # years (project dates)
    r"(grant|funded|million|thousand)",   # funding evidence
]


def ddg_search(query: str, max_results: int = 5) -> list[dict]:
    """
    DuckDuckGo HTML search — no API key, returns list of {title, url, snippet}.
    Rate-limited to be polite.
    """
    results = []
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; SolarPunkBot/1.0; research)",
            "Accept-Language": "en-US,en;q=0.9",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Extract result blocks
        blocks = re.findall(
            r'class="result__body".*?class="result__snippet"[^>]*>(.*?)</a>',
            html, re.DOTALL
        )
        # Extract titles and URLs
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
        urls   = re.findall(r'href="//duckduckgo\.com/l/\?uddg=([^"&]+)', html)
        snips  = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)

        for i in range(min(max_results, len(titles))):
            title = re.sub(r'<[^>]+>', '', titles[i]).strip()
            url_raw = urllib.parse.unquote(urls[i]) if i < len(urls) else ""
            snippet = re.sub(r'<[^>]+>', '', snips[i]).strip() if i < len(snips) else ""
            if title and url_raw:
                results.append({"title": title, "url": url_raw, "snippet": snippet})

    except Exception as e:
        print(f"    [search error] {e}")

    return results


def is_solarpunk_relevant(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in SOLARPUNK_KEYWORDS)


def has_verifiable_data(text: str) -> bool:
    return any(re.search(pat, text, re.IGNORECASE) for pat in VERIFY_SIGNALS)


def extract_location_from_text(text: str) -> dict:
    """Attempt to extract location hints from title+snippet."""
    countries = [
        "Kenya", "Ghana", "Nigeria", "Tanzania", "Rwanda", "Ethiopia", "Uganda",
        "South Africa", "Mozambique", "Senegal", "Mali", "Morocco",
        "Brazil", "Colombia", "Ecuador", "Bolivia", "Argentina", "Chile", "Peru",
        "Palestine", "Jordan", "Lebanon", "Tunisia", "Egypt",
        "UK", "Germany", "Netherlands", "Denmark", "Scotland", "France", "Spain",
        "Fiji", "Vanuatu", "Samoa", "Tonga", "Cook Islands", "New Zealand",
        "India", "Bangladesh", "Philippines", "Indonesia", "Nepal",
        "Vietnam", "Cambodia", "Myanmar", "Thailand",
        "Guatemala", "Honduras", "Nicaragua", "Costa Rica", "El Salvador",
        "Puerto Rico", "Cuba", "Jamaica", "Trinidad",
    ]
    found = [c for c in countries if c.lower() in text.lower()]
    return {"country": found[0]} if found else {}


def score_result(result: dict, gap_id: str) -> float:
    """Score a search result for relevance (0-1)."""
    text = f"{result.get('title','')} {result.get('snippet','')}".lower()
    score = 0.0
    if is_solarpunk_relevant(text):
        score += 0.4
    if has_verifiable_data(text):
        score += 0.3
    relevant_kws = sum(1 for kw in SOLARPUNK_KEYWORDS if kw in text)
    score += min(relevant_kws * 0.05, 0.3)
    return min(score, 1.0)


def search_gap(gap_id: str, gap: dict, dimension: str, max_queries: int = 2) -> list[dict]:
    """Search for projects filling a specific gap. Returns candidate list."""
    queries = gap.get("search_queries", [])[:max_queries]
    if not queries:
        return []

    candidates = []
    for query in queries:
        print(f"    [{dimension[:4]}] {query[:70]}")
        results = ddg_search(query, max_results=4)
        time.sleep(1.5)  # polite rate limiting

        for r in results:
            text = f"{r.get('title','')} {r.get('snippet','')}"
            score = score_result(r, gap_id)
            if score >= 0.35:
                candidate = {
                    "id": f"candidate_{gap_id}_{hash(r.get('url',''))%10000:04d}",
                    "gap_dimension": dimension,
                    "gap_id": gap_id,
                    "search_query": query,
                    "score": round(score, 2),
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("snippet", ""),
                    "location": extract_location_from_text(text),
                    "solarpunk_relevant": is_solarpunk_relevant(text),
                    "has_verifiable_data": has_verifiable_data(text),
                    "found_at": datetime.datetime.utcnow().isoformat() + "Z",
                    "status": "candidate",  # -> verified -> rejected -> ingested
                }
                candidates.append(candidate)
                print(f"      + [{score:.2f}] {r['title'][:60]}")

    return candidates


def load_existing_candidates() -> list[dict]:
    if CANDIDATES_FILE.exists():
        with open(CANDIDATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("candidates", [])
    return []


def save_candidates(all_candidates: list[dict], new_count: int) -> None:
    # Deduplicate by URL
    seen_urls = set()
    unique = []
    for c in all_candidates:
        u = c.get("url", "")
        if u and u not in seen_urls:
            seen_urls.add(u)
            unique.append(c)

    output = {
        "meta": {
            "last_run": datetime.datetime.utcnow().isoformat() + "Z",
            "total_candidates": len(unique),
            "new_this_run": new_count,
            "pending_review": sum(1 for c in unique if c.get("status") == "candidate"),
            "verified": sum(1 for c in unique if c.get("status") == "verified"),
            "ingested": sum(1 for c in unique if c.get("status") == "ingested"),
        },
        "candidates": sorted(unique, key=lambda x: -x.get("score", 0)),
    }
    with open(CANDIDATES_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def run(gap_filter: str = None, limit: int = None):
    print("\n" + "="*58)
    print("  RESEARCH_FETCHER -- SolarPunk Gap Research Engine")
    print(f"  {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("="*58 + "\n")

    if not GAPS_FILE.exists():
        print("  No gaps file found. Run KNOWLEDGE_LOOP.py first.")
        return

    with open(GAPS_FILE, "r", encoding="utf-8") as f:
        gaps_data = json.load(f)

    existing = load_existing_candidates()
    existing_urls = {c.get("url") for c in existing}
    new_candidates = []
    queries_run = 0

    dimensions = {
        "geographic":  gaps_data.get("geographic", {}),
        "categorical": gaps_data.get("categorical", {}),
    }

    for dimension, gaps in dimensions.items():
        if not gaps:
            continue
        # Sort geographic by priority
        if dimension == "geographic":
            priority_order = {"high": 0, "medium": 1, "low": 2}
            gaps_sorted = sorted(
                gaps.items(),
                key=lambda x: priority_order.get(x[1].get("priority", "medium"), 1)
            )
        else:
            gaps_sorted = list(gaps.items())

        for gap_id, gap in gaps_sorted:
            full_id = f"{dimension}.{gap_id}"
            if gap_filter and full_id != gap_filter and gap_id != gap_filter:
                continue
            if gap.get("filled"):
                continue
            if limit and queries_run >= limit:
                break

            label = gap.get("label") or gap.get("description", gap_id)[:50]
            print(f"\n  Researching: [{dimension}] {label}")
            candidates = search_gap(gap_id, gap, dimension, max_queries=2)
            new = [c for c in candidates if c.get("url") not in existing_urls]
            new_candidates.extend(new)
            existing_urls.update(c.get("url") for c in new)
            queries_run += 1

    all_candidates = existing + new_candidates
    save_candidates(all_candidates, len(new_candidates))

    print(f"\n  Research complete.")
    print(f"  New candidates found: {len(new_candidates)}")
    print(f"  Total in pipeline: {len(all_candidates)}")
    print(f"  Top candidates:")
    top = sorted(new_candidates, key=lambda x: -x.get("score", 0))[:5]
    for c in top:
        print(f"    [{c['score']:.2f}] {c['title'][:60]}")
        print(f"           {c['url'][:70]}")
    print()


if __name__ == "__main__":
    gap_filter = None
    limit = None
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--gap" and i + 1 < len(sys.argv) - 1:
            gap_filter = sys.argv[i + 2]
        elif arg == "--limit" and i + 1 < len(sys.argv) - 1:
            limit = int(sys.argv[i + 2])
        elif arg.startswith("--gap="):
            gap_filter = arg.split("=", 1)[1]
        elif arg.startswith("--limit="):
            limit = int(arg.split("=", 1)[1])
    run(gap_filter=gap_filter, limit=limit)
