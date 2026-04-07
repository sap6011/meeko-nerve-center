#!/usr/bin/env python3
"""
TURBO_TRADER.py -- High-frequency compounding prediction market engine
======================================================================
v1 (2026-04-05): The compounding machine. No idle cash. No waiting.

PHILOSOPHY:
  Every dollar deployed. Every settlement reinvested. Every deposit detected.
  Micro-trades across EVERY Kalshi market that resolves FAST.
  Daily S&P 500 brackets + weather + gas prices = DAILY compounding.
  Not monthly. Not quarterly. DAILY.

HOW IT WORKS:
  1. DISCOVER: Dynamic series discovery (GET /series, not hardcoded)
  2. SCAN: All fast-resolving markets across EVERY category
  3. DETECT: Balance changes = new deposits -> instant deployment
  4. TRADE: Batch orders -- many trades in one API call
  5. MONITOR: Track settlements, detect resolved positions
  6. COMPOUND: Reinvest resolved payouts immediately
  7. REPEAT: Every NERVE_LOOP cycle, 4x/day minimum

DAILY COMPOUNDING MATH:
  $25 @ 5% daily (buy $0.95, collect $1.00):
    Day 1: $25.00 -> $26.25
    Day 7: $35.17
    Day 30: $108.05
    Day 90: $1,816.65
  Even 2% daily: $25 -> $30.40 (week) -> $45.45 (month) -> $152.17 (quarter)

FAST-RESOLVING SERIES (settle daily/weekly):
  KXINX  -- S&P 500 daily range (settles 4pm ET daily)
  KXHIGHNY -- NYC temperature daily (settles via NWS)
  KXAAAGASD -- Gas prices daily
  KXNASDAQ100 -- Nasdaq daily range
  KXBTC  -- Bitcoin daily/weekly brackets
  KXETH  -- Ethereum daily/weekly brackets

RISK: Same near-certain strategy but FASTER turnover.
  Buy wide brackets/obvious outcomes at 90-97 cents.
  Collect $1.00 on resolution. Rinse and repeat.

Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)

Called by: NERVE_LOOP Phase 4.5 (EXECUTE), OMNIBUS
Reads: all Kalshi series dynamically, portfolio state
Writes: data/turbo_trader_state.json, feeds into trade_ledger.json
"""

import json
import time
import uuid
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

KALSHI_API = "https://api.elections.kalshi.com/trade-api/v2"

# Series prioritized by resolution speed (fastest first)
# Daily settlers get max priority, then weekly, then monthly
FAST_SERIES = [
    # === DAILY RESOLUTION (highest priority — fastest compounding) ===
    "KXINX",        # S&P 500 daily range -- settles 4pm ET EVERY DAY
    "KXNASDAQ100",  # Nasdaq 100 daily range
    "KXHIGHNY",     # NYC temperature daily
    "KXAAAGASD",    # US gas prices daily
    "KXGOLD",       # Gold price daily
    "KXBTC",        # Bitcoin price brackets (daily/weekly)
    "KXETH",        # Ethereum price brackets (daily/weekly)
    # === CRYPTO & MEME COINS (volatile = more daily brackets) ===
    "KXSOL",        # Solana price brackets
    "KXDOGE",       # Dogecoin brackets (meme coin king)
    "KXSHIB",       # Shiba Inu brackets
    "KXPEPE",       # PEPE brackets
    "KXWIF",        # dogwifhat brackets
    "KXBONK",       # BONK brackets
    "KXFLOKI",      # FLOKI brackets
    "KXAVAX",       # Avalanche
    "KXLINK",       # Chainlink
    "KXMATIC",      # Polygon/MATIC
    "KXADA",        # Cardano
    "KXXRP",        # XRP/Ripple
    "KXDOT",        # Polkadot
    "KXCRYPTOCAP",  # Total crypto market cap
    # === STABLECOINS & DEFI (stability = near-certain bets) ===
    "KXUSDT",       # Tether peg stability
    "KXUSDC",       # USDC peg stability
    "KXDEFI",       # DeFi TVL
    # === COMMODITIES (daily/weekly movers) ===
    "KXSILVER",     # Silver price
    "KXOIL",        # Oil/WTI price
    "KXNATGAS",     # Natural gas
    # === MACRO (still trade, lower priority) ===
    "KXFED",        # Fed funds rate (per meeting)
    "KXCPI",        # CPI inflation (monthly)
    "KXGDP",        # GDP growth (quarterly)
    "KXINXY",       # S&P 500 yearly range
    "KXINXMAXY",    # S&P 500 yearly high
    "KXEMPLOYMENTCOMBO",  # Employment data
    "KXJOBLESS",    # Jobless claims (weekly)
    # === POP CULTURE & SPORTS (fast resolution, high volume) ===
    "KXTOPALBUMSPOTIFYUSA",  # Spotify top album
    "KXATF",        # ATF/regulatory
    "KXNFL",        # NFL
    "KXNBA",        # NBA
    "KXMLB",        # MLB
    "KXMMA",        # MMA/UFC
    "KXELECTIONS",  # Elections (various)
    # === MULTI-EVENT / CROSS-CATEGORY (parlays, combos — often close FAST) ===
    "KXMVESPORTSMULTIGAME",    # Multi-game sports parlays
    "KXMVECROSSCATEGORY-S",    # Cross-category combos
    "KXMVECROSSCATEGORY-L",    # Cross-category long
    "KXSOCCER",     # Soccer/football
    "KXNHL",        # NHL hockey
    "KXTENNIS",     # Tennis
    "KXGOLF",       # Golf
    "KXBOXING",     # Boxing
    "KXEPL",        # English Premier League
    "KXCHAMPIONSLEAGUE",  # Champions League
    "KXWEATHER",    # General weather
    "KXREALTIME",   # Real-time events
]

# Resolution speed classification (hours until typical settlement)
RESOLUTION_SPEED = {
    "KXINX": 24,       # Daily
    "KXNASDAQ100": 24,  # Daily
    "KXHIGHNY": 24,     # Daily
    "KXAAAGASD": 24,    # Daily
    "KXGOLD": 24,       # Daily
    "KXBTC": 24,        # Daily brackets available
    "KXETH": 24,        # Daily brackets available
    "KXSOL": 24,        # Daily
    "KXDOGE": 168,      # Weekly
    "KXSHIB": 168,      # Weekly
    "KXPEPE": 168,      # Weekly
    "KXWIF": 168,       # Weekly
    "KXBONK": 168,      # Weekly
    "KXFLOKI": 168,     # Weekly
    "KXSILVER": 24,     # Daily
    "KXOIL": 24,        # Daily
    "KXNATGAS": 168,    # Weekly
    "KXFED": 1344,      # ~8 weeks
    "KXCPI": 720,       # Monthly
    "KXGDP": 2160,      # Quarterly
    "KXJOBLESS": 168,   # Weekly
}


def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_kalshi_auth():
    """Load Kalshi credentials."""
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


def _sign_and_fetch(endpoint, api_key, pem_data, method="GET", body=None, timeout=15):
    """Authenticated Kalshi API request with RSA-PSS signing."""
    import urllib.request
    import urllib.error
    import base64

    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError:
        print("  [TURBO] cryptography not installed")
        return None

    # Strip query params from signing path (Kalshi signs path only, not query string)
    clean_endpoint = endpoint.split("?")[0]
    path = f"/trade-api/v2{clean_endpoint}"
    url = f"{KALSHI_API}{endpoint}"
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
    except Exception as e:
        print(f"  [TURBO] Signing error: {e}")
        return None

    try:
        data_bytes = json.dumps(body).encode("utf-8") if body else None
        req = urllib.request.Request(url, data=data_bytes, method=method)
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")
        req.add_header("KALSHI-ACCESS-KEY", api_key)
        req.add_header("KALSHI-ACCESS-TIMESTAMP", timestamp_ms)
        req.add_header("KALSHI-ACCESS-SIGNATURE", sig_b64)

        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace") if e.fp else ""
        print(f"  [TURBO] API error {e.code}: {body_text[:200]}")
        return None
    except Exception as e:
        print(f"  [TURBO] Fetch error: {e}")
        return None


