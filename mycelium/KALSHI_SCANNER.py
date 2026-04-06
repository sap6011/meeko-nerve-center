#!/usr/bin/env python3
"""
KALSHI_SCANNER.py -- CFTC-regulated prediction market intelligence
===================================================================
v1 (2026-04-05): Second prediction source for cross-validation.

Kalshi = CFTC-regulated Designated Contract Market, available in all 50 US states.
Free public API, zero auth needed for market data, 0% trading fees.

WHY TWO PREDICTION SOURCES:
  Polymarket + Kalshi = cross-validated probability estimates.
  When both sources agree on a prediction, confidence is HIGH.
  When they disagree, something interesting is happening.

API (no auth required):
  Base: https://api.elections.kalshi.com/trade-api/v2
  GET /markets          -- all active markets (paginated)
  GET /markets/{ticker} -- single market detail
  GET /events           -- all events
  GET /exchange/status  -- exchange health

Categories covered: economics, crypto, politics, sports, weather,
  entertainment, companies, tech, health, world, transportation

Intelligence flow:
  KALSHI_SCANNER + POLYMARKET_SCANNER
    -> merge into prediction_intelligence.json
    -> SOL_MAXIMIZER reads for yield strategy
    -> YIELD_LOOP reads for compound urgency
    -> ARBITRAGE_SCANNER reads for profit routing context

Called by: OMNIBUS
Writes: data/kalshi_scan.json
Merges into: data/prediction_intelligence.json
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

KALSHI_API = "https://api.elections.kalshi.com/trade-api/v2"


def _fetch(url, timeout=15):
    """Fetch JSON from Kalshi API (no auth needed for public data)."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "SolarPunk-Intel/1.0")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"  [KALSHI] Fetch error: {e}")
        return None


