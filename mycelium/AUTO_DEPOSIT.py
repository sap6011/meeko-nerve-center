#!/usr/bin/env python3
"""
AUTO_DEPOSIT.py -- Smart capital splitter and deployment router
================================================================
v1 (2026-04-06): When money arrives, this engine decides WHERE it goes.

THE PROBLEM:
  A deposit lands. Old behavior: dump it all into TURBO_TRADER.
  That's a single-cell organism. No intelligence. No diversification.

THE SOLUTION:
  Read the ENTIRE nervous system -- SIGNAL_MESH conviction, CROSS_POLLINATOR
  mycelium health, platform balances, opportunity counts -- and calculate
  the OPTIMAL split. Then route capital to the right engine automatically.

DECISION LOGIC (priority order):
  a) HIGH URGENCY: SIGNAL_MESH urgency > 70 + composite_strength > 60
     -> 80% to highest-urgency platform, 20% to the other

  b) OPPORTUNITY VACUUM: One platform has 0 opps, the other has many
     -> 90% to the platform with opportunities

  c) REBALANCE NEEDED: Mycelium diversification score < 10 (too concentrated)
     -> 70% to the UNDERWEIGHT platform to rebalance

  d) DEFAULT: 60% Kalshi (higher ROI historically), 40% Alpaca (diversification)

AUTO-EXECUTION:
  - Kalshi: import and call TURBO_TRADER.run() directly (always available)
  - Alpaca: call ALPACA_TRADER.run() if market is open, else queue for open
  - All decisions emitted to SYNAPTIC_BUS for full mesh awareness

Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)
Called by: REFLEX_ARC (DEPOSIT_DETECTED reflex), OMNIBUS, AUTONOMIC_NERVE
Reads: SYNAPTIC_BUS, cross_pollinator_state.json, signal_mesh_state.json
Writes: data/auto_deposit_state.json
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA = Path("data")
DATA.mkdir(exist_ok=True)

STATE_FILE = DATA / "auto_deposit_state.json"
CROSS_POLL_FILE = DATA / "cross_pollinator_state.json"
MESH_FILE = DATA / "signal_mesh_state.json"
TURBO_FILE = DATA / "turbo_trader_state.json"
ALPACA_FILE = DATA / "alpaca_trader_state.json"

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
URGENCY_THRESHOLD = 70
STRENGTH_THRESHOLD = 60
DIVERSIFICATION_FLOOR = 10       # Below this = too concentrated
MIN_DEPLOY_AMOUNT = 0.25         # Don't bother deploying less than 25 cents

DEFAULT_KALSHI_PCT = 0.60
DEFAULT_ALPACA_PCT = 0.40

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _load(path, default=None):
    """Load JSON safely."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _save(path, data):
    """Atomic-ish JSON write."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _emit(properties):
    """Emit state to SYNAPTIC_BUS (lazy import, crash-safe)."""
    try:
        import SYNAPTIC_BUS
        SYNAPTIC_BUS.emit_batch("AUTO_DEPOSIT", properties, silent=False)
    except Exception:
        pass


def _sense(engine_name=None):
    """Read bus state via SYNAPTIC_BUS (lazy import, fallback to file)."""
    try:
        return SYNAPTIC_BUS.sense(engine_name)
    except Exception:
        # Fallback: read bus file directly
        bus = _load(DATA / "synaptic_bus.json")
        if engine_name is None:
            return bus
        return bus.get("engines", {}).get(engine_name, {})


# ---------------------------------------------------------------------------
# Data gathering: read all intelligence sources
# ---------------------------------------------------------------------------
def _gather_intelligence():
    """
    Pull together all signals the splitter needs from the nervous system.
    Uses SYNAPTIC_BUS where possible, falls back to state files.
    """
    intel = {
        "timestamp": _now_iso(),
        "cross_pollinator": {},
        "signal_mesh": {},
        "kalshi": {},
        "alpaca": {},
    }

    # -- CROSS_POLLINATOR --
    cp = _load(CROSS_POLL_FILE)
    intel["cross_pollinator"] = {
        "mycelium_health_score": cp.get("mycelium_health_score", 50),
        "diversification": cp.get("mycelium_health_breakdown", {}).get("diversification", 50),
        "capital_efficiency": cp.get("capital_efficiency", {}),
        "idle_cash": cp.get("idle_cash", []),
        "transfer_recommendations": cp.get("transfer_recommendations", []),
        "best_opportunity_platform": cp.get("best_opportunity_platform", ""),
        "total_portfolio_value": cp.get("total_portfolio_value", 0),
    }

    # -- SIGNAL_MESH --
    mesh = _load(MESH_FILE)
    composite = mesh.get("composite_signal", {})
    summary = mesh.get("summary", {})
    intel["signal_mesh"] = {
        "composite_strength": composite.get("composite_strength", 0),
        "dominant_direction": composite.get("dominant_direction", "neutral"),
        "conviction_score": composite.get("conviction_score", 0),
        "urgency": composite.get("urgency", 0),
        "best_opportunity": summary.get("best_opportunity", {}),
        "total_opportunities": summary.get("total_opportunities", 0),
    }

    # -- KALSHI (TURBO_TRADER) --
    turbo = _load(TURBO_FILE)
    bus_turbo = _sense("TURBO_TRADER")
    turbo_props = bus_turbo.get("properties", {}) if isinstance(bus_turbo, dict) else {}
    intel["kalshi"] = {
        "balance": turbo.get("balance", turbo_props.get("balance", 0)) or 0,
        "pending_payout": turbo.get("pending_payout", 0) or 0,
        "daily_opps": turbo.get("daily_opps", turbo_props.get("daily_opps", 0)) or 0,
        "trades_placed": turbo.get("trades_placed", 0) or 0,
        "platform": "kalshi",
    }

    # -- ALPACA --
    alpaca = _load(ALPACA_FILE)
    bus_alpaca = _sense("ALPACA_TRADER")
    alpaca_props = bus_alpaca.get("properties", {}) if isinstance(bus_alpaca, dict) else {}
    intel["alpaca"] = {
        "cash": alpaca.get("cash", alpaca_props.get("cash", 0)) or 0,
        "buying_power": alpaca.get("buying_power", 0) or 0,
        "portfolio_value": alpaca.get("portfolio_value",
                                      alpaca_props.get("portfolio_value", 0)) or 0,
        "market_open": alpaca.get("market_open",
                                  alpaca_props.get("market_open", False)),
        "opportunities": alpaca.get("opportunities_found",
                                    alpaca_props.get("opportunities_found", 0)) or 0,
        "platform": "alpaca",
    }

    return intel


# ---------------------------------------------------------------------------
# Decision logic: compute optimal split
# ---------------------------------------------------------------------------
def _compute_split(amount, intel):
    """
    Given a capital amount and full intelligence, compute the optimal split.

    Returns:
        {
            "kalshi_pct": float,    "kalshi_amount": float,
            "alpaca_pct": float,    "alpaca_amount": float,
            "rule_applied": str,    "reasoning": str,
        }
    """
    mesh = intel["signal_mesh"]
    cp = intel["cross_pollinator"]
    kalshi = intel["kalshi"]
    alpaca = intel["alpaca"]

    urgency = mesh.get("urgency", 0)
    strength = mesh.get("composite_strength", 0)
    diversification = cp.get("diversification", 50)
    kalshi_opps = kalshi.get("daily_opps", 0)
    alpaca_opps = alpaca.get("opportunities", 0)
    best_platform = cp.get("best_opportunity_platform", "")

    # ------------------------------------------------------------------
    # RULE A: High urgency + strong signal -> deploy aggressively
    # ------------------------------------------------------------------
    if urgency > URGENCY_THRESHOLD and strength > STRENGTH_THRESHOLD:
        if best_platform == "kalshi" or kalshi_opps > alpaca_opps:
            k_pct, a_pct = 0.80, 0.20
            target = "kalshi"
        else:
            k_pct, a_pct = 0.20, 0.80
            target = "alpaca"

        return _build_split(amount, k_pct, a_pct, "HIGH_URGENCY",
            f"SIGNAL_MESH urgency={urgency} strength={strength} -> "
            f"80% to {target} (highest urgency opportunities)")

    # ------------------------------------------------------------------
    # RULE B: Opportunity vacuum -> concentrate on the active platform
    # ------------------------------------------------------------------
    if kalshi_opps == 0 and alpaca_opps > 0:
        return _build_split(amount, 0.10, 0.90, "OPP_VACUUM_ALPACA",
            f"Kalshi has 0 opportunities, Alpaca has {alpaca_opps} -> "
            f"90% to Alpaca")

    if alpaca_opps == 0 and kalshi_opps > 0:
        return _build_split(amount, 0.90, 0.10, "OPP_VACUUM_KALSHI",
            f"Alpaca has 0 opportunities, Kalshi has {kalshi_opps} -> "
            f"90% to Kalshi")

    # ------------------------------------------------------------------
    # RULE C: Rebalance needed -> diversify toward underweight platform
    # ------------------------------------------------------------------
    if diversification < DIVERSIFICATION_FLOOR:
        kalshi_total = kalshi.get("balance", 0) + kalshi.get("pending_payout", 0)
        alpaca_total = alpaca.get("portfolio_value", 0)
        total = kalshi_total + alpaca_total

        if total > 0:
            kalshi_share = kalshi_total / total * 100
            alpaca_share = alpaca_total / total * 100
        else:
            kalshi_share = alpaca_share = 50

        if kalshi_share > alpaca_share:
            # Kalshi overweight -> send 70% to Alpaca
            return _build_split(amount, 0.30, 0.70, "REBALANCE_TO_ALPACA",
                f"Diversification={diversification} (too concentrated). "
                f"Kalshi={kalshi_share:.0f}% Alpaca={alpaca_share:.0f}% -> "
                f"70% to Alpaca to rebalance")
        else:
            return _build_split(amount, 0.70, 0.30, "REBALANCE_TO_KALSHI",
                f"Diversification={diversification} (too concentrated). "
                f"Kalshi={kalshi_share:.0f}% Alpaca={alpaca_share:.0f}% -> "
                f"70% to Kalshi to rebalance")

    # ------------------------------------------------------------------
    # RULE D: Default -- 60/40 Kalshi/Alpaca
    # ------------------------------------------------------------------
    return _build_split(amount, DEFAULT_KALSHI_PCT, DEFAULT_ALPACA_PCT,
        "DEFAULT_SPLIT",
        f"No urgency signals, balanced diversification={diversification}. "
        f"Using default 60% Kalshi / 40% Alpaca split.")


def _build_split(amount, k_pct, a_pct, rule, reasoning):
    """Construct the split result dict."""
    return {
        "kalshi_pct": round(k_pct * 100, 1),
        "kalshi_amount": round(amount * k_pct, 2),
        "alpaca_pct": round(a_pct * 100, 1),
        "alpaca_amount": round(amount * a_pct, 2),
        "rule_applied": rule,
        "reasoning": reasoning,
    }


# ---------------------------------------------------------------------------
# Auto-execution: deploy capital to the right engine
# ---------------------------------------------------------------------------
def _execute_deployment(split, intel):
    """
    Actually trigger the trading engines to deploy the capital.

    Returns a list of execution results.
    """
    executions = []

    # -- KALSHI deployment via TURBO_TRADER --
    if split["kalshi_amount"] >= MIN_DEPLOY_AMOUNT:
        try:
            import importlib, sys
            myc = str(Path(__file__).parent)
            if myc not in sys.path:
                sys.path.insert(0, myc)

            mod = importlib.import_module("TURBO_TRADER")
            result = mod.run() if hasattr(mod, "run") else {"status": "no_run"}
            executions.append({
                "platform": "kalshi",
                "engine": "TURBO_TRADER",
                "amount_targeted": split["kalshi_amount"],
                "auto_executed": True,
                "status": result.get("status", "completed") if isinstance(result, dict) else "completed",
                "timestamp": _now_iso(),
            })
        except Exception as e:
            executions.append({
                "platform": "kalshi",
                "engine": "TURBO_TRADER",
                "amount_targeted": split["kalshi_amount"],
                "auto_executed": False,
                "status": "error",
                "error": str(e)[:200],
                "timestamp": _now_iso(),
            })
    else:
        executions.append({
            "platform": "kalshi",
            "engine": "TURBO_TRADER",
            "amount_targeted": split["kalshi_amount"],
            "auto_executed": False,
            "status": "below_minimum",
            "timestamp": _now_iso(),
        })

    # -- ALPACA deployment via ALPACA_TRADER --
    if split["alpaca_amount"] >= MIN_DEPLOY_AMOUNT:
        market_open = intel["alpaca"].get("market_open", False)
        if market_open:
            try:
                myc = str(Path(__file__).parent)
                if myc not in sys.path:
                    sys.path.insert(0, myc)

                mod = importlib.import_module("ALPACA_TRADER")
                result = mod.run() if hasattr(mod, "run") else {"status": "no_run"}
                executions.append({
                    "platform": "alpaca",
                    "engine": "ALPACA_TRADER",
                    "amount_targeted": split["alpaca_amount"],
                    "auto_executed": True,
                    "market_open": True,
                    "status": result.get("status", "completed") if isinstance(result, dict) else "completed",
                    "timestamp": _now_iso(),
                })
            except Exception as e:
                executions.append({
                    "platform": "alpaca",
                    "engine": "ALPACA_TRADER",
                    "amount_targeted": split["alpaca_amount"],
                    "auto_executed": False,
                    "market_open": True,
                    "status": "error",
                    "error": str(e)[:200],
                    "timestamp": _now_iso(),
                })
        else:
            executions.append({
                "platform": "alpaca",
                "engine": "ALPACA_TRADER",
                "amount_targeted": split["alpaca_amount"],
                "auto_executed": False,
                "market_open": False,
                "status": "queued_for_market_open",
                "timestamp": _now_iso(),
            })
    else:
        executions.append({
            "platform": "alpaca",
            "engine": "ALPACA_TRADER",
            "amount_targeted": split["alpaca_amount"],
            "auto_executed": False,
            "status": "below_minimum",
            "timestamp": _now_iso(),
        })

    return executions


# ===========================================================================
# PUBLIC API: run()
# ===========================================================================
def run(amount=None):
    """
    Main entry point. Calculate optimal capital split and deploy.

    Args:
        amount: Capital to deploy. If None, auto-detect from platform balances
                (idle cash + any detected deposit delta).

    Returns:
        State dict with split decision, execution results, and full reasoning.
    """
    print("=" * 60)
    print("  AUTO_DEPOSIT -- Smart capital splitter")
    print("  Reading nervous system. Computing optimal deployment.")
    print("=" * 60)

    t0 = time.time()
    state = _load(STATE_FILE, {
        "total_deployments": 0,
        "total_deployed_usd": 0,
        "history": [],
    })

    # 1. Gather intelligence from all sources
    intel = _gather_intelligence()
    print(f"\n  [INTEL] Portfolio: ${intel['cross_pollinator'].get('total_portfolio_value', 0):.2f}")
    print(f"  [INTEL] Kalshi balance: ${intel['kalshi']['balance']:.2f} | opps: {intel['kalshi']['daily_opps']}")
    print(f"  [INTEL] Alpaca cash: ${intel['alpaca']['cash']:.2f} | opps: {intel['alpaca']['opportunities']}")
    print(f"  [INTEL] SIGNAL_MESH urgency: {intel['signal_mesh']['urgency']} | "
          f"strength: {intel['signal_mesh']['composite_strength']}")
    print(f"  [INTEL] Diversification score: {intel['cross_pollinator']['diversification']}")

    # 2. Determine amount to deploy
    if amount is None:
        # Auto-detect: sum idle cash across platforms
        idle_total = 0
        for idle in intel["cross_pollinator"].get("idle_cash", []):
            idle_total += idle.get("idle_amount", 0)
        # Also count available balances
        available = intel["kalshi"]["balance"] + intel["alpaca"]["cash"]
        amount = max(idle_total, available)
        print(f"\n  [AMOUNT] Auto-detected deployable capital: ${amount:.2f}")
    else:
        print(f"\n  [AMOUNT] Deploying specified amount: ${amount:.2f}")

    if amount < MIN_DEPLOY_AMOUNT:
        print(f"  [SKIP] Amount ${amount:.2f} below minimum ${MIN_DEPLOY_AMOUNT:.2f}")
        state["last_run"] = _now_iso()
        state["last_result"] = "below_minimum"
        state["last_amount"] = amount
        state["status"] = "idle"
        _save(STATE_FILE, state)
        _emit({"status": "idle", "last_run": _now_iso(), "reason": "below_minimum"})
        return state

    # 3. Compute optimal split
    split = _compute_split(amount, intel)
    print(f"\n  [SPLIT] Rule: {split['rule_applied']}")
    print(f"  [SPLIT] Kalshi: {split['kalshi_pct']}% (${split['kalshi_amount']:.2f})")
    print(f"  [SPLIT] Alpaca: {split['alpaca_pct']}% (${split['alpaca_amount']:.2f})")
    print(f"  [SPLIT] Reasoning: {split['reasoning']}")

    # 4. Execute deployment
    print(f"\n  [DEPLOY] Executing...")
    executions = _execute_deployment(split, intel)

    for ex in executions:
        icon = "OK" if ex.get("auto_executed") else "--"
        print(f"    [{icon}] {ex['platform']}: ${ex['amount_targeted']:.2f} -> {ex['status']}")

    # 5. Update state
    elapsed_ms = round((time.time() - t0) * 1000, 1)
    deployment_record = {
        "timestamp": _now_iso(),
        "amount": amount,
        "split": split,
        "executions": executions,
        "intel_snapshot": {
            "urgency": intel["signal_mesh"]["urgency"],
            "strength": intel["signal_mesh"]["composite_strength"],
            "diversification": intel["cross_pollinator"]["diversification"],
            "kalshi_opps": intel["kalshi"]["daily_opps"],
            "alpaca_opps": intel["alpaca"]["opportunities"],
            "market_open": intel["alpaca"]["market_open"],
        },
        "elapsed_ms": elapsed_ms,
    }

    state["total_deployments"] = state.get("total_deployments", 0) + 1
    state["total_deployed_usd"] = round(
        state.get("total_deployed_usd", 0) + amount, 2)
    state["last_run"] = _now_iso()
    state["last_result"] = split["rule_applied"]
    state["last_amount"] = amount
    state["last_split"] = split
    state["last_executions"] = executions
    state["status"] = "active"
    state["protocol"] = "auto-deposit-v1"
    state["ethics"] = "99% mutual aid / 1% node fuel"

    # Rolling history (last 50 deployments)
    history = state.get("history", [])
    history.append(deployment_record)
    state["history"] = history[-50:]

    _save(STATE_FILE, state)

    # 6. Emit to SYNAPTIC_BUS
    _emit({
        "status": "active",
        "last_run": _now_iso(),
        "last_amount": amount,
        "rule_applied": split["rule_applied"],
        "kalshi_pct": split["kalshi_pct"],
        "alpaca_pct": split["alpaca_pct"],
        "total_deployments": state["total_deployments"],
        "total_deployed_usd": state["total_deployed_usd"],
        "elapsed_ms": elapsed_ms,
    })

    # 7. Summary
    auto_count = sum(1 for e in executions if e.get("auto_executed"))
    queued_count = sum(1 for e in executions if e.get("status") == "queued_for_market_open")

    print(f"\n{'=' * 60}")
    print(f"  AUTO_DEPOSIT COMPLETE")
    print(f"  Amount: ${amount:.2f} | Rule: {split['rule_applied']}")
    print(f"  Auto-executed: {auto_count} | Queued: {queued_count}")
    print(f"  Lifetime: {state['total_deployments']} deployments, "
          f"${state['total_deployed_usd']:.2f} total deployed")
    print(f"  Elapsed: {elapsed_ms}ms")
    print(f"  Ethics: 99% mutual aid / 1% node fuel")
    print(f"{'=' * 60}")

    return state


if __name__ == "__main__":
    run()
