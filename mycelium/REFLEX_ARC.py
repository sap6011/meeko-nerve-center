#!/usr/bin/env python3
"""
REFLEX_ARC.py -- Fast-path decision engine (bypasses slow AI for speed)
========================================================================
v1 (2026-04-06): Biological reflex arcs for the SolarPunk nervous system.

THE BIOLOGY:
  When you touch a hot stove, your hand pulls away BEFORE you consciously
  feel pain. The signal goes: sensory neuron -> spinal cord -> motor neuron.
  It bypasses the brain entirely. That's a reflex arc.

  This engine IS that spinal cord. It reads the SYNAPTIC_BUS and SIGNAL_MESH,
  evaluates hardcoded if-then rules, and fires actions INSTANTLY -- no AI
  inference, no LLM calls, no waiting. Pure reactive speed.

REFLEXES (ordered by priority, 13 total):
  0. THERMAL_DANGER     -- CPU > 90% or RAM > 95% -> PAUSE all engines
  1. ENGINE_CRASH       -- Any engine error on bus -> log + restart once
  2. DEPOSIT_DETECTED   -- New balance increase -> deploy capital immediately
  3. SETTLEMENT_SPIKE   -- Kalshi positions settle -> compound cycle
  4. MARKET_OPEN        -- Alpaca market opens -> trigger queued trades
  5. ARBITRAGE_WINDOW   -- Arb scanner finds opps -> trigger TURBO
  5. REGIME_SHIFT       -- GLOBAL_MARKETS regime change -> rebalance strategy
  6. CONVERGENCE_ALERT  -- SIGNAL_MESH conviction > 80% + urgency > 60
  7. STALE_BUS          -- Bus not updated in 10+ min -> refresh
  8. CASH_IDLE          -- Cash idle > 30 min with opps available -> trade
  8. METABOLISM_ALERT   -- Ecosystem health drops -> investigate + refresh
  9. SELF_FUNDING_ALERT -- AI costs > trading profits -> switch to local
 10. GROWTH_STALL       -- Evolution LOW or no new engines 24h -> alert

ARCHITECTURE:
  - All engine imports are LAZY (inside functions) to prevent circular imports
  - Every engine call is wrapped in try/except -- reflexes NEVER crash
  - Cooldown: 5 min per reflex to prevent rapid re-firing
  - Uses SYNAPTIC_BUS.emit_batch() for all bus communication
  - Tracks response times in milliseconds for performance tuning

Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)
Called by: NERVE_LOOP (Phase 12), OMNIBUS, AUTONOMIC_NERVE (task_queue)
Writes: data/reflex_arc_state.json, data/reflex_arc_log.json
Reads: data/synaptic_bus.json, data/signal_mesh_state.json
"""

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA = Path("data")
DATA.mkdir(exist_ok=True)

STATE_FILE = DATA / "reflex_arc_state.json"
LOG_FILE = DATA / "reflex_arc_log.json"
BUS_FILE = DATA / "synaptic_bus.json"
MESH_FILE = DATA / "signal_mesh_state.json"

MAX_LOG_ENTRIES = 200
COOLDOWN_SEC = 300  # 5 minutes between same reflex firing

# ---------------------------------------------------------------------------
# Priority-ordered reflex definitions
# ---------------------------------------------------------------------------
REFLEX_REGISTRY = [
    {"id": "THERMAL_DANGER",     "priority": 0, "desc": "CPU/RAM critical -> pause all"},
    {"id": "ENGINE_CRASH",       "priority": 1, "desc": "Engine error -> restart once"},
    {"id": "DEPOSIT_DETECTED",   "priority": 2, "desc": "New funds -> deploy immediately"},
    {"id": "SETTLEMENT_SPIKE",   "priority": 3, "desc": "Kalshi settled -> compound"},
    {"id": "MARKET_OPEN",        "priority": 4, "desc": "Alpaca market opens -> trade"},
    {"id": "ARBITRAGE_WINDOW",   "priority": 5, "desc": "Arb found -> trigger TURBO"},
    {"id": "CONVERGENCE_ALERT",  "priority": 6, "desc": "High conviction + urgency -> trade"},
    {"id": "STALE_BUS",          "priority": 7, "desc": "Bus stale 10+ min -> refresh"},
    {"id": "CASH_IDLE",          "priority": 8, "desc": "Idle cash + opps -> deploy"},
    {"id": "SELF_FUNDING_ALERT", "priority": 9, "desc": "AI cost > profits -> go local"},
    {"id": "GROWTH_STALL",       "priority": 10, "desc": "Evolution low or no new engines 24h -> alert"},
    {"id": "REGIME_SHIFT",       "priority": 5, "desc": "Global regime change -> adjust strategy"},
    {"id": "METABOLISM_ALERT",   "priority": 8, "desc": "Ecosystem health drop -> investigate"},
]


