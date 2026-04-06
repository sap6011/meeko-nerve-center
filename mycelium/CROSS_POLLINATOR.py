#!/usr/bin/env python3
"""
CROSS_POLLINATOR.py -- Mycelium capital-routing engine
======================================================
In a forest, mycorrhizal fungi connect tree root systems into a
"wood wide web." Trees with surplus sugar feed it into the network;
trees in deficit receive nutrients through the same fungal threads.
No central planner -- just gradient-driven flow toward need.

This engine does the same thing for trading capital:
  - Kalshi (prediction markets)  = one tree
  - Alpaca (stocks / ETFs)       = another tree
  - The mycelium network between them routes idle cash toward
    whichever platform has the best opportunities RIGHT NOW.

Reads from:
  data/turbo_trader_state.json   (Kalshi -- balance, positions, pending_payout, opps)
  data/alpaca_trader_state.json  (Alpaca -- cash, buying_power, portfolio_value, opps)
  data/trade_ledger.json         (all trades from both platforms)
  data/compound_tracker.json     (compound growth tracking)
  data/ai_cost_tracker.json      (AI costs vs trading profits)

Writes to:
  data/cross_pollinator_state.json

Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)

Called by: NERVE_LOOP, OMNIBUS, standalone
"""

import json
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

STATE_FILE = DATA / "cross_pollinator_state.json"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# platform readers
# ---------------------------------------------------------------------------

def _read_kalshi():
    """Read Kalshi state from turbo_trader_state.json."""
    raw = _load(DATA / "turbo_trader_state.json")
    compound = _load(DATA / "compound_tracker.json")

    balance = raw.get("balance", 0) or 0
    pending_payout = 0
    # Derive pending payout from compound tracker snapshots
    snapshots = compound.get("snapshots", [])
    if snapshots:
        latest = snapshots[-1]
        pending_payout = latest.get("pending_payout", 0) or 0

    total_value = balance + pending_payout
    opportunities = raw.get("opportunities", 0) or raw.get("daily_opps", 0) or 0

    return {
        "platform": "kalshi",
        "label": "Kalshi (Prediction Markets)",
        "balance": round(balance, 2),
        "pending_payout": round(pending_payout, 2),
        "total_value": round(total_value, 2),
        "opportunities": opportunities,
        "status": raw.get("status", "unknown"),
        "peak_balance": compound.get("peak_balance", 0),
        "compound_cycles": compound.get("compound_cycles", 0),
    }


def _read_alpaca():
    """Read Alpaca state from alpaca_trader_state.json."""
    raw = _load(DATA / "alpaca_trader_state.json")

    cash = raw.get("cash", 0) or 0
    buying_power = raw.get("buying_power", 0) or 0
    portfolio_value = raw.get("portfolio_value", 0) or 0
    equity = raw.get("equity", 0) or 0
    opportunities = raw.get("opportunities_found", 0) or 0
    market_open = raw.get("market_open", False)

    # Total value is the greater of portfolio_value and equity (they overlap)
    total_value = max(portfolio_value, equity)

    top_opps = raw.get("top_opportunities", [])

    return {
        "platform": "alpaca",
        "label": "Alpaca (Stocks/ETFs)",
        "balance": round(cash, 2),
        "buying_power": round(buying_power, 2),
        "total_value": round(total_value, 2),
        "equity": round(equity, 2),
        "opportunities": opportunities,
        "top_opportunities": top_opps,
        "market_open": market_open,
        "status": raw.get("status", "unknown"),
        "positions_count": raw.get("positions_count", 0),
        "trades_placed": raw.get("trades_placed", 0),
    }


def _read_trade_ledger():
    """Read trade ledger for cross-platform stats."""
    raw = _load(DATA / "trade_ledger.json", {"trades": [], "stats": {}})
    trades = raw.get("trades", [])
    stats = raw.get("stats", {})

    successful = [t for t in trades if t.get("success")]
    failed = [t for t in trades if not t.get("success")]

    total_profit = sum(
        t.get("order_details", {}).get("expected_profit", 0)
        for t in successful
    )
    total_cost = sum(
        t.get("order_details", {}).get("expected_cost", 0)
        for t in successful
    )

    return {
        "total_trades": stats.get("total_trades", len(trades)),
        "successful": stats.get("successful_orders", len(successful)),
        "failed": stats.get("failed_orders", len(failed)),
        "total_profit": round(total_profit, 4),
        "total_cost_basis": round(total_cost, 4),
        "last_trade": stats.get("last_trade", "never"),
    }