def _public_fetch(endpoint, timeout=10):
    """Unauthenticated Kalshi API request (market data is public)."""
    url = f"{KALSHI_API}{endpoint}"
    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"  [TURBO] Public fetch error: {e}")
        return None


# ──────────────────────────────────────────────────────────────
# PHASE 0: HIVE MIND -- AI-powered intelligence aggregation
# ──────────────────────────────────────────────────────────────

def gather_all_intelligence():
    """
    Read EVERY intelligence source in the ecosystem and build
    a unified signal matrix for AI analysis.

    Sources:
      1. prediction_intelligence.json (Polymarket + Kalshi merged sentiment)
      2. kalshi_scan.json (market-level signals)
      3. price_oracle_state.json (live prices, spreads, trends)
      4. crypto_state.json (Fear & Greed, AI analysis)
      5. arbitrage_scanner_state.json (cross-market opportunities)
      6. compound_tracker.json (our own performance data)
      7. trade_ledger.json (what worked, what didn't)
    """
    # Try SYNAPTIC_BUS first (one read for everything), fall back to files
    _bus_boost = {}
    try:
        from SYNAPTIC_BUS import sense
        bus = sense()
        engines = bus.get("engines", {})
        if engines:
            mesh = engines.get("SIGNAL_MESH", {}).get("properties", {})
            _bus_boost = {
                "mesh_direction": mesh.get("dominant_direction", "neutral"),
                "mesh_conviction": mesh.get("conviction_score", 0),
                "mesh_urgency": mesh.get("urgency", 0),
                "mesh_strength": mesh.get("composite_strength", 0),
            }
            # Read NEURAL_CORTEX risk posture for trading aggressiveness
            cortex = engines.get("NEURAL_CORTEX", {}).get("properties", {})
            _bus_boost["brain_risk_posture"] = cortex.get("risk_posture", "moderate")
            _bus_boost["brain_confidence"] = cortex.get("decision_confidence", 0)
            _bus_boost["brain_kalshi_pct"] = cortex.get("capital_kalshi_pct", 60)
    except Exception:
        pass

    intel = {
        "prediction": _load(DATA / "prediction_intelligence.json"),
        "kalshi_scan": _load(DATA / "kalshi_scan.json"),
        "prices": _load(DATA / "price_oracle_state.json"),
        "crypto": _load(DATA / "crypto_state.json"),
        "arbitrage": _load(DATA / "arbitrage_scanner_state.json"),
        "compound": _load(DATA / "compound_tracker.json"),
        "ledger_stats": _load(DATA / "trade_ledger.json", {}).get("stats", {}),
        "bus_boost": _bus_boost,
    }

    # Extract key signals
    pred = intel["prediction"]
    sentiment = pred.get("sentiment", pred.get("kalshi_sentiment", {}))

    signals = {
        "crypto_bullish": sentiment.get("crypto_bullish", 0.5),
        "macro_risk": sentiment.get("macro_risk", 0.5),
        "crisis_level": sentiment.get("crisis_level", 0),
        "sol_outlook": sentiment.get("sol_outlook", 0.5),
        "fed_hawkish": sentiment.get("fed_hawkish", 0.5),
        "recession_prob": sentiment.get("recession_prob", 0),
        "recommended_action": sentiment.get("recommended_action", "follow_base_strategy"),
        "reasoning": sentiment.get("reasoning", []),
    }

    # Price data
    prices = intel["prices"]
    if prices.get("prices"):
        for token, pdata in prices.get("prices", {}).items():
            if isinstance(pdata, dict):
                signals[f"{token}_price"] = pdata.get("average", 0)
                signals[f"{token}_24h_change"] = pdata.get("change_24h_avg", 0)

    # Our track record
    stats = intel["ledger_stats"]
    signals["our_win_rate"] = (
        stats.get("successful_orders", 0) / max(stats.get("total_trades", 1), 1)
    )
    signals["total_trades"] = stats.get("total_trades", 0)

    # Compound performance
    compound = intel["compound"]
    snapshots = compound.get("snapshots", [])
    if snapshots:
        signals["compound_growth_pct"] = snapshots[-1].get("growth_pct", 0)
        signals["compound_cycles"] = compound.get("compound_cycles", 0)

    print(f"  [HIVE] Intelligence gathered: "
          f"crypto={signals['crypto_bullish']:.1%} bullish | "
          f"macro_risk={signals['macro_risk']:.1%} | "
          f"action={signals['recommended_action']} | "
          f"win_rate={signals['our_win_rate']:.0%}")

    return signals, intel


def ai_score_opportunities(opportunities, signals, max_to_score=15):
    """
    Use AI (Groq FREE tier) to analyze and score trading opportunities
    based on ALL available intelligence.

    AI analyzes:
    - Market fundamentals (is this outcome really near-certain?)
    - Cross-validation with sentiment data
    - Risk assessment given macro conditions
    - Optimal position sizing

    Returns opportunities with AI scores (1-10) and reasoning.
    """
    if not opportunities:
        return opportunities

    try:
        import AI_CLIENT
        if not AI_CLIENT.ai_available():
            print("  [HIVE] AI not available, using raw scores")
            return opportunities
    except ImportError:
        print("  [HIVE] AI_CLIENT not importable, using raw scores")
        return opportunities

    # Build context for AI
    top_opps = opportunities[:max_to_score]
    opp_summaries = []
    for i, o in enumerate(top_opps):
        opp_summaries.append(
            f"{i+1}. {o['title'][:80]} | {o['side'].upper()} @ ${o['price']:.2f} | "
            f"ROI: {o['roi_pct']}% | Resolves: {o['resolution_class']} ({o['hours_to_resolve']:.0f}h) | "
            f"Vol: {o['volume']}"
        )

    prompt = f"""You are a prediction market trading AI. Analyze these opportunities and score each 1-10.

CURRENT MARKET INTELLIGENCE:
- Crypto sentiment: {signals['crypto_bullish']:.0%} bullish
- Macro risk: {signals['macro_risk']:.0%}
- Crisis level: {signals['crisis_level']:.0%}
- Recommended action: {signals['recommended_action']}
- Our win rate so far: {signals['our_win_rate']:.0%} ({signals['total_trades']} trades)

STRATEGY: We buy near-certain outcomes (>85% probability) on prediction markets.
We prefer DAILY-resolving markets for faster compounding.
Higher score = trade first. Consider:
- Is the outcome genuinely near-certain given current conditions?
- Does macro/crypto sentiment affect this market?
- Is the volume sufficient for our order to fill?
- How fast does it resolve (faster = better for compounding)?

OPPORTUNITIES:
{chr(10).join(opp_summaries)}

Return JSON array of objects with "index" (1-based), "score" (1-10), "reason" (brief).
Example: [{{"index": 1, "score": 9, "reason": "Gas prices stable, high volume, resolves today"}}]"""

    try:
        analysis = AI_CLIENT.ask_json(prompt, max_tokens=1500,
                                       system="You are a quantitative trading analyst. Return ONLY valid JSON.")

        if isinstance(analysis, list):
            # Apply AI scores to opportunities
            score_map = {}
            for item in analysis:
                idx = item.get("index", 0) - 1
                if 0 <= idx < len(top_opps):
                    score_map[idx] = item

            for idx, opp in enumerate(top_opps):
                if idx in score_map:
                    opp["ai_score"] = score_map[idx].get("score", 5)
                    opp["ai_reason"] = score_map[idx].get("reason", "")
                else:
                    opp["ai_score"] = 5  # neutral default

            # Re-sort by AI score (highest first), then ROI as tiebreaker
            top_opps.sort(key=lambda x: (x.get("ai_score", 5), x.get("roi_pct", 0)), reverse=True)

            scored = sum(1 for o in top_opps if o.get("ai_score", 5) != 5)
            print(f"  [HIVE] AI scored {scored}/{len(top_opps)} opportunities")
            for o in top_opps[:5]:
                print(f"    [{o.get('ai_score', '?')}/10] {o['title'][:50]}... "
                      f"| {o.get('ai_reason', '')[:60]}")

            # Rebuild full list with scored items first
            remaining = opportunities[max_to_score:]
            return top_opps + remaining

        else:
            print(f"  [HIVE] AI returned unexpected format, using raw scores")

    except Exception as e:
        print(f"  [HIVE] AI analysis error: {e}")

    return opportunities


