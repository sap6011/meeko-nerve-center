#!/usr/bin/env python3
"""
NERVE_LOOP.py -- The living loop. Everything feeds everything else, forever.
=============================================================================
v2 (2026-04-05): Added Phase 7 EVOLVE + Kalshi profit tracking in growth.
v1 (2026-04-05): Not snapshots. Not individuals. One unified organism.

This is the master pipeline that wires ALL crypto engines into a single
self-feeding, self-replicating, continuously-running loop.

THE LOOP (every cycle):
  Phase 1: SENSE     -- Gather intelligence from prediction markets
  Phase 2: OBSERVE   -- Read all wallet states + prices
  Phase 3: THINK     -- Compute strategy from intelligence + portfolio
  Phase 4: PLAN      -- Build unified action queue across ALL wallets
  Phase 4b: EXECUTE  -- Kalshi trading (autonomous, if enabled)
  Phase 4c: TURBO    -- High-frequency compounding on daily markets (9000+ series)
  Phase 5: REPLICATE -- Apply proven strategies to every eligible wallet
  Phase 6: RECORD    -- Log results, track growth (crypto + Kalshi)
  Phase 7: EVOLVE    -- LIVE_WIRE + CHIMERA + PUBLIC_LEDGER. Profits → evolution.

Each engine's OUTPUT is the next engine's INPUT. Nothing runs alone.

REPLICATION RULE:
  If a strategy works on Wallet A, it works on Wallet B.
  If it works on 2 wallets, it works on N wallets.
  Every new wallet inherits all proven strategies automatically.

RATE LIMIT COMPLIANCE:
  - Jupiter API: 1 req/sec max, 30 sec cooldown between full scans
  - Polymarket Gamma: 10 req/sec, 60 sec between full scans
  - Kalshi API: public tier, 60 sec between full scans
  - Solana RPC: public endpoint, 5 req/sec, 30 sec between wallet scans
  - Inter-cycle cooldown: 5 minutes minimum between full loops

Called by: Scheduled task (every 15 min) or OMNIBUS
Writes: data/nerve_loop_state.json, data/execution_log.json, data/growth_tracker.json
"""

import json
import time
import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# Minimum seconds between full loop cycles (rate limit protection)
MIN_CYCLE_INTERVAL = 300  # 5 minutes


