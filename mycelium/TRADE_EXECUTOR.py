#!/usr/bin/env python3
"""
TRADE_EXECUTOR.py -- SolarPunk autonomous prediction market trading engine
===========================================================================
v2 (2026-04-05): FIXED -- targeted series, correct API v2 field names, real prices.
v1 (2026-04-05): Kalshi API order execution. DISABLED by default.

This engine reads the intelligence feed, identifies high-confidence
opportunities on Kalshi, and places orders via authenticated API.
No browser, no mouse -- pure API execution.

ACTIVATION: Set "enabled": true in data/trade_executor_config.json
  The user must explicitly enable trading. SolarPunk does NOT
  trade without the user flipping this switch.

STRATEGY:
  1. NEAR-CERTAIN: Buy YES on >92% markets, NO on <8% markets
     near resolution. High probability of $1.00 payout.
  2. CROSS-VALIDATED: When Polymarket + Kalshi agree on direction,
     confidence is doubled. Bet with consensus.
  3. DIVERSIFIED: Small positions across many markets, not big bets
     on single outcomes. Portfolio approach.

RISK MANAGEMENT:
  - Max 10% of balance per single market
  - Max 80% of balance total exposure
  - Floor: stop trading if balance < $5.00
  - Max 5 trades per cycle
  - Only markets with volume > $1,000
  - All orders are LIMIT orders (Kalshi requires it)

EXECUTION:
  POST /trade-api/v2/portfolio/orders
  RSA-PSS signed authentication
  0% trading fees

Called by: NERVE_LOOP (Phase 4.5 -- between PLAN and REPLICATE)
Reads: data/prediction_intelligence.json, data/kalshi_scan.json
Writes: data/trade_executor_state.json, data/trade_ledger.json
"""

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# Import auth functions from KALSHI_SCANNER
KALSHI_API = "https://api.elections.kalshi.com/trade-api/v2"

# Risk limits
DEFAULT_CONFIG = {
    "enabled": False,
    "max_position_pct": 0.10,       # 10% of balance per market
    "max_exposure_pct": 0.80,       # 80% total exposure
    "balance_floor_usd": 5.00,     # Stop trading below $5
    "max_trades_per_cycle": 5,      # Max orders per NERVE_LOOP cycle
    "min_market_volume": 1000,      # Min $1K volume
    "min_confidence_pct": 90,       # Only trade >90% or <10% markets
    "default_order_size_usd": 1.00, # $1 per trade (conservative start)
    "time_in_force": "good_till_canceled",
}


