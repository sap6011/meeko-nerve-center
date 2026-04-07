#!/usr/bin/env python3
"""
ALPACA_TRADER.py -- Commission-free stock & ETF trading engine
================================================================
v1 (2026-04-06): Second platform in the multi-market compounding machine.

WHY ALPACA:
  - Commission-free stocks, ETFs, and crypto
  - Fractional shares (trade with $0.50 if you want)
  - $0 minimum account balance
  - Paper trading sandbox (identical API, fake money)
  - 200 req/min rate limit (generous for a bot)
  - Purpose-built for algorithmic trading
  - Extended hours trading (pre/post market)

STRATEGY (micro-account optimized):
  Swing trading (2-5 day holds) to AVOID Pattern Day Trader rule.
  PDT = 4+ day trades in 5 business days requires $25k minimum.
  With micro-balance, we get 3 free day trades per week.

  1. MOMENTUM ETFs: Buy SPY/QQQ/DIA on intraday dips
  2. FRACTIONAL BLUE CHIPS: $1-$5 of AAPL, MSFT, NVDA, GOOGL
  3. SECTOR ROTATION: Shift between growth/value/defensive ETFs
  4. MEAN REVERSION: Buy oversold (>2% daily drop) quality names
  5. CRYPTO via Alpaca: BTC/ETH with no PDT restriction

  Commission-free means even 0.5% gains are pure profit.
  Fractional shares mean we can diversify even with $5 total.

COMPOUNDING MATH (swing trades):
  $10 @ 1% per trade, 3 trades/week:
    Week 1: $10.00 -> $10.30
    Month 1: $10.00 -> $11.27
    Month 3: $10.00 -> $14.40
  Scale with deposits: $100 -> $144 in 3 months (auto-compounding)

Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)

Called by: NERVE_LOOP Phase 4d (EXECUTE), OMNIBUS
Reads: Alpaca API (paper or live), ecosystem intelligence
Writes: data/alpaca_trader_state.json, feeds into trade_ledger.json
"""

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# API endpoints
ALPACA_PAPER = "https://paper-api.alpaca.markets"
ALPACA_LIVE = "https://api.alpaca.markets"
ALPACA_DATA = "https://data.alpaca.markets"

# Core watchlist: liquid ETFs + blue chips + crypto
# These have fractional share support, high volume, tight spreads
WATCHLIST = {
    # === ETFs (most liquid, best for micro-accounts) ===
    "SPY":  {"type": "etf", "sector": "broad_market", "strategy": "momentum"},
    "QQQ":  {"type": "etf", "sector": "tech", "strategy": "momentum"},
    "DIA":  {"type": "etf", "sector": "industrials", "strategy": "momentum"},
    "IWM":  {"type": "etf", "sector": "small_cap", "strategy": "mean_reversion"},
    "XLF":  {"type": "etf", "sector": "financials", "strategy": "sector_rotation"},
    "XLE":  {"type": "etf", "sector": "energy", "strategy": "sector_rotation"},
    "XLK":  {"type": "etf", "sector": "tech", "strategy": "sector_rotation"},
    "GLD":  {"type": "etf", "sector": "gold", "strategy": "safe_haven"},
    "TLT":  {"type": "etf", "sector": "bonds", "strategy": "safe_haven"},
    "VTI":  {"type": "etf", "sector": "total_market", "strategy": "dca"},
    # === Blue chips (fractional shares) ===
    "AAPL": {"type": "stock", "sector": "tech", "strategy": "blue_chip"},
    "MSFT": {"type": "stock", "sector": "tech", "strategy": "blue_chip"},
    "NVDA": {"type": "stock", "sector": "tech", "strategy": "blue_chip"},
    "GOOGL": {"type": "stock", "sector": "tech", "strategy": "blue_chip"},
    "AMZN": {"type": "stock", "sector": "tech", "strategy": "blue_chip"},
    "META": {"type": "stock", "sector": "tech", "strategy": "blue_chip"},
    "TSLA": {"type": "stock", "sector": "auto", "strategy": "momentum"},
    # === Crypto (no PDT restriction! 24/7! Commission-free!) ===
    # UNLIMITED day trades on crypto -- this is where speed wins
    # Major coins
    "BTC/USD":  {"type": "crypto", "sector": "crypto", "strategy": "momentum"},
    "ETH/USD":  {"type": "crypto", "sector": "crypto", "strategy": "momentum"},
    "SOL/USD":  {"type": "crypto", "sector": "crypto", "strategy": "momentum"},
    "AVAX/USD": {"type": "crypto", "sector": "crypto", "strategy": "momentum"},
    "LINK/USD": {"type": "crypto", "sector": "crypto", "strategy": "momentum"},
    "DOT/USD":  {"type": "crypto", "sector": "crypto", "strategy": "mean_reversion"},
    "UNI/USD":  {"type": "crypto", "sector": "crypto", "strategy": "momentum"},
    "AAVE/USD": {"type": "crypto", "sector": "crypto", "strategy": "momentum"},
    "XRP/USD":  {"type": "crypto", "sector": "crypto", "strategy": "momentum"},
    "LTC/USD":  {"type": "crypto", "sector": "crypto", "strategy": "mean_reversion"},
    "BCH/USD":  {"type": "crypto", "sector": "crypto", "strategy": "mean_reversion"},
    # NOTE: ALGO/USD, MATIC/USD, ADA/USD, ATOM/USD delisted by Alpaca as of 2026-04
    # Meme coins -- volatile = fast gains (and fast losses, but speed + automation wins)
    "DOGE/USD": {"type": "crypto", "sector": "meme_coin", "strategy": "momentum"},
    "SHIB/USD": {"type": "crypto", "sector": "meme_coin", "strategy": "momentum"},
    # Stablecoins -- for parking cash and arb opportunities
    "USDT/USD": {"type": "crypto", "sector": "stablecoin", "strategy": "safe_haven"},
    "USDC/USD": {"type": "crypto", "sector": "stablecoin", "strategy": "safe_haven"},
}

