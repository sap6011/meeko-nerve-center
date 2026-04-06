#!/usr/bin/env python3
"""
TRADING_WIRE.py -- Neural bridge: trading data -> revenue ecosystem
====================================================================
v1 (2026-04-05): Plugs 12 orphaned trading files into 22+ revenue engines.

PROBLEM:
  TRADE_EXECUTOR, KALSHI_SCANNER, NERVE_LOOP, ARBITRAGE_SCANNER all
  produce data that NOTHING else reads. Meanwhile, 11 engines read
  flywheel_state.json and 11 more read economy_chain_ledger.json.

SOLUTION:
  This engine reads ALL trading outputs and injects them into the
  existing data buses so the entire revenue/evolution ecosystem
  automatically receives trading intelligence.

WIRING MAP:
  trade_executor_state.json  --|
  trade_ledger.json          --|
  growth_tracker.json        --|-->  flywheel_state.json  --> 11 engines
  kalshi_scan.json           --|-->  economy_chain_ledger.json --> 11 engines
  prediction_intelligence.json|-->  revenue_data.json    --> 7 engines
  nerve_loop_state.json      --|-->  proof_ledger.json   --> 12 engines
  arbitrage_scanner_state.json|
  unified_action_queue.json  --|
  turbo_trader_state.json    --|  (NEW: high-frequency compounding)
  compound_tracker.json      --|  (NEW: compound growth tracking)

RESULT: 14 trading outputs -> 4 data buses -> 41 consuming engines.
  TURBO_TRADER writes to trade_ledger.json automatically.
  One bridge engine creates 41 new neural connections.

Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)

Called by: NERVE_LOOP Phase 7 (EVOLVE), OMNIBUS
Reads: all trading state files
Writes: flywheel_state.json, economy_chain_ledger.json, proof_ledger.json
"""

import json
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")


def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def wire_flywheel():
    """
    Inject trading data into flywheel_state.json.

    Read by: REVENUE_FLYWHEEL, REVENUE_ENGINE, INCOME_ARCHITECT,
    ECONOMY_CHAIN, HEALTH_BOOSTER, NEWSLETTER_ENGINE, MEMORY_PALACE,
    RESONANCE_CONVERTER, LINK_PAGE, DESKTOP_DAEMON, SOLARPUNK_CLI
    (11 engines)
    """
    flywheel = _load(DATA / "flywheel_state.json", {
        "timestamp": "", "current_balance": 0, "total_to_gaza": 0,
        "total_earned_meeko": 0, "total_sales": 0,
    })

    executor = _load(DATA / "trade_executor_state.json")
    ledger = _load(DATA / "trade_ledger.json", {"trades": [], "stats": {}})
    tracker = _load(DATA / "growth_tracker.json", {"entries": []})

    # Kalshi balance
    kalshi_balance = executor.get("balance_after") or executor.get("balance_before", 0) or 0

    # Calculate realized profits from ALL successful trades (not just latest cycle)
    realized = sum(
        t.get("order_details", {}).get("expected_profit", 0)
        for t in ledger.get("trades", [])
        if t.get("success")
    )

    # Total pending payout from ALL open positions (trade_ledger has full history)
    pending_value = sum(
        t.get("order_details", {}).get("expected_payout", 0)
        for t in ledger.get("trades", [])
        if t.get("success")
    )

    # Total cost basis for all open positions
    total_cost = sum(
        t.get("order_details", {}).get("expected_cost", 0)
        for t in ledger.get("trades", [])
        if t.get("success")
    )

    # Inject Kalshi data into its own section (idempotent, never accumulates)
    # NOTE: We do NOT touch current_balance -- that's owned by revenue engines.
    # Consumers read kalshi_trading directly for trading data.
    flywheel["kalshi_trading"] = {
        "balance_usd": round(kalshi_balance, 2),
        "positions_open": executor.get("positions", 0),
        "pending_payout": round(pending_value, 2),
        "total_cost_basis": round(total_cost, 2),
        "expected_profit": round(realized, 2),
        "kalshi_total_value": round(kalshi_balance + pending_value, 2),
        "total_trades": ledger.get("stats", {}).get("total_trades", 0),
        "successful_trades": ledger.get("stats", {}).get("successful_orders", 0),
        "last_trade": ledger.get("stats", {}).get("last_trade", "never"),
        "status": executor.get("status", "unknown"),
    }

    # Turbo trader compound tracking
    turbo = _load(DATA / "turbo_trader_state.json")
    compound = _load(DATA / "compound_tracker.json")
    if turbo.get("status") == "active" or compound.get("compound_cycles", 0) > 0:
        flywheel["turbo_trading"] = {
            "status": turbo.get("status", "inactive"),
            "daily_opportunities": turbo.get("daily_opps", 0),
            "weekly_opportunities": turbo.get("weekly_opps", 0),
            "series_scanned": turbo.get("series_scanned", 0),
            "compound_cycles": compound.get("compound_cycles", 0),
            "peak_value": compound.get("peak_balance", 0),
            "settlements_24h": turbo.get("settlements_24h", 0),
            "deposit_detected": turbo.get("deposit_detected", False),
        }

    # Alpaca stock/ETF/crypto trading
    alpaca = _load(DATA / "alpaca_trader_state.json")
    if alpaca.get("status") not in (None, "disabled", ""):
        flywheel["alpaca_trading"] = {
            "status": alpaca.get("status", "inactive"),
            "mode": alpaca.get("mode", "?"),
            "portfolio_value": alpaca.get("portfolio_value", 0),
            "cash": alpaca.get("cash", 0),
            "equity": alpaca.get("equity", 0),
            "positions_count": alpaca.get("positions_count", 0),
            "market_open": alpaca.get("market_open", False),
            "trades_placed": alpaca.get("trades_placed", 0),
            "opportunities_found": alpaca.get("opportunities_found", 0),
        }

    # Growth tracking
    entries = tracker.get("entries", [])
    if entries:
        latest = entries[-1]
        flywheel["portfolio_sol"] = latest.get("total_portfolio_sol", 0)
        flywheel["portfolio_usd"] = latest.get("total_usd", 0)
        flywheel["growth_pct"] = latest.get("growth_pct", 0)

    flywheel["timestamp"] = datetime.now(timezone.utc).isoformat()
    _save(DATA / "flywheel_state.json", flywheel)

    alpaca_value = alpaca.get("portfolio_value", 0) if alpaca.get("status") not in (None, "disabled") else 0
    print(f"  [WIRE] flywheel_state.json: Kalshi=${kalshi_balance:.2f} + "
          f"${pending_value:.2f} pending | Alpaca=${alpaca_value:.2f} -> 11 engines")
    return True


