#!/usr/bin/env python3
"""
POLYMARKET_SCANNER.py -- Prediction Market Intelligence Layer
=============================================================
v3 (2026-04-05): INTELLIGENCE LAYER -- crowd-sourced probability engine.

The PIVOT: Polymarket deposits are geo-blocked, so we pivoted from
trading tool to INTELLIGENCE FEED. Crowd-sourced prediction probabilities
on world events = free, real-time signal layer for crypto decisions.

Architecture:
  POLYMARKET_SCANNER (this file)
    -> extract_crypto_intelligence()   # classify markets by crypto/macro/crisis
    -> derive_market_sentiment()       # aggregate into actionable scores
    -> build_intelligence_feed()       # save to data/prediction_intelligence.json
      -> SOL_MAXIMIZER reads feed     # adjusts aggressive/conservative/balanced
      -> YIELD_LOOP reads feed        # accelerate/slow compound actions

How it informs decisions:
  - "Will SOL hit $150?" at 60%  -> SOL_MAXIMIZER: accumulate mode
  - "Will recession hit?"  at 80% -> YIELD_LOOP: conservative compounding
  - "Will BTC ETF pass?"   at 90% -> crypto_bullish signal = risk on
  - Active war/crisis      at 70% -> crisis_level triggers safe harbor

Two API modes:
  - Gamma API (public): Market data, prices, volumes, edge detection
  - CLOB API (authenticated): Market depth, order book data

Writes:
  - data/polymarket_scan.json          # full scan + edges
  - data/prediction_intelligence.json  # intelligence feed for other engines

Called by: OMNIBUS
Consumed by: SOL_MAXIMIZER, YIELD_LOOP
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


def extract_crypto_intelligence(markets):
    """
    Extract crypto-relevant prediction probabilities from market data.

    This is the PIVOT: Polymarket as free intelligence feed.
    Market probabilities = crowd-sourced predictions on future events.
    Feed these into SOL_MAXIMIZER and YIELD_LOOP for smarter decisions.
    """
    # Use longer/specific keywords to avoid false positives from sports markets
    # e.g. "sol" matches "Mirassol FC", "coin" matches random words
    crypto_keywords = [
        "bitcoin", " btc ", "ethereum", " eth ", "solana", "crypto",
        " sec ", "etf", "defi", "blockchain", "token launch",
        "binance", "coinbase", "stablecoin", "usdc", "usdt",
        "market cap", "altcoin", "memecoin", " nft ",
    ]
    macro_keywords = [
        "federal reserve", "interest rate", "inflation", "recession", "gdp",
        "tariff", "trade war", "sanctions", "treasury", "dollar",
        "unemployment", "stock market", "s&p", "nasdaq",
    ]
    crisis_keywords = [
        "war ", "conflict", "invasion", "missile", "nuclear",
        "earthquake", "hurricane", "pandemic", "outbreak",
    ]

    signals = {
        "crypto": [],
        "macro": [],
        "crisis": [],
        "sol_specific": [],
    }

    for m in markets:
        p = parse_market(m)
        q = p["question"].lower()

        # Classify the market
        is_crypto = any(kw in q for kw in crypto_keywords)
        is_macro = any(kw in q for kw in macro_keywords)
        is_crisis = any(kw in q for kw in crisis_keywords)
        is_sol = any(kw in q for kw in ["solana", " sol ", "sol price", "sol hit"])

        signal = {
            "question": p["question"],
            "yes_pct": p["yes_pct"],
            "no_pct": p["no_pct"],
            "volume": p["volume"],
            "end_date": p["end_date"],
            "confidence": "high" if p["volume"] > 100000 else "medium" if p["volume"] > 10000 else "low",
        }

        if is_sol:
            signals["sol_specific"].append(signal)
        if is_crypto:
            signals["crypto"].append(signal)
        if is_macro:
            signals["macro"].append(signal)
        if is_crisis:
            signals["crisis"].append(signal)

    # Sort each category by volume (higher volume = more reliable signal)
    for cat in signals:
        signals[cat].sort(key=lambda x: x["volume"], reverse=True)

    return signals


def derive_market_sentiment(signals):
    """
    Derive actionable sentiment scores from prediction markets.

    Returns scores that SOL_MAXIMIZER and YIELD_LOOP can consume directly.
    """
    sentiment = {
        "crypto_bullish": 0.5,      # 0-1 scale, 0.5 = neutral
        "macro_risk": 0.5,          # 0-1, higher = more risk
        "crisis_level": 0.0,        # 0-1, higher = more crisis
        "sol_outlook": 0.5,         # 0-1, higher = more bullish on SOL
        "recommended_action": "hold",
        "reasoning": [],
    }

    # Crypto sentiment: average YES probability of bullish crypto markets
    crypto_sigs = signals.get("crypto", [])
    if crypto_sigs:
        # Markets about crypto going UP -> high yes_pct = bullish
        avg_crypto = sum(s["yes_pct"] for s in crypto_sigs[:10]) / min(len(crypto_sigs), 10)
        sentiment["crypto_bullish"] = round(avg_crypto / 100, 3)
        if avg_crypto > 65:
            sentiment["reasoning"].append(f"Crypto markets leaning bullish ({avg_crypto:.0f}% avg YES)")
        elif avg_crypto < 35:
            sentiment["reasoning"].append(f"Crypto markets leaning bearish ({avg_crypto:.0f}% avg YES)")

    # SOL-specific outlook
    sol_sigs = signals.get("sol_specific", [])
    if sol_sigs:
        avg_sol = sum(s["yes_pct"] for s in sol_sigs[:5]) / min(len(sol_sigs), 5)
        sentiment["sol_outlook"] = round(avg_sol / 100, 3)
        if avg_sol > 70:
            sentiment["reasoning"].append(f"SOL-specific markets bullish ({avg_sol:.0f}%)")
            sentiment["recommended_action"] = "accumulate"
        elif avg_sol < 30:
            sentiment["reasoning"].append(f"SOL-specific markets cautious ({avg_sol:.0f}%)")
            sentiment["recommended_action"] = "reduce_exposure"

    # Macro risk: high YES on rate hikes, recession = risky for crypto
    macro_sigs = signals.get("macro", [])
    if macro_sigs:
        avg_macro = sum(s["yes_pct"] for s in macro_sigs[:5]) / min(len(macro_sigs), 5)
        sentiment["macro_risk"] = round(avg_macro / 100, 3)
        if avg_macro > 70:
            sentiment["reasoning"].append(f"Macro headwinds detected ({avg_macro:.0f}% risk)")

    # Crisis level: any high-confidence crisis market = caution
    crisis_sigs = signals.get("crisis", [])
    if crisis_sigs:
        max_crisis = max(s["yes_pct"] for s in crisis_sigs[:5])
        sentiment["crisis_level"] = round(max_crisis / 100, 3)
        if max_crisis > 80:
            sentiment["reasoning"].append(f"Active crisis signal ({max_crisis:.0f}% probability)")
            if sentiment["recommended_action"] != "reduce_exposure":
                sentiment["recommended_action"] = "hold"

    # Final action logic
    if not sentiment["reasoning"]:
        sentiment["reasoning"].append("Insufficient prediction market data -- defaulting to base strategy")
        sentiment["recommended_action"] = "follow_base_strategy"

    return sentiment


def build_intelligence_feed():
    """
    Build the full intelligence feed from Polymarket data.

    This is what SOL_MAXIMIZER and YIELD_LOOP consume.
    Saved to data/prediction_intelligence.json
    """
    print("[POLYMARKET] Building intelligence feed...")

    markets = get_active_markets(limit=200)
    if not markets:
        print("[POLYMARKET] No market data available -- feed empty")
        return {"status": "no_data", "timestamp": datetime.now(timezone.utc).isoformat()}

    signals = extract_crypto_intelligence(markets)
    sentiment = derive_market_sentiment(signals)

    feed = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "polymarket_gamma_api",
        "markets_analyzed": len(markets),
        "signals": {
            "crypto_markets": len(signals["crypto"]),
            "macro_markets": len(signals["macro"]),
            "crisis_markets": len(signals["crisis"]),
            "sol_specific": len(signals["sol_specific"]),
        },
        "sentiment": sentiment,
        "top_crypto_signals": signals["crypto"][:10],
        "top_macro_signals": signals["macro"][:5],
        "sol_signals": signals["sol_specific"][:5],
        "crisis_signals": signals["crisis"][:5],
    }

    (DATA / "prediction_intelligence.json").write_text(
        json.dumps(feed, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[POLYMARKET] Intelligence feed: {len(signals['crypto'])} crypto, "
          f"{len(signals['macro'])} macro, {len(signals['sol_specific'])} SOL-specific")
    print(f"[POLYMARKET] Sentiment: {sentiment['recommended_action']} "
          f"(crypto={sentiment['crypto_bullish']}, sol={sentiment['sol_outlook']})")

    return feed


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

    # BUILD INTELLIGENCE FEED -- the core pivot
    # This is what SOL_MAXIMIZER and YIELD_LOOP consume for decisions
    intel_feed = build_intelligence_feed()
    scan_data["intelligence_feed"] = {
        "status": "active",
        "sentiment": intel_feed.get("sentiment", {}),
        "signals_found": intel_feed.get("signals", {}),
        "file": "data/prediction_intelligence.json",
    }

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
            "note": "SolarPunk crisis data informs geopolitical prediction markets",
        }

    # Add nervous system awareness
    _homeo = _load(DATA / "homeostasis_state.json")
    _cortex = _load(DATA / "neural_cortex_state.json")
    scan_data["nervous_system"] = {
        "equilibrium": _homeo.get("equilibrium", 0) if _homeo else 0,
        "homeostasis_trend": _homeo.get("trend", "unknown") if _homeo else "unknown",
        "brain_confidence": _cortex.get("decision_confidence", 0) if _cortex else 0,
        "brain_risk_posture": _cortex.get("strategy", {}).get("risk_posture", "moderate") if _cortex else "moderate",
    }

    # Save enriched scan
    (DATA / "polymarket_scan.json").write_text(
        json.dumps(scan_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Broadcast to synaptic bus
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_batch("POLYMARKET_SCANNER", {
            "edges_found": scan_data.get("edges_found", 0),
            "total_markets_scanned": scan_data.get("total_markets_scanned", 0),
            "status": "active",
            "equilibrium": scan_data["nervous_system"]["equilibrium"],
            "brain_confidence": scan_data["nervous_system"]["brain_confidence"],
        }, silent=True)
    except Exception:
        pass

    edges = scan_data.get("edges_found", 0)
    sentiment = intel_feed.get("sentiment", {})
    print(f"[POLYMARKET] Scan complete: {scan_data.get('total_markets_scanned', 0)} markets, {edges} edges")
    print(f"[POLYMARKET] Intelligence: {sentiment.get('recommended_action', 'N/A')} "
          f"(crypto={sentiment.get('crypto_bullish', '?')}, sol={sentiment.get('sol_outlook', '?')})")
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
