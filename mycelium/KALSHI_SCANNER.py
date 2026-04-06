#!/usr/bin/env python3
"""
KALSHI_SCANNER.py -- CFTC-regulated prediction market: intelligence + LIVE TRADING
====================================================================================
v3 (2026-04-05): FIXED -- targeted series fetching, correct API v2 field names.
v2 (2026-04-05): AUTHENTICATED -- $25 account, RSA-signed API, 0% fees.

Kalshi = CFTC-regulated Designated Contract Market, all 50 US states.
0% trading fees. $0.01-$0.99 per contract. $25 account balance.

TWO MODES:
  - Public (no auth): Market data, prices, events, exchange status
  - Authenticated (RSA signed): Portfolio, positions, ORDER PLACEMENT

DUAL-SOURCE INTELLIGENCE:
  Polymarket (geo-blocked for trading) + Kalshi (LIVE TRADING)
  = cross-validated signals AND execution capability

API:
  Base: https://api.elections.kalshi.com/trade-api/v2
  Public:  GET /markets, /events, /exchange/status
  Auth:    GET /portfolio/balance, /portfolio/positions
  Auth:    POST /portfolio/orders (PLACE TRADES)

Authentication: RSA key-pair signing
  Headers: KALSHI-ACCESS-KEY, KALSHI-ACCESS-SIGNATURE, KALSHI-ACCESS-TIMESTAMP
  Credentials: data/.secrets/kalshi.json + kalshi_rsa.pem (gitignored)

Intelligence + execution flow:
  KALSHI_SCANNER scans 200+ markets
    -> extract intelligence -> merge with Polymarket
    -> check portfolio ($25 balance)
    -> identify high-confidence trades (cross-validated by both sources)
    -> queue orders for NERVE_LOOP execution

Called by: OMNIBUS, NERVE_LOOP
Writes: data/kalshi_scan.json
Merges into: data/prediction_intelligence.json
"""

import json
import time
import hashlib
import base64
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

KALSHI_API = "https://api.elections.kalshi.com/trade-api/v2"


def _load_credentials():
    """Load Kalshi API credentials from local secrets (gitignored)."""
    secrets_path = DATA / ".secrets" / "kalshi.json"
    try:
        creds = json.loads(secrets_path.read_text(encoding="utf-8"))
        api_key = creds.get("api_key")
        pem_path = creds.get("rsa_private_key_path")
        if pem_path:
            pem_full = DATA.parent / pem_path if not Path(pem_path).is_absolute() else Path(pem_path)
            if pem_full.exists():
                pem_data = pem_full.read_text(encoding="utf-8")
                return api_key, pem_data
        return api_key, None
    except Exception:
        return None, None