def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default or {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _import_engine(name):
    """Dynamically import an engine module from mycelium/."""
    # Ensure mycelium/ is on sys.path (handles running from repo root or mycelium/)
    mycelium_dir = str(Path(__file__).parent)
    if mycelium_dir not in sys.path:
        sys.path.insert(0, mycelium_dir)

    try:
        if name in sys.modules:
            return importlib.reload(sys.modules[name])
        return importlib.import_module(name)
    except Exception as e:
        print(f"  [NERVE] Failed to load {name}: {e}")
        return None


def _run_engine(name, phase_label):
    """Run an engine's run() function with error handling."""
    start = time.time()
    try:
        mod = _import_engine(name)
        if mod and hasattr(mod, "run"):
            result = mod.run()
            elapsed = round(time.time() - start, 1)
            print(f"  [{phase_label}] {name}: OK ({elapsed}s)")
            return {"status": "ok", "engine": name, "elapsed": elapsed, "result": result}
        else:
            print(f"  [{phase_label}] {name}: no run() found")
            return {"status": "no_run", "engine": name}
    except Exception as e:
        elapsed = round(time.time() - start, 1)
        print(f"  [{phase_label}] {name}: ERROR ({e})")
        return {"status": "error", "engine": name, "error": str(e), "elapsed": elapsed}


def check_cooldown():
    """Ensure we don't run too frequently (rate limit protection)."""
    state = _load(DATA / "nerve_loop_state.json")
    last_run = state.get("last_cycle_end")
    if last_run:
        try:
            last = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
            elapsed = (datetime.now(timezone.utc) - last).total_seconds()
            if elapsed < MIN_CYCLE_INTERVAL:
                wait = int(MIN_CYCLE_INTERVAL - elapsed)
                print(f"[NERVE] Cooldown: {wait}s remaining (rate limit protection)")
                return False, wait
        except Exception:
            pass
    return True, 0


def phase_1_sense():
    """
    PHASE 1: SENSE -- Gather intelligence from prediction markets.

    Polymarket (200 markets) + Kalshi (200 markets) = 400 markets analyzed.
    Output: data/prediction_intelligence.json (merged, cross-validated)
    """
    print("\n=== PHASE 1: SENSE (Intelligence Gather) ===")
    results = []

    # Polymarket first (writes prediction_intelligence.json)
    results.append(_run_engine("POLYMARKET_SCANNER", "SENSE"))
    time.sleep(2)  # Rate limit courtesy

    # Kalshi merges into same file (cross-validates)
    results.append(_run_engine("KALSHI_SCANNER", "SENSE"))

    intel = _load(DATA / "prediction_intelligence.json")
    sentiment = intel.get("sentiment", {})
    print(f"  [SENSE] Intelligence: {intel.get('sources', ['none'])} | "
          f"Action: {sentiment.get('recommended_action', 'N/A')} | "
          f"SOL: {sentiment.get('sol_outlook', '?')} | "
          f"Crypto: {sentiment.get('crypto_bullish', '?')}")

    return {"phase": "sense", "results": results, "sentiment": sentiment}


def phase_2_observe():
    """
    PHASE 2: OBSERVE -- Read all wallet states + prices.

    Scans EVERY wallet (desktop + phone + any future wallets).
    Output: data/wallet_balances.json, data/price_oracle_state.json
    """
    print("\n=== PHASE 2: OBSERVE (Portfolio State) ===")
    results = []

    results.append(_run_engine("WALLET_BRIDGE", "OBSERVE"))
    time.sleep(1)
    results.append(_run_engine("PRICE_ORACLE", "OBSERVE"))

    balances = _load(DATA / "wallet_balances.json")
    prices = _load(DATA / "price_oracle_state.json")

    # Summarize across ALL wallets
    total_sol = 0
    wallet_count = 0
    for name, w in balances.items():
        if w.get("chain") == "solana":
            sol = w.get("sol_balance", 0) or 0
            total_sol += sol
            wallet_count += 1

    sol_price = prices.get("prices_avg", {}).get("SOL", 0)
    total_usd = total_sol * sol_price if sol_price else 0

    print(f"  [OBSERVE] {wallet_count} Solana wallets | "
          f"Total: {total_sol:.6f} SOL (${total_usd:.2f}) | "
          f"SOL price: ${sol_price:.2f}")

    return {
        "phase": "observe",
        "results": results,
        "total_sol": total_sol,
        "total_usd": round(total_usd, 2),
        "wallet_count": wallet_count,
        "sol_price": sol_price,
    }


def phase_3_think():
    """
    PHASE 3: THINK -- Compute strategy from intelligence + portfolio.

    SOL_MAXIMIZER reads prediction_intelligence.json and adjusts strategy.
    Output: data/sol_maximizer_state.json (intelligence-adjusted)
    """
    print("\n=== PHASE 3: THINK (Strategy Compute) ===")
    results = []

    results.append(_run_engine("SOL_MAXIMIZER", "THINK"))

    state = _load(DATA / "sol_maximizer_state.json")
    strategy = state.get("strategy", {})
    predictions = strategy.get("prediction_intelligence", {})

    action = predictions.get("action", "none")
    print(f"  [THINK] Strategy mode: {action} | "
          f"Options: {len(state.get('yield_options', []))}")

    return {"phase": "think", "results": results, "strategy_mode": action}


def phase_4_plan():
    """
    PHASE 4: PLAN -- Build unified action queue across ALL wallets.

    YIELD_LOOP + ARBITRAGE_SCANNER + AIRDROP_HUNTER all produce actions.
    Merge into one prioritized queue.
    """
    print("\n=== PHASE 4: PLAN (Action Queue) ===")
    results = []

    results.append(_run_engine("YIELD_LOOP", "PLAN"))
    time.sleep(1)
    results.append(_run_engine("ARBITRAGE_SCANNER", "PLAN"))
    time.sleep(1)
    results.append(_run_engine("AIRDROP_HUNTER", "PLAN"))

    # Merge all action queues into unified queue
    yield_state = _load(DATA / "yield_loop_state.json")
    arb_state = _load(DATA / "arbitrage_scanner_state.json")
    airdrop_state = _load(DATA / "airdrop_hunter_state.json")

    unified_queue = []

    # Yield actions
    for action in yield_state.get("action_queue", []):
        action["source"] = "yield_loop"
        unified_queue.append(action)

    # Arb actions
    for action in arb_state.get("actionable_opportunities", []):
        action["source"] = "arbitrage"
        action["priority"] = 0 if action.get("urgency") == "high" else 1
        unified_queue.append(action)

    # Airdrop targets
    for target in airdrop_state.get("high_priority_targets", []):
        unified_queue.append({
            "source": "airdrop",
            "priority": 4,
            "type": "protocol_interaction",
            "target": target,
            "status": "pending",
        })

    unified_queue.sort(key=lambda x: x.get("priority", 99))
    _save(DATA / "unified_action_queue.json", {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_actions": len(unified_queue),
        "queue": unified_queue,
    })

    pending = sum(1 for a in unified_queue if a.get("status") == "pending")
    print(f"  [PLAN] Unified queue: {len(unified_queue)} actions ({pending} pending)")

    return {"phase": "plan", "results": results, "queue_size": len(unified_queue), "pending": pending}


def phase_4b_execute():
    """
    PHASE 4b: EXECUTE -- Run TRADE_EXECUTOR on Kalshi.

    Reads intelligence + opportunities, places orders if enabled.
    Disabled by default -- user must set enabled: true in config.
    """
    print("\n=== PHASE 4b: EXECUTE (Kalshi Trading) ===")
    result = _run_engine("TRADE_EXECUTOR", "EXECUTE")

    executor_state = _load(DATA / "trade_executor_state.json")
    status = executor_state.get("status", "unknown")
    trades = executor_state.get("trades_this_cycle", 0)
    balance = executor_state.get("balance_after") or executor_state.get("balance_before", "?")
    opps = executor_state.get("opportunities_found", 0)

    print(f"  [EXECUTE] Status: {status} | Trades: {trades} | "
          f"Opportunities: {opps} | Balance: ${balance}")

    return {
        "phase": "execute",
        "result": result,
        "status": status,
        "trades": trades,
        "balance": balance,
    }


def phase_4c_turbo():
    """
    PHASE 4c: TURBO -- High-frequency compounding on fast-resolving markets.

    Scans 9,000+ Kalshi series, targets DAILY resolution markets (S&P 500
    ranges, weather, gas prices), detects balance changes (new deposits),
    and compounds profits from resolved positions.
    """
    print("\n=== PHASE 4c: TURBO (High-Frequency Compounding) ===")
    result = _run_engine("TURBO_TRADER", "TURBO")

    turbo_state = _load(DATA / "turbo_trader_state.json")
    status = turbo_state.get("status", "unknown")
    balance = turbo_state.get("balance", "?")
    daily = turbo_state.get("daily_opps", 0)
    weekly = turbo_state.get("weekly_opps", 0)
    trades = turbo_state.get("trades_placed", 0)
    deposit = turbo_state.get("deposit_detected", False)
    settlements = turbo_state.get("settlements_24h", 0)

    print(f"  [TURBO] Status: {status} | Daily opps: {daily} | "
          f"Weekly opps: {weekly} | Trades: {trades}")
    if deposit:
        print(f"  [TURBO] NEW DEPOSIT DETECTED! Deploying immediately...")
    if settlements > 0:
        print(f"  [TURBO] {settlements} positions settled in last 24h")

    return {
        "phase": "turbo",
        "result": result,
        "status": status,
        "balance": balance,
        "daily_opportunities": daily,
        "weekly_opportunities": weekly,
        "trades_placed": trades,
        "deposit_detected": deposit,
        "settlements_24h": settlements,
    }


def phase_4d_alpaca():
    """
    PHASE 4d: ALPACA -- Commission-free stock/ETF/crypto trading.

    Second platform in the multi-market machine. Trades stocks, ETFs,
    and crypto via Alpaca's API. Fractional shares mean $1 buys you a
    piece of any stock. Commission-free = even tiny gains compound.
    """
    print("\n=== PHASE 4d: ALPACA (Stocks/ETFs/Crypto) ===")
    result = _run_engine("ALPACA_TRADER", "ALPACA")

    alpaca_state = _load(DATA / "alpaca_trader_state.json")
    status = alpaca_state.get("status", "unknown")
    mode = alpaca_state.get("mode", "?")
    portfolio = alpaca_state.get("portfolio_value", 0)
    positions = alpaca_state.get("positions_count", 0)
    trades = alpaca_state.get("trades_placed", 0)
    opportunities = alpaca_state.get("opportunities_found", 0)
    market_open = alpaca_state.get("market_open", False)

    print(f"  [ALPACA] {mode} | Status: {status} | "
          f"Market: {'OPEN' if market_open else 'CLOSED'}")
    print(f"  [ALPACA] Portfolio: ${portfolio:.2f} | "
          f"Positions: {positions} | Opps: {opportunities} | Trades: {trades}")

    return {
        "phase": "alpaca",
        "result": result,
        "status": status,
        "mode": mode,
        "portfolio_value": portfolio,
        "positions_count": positions,
        "market_open": market_open,
        "trades_placed": trades,
        "opportunities_found": opportunities,
    }


def phase_5_replicate():
    """
    PHASE 5: REPLICATE -- Apply proven strategies to every eligible wallet.

    The rule: if it works on one wallet, apply it to ALL wallets.
    Desktop strategies -> Phone. Phone strategies -> Desktop. N wallets -> N strategies.
    """
    print("\n=== PHASE 5: REPLICATE (Multi-Wallet) ===")

    config = _load(DATA / "wallet_config.json")
    wallets = config.get("wallets", {})
    balances = _load(DATA / "wallet_balances.json")
    yield_state = _load(DATA / "yield_loop_state.json")

    solana_wallets = []
    for name, w in wallets.items():
        if w.get("chain") == "solana":
            bal = 0
            for bname, bdata in balances.items():
                if bdata.get("address") == w.get("address"):
                    bal = bdata.get("sol_balance", 0) or 0
                    break
            solana_wallets.append({
                "name": name,
                "address": w.get("address", ""),
                "role": w.get("role", "unknown"),
                "balance": bal,
            })

    # Proven strategies (executed successfully at least once)
    proven = [
        {"strategy": "jitosol_swap", "min_sol": 0.01, "apy": 7.7,
         "proven_date": "2026-04-05", "url": "https://jup.ag/swap/SOL-JitoSOL"},
        {"strategy": "marinade_native", "min_sol": 1.0046, "apy": 6.39,
         "proven_date": "2026-04-05", "url": "https://app.marinade.finance/earn/sol/"},
    ]

    replications = []
    for wallet in solana_wallets:
        available = wallet["balance"] - 0.02  # gas reserve
        if available <= 0:
            continue

        for strat in proven:
            if available >= strat["min_sol"]:
                replications.append({
                    "wallet": wallet["name"],
                    "wallet_role": wallet["role"],
                    "address": wallet["address"][:12] + "...",
                    "strategy": strat["strategy"],
                    "amount_sol": round(min(available, available * 0.8), 6),
                    "expected_apy": strat["apy"],
                    "url": strat["url"],
                    "status": "queued_for_replication",
                })

    _save(DATA / "replication_queue.json", {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "solana_wallets": len(solana_wallets),
        "proven_strategies": len(proven),
        "replications_queued": len(replications),
        "replications": replications,
    })

    print(f"  [REPLICATE] {len(solana_wallets)} Solana wallets | "
          f"{len(proven)} proven strategies | "
          f"{len(replications)} replications queued")

    return {
        "phase": "replicate",
        "wallets": len(solana_wallets),
        "strategies": len(proven),
        "replications": len(replications),
    }


def phase_6_record():
    """
    PHASE 6: RECORD -- Log results, track growth, feed back into next cycle.

    This is the compound loop closing. Every cycle's results become
    the next cycle's inputs. Growth compounds on growth.
    """
    print("\n=== PHASE 6: RECORD (Growth Track) ===")

    # Load current portfolio state
    balances = _load(DATA / "wallet_balances.json")
    prices = _load(DATA / "price_oracle_state.json")
    sol_price = prices.get("prices_avg", {}).get("SOL", 0)

    total_sol = 0
    total_staked = 0
    for name, w in balances.items():
        if w.get("chain") != "solana":
            continue
        total_sol += w.get("sol_balance", 0) or 0
        for t in w.get("tokens", []):
            sym = t.get("symbol", "")
            bal = t.get("balance", 0) or 0
            if sym in ("JitoSOL", "mSOL", "bSOL", "INF"):
                total_staked += bal

    crypto_usd = (total_sol + total_staked) * sol_price if sol_price else 0

    # Include Kalshi balance + positions in portfolio
    executor_state = _load(DATA / "trade_executor_state.json")
    kalshi_balance = executor_state.get("balance_after") or executor_state.get("balance_before", 0) or 0
    kalshi_positions = executor_state.get("positions", 0)
    kalshi_trades = executor_state.get("trades_this_cycle", 0)

    # Total USD = crypto + Kalshi cash + Kalshi position value (count × expected $1 payout)
    kalshi_position_value = 0
    for t in executor_state.get("trades", []):
        if t.get("success"):
            kalshi_position_value += t.get("order_details", {}).get("expected_payout", 0)
    total_usd = crypto_usd + kalshi_balance + kalshi_position_value

    # Load growth history
    tracker_path = DATA / "growth_tracker.json"
    tracker = _load(tracker_path, {"entries": [], "initial": None})

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_sol": round(total_sol, 9),
        "total_staked_lst": round(total_staked, 9),
        "total_portfolio_sol": round(total_sol + total_staked, 9),
        "sol_price": sol_price,
        "crypto_usd": round(crypto_usd, 2),
        "kalshi_balance": round(kalshi_balance, 2),
        "kalshi_positions": kalshi_positions,
        "kalshi_position_value": round(kalshi_position_value, 2),
        "total_usd": round(total_usd, 2),
    }

    if not tracker["initial"]:
        tracker["initial"] = entry
        print(f"  [RECORD] Initial portfolio recorded: {entry['total_portfolio_sol']} SOL (${entry['total_usd']})")
    else:
        initial_sol = tracker["initial"]["total_portfolio_sol"]
        current_sol = entry["total_portfolio_sol"]
        growth_sol = current_sol - initial_sol
        growth_pct = (growth_sol / initial_sol * 100) if initial_sol > 0 else 0
        entry["growth_sol"] = round(growth_sol, 9)
        entry["growth_pct"] = round(growth_pct, 4)
        print(f"  [RECORD] Portfolio: {current_sol:.6f} SOL (${entry['total_usd']}) | "
              f"Growth: {growth_sol:+.6f} SOL ({growth_pct:+.2f}%)")

    tracker["entries"].append(entry)
    tracker["entries"] = tracker["entries"][-2000:]  # Keep last 2000 entries
    tracker["latest"] = entry
    tracker["cycles_completed"] = len(tracker["entries"])
    _save(tracker_path, tracker)

    return {"phase": "record", "portfolio": entry}