def _read_ai_costs():
    """Read AI cost tracker."""
    raw = _load(DATA / "ai_cost_tracker.json")
    return {
        "total_ai_cost": raw.get("total_cost_usd", 0),
        "total_trading_profit": raw.get("total_trading_profit", 0),
        "profit_minus_ai_cost": raw.get("profit_minus_ai_cost", 0),
        "self_sustaining": raw.get("self_sustaining", False),
    }


# ---------------------------------------------------------------------------
# cross-platform calculations
# ---------------------------------------------------------------------------

def _calc_capital_efficiency(kalshi, alpaca, ledger):
    """Profit per dollar deployed on each platform."""
    efficiency = {}

    # Kalshi efficiency: profit / cost basis
    if ledger["total_cost_basis"] > 0:
        efficiency["kalshi"] = round(
            ledger["total_profit"] / ledger["total_cost_basis"] * 100, 2
        )
    else:
        efficiency["kalshi"] = 0.0

    # Alpaca efficiency: based on portfolio performance
    if alpaca["total_value"] > 0 and alpaca["trades_placed"] > 0:
        # Use equity growth as proxy
        efficiency["alpaca"] = round(
            (alpaca["equity"] / max(alpaca["total_value"], 0.01)) * 100, 2
        )
    else:
        efficiency["alpaca"] = 0.0

    return efficiency


def _calc_idle_cash(kalshi, alpaca):
    """Identify which platforms have idle cash that could be deployed."""
    idle = []

    # Kalshi: balance sitting un-traded while opps exist
    if kalshi["balance"] > 0.50 and kalshi["opportunities"] > 0:
        idle.append({
            "platform": "kalshi",
            "idle_amount": kalshi["balance"],
            "note": "Cash available with %d opportunities open" % kalshi["opportunities"],
        })
    elif kalshi["balance"] > 0.50 and kalshi["opportunities"] == 0:
        idle.append({
            "platform": "kalshi",
            "idle_amount": kalshi["balance"],
            "note": "Cash idle -- no current opportunities",
        })

    # Alpaca: cash sitting un-invested
    if alpaca["balance"] > 1.00:
        idle.append({
            "platform": "alpaca",
            "idle_amount": alpaca["balance"],
            "note": "Cash not deployed" + (" (market open)" if alpaca["market_open"] else " (market closed)"),
        })

    return idle


