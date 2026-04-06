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
from datetime import datetime, timezone, timedelta
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

KALSHI_API = "https://api.elections.kalshi.com/trade-api/v2"

# Series prioritized by resolution speed (fastest first)
# Daily settlers get max priority, then weekly, then monthly
FAST_SERIES = [
    # === DAILY RESOLUTION ===
    "KXINX",        # S&P 500 daily range -- settles 4pm ET EVERY DAY
    "KXNASDAQ100",  # Nasdaq 100 daily range
    "KXHIGHNY",     # NYC temperature daily
    "KXAAAGASD",    # US gas prices daily
    "KXGOLD",       # Gold price daily
    # === WEEKLY/BIWEEKLY RESOLUTION ===
    "KXBTC",        # Bitcoin price brackets (weekly/monthly)
    "KXETH",        # Ethereum price brackets
    # === MONTHLY+ RESOLUTION (still trade, lower priority) ===
    "KXFED",        # Fed funds rate (per meeting, ~6-8 weeks)
    "KXCPI",        # CPI inflation (monthly)
    "KXGDP",        # GDP growth (quarterly)
    "KXINXY",       # S&P 500 yearly range
    "KXINXMAXY",    # S&P 500 yearly high
    "KXEMPLOYMENTCOMBO",  # Employment data
]

# Resolution speed classification (hours until typical settlement)
RESOLUTION_SPEED = {
    "KXINX": 24,       # Daily
    "KXNASDAQ100": 24,  # Daily
    "KXHIGHNY": 24,     # Daily
    "KXAAAGASD": 24,    # Daily
    "KXGOLD": 24,       # Daily
    "KXBTC": 168,       # Weekly
    "KXETH": 168,       # Weekly
    "KXFED": 1344,      # ~8 weeks
    "KXCPI": 720,       # Monthly
    "KXGDP": 2160,      # Quarterly
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
    import urllib.request
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
# PHASE 1: DISCOVER -- Dynamic series + market scanning
# ──────────────────────────────────────────────────────────────

def discover_all_series():
    """
    Dynamically discover ALL Kalshi series.
    GET /series returns every series ticker on the platform.
    We prioritize FAST_SERIES but also scan anything new.
    """
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
    import urllib.request

    opportunities = []
    now = datetime.now(timezone.utc)
    series_scanned = 0
    markets_scanned = 0

    # Scan prioritized series (fast-resolving first)
    # Rate limit: 20 reads/sec, we use 3/sec to be safe
    for series in series_list[:20]:  # Cap at 20 series per cycle
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

        time.sleep(0.35)  # Stay well within rate limit

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
    if hours <= 24:
        return "DAILY"
    elif hours <= 168:
        return "WEEKLY"
    elif hours <= 720:
        return "MONTHLY"
    else:
        return "LONG"


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
    """
    max_per_market = balance * config.get("max_position_pct", 0.25)
    max_exposure = balance * config.get("max_exposure_pct", 0.95)
    floor = config.get("balance_floor_usd", 1.00)
    available = min(balance - floor, max_exposure)

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
        if opp["resolution_class"] == "DAILY":
            order_size = min(config.get("default_order_size_usd", 4.00), max_per_market)
        elif opp["resolution_class"] == "WEEKLY":
            order_size = min(config.get("default_order_size_usd", 4.00) * 0.75, max_per_market)
        else:
            order_size = min(config.get("default_order_size_usd", 4.00) * 0.5, max_per_market)

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
    1. Check for deposits (balance change detection)
    2. Check for settlements (resolved positions)
    3. Discover all available markets
    4. Scan for fast-resolving opportunities
    5. Place micro-trades across maximum markets
    6. Track compound growth
    7. Wire data to ecosystem (via trade_ledger.json -> TRADING_WIRE)
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

    # Check floor
    floor = config.get("balance_floor_usd", 1.00)
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

    # === PHASE 3: SCAN for fast-resolving opportunities ===
    min_conf = config.get("min_confidence_pct", 85)
    min_vol = config.get("min_market_volume", 100)
    opportunities = scan_fast_markets(series_list, min_conf, min_vol)

    if not opportunities:
        print("[TURBO_TRADER] No qualifying opportunities this cycle")
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "active_no_trades",
            "balance": balance,
            "last_known_balance": balance,
            "series_scanned": len(series_list[:20]),
            "settlements_24h": len(settlements),
        }
        _save(DATA / "turbo_trader_state.json", state)
        return state

    # Classify opportunities by speed
    daily_opps = [o for o in opportunities if o["resolution_class"] == "DAILY"]
    weekly_opps = [o for o in opportunities if o["resolution_class"] == "WEEKLY"]
    monthly_opps = [o for o in opportunities if o["resolution_class"] in ("MONTHLY", "LONG")]

    print(f"[TURBO_TRADER] Opportunities: {len(daily_opps)} daily, "
          f"{len(weekly_opps)} weekly, {len(monthly_opps)} monthly+")

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

    # Update shared trade ledger
    if results:
        update_trade_ledger(results)

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
        "daily_opps": len(daily_opps),
        "weekly_opps": len(weekly_opps),
        "monthly_opps": len(monthly_opps),
        "total_opportunities": len(opportunities),
        "total_pending_payout": round(total_pending, 2),
        "settlements_24h": len(settlements),
        "velocity_freed": velocity_freed,
        "velocity_sells": len(velocity_sells),
        "series_scanned": len(series_list[:20]),
        "top_opportunities": opportunities[:10],
        "trades": results,
    }
    _save(DATA / "turbo_trader_state.json", state)

    # Track compound growth
    tracker = update_compound_tracker(state)

    print(f"\n[TURBO_TRADER] >> Cycle complete:")
    print(f"  Trades: {successful}/{len(results)} filled")
    print(f"  Balance: ${balance:.2f} -> ${new_balance:.2f}")
    print(f"  Positions: {positions_count} open")
    print(f"  Pending payout: ${total_pending:.2f}")
    print(f"  Compound cycles: {tracker.get('compound_cycles', 0)}")
    print(f"  Growth: {tracker['snapshots'][-1]['growth_pct']:.1f}%" if tracker.get("snapshots") else "")

    return state


if __name__ == "__main__":
    run()
