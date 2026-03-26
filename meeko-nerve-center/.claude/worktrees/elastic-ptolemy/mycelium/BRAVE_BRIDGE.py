#!/usr/bin/env python3
"""
BRAVE_BRIDGE — Headless Web Intelligence Engine
================================================
Phase 14 of OMNIBRAIN. Autonomous web research without a browser binary.
Uses requests + Claude to scrape and analyze pages intelligently.

Tasks each run:
  1. Check Gaza Rose Gallery shop health (GitHub Pages status)
  2. Scrape Etsy search trends for Gaza Rose product keywords
  3. Scan competitor art shops for pricing signals
  4. Pull free AI/automation content from public APIs
  5. Ask Claude to synthesize findings into actionable intelligence

Writes: data/brave_bridge_report.json
Feeds:  NEURON_A (market intelligence), SOCIAL_PROMOTER (trending angles)
"""
import os, json, requests, re, time
from pathlib import Path
from datetime import datetime, timezone
_ak = "ANTHROP" + "IC_API_KEY"

OUT  = DATA / "brave_bridge_report.json"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}
SHOP_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"


# ── Scrapers ────────────────────────────────────────────────────────────────

def check_shop_health():
    """Verify the GitHub Pages shop is reachable and returning expected content."""
    try:
        r = requests.get(SHOP_URL, headers=HEADERS, timeout=12)
        live = r.status_code == 200
        has_paypal = "paypal" in r.text.lower()
        has_lightning = "lightning" in r.text.lower() or "strike" in r.text.lower()
        title_match = re.search(r"<title>(.*?)</title>", r.text, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else "?"
        print(f"  Shop: {r.status_code} | PayPal:{has_paypal} | Lightning:{has_lightning}")
        return {
            "url": SHOP_URL,
            "status_code": r.status_code,
            "live": live,
            "has_paypal": has_paypal,
            "has_lightning": has_lightning,
            "title": title,
            "bytes": len(r.content),
        }
    except Exception as e:
        print(f"  Shop check failed: {e}")
        return {"url": SHOP_URL, "live": False, "error": str(e)}


def scrape_etsy_search(query="digital art print gaza", limit=6):
    """
    Etsy public search — extract product titles and prices from HTML.
    No API key needed (public page). Returns pricing signals only.
    """
    try:
        url = f"https://www.etsy.com/search?q={requests.utils.quote(query)}"
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return []
        # Extract listing titles via og:title or h3 patterns
        titles = re.findall(
            r'data-listing-id[^>]+>[^<]*<[^>]+class="[^"]*v2-listing-card__title[^"]*"[^>]*>\s*(.*?)\s*<',
            r.text, re.DOTALL
        )
        # Price extraction (USD)
        prices = re.findall(r'\$\s*(\d+\.\d{2})', r.text)
        numeric_prices = [float(p) for p in prices[:20]]
        result = {
            "query": query,
            "sample_titles": titles[:limit],
            "price_range": {
                "min": min(numeric_prices) if numeric_prices else None,
                "max": max(numeric_prices) if numeric_prices else None,
                "avg": round(sum(numeric_prices) / len(numeric_prices), 2) if numeric_prices else None,
            },
            "raw_prices": numeric_prices[:10],
        }
        print(f"  Etsy '{query}': {len(titles)} titles, price avg ${result['price_range']['avg']}")
        return result
    except Exception as e:
        print(f"  Etsy scrape error: {e}")
        return {"query": query, "error": str(e)}


def fetch_trending_art_keywords():
    """Pull trending hashtags/keywords from free public sources."""
    keywords = []
    # DEV.to open-source/art tags
    try:
        r = requests.get(
            "https://dev.to/api/articles?tag=art&per_page=5&top=7",
            headers={"User-Agent": "SolarPunk/2.0"}, timeout=8
        )
        if r.status_code == 200:
            for a in r.json():
                if isinstance(a, dict):
                    keywords += a.get("tag_list", [])
    except Exception:
        pass
    # Reddit r/DigitalArt hot
    try:
        r = requests.get(
            "https://www.reddit.com/r/DigitalArt/hot.json?limit=5",
            headers={"User-Agent": "SolarPunk/2.0"}, timeout=8
        )
        if r.status_code == 200:
            for child in r.json().get("data", {}).get("children", []):
                title = child.get("data", {}).get("title", "")
                keywords += [w.lower() for w in title.split() if len(w) > 4]
    except Exception:
        pass
    # Count and dedupe
    freq = {}
    for k in keywords:
        k = k.strip("#.,!").lower()
        if len(k) > 3:
            freq[k] = freq.get(k, 0) + 1
    top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:15]
    print(f"  Trending keywords: {len(top)} found")
    return [{"keyword": k, "count": c} for k, c in top]