def _generate_transfer_recommendations(kalshi, alpaca, ledger, efficiency):
    """
    Generate transfer recommendations based on opportunity gradients.
    Money flows toward the platform with the best risk-adjusted opps.
    """
    recs = []
    now = datetime.now(timezone.utc).isoformat()

    # --- Kalshi -> Alpaca flow ---
    # If Kalshi has settled profits (pending_payout resolved to balance)
    # and Alpaca has high-scoring opportunities
    kalshi_withdrawable = kalshi["balance"]
    alpaca_has_opps = alpaca["opportunities"] > 0 and alpaca["market_open"]

    if kalshi_withdrawable >= 5.00 and alpaca_has_opps:
        best_opp = ""
        top_opps = alpaca.get("top_opportunities", [])
        if top_opps:
            best = top_opps[0]
            best_opp = " (best: %s score=%s)" % (
                best.get("symbol", "?"), best.get("score", "?")
            )
        recs.append({
            "direction": "kalshi -> alpaca",
            "amount": round(kalshi_withdrawable, 2),
            "reason": "Kalshi has withdrawable cash, Alpaca market open with %d opps%s" % (
                alpaca["opportunities"], best_opp
            ),
            "action": "Withdraw $%.2f from Kalshi -> Deposit to Alpaca" % kalshi_withdrawable,
            "priority": "high" if kalshi_withdrawable >= 10 else "medium",
            "timestamp": now,
        })

    # --- Alpaca -> Kalshi flow ---
    # If Alpaca has realized gains sitting as cash and Kalshi has daily markets
    alpaca_withdrawable = alpaca["balance"]
    kalshi_has_opps = kalshi["opportunities"] > 0

    if alpaca_withdrawable >= 5.00 and kalshi_has_opps:
        recs.append({
            "direction": "alpaca -> kalshi",
            "amount": round(alpaca_withdrawable, 2),
            "reason": "Alpaca has idle cash, Kalshi has %d daily markets open" % kalshi["opportunities"],
            "action": "Withdraw $%.2f from Alpaca -> Deposit to Kalshi" % alpaca_withdrawable,
            "priority": "high" if alpaca_withdrawable >= 10 else "medium",
            "timestamp": now,
        })

    # --- Rebalance signal ---
    # If one platform holds >80% of total capital, suggest rebalance
    total = kalshi["total_value"] + alpaca["total_value"]
    if total > 0:
        kalshi_pct = kalshi["total_value"] / total * 100
        alpaca_pct = alpaca["total_value"] / total * 100

        if kalshi_pct > 80 and alpaca["opportunities"] > 0:
            recs.append({
                "direction": "rebalance -> alpaca",
                "amount": round(total * 0.2, 2),
                "reason": "Kalshi holds %.0f%% of capital -- consider diversifying to Alpaca" % kalshi_pct,
                "action": "Move ~$%.2f to Alpaca for diversification" % (total * 0.2),
                "priority": "low",
                "timestamp": now,
            })
        elif alpaca_pct > 80 and kalshi["opportunities"] > 0:
            recs.append({
                "direction": "rebalance -> kalshi",
                "amount": round(total * 0.2, 2),
                "reason": "Alpaca holds %.0f%% of capital -- consider diversifying to Kalshi" % alpaca_pct,
                "action": "Move ~$%.2f to Kalshi for diversification" % (total * 0.2),
                "priority": "low",
                "timestamp": now,
            })

    # If no recommendations, note the network is balanced
    if not recs:
        recs.append({
            "direction": "none",
            "amount": 0,
            "reason": "Capital distribution is balanced -- no transfers needed",
            "action": "Hold current positions",
            "priority": "info",
            "timestamp": now,
        })

    return recs


def _calc_mycelium_health(kalshi, alpaca, ledger, ai_costs, efficiency):
    """
    Mycelium Health Score (0-100).

    Components:
      - Capital utilization  (0-25): How much capital is actively deployed
      - Diversification      (0-20): Spread across platforms
      - Profit rate          (0-25): Realized gains vs cost basis
      - Settlement speed     (0-15): Compound cycles / successful trade ratio
      - AI cost ratio        (0-15): Trading profits vs AI costs
    """
    score = 0
    breakdown = {}

    # --- Capital utilization (0-25) ---
    total_value = kalshi["total_value"] + alpaca["total_value"]
    idle_cash = kalshi["balance"] + alpaca["balance"]
    if total_value > 0:
        deployed_pct = max(0, (total_value - idle_cash) / total_value * 100)
        util_score = min(25, deployed_pct / 4)  # 100% deployed = 25 pts
    else:
        util_score = 0
    breakdown["capital_utilization"] = round(util_score, 1)
    score += util_score

    # --- Diversification (0-20) ---
    if total_value > 0:
        kalshi_share = kalshi["total_value"] / total_value
        alpaca_share = alpaca["total_value"] / total_value
        # Perfect diversification = 50/50 -> score 20
        # All on one side -> score ~10
        # Nothing -> score 0
        balance_ratio = 1 - abs(kalshi_share - alpaca_share)
        div_score = balance_ratio * 20
    else:
        div_score = 0
    # Bonus: if both platforms are active, +5
    if kalshi["status"] not in ("unknown", "disabled", "") and \
       alpaca["status"] not in ("unknown", "disabled", ""):
        div_score = min(20, div_score + 5)
    breakdown["diversification"] = round(div_score, 1)
    score += div_score

    # --- Profit rate (0-25) ---
    if ledger["total_cost_basis"] > 0:
        profit_pct = ledger["total_profit"] / ledger["total_cost_basis"] * 100
        profit_score = min(25, profit_pct * 2.5)  # 10% profit = 25 pts
    elif ledger["total_profit"] > 0:
        profit_score = 15  # Profit with no tracked cost = decent
    else:
        profit_score = 0
    breakdown["profit_rate"] = round(profit_score, 1)
    score += profit_score

    # --- Settlement speed (0-15) ---
    compound_cycles = kalshi.get("compound_cycles", 0)
    total_trades = ledger["total_trades"]
    if total_trades > 0:
        success_ratio = ledger["successful"] / total_trades
        settle_score = min(15, (success_ratio * 10) + min(5, compound_cycles))
    else:
        settle_score = 0
    breakdown["settlement_speed"] = round(settle_score, 1)
    score += settle_score

    # --- AI cost ratio (0-15) ---
    trading_profit = ai_costs.get("total_trading_profit", 0)
    ai_cost = ai_costs.get("total_ai_cost", 0)
    if ai_cost == 0 and trading_profit > 0:
        cost_score = 15  # Zero AI cost + positive profit = perfect
    elif ai_cost > 0 and trading_profit > 0:
        ratio = trading_profit / ai_cost
        cost_score = min(15, ratio * 3)  # 5x profit/cost = 15 pts
    else:
        cost_score = 5  # Neutral -- no data yet
    if ai_costs.get("self_sustaining"):
        cost_score = min(15, cost_score + 3)
    breakdown["ai_cost_ratio"] = round(cost_score, 1)
    score += cost_score

    return {
        "score": round(min(100, max(0, score)), 1),
        "grade": _grade(score),
        "breakdown": breakdown,
    }


