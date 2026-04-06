#!/usr/bin/env python3
"""
EXECUTIVE_FUNCTION.py -- Motor cortex of the SolarPunk nervous system
======================================================================
v1 (2026-04-06): The motor cortex. Executes what NEURAL_CORTEX decides.

THE BIOLOGY:
  NEURAL_CORTEX is the prefrontal cortex -- it THINKS and DECIDES.
  EXECUTIVE_FUNCTION is the motor cortex -- it ACTS on those decisions.

  Without this engine, the brain thinks but the body can't move.
  NEURAL_CORTEX outputs a top_action with {description, engine, urgency}
  and system_health.recommendations with CRITICAL warnings. This engine
  reads both and actually fires the target engines.

THE EXECUTION PIPELINE:
  1. READ:    Load NEURAL_CORTEX state (top_action + recommendations)
  2. CHECK:   Urgency threshold, cooldowns, protected engine list
  3. EXECUTE: Import and run the target engine (max 1 per cycle)
  4. TRIAGE:  Scan recommendations for CRITICAL items, attempt fixes
  5. TRACK:   Log execution history, success/failure stats
  6. SAVE:    Write state to data/executive_function_state.json
  7. EMIT:    Broadcast to SYNAPTIC_BUS

SAFETY RAILS:
  - Maximum 1 engine execution per cycle (prevent cascade)
  - 10-minute cooldown per target engine (prevent hammer)
  - NEVER execute NERVE_LOOP, EXECUTIVE_FUNCTION, or OMNIBUS
  - Urgency < 50 = log only, do not execute
  - Track success/failure rates to detect chronic failures

Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)
Called by: NERVE_LOOP, OMNIBUS, AUTONOMIC_NERVE
Reads: data/neural_cortex_state.json, data/synaptic_bus.json
Writes: data/executive_function_state.json
"""

import json
import time
import importlib
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA = Path("data")
DATA.mkdir(exist_ok=True)

STATE_FILE   = DATA / "executive_function_state.json"
CORTEX_FILE  = DATA / "neural_cortex_state.json"
BUS_FILE     = DATA / "synaptic_bus.json"

# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------
URGENCY_THRESHOLD  = 50          # Below this: log but don't act
COOLDOWN_MINUTES   = 10          # Per-engine cooldown to prevent hammer
MAX_HISTORY        = 100         # Rolling execution history cap
MAX_EXEC_TIME_SEC  = 120         # Kill execution after 2 minutes

# Engines that must NEVER be auto-executed
PROTECTED_ENGINES = [
    "NERVE_LOOP",               # Too heavy for reactive execution
    "EXECUTIVE_FUNCTION",       # Prevent recursion
    "OMNIBUS",                  # Orchestrator -- not a leaf engine
]

# Engines whose CRITICAL recommendations map to corrective engines
CRITICAL_REMEDIES = {
    "restart dead engines":        "REFLEX_ARC",
    "check signal sources":        "SIGNAL_MESH",
    "prioritize revenue":          "FLYWHEEL",
    "revenue generation":          "FLYWHEEL",
    "engines are not emitting":    "PROPRIOCEPTION",
    "close the feedback loop":     "METABOLISM_LOOP",
    "I/O bottleneck":              "PROPRIOCEPTION",
}