# ---------------------------------------------------------------------------
# Utility: file I/O
# ---------------------------------------------------------------------------
def _load(path, default=None):
    """Load JSON file with safe fallback."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _save(path, data):
    """Atomic-ish JSON write."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _ms_since(start):
    """Milliseconds elapsed since start time."""
    return round((time.time() - start) * 1000, 1)


# ---------------------------------------------------------------------------
# Logging: rolling reflex log (200 entries max)
# ---------------------------------------------------------------------------
def _log_reflex(reflex_id, triggered, action_taken, response_ms, detail=""):
    """Append to rolling reflex log."""
    log = _load(LOG_FILE, {"entries": []})
    entries = log.get("entries", [])

    entries.append({
        "timestamp": _now_iso(),
        "reflex": reflex_id,
        "triggered": triggered,
        "action": action_taken,
        "response_ms": response_ms,
        "detail": str(detail)[:500],
    })

    # Rolling window
    entries = entries[-MAX_LOG_ENTRIES:]
    log["entries"] = entries
    log["last_updated"] = _now_iso()
    log["total_logged"] = len(entries)
    _save(LOG_FILE, log)


# ---------------------------------------------------------------------------
# Cooldown check
# ---------------------------------------------------------------------------
def _check_cooldown(reflex_id, state):
    """Return True if reflex is allowed to fire (past cooldown)."""
    last_fired = state.get("last_fired", {}).get(reflex_id)
    if not last_fired:
        return True
    try:
        last_dt = datetime.fromisoformat(last_fired.replace("Z", "+00:00"))
        elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
        return elapsed >= COOLDOWN_SEC
    except Exception:
        return True


def _mark_fired(reflex_id, state):
    """Record that a reflex just fired."""
    if "last_fired" not in state:
        state["last_fired"] = {}
    state["last_fired"][reflex_id] = _now_iso()


# ---------------------------------------------------------------------------
# Bus communication helpers
# ---------------------------------------------------------------------------
def _emit_to_bus(engine, properties):
    """Emit reflex state to SYNAPTIC_BUS (lazy import, safe fallback)."""
    try:
        import SYNAPTIC_BUS
        SYNAPTIC_BUS.emit_batch(engine, properties, silent=False)
    except Exception:
        pass  # Bus unavailable -- reflex still works standalone


def _read_bus():
    """Read synaptic bus state directly from file (faster than import)."""
    return _load(BUS_FILE)


def _read_mesh():
    """Read signal mesh state."""
    return _load(MESH_FILE)


def _run_engine_safe(engine_name):
    """Import and run an engine's run() with full crash protection."""
    try:
        import importlib
        import sys

        mycelium_dir = str(Path(__file__).parent)
        if mycelium_dir not in sys.path:
            sys.path.insert(0, mycelium_dir)

        if engine_name in sys.modules:
            mod = importlib.reload(sys.modules[engine_name])
        else:
            mod = importlib.import_module(engine_name)

        if hasattr(mod, "run"):
            return mod.run()
        return {"status": "no_run_method"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ===========================================================================
# REFLEX IMPLEMENTATIONS -- Each returns (triggered: bool, detail: str)
# ===========================================================================

def _reflex_thermal_danger(bus, mesh, state):
    """PRIORITY 0: CPU > 90% or RAM > 95% -> pause all engines."""
    t0 = time.time()
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=None)  # Non-blocking: instant read from OS counter
        ram = psutil.virtual_memory().percent
    except ImportError:
        # psutil not installed -- check bus for any reported thermals
        thermals = bus.get("engines", {}).get("PULSE", {}).get("properties", {})
        cpu = thermals.get("cpu_percent", 0)
        ram = thermals.get("ram_percent", 0)
        if not cpu and not ram:
            return False, "psutil unavailable, no bus data", _ms_since(t0)
    except Exception:
        return False, "thermal check failed", _ms_since(t0)

    if cpu > 90 or ram > 95:
        detail = f"DANGER: CPU={cpu}% RAM={ram}% -- emitting PAUSE to all engines"
        _emit_to_bus("REFLEX_ARC", {
            "action": "THERMAL_PAUSE",
            "cpu_percent": cpu,
            "ram_percent": ram,
            "status": "PAUSING_ALL",
        })
        return True, detail, _ms_since(t0)

    return False, f"OK: CPU={cpu}% RAM={ram}%", _ms_since(t0)


