#!/usr/bin/env python3
"""
SETTLEMENT_WATCHER.py -- Detect Kalshi settlements, redeploy capital instantly
==============================================================================
v1 (2026-04-06): Cash sitting idle after settlement is compounding at 0%.

THE PROBLEM:
  Kalshi positions settle (gas prices, S&P brackets, weather). Cash floods
  back into available balance. Nothing detects this. Nothing redeploys it.
  Every minute that cash sits idle is a minute of zero yield.

THE SOLUTION:
  1. Poll balance every cycle (< 2 seconds total)
  2. Compare to last known balance
  3. If balance increased by > $0.25 -> settlement detected
  4. Emit DEPOSIT_DETECTED to SYNAPTIC_BUS (every engine sees it)
  5. Read CROSS_POLLINATOR for optimal platform split
  6. If Kalshi should keep the cash -> trigger TURBO_TRADER
  7. If Alpaca is the better home -> log recommendation
  8. Update compound_tracker with new balance snapshot

SPEED:  < 2 seconds. Two API calls (balance + settlements), local file I/O.
WEIGHT: ~220 lines. Zero AI calls. Pure arithmetic.

Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)
Called by: NERVE_LOOP Phase 0.5 (before TURBO), OMNIBUS
Reads:  Kalshi API (balance, settlements), cross_pollinator_state.json
Writes: data/settlement_watcher_state.json, data/compound_tracker.json
"""

import json
import time
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA = Path("data")
DATA.mkdir(exist_ok=True)

STATE_FILE = DATA / "settlement_watcher_state.json"
COMPOUND_FILE = DATA / "compound_tracker.json"
XPOL_FILE = DATA / "cross_pollinator_state.json"
TURBO_STATE_FILE = DATA / "turbo_trader_state.json"

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
SETTLEMENT_THRESHOLD = 0.25   # Minimum balance increase to count as settlement ($)
KALSHI_KEEP_THRESHOLD = 0.60  # If CROSS_POLLINATOR says > 60% stays on Kalshi, trade it
MIN_TRADE_BALANCE = 0.50      # Don't bother trading if balance under 50 cents


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8")


def _import_turbo():
    """Import signing functions from TURBO_TRADER (no code duplication)."""
    mycelium_dir = str(Path(__file__).parent)
    if mycelium_dir not in sys.path:
        sys.path.insert(0, mycelium_dir)
    try:
        from TURBO_TRADER import _sign_and_fetch, _load_kalshi_auth
        return _sign_and_fetch, _load_kalshi_auth
    except ImportError as e:
        print(f"  [SETTLE] Cannot import TURBO_TRADER: {e}")
        return None, None


def _emit_to_bus(properties):
    """Broadcast state to SYNAPTIC_BUS. Graceful if bus unavailable."""
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_batch("SETTLEMENT_WATCHER", properties, silent=False)
    except Exception:
        pass  # Bus not available -- degrade gracefully


def _emit_event(key, value):
    """Emit a single event to the bus."""
    try:
        emit_batch("SETTLEMENT_WATCHER", {key: value}, silent=False)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Core: Fetch balance and settlements from Kalshi
# ---------------------------------------------------------------------------
def _fetch_balance(sign_fn, api_key, pem_data):
    """Get current Kalshi balance in dollars."""
    resp = sign_fn("/portfolio/balance", api_key, pem_data, method="GET")
    if resp and "balance" in resp:
        return round(resp["balance"] / 100.0, 2)  # cents -> dollars
    return None


def _fetch_settlements(sign_fn, api_key, pem_data, limit=20):
    """Get recent settlements."""
    resp = sign_fn(f"/portfolio/settlements?limit={limit}", api_key, pem_data, method="GET")
    if resp and "settlements" in resp:
        return resp["settlements"]
    return []


# ---------------------------------------------------------------------------
# Core: Detect settlement and decide redeployment
# ---------------------------------------------------------------------------
def _get_last_known_balance():
    """Read last known balance from our state or turbo_trader_state."""
    state = _load(STATE_FILE)
    if state.get("last_balance") is not None:
        return state["last_balance"]
    # Fall back to turbo_trader_state
    turbo = _load(TURBO_STATE_FILE)
    return turbo.get("balance", turbo.get("last_known_balance", 0)) or 0