# Strategy parameters
STRATEGIES = {
    "momentum": {
        "min_daily_change_pct": 0.5,   # Buy on pullback from uptrend
        "take_profit_pct": 2.0,         # Sell at 2% gain
        "stop_loss_pct": -3.0,          # Cut at 3% loss
        "hold_days_min": 2,             # Avoid PDT
        "hold_days_max": 10,            # Don't hold forever
    },
    "mean_reversion": {
        "min_drop_pct": -2.0,           # Buy when down 2%+
        "take_profit_pct": 1.5,         # Sell at 1.5% bounce
        "stop_loss_pct": -5.0,          # Wider stop for mean reversion
        "hold_days_min": 1,
        "hold_days_max": 5,
    },
    "blue_chip": {
        "min_drop_pct": -1.0,           # Buy any dip
        "take_profit_pct": 3.0,         # Let winners run
        "stop_loss_pct": -5.0,          # Wide stops on quality
        "hold_days_min": 2,
        "hold_days_max": 20,
    },
    "sector_rotation": {
        "min_drop_pct": -1.5,           # Rotate into beaten sectors
        "take_profit_pct": 2.5,
        "stop_loss_pct": -4.0,
        "hold_days_min": 3,
        "hold_days_max": 15,
    },
    "safe_haven": {
        "min_drop_pct": -0.5,           # Buy safe havens on any dip
        "take_profit_pct": 1.0,         # Quick exits
        "stop_loss_pct": -2.0,
        "hold_days_min": 2,
        "hold_days_max": 30,
    },
    "dca": {
        "min_drop_pct": 0,              # Buy regardless
        "take_profit_pct": 5.0,         # Long hold
        "stop_loss_pct": -10.0,
        "hold_days_min": 5,
        "hold_days_max": 60,
    },
}


def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_alpaca_auth():
    """Load Alpaca credentials from secrets."""
    secrets_path = DATA / ".secrets" / "alpaca.json"
    try:
        creds = json.loads(secrets_path.read_text(encoding="utf-8"))
        api_key = creds.get("api_key")
        secret_key = creds.get("secret_key")
        paper = creds.get("paper", True)  # Default to paper trading
        return api_key, secret_key, paper
    except Exception:
        return None, None, True


def _alpaca_fetch(endpoint, api_key, secret_key, paper=True,
                  method="GET", body=None, timeout=15, data_api=False):
    """Alpaca API request with key-based auth."""
    import urllib.request
    import urllib.error

    if data_api:
        base = ALPACA_DATA
    else:
        base = ALPACA_PAPER if paper else ALPACA_LIVE

    url = f"{base}{endpoint}"

    try:
        data_bytes = json.dumps(body).encode("utf-8") if body else None
        req = urllib.request.Request(url, data=data_bytes, method=method)
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")
        req.add_header("APCA-API-KEY-ID", api_key)
        req.add_header("APCA-API-SECRET-KEY", secret_key)

        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace") if e.fp else ""
        print(f"  [ALPACA] API error {e.code}: {body_text[:200]}")
        return None
    except Exception as e:
        print(f"  [ALPACA] Fetch error: {e}")
        return None


# ================================================================
# PHASE 1: ACCOUNT -- Check balance, buying power, PDT status
# ================================================================

def check_account(api_key, secret_key, paper):
    """Get account status, balance, and buying power."""
    account = _alpaca_fetch("/v2/account", api_key, secret_key, paper)
    if not account:
        return None

    return {
        "status": account.get("status", "UNKNOWN"),
        "cash": float(account.get("cash", 0)),
        "buying_power": float(account.get("buying_power", 0)),
        "portfolio_value": float(account.get("portfolio_value", 0)),
        "equity": float(account.get("equity", 0)),
        "long_market_value": float(account.get("long_market_value", 0)),
        "daytrade_count": int(account.get("daytrade_count", 0)),
        "pattern_day_trader": account.get("pattern_day_trader", False),
        "trading_blocked": account.get("trading_blocked", False),
        "currency": account.get("currency", "USD"),
    }


def get_positions(api_key, secret_key, paper):
    """Get all open positions."""
    positions = _alpaca_fetch("/v2/positions", api_key, secret_key, paper)
    if not positions:
        return []

    result = []
    for p in positions:
        result.append({
            "symbol": p.get("symbol"),
            "qty": float(p.get("qty", 0)),
            "side": p.get("side", "long"),
            "avg_entry_price": float(p.get("avg_entry_price", 0)),
            "market_value": float(p.get("market_value", 0)),
            "current_price": float(p.get("current_price", 0)),
            "unrealized_pl": float(p.get("unrealized_pl", 0)),
            "unrealized_plpc": float(p.get("unrealized_plpc", 0)),
            "change_today": float(p.get("change_today", 0)),
        })
    return result


def check_market_status(api_key, secret_key, paper):
    """Check if market is open."""
    clock = _alpaca_fetch("/v2/clock", api_key, secret_key, paper)
    if not clock:
        return {"is_open": False}

    return {
        "is_open": clock.get("is_open", False),
        "next_open": clock.get("next_open", ""),
        "next_close": clock.get("next_close", ""),
    }


