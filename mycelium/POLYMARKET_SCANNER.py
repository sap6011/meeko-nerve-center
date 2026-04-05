#!/usr/bin/env python3
"""
POLYMARKET_SCANNER.py -- Market intelligence for prediction markets
===================================================================
Reads live market data from Polymarket's Gamma API (no auth needed).
Identifies mispriced contracts, high-volume opportunities, and
markets approaching resolution.

This is RESEARCH ONLY. No trades are placed. No auth required.
The human anchor makes all trading decisions.

Usage:
  python POLYMARKET_SCANNER.py              # Full scan
  python POLYMARKET_SCANNER.py --politics   # Filter by category
  python POLYMARKET_SCANNER.py --edge       # Show potential mispricings
"""
import json, sys, time, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

GAMMA_API = "https://gamma-api.polymarket.com"


def fetch_json(url, timeout=30):
    """Fetch JSON from URL with error handling."""
    req = urllib.request.Request(url, headers={"User-Agent": "SolarPunk-Scanner/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"  [SCAN] Fetch error: {e}")
        return []


def get_active_markets(limit=100, category=None):
    """Pull active markets sorted by volume."""
    url = f"{GAMMA_API}/markets?closed=false&limit={limit}&order=volume&ascending=false"
    if category:
        url += f"&tag={category}"
    return fetch_json(url)


def get_market_detail(condition_id):
    """Get detailed market info including order book depth."""
    url = f"{GAMMA_API}/markets/{condition_id}"
    return fetch_json(url)


def parse_market(m):
    """Extract clean data from a market object."""
    try:
        prices = json.loads(m.get("outcomePrices", "[]"))
        outcomes = m.get("outcomes", [])
    except (json.JSONDecodeError, TypeError):
        prices = []
        outcomes = []

    yes_price = float(prices[0]) if len(prices) > 0 else 0
    no_price = float(prices[1]) if len(prices) > 1 else 0
    volume = float(m.get("volume", 0))
    liquidity = float(m.get("liquidity", 0))

    return {
        "id": m.get("conditionId", m.get("id", "")),
        "question": m.get("question", "")[:100],
        "volume": volume,
        "liquidity": liquidity,
        "yes_price": yes_price,
        "no_price": no_price,
        "yes_pct": round(yes_price * 100, 1),
        "no_pct": round(no_price * 100, 1),
        "end_date": (m.get("endDate") or "")[:10],
        "category": m.get("groupSlug", m.get("category", "unknown")),
        "active": m.get("active", True),
        "spread": round(abs(1.0 - yes_price - no_price), 4),
    }


def find_edges(markets, min_volume=10000):
    """
    Find potential mispricings.

    Edge signals:
    1. High spread (yes + no != 1.0) -- arbitrage opportunity
    2. Extreme odds (>95% or <5%) near resolution -- easy money if correct
    3. High volume + recent price movement -- momentum
    4. Low liquidity relative to volume -- thin book, can be moved
    """
    edges = []
    for m in markets:
        p = parse_market(m)
        if p["volume"] < min_volume:
            continue

        signals = []
        score = 0

        # Spread check
        if p["spread"] > 0.02:
            signals.append(f"SPREAD: {p['spread']:.3f} (arb opportunity)")
            score += 3

        # Near-certain markets approaching resolution
        if p["yes_pct"] > 95 or p["yes_pct"] < 5:
            signals.append(f"EXTREME: {p['yes_pct']}% (easy money if correct)")
            score += 2

        # Volume to liquidity ratio (thin markets)
        if p["liquidity"] > 0:
            vol_liq_ratio = p["volume"] / p["liquidity"]
            if vol_liq_ratio > 5:
                signals.append(f"THIN: vol/liq={vol_liq_ratio:.1f} (movable)")
                score += 1

        # Near resolution date
        if p["end_date"]:
            try:
                end = datetime.strptime(p["end_date"], "%Y-%m-%d")
                days_left = (end - datetime.now()).days
                if 0 < days_left <= 3:
                    signals.append(f"IMMINENT: {days_left}d left")
                    score += 2
                elif 3 < days_left <= 7:
                    signals.append(f"SOON: {days_left}d left")
                    score += 1
            except ValueError:
                pass

        if signals:
            p["signals"] = signals
            p["edge_score"] = score
            edges.append(p)

    edges.sort(key=lambda x: x["edge_score"], reverse=True)
    return edges


def scan_categories():
    """Scan markets by category."""
    categories = ["politics", "crypto", "sports", "science", "culture", "business"]
    results = {}
    for cat in categories:
        markets = get_active_markets(limit=10, category=cat)
        results[cat] = [parse_market(m) for m in markets if float(m.get("volume", 0)) > 1000]
        print(f"  [SCAN] {cat}: {len(results[cat])} active markets")
    return results


def full_scan():
    """Run a complete market scan and save results."""
    print("POLYMARKET SCANNER -- Live Market Intelligence")
    print("=" * 60)
    print()

    # 1. Get top markets by volume
    print("[1/3] Fetching top markets by volume...")
    top_markets = get_active_markets(limit=100)
    parsed = [parse_market(m) for m in top_markets]
    print(f"  Found {len(parsed)} active markets")
    print()

    # 2. Find edges
    print("[2/3] Scanning for edges...")
    edges = find_edges(top_markets, min_volume=5000)
    print(f"  Found {len(edges)} potential opportunities")
    print()

    # 3. Display top opportunities
    print("[3/3] TOP OPPORTUNITIES")
    print("-" * 60)
    for e in edges[:15]:
        print(f"  {e['question']}")
        print(f"    YES: {e['yes_pct']}% | NO: {e['no_pct']}% | Vol: ${e['volume']:,.0f} | Ends: {e['end_date']}")
        for s in e["signals"]:
            print(f"    >> {s}")
        print()

    # Save scan results
    scan_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_markets_scanned": len(parsed),
        "edges_found": len(edges),
        "top_markets": parsed[:25],
        "top_edges": edges[:15],
    }
    (DATA / "polymarket_scan.json").write_text(
        json.dumps(scan_data, indent=2, ensure_ascii=False)
    , encoding="utf-8")
    print(f"Scan saved to data/polymarket_scan.json")
    return scan_data


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--edge" in args:
        markets = get_active_markets(limit=200)
        edges = find_edges(markets, min_volume=1000)
        for e in edges[:20]:
            print(f"{e['question']}")
            print(f"  YES: {e['yes_pct']}% | Vol: ${e['volume']:,.0f} | Score: {e['edge_score']}")
            for s in e["signals"]:
                print(f"  >> {s}")
            print()
    elif "--politics" in args:
        markets = get_active_markets(limit=50, category="politics")
        for m in markets:
            p = parse_market(m)
            if p["volume"] > 1000:
                print(f"{p['question']}")
                print(f"  YES: {p['yes_pct']}% | Vol: ${p['volume']:,.0f}")
                print()
    else:
        full_scan()
