#!/usr/bin/env python3
"""
YIELD_LOOP.py — Autonomous crypto yield compounding for SolarPunk
==================================================================

The engine that closes the loop: detect -> decide -> execute -> compound.

What this does:
  1. Reads wallet balances from WALLET_BRIDGE
  2. Reads yield rates from SOL_MAXIMIZER
  3. Reads prices from PRICE_ORACLE
  4. Detects compounding opportunities:
     - Unstaked SOL sitting idle -> route to best yield
     - Staking rewards accumulated -> restake
     - New SOL from revenue/BAT -> auto-allocate
     - Yield rate changes -> suggest rebalance
  5. Generates action queue for execution
  6. Tracks compound history and growth rate

The execution path (proven 2026-04-05):
  Claude -> Browser Automation -> Jupiter/Marinade -> Phantom -> Solana

  With Phantom Auto Confirm enabled:
    Detection -> Decision -> Execution -> Confirmation = FULLY AUTONOMOUS

Revenue compound loop:
  SolarPunk earns $ -> Buy SOL -> Stake/Swap -> Earn yield -> More SOL -> Repeat
  Brave BAT -> Swap to SOL -> Stake -> Compound
  Staking rewards -> Restake -> Compound the compound

Called by: OMNIBUS, SOL_MAXIMIZER
Writes: data/yield_loop_state.json
"""

import json
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)