def _reflex_engine_crash(bus, mesh, state):
    """PRIORITY 1: Any engine error on bus -> log and try restart once."""
    t0 = time.time()
    engines = bus.get("engines", {})
    crashed = []

    for name, eng_data in engines.items():
        props = eng_data.get("properties", {})
        status = props.get("status", "")
        if status == "error" or props.get("error"):
            # Check if we already tried restarting this engine this cycle
            restart_key = f"restart_{name}"
            already_tried = state.get("restart_attempts", {}).get(name, 0)
            if already_tried < 1:
                crashed.append(name)

    if not crashed:
        return False, "no crashes detected", _ms_since(t0)

    # Try to restart first crashed engine only (one per cycle to avoid cascade)
    target = crashed[0]
    detail = f"Restarting {target} (crash detected on bus)"
    result = _run_engine_safe(target)
    restart_status = result.get("status", "unknown")

    # Track attempt
    if "restart_attempts" not in state:
        state["restart_attempts"] = {}
    state["restart_attempts"][target] = state["restart_attempts"].get(target, 0) + 1

    _emit_to_bus("REFLEX_ARC", {
        "action": "ENGINE_RESTART",
        "target": target,
        "restart_result": restart_status,
    })

    detail += f" -> {restart_status}"
    if len(crashed) > 1:
        detail += f" (+{len(crashed) - 1} others queued)"

    return True, detail, _ms_since(t0)


def _reflex_deposit_detected(bus, mesh, state):
    """PRIORITY 2: New deposit/balance increase -> route through AUTO_DEPOSIT smart splitter."""
    t0 = time.time()
    engines = bus.get("engines", {})

    deposit_amount = 0
    deposit_source = None

    # Check TURBO_TRADER for deposit flag
    turbo = engines.get("TURBO_TRADER", {}).get("properties", {})
    if turbo.get("deposit_detected"):
        deposit_source = "kalshi_deposit_flag"
        deposit_amount = turbo.get("balance", 0) or 0

    # Check Alpaca for balance increases
    if not deposit_source:
        alpaca = engines.get("ALPACA_TRADER", {}).get("properties", {})
        prev_balance = state.get("prev_balances", {}).get("alpaca", 0)
        curr_balance = alpaca.get("portfolio_value", 0) or 0
        if curr_balance > 0 and prev_balance > 0 and (curr_balance - prev_balance) > 1.0:
            deposit_source = "alpaca_balance_increase"
            deposit_amount = round(curr_balance - prev_balance, 2)

    if not deposit_source:
        return False, "no deposits detected", _ms_since(t0)

    # Route through AUTO_DEPOSIT smart splitter instead of directly calling traders
    detail = (f"Deposit detected ({deposit_source}, ~${deposit_amount:.2f}) "
              f"-- routing through AUTO_DEPOSIT smart splitter")
    result = _run_engine_safe("AUTO_DEPOSIT")
    _emit_to_bus("REFLEX_ARC", {
        "action": "DEPOSIT_SMART_SPLIT",
        "deposit_source": deposit_source,
        "deposit_amount": deposit_amount,
        "router": "AUTO_DEPOSIT",
        "result": result.get("status", "unknown") if isinstance(result, dict) else "completed",
    })
    return True, detail, _ms_since(t0)


def _reflex_settlement_spike(bus, mesh, state):
    """PRIORITY 3: Kalshi positions settle (balance jump) -> compound cycle."""
    t0 = time.time()
    engines = bus.get("engines", {})
    turbo = engines.get("TURBO_TRADER", {}).get("properties", {})

    settlements = turbo.get("settlements_24h", 0) or 0
    prev_settlements = state.get("prev_settlements_24h", 0)

    if settlements > prev_settlements and settlements > 0:
        detail = f"New settlements: {prev_settlements} -> {settlements} -- compounding"
        result = _run_engine_safe("TURBO_TRADER")
        _emit_to_bus("REFLEX_ARC", {
            "action": "SETTLEMENT_COMPOUND",
            "new_settlements": settlements - prev_settlements,
            "total_settlements": settlements,
            "result": result.get("status", "unknown"),
        })
        return True, detail, _ms_since(t0)

    return False, f"settlements steady at {settlements}", _ms_since(t0)