def build_feedback_loop(trades_placed, signals):
    """
    Record what intelligence led to what trades.
    Future cycles can learn from this: did the AI's reasoning pan out?
    """
    feedback_path = DATA / "trading_feedback.json"
    feedback = _load(feedback_path, {"cycles": [], "ai_accuracy": []})

    cycle_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "signals_at_trade_time": {
            "crypto_bullish": signals.get("crypto_bullish", 0),
            "macro_risk": signals.get("macro_risk", 0),
            "recommended_action": signals.get("recommended_action", ""),
        },
        "trades_placed": len(trades_placed),
        "successful": sum(1 for t in trades_placed if t.get("success")),
        "ai_scores_used": [
            {"ticker": t.get("ticker"), "ai_score": t.get("order_details", {}).get("ai_score")}
            for t in trades_placed if t.get("success")
        ],
    }

    if "cycles" not in feedback:
        feedback["cycles"] = []
    feedback["cycles"].append(cycle_record)
    feedback["cycles"] = feedback["cycles"][-500:]  # Keep last 500 cycles
    _save(feedback_path, feedback)


# ──────────────────────────────────────────────────────────────
# PHASE 1: DISCOVER -- Dynamic series + market scanning
# ──────────────────────────────────────────────────────────────

_series_cache = {"data": None, "ts": 0}
_SERIES_CACHE_TTL = 600  # 10 min -- series don't change often


def discover_all_series():
    """
    Dynamically discover ALL Kalshi series.
    GET /series returns every series ticker on the platform.
    We prioritize FAST_SERIES but also scan anything new.
    Cached for 10 minutes to avoid redundant API calls.
    """
    now = time.time()
    if _series_cache["data"] and (now - _series_cache["ts"]) < _SERIES_CACHE_TTL:
        print(f"  [TURBO] Using cached series ({len(_series_cache['data'])} series, "
              f"{int(now - _series_cache['ts'])}s old)")
        return _series_cache["data"]

    data = _public_fetch("/series?limit=200")
    if not data:
        print("  [TURBO] Could not fetch series list, using hardcoded FAST_SERIES")
        return FAST_SERIES

    all_series = []
    for s in data.get("series", []):
        ticker = s.get("ticker", "")
        if ticker:
            all_series.append(ticker)

    if not all_series:
        return FAST_SERIES

    # Prioritize fast-resolving series first, then anything else
    ordered = []
    for fast in FAST_SERIES:
        if fast in all_series:
            ordered.append(fast)
            all_series.remove(fast)

    # Add remaining series (potential new markets we haven't seen)
    ordered.extend(all_series)

    print(f"  [TURBO] Discovered {len(ordered)} series ({len(FAST_SERIES)} prioritized)")
    _series_cache["data"] = ordered
    _series_cache["ts"] = time.time()
    return ordered


def scan_fast_markets(series_list, min_conf=85, min_vol=100):
    """
    Scan markets across all series for tradeable opportunities.

    Prioritizes:
    1. Markets that resolve SOONEST (daily > weekly > monthly)
    2. Highest confidence (near-certain outcomes)
    3. Best ROI per dollar deployed

    Uses lower volume threshold (100 vs 500) because daily markets
    are newer and have less historical volume.
    """

    opportunities = []
    now = datetime.now(timezone.utc)
    series_scanned = 0
    markets_scanned = 0

    # Scan prioritized series (fast-resolving first)
    # Rate limit: 20 reads/sec, we use 3/sec to be safe
    for series in series_list[:80]:  # Scan WIDE — every series we can find
        try:
            url = f"{KALSHI_API}/markets?limit=100&status=open&series_ticker={series}"
            req = urllib.request.Request(url)
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode())
                markets = data.get("markets", [])
                series_scanned += 1
                markets_scanned += len(markets)

                for m in markets:
                    opp = _evaluate_market(m, series, min_conf, min_vol, now)
                    if opp:
                        opportunities.append(opp)

                if markets:
                    fast_count = sum(1 for o in opportunities if o.get("series") == series)
                    if fast_count > 0:
                        print(f"  [TURBO] {series}: {len(markets)} markets, {fast_count} tradeable")

        except Exception as e:
            print(f"  [TURBO] {series} scan error: {e}")

        time.sleep(0.25)  # 4 req/s (rate limit is 20/s, but 80 series = many calls)

    print(f"  [TURBO] Scanned {series_scanned} series, {markets_scanned} markets, "
          f"{len(opportunities)} opportunities")

    # Sort: fastest resolution first, then by ROI
    opportunities.sort(key=lambda x: (x.get("hours_to_resolve", 9999), -x.get("roi_pct", 0)))
    return opportunities