def phase_7_evolve():
    """
    PHASE 7: EVOLVE -- Trading profits feed the living system.

    Every dollar earned compounds through the evolution engines:
      LIVE_WIRE  → discovers new neural connections between engines
      CHIMERA    → sovereign evolution loop (mutate, score, evolve)

    Also logs all Kalshi trades to PUBLIC_LEDGER for transparency.
    Revenue split: 99% mutual aid / 1% node fuel (CHIMERA_CORE ethics lock).
    """
    print("\n=== PHASE 7: EVOLVE (Self-Evolution) ===")
    results = []

    # 1. Log Kalshi trades to PUBLIC_LEDGER
    executor_state = _load(DATA / "trade_executor_state.json")
    ledger_path = DATA / "PUBLIC_LEDGER.json"
    ledger = _load(ledger_path, {"entries": [], "total_in": 0, "total_out": 0})

    trades = executor_state.get("trades", [])
    new_entries = 0
    total_profit_pending = 0
    for t in trades:
        if t.get("success"):
            details = t.get("order_details", {})
            ledger["entries"].append({
                "type": "kalshi_trade",
                "timestamp": t.get("recorded_at", datetime.now(timezone.utc).isoformat()),
                "ticker": t.get("ticker"),
                "side": t.get("side"),
                "cost": details.get("expected_cost", 0),
                "expected_payout": details.get("expected_payout", 0),
                "expected_profit": details.get("expected_profit", 0),
                "roi_pct": details.get("roi_pct", 0),
                "status": "position_open",
                "owner": "SolarPunk",
            })
            total_profit_pending += details.get("expected_profit", 0)
            new_entries += 1

    ledger["entries"] = ledger["entries"][-5000:]  # Keep last 5000
    _save(ledger_path, ledger)

    if new_entries:
        print(f"  [EVOLVE] Logged {new_entries} trades to PUBLIC_LEDGER "
              f"(${total_profit_pending:.2f} profit pending)")

    # 2. Run TRADING_WIRE -- bridge trading data into revenue ecosystem
    results.append(_run_engine("TRADING_WIRE", "EVOLVE"))
    time.sleep(1)

    # 3. Run LIVE_WIRE -- discover new neural connections
    results.append(_run_engine("LIVE_WIRE", "EVOLVE"))
    time.sleep(1)

    # 4. Run CHIMERA_EVOLUTION_ENGINE -- sovereign evolution loop
    results.append(_run_engine("CHIMERA_EVOLUTION_ENGINE", "EVOLVE"))

    # Check evolution results
    chimera = _load(DATA / "chimera_evolution_report.json")
    live_wire = _load(DATA / "live_wire_report.json")

    mutations = chimera.get("mutations_generated", 0)
    connections = live_wire.get("connections_found", live_wire.get("total_connections", 0))

    print(f"  [EVOLVE] LIVE_WIRE: {connections} connections | "
          f"CHIMERA: {mutations} mutations | "
          f"Profit pending: ${total_profit_pending:.2f}")

    return {
        "phase": "evolve",
        "results": results,
        "trades_logged": new_entries,
        "profit_pending": round(total_profit_pending, 4),
        "connections": connections,
        "mutations": mutations,
    }