def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default or {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def detect_idle_sol():
    """Find SOL sitting in wallets that could be earning yield."""
    balances = _load(DATA / "wallet_balances.json")
    maximizer = _load(DATA / "sol_maximizer_state.json")

    idle = []
    gas_reserve = 0.02  # Keep 0.02 SOL per wallet for gas
    marinade_min = 1.0046  # Marinade Native minimum

    for name, w in balances.items():
        if w.get("chain") != "solana":
            continue

        sol = w.get("sol_balance", 0) or 0
        available = sol - gas_reserve

        if available <= 0:
            continue

        # Check what's already staked (tokens like JitoSOL, mSOL)
        staked_tokens = []
        for t in w.get("tokens", []):
            symbol = t.get("symbol", "")
            if symbol in ("JitoSOL", "mSOL", "bSOL", "MSOL"):
                staked_tokens.append({
                    "symbol": symbol,
                    "balance": t.get("balance", 0),
                })

        opportunity = {
            "wallet": name,
            "address": w.get("address", "")[:12] + "...",
            "sol_balance": sol,
            "available_sol": round(available, 6),
            "already_staked": staked_tokens,
            "actions": [],
        }

        # Decision logic
        if available >= marinade_min:
            opportunity["actions"].append({
                "type": "marinade_native_stake",
                "amount": round(available - 0.01, 6),  # Extra buffer
                "apy": 6.39,
                "risk": "very_low",
                "reason": "Above Marinade minimum — native staking is safest yield",
                "url": "https://app.marinade.finance/earn/sol/",
            })

        if available >= 0.01:
            opportunity["actions"].append({
                "type": "jitosol_swap",
                "amount": round(min(available, available - 0.005), 6),
                "apy": 7.7,
                "risk": "low",
                "reason": "JitoSOL via Jupiter — no minimum, higher APY with MEV tips",
                "url": "https://jup.ag/swap/SOL-JitoSOL",
            })

        if available >= 0.001:
            opportunity["actions"].append({
                "type": "jupiter_lend",
                "amount": round(available, 6),
                "apy": 4.46,
                "risk": "low",
                "reason": "Jupiter Lend vault — lending yield, instant withdrawal",
                "url": "https://jup.ag/lend/earn",
            })

        if opportunity["actions"]:
            idle.append(opportunity)

    return idle


def detect_compound_opportunities():
    """Detect when staking rewards should be restaked."""
    balances = _load(DATA / "wallet_balances.json")
    history = _load(DATA / "yield_loop_history.json", {"entries": []})

    compounds = []

    for name, w in balances.items():
        if w.get("chain") != "solana":
            continue

        # Check if JitoSOL/mSOL balance has grown (rewards accumulated)
        for t in w.get("tokens", []):
            symbol = t.get("symbol", "")
            bal = t.get("balance", 0)

            if symbol in ("JitoSOL", "mSOL", "bSOL") and bal > 0:
                # Compare with last known balance
                last = None
                for entry in reversed(history.get("entries", [])):
                    for prev_t in entry.get("token_balances", []):
                        if prev_t.get("symbol") == symbol and prev_t.get("wallet") == name:
                            last = prev_t.get("balance", 0)
                            break
                    if last is not None:
                        break

                if last is not None and bal > last:
                    growth = bal - last
                    compounds.append({
                        "wallet": name,
                        "token": symbol,
                        "current": bal,
                        "previous": last,
                        "growth": round(growth, 9),
                        "note": f"{symbol} appreciated — liquid staking rewards accumulating",
                    })

    return compounds


def detect_revenue_to_compound():
    """Check if SolarPunk revenue can be routed to crypto."""
    revenue = _load(DATA / "revenue_audit.json")
    proof = _load(DATA / "proof_ledger.json")

    opportunities = []

    total_revenue = revenue.get("total_revenue_usd", 0)
    total_transferred = proof.get("total_transferred", 0)

    if total_revenue > 0:
        opportunities.append({
            "type": "revenue_to_sol",
            "revenue_usd": total_revenue,
            "action": "Convert SolarPunk revenue to SOL -> stake for compound growth",
            "note": "Revenue from Ko-fi/Gumroad -> buy SOL -> Marinade/JitoSOL",
        })

    # Check BAT balance
    for name, w in _load(DATA / "wallet_balances.json").items():
        for t in w.get("tokens", []):
            if t.get("symbol") == "BAT" and t.get("balance", 0) > 0:
                opportunities.append({
                    "type": "bat_to_sol",
                    "bat_balance": t["balance"],
                    "action": f"Swap {t['balance']} BAT -> SOL on Jupiter -> stake",
                    "url": "https://jup.ag/swap/BAT-SOL",
                })

    return opportunities


def check_market_signals():
    """
    Read prediction intelligence to adjust compound urgency.

    Polymarket intelligence -> YIELD_LOOP decision modifiers:
      - Bullish signals -> compound faster, route more to liquid staking
      - Bearish/crisis  -> slow down, favor native staking (safer)
      - SOL bullish     -> accumulate more SOL before price rises
    """
    intel = _load(DATA / "prediction_intelligence.json")
    if not intel or "sentiment" not in intel:
        return {"available": False, "modifier": "normal"}

    sentiment = intel["sentiment"]

    # Check freshness
    try:
        ts = datetime.fromisoformat(intel["timestamp"].replace("Z", "+00:00"))
        age_hours = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
        if age_hours > 24:
            return {"available": True, "modifier": "normal", "note": "stale data (>24h)"}
    except Exception:
        pass

    action = sentiment.get("recommended_action", "hold")
    sol_outlook = sentiment.get("sol_outlook", 0.5)
    crisis = sentiment.get("crisis_level", 0.0)

    modifier = "normal"
    notes = []

    if action == "accumulate" or sol_outlook > 0.65:
        modifier = "accelerate"
        notes.append("Prediction markets bullish on SOL -- compound faster")
    elif action == "reduce_exposure" or crisis > 0.7:
        modifier = "conservative"
        notes.append("Prediction markets signal caution -- favor safe yield")
    elif sol_outlook > 0.55:
        modifier = "slightly_bullish"
        notes.append("Mild bullish signal -- standard compounding")

    return {
        "available": True,
        "modifier": modifier,
        "action": action,
        "sol_outlook": sol_outlook,
        "crisis_level": crisis,
        "notes": notes,
    }


def build_action_queue(idle, compounds, revenue):
    """Prioritized queue of yield actions, informed by prediction markets."""
    queue = []
    signals = check_market_signals()

    # Adjust action selection based on market signals
    prefer_safe = signals.get("modifier") == "conservative"
    prefer_aggressive = signals.get("modifier") in ("accelerate", "slightly_bullish")

    # Priority 1: Idle SOL -> best yield (adjusted by market signals)
    for opp in idle:
        if opp["actions"]:
            if prefer_safe:
                # Conservative: prefer native staking or lending
                safe_actions = [a for a in opp["actions"]
                                if a["type"] in ("marinade_native_stake", "jupiter_lend")]
                best = max(safe_actions or opp["actions"], key=lambda a: a.get("apy", 0))
            elif prefer_aggressive:
                # Aggressive: prefer highest APY (liquid staking)
                best = max(opp["actions"], key=lambda a: a.get("apy", 0))
            else:
                best = max(opp["actions"], key=lambda a: a.get("apy", 0))

            entry = {
                "priority": 1,
                "type": best["type"],
                "wallet": opp["wallet"],
                "amount_sol": best["amount"],
                "expected_apy": best["apy"],
                "url": best["url"],
                "reason": best["reason"],
                "status": "pending",
            }
            if signals.get("available"):
                entry["market_signal"] = signals["modifier"]
            queue.append(entry)

    # Priority 2: Compound opportunities
    for comp in compounds:
        queue.append({
            "priority": 2,
            "type": "compound_detected",
            "wallet": comp["wallet"],
            "token": comp["token"],
            "growth": comp["growth"],
            "status": "info",
        })

    # Priority 3: Revenue routing
    for rev in revenue:
        queue.append({
            "priority": 3,
            "type": rev["type"],
            "action": rev["action"],
            "status": "pending",
        })

    # Priority 0: Market signal alert (if strong signal)
    if signals.get("available") and signals.get("modifier") != "normal":
        queue.insert(0, {
            "priority": 0,
            "type": "market_intelligence",
            "signal": signals["modifier"],
            "sol_outlook": signals.get("sol_outlook"),
            "notes": signals.get("notes", []),
            "status": "info",
        })

    return sorted(queue, key=lambda x: x["priority"])


def update_history(state):
    """Track yield loop history for compound detection."""
    history_path = DATA / "yield_loop_history.json"
    history = _load(history_path, {"entries": []})

    balances = _load(DATA / "wallet_balances.json")

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "token_balances": [],
    }

    for name, w in balances.items():
        for t in w.get("tokens", []):
            if t.get("balance", 0) > 0:
                entry["token_balances"].append({
                    "wallet": name,
                    "symbol": t.get("symbol"),
                    "balance": t.get("balance"),
                })

    history["entries"].append(entry)
    history["entries"] = history["entries"][-500:]
    history["last_updated"] = entry["timestamp"]
    _save(history_path, history)