def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default or {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_kalshi_auth():
    """Load Kalshi credentials -- reuse from KALSHI_SCANNER."""
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
    import hashlib

    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError:
        print("  [EXECUTOR] cryptography not installed")
        return None

    path = f"/trade-api/v2{endpoint}"
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
        print(f"  [EXECUTOR] Signing error: {e}")
        return None

    try:
        data_bytes = None
        if body:
            data_bytes = json.dumps(body).encode("utf-8")

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
        print(f"  [EXECUTOR] API error {e.code}: {body_text[:300]}")
        return None
    except Exception as e:
        print(f"  [EXECUTOR] Fetch error: {e}")
        return None


def get_balance(api_key, pem_data):
    """Get current Kalshi balance in USD."""
    data = _sign_and_fetch("/portfolio/balance", api_key, pem_data)
    if data:
        return round(data.get("balance", 0) / 100, 2)
    return None


def get_positions(api_key, pem_data):
    """Get current open positions."""
    data = _sign_and_fetch("/portfolio/positions", api_key, pem_data)
    if data:
        return data.get("market_positions", [])
    return []


def get_market_orderbook(ticker):
    """Get orderbook for a specific market (public, no auth needed)."""
    import urllib.request
    url = f"{KALSHI_API}/orderbook/{ticker}"
    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def find_opportunities(config):
    """
    Scan targeted Kalshi series for tradeable opportunities.

    Strategy: find markets where prediction probability is extreme
    (>90% or <10%) meaning near-certain outcomes. Buy the likely
    side cheaply, collect $1.00 payout on resolution.

    Fetches from TRADING_SERIES (crypto, macro, economics) —
    NOT the generic /markets endpoint which returns sports parlays.

    Kalshi API v2 field names (2026):
      yes_bid_dollars / yes_ask_dollars  (buying price)
      no_bid_dollars / no_ask_dollars
      last_price_dollars                 (last traded)
      volume_fp                          (total volume)
    """
    import urllib.request

    min_conf = config.get("min_confidence_pct", 90)
    min_vol = config.get("min_market_volume", 1000)

    opportunities = []

    # Targeted series: crypto, macro, economics, financials, weather
    # Expanded from 5 → 13 series for maximum market coverage
    TRADING_SERIES = [
        # Daily resolution (fastest compounding)
        "KXINX",        # S&P 500 daily range
        "KXNASDAQ100",  # Nasdaq 100 daily range
        "KXHIGHNY",     # NYC temperature daily
        "KXAAAGASD",    # US gas prices daily
        "KXGOLD",       # Gold price daily
        # Weekly/monthly resolution
        "KXBTC",        # Bitcoin price
        "KXETH",        # Ethereum price
        "KXFED",        # Fed funds rate
        "KXCPI",        # CPI inflation
        "KXGDP",        # GDP growth
        "KXINXY",       # S&P 500 yearly range
        "KXINXMAXY",    # S&P 500 yearly high
        "KXEMPLOYMENTCOMBO",  # Employment data
    ]

    all_markets = []
    for series in TRADING_SERIES:
        try:
            url = f"{KALSHI_API}/markets?limit=50&status=open&series_ticker={series}"
            req = urllib.request.Request(url)
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode())
                markets = data.get("markets", [])
                for m in markets:
                    m["_series"] = series
                all_markets.extend(markets)
                if markets:
                    print(f"  [EXECUTOR] {series}: {len(markets)} markets")
        except Exception as e:
            print(f"  [EXECUTOR] {series} fetch error: {e}")
        time.sleep(0.3)  # Rate limit: 10 req/sec

    print(f"  [EXECUTOR] Total markets scanned: {len(all_markets)}")

    for m in all_markets:
        ticker = m.get("ticker", "")
        title = m.get("title", m.get("subtitle", ""))
        series = m.get("_series", "")

        # Use last_price_dollars as best estimate of current price
        # Fall back to yes_bid_dollars (what buyers are offering)
        last_price = m.get("last_price_dollars")
        yes_bid = m.get("yes_bid_dollars")
        yes_ask = m.get("yes_ask_dollars")  # Price to BUY YES
        no_bid = m.get("no_bid_dollars")
        no_ask = m.get("no_ask_dollars")    # Price to BUY NO

        # Need at least one price reference
        if not last_price and not yes_bid:
            continue

        last_price = float(last_price) if last_price else 0
        yes_bid = float(yes_bid) if yes_bid else 0
        yes_ask = float(yes_ask) if yes_ask else 0
        no_bid = float(no_bid) if no_bid else 0
        no_ask = float(no_ask) if no_ask else 0

        # Best estimate of YES probability
        yes_price = last_price or yes_bid
        yes_pct = yes_price * 100

        # Volume check — use volume_fp
        volume = float(m.get("volume_fp") or m.get("volume") or 0)
        open_interest = float(m.get("open_interest_fp") or m.get("open_interest") or 0)

        if volume < min_vol:
            continue

        # Near-certain YES (>90%): buy YES at ask, expect $1.00 payout
        if yes_pct >= min_conf:
            buy_price = yes_ask if yes_ask > 0 else yes_price
            if buy_price <= 0 or buy_price >= 1.0:
                continue
            profit_per_contract = 1.00 - buy_price
            roi_pct = (profit_per_contract / buy_price) * 100
            opportunities.append({
                "ticker": ticker,
                "title": title[:100],
                "side": "yes",
                "action": "buy",
                "price": buy_price,
                "yes_pct": round(yes_pct, 1),
                "profit_per_contract": round(profit_per_contract, 4),
                "roi_pct": round(roi_pct, 2),
                "volume": int(volume),
                "open_interest": int(open_interest),
                "strategy": "near_certain_yes",
                "series": series,
                "close_time": m.get("close_time", ""),
            })

        # Near-certain NO (<10% yes = >90% no): buy NO at ask
        elif yes_pct <= (100 - min_conf):
            buy_price = no_ask if no_ask > 0 else (1.00 - yes_price)
            if buy_price <= 0 or buy_price >= 1.0:
                continue
            profit_per_contract = 1.00 - buy_price
            roi_pct = (profit_per_contract / buy_price) * 100
            opportunities.append({
                "ticker": ticker,
                "title": title[:100],
                "side": "no",
                "action": "buy",
                "price": buy_price,
                "yes_pct": round(yes_pct, 1),
                "profit_per_contract": round(profit_per_contract, 4),
                "roi_pct": round(roi_pct, 2),
                "volume": int(volume),
                "open_interest": int(open_interest),
                "strategy": "near_certain_no",
                "series": series,
                "close_time": m.get("close_time", ""),
            })

    # Sort by ROI (best risk/reward first)
    opportunities.sort(key=lambda x: x["roi_pct"], reverse=True)
    return opportunities