def run():
    """
    The living loop. One cycle of the full pipeline.

    Each phase feeds the next. Nothing runs alone.
    The output of this cycle becomes the input of the next.
    Profits → trades → evolution → more profits. Infinite compound.
    """
    print("=" * 70)
    print("  NERVE LOOP -- The Living Loop")
    print("  Everything feeds everything. Nothing runs alone.")
    print("=" * 70)

    # Rate limit check
    can_run, wait = check_cooldown()
    if not can_run:
        print(f"[NERVE] Skipping cycle -- cooldown active ({wait}s)")
        return {"status": "cooldown", "wait_seconds": wait}

    cycle_start = time.time()
    cycle_results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "nerve-loop-v1",
        "phases": {},
    }

    # THE LOOP: each phase feeds the next
    try:
        # Phase 1: SENSE -- gather intelligence
        cycle_results["phases"]["sense"] = phase_1_sense()
        time.sleep(2)

        # Phase 2: OBSERVE -- read wallet states
        cycle_results["phases"]["observe"] = phase_2_observe()
        time.sleep(1)

        # Phase 3: THINK -- compute strategy from intelligence + portfolio
        cycle_results["phases"]["think"] = phase_3_think()
        time.sleep(1)

        # Phase 4: PLAN -- build unified action queue
        cycle_results["phases"]["plan"] = phase_4_plan()
        time.sleep(1)

        # Phase 4b: EXECUTE -- Kalshi trading (if enabled)
        cycle_results["phases"]["execute"] = phase_4b_execute()
        time.sleep(1)

        # Phase 4c: TURBO -- high-frequency compounding on daily markets
        cycle_results["phases"]["turbo"] = phase_4c_turbo()
        time.sleep(1)

        # Phase 4d: ALPACA -- commission-free stocks/ETFs/crypto
        cycle_results["phases"]["alpaca"] = phase_4d_alpaca()
        time.sleep(1)

        # Phase 5: REPLICATE -- apply to all wallets
        cycle_results["phases"]["replicate"] = phase_5_replicate()

        # Phase 6: RECORD -- log growth, close the loop
        cycle_results["phases"]["record"] = phase_6_record()
        time.sleep(1)

        # Phase 7: EVOLVE -- profits feed self-evolution
        cycle_results["phases"]["evolve"] = phase_7_evolve()

        # Phase 8: CROSS-POLLINATE -- route capital between platforms
        print("\n=== PHASE 8: CROSS-POLLINATE (Capital Routing) ===")
        xpol_result = _run_engine("CROSS_POLLINATOR", "XPOL")
        xpol_state = _load(DATA / "cross_pollinator_state.json")
        health = xpol_state.get("mycelium_health", {})
        score = health.get("score", 0)
        grade = health.get("grade", "?")
        total_val = xpol_state.get("total_portfolio_value", 0)
        recs = len(xpol_state.get("transfer_recommendations", []))
        print(f"  [XPOL] Portfolio: ${total_val:.2f} | "
              f"Health: {score}/100 ({grade}) | "
              f"Recommendations: {recs}")
        cycle_results["phases"]["cross_pollinate"] = {
            "phase": "cross_pollinate",
            "result": xpol_result,
            "total_portfolio_value": total_val,
            "mycelium_health_score": score,
            "mycelium_grade": grade,
            "transfer_recommendations": recs,
        }

        # Phase 9: PULSE -- system vital signs snapshot
        print("\n=== PHASE 9: PULSE (Vital Signs) ===")
        pulse_result = _run_engine("PULSE", "PULSE")
        pulse_state = _load(DATA / "pulse_state.json")
        print(f"  [PULSE] Snapshot saved | "
              f"Total: ${pulse_state.get('portfolio', {}).get('total_usd', 0):.2f}")
        cycle_results["phases"]["pulse"] = {
            "phase": "pulse",
            "result": pulse_result,
        }

        # Phase 10: SIGNAL_MESH -- aggregate all signals into composite
        print("\n=== PHASE 10: SIGNAL_MESH (Signal Aggregation) ===")
        mesh_result = _run_engine("SIGNAL_MESH", "SIGNAL_MESH")
        mesh_state = _load(DATA / "signal_mesh_state.json")
        composite = mesh_state.get("composite_signal", {})
        hb = mesh_state.get("heartbeat", {})
        print(f"  [SIGNAL_MESH] Strength: {composite.get('composite_strength', 0)}/100 | "
              f"Direction: {composite.get('dominant_direction', '?').upper()} | "
              f"Conviction: {composite.get('conviction_score', 0)}% | "
              f"Urgency: {composite.get('urgency', 0)}/100")
        print(f"  [SIGNAL_MESH] Sources: {hb.get('alive', 0)} alive / "
              f"{hb.get('stale', 0)} stale / {hb.get('dead', 0)} dead | "
              f"Connectivity: {hb.get('neural_connectivity', 0)}%")
        cycle_results["phases"]["signal_mesh"] = {
            "phase": "signal_mesh",
            "result": mesh_result,
            "composite_strength": composite.get("composite_strength", 0),
            "dominant_direction": composite.get("dominant_direction", "neutral"),
            "conviction_score": composite.get("conviction_score", 0),
            "urgency": composite.get("urgency", 0),
            "neural_connectivity": hb.get("neural_connectivity", 0),
        }

        # Phase 11: SYNAPTIC_BUS -- shared consciousness, every engine aware of every other
        print("\n=== PHASE 11: SYNAPTIC_BUS (Shared Consciousness) ===")
        bus_result = _run_engine("SYNAPTIC_BUS", "SYNAPTIC_BUS")
        bus_state = _load(DATA / "synaptic_bus.json")
        bus_pulse = bus_state.get("last_pulse", {})
        convergence = bus_state.get("convergence", {})
        themes = convergence.get("themes", [])
        theme_str = ", ".join(t.get("theme", "?") for t in themes) if themes else "none"
        print(f"  [SYNAPTIC_BUS] Connectivity: {bus_pulse.get('connectivity', 0)}% | "
              f"Engines: {bus_pulse.get('alive', 0)} alive / "
              f"{bus_pulse.get('stale', 0)} stale / {bus_pulse.get('dead', 0)} dead")
        print(f"  [SYNAPTIC_BUS] Total emissions: {bus_pulse.get('total_emissions', 0)} | "
              f"Sync: {convergence.get('sync_score', 0)}% | Themes: {theme_str}")
        cycle_results["phases"]["synaptic_bus"] = {
            "phase": "synaptic_bus",
            "result": bus_result,
            "connectivity": bus_pulse.get("connectivity", 0),
            "alive": bus_pulse.get("alive", 0),
            "total_emissions": bus_pulse.get("total_emissions", 0),
            "sync_score": convergence.get("sync_score", 0),
        }

        # Phase 12: REFLEX_ARC -- fast-path decisions, millisecond response
        print("\n=== PHASE 12: REFLEX_ARC (Fast-Path Reflexes) ===")
        reflex_result = _run_engine("REFLEX_ARC", "REFLEX_ARC")
        reflex_state = _load(DATA / "reflex_arc_state.json")
        last_cycle = reflex_state.get("last_cycle", {})
        reflex_checked = last_cycle.get("checked", 0)
        reflex_fired = last_cycle.get("fired", 0)
        reflex_ms = last_cycle.get("arc_response_ms", 0)
        lifetime_fires = reflex_state.get("total_fires", 0)
        print(f"  [REFLEX_ARC] Checked: {reflex_checked} | Fired: {reflex_fired} | "
              f"Response: {reflex_ms}ms | Lifetime fires: {lifetime_fires}")
        cycle_results["phases"]["reflex_arc"] = {
            "phase": "reflex_arc",
            "result": reflex_result,
            "checked": reflex_checked,
            "fired": reflex_fired,
            "arc_response_ms": reflex_ms,
            "lifetime_fires": lifetime_fires,
        }

    except Exception as e:
        print(f"\n[NERVE] Loop error: {e}")
        cycle_results["error"] = str(e)

    # Finalize
    elapsed = round(time.time() - cycle_start, 1)
    cycle_results["elapsed_seconds"] = elapsed
    cycle_results["last_cycle_end"] = datetime.now(timezone.utc).isoformat()
    cycle_results["status"] = "complete"

    # Summary
    observe = cycle_results["phases"].get("observe", {})
    plan = cycle_results["phases"].get("plan", {})
    replicate = cycle_results["phases"].get("replicate", {})
    record = cycle_results["phases"].get("record", {})
    portfolio = record.get("portfolio", {})

    evolve = cycle_results["phases"].get("evolve", {})
    execute = cycle_results["phases"].get("execute", {})

    print("\n" + "=" * 70)
    print("  NERVE LOOP CYCLE COMPLETE")
    print(f"  Time: {elapsed}s | Wallets: {observe.get('wallet_count', '?')} | "
          f"Actions: {plan.get('queue_size', 0)} | "
          f"Replications: {replicate.get('replications', 0)}")
    print(f"  Portfolio: {portfolio.get('total_portfolio_sol', '?')} SOL "
          f"(${portfolio.get('total_usd', '?')})")
    if portfolio.get("kalshi_balance") is not None:
        print(f"  Kalshi: ${portfolio.get('kalshi_balance', 0):.2f} cash + "
              f"${portfolio.get('kalshi_position_value', 0):.2f} in positions")
    growth = portfolio.get("growth_pct")
    if growth is not None:
        print(f"  Growth: {growth:+.2f}% since tracking started")
    if evolve.get("mutations"):
        print(f"  Evolution: {evolve.get('connections', 0)} connections | "
              f"{evolve.get('mutations', 0)} mutations | "
              f"${evolve.get('profit_pending', 0):.2f} profit pending")
    print(f"  Next cycle in {MIN_CYCLE_INTERVAL}s (rate limit protection)")
    print("=" * 70)

    _save(DATA / "nerve_loop_state.json", cycle_results)
    return cycle_results


if __name__ == "__main__":
    run()