def _reflex_market_open(bus, mesh, state):
    """PRIORITY 4: Alpaca market transitions to open -> trigger queued trades."""
    t0 = time.time()
    engines = bus.get("engines", {})
    alpaca = engines.get("ALPACA_TRADER", {}).get("properties", {})

    market_open = alpaca.get("market_open", False)
    prev_market_open = state.get("prev_market_open", False)

    # Transition detection: was closed, now open
    if market_open and not prev_market_open:
        detail = "Market OPENED -- triggering ALPACA_TRADER for queued trades"
        result = _run_engine_safe("ALPACA_TRADER")
        _emit_to_bus("REFLEX_ARC", {
            "action": "MARKET_OPEN_TRADE",
            "result": result.get("status", "unknown"),
        })
        return True, detail, _ms_since(t0)

    status = "open" if market_open else "closed"
    return False, f"market {status} (no transition)", _ms_since(t0)


def _reflex_arbitrage_window(bus, mesh, state):
    """PRIORITY 5: Arbitrage scanner finds opportunities -> trigger TURBO."""
    t0 = time.time()
    engines = bus.get("engines", {})
    arb = engines.get("ARBITRAGE_SCANNER", {}).get("properties", {})

    opps = arb.get("actionable_opportunities", 0)
    if isinstance(opps, list):
        opps = len(opps)

    if opps and opps > 0:
        detail = f"Arbitrage: {opps} opportunities -- triggering TURBO_TRADER"
        result = _run_engine_safe("TURBO_TRADER")
        _emit_to_bus("REFLEX_ARC", {
            "action": "ARBITRAGE_DEPLOY",
            "opportunities": opps,
            "result": result.get("status", "unknown"),
        })
        return True, detail, _ms_since(t0)

    return False, "no arb opportunities", _ms_since(t0)


def _reflex_convergence_alert(bus, mesh, state):
    """PRIORITY 6: SIGNAL_MESH conviction > 80% and urgency > 60 -> trade."""
    t0 = time.time()
    composite = mesh.get("composite_signal", {})
    conviction = composite.get("conviction_score", 0)
    urgency = composite.get("urgency", 0)
    direction = composite.get("dominant_direction", "neutral")

    if conviction > 80 and urgency > 60:
        detail = (f"CONVERGENCE: conviction={conviction}% urgency={urgency} "
                  f"direction={direction} -- deploying")

        # Route to appropriate trader based on direction
        if direction in ("bullish", "buy"):
            target = "ALPACA_TRADER"
        else:
            target = "TURBO_TRADER"

        result = _run_engine_safe(target)
        _emit_to_bus("REFLEX_ARC", {
            "action": "CONVERGENCE_TRADE",
            "conviction": conviction,
            "urgency": urgency,
            "direction": direction,
            "target_engine": target,
            "result": result.get("status", "unknown"),
        })
        return True, detail, _ms_since(t0)

    return False, f"conviction={conviction}% urgency={urgency} (below threshold)", _ms_since(t0)


def _reflex_stale_bus(bus, mesh, state):
    """PRIORITY 7: Bus not updated in 10+ minutes -> refresh."""
    t0 = time.time()
    last_pulse = bus.get("last_pulse", {})
    last_updated = last_pulse.get("timestamp") or bus.get("last_updated")

    if not last_updated:
        detail = "Bus has no timestamp -- triggering refresh"
        result = _run_engine_safe("SYNAPTIC_BUS")
        _emit_to_bus("REFLEX_ARC", {
            "action": "STALE_BUS_REFRESH",
            "reason": "no_timestamp",
            "result": result.get("status", "unknown"),
        })
        return True, detail, _ms_since(t0)

    try:
        last_dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        age_sec = (datetime.now(timezone.utc) - last_dt).total_seconds()
    except Exception:
        age_sec = 9999

    if age_sec > 600:  # 10 minutes
        detail = f"Bus stale ({int(age_sec)}s old) -- triggering SYNAPTIC_BUS refresh"
        result = _run_engine_safe("SYNAPTIC_BUS")
        _emit_to_bus("REFLEX_ARC", {
            "action": "STALE_BUS_REFRESH",
            "age_seconds": int(age_sec),
            "result": result.get("status", "unknown"),
        })
        return True, detail, _ms_since(t0)

    return False, f"bus age {int(age_sec)}s (fresh)", _ms_since(t0)