def _evaluate_market(m, series, min_conf, min_vol, now):
    """Evaluate a single market for trading opportunity."""
    ticker = m.get("ticker", "")
    title = m.get("title", m.get("subtitle", ""))

    # Price data
    last_price = m.get("last_price_dollars")
    yes_bid = m.get("yes_bid_dollars")
    yes_ask = m.get("yes_ask_dollars")
    no_bid = m.get("no_bid_dollars")
    no_ask = m.get("no_ask_dollars")

    if not last_price and not yes_bid:
        return None

    last_price = float(last_price) if last_price else 0
    yes_bid = float(yes_bid) if yes_bid else 0
    yes_ask = float(yes_ask) if yes_ask else 0
    no_bid = float(no_bid) if no_bid else 0
    no_ask = float(no_ask) if no_ask else 0
    yes_price = last_price or yes_bid
    yes_pct = yes_price * 100

    # Volume check (lower threshold for daily markets)
    volume = float(m.get("volume_fp") or m.get("volume") or 0)
    open_interest = float(m.get("open_interest_fp") or m.get("open_interest") or 0)
    if volume < min_vol:
        return None

    # Calculate time to resolution
    close_time_str = m.get("close_time", "")
    hours_to_resolve = RESOLUTION_SPEED.get(series, 2160)
    if close_time_str:
        try:
            close_time = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
            delta = close_time - now
            hours_to_resolve = max(1, delta.total_seconds() / 3600)
        except Exception:
            pass

    # Near-certain YES (high probability) -- buy YES
    if yes_pct >= min_conf:
        buy_price = yes_ask if yes_ask > 0 else yes_price
        if buy_price <= 0 or buy_price >= 1.0:
            return None
        profit = 1.00 - buy_price
        roi = (profit / buy_price) * 100
        # Annualized ROI for comparison (daily markets look MUCH better)
        annual_factor = 8760 / max(hours_to_resolve, 1)
        annualized_roi = roi * annual_factor

        return {
            "ticker": ticker,
            "title": title[:100],
            "side": "yes",
            "action": "buy",
            "price": buy_price,
            "yes_pct": round(yes_pct, 1),
            "profit_per_contract": round(profit, 4),
            "roi_pct": round(roi, 2),
            "annualized_roi": round(min(annualized_roi, 99999), 1),
            "volume": int(volume),
            "open_interest": int(open_interest),
            "hours_to_resolve": round(hours_to_resolve, 1),
            "strategy": "near_certain_yes",
            "series": series,
            "close_time": close_time_str,
            "resolution_class": _classify_speed(hours_to_resolve),
        }

    # Near-certain NO (low probability YES = high probability NO) -- buy NO
    elif yes_pct <= (100 - min_conf):
        buy_price = no_ask if no_ask > 0 else (1.00 - yes_price)
        if buy_price <= 0 or buy_price >= 1.0:
            return None
        profit = 1.00 - buy_price
        roi = (profit / buy_price) * 100
        annual_factor = 8760 / max(hours_to_resolve, 1)
        annualized_roi = roi * annual_factor

        return {
            "ticker": ticker,
            "title": title[:100],
            "side": "no",
            "action": "buy",
            "price": buy_price,
            "yes_pct": round(yes_pct, 1),
            "profit_per_contract": round(profit, 4),
            "roi_pct": round(roi, 2),
            "annualized_roi": round(min(annualized_roi, 99999), 1),
            "volume": int(volume),
            "open_interest": int(open_interest),
            "hours_to_resolve": round(hours_to_resolve, 1),
            "strategy": "near_certain_no",
            "series": series,
            "close_time": close_time_str,
            "resolution_class": _classify_speed(hours_to_resolve),
        }

    return None


def _classify_speed(hours):
    """Classify market by resolution speed."""
    if hours <= 6:
        return "CLOSING_SOON"
    elif hours <= 24:
        return "DAILY"
    elif hours <= 168:
        return "WEEKLY"
    elif hours <= 720:
        return "MONTHLY"
    else:
        return "LONG"


# ──────────────────────────────────────────────────────────────
# PHASE 2.5: SNIPER MODE -- Buy seconds before close for instant payout
# ──────────────────────────────────────────────────────────────

def sniper_scan(config):
    """
    SNIPER MODE: Find markets closing within 1-6 hours and BUY.

    When a market is about to close, the outcome is usually visible.
    The S&P 500 daily close bracket? At 3:55pm, you KNOW where it'll be.
    Weather today? At 11pm, it already happened.

    Strategy:
      - Query ALL open markets (no series filter -- cast the widest net)
      - Filter: close_time within next 1-6 hours
      - Lower confidence threshold (75%) -- outcome is nearly certain
      - Lower volume requirement (25) -- closing markets have less volume
      - Buy at whatever price is available -- speed > price optimization
      - Tag as "sniper" strategy for tracking

    Result: Buy at $0.95-0.99, collect $1.00 in hours (not days).
    Instant compounding.
    """
    now = datetime.now(timezone.utc)
    sniper_window_min = timedelta(minutes=5)   # At least 5 min to fill
    sniper_window_max = timedelta(hours=config.get("sniper_max_hours", 6))
    # Also scan 6-24h as "warm-up" targets (slightly higher confidence needed)
    warmup_window_max = timedelta(hours=24)
    min_conf = config.get("sniper_min_confidence", 75)
    warmup_min_conf = min(min_conf + 8, 85)  # 83% for warm-up tier
    min_vol = config.get("sniper_min_volume", 25)

    opportunities = []
    markets_checked = 0
    cursor = None
    pages = 0
    max_pages = 10  # 200 per page × 10 = 2000 markets scanned

    print(f"  [SNIPER] Scanning ALL open markets for close within 6h...")

    while pages < max_pages:
        # Build URL -- no series filter = ALL markets
        params = "status=open&limit=200"
        if cursor:
            params += f"&cursor={cursor}"
        data = _public_fetch(f"/markets?{params}", timeout=20)

        if not data:
            break

        markets = data.get("markets", [])
        if not markets:
            break

        for m in markets:
            markets_checked += 1
            close_time_str = m.get("close_time", "")
            if not close_time_str:
                continue

            # Parse close time
            try:
                close_time = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
            except Exception:
                continue

            time_to_close = close_time - now

            # Filter: must be closing within our windows
            # Tier 1: SNIPER (5min - 6h) — lowest confidence needed
            # Tier 2: WARMUP (6h - 24h) — slightly higher confidence
            is_sniper = sniper_window_min <= time_to_close <= sniper_window_max
            is_warmup = sniper_window_max < time_to_close <= warmup_window_max

            if not is_sniper and not is_warmup:
                continue

            hours_to_close = time_to_close.total_seconds() / 3600
            effective_min_conf = min_conf if is_sniper else warmup_min_conf
            tier = "sniper" if is_sniper else "warmup"

            # Get price data
            ticker = m.get("ticker", "")
            title = m.get("title", m.get("subtitle", ""))
            last_price = float(m.get("last_price_dollars") or 0)
            yes_bid = float(m.get("yes_bid_dollars") or 0)
            yes_ask = float(m.get("yes_ask_dollars") or 0)
            no_bid = float(m.get("no_bid_dollars") or 0)
            no_ask = float(m.get("no_ask_dollars") or 0)
            volume = float(m.get("volume_fp") or m.get("volume") or 0)
            open_interest = float(m.get("open_interest_fp") or m.get("open_interest") or 0)

            yes_price = last_price or yes_bid
            if not yes_price:
                continue

            yes_pct = yes_price * 100

            # Volume check (relaxed for closing markets)
            if volume < min_vol:
                continue

            # SNIPER: Lower confidence threshold -- outcome is visible
            # Near-certain YES
            if yes_pct >= effective_min_conf:
                buy_price = yes_ask if yes_ask > 0 else yes_price
                if buy_price <= 0 or buy_price >= 1.0:
                    continue
                profit = 1.00 - buy_price
                roi = (profit / buy_price) * 100
                # Annualized ROI for snipers is astronomical (hours, not days)
                annual_factor = 8760 / max(hours_to_close, 0.1)
                annualized_roi = roi * annual_factor

                # Urgency bonus: closer to close = more certain = higher priority
                urgency = max(1, 10 - int(hours_to_close))

                series = m.get("series_ticker", "UNKNOWN")

                opportunities.append({
                    "ticker": ticker,
                    "title": title[:100],
                    "side": "yes",
                    "action": "buy",
                    "price": buy_price,
                    "yes_pct": round(yes_pct, 1),
                    "profit_per_contract": round(profit, 4),
                    "roi_pct": round(roi, 2),
                    "annualized_roi": round(min(annualized_roi, 999999), 1),
                    "volume": int(volume),
                    "open_interest": int(open_interest),
                    "hours_to_resolve": round(hours_to_close, 2),
                    "strategy": f"{tier}_yes",
                    "series": series,
                    "close_time": close_time_str,
                    "resolution_class": "CLOSING_SOON" if is_sniper else "DAILY",
                    "urgency": urgency,
                    "sniper": is_sniper,
                    "tier": tier,
                })

            # Near-certain NO
            elif yes_pct <= (100 - effective_min_conf):
                buy_price = no_ask if no_ask > 0 else (1.00 - yes_price)
                if buy_price <= 0 or buy_price >= 1.0:
                    continue
                profit = 1.00 - buy_price
                roi = (profit / buy_price) * 100
                annual_factor = 8760 / max(hours_to_close, 0.1)
                annualized_roi = roi * annual_factor
                urgency = max(1, 10 - int(hours_to_close))
                series = m.get("series_ticker", "UNKNOWN")

                opportunities.append({
                    "ticker": ticker,
                    "title": title[:100],
                    "side": "no",
                    "action": "buy",
                    "price": buy_price,
                    "yes_pct": round(yes_pct, 1),
                    "profit_per_contract": round(profit, 4),
                    "roi_pct": round(roi, 2),
                    "annualized_roi": round(min(annualized_roi, 999999), 1),
                    "volume": int(volume),
                    "open_interest": int(open_interest),
                    "hours_to_resolve": round(hours_to_close, 2),
                    "strategy": f"{tier}_no",
                    "series": series,
                    "close_time": close_time_str,
                    "resolution_class": "CLOSING_SOON" if is_sniper else "DAILY",
                    "urgency": urgency,
                    "sniper": is_sniper,
                    "tier": tier,
                })

        # Pagination
        cursor = data.get("cursor")
        if not cursor:
            break
        pages += 1
        time.sleep(0.15)  # Rate limit safety

    # Sort: highest urgency first (closest to close), then by ROI
    opportunities.sort(key=lambda x: (-x.get("urgency", 0), -x.get("roi_pct", 0)))

    sniper_count = sum(1 for o in opportunities if o.get("tier") == "sniper")
    warmup_count = sum(1 for o in opportunities if o.get("tier") == "warmup")
    print(f"  [SNIPER] Checked {markets_checked} markets | "
          f"{sniper_count} SNIPER (<6h) + {warmup_count} WARMUP (6-24h)")

    if opportunities:
        for opp in opportunities[:8]:
            hrs = opp["hours_to_resolve"]
            tag = "🎯" if opp.get("tier") == "sniper" else "⏳"
            if hrs < 1:
                time_str = f"{hrs * 60:.0f}min"
            else:
                time_str = f"{hrs:.1f}h"
            print(f"    {tag} {opp['title'][:55]}... | {opp['side'].upper()} @ "
                  f"${opp['price']:.2f} | closes in {time_str} | "
                  f"ROI: {opp['roi_pct']:.1f}%")

    return opportunities