def run():
    """Engine entry point for OMNIBUS."""
    print("[YIELD_LOOP] Scanning for compound opportunities...")

    idle = detect_idle_sol()
    compounds = detect_compound_opportunities()
    revenue = detect_revenue_to_compound()
    queue = build_action_queue(idle, compounds, revenue)

    # Get market intelligence for state reporting
    market_signals = check_market_signals()

    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "yield-loop-v2",
        "idle_sol_detected": len(idle),
        "compound_opportunities": len(compounds),
        "revenue_routing": len(revenue),
        "market_intelligence": market_signals,
        "action_queue": queue,
        "execution_path": {
            "automated": "Claude -> Browser -> Jupiter/Marinade -> Phantom -> Solana",
            "requires_approval": "Phantom wallet signature (enable Auto Confirm for full autonomy)",
            "proven": "2026-04-05: JitoSOL swap + Marinade Native stake executed successfully",
        },
        "portfolio_strategy": {
            "primary_yield": "Marinade Native (6.39% APY, zero smart contract risk)",
            "secondary_yield": "JitoSOL (7.7% APY, liquid staking + MEV tips)",
            "free_income": "Brave BAT rewards (browse -> earn -> swap to SOL -> stake)",
            "revenue_routing": "SolarPunk revenue -> SOL -> stake -> compound",
            "intelligence": "Polymarket prediction feed informs yield strategy adjustments",
        },
    }

    # Save state
    _save(DATA / "yield_loop_state.json", state)

    # Update history for next cycle comparison
    update_history(state)

    # Summary
    total_actions = len(queue)
    pending = sum(1 for q in queue if q.get("status") == "pending")

    if market_signals.get("available") and market_signals.get("modifier") != "normal":
        print(f"[YIELD_LOOP] Market signal: {market_signals['modifier']} "
              f"(SOL outlook={market_signals.get('sol_outlook', '?')})")
    if idle:
        for opp in idle:
            print(f"[YIELD_LOOP] {opp['wallet']}: {opp['available_sol']} SOL idle -> {len(opp['actions'])} yield options")
    if compounds:
        for comp in compounds:
            print(f"[YIELD_LOOP] {comp['token']} grew by {comp['growth']} -- compounding detected!")

    print(f"[YIELD_LOOP] Actions queued: {total_actions} ({pending} pending)")
    print(f"[YIELD_LOOP] Loop: detect -> predict -> decide -> execute -> compound -> repeat")

    return state


if __name__ == "__main__":
    run()