def _get_cross_pollinator_split():
    """
    Read CROSS_POLLINATOR state to determine what % should stay on Kalshi.

    Returns (kalshi_pct, alpaca_pct) as floats 0.0-1.0.
    Default: 70/30 Kalshi-heavy (prediction markets are the compounding engine).
    """
    xpol = _load(XPOL_FILE)
    breakdown = xpol.get("platform_breakdown", {})
    kalshi_val = breakdown.get("kalshi", {}).get("total_value", 0) or 0
    alpaca_val = breakdown.get("alpaca", {}).get("total_value", 0) or 0
    total = kalshi_val + alpaca_val

    if total <= 0:
        return 0.70, 0.30  # Default: Kalshi-heavy

    kalshi_pct = kalshi_val / total
    alpaca_pct = alpaca_val / total

    # Bias toward the platform with more opportunities
    best = xpol.get("best_opportunity_platform", "kalshi")
    if best == "kalshi":
        kalshi_pct = max(kalshi_pct, 0.60)
        alpaca_pct = 1.0 - kalshi_pct
    elif best == "alpaca":
        alpaca_pct = max(alpaca_pct, 0.40)
        kalshi_pct = 1.0 - alpaca_pct

    return round(kalshi_pct, 2), round(alpaca_pct, 2)


def _update_compound_tracker(new_balance, settlement_amount):
    """Update compound_tracker.json with new balance snapshot."""
    tracker = _load(COMPOUND_FILE, {
        "compound_cycles": 0,
        "peak_balance": 0,
        "snapshots": [],
    })

    now = datetime.now(timezone.utc).isoformat()
    tracker["compound_cycles"] = tracker.get("compound_cycles", 0) + 1
    if new_balance > tracker.get("peak_balance", 0):
        tracker["peak_balance"] = new_balance
    tracker["last_settlement"] = now
    tracker["last_settlement_amount"] = settlement_amount

    snapshots = tracker.get("snapshots", [])
    snapshots.append({
        "timestamp": now,
        "balance": new_balance,
        "settlement_amount": settlement_amount,
        "type": "settlement_detected",
    })
    # Keep last 100 snapshots
    if len(snapshots) > 100:
        snapshots = snapshots[-100:]
    tracker["snapshots"] = snapshots

    _save(COMPOUND_FILE, tracker)
    return tracker