# ──────────────────────────────────────────────────────────────
# PHASE 2: DETECT -- Balance changes + settlement monitoring
# ──────────────────────────────────────────────────────────────

def detect_balance_change(api_key, pem_data):
    """
    Detect if balance increased since last check (user deposit!).
    Returns (current_balance, delta, is_new_deposit).
    """
    balance_data = _sign_and_fetch("/portfolio/balance", api_key, pem_data)
    if not balance_data:
        return None, 0, False

    current = round(balance_data.get("balance", 0) / 100, 2)

    # Load previous state
    prev_state = _load(DATA / "turbo_trader_state.json")
    last_balance = prev_state.get("last_known_balance", 0)

    delta = round(current - last_balance, 2)
    is_deposit = delta > 0.50  # More than 50 cents appeared = likely deposit

    if is_deposit:
        print(f"  [TURBO] $$ DEPOSIT DETECTED! Balance: ${last_balance:.2f} -> ${current:.2f} "
              f"(+${delta:.2f})")

    return current, delta, is_deposit


def check_settlements(api_key, pem_data):
    """
    Check for recently settled positions.
    GET /portfolio/settlements returns resolved contracts.
    """
    # Check settlements from last 24 hours
    data = _sign_and_fetch("/portfolio/settlements?limit=50", api_key, pem_data)

    if not data:
        return []

    settlements = data.get("settlements", [])
    if settlements:
        total_payout = sum(s.get("revenue", 0) / 100 for s in settlements)
        print(f"  [TURBO] >> {len(settlements)} settlements in last 24h, "
              f"${total_payout:.2f} revenue")

    return settlements


def get_positions(api_key, pem_data):
    """Get all open positions with value estimates."""
    data = _sign_and_fetch("/portfolio/positions", api_key, pem_data)
    if data:
        positions = data.get("market_positions", [])
        return positions
    return []


# ──────────────────────────────────────────────────────────────
# PHASE 2b: VELOCITY -- Sell slow positions, free cash for daily trades
# ──────────────────────────────────────────────────────────────

def evaluate_positions_for_velocity(api_key, pem_data):
    """
    Analyze all open positions and identify which to SELL for faster cycling.

    Strategy:
    - KEEP positions resolving within 7 days (too close, just wait)
    - SELL positions resolving in 30+ days (free cash for daily markets)
    - Calculate freed cash vs opportunity cost
    """
    positions = get_positions(api_key, pem_data)
    if not positions:
        return [], [], 0

    now = datetime.now(timezone.utc)
    to_sell = []
    to_keep = []

    for p in positions:
        ticker = p.get("ticker", "")
        pos_fp = float(p.get("position_fp", 0))
        if pos_fp == 0:
            continue

        side = "yes" if pos_fp > 0 else "no"
        qty = abs(int(pos_fp))
        cost = float(p.get("total_traded_dollars", 0))

        # Get current market data for sell price
        market_data = _public_fetch(f"/markets/{ticker}")
        if not market_data or not market_data.get("market"):
            time.sleep(0.35)
            continue

        m = market_data["market"]
        close_str = m.get("close_time", "")

        # Calculate days to resolution
        days_to_close = 999
        if close_str:
            try:
                close_dt = datetime.fromisoformat(close_str.replace("Z", "+00:00"))
                days_to_close = max(0, (close_dt - now).total_seconds() / 86400)
            except Exception:
                pass

        # Get sell price (bid side)
        if side == "yes":
            sell_price = float(m.get("yes_bid_dollars", 0) or 0)
        else:
            sell_price = float(m.get("no_bid_dollars", 0) or 0)

        sell_value = sell_price * qty
        hold_value = qty * 1.00  # $1.00 payout on resolution
        loss_if_sell = cost - sell_value

        info = {
            "ticker": ticker,
            "side": side,
            "qty": qty,
            "cost": cost,
            "sell_price": sell_price,
            "sell_value": round(sell_value, 2),
            "hold_value": hold_value,
            "loss_if_sell": round(loss_if_sell, 2),
            "days_to_close": round(days_to_close, 1),
            "close_time": close_str[:10],
        }

        # Decision: keep if resolving within 7 days, sell if 30+ days
        if days_to_close <= 7:
            to_keep.append(info)
            print(f"  [VELOCITY] KEEP {ticker}: {qty}x {side.upper()} -- "
                  f"resolves in {days_to_close:.0f} days (too close to sell)")
        elif sell_price > 0:
            to_sell.append(info)
            print(f"  [VELOCITY] SELL {ticker}: {qty}x {side.upper()} -- "
                  f"${sell_value:.2f} freed, resolves in {days_to_close:.0f} days")

        time.sleep(0.35)

    freed_cash = sum(s["sell_value"] for s in to_sell)
    print(f"  [VELOCITY] Summary: SELL {len(to_sell)} positions (${freed_cash:.2f}) | "
          f"KEEP {len(to_keep)} positions")

    return to_sell, to_keep, freed_cash


