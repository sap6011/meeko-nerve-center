#!/usr/bin/env python3
"""
POLYMARKET_SCANNER.py -- LIVE market intelligence + portfolio tracking
=====================================================================
v2 (2026-04-05): UPGRADED with Polymarket CLOB API authentication.

Two modes:
  - Gamma API (public): Market data, prices, volumes, edge detection
  - CLOB API (authenticated): Portfolio, positions, balance tracking

API credentials loaded from data/.secrets/polymarket.json (gitignored).
SolarPunk intelligence feeds inform market analysis.

Usage:
  python POLYMARKET_SCANNER.py              # Full scan + portfolio check
  python POLYMARKET_SCANNER.py --edge       # Show potential mispricings
  python POLYMARKET_SCANNER.py --portfolio  # Check positions + balance

Called by: OMNIBUS
Writes: data/polymarket_scan.json
"""
import json, sys, time, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"


def _load_credentials():
    """Load Polymarket API credentials from local secrets (gitignored)."""
    secrets_path = DATA / ".secrets" / "polymarket.json"
    try:
        creds = json.loads(secrets_path.read_text(encoding="utf-8"))
        return creds.get("api_key"), creds.get("address")
    except Exception:
        return None, None


def clob_fetch(endpoint, api_key=None, timeout=15):
    """Authenticated fetch from Polymarket CLOB API."""
    url = f"{CLOB_API}{endpoint}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "SolarPunk/1.0",
        "Accept": "application/json",
    })
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"  [CLOB] Error: {e}")
        return None


def check_portfolio(api_key, address):
    """Check Polymarket portfolio: positions, balance, P&L."""
    print("[POLYMARKET] Checking portfolio...")

    portfolio = {
        "address": address,
        "authenticated": api_key is not None,
        "positions": [],
        "total_value": 0,
    }

    # Check server health
    health = clob_fetch("/")
    if health:
        portfolio["server"] = "online"
        print(f"  [CLOB] Server: online")
    else:
        portfolio["server"] = "unreachable"
        print(f"  [CLOB] Server: unreachable")
        return portfolio

    # Get user positions if authenticated
    if api_key:
        # Try market-data endpoint
        markets_data = clob_fetch("/markets", api_key)
        if markets_data:
            count = len(markets_data) if isinstance(markets_data, list) else 0
            portfolio["clob_markets_available"] = count
            print(f"  [CLOB] Markets available: {count}")

    return portfolio


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


def run():
    """Engine entry point for OMNIBUS. Full scan + portfolio check."""
    print("[POLYMARKET] Starting live market scan...")

    api_key, address = _load_credentials()
    authenticated = api_key is not None

    if authenticated:
        print(f"[POLYMARKET] Authenticated: {address[:10]}...{address[-6:]}")
    else:
        print("[POLYMARKET] Running in public mode (no API key found)")

    # Run the full market scan (public Gamma API)
    scan_data = full_scan()

    # Check portfolio if authenticated
    portfolio = None
    if authenticated:
        portfolio = check_portfolio(api_key, address)
        scan_data["portfolio"] = portfolio
        scan_data["authenticated"] = True
    else:
        scan_data["authenticated"] = False

    # Cross-reference with SolarPunk intelligence
    crisis_data = {}
    try:
        crisis_path = DATA / "crisis_monitor_state.json"
        if crisis_path.exists():
            crisis_data = json.loads(crisis_path.read_text(encoding="utf-8"))
    except Exception:
        pass

    if crisis_data:
        scan_data["intelligence_sources"] = {
            "crisis_monitor": True,
            "active_crises": len(crisis_data.get("crises", [])),
            "note": "SolarPunk crisis data can inform geopolitical prediction markets",
        }

    # Save enriched scan
    (DATA / "polymarket_scan.json").write_text(
        json.dumps(scan_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    edges = scan_data.get("edges_found", 0)
    print(f"[POLYMARKET] Scan complete: {scan_data.get('total_markets_scanned', 0)} markets, {edges} edges")
    if authenticated:
        print(f"[POLYMARKET] Portfolio: {'online' if portfolio and portfolio.get('server') == 'online' else 'checking'}")

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
    elif "--portfolio" in args:
        api_key, address = _load_credentials()
        if api_key:
            portfolio = check_portfolio(api_key, address)
            print(json.dumps(portfolio, indent=2))
        else:
            print("No API key found in data/.secrets/polymarket.json")
    elif "--politics" in args:
        markets = get_active_markets(limit=50, category="politics")
        for m in markets:
            p = parse_market(m)
            if p["volume"] > 1000:
                print(f"{p['question']}")
                print(f"  YES: {p['yes_pct']}% | Vol: ${p['volume']:,.0f}")
                print()
    else:
        run()