# ================================================================
# PHASE 2: SCAN -- Find opportunities across watchlist
# ================================================================

def scan_opportunities(api_key, secret_key, paper, intelligence=None):
    """
    Scan watchlist for trading opportunities.

    Uses Alpaca market data to find:
    - Oversold stocks (mean reversion)
    - Momentum breakouts
    - Sector rotation candidates
    """
    opportunities = []
    now = datetime.now(timezone.utc)

    # Get latest quotes for all watchlist symbols
    # Use snapshots endpoint for efficiency (one call for multiple symbols)
    equity_symbols = [s for s, meta in WATCHLIST.items() if meta["type"] != "crypto"]
    crypto_symbols = [s for s, meta in WATCHLIST.items() if meta["type"] == "crypto"]

    # Batch equity snapshots
    if equity_symbols:
        symbols_param = ",".join(equity_symbols)
        snapshots = _alpaca_fetch(
            f"/v2/stocks/snapshots?symbols={symbols_param}",
            api_key, secret_key, paper, data_api=True
        )
        if snapshots:
            for symbol, snap in snapshots.items():
                opp = _evaluate_equity_snapshot(symbol, snap, intelligence)
                if opp:
                    opportunities.append(opp)

    # Crypto snapshots (batch query param endpoint)
    if crypto_symbols:
        crypto_param = ",".join(crypto_symbols)  # BTC/USD,ETH/USD
        crypto_resp = _alpaca_fetch(
            f"/v1beta3/crypto/us/snapshots?symbols={crypto_param}",
            api_key, secret_key, paper, data_api=True
        )
        if crypto_resp:
            snapshots_map = crypto_resp.get("snapshots", crypto_resp)
            for symbol in crypto_symbols:
                snap = snapshots_map.get(symbol)
                if snap:
                    opp = _evaluate_crypto_snapshot(symbol, snap, intelligence)
                    if opp:
                        opportunities.append(opp)

    # Sort: highest conviction first (score descending)
    opportunities.sort(key=lambda x: -x.get("score", 0))

    return opportunities


def _evaluate_equity_snapshot(symbol, snap, intelligence=None):
    """Evaluate a stock/ETF snapshot for trading opportunity."""
    meta = WATCHLIST.get(symbol, {})
    strategy_name = meta.get("strategy", "momentum")
    strategy = STRATEGIES.get(strategy_name, STRATEGIES["momentum"])

    # Extract price data
    daily_bar = snap.get("dailyBar", {})
    prev_daily = snap.get("prevDailyBar", {})
    latest_trade = snap.get("latestTrade", {})
    latest_quote = snap.get("latestQuote", {})

    current_price = float(latest_trade.get("p", 0)) or float(daily_bar.get("c", 0))
    prev_close = float(prev_daily.get("c", 0))
    today_open = float(daily_bar.get("o", 0))
    today_high = float(daily_bar.get("h", 0))
    today_low = float(daily_bar.get("l", 0))
    volume = int(daily_bar.get("v", 0))

    if not current_price or not prev_close:
        return None

    # Calculate metrics
    daily_change_pct = ((current_price - prev_close) / prev_close) * 100
    intraday_range_pct = ((today_high - today_low) / prev_close) * 100 if today_low > 0 else 0
    from_open_pct = ((current_price - today_open) / today_open) * 100 if today_open > 0 else 0

    # Score the opportunity (0-100)
    score = 50  # Base score

    # Mean reversion: buy oversold
    if strategy_name in ("mean_reversion", "blue_chip", "sector_rotation", "safe_haven"):
        min_drop = strategy.get("min_drop_pct", -1.0)
        if daily_change_pct <= min_drop:
            # Bigger drop = stronger signal (up to a point)
            drop_score = min(30, abs(daily_change_pct) * 10)
            score += drop_score
        else:
            score -= 20  # Not enough of a dip

    # Momentum: buy breakouts
    if strategy_name == "momentum":
        if daily_change_pct >= strategy.get("min_daily_change_pct", 0.5):
            score += 20
        elif daily_change_pct < -1.0:
            # Momentum broken, don't buy
            score -= 30

    # Volume confirmation
    if volume > 1_000_000:
        score += 10
    elif volume > 100_000:
        score += 5

    # DCA always buys (lowest threshold)
    if strategy_name == "dca":
        score = max(score, 60)

    # Intelligence overlay (from HIVE MIND)
    if intelligence:
        # If macro risk is high, boost safe havens, reduce risk
        macro_risk = intelligence.get("macro_risk", 0.5)
        if macro_risk > 0.7:
            if meta.get("sector") in ("gold", "bonds"):
                score += 15
            elif meta.get("type") == "stock":
                score -= 15
        # If crypto bullish, boost crypto-adjacent
        crypto_bull = intelligence.get("crypto_bullish", 0.5)
        if crypto_bull > 0.6 and meta.get("sector") == "tech":
            score += 5

    # Minimum threshold
    if score < 55:
        return None

    return {
        "symbol": symbol,
        "type": meta.get("type", "stock"),
        "sector": meta.get("sector", "unknown"),
        "strategy": strategy_name,
        "current_price": round(current_price, 2),
        "prev_close": round(prev_close, 2),
        "daily_change_pct": round(daily_change_pct, 2),
        "intraday_range_pct": round(intraday_range_pct, 2),
        "volume": volume,
        "score": round(score, 1),
        "take_profit_pct": strategy.get("take_profit_pct", 2.0),
        "stop_loss_pct": strategy.get("stop_loss_pct", -3.0),
        "hold_days_max": strategy.get("hold_days_max", 10),
    }