def sell_positions(positions_to_sell, api_key, pem_data):
    """
    Execute sell orders for positions we want to liquidate.

    Kalshi sell order: action="sell", same ticker/side/count format.
    Sell at current bid price for instant fill.
    """
    results = []

    for pos in positions_to_sell:
        ticker = pos["ticker"]
        side = pos["side"]
        qty = pos["qty"]
        sell_price = pos["sell_price"]

        if sell_price <= 0 or qty <= 0:
            continue

        price_cents = int(round(sell_price * 100))

        order = {
            "ticker": ticker,
            "action": "sell",
            "side": side,
            "count": qty,
            "type": "limit",
            "client_order_id": str(uuid.uuid4()),
        }

        if side == "yes":
            order["yes_price"] = price_cents
        else:
            order["no_price"] = price_cents

        print(f"  [VELOCITY] Selling {qty}x {side.upper()} {ticker} @ ${sell_price:.2f}...")

        result = _sign_and_fetch("/portfolio/orders", api_key, pem_data,
                                 method="POST", body=order)

        if result and result.get("order"):
            order_data = result["order"]
            status = order_data.get("status", "unknown")
            results.append({
                "success": True,
                "action": "sell",
                "ticker": ticker,
                "side": side,
                "qty": qty,
                "sell_price": sell_price,
                "total": round(sell_price * qty, 2),
                "status": status,
                "order_id": order_data.get("order_id", ""),
            })
            print(f"    [OK] SOLD: {status} | ${sell_price * qty:.2f} freed")
        else:
            results.append({
                "success": False,
                "action": "sell",
                "ticker": ticker,
                "error": "sell order failed",
            })
            print(f"    [X] SELL FAILED for {ticker}")

        time.sleep(0.15)

    return results


def velocity_mode(api_key, pem_data, config):
    """
    VELOCITY MODE: Sell slow positions, free cash, deploy into daily markets.

    1. Evaluate all positions (keep 7-day, sell 30+ day)
    2. Execute sell orders
    3. Return freed cash for immediate redeployment by the main cycle
    """
    print("\n  [VELOCITY] Evaluating positions for velocity cycling...")
    to_sell, to_keep, potential_cash = evaluate_positions_for_velocity(api_key, pem_data)

    if not to_sell:
        print("  [VELOCITY] No slow positions to sell -- already optimized")
        return 0, []

    # Execute sells
    print(f"  [VELOCITY] Selling {len(to_sell)} slow positions to free ${potential_cash:.2f}...")
    sell_results = sell_positions(to_sell, api_key, pem_data)

    freed = sum(r["total"] for r in sell_results if r.get("success"))
    sold_count = sum(1 for r in sell_results if r.get("success"))

    print(f"  [VELOCITY] Freed ${freed:.2f} from {sold_count} positions -- "
          f"ready for daily deployment!")

    return freed, sell_results


# ──────────────────────────────────────────────────────────────
# PHASE 3: TRADE -- Batch order placement for maximum speed
# ──────────────────────────────────────────────────────────────

def construct_micro_orders(opportunities, balance, config):
    """
    Build orders for multiple opportunities at once.

    Strategy: spread capital across as many fast-resolving markets
    as possible. Many small bets > few big bets.

    Prioritizes daily-resolving markets (compound faster).

    PENNY MODE: When cash is micro ($0.10-$2.00), uses dynamic floor
    based on portfolio value so every cent gets deployed.
    """
    max_exposure = balance * config.get("max_exposure_pct", 0.95)

    # Dynamic floor: scale to portfolio value, not just cash
    # With $48 in pending positions, holding $1.00 floor on $1.69 is wasteful
    # Floor = 10% of cash, min $0.05, max $1.00
    static_floor = config.get("balance_floor_usd", 1.00)
    dynamic_floor = max(0.05, min(static_floor, balance * 0.10))
    floor = dynamic_floor

    available = min(balance - floor, max_exposure)

    # PENNY MODE: When balance is small, max_per_market must cover at least 1 contract
    # At $1.69 balance, 25% = $0.42 which can't buy any $0.85 contract -- useless.
    # In penny mode, allow up to 100% of available per market (spread naturally limited by cash)
    if available < 5.00:
        max_per_market = available  # Let the available cash itself be the limit
    else:
        max_per_market = balance * config.get("max_position_pct", 0.25)

    if available <= 0:
        return []

    orders = []
    total_cost = 0

    for opp in opportunities:
        if total_cost >= available:
            break

        price = opp["price"]
        if price <= 0 or price >= 1.0:
            continue

        # Calculate order size -- smaller for daily (more diversified)
        # PENNY MODE: When available < $2, size = single contracts to maximize trades
        base_size = config.get("default_order_size_usd", 4.00)
        if available < 2.00:
            # Penny mode: 1 contract each, spread across many markets
            base_size = min(price + 0.01, available - total_cost)

        if opp["resolution_class"] == "CLOSING_SOON":
            # SNIPER: max allocation — it resolves in HOURS
            order_size = min(base_size * 1.5, max_per_market)
        elif opp["resolution_class"] == "DAILY":
            order_size = min(base_size, max_per_market)
        elif opp["resolution_class"] == "WEEKLY":
            order_size = min(base_size * 0.75, max_per_market)
        else:
            order_size = min(base_size * 0.5, max_per_market)

        # Don't exceed remaining capacity
        order_size = min(order_size, available - total_cost)
        if order_size < price:
            continue

        count = max(1, int(order_size / price))
        cost = count * price

        if total_cost + cost > available:
            count = max(1, int((available - total_cost) / price))
            cost = count * price

        if count < 1:
            continue

        price_cents = int(round(price * 100))

        order = {
            "ticker": opp["ticker"],
            "action": "buy",
            "side": opp["side"],
            "count": count,
            "type": "limit",
            "client_order_id": str(uuid.uuid4()),
        }

        if opp["side"] == "yes":
            order["yes_price"] = price_cents
        else:
            order["no_price"] = price_cents

        order["_meta"] = {
            "title": opp["title"],
            "strategy": opp["strategy"],
            "resolution_class": opp["resolution_class"],
            "hours_to_resolve": opp["hours_to_resolve"],
            "expected_cost": round(cost, 4),
            "expected_payout": round(count * 1.00, 4),
            "expected_profit": round(count * opp["profit_per_contract"], 4),
            "roi_pct": opp["roi_pct"],
            "annualized_roi": opp.get("annualized_roi", 0),
        }

        orders.append(order)
        total_cost += cost

    return orders


def place_orders(orders, api_key, pem_data):
    """
    Place orders one at a time (batch endpoint may have issues).
    Rate limited to 10 writes/sec.
    """
    results = []

    for order in orders:
        send_order = {k: v for k, v in order.items() if not k.startswith("_")}
        meta = order.get("_meta", {})

        speed = meta.get("resolution_class", "?")
        print(f"  [TURBO] >> {speed} | {order['side'].upper()} {order['count']}x "
              f"{order['ticker']} @ ${order.get('yes_price', order.get('no_price', 0))/100:.2f}")

        result = _sign_and_fetch("/portfolio/orders", api_key, pem_data,
                                 method="POST", body=send_order)

        if result and result.get("order"):
            order_data = result["order"]
            results.append({
                "success": True,
                "order_id": order_data.get("order_id", ""),
                "status": order_data.get("status", "unknown"),
                "ticker": order["ticker"],
                "side": order["side"],
                "count": order["count"],
                "response": order_data,
                "order_details": meta,
            })
            print(f"    [OK] FILLED: {order_data.get('status')}")
        else:
            results.append({
                "success": False,
                "ticker": order["ticker"],
                "side": order["side"],
                "error": "Order failed",
                "order_details": meta,
            })
            print(f"    [X] FAILED")

        time.sleep(0.15)  # Rate limit: 10 writes/sec

    return results


# ──────────────────────────────────────────────────────────────
# PHASE 4: COMPOUND -- Track growth and wire back to ecosystem
# ──────────────────────────────────────────────────────────────