def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default or {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def check_exchange_status():
    """Check if Kalshi exchange is online."""
    data = _fetch(f"{KALSHI_API}/exchange/status")
    if data:
        trading = data.get("trading_active", False)
        exchange = data.get("exchange_active", False)
        print(f"  [KALSHI] Exchange: {'ACTIVE' if exchange else 'DOWN'} | Trading: {'OPEN' if trading else 'CLOSED'}")
        return {"exchange_active": exchange, "trading_active": trading}
    print("  [KALSHI] Exchange: unreachable")
    return {"exchange_active": False, "trading_active": False}


def get_markets(limit=200, cursor=None, status="open"):
    """Fetch active markets from Kalshi."""
    url = f"{KALSHI_API}/markets?limit={limit}&status={status}"
    if cursor:
        url += f"&cursor={cursor}"
    data = _fetch(url)
    if data:
        return data.get("markets", []), data.get("cursor", None)
    return [], None


def get_events(limit=100, status="open"):
    """Fetch active events from Kalshi."""
    url = f"{KALSHI_API}/events?limit={limit}&status={status}"
    data = _fetch(url)
    if data:
        return data.get("events", [])
    return []


def parse_market(m):
    """Extract clean data from a Kalshi market object."""
    # Kalshi uses yes_price (cents 0-100) or yes_price_dollars (0.00-1.00)
    yes_price = m.get("yes_price_dollars") or (m.get("yes_price", 0) / 100.0)
    no_price = m.get("no_price_dollars") or (m.get("no_price", 0) / 100.0)

    # Handle None values
    if yes_price is None:
        yes_price = 0
    if no_price is None:
        no_price = 0

    volume = m.get("volume", 0) or 0
    open_interest = m.get("open_interest", 0) or 0

    return {
        "ticker": m.get("ticker", ""),
        "title": m.get("title", m.get("subtitle", ""))[:120],
        "category": m.get("category", m.get("event_ticker", "unknown")),
        "yes_price": float(yes_price),
        "no_price": float(no_price),
        "yes_pct": round(float(yes_price) * 100, 1),
        "no_pct": round(float(no_price) * 100, 1),
        "volume": int(volume),
        "open_interest": int(open_interest),
        "close_time": (m.get("close_time") or "")[:10],
        "status": m.get("status", "open"),
    }


def extract_intelligence(markets):
    """
    Extract actionable intelligence from Kalshi markets.

    Same classification as POLYMARKET_SCANNER for cross-validation.
    """
    crypto_keywords = [
        "bitcoin", " btc ", "ethereum", " eth ", "solana", "crypto",
        "digital asset", "stablecoin", "blockchain", "defi",
    ]
    macro_keywords = [
        "federal reserve", "fed funds", "interest rate", "inflation",
        "cpi", "recession", "gdp", "unemployment", "jobs report",
        "tariff", "treasury", "yield curve",
    ]
    crisis_keywords = [
        "war ", "conflict", "invasion", "missile", "nuclear",
        "hurricane", "earthquake", "pandemic", "emergency",
    ]
    sol_keywords = ["solana", " sol ", "sol price"]

    signals = {
        "crypto": [],
        "macro": [],
        "crisis": [],
        "sol_specific": [],
        "economics": [],   # Kalshi strength: economic indicators
        "weather": [],      # Kalshi unique: weather contracts
    }

    economics_keywords = [
        "gdp", "unemployment", "jobs", "nonfarm", "cpi", "pce",
        "retail sales", "housing", "consumer", "manufacturing",
    ]
    weather_keywords = [
        "temperature", "hurricane", "tornado", "snowfall",
        "rainfall", "heat", "cold", "storm", "flood",
    ]

    for m in markets:
        p = parse_market(m)
        q = p["title"].lower()

        signal = {
            "ticker": p["ticker"],
            "question": p["title"],
            "yes_pct": p["yes_pct"],
            "no_pct": p["no_pct"],
            "volume": p["volume"],
            "open_interest": p["open_interest"],
            "close_time": p["close_time"],
            "confidence": "high" if p["volume"] > 1000 else "medium" if p["volume"] > 100 else "low",
            "source": "kalshi",
        }

        if any(kw in q for kw in sol_keywords):
            signals["sol_specific"].append(signal)
        if any(kw in q for kw in crypto_keywords):
            signals["crypto"].append(signal)
        if any(kw in q for kw in macro_keywords):
            signals["macro"].append(signal)
        if any(kw in q for kw in crisis_keywords):
            signals["crisis"].append(signal)
        if any(kw in q for kw in economics_keywords):
            signals["economics"].append(signal)
        if any(kw in q for kw in weather_keywords):
            signals["weather"].append(signal)

    # Sort by volume
    for cat in signals:
        signals[cat].sort(key=lambda x: x["volume"], reverse=True)

    return signals


def derive_sentiment(signals):
    """Derive actionable sentiment from Kalshi signals."""
    sentiment = {
        "crypto_bullish": 0.5,
        "macro_risk": 0.5,
        "crisis_level": 0.0,
        "sol_outlook": 0.5,
        "fed_hawkish": 0.5,     # Kalshi unique: Fed policy prediction
        "recession_prob": 0.0,  # Kalshi unique: recession probability
        "reasoning": [],
    }

    # Crypto sentiment
    crypto = signals.get("crypto", [])
    if crypto:
        avg = sum(s["yes_pct"] for s in crypto[:10]) / min(len(crypto), 10)
        sentiment["crypto_bullish"] = round(avg / 100, 3)

    # SOL-specific
    sol = signals.get("sol_specific", [])
    if sol:
        avg = sum(s["yes_pct"] for s in sol[:5]) / min(len(sol), 5)
        sentiment["sol_outlook"] = round(avg / 100, 3)

    # Macro/economics -- Kalshi's strength
    econ = signals.get("economics", []) + signals.get("macro", [])
    if econ:
        # Look for specific indicators
        for sig in econ:
            q = sig["question"].lower()
            if "recession" in q:
                sentiment["recession_prob"] = sig["yes_pct"] / 100
                if sig["yes_pct"] > 50:
                    sentiment["reasoning"].append(
                        f"Kalshi: recession probability at {sig['yes_pct']}%")
            if "fed" in q and ("cut" in q or "lower" in q):
                sentiment["fed_hawkish"] = 1.0 - (sig["yes_pct"] / 100)
                if sig["yes_pct"] > 60:
                    sentiment["reasoning"].append(
                        f"Kalshi: Fed rate cut expected ({sig['yes_pct']}%) -- bullish for crypto")
            if "fed" in q and ("hike" in q or "raise" in q or "increase" in q):
                sentiment["fed_hawkish"] = sig["yes_pct"] / 100
                if sig["yes_pct"] > 50:
                    sentiment["reasoning"].append(
                        f"Kalshi: Fed rate hike expected ({sig['yes_pct']}%) -- bearish for crypto")

    # Crisis
    crisis = signals.get("crisis", [])
    if crisis:
        max_crisis = max(s["yes_pct"] for s in crisis[:5])
        sentiment["crisis_level"] = round(max_crisis / 100, 3)
        if max_crisis > 70:
            sentiment["reasoning"].append(
                f"Kalshi: active crisis signal at {max_crisis}%")

    if not sentiment["reasoning"]:
        sentiment["reasoning"].append("Kalshi data processed -- no strong directional signals")

    return sentiment


def merge_with_polymarket(kalshi_sentiment, kalshi_signals):
    """
    Merge Kalshi intelligence with existing Polymarket feed.

    Cross-validation: when both sources agree, confidence doubles.
    """
    intel_path = DATA / "prediction_intelligence.json"
    existing = _load(intel_path)

    if not existing or "sentiment" not in existing:
        # No Polymarket data -- Kalshi is sole source
        return kalshi_sentiment

    poly_sentiment = existing["sentiment"]

    merged = {
        "crypto_bullish": round(
            (poly_sentiment.get("crypto_bullish", 0.5) + kalshi_sentiment["crypto_bullish"]) / 2, 3),
        "macro_risk": round(
            (poly_sentiment.get("macro_risk", 0.5) + kalshi_sentiment["macro_risk"]) / 2, 3),
        "crisis_level": round(
            max(poly_sentiment.get("crisis_level", 0), kalshi_sentiment["crisis_level"]), 3),
        "sol_outlook": round(
            (poly_sentiment.get("sol_outlook", 0.5) + kalshi_sentiment["sol_outlook"]) / 2, 3),
        "fed_hawkish": kalshi_sentiment.get("fed_hawkish", 0.5),
        "recession_prob": kalshi_sentiment.get("recession_prob", 0.0),
        "sources": ["polymarket", "kalshi"],
        "cross_validated": True,
        "reasoning": [],
    }

    # Cross-validation logic
    poly_crypto = poly_sentiment.get("crypto_bullish", 0.5)
    kalshi_crypto = kalshi_sentiment["crypto_bullish"]

    if abs(poly_crypto - kalshi_crypto) < 0.15:
        merged["reasoning"].append(
            f"CONFIRMED: Both sources agree on crypto sentiment "
            f"(Poly={poly_crypto:.0%}, Kalshi={kalshi_crypto:.0%})")
    else:
        merged["reasoning"].append(
            f"DIVERGENCE: Polymarket={poly_crypto:.0%} vs Kalshi={kalshi_crypto:.0%} "
            f"on crypto -- investigate")

    # Determine action
    if merged["sol_outlook"] > 0.65 and merged["crypto_bullish"] > 0.6:
        merged["recommended_action"] = "accumulate"
    elif merged["crisis_level"] > 0.7 or merged["sol_outlook"] < 0.35:
        merged["recommended_action"] = "reduce_exposure"
    elif merged["recession_prob"] > 0.6:
        merged["recommended_action"] = "defensive"
        merged["reasoning"].append("Recession probability elevated -- defensive positioning")
    else:
        merged["recommended_action"] = "follow_base_strategy"

    # Add reasoning from both sources
    merged["reasoning"].extend(
        [f"[Poly] {r}" for r in poly_sentiment.get("reasoning", [])])
    merged["reasoning"].extend(
        [f"[Kalshi] {r}" for r in kalshi_sentiment.get("reasoning", [])])

    return merged


def run():
    """Engine entry point for OMNIBUS."""
    print("[KALSHI] Scanning CFTC-regulated prediction markets...")

    # 1. Check exchange status
    status = check_exchange_status()

    # 2. Fetch markets
    print("[KALSHI] Fetching active markets...")
    markets, cursor = get_markets(limit=200)
    print(f"  [KALSHI] Retrieved {len(markets)} markets")

    if not markets:
        print("[KALSHI] No markets retrieved -- exchange may be down")
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "protocol": "kalshi-scanner-v1",
            "exchange_status": status,
            "markets_scanned": 0,
            "status": "no_data",
        }
        _save(DATA / "kalshi_scan.json", state)
        return state

    # 3. Extract intelligence
    print("[KALSHI] Extracting intelligence signals...")
    signals = extract_intelligence(markets)
    sentiment = derive_sentiment(signals)

    # 4. Merge with Polymarket for cross-validation
    print("[KALSHI] Cross-validating with Polymarket feed...")
    merged_sentiment = merge_with_polymarket(sentiment, signals)

    # 5. Update the shared intelligence feed
    intel_path = DATA / "prediction_intelligence.json"
    existing_intel = _load(intel_path)

    updated_intel = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sources": ["polymarket", "kalshi"],
        "markets_analyzed": existing_intel.get("markets_analyzed", 0) + len(markets),
        "signals": {
            "polymarket": existing_intel.get("signals", {}),
            "kalshi": {
                "crypto_markets": len(signals["crypto"]),
                "macro_markets": len(signals["macro"]),
                "economics_markets": len(signals["economics"]),
                "crisis_markets": len(signals["crisis"]),
                "sol_specific": len(signals["sol_specific"]),
                "weather_markets": len(signals["weather"]),
            },
        },
        "sentiment": merged_sentiment,
        "top_crypto_signals": existing_intel.get("top_crypto_signals", []),
        "top_macro_signals": existing_intel.get("top_macro_signals", []),
        "sol_signals": existing_intel.get("sol_signals", []),
        "crisis_signals": existing_intel.get("crisis_signals", []),
        "kalshi_crypto": signals["crypto"][:10],
        "kalshi_macro": signals["macro"][:10],
        "kalshi_economics": signals["economics"][:10],
        "kalshi_weather": signals["weather"][:5],
    }

    _save(intel_path, updated_intel)

    # 6. Save Kalshi-specific scan
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "kalshi-scanner-v1",
        "exchange_status": status,
        "markets_scanned": len(markets),
        "signals_found": {k: len(v) for k, v in signals.items()},
        "kalshi_sentiment": sentiment,
        "merged_sentiment": merged_sentiment,
        "top_signals": {
            "crypto": signals["crypto"][:5],
            "economics": signals["economics"][:5],
            "macro": signals["macro"][:5],
        },
    }
    _save(DATA / "kalshi_scan.json", state)

    # Summary
    print(f"[KALSHI] Scanned {len(markets)} markets:")
    for cat, sigs in signals.items():
        if sigs:
            print(f"  {cat}: {len(sigs)} signals")
    print(f"[KALSHI] Merged sentiment: {merged_sentiment.get('recommended_action', 'N/A')}")
    print(f"  crypto={merged_sentiment.get('crypto_bullish', '?')}, "
          f"sol={merged_sentiment.get('sol_outlook', '?')}, "
          f"recession={merged_sentiment.get('recession_prob', '?')}")
    if merged_sentiment.get("cross_validated"):
        print(f"[KALSHI] Cross-validated with Polymarket -- dual-source intelligence active")

    return state


if __name__ == "__main__":
    run()