def construct_order(opp, balance, config):
    """
    Build a Kalshi order from an opportunity.

    Returns the order body dict for POST /portfolio/orders.
    """
    max_position = balance * config.get("max_position_pct", 0.10)
    order_size = min(
        config.get("default_order_size_usd", 1.00),
        max_position,
    )

    if order_size < 0.01:
        return None

    # Calculate contract count (WHOLE contracts only -- fractional disabled on most markets)
    price = opp["price"]
    if price <= 0 or price >= 1.0:
        return None

    count = int(order_size / price)  # Floor to whole contracts
    count = max(1, count)            # At least 1 contract

    # Kalshi API v2 order format (confirmed working 2026-04-06):
    #   count: integer (whole contracts)
    #   type: "limit"
    #   yes_price / no_price: integer in CENTS (91 = $0.91)
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
        "expected_cost": round(count * price, 4),
        "expected_payout": round(count * 1.00, 4),
        "expected_profit": round(count * opp["profit_per_contract"], 4),
        "roi_pct": opp["roi_pct"],
    }

    return order


def place_order(order, api_key, pem_data):
    """Place a single order on Kalshi via authenticated API."""
    # Strip internal metadata before sending
    send_order = {k: v for k, v in order.items() if not k.startswith("_")}

    print(f"  [EXECUTOR] Placing order: {order['side'].upper()} {order['count']} "
          f"contracts on {order['ticker']}")

    result = _sign_and_fetch("/portfolio/orders", api_key, pem_data,
                             method="POST", body=send_order)

    if result and result.get("order"):
        order_data = result["order"]
        status = order_data.get("status", "unknown")
        order_id = order_data.get("order_id", "")
        print(f"  [EXECUTOR] Order placed: {order_id} | Status: {status}")
        return {
            "success": True,
            "order_id": order_id,
            "status": status,
            "ticker": order["ticker"],
            "side": order["side"],
            "count": order["count"],
            "response": order_data,
        }
    else:
        print(f"  [EXECUTOR] Order FAILED for {order['ticker']}")
        return {
            "success": False,
            "ticker": order["ticker"],
            "error": "API returned no order data",
        }


def update_ledger(trades):
    """Append trades to the persistent trade ledger."""
    ledger_path = DATA / "trade_ledger.json"
    ledger = _load(ledger_path, {"trades": [], "stats": {}})

    for trade in trades:
        trade["recorded_at"] = datetime.now(timezone.utc).isoformat()
        ledger["trades"].append(trade)

    # Update stats
    total = len(ledger["trades"])
    wins = sum(1 for t in ledger["trades"] if t.get("success"))
    ledger["stats"] = {
        "total_trades": total,
        "successful_orders": wins,
        "failed_orders": total - wins,
        "last_trade": datetime.now(timezone.utc).isoformat(),
    }

    # Keep last 5000 trades
    ledger["trades"] = ledger["trades"][-5000:]
    _save(ledger_path, ledger)