def _evaluate_crypto_snapshot(symbol, snap, intelligence=None):
    """Evaluate a crypto snapshot for trading opportunity."""
    meta = WATCHLIST.get(symbol, {})

    latest_trade = snap.get("latestTrade", {})
    daily_bar = snap.get("dailyBar", {})
    prev_daily = snap.get("prevDailyBar", {})

    current_price = float(latest_trade.get("p", 0))
    prev_close = float(prev_daily.get("c", 0)) if prev_daily else 0

    if not current_price or not prev_close:
        return None

    daily_change_pct = ((current_price - prev_close) / prev_close) * 100
    volume = int(daily_bar.get("v", 0)) if daily_bar else 0

    score = 50
    sector = meta.get("sector", "crypto")
    strategy = "momentum"

    # Crypto momentum scoring
    if daily_change_pct > 5.0:
        score += 25  # Massive pump — ride the wave
        strategy = "momentum"
    elif daily_change_pct > 1.0:
        score += 15
        strategy = "momentum"
    elif daily_change_pct < -5.0:
        score += 30  # Major dip buy
        strategy = "mean_reversion"
    elif daily_change_pct < -2.0:
        score += 20  # Mean reversion on decent drop
        strategy = "mean_reversion"

    # Meme coin bonus — volatile = opportunity (speed + automation wins)
    if sector == "meme_coin":
        score += 10  # Always interesting
        if abs(daily_change_pct) > 3.0:
            score += 10  # Volatile meme = high opportunity

    # Stablecoin — look for de-peg arb (should be ~$1.00)
    if sector == "stablecoin":
        if abs(current_price - 1.0) > 0.005:  # >0.5% off peg
            score += 25  # Arb opportunity
            strategy = "safe_haven"
        else:
            return None  # Stable at peg = no trade

    # Intelligence overlay
    if intelligence:
        crypto_bull = intelligence.get("crypto_bullish", 0.5)
        if crypto_bull > 0.6:
            score += 15
        elif crypto_bull < 0.3:
            score -= 10  # Less penalty — we still trade in bear markets

        # Fear & Greed Index: extreme fear = contrarian buy, extreme greed = caution
        fg = intelligence.get("fear_greed", 50)
        if fg <= 20:
            score += 20  # EXTREME FEAR = strongest buy signal
        elif fg <= 35:
            score += 10  # Fear = good entry
        elif fg >= 80:
            score -= 15  # Extreme greed = likely reversal

        # Trending coin bonus (CoinGecko trending = momentum)
        trending = intelligence.get("trending_crypto", [])
        base_sym = symbol.replace("/USD", "").replace("USD", "")
        if base_sym in trending:
            score += 10  # Trending = momentum confirmation

        # VIX-based caution for risk assets
        vix = intelligence.get("vix", 20)
        if vix > 30:
            score -= 10  # High vol environment = reduce crypto risk

    # Lower threshold for crypto — speed + automation compensates for lower conviction
    if score < 50:
        return None

    # Tighter TP/SL for meme coins (get in fast, get out fast)
    tp = 5.0 if sector == "meme_coin" else 3.0
    sl = -8.0 if sector == "meme_coin" else -5.0
    hold_max = 3 if sector == "meme_coin" else 14

    return {
        "symbol": symbol,
        "type": "crypto",
        "sector": sector,
        "strategy": strategy,
        "current_price": round(current_price, 2),
        "prev_close": round(prev_close, 2),
        "daily_change_pct": round(daily_change_pct, 2),
        "intraday_range_pct": 0,
        "volume": volume,
        "score": round(score, 1),
        "take_profit_pct": tp,
        "stop_loss_pct": sl,
        "hold_days_max": hold_max,
        "no_pdt": True,  # Crypto exempt from PDT
    }


# ================================================================
# PHASE 3: TRADE -- Place fractional/notional orders
# ================================================================

def construct_orders(opportunities, account, positions):
    """
    Build orders from opportunities.

    Uses NOTIONAL orders ($-based, not share-based) for maximum
    flexibility with micro-balances. $1 of AAPL? No problem.

    PDT-aware: tracks day trades, avoids crossing 4/week threshold.
    """
    buying_power = account.get("buying_power", 0)
    daytrade_count = account.get("daytrade_count", 0)
    is_pdt = account.get("pattern_day_trader", False)

    # Aggressive floor: keep just $0.10 in reserve
    floor = max(0.10, buying_power * 0.05)
    available = buying_power - floor

    if available <= 0:
        return []

    # Existing position symbols
    held = {p["symbol"] for p in positions}

    orders = []
    total_allocated = 0

    for opp in opportunities:
        if total_allocated >= available:
            break

        symbol = opp["symbol"]

        # Skip if already holding (don't double up)
        if symbol in held:
            continue

        # PDT check: if we're at 3 day trades, only crypto is allowed
        if daytrade_count >= 3 and not opp.get("no_pdt"):
            if not is_pdt:  # Non-PDT accounts get 3 per week
                continue

        # Allocate: concentrate into fewer, bigger positions
        # Alpaca crypto minimum is $1 per order
        min_order = 1.00  # Alpaca enforces $1 minimum on crypto
        remaining = available - total_allocated
        # With micro balance: go all-in on best opportunity
        # With bigger balance: spread 25% per position
        if remaining < 5.00:
            allocation = remaining  # All-in on top pick
        else:
            allocation = min(remaining * 0.25, remaining)
        allocation = max(min_order, allocation)

        if total_allocated + allocation > available:
            allocation = available - total_allocated
            if allocation < min_order:
                break

        # Use notional (dollar-based) for fractional share support
        # Crypto requires "gtc" time_in_force; stocks use "day"
        tif = "gtc" if opp.get("type") == "crypto" else "day"
        order = {
            "symbol": symbol,
            "notional": str(round(allocation, 2)),
            "side": "buy",
            "type": "market",
            "time_in_force": tif,
        }

        order["_meta"] = {
            "strategy": opp["strategy"],
            "score": opp["score"],
            "daily_change_pct": opp["daily_change_pct"],
            "current_price": opp["current_price"],
            "take_profit_pct": opp["take_profit_pct"],
            "stop_loss_pct": opp["stop_loss_pct"],
            "hold_days_max": opp["hold_days_max"],
            "sector": opp["sector"],
            "type": opp["type"],
            "allocated": round(allocation, 2),
        }

        orders.append(order)
        total_allocated += allocation

    return orders