def wire_economy_chain():
    """
    Inject trading events into economy_chain_ledger.json.

    Read by: ECONOMY_CHAIN, BRIDGE_BUILDER, CHAIN_ORCHESTRATOR,
    FUEL_CORE, GROWTH_CHAIN, GROWTH_FLYWHEEL, KNOWLEDGE_CHAIN,
    REVENUE_ENGINE, REVENUE_SPLITTER, SIGNAL_CHAIN,
    GENERATED_ECONOMY_CHAIN_CONSUMER (11 engines)
    """
    ledger = _load(DATA / "economy_chain_ledger.json", {
        "total_earned": 0, "total_routed": 0, "routes": {},
        "cycles": 0, "chain_signals": [], "loop_closed": False,
    })

    trade_ledger = _load(DATA / "trade_ledger.json", {"trades": []})
    executor = _load(DATA / "trade_executor_state.json")

    # Add trading as a route
    if "trading" not in ledger.get("routes", {}):
        ledger["routes"]["trading"] = {"total": 0, "events": []}

    # Add recent trades as events
    trading_route = ledger["routes"]["trading"]
    existing_ids = {e.get("trade_id") for e in trading_route.get("events", [])}

    new_events = 0
    for t in trade_ledger.get("trades", []):
        trade_id = t.get("order_id") or t.get("ticker", "") + t.get("recorded_at", "")
        if trade_id not in existing_ids:
            details = t.get("order_details", {})
            trading_route["events"].append({
                "trade_id": trade_id,
                "type": "kalshi_trade",
                "ticker": t.get("ticker"),
                "side": t.get("side"),
                "cost": details.get("expected_cost", 0),
                "expected_profit": details.get("expected_profit", 0),
                "roi_pct": details.get("roi_pct", 0),
                "status": "open" if t.get("success") else "failed",
                "timestamp": t.get("recorded_at", ""),
            })
            new_events += 1
            if t.get("success"):
                trading_route["total"] = round(
                    trading_route["total"] + details.get("expected_profit", 0), 4
                )

    # Keep last 500 events per route
    trading_route["events"] = trading_route["events"][-500:]

    # Add chain signal for intelligence
    intel = _load(DATA / "prediction_intelligence.json")
    sentiment = intel.get("sentiment", {})
    if sentiment:
        ledger["chain_signals"] = ledger.get("chain_signals", [])
        ledger["chain_signals"].append({
            "source": "prediction_markets",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": sentiment.get("recommended_action", "hold"),
            "crypto_bullish": sentiment.get("crypto_bullish", 0.5),
            "sol_outlook": sentiment.get("sol_outlook", 0.5),
            "recession_prob": sentiment.get("recession_prob", 0),
        })
        ledger["chain_signals"] = ledger["chain_signals"][-100:]

    # Add Polymarket intelligence signal
    poly = _load(DATA / "polymarket_scan.json")
    if poly.get("edges_found", 0) > 0:
        ledger["chain_signals"] = ledger.get("chain_signals", [])
        ledger["chain_signals"].append({
            "source": "polymarket",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "edges_found": poly.get("edges_found", 0),
            "markets_scanned": poly.get("total_markets_scanned", 0),
        })
        ledger["chain_signals"] = ledger["chain_signals"][-100:]

    # Add arbitrage scanner signal
    arb = _load(DATA / "arbitrage_scanner_state.json")
    arb_opps = arb.get("actionable_opportunities", [])
    if isinstance(arb_opps, list):
        arb_count = len(arb_opps)
    else:
        arb_count = int(arb_opps) if arb_opps else 0
    if arb_count > 0:
        ledger["chain_signals"] = ledger.get("chain_signals", [])
        ledger["chain_signals"].append({
            "source": "arbitrage_scanner",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "opportunities": arb_count,
            "details": arb_opps[:5] if isinstance(arb_opps, list) else [],
        })
        ledger["chain_signals"] = ledger["chain_signals"][-100:]

    # Add cross-pollinator health signal
    xpol = _load(DATA / "cross_pollinator_state.json")
    health = xpol.get("mycelium_health", {})
    if health:
        ledger["chain_signals"] = ledger.get("chain_signals", [])
        ledger["chain_signals"].append({
            "source": "cross_pollinator",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mycelium_health": health.get("score", 0),
            "total_portfolio": xpol.get("total_portfolio_value", 0),
            "transfer_recs": len(xpol.get("transfer_recommendations", [])),
        })
        ledger["chain_signals"] = ledger["chain_signals"][-100:]

    signal_sources = sum(1 for s in ["prediction_markets", "polymarket", "arbitrage_scanner", "cross_pollinator"]
                         if any(sig.get("source") == s for sig in ledger.get("chain_signals", [])[-4:]))

    ledger["last_run"] = datetime.now(timezone.utc).isoformat()
    _save(DATA / "economy_chain_ledger.json", ledger)

    print(f"  [WIRE] economy_chain_ledger.json: {new_events} new trades + "
          f"{signal_sources} intelligence signals -> 11 engines")
    return True