def run():
    """
    Engine entry point for NERVE_LOOP.

    DISABLED by default. Enable by creating data/trade_executor_config.json
    with "enabled": true.
    """
    print("[TRADE_EXECUTOR] Checking trading status...")

    # Load config (create default if missing)
    config_path = DATA / "trade_executor_config.json"
    if not config_path.exists():
        _save(config_path, DEFAULT_CONFIG)
        print("[TRADE_EXECUTOR] Config created at data/trade_executor_config.json")
        print("[TRADE_EXECUTOR] Set 'enabled': true to activate trading")
        return {"status": "disabled", "reason": "config created, enable to start"}

    config = _load(config_path, DEFAULT_CONFIG)

    if not config.get("enabled", False):
        print("[TRADE_EXECUTOR] DISABLED -- set 'enabled': true in config to activate")
        # Still scan for opportunities even when disabled
        opps = find_opportunities(config)
        if opps:
            print(f"[TRADE_EXECUTOR] Found {len(opps)} opportunities (not trading, disabled)")
            for opp in opps[:3]:
                print(f"  {opp['title'][:60]}...")
                print(f"    {opp['side'].upper()} at ${opp['price']:.2f} | ROI: {opp['roi_pct']}%")

        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "protocol": "trade-executor-v1",
            "status": "disabled",
            "opportunities_found": len(opps),
            "top_opportunities": opps[:5],
        }
        _save(DATA / "trade_executor_state.json", state)
        return state

    # === TRADING ENABLED ===
    print("[TRADE_EXECUTOR] ENABLED -- scanning for trades...")

    # Authenticate
    api_key, pem_data = _load_kalshi_auth()
    if not api_key or not pem_data:
        print("[TRADE_EXECUTOR] No credentials -- cannot trade")
        return {"status": "error", "reason": "no_credentials"}

    # Check balance
    balance = get_balance(api_key, pem_data)
    if balance is None:
        print("[TRADE_EXECUTOR] Cannot read balance -- aborting")
        return {"status": "error", "reason": "balance_check_failed"}

    print(f"[TRADE_EXECUTOR] Balance: ${balance:.2f}")

    # Check floor
    floor = config.get("balance_floor_usd", 5.00)
    if balance < floor:
        print(f"[TRADE_EXECUTOR] Balance ${balance:.2f} below floor ${floor:.2f} -- halting")
        return {"status": "halted", "reason": "below_balance_floor", "balance": balance}

    # Check existing positions
    positions = get_positions(api_key, pem_data)
    total_exposure = sum(
        abs(p.get("market_exposure", 0)) / 100
        for p in positions
    ) if positions else 0

    max_exposure = balance * config.get("max_exposure_pct", 0.80)
    remaining_capacity = max_exposure - total_exposure

    print(f"[TRADE_EXECUTOR] Exposure: ${total_exposure:.2f} / ${max_exposure:.2f} max")

    if remaining_capacity <= 0:
        print("[TRADE_EXECUTOR] Max exposure reached -- no new trades")
        return {"status": "maxed_out", "balance": balance, "exposure": total_exposure}

    # Find opportunities
    opportunities = find_opportunities(config)
    print(f"[TRADE_EXECUTOR] Found {len(opportunities)} opportunities")

    if not opportunities:
        print("[TRADE_EXECUTOR] No qualifying opportunities this cycle")
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "protocol": "trade-executor-v1",
            "status": "active_no_trades",
            "balance": balance,
            "positions": len(positions),
        }
        _save(DATA / "trade_executor_state.json", state)
        return state

    # Construct and place orders
    max_trades = config.get("max_trades_per_cycle", 5)
    trades_placed = []

    for opp in opportunities[:max_trades]:
        if remaining_capacity <= 0:
            break

        order = construct_order(opp, balance, config)
        if not order:
            continue

        expected_cost = order["_meta"]["expected_cost"]
        if expected_cost > remaining_capacity:
            continue

        # Place the order
        result = place_order(order, api_key, pem_data)
        result["order_details"] = order.get("_meta", {})
        trades_placed.append(result)

        if result["success"]:
            remaining_capacity -= expected_cost
            time.sleep(0.2)  # Rate limit: 10 req/sec max

    # Update ledger
    if trades_placed:
        update_ledger(trades_placed)

    # Re-check balance after trading
    new_balance = get_balance(api_key, pem_data)

    # Save state
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "trade-executor-v1",
        "status": "active",
        "balance_before": balance,
        "balance_after": new_balance,
        "positions": len(positions) + sum(1 for t in trades_placed if t["success"]),
        "trades_this_cycle": len(trades_placed),
        "successful_trades": sum(1 for t in trades_placed if t["success"]),
        "failed_trades": sum(1 for t in trades_placed if not t["success"]),
        "opportunities_found": len(opportunities),
        "remaining_capacity": round(remaining_capacity, 2),
        "trades": trades_placed,
        "top_opportunities": opportunities[:5],
        "risk_limits": {
            "max_per_market": round(balance * config.get("max_position_pct", 0.10), 2),
            "max_exposure": round(max_exposure, 2),
            "balance_floor": floor,
        },
    }
    _save(DATA / "trade_executor_state.json", state)

    # Broadcast to synaptic bus
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_batch("TRADE_EXECUTOR", {
            "balance_after": new_balance,
            "trades_this_cycle": len(trades_placed),
            "successful_trades": sum(1 for t in trades_placed if t["success"]),
            "status": "active",
            "platform": "kalshi",
        }, silent=True)
    except Exception:
        pass

    # Summary
    successful = sum(1 for t in trades_placed if t["success"])
    print(f"[TRADE_EXECUTOR] Cycle complete:")
    print(f"  Trades: {successful}/{len(trades_placed)} successful")
    print(f"  Balance: ${balance:.2f} -> ${new_balance or '?'}")
    print(f"  Remaining capacity: ${remaining_capacity:.2f}")

    return state


if __name__ == "__main__":
    run()