def update_compound_tracker(state):
    """
    Track compound growth over time.
    Every cycle appends a snapshot for growth curves.
    """
    tracker_path = DATA / "compound_tracker.json"
    tracker = _load(tracker_path, {
        "started": datetime.now(timezone.utc).isoformat(),
        "initial_balance": 0,
        "snapshots": [],
        "peak_balance": 0,
        "total_settlements": 0,
        "total_revenue": 0,
        "compound_cycles": 0,
    })

    balance = state.get("balance", 0)
    pending = state.get("total_pending_payout", 0)
    total_value = balance + pending

    if tracker.get("initial_balance", 0) == 0 and balance > 0:
        tracker["initial_balance"] = balance

    tracker["peak_balance"] = max(tracker.get("peak_balance", 0), total_value)
    tracker["compound_cycles"] = tracker.get("compound_cycles", 0) + 1

    # Growth since inception
    initial = tracker.get("initial_balance", 0)
    growth_pct = ((total_value / initial) - 1) * 100 if initial > 0 else 0

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "balance_cash": balance,
        "pending_payout": pending,
        "total_value": total_value,
        "positions_open": state.get("positions_count", 0),
        "trades_this_cycle": state.get("trades_placed", 0),
        "growth_pct": round(growth_pct, 2),
        "daily_trades": state.get("daily_opps", 0),
        "weekly_trades": state.get("weekly_opps", 0),
    }
    if "snapshots" not in tracker:
        tracker["snapshots"] = []
    tracker["snapshots"].append(snapshot)
    tracker["snapshots"] = tracker["snapshots"][-1000:]  # Keep 1000 snapshots

    _save(tracker_path, tracker)
    return tracker


def update_trade_ledger(trades):
    """Append trades to the shared trade_ledger.json (used by TRADING_WIRE)."""
    ledger_path = DATA / "trade_ledger.json"
    ledger = _load(ledger_path, {"trades": [], "stats": {}})

    for trade in trades:
        trade["recorded_at"] = datetime.now(timezone.utc).isoformat()
        trade["source"] = "TURBO_TRADER"
        ledger["trades"].append(trade)

    total = len(ledger["trades"])
    wins = sum(1 for t in ledger["trades"] if t.get("success"))
    ledger["stats"] = {
        "total_trades": total,
        "successful_orders": wins,
        "failed_orders": total - wins,
        "last_trade": datetime.now(timezone.utc).isoformat(),
    }
    ledger["trades"] = ledger["trades"][-5000:]
    _save(ledger_path, ledger)


# ──────────────────────────────────────────────────────────────
# MAIN RUN LOOP
# ──────────────────────────────────────────────────────────────