def _reflex_cash_idle(bus, mesh, state):
    """PRIORITY 8: Cash idle > 30 min while opportunities exist -> deploy."""
    t0 = time.time()
    engines = bus.get("engines", {})

    # Check each platform for idle cash
    turbo = engines.get("TURBO_TRADER", {}).get("properties", {})
    alpaca = engines.get("ALPACA_TRADER", {}).get("properties", {})

    kalshi_balance = turbo.get("balance", 0) or 0
    kalshi_opps = turbo.get("daily_opps", 0) or 0
    alpaca_cash = alpaca.get("cash_available", 0) or 0
    alpaca_opps = alpaca.get("opportunities_found", 0) or 0

    # Track when we first saw idle cash
    idle_key = "cash_idle_since"
    now = datetime.now(timezone.utc)

    has_idle_cash = False
    platform = None

    if kalshi_balance > 0.50 and kalshi_opps > 0:
        has_idle_cash = True
        platform = "kalshi"
    elif alpaca_cash > 1.00 and alpaca_opps > 0:
        has_idle_cash = True
        platform = "alpaca"

    if has_idle_cash:
        idle_since = state.get(idle_key)
        if not idle_since:
            state[idle_key] = _now_iso()
            return False, f"cash idle on {platform}, starting timer", _ms_since(t0)

        try:
            idle_dt = datetime.fromisoformat(idle_since.replace("Z", "+00:00"))
            idle_sec = (now - idle_dt).total_seconds()
        except Exception:
            idle_sec = 0

        if idle_sec >= 1800:  # 30 minutes
            target = "TURBO_TRADER" if platform == "kalshi" else "ALPACA_TRADER"
            detail = f"Cash idle {int(idle_sec)}s on {platform} with opps -- deploying via {target}"
            result = _run_engine_safe(target)
            state.pop(idle_key, None)  # Reset timer

            _emit_to_bus("REFLEX_ARC", {
                "action": "IDLE_CASH_DEPLOY",
                "platform": platform,
                "idle_seconds": int(idle_sec),
                "target_engine": target,
                "result": result.get("status", "unknown"),
            })
            return True, detail, _ms_since(t0)

        remain = int(1800 - idle_sec)
        return False, f"cash idle on {platform} ({int(idle_sec)}s, {remain}s to trigger)", _ms_since(t0)
    else:
        state.pop(idle_key, None)
        return False, "no idle cash with opportunities", _ms_since(t0)


def _reflex_self_funding(bus, mesh, state):
    """PRIORITY 9: AI costs exceed trading profits -> switch to local models."""
    t0 = time.time()
    engines = bus.get("engines", {})

    # Read revenue data if available
    revenue = engines.get("TRADING_WIRE", {}).get("properties", {})
    ai_costs = revenue.get("ai_costs_24h", 0) or 0
    trading_profits = revenue.get("trading_profits_24h", 0) or 0

    # Also check growth tracker
    if not ai_costs and not trading_profits:
        return False, "no cost/profit data available yet", _ms_since(t0)

    if ai_costs > 0 and trading_profits > 0 and ai_costs > trading_profits:
        detail = (f"AI costs ${ai_costs:.2f} > trading profits ${trading_profits:.2f} -- "
                  f"ALERT: switch to local models recommended")
        _emit_to_bus("REFLEX_ARC", {
            "action": "SELF_FUNDING_ALERT",
            "ai_costs_24h": ai_costs,
            "trading_profits_24h": trading_profits,
            "ratio": round(ai_costs / max(trading_profits, 0.01), 2),
            "recommendation": "switch_to_local_models",
        })
        return True, detail, _ms_since(t0)

    if trading_profits > 0:
        ratio = round(ai_costs / max(trading_profits, 0.01), 2)
        return False, f"AI cost ratio: {ratio}x (sustainable)", _ms_since(t0)

    return False, "insufficient data for cost analysis", _ms_since(t0)