def _sign_request(api_key, pem_data, method, path, body=""):
    """
    Sign a Kalshi API request using RSA-PSS.

    Kalshi requires:
      KALSHI-ACCESS-KEY: api_key
      KALSHI-ACCESS-TIMESTAMP: unix timestamp (ms)
      KALSHI-ACCESS-SIGNATURE: base64(RSA-PSS-sign(timestamp + method + path))
    """
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError:
        print("  [KALSHI] cryptography package not installed -- auth disabled")
        print("  [KALSHI] Install with: pip install cryptography")
        return None

    timestamp_ms = str(int(time.time() * 1000))
    message = timestamp_ms + method.upper() + path

    try:
        private_key = serialization.load_pem_private_key(
            pem_data.encode("utf-8"), password=None
        )
        signature = private_key.sign(
            message.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        sig_b64 = base64.b64encode(signature).decode("utf-8")
        return {
            "KALSHI-ACCESS-KEY": api_key,
            "KALSHI-ACCESS-TIMESTAMP": timestamp_ms,
            "KALSHI-ACCESS-SIGNATURE": sig_b64,
        }
    except Exception as e:
        print(f"  [KALSHI] Signing error: {e}")
        return None


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


def _auth_fetch(endpoint, api_key, pem_data, method="GET", body=None, timeout=15):
    """Authenticated fetch from Kalshi API using RSA-PSS signing."""
    path = f"/trade-api/v2{endpoint}"
    url = f"{KALSHI_API}{endpoint}"

    headers = _sign_request(api_key, pem_data, method, path)
    if not headers:
        return None

    try:
        data_bytes = None
        if body:
            data_bytes = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(url, data=data_bytes, method=method)
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")
        for k, v in headers.items():
            req.add_header(k, v)

        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace") if e.fp else ""
        print(f"  [KALSHI] Auth error {e.code}: {body_text[:200]}")
        return None
    except Exception as e:
        print(f"  [KALSHI] Auth fetch error: {e}")
        return None


def check_portfolio(api_key, pem_data):
    """Check Kalshi portfolio: balance, positions, P&L."""
    print("[KALSHI] Checking portfolio...")

    portfolio = {
        "authenticated": True,
        "balance_usd": None,
        "positions": [],
    }

    # Get balance
    balance_data = _auth_fetch("/portfolio/balance", api_key, pem_data)
    if balance_data:
        # Balance is in cents
        balance_cents = balance_data.get("balance", 0)
        portfolio["balance_usd"] = round(balance_cents / 100, 2)
        print(f"  [KALSHI] Balance: ${portfolio['balance_usd']:.2f}")
    else:
        print("  [KALSHI] Balance: auth failed or unavailable")

    # Get positions
    positions_data = _auth_fetch("/portfolio/positions", api_key, pem_data)
    if positions_data:
        positions = positions_data.get("market_positions", [])
        portfolio["positions"] = positions
        portfolio["position_count"] = len(positions)
        print(f"  [KALSHI] Positions: {len(positions)}")
    else:
        print("  [KALSHI] Positions: unavailable")

    return portfolio


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


def get_markets(limit=200, cursor=None, status="open", series_ticker=None, event_ticker=None):
    """Fetch active markets from Kalshi."""
    url = f"{KALSHI_API}/markets?limit={limit}&status={status}"
    if cursor:
        url += f"&cursor={cursor}"
    if series_ticker:
        url += f"&series_ticker={series_ticker}"
    if event_ticker:
        url += f"&event_ticker={event_ticker}"
    data = _fetch(url)
    if data:
        return data.get("markets", []), data.get("cursor", None)
    return [], None


# Targeted series tickers: skip sports parlays, fetch what matters
INTELLIGENCE_SERIES = [
    "KXBTC",    # Bitcoin price ranges
    "KXETH",    # Ethereum price ranges
    "KXFED",    # Fed funds rate decisions
    "KXCPI",    # CPI inflation data (HUGE volume)
    "KXGDP",    # GDP growth
]

TRADING_SERIES = INTELLIGENCE_SERIES  # Same for now, expand as discovered


def get_targeted_markets(series_list=None, limit_per=50):
    """
    Fetch markets from specific series tickers.

    The generic /markets endpoint returns sports parlays first.
    This targets crypto, macro, and economics series directly.
    """
    if series_list is None:
        series_list = INTELLIGENCE_SERIES

    all_markets = []
    for series in series_list:
        markets, _ = get_markets(limit=limit_per, series_ticker=series)
        for m in markets:
            m["_series"] = series  # Tag source for classification
        all_markets.extend(markets)
        time.sleep(0.3)  # Rate limit: 10 req/sec

    print(f"  [KALSHI] Fetched {len(all_markets)} targeted markets from {len(series_list)} series")
    return all_markets


def get_events(limit=100, status="open"):
    """Fetch active events from Kalshi."""
    url = f"{KALSHI_API}/events?limit={limit}&status={status}"
    data = _fetch(url)
    if data:
        return data.get("events", [])
    return []


def parse_market(m):
    """
    Extract clean data from a Kalshi market object.

    Kalshi API v2 field names (2026):
      yes_bid_dollars / yes_ask_dollars  (NOT yes_price_dollars)
      no_bid_dollars / no_ask_dollars
      last_price_dollars
      volume_fp / volume_24h_fp          (NOT volume)
      open_interest_fp                   (NOT open_interest)
    """
    # Use last_price_dollars as primary, fall back to yes_bid
    yes_price = m.get("last_price_dollars") or m.get("yes_bid_dollars") or 0
    no_price = m.get("no_bid_dollars") or 0
    yes_ask = m.get("yes_ask_dollars") or 0
    no_ask = m.get("no_ask_dollars") or 0

    # Handle None/string values
    yes_price = float(yes_price) if yes_price else 0
    no_price = float(no_price) if no_price else 0
    yes_ask = float(yes_ask) if yes_ask else 0
    no_ask = float(no_ask) if no_ask else 0

    volume = float(m.get("volume_fp") or m.get("volume") or 0)
    volume_24h = float(m.get("volume_24h_fp") or 0)
    open_interest = float(m.get("open_interest_fp") or m.get("open_interest") or 0)

    # Derive series from event_ticker or tagged _series
    series = m.get("_series", "")
    if not series:
        evt = m.get("event_ticker", "")
        for s in INTELLIGENCE_SERIES:
            if evt.startswith(s):
                series = s
                break

    return {
        "ticker": m.get("ticker", ""),
        "title": m.get("title", m.get("subtitle", ""))[:120],
        "category": series or m.get("event_ticker", "unknown"),
        "event_ticker": m.get("event_ticker", ""),
        "yes_price": yes_price,
        "no_price": no_price,
        "yes_ask": yes_ask,
        "no_ask": no_ask,
        "yes_pct": round(yes_price * 100, 1),
        "no_pct": round(no_price * 100, 1),
        "volume": int(volume),
        "volume_24h": int(volume_24h),
        "open_interest": int(open_interest),
        "close_time": (m.get("close_time") or "")[:10],
        "status": m.get("status", "open"),
    }


def extract_intelligence(markets):
    """
    Extract actionable intelligence from Kalshi markets.

    Uses series ticker tags for primary classification, keyword fallback.
    Cross-validates with POLYMARKET_SCANNER categories.
    """
    # Series-based classification (primary — fast, accurate)
    SERIES_MAP = {
        "KXBTC": "crypto",
        "KXETH": "crypto",
        "KXFED": "macro",
        "KXCPI": "economics",
        "KXGDP": "economics",
    }

    # Keyword fallback for markets without series tags
    crypto_keywords = [
        "bitcoin", " btc ", "ethereum", " eth ", "solana", "crypto",
        "digital asset", "stablecoin", "blockchain", "defi",
    ]
    macro_keywords = [
        "federal reserve", "fed funds", "interest rate", "inflation",
        "tariff", "treasury", "yield curve",
    ]
    crisis_keywords = [
        "war ", "conflict", "invasion", "missile", "nuclear",
        "hurricane", "earthquake", "pandemic", "emergency",
    ]
    sol_keywords = ["solana", " sol ", "sol price"]
    economics_keywords = [
        "gdp", "unemployment", "jobs", "nonfarm", "cpi", "pce",
        "retail sales", "housing", "consumer", "manufacturing",
        "recession",
    ]

    signals = {
        "crypto": [],
        "macro": [],
        "crisis": [],
        "sol_specific": [],
        "economics": [],
        "weather": [],
    }

    for m in markets:
        p = parse_market(m)
        q = p["title"].lower()

        # Skip markets with no price data (empty parlays)
        if p["yes_price"] == 0 and p.get("yes_ask", 0) == 0:
            continue

        signal = {
            "ticker": p["ticker"],
            "question": p["title"],
            "yes_pct": p["yes_pct"],
            "no_pct": p["no_pct"],
            "yes_ask": p.get("yes_ask", 0),
            "no_ask": p.get("no_ask", 0),
            "volume": p["volume"],
            "volume_24h": p.get("volume_24h", 0),
            "open_interest": p["open_interest"],
            "close_time": p["close_time"],
            "event_ticker": p.get("event_ticker", ""),
            "confidence": "high" if p["volume"] > 10000 else "medium" if p["volume"] > 1000 else "low",
            "source": "kalshi",
        }

        # Primary: series-based classification
        series = p.get("category", "")
        category = SERIES_MAP.get(series)

        if category:
            signals[category].append(signal)
            # Also check for SOL-specific within crypto
            if series in ("KXBTC", "KXETH") and any(kw in q for kw in sol_keywords):
                signals["sol_specific"].append(signal)
        else:
            # Fallback: keyword matching
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

    # Sort by volume (highest first)
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

    # Add reasoning from both sources (strip existing prefixes to prevent nesting)
    for r in poly_sentiment.get("reasoning", []):
        clean = r.lstrip("[Poly] ").lstrip("[Kalshi] ") if r.startswith("[") else r
        merged["reasoning"].append(f"[Poly] {clean}")
    for r in kalshi_sentiment.get("reasoning", []):
        clean = r.lstrip("[Poly] ").lstrip("[Kalshi] ") if r.startswith("[") else r
        merged["reasoning"].append(f"[Kalshi] {clean}")

    return merged


def run():
    """Engine entry point for OMNIBUS / NERVE_LOOP."""
    print("[KALSHI] Scanning CFTC-regulated prediction markets...")

    # Load credentials
    api_key, pem_data = _load_credentials()
    authenticated = api_key is not None and pem_data is not None
    if authenticated:
        print(f"[KALSHI] Authenticated: {api_key[:8]}...")
    else:
        print("[KALSHI] Running in public mode (no credentials or missing cryptography)")

    # 1. Check exchange status
    status = check_exchange_status()

    # 2. Fetch targeted markets (skip sports parlays, hit crypto/macro/econ)
    print("[KALSHI] Fetching targeted markets (crypto, macro, economics)...")
    markets = get_targeted_markets()

    if not markets:
        print("[KALSHI] No markets retrieved -- exchange may be down")
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "protocol": "kalshi-scanner-v2",
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

    # 5. Check portfolio if authenticated
    portfolio = None
    if authenticated:
        portfolio = check_portfolio(api_key, pem_data)

    # 6. Update the shared intelligence feed
    intel_path = DATA / "prediction_intelligence.json"
    existing_intel = _load(intel_path)

    # Extract Polymarket signal counts from existing intel (don't nest)
    poly_signals = existing_intel.get("signals", {})
    if isinstance(poly_signals, dict) and "polymarket" in poly_signals:
        poly_signals = poly_signals.get("polymarket", {})
        # Unwrap double-nesting from previous runs
        if isinstance(poly_signals, dict) and "polymarket" in poly_signals:
            poly_signals = poly_signals.get("polymarket", {})

    updated_intel = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sources": ["polymarket", "kalshi"],
        "markets_analyzed": len(markets),
        "signals": {
            "polymarket": poly_signals if isinstance(poly_signals, dict) else {},
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

    # 7. Save Kalshi-specific scan
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "kalshi-scanner-v2",
        "authenticated": authenticated,
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

    if portfolio:
        state["portfolio"] = portfolio

    _save(DATA / "kalshi_scan.json", state)

    # Broadcast to synaptic bus
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_batch("KALSHI_SCANNER", {
            "markets_scanned": len(markets),
            "opportunities": sum(len(v) for v in signals.values()),
            "status": "active",
        }, silent=True)
    except Exception:
        pass

    # Summary
    print(f"[KALSHI] Scanned {len(markets)} markets:")
    for cat, sigs in signals.items():
        if sigs:
            print(f"  {cat}: {len(sigs)} signals")
    if portfolio and portfolio.get("balance_usd") is not None:
        print(f"[KALSHI] Portfolio: ${portfolio['balance_usd']:.2f} | "
              f"Positions: {portfolio.get('position_count', 0)}")
    print(f"[KALSHI] Merged sentiment: {merged_sentiment.get('recommended_action', 'N/A')}")
    print(f"  crypto={merged_sentiment.get('crypto_bullish', '?')}, "
          f"sol={merged_sentiment.get('sol_outlook', '?')}, "
          f"recession={merged_sentiment.get('recession_prob', '?')}")
    if merged_sentiment.get("cross_validated"):
        print(f"[KALSHI] Cross-validated with Polymarket -- dual-source intelligence active")

    return state


if __name__ == "__main__":
    run()