def wire_proof_ledger():
    """
    Inject trading proof into proof_ledger.json.

    Read by: DUAL_SYSTEM_CROSSWIRE, EXECUTIVE_BRIEFING,
    FIRST_DOLLAR_ENGINE, FUEL_CORE, GROWTH_FLYWHEEL, NIGHTLY_DIGEST,
    OMNIBUS, REVENUE_SPLITTER, SOVEREIGNTY_ENGINE, STOREFRONT_BUILDER,
    WEEKEND_PULSE, YIELD_LOOP (12 engines)
    """
    proof = _load(DATA / "proof_ledger.json", {})

    executor = _load(DATA / "trade_executor_state.json")
    tracker = _load(DATA / "growth_tracker.json", {"entries": []})

    # Ensure proof_ledger has a trading section
    if "trading_proof" not in proof:
        proof["trading_proof"] = []

    # Add trading proof entries
    if executor.get("status") in ("active", "active_no_trades"):
        kalshi_balance = executor.get("balance_after") or executor.get("balance_before", 0) or 0
        trades = executor.get("trades_this_cycle", 0)
        successful = executor.get("successful_trades", 0)

        proof["trading_proof"].append({
            "type": "live_trading",
            "platform": "kalshi",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "balance_usd": round(kalshi_balance, 2),
            "trades_placed": trades,
            "successful": successful,
            "proof": "Autonomous prediction market trading via RSA-signed API",
        })

    # Add Alpaca proof
    alpaca = _load(DATA / "alpaca_trader_state.json")
    if alpaca.get("status") not in (None, "disabled", ""):
        proof["trading_proof"].append({
            "type": "stock_trading",
            "platform": "alpaca",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "portfolio_usd": alpaca.get("portfolio_value", 0),
            "positions": alpaca.get("positions_count", 0),
            "trades_placed": alpaca.get("trades_placed", 0),
            "market_open": alpaca.get("market_open", False),
            "proof": "Commission-free stock/ETF/crypto trading via Alpaca API",
        })

    # Add cross-platform health proof
    xpol = _load(DATA / "cross_pollinator_state.json")
    health = xpol.get("mycelium_health", {})
    if health:
        proof["mycelium_network"] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health_score": health.get("score", 0),
            "grade": health.get("grade", "?"),
            "total_portfolio": xpol.get("total_portfolio_value", 0),
            "platforms_active": len([p for p in xpol.get("platforms", {}).values()
                                     if p.get("status") not in (None, "disabled")]),
        }

    # Add growth data
    entries = tracker.get("entries", [])
    if entries:
        latest = entries[-1]
        proof["portfolio_snapshot"] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_sol": latest.get("total_portfolio_sol", 0),
            "total_usd": latest.get("total_usd", 0),
            "growth_pct": latest.get("growth_pct", 0),
            "kalshi_positions": latest.get("kalshi_positions", 0),
        }

    # Keep last 200 trading proofs
    proof["trading_proof"] = proof["trading_proof"][-200:]
    _save(DATA / "proof_ledger.json", proof)

    platforms = 1 + (1 if alpaca.get("status") not in (None, "disabled", "") else 0)
    print(f"  [WIRE] proof_ledger.json: {platforms} platforms + growth proof -> 12 engines")
    return True