def _reflex_growth_stall(bus, mesh, state):
    """PRIORITY 10: PROPRIOCEPTION reports LOW evolution or no new engines in 24h -> alert."""
    t0 = time.time()
    engines = bus.get("engines", {})
    proprio = engines.get("PROPRIOCEPTION", {}).get("properties", {})

    # Check 1: evolution_label == "LOW"
    evo_label = proprio.get("evolution_label", "")
    evo_low = evo_label == "LOW"

    # Check 2: engine count hasn't increased in 24h
    # Compare current engine_count to what we saw last time
    current_engines = proprio.get("engine_count", 0)
    prev_engines = state.get("prev_engine_count", 0)
    prev_engine_ts = state.get("prev_engine_count_ts", "")

    no_growth_24h = False
    if current_engines > 0 and prev_engines > 0 and current_engines <= prev_engines:
        if prev_engine_ts:
            try:
                prev_dt = datetime.fromisoformat(prev_engine_ts.replace("Z", "+00:00"))
                elapsed = (datetime.now(timezone.utc) - prev_dt).total_seconds()
                no_growth_24h = elapsed >= 86400  # 24 hours
            except Exception:
                pass

    # Track engine count for next cycle
    if current_engines > 0:
        if current_engines > prev_engines or not prev_engine_ts:
            # Engine count increased or first observation -- reset timer
            state["prev_engine_count"] = current_engines
            state["prev_engine_count_ts"] = _now_iso()
        # else: keep the old timestamp to measure stall duration

    if evo_low or no_growth_24h:
        reasons = []
        if evo_low:
            reasons.append(f"evolution_label=LOW")
        if no_growth_24h:
            reasons.append(f"engine_count={current_engines} unchanged 24h+")
        reason_str = " + ".join(reasons)

        detail = f"GROWTH STALL: {reason_str} -- system needs to grow faster"
        _emit_to_bus("REFLEX_ARC", {
            "action": "GROWTH_STALL_ALERT",
            "evolution_label": evo_label,
            "engine_count": current_engines,
            "no_growth_24h": no_growth_24h,
            "reasons": reasons,
        })
        return True, detail, _ms_since(t0)

    return False, f"growth OK (evo={evo_label}, engines={current_engines})", _ms_since(t0)


def _reflex_regime_shift(bus, mesh, state):
    """PRIORITY 5: GLOBAL_MARKETS regime changes -> adjust trading strategy.

    Reads GLOBAL_MARKETS state from the bus. When regime transitions
    (risk-on -> risk-off, or risk-off -> risk-on), immediately:
    - Emit alert to bus so all engines see the shift
    - Trigger AUTO_DEPOSIT to rebalance capital split
    - Trigger appropriate trader (TURBO for risk-off hedging, ALPACA for risk-on)

    This reflex gives SolarPunk a sub-second reaction to global mood changes.
    """
    t0 = time.time()
    engines = bus.get("engines", {})

    # Read GLOBAL_MARKETS from bus
    gm = engines.get("GLOBAL_MARKETS", {}).get("properties", {})
    current_regime = gm.get("regime", "")

    # Also try direct file read if bus doesn't have it yet
    if not current_regime:
        gm_file = DATA / "global_markets_state.json"
        gm_data = _load(gm_file)
        current_regime = gm_data.get("cross_market", {}).get("regime", "")

    if not current_regime:
        return False, "no regime data available yet", _ms_since(t0)

    prev_regime = state.get("prev_regime", "")

    # Detect transition
    if prev_regime and current_regime != prev_regime:
        detail = (f"REGIME SHIFT: {prev_regime} -> {current_regime} "
                  f"-- rebalancing strategy")

        # Determine action based on new regime
        if current_regime == "RISK_OFF":
            # Risk-off: prioritize prediction markets (hedging), reduce equities
            target = "TURBO_TRADER"
            action = "SHIFT_TO_HEDGING"
        elif current_regime == "RISK_ON":
            # Risk-on: prioritize equities and growth assets
            target = "ALPACA_TRADER"
            action = "SHIFT_TO_GROWTH"
        else:
            # Neutral: rebalance to default split
            target = "AUTO_DEPOSIT"
            action = "REBALANCE_NEUTRAL"

        _emit_to_bus("REFLEX_ARC", {
            "action": action,
            "prev_regime": prev_regime,
            "new_regime": current_regime,
            "target_engine": target,
            "reflex": "REGIME_SHIFT",
        })

        # Trigger rebalance
        _run_engine_safe("AUTO_DEPOSIT")
        # Also trigger the directional trader
        if target != "AUTO_DEPOSIT":
            _run_engine_safe(target)

        # Save new regime for next comparison
        state["prev_regime"] = current_regime
        return True, detail, _ms_since(t0)

    # No transition -- just track current regime
    state["prev_regime"] = current_regime
    return False, f"regime stable ({current_regime})", _ms_since(t0)