def place_orders(orders, api_key, secret_key, paper):
    """Place orders via Alpaca API. Rate limited to stay under 200/min."""
    results = []

    for order in orders:
        send_order = {k: v for k, v in order.items() if not k.startswith("_")}
        meta = order.get("_meta", {})

        print(f"  [ALPACA] >> {meta.get('strategy','?')} | BUY "
              f"${meta.get('allocated',0):.2f} of {order['symbol']} "
              f"({meta.get('daily_change_pct',0):+.1f}% today, score={meta.get('score',0)})")

        result = _alpaca_fetch("/v2/orders", api_key, secret_key, paper,
                               method="POST", body=send_order)

        if result and result.get("id"):
            results.append({
                "success": True,
                "order_id": result.get("id"),
                "status": result.get("status", "unknown"),
                "symbol": order["symbol"],
                "side": "buy",
                "notional": order["notional"],
                "filled_qty": result.get("filled_qty", "0"),
                "filled_avg_price": result.get("filled_avg_price"),
                "order_details": meta,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "source": "ALPACA_TRADER",
            })
            print(f"    [OK] {result.get('status', 'accepted')}")
        else:
            results.append({
                "success": False,
                "symbol": order["symbol"],
                "error": str(result)[:200] if result else "no response",
                "order_details": meta,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "source": "ALPACA_TRADER",
            })
            print(f"    [X] FAILED")

        # Rate limit: 200/min = ~3.3/sec, be conservative
        time.sleep(0.5)

    return results


# ================================================================
# PHASE 4: MANAGE -- Monitor positions, take profits, cut losses
# ================================================================

