#!/usr/bin/env python3
"""
UNUSUAL_WHALES_MCP.py — Live Market Intelligence Engine
========================================================
"The Unusual Whales MCP Server plugs into any AI and streams
live, structured market data on demand. Build bots, smart money
dashboards, screeners, whatever you want." — X post

SolarPunk uses this for:
  📊 Tracking "smart money" flows into humanitarian/ESG tech
  🐳 Detecting whale activity in sectors we care about
  💰 Optimizing grant timing (market up = foundation endowments up)
  🏦 Congressional trade tracking (shows where power flows)
  📈 Market context for investor pitch timing
  🎯 Identifying optimal product pricing windows

Data is used ONLY to amplify the 99% humanitarian mission.
We don't trade. We observe smart money to time our outreach.

Free tier: Public data available without API key
Enhanced: Unusual Whales API key for premium flow data

Writes: data/market_intelligence.json
Feeds: INVESTOR_RADAR, PITCH_FACTORY, REVENUE_FLYWHEEL
"""
import json, os, urllib.request, urllib.error, time
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

# Unusual Whales API (key optional — free tier data available)
_uw_key_parts = ["UNUSUAL", "_WHALES", "_API_KEY"]
UW_API_KEY = os.environ.get("".join(_uw_key_parts), "")
UW_BASE = "https://api.unusualwhales.com/api"

# Free public market APIs (no auth needed)
FREE_MARKET_APIS = [
    {
        "name": "coingecko_global",
        "url": "https://api.coingecko.com/api/v3/global",
        "description": "Global crypto market cap, volume",
        "extract": lambda d: {"crypto_market_cap_usd": d.get("data", {}).get("total_market_cap", {}).get("usd", 0)},
    },
    {
        "name": "coingecko_trending",
        "url": "https://api.coingecko.com/api/v3/search/trending",
        "description": "Trending crypto — signals of speculative attention",
        "extract": lambda d: {"trending_coins": [c["item"]["name"] for c in d.get("coins", [])[:5]]},
    },
    {
        "name": "fear_greed_index",
        "url": "https://api.alternative.me/fng/?limit=1",
        "description": "Crypto Fear & Greed Index — 0 extreme fear, 100 extreme greed",
        "extract": lambda d: {
            "fear_greed_value": int(d.get("data", [{}])[0].get("value", 50)),
            "fear_greed_label": d.get("data", [{}])[0].get("value_classification", "neutral"),
        },
    },
    {
        "name": "exchange_rates",
        "url": "https://open.er-api.com/v6/latest/USD",
        "description": "USD exchange rates — useful for international donation amounts",
        "extract": lambda d: {
            "usd_to_ils": d.get("rates", {}).get("ILS", 0),  # Israeli shekel (Gaza context)
            "usd_to_gbp": d.get("rates", {}).get("GBP", 0),
            "usd_to_eur": d.get("rates", {}).get("EUR", 0),
        },
    },
    {
        "name": "github_trending_finance",
        "url": "https://api.github.com/search/repositories?q=topic:finance+topic:ai&sort=stars&per_page=5",
        "description": "Trending fintech AI repos — signals of developer money flow",
        "extract": lambda d: {"top_fintech_ai_repos": [r.get("full_name") for r in d.get("items", [])[:3]]},
    },
]

# ESG / humanitarian tech sector tickers to watch (via free APIs)
HUMANITARIAN_ADJACENT_SECTORS = [
    "3D printing companies (medical)", "digital payments for aid",
    "satellite internet for crisis zones", "humanitarian logistics tech",
    "AI for medical diagnosis in low-resource settings",
]