# ---------------------------------------------------------------------------
# Core I/O
# ---------------------------------------------------------------------------
def _load(path, default=None):
    """Read JSON file with graceful fallback."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _save(path, data):
    """Write JSON file."""
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _now_dt():
    return datetime.now(timezone.utc)


def _ms_since(start):
    """Milliseconds elapsed since start time."""
    return round((time.time() - start) * 1000, 1)


def _parse_iso(ts_str):
    """Parse an ISO timestamp string to datetime, or None."""
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Cooldown management
# ---------------------------------------------------------------------------
def _is_cooled_down(cooldowns, engine_name):
    """Check if an engine has cleared its cooldown window."""
    expiry_str = cooldowns.get(engine_name)
    if not expiry_str:
        return True  # Never executed -- no cooldown
    expiry = _parse_iso(expiry_str)
    if expiry is None:
        return True
    return _now_dt() >= expiry


def _set_cooldown(cooldowns, engine_name):
    """Set a cooldown expiry for an engine."""
    expiry = _now_dt() + timedelta(minutes=COOLDOWN_MINUTES)
    cooldowns[engine_name] = expiry.isoformat()


def _clean_expired_cooldowns(cooldowns):
    """Remove cooldowns that have already expired."""
    now = _now_dt()
    expired = [
        eng for eng, ts in cooldowns.items()
        if _parse_iso(ts) and _parse_iso(ts) < now
    ]
    for eng in expired:
        del cooldowns[eng]


# ---------------------------------------------------------------------------
# Engine execution
# ---------------------------------------------------------------------------
def _execute_engine(engine_name):
    """
    Import and run a target engine by name.

    Returns (success: bool, result_summary: str, elapsed_ms: float).
    Uses lazy import via importlib to avoid circular dependencies.
    """
    t0 = time.time()
    try:
        mod = importlib.import_module(engine_name)
        result = mod.run()
        elapsed = _ms_since(t0)

        # Determine success from result
        if isinstance(result, dict):
            status = result.get("status", "unknown")
            summary = f"Engine returned status={status}"
            success = status not in ("error", "failed", "crash")
        elif result is None:
            summary = "Engine returned None (assumed success)"
            success = True
        else:
            summary = f"Engine returned: {str(result)[:200]}"
            success = True

        return success, summary, elapsed

    except Exception as exc:
        elapsed = _ms_since(t0)
        tb = traceback.format_exc()
        # Keep traceback short for state file
        short_tb = tb.strip().split("\n")[-1] if tb else str(exc)
        return False, f"Exception: {short_tb}", elapsed


# ---------------------------------------------------------------------------
# CRITICAL recommendation triage
# ---------------------------------------------------------------------------
def _find_critical_recommendations(recommendations):
    """Extract recommendations containing 'CRITICAL' from the list."""
    if not recommendations:
        return []
    return [r for r in recommendations if "CRITICAL" in r.upper()]


def _map_recommendation_to_engine(recommendation):
    """
    Map a CRITICAL recommendation string to a corrective engine name.
    Returns engine name or None if no known remedy.
    """
    rec_lower = recommendation.lower()
    for keyword, engine in CRITICAL_REMEDIES.items():
        if keyword in rec_lower:
            return engine
    return None


# ---------------------------------------------------------------------------
# Stats tracking
# ---------------------------------------------------------------------------
def _update_stats(stats, engine_name, success):
    """Update execution statistics."""
    stats["total_executions"] = stats.get("total_executions", 0) + 1
    if success:
        stats["successful"] = stats.get("successful", 0) + 1
    else:
        stats["failed"] = stats.get("failed", 0) + 1

    engines_map = stats.get("engines_executed", {})
    engines_map[engine_name] = engines_map.get(engine_name, 0) + 1
    stats["engines_executed"] = engines_map


def _append_history(history, entry):
    """Append to execution history with rolling cap."""
    history.append(entry)
    if len(history) > MAX_HISTORY:
        history[:] = history[-MAX_HISTORY:]


# ---------------------------------------------------------------------------
# Console output
# ---------------------------------------------------------------------------
def _print_summary(state):
    """Print a formatted summary of the executive function output."""
    W = 60
    print()
    print("=" * W)
    print("  EXECUTIVE_FUNCTION -- Motor Cortex Output")
    print("=" * W)

    last = state.get("last_execution", {})
    if last:
        target = last.get("target_engine", "none")
        result = last.get("result", "none")
        urgency = last.get("urgency", 0)
        elapsed = last.get("elapsed_ms", 0)
        trigger = last.get("triggered_by", "?")
        desc = last.get("description", "")

        print(f"\n  LAST EXECUTION:")
        print(f"    Target:        {target}")
        print(f"    Description:   {desc[:50]}")
        print(f"    Urgency:       {urgency}/100")
        print(f"    Result:        {result}")
        print(f"    Elapsed:       {elapsed}ms")
        print(f"    Triggered by:  {trigger}")
    else:
        print(f"\n  LAST EXECUTION:  none (first run or below threshold)")

    # Active cooldowns
    cooldowns = state.get("cooldowns", {})
    active = {k: v for k, v in cooldowns.items() if _parse_iso(v) and _parse_iso(v) > _now_dt()}
    if active:
        print(f"\n  ACTIVE COOLDOWNS: {len(active)}")
        for eng, exp in sorted(active.items()):
            remaining = (_parse_iso(exp) - _now_dt()).total_seconds()
            print(f"    {eng}: {remaining:.0f}s remaining")
    else:
        print(f"\n  ACTIVE COOLDOWNS: none")

    # Stats
    stats = state.get("stats", {})
    total = stats.get("total_executions", 0)
    good = stats.get("successful", 0)
    bad = stats.get("failed", 0)
    rate = f"{(good / total * 100):.0f}%" if total > 0 else "n/a"
    print(f"\n  STATS:")
    print(f"    Total:         {total} executions")
    print(f"    Successful:    {good}")
    print(f"    Failed:        {bad}")
    print(f"    Success rate:  {rate}")

    engines_executed = stats.get("engines_executed", {})
    if engines_executed:
        top3 = sorted(engines_executed.items(), key=lambda x: x[1], reverse=True)[:3]
        top3_str = ", ".join(f"{e}({c})" for e, c in top3)
        print(f"    Top engines:   {top3_str}")

    print(f"\n  ETHICS: {state.get('ethics', '99% mutual aid / 1% node fuel')}")
    print("=" * W)


# ===========================================================================
# MAIN ENTRY POINT
# ===========================================================================
def run():
    """
    Execute the full Executive Function pipeline:
    Read -> Check -> Execute -> Triage -> Track -> Save -> Emit

    Returns the complete executive_function_state dict.

    Ethics: 99% mutual aid / 1% node fuel
    """
    t0 = time.time()

    # ----- Load previous state -----
    prev_state = _load(STATE_FILE)
    cooldowns = prev_state.get("cooldowns", {})
    history = prev_state.get("execution_history", [])
    stats = prev_state.get("stats", {
        "total_executions": 0,
        "successful": 0,
        "failed": 0,
        "engines_executed": {},
    })

    _clean_expired_cooldowns(cooldowns)

    # ----- PHASE 1: READ NEURAL_CORTEX -----
    cortex = _load(CORTEX_FILE)
    strategy = cortex.get("strategy", {})
    top_action = strategy.get("top_action", {})
    health = cortex.get("system_health", {})
    recommendations = health.get("recommendations", [])

    target_engine = top_action.get("engine", "")
    urgency = top_action.get("urgency", 0)
    description = top_action.get("description", "no action specified")

    # ----- PHASE 1b: READ FIRE LEDGER (race prevention with REFLEX_ARC) -----
    fire_ledger = _load(DATA / "fire_ledger.json")
    recently_fired = fire_ledger.get("summary", {}).get("recently_fired_engines", [])

    # ----- PHASE 1c: READ REFLEX_ARC recent fires -----
    reflex_state = _load(DATA / "reflex_arc_state.json")
    reflex_fire_log = reflex_state.get("fire_log", [])
    reflex_recent_engines = set()
    for fire in reflex_fire_log:
        fire_ts = _parse_iso(fire.get("timestamp"))
        if fire_ts and (_now_dt() - fire_ts).total_seconds() < COOLDOWN_MINUTES * 60:
            engine_fired = fire.get("engine_fired", fire.get("action", ""))
            if engine_fired:
                reflex_recent_engines.add(engine_fired)

    # ----- PHASE 2: CHECK execution eligibility -----
    last_execution = {}
    executed_this_cycle = False

    # Determine if top_action should fire
    skip_reason = None
    if not target_engine:
        skip_reason = "no target engine specified"
    elif target_engine in PROTECTED_ENGINES:
        skip_reason = f"{target_engine} is protected (never auto-execute)"
    elif urgency < URGENCY_THRESHOLD:
        skip_reason = f"urgency {urgency} below threshold {URGENCY_THRESHOLD}"
    elif not _is_cooled_down(cooldowns, target_engine):
        skip_reason = f"{target_engine} is on cooldown"
    elif target_engine in reflex_recent_engines:
        skip_reason = f"{target_engine} already fired by REFLEX_ARC recently (race prevention)"
    elif target_engine in recently_fired:
        skip_reason = f"{target_engine} in fire ledger (HOMEOSTASIS race prevention)"

    # ----- PHASE 3: EXECUTE top_action -----
    if skip_reason is None:
        print(f"  [EXEC] Firing {target_engine} (urgency={urgency}): {description}")
        success, summary, elapsed = _execute_engine(target_engine)
        result_str = "success" if success else "failed"

        last_execution = {
            "target_engine": target_engine,
            "description": description,
            "urgency": urgency,
            "result": result_str,
            "detail": summary,
            "elapsed_ms": elapsed,
            "triggered_by": "top_action",
        }

        _set_cooldown(cooldowns, target_engine)
        _update_stats(stats, target_engine, success)
        _append_history(history, {
            "timestamp": _now_iso(),
            "engine": target_engine,
            "urgency": urgency,
            "result": result_str,
            "reason": description,
            "elapsed_ms": elapsed,
        })
        executed_this_cycle = True
    else:
        print(f"  [SKIP] Top action not executed: {skip_reason}")
        last_execution = prev_state.get("last_execution", {})

    # ----- PHASE 4: TRIAGE CRITICAL recommendations -----
    critical_recs = _find_critical_recommendations(recommendations)
    critical_actions = []

    for rec in critical_recs:
        remedy_engine = _map_recommendation_to_engine(rec)
        if remedy_engine is None:
            critical_actions.append({
                "recommendation": rec,
                "action": "no known remedy",
                "engine": None,
            })
            continue

        # Only execute remedy if we haven't already executed this cycle
        if executed_this_cycle:
            critical_actions.append({
                "recommendation": rec,
                "action": "deferred (already executed this cycle)",
                "engine": remedy_engine,
            })
            continue

        if remedy_engine in PROTECTED_ENGINES:
            critical_actions.append({
                "recommendation": rec,
                "action": f"skipped ({remedy_engine} is protected)",
                "engine": remedy_engine,
            })
            continue

        if not _is_cooled_down(cooldowns, remedy_engine):
            critical_actions.append({
                "recommendation": rec,
                "action": f"skipped ({remedy_engine} on cooldown)",
                "engine": remedy_engine,
            })
            continue

        # Execute the corrective engine
        print(f"  [CRIT] Firing {remedy_engine} for: {rec[:60]}")
        success, summary, elapsed = _execute_engine(remedy_engine)
        result_str = "success" if success else "failed"

        critical_actions.append({
            "recommendation": rec,
            "action": f"executed {remedy_engine}: {result_str}",
            "engine": remedy_engine,
        })

        last_execution = {
            "target_engine": remedy_engine,
            "description": f"CRITICAL remedy: {rec[:80]}",
            "urgency": 100,
            "result": result_str,
            "detail": summary,
            "elapsed_ms": elapsed,
            "triggered_by": "critical_recommendation",
        }

        _set_cooldown(cooldowns, remedy_engine)
        _update_stats(stats, remedy_engine, success)
        _append_history(history, {
            "timestamp": _now_iso(),
            "engine": remedy_engine,
            "urgency": 100,
            "result": result_str,
            "reason": f"CRITICAL: {rec[:100]}",
            "elapsed_ms": elapsed,
        })
        executed_this_cycle = True

    total_ms = _ms_since(t0)

    # ----- PHASE 5: BUILD STATE -----
    state = {
        "timestamp": _now_iso(),
        "engine": "EXECUTIVE_FUNCTION",
        "status": "active",
        "last_execution": last_execution,
        "cortex_input": {
            "top_action": top_action,
            "urgency": urgency,
            "skip_reason": skip_reason,
            "critical_count": len(critical_recs),
            "critical_actions": critical_actions,
        },
        "execution_history": history,
        "cooldowns": cooldowns,
        "stats": stats,
        "performance": {
            "total_ms": total_ms,
        },
        "ethics": "99% mutual aid / 1% node fuel",
    }

    # ----- PHASE 6: PRINT SUMMARY -----
    _print_summary(state)
    print(f"\n  [PERF] total={total_ms}ms")

    # ----- PHASE 7: SAVE STATE -----
    _save(STATE_FILE, state)

    # ----- PHASE 8: EMIT TO SYNAPTIC_BUS -----
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_payload = {
            "status": "active",
            "last_target": last_execution.get("target_engine", "none"),
            "last_result": last_execution.get("result", "none"),
            "last_urgency": last_execution.get("urgency", 0),
            "last_trigger": last_execution.get("triggered_by", "none"),
            "skip_reason": skip_reason or "none",
            "critical_count": len(critical_recs),
            "total_executions": stats.get("total_executions", 0),
            "success_rate": round(
                stats["successful"] / max(stats["total_executions"], 1) * 100, 1
            ),
            "active_cooldowns": len([
                k for k, v in cooldowns.items()
                if _parse_iso(v) and _parse_iso(v) > _now_dt()
            ]),
            "total_ms": total_ms,
        }
        emit_batch("EXECUTIVE_FUNCTION", emit_payload, silent=False)
    except Exception:
        pass  # Bus unavailable -- degrade gracefully

    return state


if __name__ == "__main__":
    run()