def _grade(score):
    """Letter grade for health score."""
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def run():
    """
    Cross-pollinate capital intelligence across all trading platforms.

    Reads Kalshi + Alpaca state, calculates cross-platform metrics,
    generates transfer recommendations, scores mycelium health,
    and writes everything to data/cross_pollinator_state.json.

    Returns the full state dict.
    """
    now = datetime.now(timezone.utc).isoformat()

    print("[CROSS_POLLINATOR] Mycelium network scan starting...")
    print("  Reading platform root systems...")

    # --- 1. Read all platforms ---
    kalshi = _read_kalshi()
    alpaca = _read_alpaca()
    ledger = _read_trade_ledger()
    ai_costs = _read_ai_costs()

    # --- 2. Cross-platform metrics ---
    total_portfolio = round(kalshi["total_value"] + alpaca["total_value"], 2)
    efficiency = _calc_capital_efficiency(kalshi, alpaca, ledger)
    idle = _calc_idle_cash(kalshi, alpaca)

    # --- 3. Transfer recommendations ---
    recommendations = _generate_transfer_recommendations(
        kalshi, alpaca, ledger, efficiency
    )

    # --- 4. Mycelium health score ---
    health = _calc_mycelium_health(kalshi, alpaca, ledger, ai_costs, efficiency)

    # --- 5. Best opportunity platform ---
    best_platform = "kalshi" if kalshi["opportunities"] > alpaca["opportunities"] else "alpaca"
    if kalshi["opportunities"] == alpaca["opportunities"]:
        # Tie-break: whichever has better efficiency
        best_platform = "kalshi" if efficiency.get("kalshi", 0) >= efficiency.get("alpaca", 0) else "alpaca"

    # --- Print summary ---
    print("")
    print("  ============================================")
    print("  CROSS-PLATFORM PORTFOLIO")
    print("  ============================================")
    print("  Total portfolio value:  $%.2f" % total_portfolio)
    print("  ------------------------------------------")
    print("  Kalshi:")
    print("    Balance:        $%.2f" % kalshi["balance"])
    print("    Pending payout: $%.2f" % kalshi["pending_payout"])
    print("    Total value:    $%.2f" % kalshi["total_value"])
    print("    Opportunities:  %d" % kalshi["opportunities"])
    print("    Status:         %s" % kalshi["status"])
    print("  ------------------------------------------")
    print("  Alpaca:")
    print("    Cash:           $%.2f" % alpaca["balance"])
    print("    Portfolio:      $%.2f" % alpaca["total_value"])
    print("    Opportunities:  %d" % alpaca["opportunities"])
    print("    Market open:    %s" % alpaca["market_open"])
    print("    Status:         %s" % alpaca["status"])
    print("  ------------------------------------------")
    print("  Trade ledger:  %d total | %d won | %d failed" % (
        ledger["total_trades"], ledger["successful"], ledger["failed"]
    ))
    print("  Realized profit: $%.4f" % ledger["total_profit"])
    print("  AI costs:        $%.4f (self-sustaining: %s)" % (
        ai_costs["total_ai_cost"],
        "YES" if ai_costs["self_sustaining"] else "NO",
    ))
    print("  Net profit:      $%.4f" % ai_costs["profit_minus_ai_cost"])
    print("")
    print("  Capital efficiency:")
    print("    Kalshi: %.2f%%" % efficiency.get("kalshi", 0))
    print("    Alpaca: %.2f%%" % efficiency.get("alpaca", 0))
    print("  Best opportunity platform: %s" % best_platform)
    print("")

    # Idle cash
    if idle:
        print("  [!] Idle cash detected:")
        for i in idle:
            print("      %s: $%.2f -- %s" % (
                i["platform"].upper(), i["idle_amount"], i["note"]
            ))
        print("")

    # Transfer recommendations
    print("  TRANSFER RECOMMENDATIONS:")
    for rec in recommendations:
        if rec["direction"] == "none":
            print("    [OK] %s" % rec["reason"])
        else:
            arrow = rec["direction"].replace("->", ">>")
            priority_tag = "[%s]" % rec["priority"].upper()
            print("    %s %s" % (priority_tag, rec["action"]))
            print("         Reason: %s" % rec["reason"])
    print("")

    # Mycelium health
    bd = health["breakdown"]
    print("  MYCELIUM HEALTH SCORE: %s / 100  (Grade: %s)" % (
        health["score"], health["grade"]
    ))
    print("    Capital utilization: %.1f / 25" % bd["capital_utilization"])
    print("    Diversification:    %.1f / 20" % bd["diversification"])
    print("    Profit rate:        %.1f / 25" % bd["profit_rate"])
    print("    Settlement speed:   %.1f / 15" % bd["settlement_speed"])
    print("    AI cost ratio:      %.1f / 15" % bd["ai_cost_ratio"])
    print("  ============================================")
    print("")

    # --- 6. Build and save state ---
    state = {
        "timestamp": now,
        "protocol": "cross-pollinator-v1",
        "engine": "CROSS_POLLINATOR",
        "total_portfolio_value": total_portfolio,
        "platform_breakdown": {
            "kalshi": kalshi,
            "alpaca": alpaca,
        },
        "trade_ledger_summary": ledger,
        "ai_cost_summary": ai_costs,
        "capital_efficiency": efficiency,
        "idle_cash": idle,
        "best_opportunity_platform": best_platform,
        "transfer_recommendations": recommendations,
        "mycelium_health_score": health["score"],
        "mycelium_health_grade": health["grade"],
        "mycelium_health_breakdown": health["breakdown"],
        "status": "active",
    }

    _save(STATE_FILE, state)

    # Broadcast to synaptic bus -- every engine sees this INSTANTLY
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_batch("CROSS_POLLINATOR", {
            "total_portfolio_value": total_portfolio,
            "mycelium_health_score": health["score"],
            "mycelium_health_grade": health["grade"],
            "best_opportunity_platform": best_platform,
            "transfer_count": len(recommendations),
            "idle_cash_platforms": len(idle),
            "kalshi_balance": kalshi["balance"],
            "alpaca_cash": alpaca["balance"],
            "signal_direction": "opportunity" if recommendations else "neutral",
            "status": "active",
        }, silent=False)
    except Exception:
        pass  # Bus not available -- degrade gracefully

    print("[CROSS_POLLINATOR] State written: data/cross_pollinator_state.json")
    print("[CROSS_POLLINATOR] Mycelium network scan complete.")

    return state


if __name__ == "__main__":
    run()
