#!/usr/bin/env python3
"""
HOMEOSTASIS.py -- Active equilibrium maintenance for the living system
=======================================================================
v2 (2026-04-06): Nervous system integration. Health zones, fire ledger,
                 race prevention, trend detection, equilibrium scoring.

v1: Planetary health check (crisis/NGO focused).
v2: Full nervous system wiring -- reads EVERY health-relevant engine,
    resolves the REFLEX↔EXECUTIVE race condition, tracks health trends.

THE BIOLOGY:
  Homeostasis is how living organisms maintain internal stability despite
  external chaos. Body temperature, blood pressure, pH levels -- all
  regulated by feedback loops that detect deviation and correct it.

  SolarPunk's HOMEOSTASIS does the same thing:
    - Detects which subsystems are degraded (nervous, ecosystem, trading, infra)
    - Prioritizes interventions by severity
    - Resolves the REFLEX↔EXECUTIVE race condition (shared fire ledger)
    - Tracks health trends over time (improving/degrading/stable)
    - Provides a unified equilibrium score

THE RACE CONDITION FIX:
  Before HOMEOSTASIS, both REFLEX_ARC and EXECUTIVE_FUNCTION could fire
  the same engine in the same cycle. HOMEOSTASIS maintains a shared
  "fire ledger" that both can read, preventing duplicate executions.
  Every engine that fires writes to the ledger. Every engine that wants
  to fire checks the ledger first.

READS:
  - neural_cortex_state.json     (brain health recommendations)
  - metabolism_state.json         (ecosystem health, circuit status)
  - executive_function_state.json (execution history, cooldowns)
  - reflex_arc_state.json         (fire data, fire rate)
  - proprioception_state.json     (evolution, coordination, speed)
  - synaptic_bus.json             (engine liveness, connectivity)
  - signal_mesh_state.json        (signal health, source freshness)

WRITES:
  - data/homeostasis_state.json
  - data/fire_ledger.json          (shared REFLEX↔EXECUTIVE race prevention)

EMITS:
  - SYNAPTIC_BUS: health_zones, equilibrium, trend, interventions_count

Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)
Called by: NERVE_LOOP, OMNIBUS, AUTONOMIC_NERVE, task_queue (10 min)
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

STATE_FILE  = DATA / "homeostasis_state.json"
FIRE_LEDGER = DATA / "fire_ledger.json"

# Source files
CORTEX_FILE  = DATA / "neural_cortex_state.json"
METAB_FILE   = DATA / "metabolism_state.json"
EXEC_FILE    = DATA / "executive_function_state.json"
REFLEX_FILE  = DATA / "reflex_arc_state.json"
PROPRIO_FILE = DATA / "proprioception_state.json"
BUS_FILE     = DATA / "synaptic_bus.json"
MESH_FILE    = DATA / "signal_mesh_state.json"

# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------
# Health zone thresholds (0-100)
ZONE_CRITICAL  = 25
ZONE_WARNING   = 50
ZONE_HEALTHY   = 75

# Fire ledger expiry
FIRE_LEDGER_WINDOW_MIN = 15

# Trend detection
TREND_WINDOW = 6

# History caps
MAX_HISTORY = 50
MAX_FIRE_LEDGER = 200


# ---------------------------------------------------------------------------
# Core I/O
# ---------------------------------------------------------------------------
def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _save(path, data):
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _now():
    return datetime.now(timezone.utc)


def _now_iso():
    return _now().isoformat()


def _parse_ts(raw):
    if not raw or not isinstance(raw, str):
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _age_minutes(ts_str, now=None):
    now = now or _now()
    dt = _parse_ts(ts_str)
    if dt is None:
        return float("inf")
    return max(0, (now - dt).total_seconds() / 60)


def _safe_float(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Phase 1: GATHER
# ---------------------------------------------------------------------------
def _gather_all(now):
    return {
        "cortex":  _load(CORTEX_FILE),
        "metab":   _load(METAB_FILE),
        "exec":    _load(EXEC_FILE),
        "reflex":  _load(REFLEX_FILE),
        "proprio": _load(PROPRIO_FILE),
        "bus":     _load(BUS_FILE),
        "mesh":    _load(MESH_FILE),
    }


# ---------------------------------------------------------------------------
# Phase 2: ASSESS health zones (0-100 each)
# ---------------------------------------------------------------------------
def _assess_nervous_system(data, now):
    bus = data["bus"]
    mesh = data["mesh"]

    pulse = bus.get("last_pulse", {})
    alive = pulse.get("alive", 0)
    total = pulse.get("total_registered", max(alive, 1))
    liveness_pct = (alive / max(total, 1)) * 100

    heartbeat = mesh.get("heartbeat", {})
    connectivity = _safe_float(heartbeat.get("neural_connectivity", 0))
    alive_sources = heartbeat.get("alive", 0)
    total_sources = heartbeat.get("total_sources", max(alive_sources, 1))
    source_health = (alive_sources / max(total_sources, 1)) * 100

    convergence = _safe_float(bus.get("convergence", {}).get("sync_score", 0))

    bus_age = _age_minutes(pulse.get("timestamp"), now)
    freshness = max(0, 100 - bus_age * 5)

    score = (
        liveness_pct * 0.30 +
        connectivity * 0.25 +
        source_health * 0.20 +
        convergence * 0.15 +
        freshness * 0.10
    )
    return {
        "score": round(min(100, max(0, score)), 1),
        "liveness_pct": round(liveness_pct, 1),
        "connectivity": round(connectivity, 1),
        "source_health": round(source_health, 1),
        "convergence": round(convergence, 1),
        "freshness": round(freshness, 1),
        "engines_alive": alive,
        "engines_total": total,
    }


def _assess_ecosystem(data, now):
    metab = data["metab"]
    metabolism = metab.get("metabolism", metab)

    eco_health = _safe_float(metabolism.get("ecosystem_health", 0))
    circuit = metabolism.get("circuit_status", "open")
    self_funding = _safe_float(metabolism.get("self_funding_ratio", 0))
    rev_velocity = _safe_float(metabolism.get("revenue_velocity_per_day", 0))

    eco_snap = metab.get("ecosystem_snapshot", {})
    products_live = eco_snap.get("products_live", 0)
    bridges_active = eco_snap.get("bridges_active", 0)

    circuit_bonus = 20 if circuit == "closed" else 0
    funding_score = min(100, self_funding * 50)
    product_score = min(100, products_live * 15)
    bridge_score = min(100, bridges_active * 25)

    score = (
        eco_health * 0.30 +
        circuit_bonus * 0.15 +
        funding_score * 0.20 +
        product_score * 0.15 +
        bridge_score * 0.10 +
        min(100, rev_velocity * 10) * 0.10
    )
    return {
        "score": round(min(100, max(0, score)), 1),
        "ecosystem_health": round(eco_health, 1),
        "circuit_status": circuit,
        "self_funding_ratio": round(self_funding, 3),
        "revenue_velocity_day": round(rev_velocity, 4),
        "products_live": products_live,
        "bridges_active": bridges_active,
    }


def _assess_trading(data, now):
    cortex = data["cortex"]
    strategy = cortex.get("strategy", {})
    intel = cortex.get("intelligence_summary", {})

    confidence = _safe_float(cortex.get("decision_confidence", 0))
    total_capital = _safe_float(intel.get("total_capital_usd", 0))
    regime = intel.get("regime", "unknown")

    bus = data["bus"]
    engines = bus.get("engines", {})
    turbo = engines.get("TURBO_TRADER", {}).get("properties", {})
    alpaca = engines.get("ALPACA_TRADER", {}).get("properties", {})
    turbo_balance = _safe_float(turbo.get("balance", 0))
    alpaca_value = _safe_float(alpaca.get("portfolio_value", alpaca.get("cash", 0)))

    execf = data["exec"]
    stats = execf.get("stats", {})
    total_exec = stats.get("total_executions", 0)
    success_exec = stats.get("successful", 0)
    exec_success_rate = (success_exec / max(total_exec, 1)) * 100

    capital_score = min(100, total_capital * 2)
    confidence_score = confidence
    regime_score = {"risk-on": 80, "RISK_ON": 80, "neutral": 50, "NEUTRAL": 50,
                    "risk-off": 30, "RISK_OFF": 30, "unknown": 40}.get(regime, 40)
    exec_score = exec_success_rate

    score = (
        capital_score * 0.25 +
        confidence_score * 0.25 +
        regime_score * 0.20 +
        exec_score * 0.15 +
        min(100, (turbo_balance + alpaca_value) * 3) * 0.15
    )
    return {
        "score": round(min(100, max(0, score)), 1),
        "total_capital": round(total_capital, 2),
        "confidence": round(confidence, 1),
        "regime": regime,
        "turbo_balance": round(turbo_balance, 2),
        "alpaca_value": round(alpaca_value, 2),
        "exec_success_rate": round(exec_success_rate, 1),
        "total_executions": total_exec,
    }


def _assess_infrastructure(data, now):
    proprio = data["proprio"]

    engine_count = proprio.get("engine_count", 0)
    coordination = _safe_float(proprio.get("coordination_score", 0))
    evolution = proprio.get("evolution_label", "UNKNOWN")

    reflex = data["reflex"]
    last_cycle = reflex.get("last_cycle", {})
    reflex_ms = _safe_float(last_cycle.get("arc_response_ms", 0))

    fastest_interval = _safe_float(proprio.get("fastest_interval_s", 999))

    engine_score = min(100, engine_count / 4)
    coordination_score = coordination
    evolution_score = {"TRANSCENDENT": 100, "SOVEREIGN": 90, "HIGH": 70,
                       "MODERATE": 50, "LOW": 30, "UNKNOWN": 20}.get(evolution, 20)
    reflex_score = max(0, 100 - reflex_ms / 5)
    speed_score = max(0, 100 - fastest_interval)

    score = (
        engine_score * 0.25 +
        coordination_score * 0.25 +
        evolution_score * 0.20 +
        reflex_score * 0.15 +
        speed_score * 0.15
    )
    return {
        "score": round(min(100, max(0, score)), 1),
        "engine_count": engine_count,
        "coordination": round(coordination, 1),
        "evolution_label": evolution,
        "reflex_response_ms": round(reflex_ms, 1),
        "fastest_interval_s": round(fastest_interval, 1),
    }


# ---------------------------------------------------------------------------
# Phase 3: FIRE LEDGER -- Race condition prevention
# ---------------------------------------------------------------------------
def _load_fire_ledger():
    return _load(FIRE_LEDGER, {"entries": [], "summary": {}})


def _update_fire_ledger(ledger, data, now):
    entries = ledger.get("entries", [])
    cutoff = now - timedelta(minutes=FIRE_LEDGER_WINDOW_MIN)

    # Ingest REFLEX_ARC fires
    reflex = data["reflex"]
    fire_log = reflex.get("fire_log", [])
    for fire in fire_log:
        ts = _parse_ts(fire.get("timestamp"))
        if ts and ts > cutoff:
            entry_id = f"reflex:{fire.get('reflex_id', '?')}:{fire.get('timestamp', '')}"
            if not any(e.get("id") == entry_id for e in entries):
                entries.append({
                    "id": entry_id,
                    "source": "REFLEX_ARC",
                    "engine_fired": fire.get("engine_fired", fire.get("action", "unknown")),
                    "reflex_id": fire.get("reflex_id", "?"),
                    "timestamp": fire.get("timestamp", ""),
                    "urgency": fire.get("urgency", 0),
                    "result": fire.get("result", "unknown"),
                })

    # Ingest EXECUTIVE_FUNCTION fires
    execf = data["exec"]
    exec_history = execf.get("execution_history", [])
    for ex in exec_history:
        ts = _parse_ts(ex.get("timestamp"))
        if ts and ts > cutoff:
            entry_id = f"exec:{ex.get('engine', '?')}:{ex.get('timestamp', '')}"
            if not any(e.get("id") == entry_id for e in entries):
                entries.append({
                    "id": entry_id,
                    "source": "EXECUTIVE_FUNCTION",
                    "engine_fired": ex.get("engine", "unknown"),
                    "timestamp": ex.get("timestamp", ""),
                    "urgency": ex.get("urgency", 0),
                    "result": ex.get("result", "unknown"),
                })

    # Prune expired
    entries = [e for e in entries if _age_minutes(e.get("timestamp"), now) < FIRE_LEDGER_WINDOW_MIN]
    if len(entries) > MAX_FIRE_LEDGER:
        entries = entries[-MAX_FIRE_LEDGER:]

    # Summary
    recently_fired_engines = list(set(
        e.get("engine_fired", "") for e in entries if e.get("engine_fired")
    ))
    reflex_fires = [e for e in entries if e.get("source") == "REFLEX_ARC"]
    exec_fires = [e for e in entries if e.get("source") == "EXECUTIVE_FUNCTION"]
    reflex_engines = set(e.get("engine_fired", "") for e in reflex_fires)
    exec_engines = set(e.get("engine_fired", "") for e in exec_fires)
    overlaps = reflex_engines & exec_engines

    summary = {
        "recently_fired_engines": recently_fired_engines,
        "reflex_fire_count": len(reflex_fires),
        "executive_fire_count": len(exec_fires),
        "total_fires_in_window": len(entries),
        "overlap_engines": list(overlaps),
        "overlap_detected": len(overlaps) > 0,
        "window_minutes": FIRE_LEDGER_WINDOW_MIN,
    }

    ledger["entries"] = entries
    ledger["summary"] = summary
    ledger["last_updated"] = _now_iso()
    return ledger


# ---------------------------------------------------------------------------
# Phase 4: INTERVENTIONS
# ---------------------------------------------------------------------------
def _compute_interventions(zones, data, fire_ledger, now):
    interventions = []

    # From NEURAL_CORTEX recommendations
    cortex = data["cortex"]
    health = cortex.get("system_health", {})
    recommendations = health.get("recommendations", [])
    for rec in recommendations:
        severity = "CRITICAL" if "CRITICAL" in rec.upper() else "WARNING" if "WARNING" in rec.upper() else "INFO"
        priority = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}.get(severity, 2)
        interventions.append({
            "source": "NEURAL_CORTEX",
            "severity": severity,
            "priority": priority,
            "description": rec,
            "zone": "system",
        })

    # From health zone scores
    for zone_name, zone_data in zones.items():
        score = zone_data.get("score", 0)
        if score < ZONE_CRITICAL:
            interventions.append({
                "source": "HOMEOSTASIS",
                "severity": "CRITICAL",
                "priority": 0,
                "description": f"{zone_name} health CRITICAL at {score}/100",
                "zone": zone_name,
                "score": score,
            })
        elif score < ZONE_WARNING:
            interventions.append({
                "source": "HOMEOSTASIS",
                "severity": "WARNING",
                "priority": 1,
                "description": f"{zone_name} health WARNING at {score}/100",
                "zone": zone_name,
                "score": score,
            })

    # From circuit status
    metab = data["metab"]
    metabolism = metab.get("metabolism", metab)
    circuit = metabolism.get("circuit_status", "open")
    if circuit != "closed":
        interventions.append({
            "source": "HOMEOSTASIS",
            "severity": "WARNING",
            "priority": 1,
            "description": f"Metabolic circuit is {circuit} -- feedback loop broken",
            "zone": "ecosystem",
        })

    # From fire ledger overlaps
    summary = fire_ledger.get("summary", {})
    if summary.get("overlap_detected"):
        overlaps = summary.get("overlap_engines", [])
        interventions.append({
            "source": "HOMEOSTASIS",
            "severity": "WARNING",
            "priority": 1,
            "description": f"RACE DETECTED: {', '.join(overlaps)} fired by both REFLEX and EXECUTIVE",
            "zone": "infrastructure",
        })

    # From self-funding ratio
    self_funding = _safe_float(metabolism.get("self_funding_ratio", 0))
    if self_funding < 0.5:
        interventions.append({
            "source": "HOMEOSTASIS",
            "severity": "CRITICAL",
            "priority": 0,
            "description": f"Self-funding ratio {self_funding:.3f}x -- burning faster than earning",
            "zone": "ecosystem",
        })

    # From brain confidence
    confidence = _safe_float(data["cortex"].get("decision_confidence", 0))
    if confidence < 30:
        interventions.append({
            "source": "HOMEOSTASIS",
            "severity": "WARNING",
            "priority": 1,
            "description": f"Brain confidence only {confidence}% -- low-quality decisions",
            "zone": "nervous_system",
        })

    # From reflex response time
    reflex_ms = _safe_float(data["reflex"].get("last_cycle", {}).get("arc_response_ms", 0))
    if reflex_ms > 1000:
        interventions.append({
            "source": "HOMEOSTASIS",
            "severity": "WARNING",
            "priority": 1,
            "description": f"Reflex response {reflex_ms}ms -- should be <500ms",
            "zone": "infrastructure",
        })

    interventions.sort(key=lambda x: x.get("priority", 99))
    return interventions


# ---------------------------------------------------------------------------
# Phase 5: TREND
# ---------------------------------------------------------------------------
def _compute_trend(current_equilibrium, history):
    if len(history) < 2:
        return "insufficient_data"
    recent = history[-TREND_WINDOW:] if len(history) >= TREND_WINDOW else history
    recent_scores = [h.get("equilibrium", 50) for h in recent]
    avg_recent = sum(recent_scores) / len(recent_scores)
    diff = current_equilibrium - avg_recent
    if diff > 5:
        return "improving"
    elif diff < -5:
        return "degrading"
    return "stable"


# ---------------------------------------------------------------------------
# Phase 6: EQUILIBRIUM
# ---------------------------------------------------------------------------
def _compute_equilibrium(zones):
    scores = [z.get("score", 0) for z in zones.values()]
    if not scores:
        return 0.0
    lowest = min(scores)
    average = sum(scores) / len(scores)
    # Weakest-link weighting: 60% lowest, 40% average
    equilibrium = lowest * 0.6 + average * 0.4
    return round(min(100, max(0, equilibrium)), 1)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def _print_dashboard(state):
    W = 64
    print()
    print("=" * W)
    print("  HOMEOSTASIS -- Active Equilibrium Maintenance")
    print("=" * W)

    eq = state.get("equilibrium", 0)
    trend = state.get("trend", "?")
    trend_arrow = {"improving": "^", "degrading": "v", "stable": "="}.get(trend, "?")

    print(f"\n  EQUILIBRIUM: {eq}/100 [{trend_arrow} {trend}]")

    zones = state.get("health_zones", {})
    print(f"\n  HEALTH ZONES:")
    for zone_name, zone_data in zones.items():
        score = zone_data.get("score", 0)
        status = "CRITICAL" if score < ZONE_CRITICAL else "WARNING" if score < ZONE_WARNING else "HEALTHY" if score >= ZONE_HEALTHY else "OK"
        bar_len = int(score / 5)
        bar = "#" * bar_len + "-" * (20 - bar_len)
        print(f"    {zone_name:<20} [{bar}] {score:5.1f}  [{status}]")

    fl = state.get("fire_ledger_summary", {})
    print(f"\n  FIRE LEDGER (race prevention):")
    print(f"    Reflex fires:    {fl.get('reflex_fire_count', 0)} in last {fl.get('window_minutes', 15)}min")
    print(f"    Executive fires: {fl.get('executive_fire_count', 0)}")
    overlap_str = "RACE" if fl.get("overlap_detected") else "clean"
    print(f"    Overlaps:        {fl.get('overlap_engines', [])} [{overlap_str}]")

    interventions = state.get("interventions", [])
    critical = [i for i in interventions if i.get("severity") == "CRITICAL"]
    warnings = [i for i in interventions if i.get("severity") == "WARNING"]
    print(f"\n  INTERVENTIONS: {len(critical)} CRITICAL, {len(warnings)} WARNING")
    for i in interventions[:8]:
        sev = i.get("severity", "?")[0]
        desc = i.get("description", "?")[:55]
        print(f"    [{sev}] {desc}")

    print(f"\n  ETHICS: 99% mutual aid / 1% node fuel")
    print("=" * W)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def run():
    """
    Full homeostasis pipeline:
    1. GATHER all health data
    2. ASSESS each health zone
    3. UPDATE fire ledger (race prevention)
    4. COMPUTE interventions
    5. COMPUTE equilibrium + trend
    6. SAVE state + EMIT to bus

    Ethics: 99% mutual aid / 1% node fuel
    """
    t0 = time.time()
    now = _now()

    # Phase 1
    data = _gather_all(now)

    # Phase 2
    zones = {
        "nervous_system":  _assess_nervous_system(data, now),
        "ecosystem":       _assess_ecosystem(data, now),
        "trading":         _assess_trading(data, now),
        "infrastructure":  _assess_infrastructure(data, now),
    }

    # Phase 3
    fire_ledger = _load_fire_ledger()
    fire_ledger = _update_fire_ledger(fire_ledger, data, now)
    _save(FIRE_LEDGER, fire_ledger)

    # Phase 4
    interventions = _compute_interventions(zones, data, fire_ledger, now)

    # Phase 5
    equilibrium = _compute_equilibrium(zones)

    prev_state = _load(STATE_FILE)
    history = prev_state.get("history", [])
    trend = _compute_trend(equilibrium, history)

    history.append({
        "timestamp": _now_iso(),
        "equilibrium": equilibrium,
        "zones": {k: v.get("score", 0) for k, v in zones.items()},
    })
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    elapsed_ms = round((time.time() - t0) * 1000, 1)

    state = {
        "timestamp": _now_iso(),
        "engine": "HOMEOSTASIS",
        "version": 2,
        "status": "active",
        "ethics": "99% mutual aid / 1% node fuel",
        "equilibrium": equilibrium,
        "trend": trend,
        "health_zones": zones,
        "interventions": interventions,
        "interventions_count": {
            "critical": len([i for i in interventions if i.get("severity") == "CRITICAL"]),
            "warning": len([i for i in interventions if i.get("severity") == "WARNING"]),
            "info": len([i for i in interventions if i.get("severity") == "INFO"]),
            "total": len(interventions),
        },
        "fire_ledger_summary": fire_ledger.get("summary", {}),
        "history": history,
        "performance": {"elapsed_ms": elapsed_ms},
    }

    _save(STATE_FILE, state)
    _print_dashboard(state)
    print(f"\n  [PERF] homeostasis={elapsed_ms}ms")

    # Emit to SYNAPTIC_BUS
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_batch("HOMEOSTASIS", {
            "status": "active",
            "equilibrium": equilibrium,
            "trend": trend,
            "nervous_system_score": zones["nervous_system"]["score"],
            "ecosystem_score": zones["ecosystem"]["score"],
            "trading_score": zones["trading"]["score"],
            "infrastructure_score": zones["infrastructure"]["score"],
            "interventions_critical": state["interventions_count"]["critical"],
            "interventions_warning": state["interventions_count"]["warning"],
            "interventions_total": state["interventions_count"]["total"],
            "fire_overlap_detected": fire_ledger.get("summary", {}).get("overlap_detected", False),
            "recently_fired_count": len(fire_ledger.get("summary", {}).get("recently_fired_engines", [])),
            "elapsed_ms": elapsed_ms,
        }, silent=False)
    except Exception:
        pass

    return state


# Keep backward compatibility with old main() pattern
def main():
    return run()


if __name__ == "__main__":
    run()