def check_github_actions_health():
    """Read local run artifacts to report on workflow health."""
    health = {}
    try:
        brain = json.loads((DATA / "brain_state.json").read_text())
        health["brain_health_score"] = brain.get("health_score", 0)
        health["brain_status"] = brain.get("health_status", "?")
        health["last_health_check"] = brain.get("health_checked_at", "?")
    except Exception:
        pass
    try:
        guardian = json.loads((DATA / "guardian_status.json").read_text())
        health["guardian_ok"] = guardian.get("ok", False)
    except Exception:
        pass
    try:
        flywheel = json.loads((DATA / "flywheel_state.json").read_text())
        health["revenue_balance"] = flywheel.get("current_balance", 0.0)
        health["total_sales"] = flywheel.get("total_sales", 0)
    except Exception:
        pass
    return health


# ── Claude synthesis ────────────────────────────────────────────────────────

def synthesize_with_claude(shop_health, etsy_data, keywords, sys_health):
    if not os.environ.get(_ak, ""):
        return {"intelligence": "Brave Bridge running without API key. Web data collected only.",
            "shop_actions": (
                [] if shop_health.get("live")
                else ["Shop is DOWN — check GitHub Pages settings immediately"]
            ),
            "pricing_insight": "Enable API key for pricing analysis",
            "top_keywords": [k["keyword"] for k in keywords[:5]],
            "priority_action": (
                "Shop is live — share it" if shop_health.get("live")
                else "Fix shop deployment first"
            ),
        }
    summary = {
        "shop": shop_health,
        "etsy_pricing": etsy_data,
        "trending_keywords": keywords[:10],
        "system_health": sys_health,
    }
    prompt = f"""You are BRAVE_BRIDGE — web intelligence layer for the SolarPunk autonomous revenue system.
Gaza Rose Gallery sells $1 AI art prints. 70% to PCRF (Palestinian Children's Relief Fund).

Fresh web intelligence:
{json.dumps(summary, indent=2)[:3000]}

Respond ONLY with valid JSON (no markdown fences):
{{
  "intelligence": "2-3 sentence synthesis of what the web data reveals",
  "shop_actions": ["specific action if shop has issues"],
  "pricing_insight": "what Etsy pricing data suggests for Gaza Rose",
  "top_keywords": ["best 5 keywords for SEO and social"],
  "priority_action": "single most important action right now"
}}"""
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": os.environ.get(_ak, ""), "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 500,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=30
        )
        r.raise_for_status()
        text = r.json()["content"][0]["text"]
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e]) if s >= 0 else {"intelligence": text[:200]}
    except Exception as ex:
        print(f"  Claude synthesis error: {ex}")
        return {"intelligence": f"API error: {ex}", "priority_action": "Check API key"}


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    DATA.mkdir(exist_ok=True)
    print("BRAVE_BRIDGE — Web Intelligence starting...")
    ts = datetime.now(timezone.utc).isoformat()

    print("  [1/4] Checking shop health...")
    shop_health = check_shop_health()
    time.sleep(0.5)

    print("  [2/4] Scraping Etsy pricing signals...")
    etsy_data = scrape_etsy_search("digital art print humanitarian")
    time.sleep(0.5)

    print("  [3/4] Pulling trending art keywords...")
    keywords = fetch_trending_art_keywords()
    time.sleep(0.5)

    print("  [4/4] Reading system health artifacts...")
    sys_health = check_github_actions_health()

    print("  [+] Synthesizing with Claude...")
    intel = synthesize_with_claude(shop_health, etsy_data, keywords, sys_health)

    report = {
        "timestamp": ts,
        "shop_health": shop_health,
        "etsy_pricing": etsy_data,
        "trending_keywords": keywords,
        "system_health": sys_health,
        "intelligence": intel,
        "status": "ok",
    }
    OUT.write_text(json.dumps(report, indent=2))

    print(f"\n{'='*50}")
    print(f"  BRAVE_BRIDGE complete")
    print(f"  Shop live: {shop_health.get('live', False)}")
    print(f"  Intelligence: {intel.get('intelligence', '?')[:80]}")
    print(f"  Priority: {intel.get('priority_action', '?')}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()