def manage_positions(positions, api_key, secret_key, paper):
    """
    Check existing positions for take-profit or stop-loss triggers.
    Close positions that hit targets.
    """
    actions = []
    state = _load(DATA / "alpaca_trader_state.json")
    position_meta = state.get("position_meta", {})

    for pos in positions:
        symbol = pos["symbol"]
        unrealized_plpc = pos.get("unrealized_plpc", 0) * 100  # Convert to %
        meta = position_meta.get(symbol, {})
        take_profit = meta.get("take_profit_pct", 2.0)
        stop_loss = meta.get("stop_loss_pct", -3.0)
        hold_days_max = meta.get("hold_days_max", 10)

        # Check entry time
        entry_time_str = meta.get("entry_time", "")
        days_held = 0
        if entry_time_str:
            try:
                entry_time = datetime.fromisoformat(entry_time_str)
                days_held = (datetime.now(timezone.utc) - entry_time).days
            except Exception:
                pass

        action = None

        # Take profit
        if unrealized_plpc >= take_profit:
            action = "take_profit"
            print(f"  [ALPACA] TAKE PROFIT: {symbol} at {unrealized_plpc:+.1f}% "
                  f"(target: {take_profit}%)")

        # Stop loss
        elif unrealized_plpc <= stop_loss:
            action = "stop_loss"
            print(f"  [ALPACA] STOP LOSS: {symbol} at {unrealized_plpc:+.1f}% "
                  f"(limit: {stop_loss}%)")

        # Max hold time exceeded
        elif days_held >= hold_days_max and hold_days_max > 0:
            action = "time_exit"
            print(f"  [ALPACA] TIME EXIT: {symbol} held {days_held} days "
                  f"(max: {hold_days_max})")

        if action:
            # Close position
            close_result = _alpaca_fetch(
                f"/v2/positions/{symbol}",
                api_key, secret_key, paper, method="DELETE"
            )
            actions.append({
                "symbol": symbol,
                "action": action,
                "unrealized_plpc": round(unrealized_plpc, 2),
                "days_held": days_held,
                "market_value": pos.get("market_value", 0),
                "closed": close_result is not None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    return actions


# ================================================================
# PHASE 5: WIRE -- Feed results into ecosystem
# ================================================================

def update_trade_ledger(results):
    """Append Alpaca trades to the shared trade ledger."""
    ledger = _load(DATA / "trade_ledger.json", {"trades": [], "stats": {}})

    for r in results:
        if r.get("success"):
            ledger["trades"].append({
                "ticker": r.get("symbol"),
                "side": r.get("side"),
                "order_id": r.get("order_id"),
                "success": True,
                "order_details": {
                    "expected_cost": float(r.get("notional", 0)),
                    "expected_payout": 0,  # Stocks don't have guaranteed payout
                    "expected_profit": 0,
                    "roi_pct": 0,
                    "platform": "alpaca",
                    "strategy": r.get("order_details", {}).get("strategy", "unknown"),
                },
                "recorded_at": r.get("recorded_at"),
                "source": "ALPACA_TRADER",
            })

    # Update stats
    stats = ledger.get("stats", {})
    alpaca_trades = [t for t in ledger["trades"] if t.get("source") == "ALPACA_TRADER"]
    stats["alpaca_total_trades"] = len(alpaca_trades)
    stats["alpaca_successful"] = sum(1 for t in alpaca_trades if t.get("success"))
    stats["last_alpaca_trade"] = datetime.now(timezone.utc).isoformat()
    ledger["stats"] = stats

    _save(DATA / "trade_ledger.json", ledger)


# ================================================================
# MAIN RUN
# ================================================================

def run():
    """
    ALPACA TRADER: Commission-free stock + ETF compounding engine.

    Every cycle:
    1. ACCOUNT: Check balance, buying power, PDT status
    2. MARKET: Check if market is open
    3. MANAGE: Check existing positions for TP/SL
    4. SCAN: Find opportunities across watchlist
    5. TRADE: Place fractional orders on top picks
    6. WIRE: Feed results into ecosystem
    """
    print("[ALPACA_TRADER] >> Commission-free stock/ETF engine starting...")

    # Load config
    config = _load(DATA / "alpaca_trader_config.json", {
        "enabled": False,
        "paper": True,
        "max_positions": 10,
        "max_allocation_per_position_pct": 20,
        "min_score": 55,
        "strategies_enabled": ["momentum", "mean_reversion", "blue_chip",
                               "sector_rotation", "safe_haven", "dca"],
    })

    # Read nervous system for trade modulation
    _homeo = _load(DATA / "homeostasis_state.json", {})
    _cortex = _load(DATA / "neural_cortex_state.json", {})
    _fire = _load(DATA / "fire_ledger.json", {})
    _equilibrium = _homeo.get("equilibrium", 50)
    _brain_risk = _cortex.get("strategy", {}).get("risk_posture", "moderate")
    _fire_overlap = _fire.get("summary", {}).get("overlap_detected", False)

    # Modulate: low equilibrium / conservative brain -> tighter filters
    if _equilibrium < 20 or _brain_risk == "conservative":
        config["min_score"] = max(config.get("min_score", 55), 70)
        config["max_allocation_per_position_pct"] = min(config.get("max_allocation_per_position_pct", 20), 10)
        print(f"[ALPACA_TRADER] Nervous system override: conservative (eq={_equilibrium}, brain={_brain_risk})")
    elif _fire_overlap:
        config["min_score"] = max(config.get("min_score", 55), 60)
        print(f"[ALPACA_TRADER] Fire overlap: raising min score filter")

    if not config.get("enabled", False):
        print("[ALPACA_TRADER] DISABLED -- not enabled in config")
        # Still save state so ecosystem knows we exist
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "protocol": "alpaca-trader-v1",
            "status": "disabled",
            "message": "Set enabled=true in data/alpaca_trader_config.json "
                       "and add credentials to data/.secrets/alpaca.json",
        }
        _save(DATA / "alpaca_trader_state.json", state)
        return state

    # Authenticate
    api_key, secret_key, paper = _load_alpaca_auth()
    if not api_key or not secret_key:
        print("[ALPACA_TRADER] No credentials -- cannot trade")
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "reason": "no_credentials",
            "message": "Add api_key and secret_key to data/.secrets/alpaca.json",
        }
        _save(DATA / "alpaca_trader_state.json", state)
        return state

    # Override paper from config if set
    paper = config.get("paper", paper)

    # === PHASE 1: ACCOUNT ===
    account = check_account(api_key, secret_key, paper)
    if not account:
        print("[ALPACA_TRADER] Cannot read account -- aborting")
        return {"status": "error", "reason": "account_check_failed"}

    mode = "PAPER" if paper else "LIVE"
    print(f"[ALPACA_TRADER] {mode} | Cash: ${account['cash']:.2f} | "
          f"Buying power: ${account['buying_power']:.2f} | "
          f"Portfolio: ${account['portfolio_value']:.2f}")

    if account.get("trading_blocked"):
        print("[ALPACA_TRADER] Trading is blocked on this account")
        return {"status": "error", "reason": "trading_blocked"}

    # === PHASE 2: MARKET STATUS ===
    market = check_market_status(api_key, secret_key, paper)
    is_open = market.get("is_open", False)

    if not is_open:
        print(f"[ALPACA_TRADER] Market closed. Next open: {market.get('next_open', '?')}")

    # SPEED: If market closed AND no cash AND no positions, do a quick scan-only pass
    # Skip position management and trading (nothing to manage or trade)
    _fast_mode = (not is_open and account.get("buying_power", 0) < 0.50)

    # === PHASE 3: MANAGE existing positions ===
    positions = get_positions(api_key, secret_key, paper)
    print(f"[ALPACA_TRADER] Open positions: {len(positions)}")

    close_actions = []
    if positions:
        close_actions = manage_positions(positions, api_key, secret_key, paper)
        if close_actions:
            print(f"[ALPACA_TRADER] Closed {len(close_actions)} positions")
            # Refresh account after closes
            account = check_account(api_key, secret_key, paper)
            positions = get_positions(api_key, secret_key, paper)

    # === PHASE 4: SCAN for opportunities ===
    # Gather intelligence: try SYNAPTIC_BUS first (one read), fall back to files
    intelligence = {}
    try:
        bus_available = False
        try:
            from SYNAPTIC_BUS import sense
            bus = sense()
            engines = bus.get("engines", {})
            if engines:
                bus_available = True
                # Pull from bus (instant -- already in memory)
                turbo = engines.get("TURBO_TRADER", {}).get("properties", {})
                poly = engines.get("POLYMARKET", {}).get("properties", {})
                arb = engines.get("ARBITRAGE", {}).get("properties", {})
                xpol = engines.get("CROSS_POLLINATOR", {}).get("properties", {})
                mesh = engines.get("SIGNAL_MESH", {}).get("properties", {})

                intelligence["crypto_bullish"] = 0.5
                intelligence["macro_risk"] = 0.25
                intelligence["action"] = "hold"
                if mesh.get("dominant_direction") == "bullish":
                    intelligence["crypto_bullish"] = 0.7
                    intelligence["action"] = "buy"
                if poly.get("edges_found", 0) > 0:
                    intelligence["polymarket_edges"] = poly.get("edges_found", 0)
                if arb.get("opportunities_count", 0) > 0:
                    intelligence["arbitrage_opps"] = arb.get("opportunities_count", 0)
                intelligence["mycelium_health"] = xpol.get("mycelium_health_score", 50)
                intelligence["signal_mesh_conviction"] = mesh.get("conviction_score", 0)
                intelligence["signal_mesh_direction"] = mesh.get("dominant_direction", "neutral")
                # NEURAL_CORTEX brain awareness
                cortex = engines.get("NEURAL_CORTEX", {}).get("properties", {})
                intelligence["brain_risk_posture"] = cortex.get("risk_posture", "moderate")
                intelligence["brain_confidence"] = cortex.get("decision_confidence", 0)
                intelligence["brain_alpaca_pct"] = cortex.get("capital_alpaca_pct", 40)
                intelligence["brain_growth_priority"] = cortex.get("growth_priority", "trading")
        except Exception:
            bus_available = False

        if not bus_available:
            # Fallback: read individual files
            intel = _load(DATA / "prediction_intelligence.json")
            sentiment = intel.get("sentiment", {})
            intelligence["crypto_bullish"] = sentiment.get("crypto_bullish", 0.5)
            intelligence["macro_risk"] = sentiment.get("recession_prob", 0.25)
            intelligence["action"] = sentiment.get("recommended_action", "hold")

            poly = _load(DATA / "polymarket_scan.json")
            if poly.get("top_edges"):
                intelligence["polymarket_edges"] = len(poly.get("top_edges", []))

            kalshi = _load(DATA / "kalshi_scan.json")
            if kalshi.get("markets_scanned"):
                intelligence["kalshi_markets"] = kalshi.get("markets_scanned", 0)

            arb = _load(DATA / "arbitrage_scanner_state.json")
            arb_opps = arb.get("actionable_opportunities", [])
            if isinstance(arb_opps, list) and len(arb_opps) > 0:
                intelligence["arbitrage_opps"] = len(arb_opps)
            elif isinstance(arb_opps, (int, float)) and arb_opps > 0:
                intelligence["arbitrage_opps"] = arb_opps

            xpol = _load(DATA / "cross_pollinator_state.json")
            health = xpol.get("mycelium_health", {})
            intelligence["mycelium_health"] = health.get("score", 50)

        # === GLOBAL INTELLIGENCE: world market context ===
        # VIX, market regime, Fear & Greed, commodities, trending crypto
        global_intel = _load(DATA / "global_intelligence.json")
        if global_intel:
            gsig = global_intel.get("signals", {})
            gprices = gsig.get("live_prices", {})
            gcrypto = global_intel.get("crypto", {})

            intelligence["market_regime"] = gsig.get("market_regime", "UNKNOWN")
            intelligence["risk_level"] = gsig.get("risk_level", "MODERATE")
            intelligence["vix"] = gprices.get("vix", 20)

            # Crypto Fear & Greed overrides generic bullish signal
            fg = gcrypto.get("fear_greed", 50)
            intelligence["fear_greed"] = fg
            if fg <= 25:
                # EXTREME FEAR = contrarian buy signal for crypto
                intelligence["crypto_bullish"] = max(intelligence.get("crypto_bullish", 0.5), 0.75)
                intelligence["fear_greed_signal"] = "EXTREME_FEAR_BUY"
            elif fg >= 75:
                # EXTREME GREED = take profits
                intelligence["crypto_bullish"] = min(intelligence.get("crypto_bullish", 0.5), 0.3)
                intelligence["fear_greed_signal"] = "EXTREME_GREED_SELL"

            # Trending coins — boost score for trending assets
            intelligence["trending_crypto"] = gsig.get("trending_crypto", [])

            # Gold/Oil for commodity-correlated trades
            intelligence["gold_price"] = gprices.get("gold", 0)
            intelligence["oil_price"] = gprices.get("oil_wti", 0)

            # VIX-based risk adjustment
            vix = intelligence["vix"]
            if vix > 30:
                intelligence["macro_risk"] = max(intelligence.get("macro_risk", 0.25), 0.8)
            elif vix > 25:
                intelligence["macro_risk"] = max(intelligence.get("macro_risk", 0.25), 0.6)

        src_count = sum(1 for k in ["crypto_bullish", "polymarket_edges",
                                     "kalshi_markets", "arbitrage_opps",
                                     "mycelium_health", "signal_mesh_conviction",
                                     "market_regime", "fear_greed", "vix"]
                        if k in intelligence)
        src_label = "BUS" if bus_available else "FILES"
        print(f"[ALPACA_TRADER] Intelligence: {src_count} sources ({src_label})")
    except Exception:
        pass

    opportunities = []
    if is_open or True:  # Always scan (crypto is 24/7, and we want to queue)
        opportunities = scan_opportunities(api_key, secret_key, paper, intelligence)

    print(f"[ALPACA_TRADER] Opportunities found: {len(opportunities)}")
    for opp in opportunities[:5]:
        print(f"  {opp['symbol']} | {opp['strategy']} | "
              f"{opp['daily_change_pct']:+.1f}% | score={opp['score']}")

    # === PHASE 5: TRADE ===
    # Crypto trades 24/7 regardless of stock market hours
    # Stocks only during market open
    crypto_opps = [o for o in opportunities if o.get("type") == "crypto"]
    stock_opps = [o for o in opportunities if o.get("type") != "crypto"]

    tradeable_opps = crypto_opps[:]  # Crypto always tradeable
    if is_open:
        tradeable_opps.extend(stock_opps)  # Add stocks only when market open
    elif stock_opps:
        print(f"[ALPACA_TRADER] Market closed -- {len(stock_opps)} stock trades queued for next open")

    new_trades = []
    if tradeable_opps and account.get("buying_power", 0) > 0.50:
        max_pos = config.get("max_positions", 20)
        if len(positions) < max_pos:
            orders = construct_orders(tradeable_opps, account, positions)
            if orders:
                trade_type = "crypto" if not is_open else "mixed"
                print(f"[ALPACA_TRADER] Placing {len(orders)} {trade_type} trades...")
                new_trades = place_orders(orders, api_key, secret_key, paper)
                if new_trades:
                    update_trade_ledger(new_trades)
    elif not tradeable_opps and not is_open:
        print("[ALPACA_TRADER] No crypto opportunities and stock market closed")

    # === PHASE 6: SAVE STATE ===
    successful = sum(1 for t in new_trades if t.get("success"))
    failed = len(new_trades) - successful

    # Save position metadata for TP/SL tracking
    position_meta = {}
    state_old = _load(DATA / "alpaca_trader_state.json")
    position_meta = state_old.get("position_meta", {})

    # Add new position entries
    for t in new_trades:
        if t.get("success"):
            symbol = t.get("symbol")
            meta = t.get("order_details", {})
            position_meta[symbol] = {
                "entry_time": t.get("recorded_at"),
                "strategy": meta.get("strategy"),
                "take_profit_pct": meta.get("take_profit_pct", 2.0),
                "stop_loss_pct": meta.get("stop_loss_pct", -3.0),
                "hold_days_max": meta.get("hold_days_max", 10),
                "score": meta.get("score", 0),
                "entry_price": meta.get("current_price", 0),
                "allocated": meta.get("allocated", 0),
            }

    # Remove closed positions from meta
    held_symbols = {p["symbol"] for p in positions}
    for closed in close_actions:
        sym = closed.get("symbol")
        if sym and sym not in held_symbols:
            position_meta.pop(sym, None)

    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "alpaca-trader-v1",
        "status": "active" if successful > 0 else ("active_no_trades" if is_open else "market_closed"),
        "mode": mode,
        "cash": account.get("cash", 0),
        "buying_power": account.get("buying_power", 0),
        "portfolio_value": account.get("portfolio_value", 0),
        "equity": account.get("equity", 0),
        "positions_count": len(positions),
        "daytrade_count": account.get("daytrade_count", 0),
        "market_open": is_open,
        "next_open": market.get("next_open", ""),
        "opportunities_found": len(opportunities),
        "trades_placed": len(new_trades),
        "successful": successful,
        "failed": failed,
        "positions_closed": len(close_actions),
        "close_actions": close_actions[:10],
        "top_opportunities": [
            {k: v for k, v in o.items() if k != "_meta"}
            for o in opportunities[:10]
        ],
        "position_meta": position_meta,
    }
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    _save(DATA / "alpaca_trader_state.json", state)

    # Broadcast to synaptic bus -- every engine sees this INSTANTLY
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_batch("ALPACA_TRADER", {
            "cash": account.get("cash", 0),
            "portfolio_value": account.get("portfolio_value", 0),
            "buying_power": account.get("buying_power", 0),
            "market_open": is_open,
            "opportunities_found": len(opportunities),
            "trades_placed": len(new_trades),
            "positions_count": len(positions),
            "status": state["status"],
            "platform": "alpaca",
            "signal_direction": "opportunity" if len(opportunities) > 0 and is_open else "neutral",
            "equilibrium": _equilibrium,
            "brain_risk": _brain_risk,
            "fire_overlap": _fire_overlap,
        }, silent=False)
    except Exception:
        pass  # Bus not available -- degrade gracefully

    total_actions = successful + len(close_actions)
    print(f"\n[ALPACA_TRADER] >> Cycle complete:")
    print(f"  Mode: {mode} | Market: {'OPEN' if is_open else 'CLOSED'}")
    print(f"  Portfolio: ${account.get('portfolio_value', 0):.2f}")
    print(f"  Trades: {successful} new | {len(close_actions)} closed")
    print(f"  Positions: {len(positions)} open | {len(opportunities)} opportunities")

    return state


if __name__ == "__main__":
    run()