def _reflex_metabolism_alert(bus, mesh, state):
    """PRIORITY 8: Ecosystem health drops below threshold -> investigate.

    Reads METABOLISM_LOOP from the bus. When ecosystem_health drops
    below 30% (critical) or drops by >20% since last check (rapid decline),
    triggers METABOLISM_LOOP refresh and alerts via bus.

    This reflex prevents the SolarPunk ecosystem from degrading silently.
    """
    t0 = time.time()
    engines = bus.get("engines", {})

    # Read metabolism from bus
    metab = engines.get("METABOLISM_LOOP", {}).get("properties", {})
    health = metab.get("ecosystem_health", -1)

    # Also try direct file read
    if health < 0:
        metab_file = DATA / "metabolism_state.json"
        metab_data = _load(metab_file)
        health = metab_data.get("ecosystem_health", -1)

    if health < 0:
        return False, "no ecosystem health data yet", _ms_since(t0)

    prev_health = state.get("prev_ecosystem_health", health)
    health_drop = prev_health - health

    triggered = False
    reasons = []

    # Check 1: Absolute threshold -- health below 30% is critical
    if health < 30:
        reasons.append(f"health={health}% (CRITICAL, below 30%)")
        triggered = True

    # Check 2: Rapid decline -- >20% drop since last check
    if health_drop > 20:
        reasons.append(f"rapid decline: {prev_health}% -> {health}% (drop={health_drop}%)")
        triggered = True

    # Check 3: Self-funding ratio collapsed
    self_funding = metab.get("self_funding_ratio", 1.0)
    if self_funding < 0.5 and self_funding > 0:
        reasons.append(f"self_funding_ratio={self_funding} (below 0.5)")
        triggered = True

    # Check 4: Circuit broken (metabolism loop disconnected)
    circuit = metab.get("circuit_status", "")
    if circuit == "BROKEN":
        reasons.append("metabolism circuit BROKEN")
        triggered = True

    # Track health for next cycle
    state["prev_ecosystem_health"] = health

    if triggered:
        reason_str = " + ".join(reasons)
        detail = f"METABOLISM ALERT: {reason_str}"

        _emit_to_bus("REFLEX_ARC", {
            "action": "METABOLISM_ALERT",
            "ecosystem_health": health,
            "prev_health": prev_health,
            "health_drop": round(health_drop, 1),
            "self_funding_ratio": self_funding,
            "circuit_status": circuit,
            "reasons": reasons,
            "reflex": "METABOLISM_ALERT",
        })

        # Re-run metabolism loop to refresh readings
        _run_engine_safe("METABOLISM_LOOP")
        return True, detail, _ms_since(t0)

    return False, f"ecosystem healthy ({health}%, delta={health_drop:+.1f}%)", _ms_since(t0)


# ===========================================================================
# Reflex dispatch table (maps IDs to functions)
# ===========================================================================
REFLEX_FNS = {
    "THERMAL_DANGER":     _reflex_thermal_danger,
    "ENGINE_CRASH":       _reflex_engine_crash,
    "DEPOSIT_DETECTED":   _reflex_deposit_detected,
    "SETTLEMENT_SPIKE":   _reflex_settlement_spike,
    "MARKET_OPEN":        _reflex_market_open,
    "ARBITRAGE_WINDOW":   _reflex_arbitrage_window,
    "CONVERGENCE_ALERT":  _reflex_convergence_alert,
    "STALE_BUS":          _reflex_stale_bus,
    "CASH_IDLE":          _reflex_cash_idle,
    "SELF_FUNDING_ALERT": _reflex_self_funding,
    "GROWTH_STALL":       _reflex_growth_stall,
    "REGIME_SHIFT":       _reflex_regime_shift,
    "METABOLISM_ALERT":   _reflex_metabolism_alert,
}