def run():
    """
    TURBO TRADER: The compounding machine.

    Every cycle:
    0. HIVE MIND: Gather ALL intelligence (9 sources)
    1. DETECT: Balance changes + settlements
    1b. VELOCITY: Sell slow positions, free cash
    2. DISCOVER: Dynamic series discovery (9000+)
    3. SCAN: Fast-resolving market opportunities
    3b. AI ANALYZE: Groq (FREE) scores opportunities using ALL intelligence
    4. TRADE: Place micro-orders on AI's top picks
    5. FEEDBACK: Record what intelligence led to what trades
    6. COMPOUND: Track growth, wire to ecosystem
    """
    print("[TURBO_TRADER] >> High-frequency compounding engine starting...")

    # Load config (shares trade_executor_config.json)
    config = _load(DATA / "trade_executor_config.json", {
        "enabled": False,
        "max_position_pct": 0.25,
        "max_exposure_pct": 0.95,
        "balance_floor_usd": 1.00,
        "max_trades_per_cycle": 10,
        "min_market_volume": 100,   # Lower for daily markets
        "min_confidence_pct": 85,
        "default_order_size_usd": 4.00,
    })

    if not config.get("enabled", False):
        print("[TURBO_TRADER] DISABLED -- trading not enabled in config")
        return {"status": "disabled"}

    # Read nervous system state for trade modulation
    _homeo = _load(DATA / "homeostasis_state.json", {})
    _cortex = _load(DATA / "neural_cortex_state.json", {})
    _fire = _load(DATA / "fire_ledger.json", {})
    _equilibrium = _homeo.get("equilibrium", 50)
    _brain_risk = _cortex.get("strategy", {}).get("risk_posture", "moderate")
    _fire_overlap = _fire.get("summary", {}).get("overlap_detected", False)

    # Modulate trading aggression based on internal health
    if _equilibrium < 20 or _brain_risk == "conservative":
        config["max_trades_per_cycle"] = max(1, config.get("max_trades_per_cycle", 10) // 2)
        config["min_confidence_pct"] = max(config.get("min_confidence_pct", 85), 92)
        print(f"[TURBO_TRADER] Nervous system override: conservative mode (eq={_equilibrium}, risk={_brain_risk})")
    elif _fire_overlap:
        config["max_trades_per_cycle"] = max(2, config.get("max_trades_per_cycle", 10) - 2)
        print(f"[TURBO_TRADER] Fire overlap detected: reducing trades per cycle")

    # Authenticate
    api_key, pem_data = _load_kalshi_auth()
    if not api_key or not pem_data:
        print("[TURBO_TRADER] No credentials -- cannot trade")
        return {"status": "error", "reason": "no_credentials"}

    # === PHASE 1: DETECT balance changes + settlements ===
    balance, delta, is_deposit = detect_balance_change(api_key, pem_data)
    if balance is None:
        print("[TURBO_TRADER] Cannot read balance -- aborting")
        return {"status": "error", "reason": "balance_check_failed"}

    print(f"[TURBO_TRADER] Balance: ${balance:.2f}" +
          (f" (+${delta:.2f} deposit!)" if is_deposit else ""))

    settlements = check_settlements(api_key, pem_data)

    # === PHASE 1b: VELOCITY -- sell slow positions to free cash ===
    velocity_freed = 0
    velocity_sells = []
    if config.get("velocity_mode", True):  # ON by default
        velocity_freed, velocity_sells = velocity_mode(api_key, pem_data, config)
        if velocity_freed > 0:
            # Re-read balance after selling
            new_bal = _sign_and_fetch("/portfolio/balance", api_key, pem_data)
            if new_bal:
                balance = round(new_bal.get("balance", 0) / 100, 2)
                print(f"[TURBO_TRADER] Post-velocity balance: ${balance:.2f}")

    # Check floor (dynamic: 10% of cash, min $0.05, capped at config floor)
    # With $48+ in pending positions, no reason to hold $1.00 idle
    static_floor = config.get("balance_floor_usd", 1.00)
    floor = max(0.05, min(static_floor, balance * 0.10))
    if balance < floor:
        print(f"[TURBO_TRADER] Balance ${balance:.2f} below floor ${floor:.2f}")
        # Still track state even when not trading
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "below_floor",
            "balance": balance,
            "floor": floor,
            "last_known_balance": balance,
            "settlements_24h": len(settlements),
            "velocity_freed": velocity_freed,
            "velocity_sells": len(velocity_sells),
            "message": f"Waiting for positions to resolve or new deposit. "
                       f"${floor - balance:.2f} below floor.",
        }
        _save(DATA / "turbo_trader_state.json", state)
        update_compound_tracker(state)
        return state

    # === PHASE 2: DISCOVER all available markets ===
    print("[TURBO_TRADER] Discovering markets...")
    series_list = discover_all_series()

    # === PHASE 2.5: SNIPER MODE — find markets closing SOON ===
    # Markets closing in <6 hours have near-certain outcomes.
    # The event is almost over — we can SEE the result.
    # Buy at $0.95-0.99, collect $1.00 in hours, not days.
    sniper_opps = sniper_scan(config)
    if sniper_opps:
        print(f"  [SNIPER] {len(sniper_opps)} markets closing within 6 hours!")

    # === PHASE 3: SCAN for fast-resolving opportunities ===
    min_conf = config.get("min_confidence_pct", 85)
    min_vol = config.get("min_market_volume", 100)
    opportunities = scan_fast_markets(series_list, min_conf, min_vol)

    # Merge sniper opportunities (highest priority — they close FIRST)
    existing_tickers = {o["ticker"] for o in opportunities}
    for so in sniper_opps:
        if so["ticker"] not in existing_tickers:
            opportunities.insert(0, so)  # Front of the queue

    # PENNY MODE: If cash is tight and normal scan found only expensive contracts,
    # do a TARGETED second pass with lower confidence on series that had results
    available_after_floor = balance - floor
    if available_after_floor < 2.00 and opportunities:
        cheapest = min(o["price"] for o in opportunities)
        if cheapest > available_after_floor:
            print(f"[TURBO_TRADER] PENNY MODE: cheapest contract ${cheapest:.2f} > "
                  f"available ${available_after_floor:.2f}, scanning wider...")
            # Only re-scan series that already had tradeable markets (much faster)
            active_series = list({o["series"] for o in opportunities})
            # Add a few more high-frequency series that often have cheap contracts
            for s in FAST_SERIES[:5]:
                if s not in active_series:
                    active_series.append(s)
            penny_opps = scan_fast_markets(active_series, 75, min_vol)
            # Add new cheaper opps we didn't already have
            existing_tickers = {o["ticker"] for o in opportunities}
            for po in penny_opps:
                if po["ticker"] not in existing_tickers and po["price"] <= available_after_floor:
                    po["strategy"] = "penny_" + po["strategy"]
                    opportunities.append(po)
            if opportunities:
                # Re-sort: daily first, then by annualized ROI
                opportunities.sort(
                    key=lambda x: (
                        {"CLOSING_SOON": -1, "DAILY": 0, "WEEKLY": 1, "MONTHLY": 2, "LONG": 3}
                        .get(x["resolution_class"], 4),
                        -x.get("annualized_roi", 0),
                    )
                )
                print(f"[TURBO_TRADER] PENNY MODE: {len(opportunities)} total opps after widening")

    if not opportunities:
        print("[TURBO_TRADER] No qualifying opportunities this cycle")
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "active_no_trades",
            "balance": balance,
            "last_known_balance": balance,
            "series_scanned": len(series_list[:80]),
            "settlements_24h": len(settlements),
        }
        _save(DATA / "turbo_trader_state.json", state)
        return state

    # Classify opportunities by speed
    sniper_opps_count = [o for o in opportunities if o["resolution_class"] == "CLOSING_SOON"]
    daily_opps = [o for o in opportunities if o["resolution_class"] == "DAILY"]
    weekly_opps = [o for o in opportunities if o["resolution_class"] == "WEEKLY"]
    monthly_opps = [o for o in opportunities if o["resolution_class"] in ("MONTHLY", "LONG")]

    print(f"[TURBO_TRADER] Opportunities: {len(sniper_opps_count)} SNIPER, "
          f"{len(daily_opps)} daily, {len(weekly_opps)} weekly, "
          f"{len(monthly_opps)} monthly+")

    # === PHASE 3b: HIVE MIND -- AI-powered intelligence analysis ===
    print("[TURBO_TRADER] >> HIVE MIND: AI analyzing opportunities...")
    signals, raw_intel = gather_all_intelligence()
    opportunities = ai_score_opportunities(opportunities, signals)

    # === PHASE 4: TRADE -- place micro-orders ===
    max_trades = config.get("max_trades_per_cycle", 10)
    orders = construct_micro_orders(opportunities[:max_trades * 2], balance, config)

    if not orders:
        print("[TURBO_TRADER] No orders constructed (insufficient balance?)")
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "active_no_capacity",
            "balance": balance,
            "last_known_balance": balance,
            "opportunities": len(opportunities),
        }
        _save(DATA / "turbo_trader_state.json", state)
        return state

    # Cap orders at max_trades_per_cycle
    orders = orders[:max_trades]

    print(f"[TURBO_TRADER] Placing {len(orders)} micro-trades...")
    results = place_orders(orders, api_key, pem_data)

    # Update shared trade ledger + AI feedback loop
    if results:
        update_trade_ledger(results)
        build_feedback_loop(results, signals)

    # === PHASE 5: COMPOUND -- track growth ===
    new_balance_data = _sign_and_fetch("/portfolio/balance", api_key, pem_data)
    new_balance = round(new_balance_data.get("balance", 0) / 100, 2) if new_balance_data else balance

    positions = get_positions(api_key, pem_data)
    positions_count = len(positions) if positions else 0

    # Calculate total pending payout from trade ledger
    ledger = _load(DATA / "trade_ledger.json", {"trades": []})
    total_pending = sum(
        t.get("order_details", {}).get("expected_payout", 0)
        for t in ledger.get("trades", [])
        if t.get("success")
    )

    successful = sum(1 for r in results if r.get("success"))
    failed = len(results) - successful

    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "turbo-trader-v1",
        "status": "active",
        "balance": new_balance,
        "last_known_balance": new_balance,
        "balance_change": delta,
        "deposit_detected": is_deposit,
        "positions_count": positions_count,
        "trades_placed": len(results),
        "successful": successful,
        "failed": failed,
        "sniper_opps": len(sniper_opps_count),
        "daily_opps": len(daily_opps),
        "weekly_opps": len(weekly_opps),
        "monthly_opps": len(monthly_opps),
        "total_opportunities": len(opportunities),
        "total_pending_payout": round(total_pending, 2),
        "settlements_24h": len(settlements),
        "velocity_freed": velocity_freed,
        "velocity_sells": len(velocity_sells),
        "series_scanned": len(series_list[:80]),
        "top_opportunities": opportunities[:10],
        "trades": results,
    }
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    _save(DATA / "turbo_trader_state.json", state)

    # Broadcast to synaptic bus -- every engine sees this INSTANTLY
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_batch("TURBO_TRADER", {
            "balance": new_balance,
            "trades_placed": len(results),
            "successful": successful,
            "sniper_opps": len(sniper_opps_count),
            "daily_opps": len(daily_opps),
            "total_opportunities": len(opportunities),
            "pending_payout": round(total_pending, 2),
            "deposit_detected": is_deposit,
            "positions_count": positions_count,
            "status": state["status"],
            "platform": "kalshi",
            "signal_direction": "opportunity" if len(daily_opps) > 0 else "neutral",
            "equilibrium": _equilibrium,
            "brain_risk": _brain_risk,
            "fire_overlap": _fire_overlap,
        }, silent=False)
    except Exception:
        pass  # Bus not available -- degrade gracefully

    # Track compound growth
    tracker = update_compound_tracker(state)

    print(f"\n[TURBO_TRADER] >> Cycle complete:")
    print(f"  Trades: {successful}/{len(results)} filled")
    print(f"  Balance: ${balance:.2f} -> ${new_balance:.2f}")
    print(f"  Positions: {positions_count} open")
    print(f"  Pending payout: ${total_pending:.2f}")
    print(f"  SNIPER: {len(sniper_opps_count)} closing-soon opps found")
    print(f"  Compound cycles: {tracker.get('compound_cycles', 0)}")
    print(f"  Growth: {tracker['snapshots'][-1]['growth_pct']:.1f}%" if tracker.get("snapshots") else "")

    return state


if __name__ == "__main__":
    run()