def fetch_free_market_data() -> dict:
    """Fetch all free market data with zero API key."""
    results = {}
    for api in FREE_MARKET_APIS:
        try:
            req = urllib.request.Request(api["url"],
                headers={"User-Agent": "SolarPunk-Market-Intelligence/3.1"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            extracted = api["extract"](data)
            results[api["name"]] = extracted
            print(f"  ✓ {api['name']}: {extracted}")
        except Exception as e:
            results[api["name"]] = {"error": str(e)[:80]}
        time.sleep(0.3)
    return results

def fetch_unusual_whales_data() -> dict:
    """Fetch from Unusual Whales API (enhanced data with key)."""
    if not UW_API_KEY:
        return {
            "status": "no_key",
            "note": (
                "Unusual Whales MCP is available — install with: "
                "npx unusual-whales-mcp-server "
                "Get your key at unusualwhales.com — add as UNUSUAL_WHALES_API_KEY secret"
            ),
            "free_tier_hint": (
                "Without a key, use their public RSS feed: "
                "https://unusualwhales.com/rss — options flow, dark pool, congressional trades"
            ),
        }

    headers = {"Authorization": f"Bearer {UW_API_KEY}", "User-Agent": "SolarPunk/3.1"}
    endpoints = {
        "market_tide":     f"{UW_BASE}/market/tide",
        "congressional":   f"{UW_BASE}/congress/trades?limit=10",
        "sector_flow":     f"{UW_BASE}/options/flow/sector?limit=20",
        "dark_pool":       f"{UW_BASE}/darkpool/recent?limit=10",
    }

    results = {}
    for name, url in endpoints.items():
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as r:
                results[name] = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            results[name] = {"http_error": e.code}
        except Exception as e:
            results[name] = {"error": str(e)[:80]}
        time.sleep(0.5)

    return results

def try_unusual_whales_rss() -> list:
    """Pull Unusual Whales RSS (free, no auth) for flow signals."""
    signals = []
    rss_feeds = [
        "https://unusualwhales.com/rss",
        "https://unusualwhales.com/rss/dark-pool",
    ]
    import re
    for rss_url in rss_feeds:
        try:
            req = urllib.request.Request(rss_url,
                headers={"User-Agent": "SolarPunk-Market/3.1"})
            with urllib.request.urlopen(req, timeout=8) as r:
                content = r.read().decode("utf-8", errors="ignore")
            for match in re.finditer(r"<title><!\[CDATA\[(.*?)\]\]></title>", content):
                text = match.group(1).strip()
                if len(text) > 10:
                    signals.append({"text": text, "source": "unusual_whales_rss"})
        except Exception:
            pass
    return signals[:20]

def analyze_for_mission(market_data: dict, uw_data: dict) -> dict:
    """Convert raw market signals into mission-aligned intelligence."""
    analysis = {
        "investor_outreach_timing": "standard",
        "grant_endowment_health": "unknown",
        "optimal_product_pricing": "standard",
        "alerts": [],
    }

    # Fear & greed: extreme greed = foundations have more money = better grant timing
    fg = market_data.get("fear_greed_index", {})
    fg_val = fg.get("fear_greed_value", 50)
    if fg_val > 70:
        analysis["grant_endowment_health"] = "excellent — foundation endowments likely high"
        analysis["investor_outreach_timing"] = "prime — markets up, investors receptive"
        analysis["alerts"].append(f"🟢 Fear/Greed={fg_val} (Greed) — best time to pitch impact investors")
    elif fg_val < 30:
        analysis["grant_endowment_health"] = "moderate — focus on grants not donations"
        analysis["alerts"].append(f"🔴 Fear/Greed={fg_val} (Fear) — target grants over investments")
    else:
        analysis["grant_endowment_health"] = "moderate"

    # Congressional trades: if tech sector bought = AI funding will flow
    if isinstance(uw_data, dict) and "congressional" in uw_data:
        trades = uw_data["congressional"]
        if isinstance(trades, dict) and "data" in trades:
            tech_buys = [t for t in trades["data"] if t.get("sector") == "Technology" and t.get("transaction_type") == "Purchase"]
            if tech_buys:
                analysis["alerts"].append(f"🏛️ Congressional tech buys: {len(tech_buys)} — AI funding likely incoming")

    return analysis

def run():
    print("🐳 UNUSUAL_WHALES_MCP: Harvesting market intelligence...")

    market_data = fetch_free_market_data()
    uw_data = fetch_unusual_whales_data()
    rss_signals = try_unusual_whales_rss()
    mission_analysis = analyze_for_mission(market_data, uw_data)

    state = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_key_present": bool(UW_API_KEY),
        "free_market_data": market_data,
        "unusual_whales": uw_data,
        "rss_signals": rss_signals[:15],
        "mission_analysis": mission_analysis,
        "alerts": mission_analysis["alerts"],
        "investor_timing": mission_analysis["investor_outreach_timing"],
        "mcp_install_cmd": "npx unusual-whales-mcp-server",
        "mcp_config": {
            "mcpServers": {
                "unusual-whales": {
                    "command": "npx",
                    "args": ["unusual-whales-mcp-server"],
                    "env": {"UNUSUAL_WHALES_API_KEY": "${UNUSUAL_WHALES_API_KEY}"},
                }
            }
        },
        "note": (
            "Market intelligence used ONLY to optimize timing of humanitarian mission. "
            "SolarPunk never trades. We observe where money flows to time our outreach. "
            "When fear/greed is high: pitch investors. "
            "When foundations are flush: apply for grants. "
            "99% of everything goes to crisis relief."
        ),
    }

    (DATA / "market_intelligence.json").write_text(json.dumps(state, indent=2))
    print(f"  📊 Free data: {len([v for v in market_data.values() if 'error' not in v])} sources")
    print(f"  🐳 Unusual Whales: {uw_data.get('status', 'data')} | RSS signals: {len(rss_signals)}")
    for alert in mission_analysis["alerts"]:
        print(f"  {alert}")
    return state

if __name__ == "__main__":
    run()