# ===========================================================================
# MAIN: run()
# ===========================================================================
def run():
    """
    Evaluate all reflexes in priority order. Fire those that trigger.

    Returns state dict with reflex results, timing, and summary.
    """
    print("=" * 60)
    print("  REFLEX_ARC -- Fast-path decision engine")
    print("  Bypassing AI. Pure reflex. Millisecond response.")
    print("=" * 60)

    arc_start = time.time()

    # 1. Read inputs
    bus = _read_bus()
    mesh = _read_mesh()
    state = _load(STATE_FILE, {
        "last_fired": {},
        "prev_balances": {},
        "prev_settlements_24h": 0,
        "prev_market_open": False,
        "restart_attempts": {},
        "fire_counts": {},
        "total_checks": 0,
        "total_fires": 0,
    })

    # 2. Evaluate ALL reflexes in priority order
    checked = 0
    fired = 0
    results = []

    for reflex_def in REFLEX_REGISTRY:
        rid = reflex_def["id"]
        fn = REFLEX_FNS.get(rid)
        if not fn:
            continue

        checked += 1

        # Cooldown check (THERMAL_DANGER and ENGINE_CRASH bypass cooldown)
        if rid not in ("THERMAL_DANGER", "ENGINE_CRASH"):
            if not _check_cooldown(rid, state):
                results.append({
                    "reflex": rid,
                    "triggered": False,
                    "detail": "cooldown active",
                    "response_ms": 0,
                })
                print(f"  [{rid}] COOLDOWN (skipped)")
                continue

        # Execute reflex
        try:
            triggered, detail, response_ms = fn(bus, mesh, state)
        except Exception as e:
            triggered, detail, response_ms = False, f"REFLEX ERROR: {e}", 0

        results.append({
            "reflex": rid,
            "triggered": triggered,
            "detail": detail,
            "response_ms": response_ms,
        })

        if triggered:
            fired += 1
            _mark_fired(rid, state)
            _log_reflex(rid, True, detail, response_ms)
            state["fire_counts"] = state.get("fire_counts", {})
            state["fire_counts"][rid] = state["fire_counts"].get(rid, 0) + 1
            print(f"  [{rid}] ** FIRED ** ({response_ms}ms) -- {detail[:80]}")
        else:
            print(f"  [{rid}] quiet ({response_ms}ms) -- {detail[:60]}")

    # 3. Update state transitions for next cycle
    engines = bus.get("engines", {})
    turbo_props = engines.get("TURBO_TRADER", {}).get("properties", {})
    alpaca_props = engines.get("ALPACA_TRADER", {}).get("properties", {})

    state["prev_balances"] = {
        "kalshi": turbo_props.get("balance", 0) or 0,
        "alpaca": alpaca_props.get("portfolio_value", 0) or 0,
    }
    state["prev_settlements_24h"] = turbo_props.get("settlements_24h", 0) or 0
    state["prev_market_open"] = alpaca_props.get("market_open", False)

    # Reset restart attempts each cycle (allow retry next cycle)
    state["restart_attempts"] = {}

    # 4. Update counters
    state["total_checks"] = state.get("total_checks", 0) + checked
    state["total_fires"] = state.get("total_fires", 0) + fired

    # 5. Build final state
    arc_ms = _ms_since(arc_start)
    state["last_run"] = _now_iso()
    state["last_cycle"] = {
        "timestamp": _now_iso(),
        "checked": checked,
        "fired": fired,
        "arc_response_ms": arc_ms,
        "results": results,
    }
    state["status"] = "active"
    state["protocol"] = "reflex-arc-v1"
    state["ethics"] = "99% mutual aid / 1% node fuel"

    # 6. Save state
    _save(STATE_FILE, state)

    # 7. Emit to SYNAPTIC_BUS
    _emit_to_bus("REFLEX_ARC", {
        "status": "active",
        "last_run": state["last_run"],
        "checked": checked,
        "fired": fired,
        "arc_response_ms": arc_ms,
        "total_fires_lifetime": state["total_fires"],
        "fire_counts": state.get("fire_counts", {}),
    })

    # 8. Summary
    fire_rate = round(fired / max(checked, 1) * 100, 1)
    print(f"\n{'=' * 60}")
    print(f"  REFLEX_ARC COMPLETE")
    print(f"  Checked: {checked} | Fired: {fired} | Rate: {fire_rate}%")
    print(f"  Total arc time: {arc_ms}ms")
    print(f"  Lifetime: {state['total_checks']} checks, {state['total_fires']} fires")
    print(f"  Ethics: 99% mutual aid / 1% node fuel")
    print(f"{'=' * 60}")

    return state


if __name__ == "__main__":
    run()