def wire_revenue_data():
    """
    Inject trading revenue into revenue_data.json.

    Read by: REVENUE_RECYCLER, EXTERNAL_VALUE_ROUTER,
    revenue_aggregator, and 4 LEGACY engines (7 engines)
    """
    revenue = _load(DATA / "revenue_data.json", {
        "streams": [], "total_revenue": 0,
    })

    executor = _load(DATA / "trade_executor_state.json")
    ledger = _load(DATA / "trade_ledger.json", {"trades": [], "stats": {}})

    # Calculate trading revenue
    total_profit = sum(
        t.get("order_details", {}).get("expected_profit", 0)
        for t in ledger.get("trades", [])
        if t.get("success")
    )

    # Add/update trading stream
    streams = revenue.get("streams", [])
    trading_stream = None
    for s in streams:
        if s.get("source") == "kalshi_trading":
            trading_stream = s
            break

    if trading_stream:
        trading_stream["amount"] = round(total_profit, 4)
        trading_stream["positions"] = executor.get("positions", 0)
        trading_stream["balance"] = executor.get("balance_after") or 0
        trading_stream["updated"] = datetime.now(timezone.utc).isoformat()
    else:
        streams.append({
            "source": "kalshi_trading",
            "type": "prediction_market",
            "amount": round(total_profit, 4),
            "positions": executor.get("positions", 0),
            "balance": executor.get("balance_after") or 0,
            "status": "active",
            "fees": "0%",
            "updated": datetime.now(timezone.utc).isoformat(),
        })

    revenue["streams"] = streams
    revenue["total_revenue"] = round(
        sum(s.get("amount", 0) for s in streams), 4
    )
    _save(DATA / "revenue_data.json", revenue)

    print(f"  [WIRE] revenue_data.json: ${total_profit:.2f} trading profit -> 7 engines")
    return True


def run():
    """
    Wire all trading outputs into the revenue ecosystem.

    12 orphaned files -> 4 data buses -> 41 consuming engines.
    One bridge engine, 41 new neural connections.
    """
    print("[TRADING_WIRE] Bridging trading data into revenue ecosystem...")

    results = {
        "flywheel": wire_flywheel(),
        "economy_chain": wire_economy_chain(),
        "proof_ledger": wire_proof_ledger(),
        "revenue_data": wire_revenue_data(),
    }

    wired = sum(1 for v in results.values() if v)
    total_consuming = 11 + 11 + 12 + 7  # engines fed by each bus

    print(f"[TRADING_WIRE] {wired}/4 buses wired | "
          f"{total_consuming} engines now receive trading data")

    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "trading-wire-v1",
        "buses_wired": wired,
        "engines_fed": total_consuming,
        "results": results,
        "wiring_map": {
            "flywheel_state.json": 11,
            "economy_chain_ledger.json": 11,
            "proof_ledger.json": 12,
            "revenue_data.json": 7,
        },
    }
    _save(DATA / "trading_wire_state.json", state)

    # Broadcast to synaptic bus -- every engine sees this INSTANTLY
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_batch("TRADING_WIRE", {
            "buses_wired": wired,
            "engines_fed": total_consuming,
            "status": "active" if wired > 0 else "idle",
            "signal_direction": "bullish" if wired >= 3 else "neutral",
        }, silent=False)
    except Exception:
        pass  # Bus not available -- degrade gracefully

    return state


if __name__ == "__main__":
    run()