# ---------------------------------------------------------------------------
# Main run
# ---------------------------------------------------------------------------
def run():
    """
    Settlement watch cycle:
      1. Fetch balance from Kalshi API
      2. Compare to last known balance
      3. If settlement detected -> redeploy capital
      4. Save state, emit to bus

    Returns state dict. Total runtime target: < 2 seconds.
    """
    t0 = time.time()
    now = datetime.now(timezone.utc).isoformat()

    print("[SETTLEMENT_WATCHER] Scanning for settled positions...")

    # --- Import signing from TURBO_TRADER ---
    sign_fn, load_auth = _import_turbo()
    if not sign_fn or not load_auth:
        print("  [SETTLE] TURBO_TRADER import failed -- cannot check Kalshi")
        state = {
            "timestamp": now, "status": "error",
            "error": "turbo_trader_import_failed",
            "elapsed": round(time.time() - t0, 2),
        }
        _save(STATE_FILE, state)
        return state

    # --- Load Kalshi credentials ---
    api_key, pem_data = load_auth()
    if not api_key or not pem_data:
        print("  [SETTLE] No Kalshi credentials -- skipping")
        state = {
            "timestamp": now, "status": "no_credentials",
            "elapsed": round(time.time() - t0, 2),
        }
        _save(STATE_FILE, state)
        return state

    # --- Fetch current balance ---
    balance = _fetch_balance(sign_fn, api_key, pem_data)
    if balance is None:
        print("  [SETTLE] Balance fetch failed")
        state = {
            "timestamp": now, "status": "api_error",
            "error": "balance_fetch_failed",
            "elapsed": round(time.time() - t0, 2),
        }
        _save(STATE_FILE, state)
        _emit_to_bus({"status": "api_error"})
        return state

    # --- Fetch recent settlements ---
    settlements = _fetch_settlements(sign_fn, api_key, pem_data)
    settlement_count = len(settlements)
    recent_revenue_cents = sum(s.get("revenue", 0) for s in settlements[:5])
    recent_revenue = round(recent_revenue_cents / 100.0, 2)

    # --- Compare to last known balance ---
    last_balance = _get_last_known_balance()
    delta = round(balance - last_balance, 2)
    settlement_detected = delta > SETTLEMENT_THRESHOLD

    print(f"  [SETTLE] Balance: ${balance:.2f} (was ${last_balance:.2f}, delta ${delta:+.2f})")
    print(f"  [SETTLE] Recent settlements: {settlement_count} (revenue: ${recent_revenue:.2f})")

    # --- Settlement detected! ---
    action_taken = "none"
    kalshi_pct, alpaca_pct = 0.70, 0.30
    turbo_triggered = False

    if settlement_detected:
        print(f"  [SETTLE] ** SETTLEMENT DETECTED ** +${delta:.2f}")

        # Get cross-pollinator recommendation
        kalshi_pct, alpaca_pct = _get_cross_pollinator_split()
        print(f"  [SETTLE] Cross-pollinator split: Kalshi {kalshi_pct*100:.0f}% / Alpaca {alpaca_pct*100:.0f}%")

        # Emit to bus immediately -- every engine sees this
        _emit_event("DEPOSIT_DETECTED", {
            "amount": delta,
            "new_balance": balance,
            "source": "settlement",
            "timestamp": now,
        })

        # Update compound tracker
        _update_compound_tracker(balance, delta)

        # Decide where to deploy
        if kalshi_pct >= KALSHI_KEEP_THRESHOLD and balance >= MIN_TRADE_BALANCE:
            # Keep on Kalshi -- trigger TURBO_TRADER
            print(f"  [SETTLE] Deploying ${balance:.2f} via TURBO_TRADER...")
            try:
                mycelium_dir = str(Path(__file__).parent)
                if mycelium_dir not in sys.path:
                    sys.path.insert(0, mycelium_dir)
                import TURBO_TRADER
                TURBO_TRADER.run()
                turbo_triggered = True
                action_taken = "turbo_trader_triggered"
                print(f"  [SETTLE] TURBO_TRADER completed -- capital redeployed")
            except Exception as e:
                print(f"  [SETTLE] TURBO_TRADER failed: {e}")
                action_taken = "turbo_trigger_failed"
        else:
            # Significant portion should go to Alpaca
            kalshi_amount = round(balance * kalshi_pct, 2)
            alpaca_amount = round(balance * alpaca_pct, 2)
            print(f"  [SETTLE] Recommendation: ${kalshi_amount:.2f} stays Kalshi, "
                  f"${alpaca_amount:.2f} to Alpaca (manual transfer)")
            action_taken = "alpaca_transfer_recommended"

            # Still trigger TURBO for the Kalshi portion if above minimum
            if kalshi_amount >= MIN_TRADE_BALANCE:
                try:
                    TURBO_TRADER.run()
                    turbo_triggered = True
                    action_taken = "split_deploy"
                except Exception as e:
                    print(f"  [SETTLE] TURBO partial deploy failed: {e}")
    else:
        print(f"  [SETTLE] No settlement detected (threshold: ${SETTLEMENT_THRESHOLD:.2f})")
        action_taken = "no_settlement"

    # --- Build state ---
    elapsed = round(time.time() - t0, 2)
    state = {
        "timestamp": now,
        "protocol": "settlement-watcher-v1",
        "engine": "SETTLEMENT_WATCHER",
        "status": "settlement_detected" if settlement_detected else "watching",
        "balance": balance,
        "last_balance": last_balance,
        "delta": delta,
        "settlement_detected": settlement_detected,
        "settlement_count": settlement_count,
        "recent_revenue": recent_revenue,
        "action_taken": action_taken,
        "turbo_triggered": turbo_triggered,
        "platform_split": {
            "kalshi_pct": kalshi_pct,
            "alpaca_pct": alpaca_pct,
        },
        "elapsed": elapsed,
    }

    # Add nervous system awareness
    _homeo = _load(DATA / "homeostasis_state.json", {})
    _cortex = _load(DATA / "neural_cortex_state.json", {})
    state["nervous_system"] = {
        "equilibrium": _homeo.get("equilibrium", 0) if _homeo else 0,
        "brain_confidence": _cortex.get("decision_confidence", 0) if _cortex else 0,
        "brain_risk": _cortex.get("strategy", {}).get("risk_posture", "moderate") if _cortex else "moderate",
    }

    _save(STATE_FILE, state)

    # --- Emit final state to bus ---
    _emit_to_bus({
        "status": state["status"],
        "balance": balance,
        "delta": delta,
        "settlement_detected": settlement_detected,
        "action_taken": action_taken,
        "turbo_triggered": turbo_triggered,
        "platform": "kalshi",
        "elapsed": elapsed,
        "equilibrium": state["nervous_system"]["equilibrium"],
        "brain_confidence": state["nervous_system"]["brain_confidence"],
    })

    # --- Summary ---
    if settlement_detected:
        print(f"  [SETTLE] Capital redeployed in {elapsed}s. "
              f"Action: {action_taken}. Balance: ${balance:.2f}")
    else:
        print(f"  [SETTLE] All quiet. Balance: ${balance:.2f}. ({elapsed}s)")

    return state


if __name__ == "__main__":
    run()
