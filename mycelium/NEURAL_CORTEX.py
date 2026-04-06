#!/usr/bin/env python3
"""
NEURAL_CORTEX.py -- Strategic brain of the SolarPunk nervous system
====================================================================
v1 (2026-04-06): The cerebral cortex. Reads everything, thinks, decides.

THE BIOLOGY:
  REFLEX_ARC is the spinal cord -- fast, hardcoded, no thinking.
  NEURAL_CORTEX is the cerebral cortex -- slow(ish), strategic, deliberate.

  It reads the ENTIRE system state in two file reads (bus + mesh), then
  synthesizes high-level strategic decisions that guide all other engines:

    - Where should capital go? (Kalshi vs Alpaca vs Solana DeFi)
    - How aggressive should we be? (risk posture from regime + health)
    - What's the single best action right now? (opportunity ranking)
    - Which engines need attention? (system health recommendations)

  No AI/LLM calls. Pure deterministic scoring logic. Like REFLEX_ARC but
  for STRATEGY instead of reflexes. Target: <200ms total execution.

THE DECISION PIPELINE:
  1. INGEST: Read SYNAPTIC_BUS (entire system state in one file read)
  2. INGEST: Read SIGNAL_MESH (15 sources aggregated)
  3. INGEST: Read GLOBAL_MARKETS (regime + ranked opportunities)
  4. INGEST: Read PROPRIOCEPTION (system self-awareness)
  5. INGEST: Read METABOLISM_LOOP (ecosystem health)
  6. INGEST: Read REFLEX_ARC (recent fire history)
  7. ASSESS: Score risk posture, capital allocation, growth priority
  8. DECIDE: Pick the single best action. Rank system recommendations.
  9. OUTPUT: Save to data/neural_cortex_state.json
  10. EMIT: Broadcast strategy to SYNAPTIC_BUS

Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)
Called by: NERVE_LOOP (Phase 13), OMNIBUS, AUTONOMIC_NERVE (task_queue)
Writes: data/neural_cortex_state.json
Reads: data/synaptic_bus.json, data/signal_mesh_state.json,
       data/global_markets_state.json, data/proprioception_state.json,
       data/metabolism_state.json, data/reflex_arc_state.json
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

STATE_FILE   = DATA / "neural_cortex_state.json"
BUS_FILE     = DATA / "synaptic_bus.json"
MESH_FILE    = DATA / "signal_mesh_state.json"
MARKETS_FILE = DATA / "global_markets_state.json"
PROPRIO_FILE = DATA / "proprioception_state.json"
METAB_FILE   = DATA / "metabolism_state.json"
REFLEX_FILE  = DATA / "reflex_arc_state.json"
EXEC_FILE    = DATA / "executive_function_state.json"
HOMEO_FILE   = DATA / "homeostasis_state.json"

# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------
# Risk posture thresholds
AGGRESSIVE_THRESHOLD = 60      # regime_score + conviction above this -> aggressive
CONSERVATIVE_THRESHOLD = 30    # below this -> conservative

# Capital allocation profiles (pct to each platform)
ALLOC_AGGRESSIVE   = {"kalshi_pct": 55, "alpaca_pct": 25, "solana_pct": 20}
ALLOC_MODERATE     = {"kalshi_pct": 50, "alpaca_pct": 35, "solana_pct": 15}
ALLOC_CONSERVATIVE = {"kalshi_pct": 35, "alpaca_pct": 50, "solana_pct": 15}

# Growth priority scoring weights
WEIGHT_TRADING       = 1.0   # How much trading signals matter
WEIGHT_ECOSYSTEM     = 0.7   # How much ecosystem health matters
WEIGHT_INFRASTRUCTURE = 0.5  # How much system health matters

# Health thresholds
HEALTH_CRITICAL = 30
HEALTH_WARNING  = 55
HEALTH_GOOD     = 75

# Reflex fire rate thresholds (fires per 100 checks)
FIRE_RATE_HIGH   = 40   # System is highly reactive
FIRE_RATE_NORMAL = 15
FIRE_RATE_LOW    = 5    # System is idle

# Engine freshness (seconds)
ALIVE_THRESHOLD_SEC = 300   # 5 min
STALE_THRESHOLD_SEC = 1800  # 30 min


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


def _ms_since(start):
    """Milliseconds elapsed since start time."""
    return round((time.time() - start) * 1000, 1)


def _safe_float(val, default=0.0):
    """Coerce a value to float safely."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _clamp(val, lo=0, hi=100):
    """Clamp a number to [lo, hi]."""
    return max(lo, min(hi, val))


# ---------------------------------------------------------------------------
# PHASE 1: Ingest -- Read all intelligence sources
# ---------------------------------------------------------------------------
def _ingest_bus(bus):
    """Extract key intelligence from the SYNAPTIC_BUS state."""
    engines = bus.get("engines", {})
    meta = bus.get("meta", {})
    convergence = bus.get("convergence", {})

    # Count engine liveness
    now = time.time()
    alive, stale, dead = 0, 0, 0
    engine_statuses = {}

    for name, eng_data in engines.items():
        ts_raw = eng_data.get("last_emission")
        age_sec = 999999
        if ts_raw:
            try:
                dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                age_sec = (datetime.now(timezone.utc) - dt).total_seconds()
            except Exception:
                pass

        if age_sec <= ALIVE_THRESHOLD_SEC:
            alive += 1
            status = "alive"
        elif age_sec <= STALE_THRESHOLD_SEC:
            stale += 1
            status = "stale"
        else:
            dead += 1
            status = "dead"

        engine_statuses[name] = {
            "status": status,
            "age_sec": round(age_sec),
            "emissions": eng_data.get("emission_count", 0),
        }

    # Extract capital from known engines
    total_capital = 0.0
    turbo_props = engines.get("TURBO_TRADER", {}).get("properties", {})
    alpaca_props = engines.get("ALPACA_TRADER", {}).get("properties", {})
    sol_props = engines.get("SOL_MAXIMIZER", {}).get("properties", {})

    kalshi_balance = _safe_float(turbo_props.get("balance", 0))
    alpaca_value = _safe_float(
        alpaca_props.get("portfolio_value", alpaca_props.get("cash", 0))
    )
    sol_value = _safe_float(sol_props.get("balance_usd", sol_props.get("balance", 0)))
    total_capital = kalshi_balance + alpaca_value + sol_value

    # Also check last_pulse for more accurate counts (updated by SYNAPTIC_BUS.pulse())
    pulse = bus.get("last_pulse", {})
    pulse_alive = pulse.get("alive", 0)
    pulse_stale = pulse.get("stale", 0)
    pulse_dead = pulse.get("dead", 0)
    pulse_connectivity = pulse.get("connectivity", 0)

    # Use whichever source shows more engines alive (bus pulse is more accurate)
    if pulse_alive > alive:
        alive = pulse_alive
        stale = pulse_stale
        dead = pulse_dead

    return {
        "engines_alive": alive,
        "engines_stale": stale,
        "engines_dead": dead,
        "engines_total": alive + stale + dead,
        "engine_statuses": engine_statuses,
        "total_emissions": meta.get("total_emissions", pulse.get("total_emissions", 0)),
        "connectivity": pulse_connectivity,
        "convergence": convergence,
        "sync_score": convergence.get("sync_score", 0),
        "total_capital_usd": round(total_capital, 2),
        "kalshi_balance": round(kalshi_balance, 2),
        "alpaca_value": round(alpaca_value, 2),
        "sol_value": round(sol_value, 2),
        # Per-engine props for deeper analysis
        "turbo_props": turbo_props,
        "alpaca_props": alpaca_props,
    }


def _ingest_mesh(mesh):
    """Extract composite signal from SIGNAL_MESH state."""
    composite = mesh.get("composite_signal", {})
    heartbeat = mesh.get("heartbeat", {})
    ranked = mesh.get("ranked_opportunities", [])

    return {
        "composite_strength": _safe_float(composite.get("composite_strength", 0)),
        "dominant_direction": composite.get("dominant_direction", "neutral"),
        "conviction_score": _safe_float(composite.get("conviction_score", 0)),
        "urgency": _safe_float(composite.get("urgency", 0)),
        "active_signals": composite.get("active_signals", 0),
        "total_signals": composite.get("total_signals", 0),
        "neural_connectivity": _safe_float(heartbeat.get("neural_connectivity", 0)),
        "sources_alive": heartbeat.get("alive", 0),
        "sources_dead": heartbeat.get("dead", 0),
        "top_opportunities": ranked[:5],
        "total_opportunities": len(ranked),
    }


def _ingest_markets(markets):
    """Extract regime and opportunities from GLOBAL_MARKETS state."""
    cross = markets.get("cross_platform", markets.get("cross_market", {}))
    ranked = markets.get("ranked_opportunities", [])

    regime = cross.get("regime", "NEUTRAL")
    regime_score = _safe_float(cross.get("regime_score", 0))
    regime_label = cross.get("regime_label", "")
    total_cap = _safe_float(cross.get("total_visible_capital", 0))
    recommendations = cross.get("recommendations", [])

    top_opp = None
    if ranked:
        top = ranked[0]
        top_opp = {
            "name": top.get("name", top.get("title", "?")),
            "score": _safe_float(top.get("score", 0)),
            "platform": top.get("platform", "?"),
            "type": top.get("type", "?"),
        }

    return {
        "regime": regime,
        "regime_score": regime_score,
        "regime_label": regime_label,
        "total_visible_capital": total_cap,
        "opportunities_count": len(ranked),
        "top_opportunity": top_opp,
        "recommendations": recommendations[:5],
    }


def _ingest_proprioception(proprio):
    """Extract system self-awareness from PROPRIOCEPTION state."""
    trajectory = proprio.get("growth_trajectory", {})

    return {
        "engine_count": proprio.get("engine_count", 0),
        "data_file_count": proprio.get("data_file_count", 0),
        "evolution_label": proprio.get("evolution_label", "UNKNOWN"),
        "coordination_score": _safe_float(proprio.get("coordination_score", 0)),
        "metabolism_rate": _safe_float(proprio.get("metabolism_rate", 0)),
        "portfolio_7d": _safe_float(trajectory.get("portfolio_7d", 0)),
        "engines_7d": trajectory.get("engines_7d", 0),
        "growth_velocity": _safe_float(proprio.get("growth_velocity", 0)),
    }


def _ingest_metabolism(metab):
    """Extract ecosystem health from METABOLISM_LOOP state."""
    metabolism = metab.get("metabolism", {})

    return {
        "circuit_status": metab.get("circuit_status", "open"),
        "ecosystem_health": _safe_float(metabolism.get("ecosystem_health", 0)),
        "revenue_velocity_hr": _safe_float(metabolism.get("revenue_velocity_per_hour", 0)),
        "self_funding_ratio": _safe_float(metabolism.get("self_funding_ratio", 0)),
        "circular_amplification": _safe_float(metabolism.get("circular_amplification", 1.0)),
        "combined_growth_rate": _safe_float(metabolism.get("combined_growth_rate", 0)),
        "nervous_alive": metab.get("nervous_system", {}).get("alive_engines", 0),
        "ecosystem_revenue": _safe_float(
            metab.get("ecosystem", {}).get("total_revenue", 0)
        ),
    }


def _ingest_reflex(reflex):
    """Extract reflex arc history from REFLEX_ARC state."""
    last_cycle = reflex.get("last_cycle", {})
    total_fires = reflex.get("total_fires", 0)
    total_checks = reflex.get("total_checks", 0)
    fire_counts = reflex.get("fire_counts", {})

    fire_rate = 0
    if total_checks > 0:
        fire_rate = round((total_fires / total_checks) * 100, 1)

    # Find the hottest reflex (most fired)
    hottest_reflex = "none"
    hottest_count = 0
    for name, count in fire_counts.items():
        if count > hottest_count:
            hottest_reflex = name
            hottest_count = count

    return {
        "total_fires": total_fires,
        "total_checks": total_checks,
        "fire_rate_pct": fire_rate,
        "last_cycle_fired": last_cycle.get("fired", 0),
        "last_cycle_checked": last_cycle.get("checked", 0),
        "arc_response_ms": _safe_float(last_cycle.get("arc_response_ms", 0)),
        "hottest_reflex": hottest_reflex,
        "hottest_count": hottest_count,
        "fire_counts": fire_counts,
    }


def _ingest_executive(execf):
    """
    LEARNING LOOP: Extract execution history from EXECUTIVE_FUNCTION.
    The brain learns from what worked and what failed.
    """
    stats = execf.get("stats", {})
    history = execf.get("execution_history", [])
    cooldowns = execf.get("cooldowns", {})

    total_execs = stats.get("total_executions", 0)
    successful = stats.get("successful", 0)
    failed = stats.get("failed", 0)
    success_rate = round((successful / max(total_execs, 1)) * 100, 1)

    # Track which engines succeed vs fail (learning signal)
    engines_executed = stats.get("engines_executed", {})
    # Recent history: last 10 executions
    recent = history[-10:] if history else []
    recent_success = sum(1 for r in recent if r.get("result") == "success")
    recent_fail = sum(1 for r in recent if r.get("result") == "failed")
    recent_rate = round((recent_success / max(len(recent), 1)) * 100, 1)

    # What engines are currently on cooldown (can't be recommended)
    active_cooldowns = list(cooldowns.keys())

    # Detect if execution quality is declining
    trend = "stable"
    if len(recent) >= 5:
        first_half = recent[:len(recent)//2]
        second_half = recent[len(recent)//2:]
        first_success = sum(1 for r in first_half if r.get("result") == "success")
        second_success = sum(1 for r in second_half if r.get("result") == "success")
        if second_success > first_success:
            trend = "improving"
        elif second_success < first_success:
            trend = "declining"

    return {
        "total_executions": total_execs,
        "success_rate": success_rate,
        "recent_success_rate": recent_rate,
        "execution_trend": trend,
        "engines_executed": engines_executed,
        "active_cooldowns": active_cooldowns,
        "recent_failures": [r.get("engine", "?") for r in recent if r.get("result") == "failed"],
        "recent_successes": [r.get("engine", "?") for r in recent if r.get("result") == "success"],
    }


def _ingest_homeostasis(homeo):
    """
    Extract equilibrium and health zone data from HOMEOSTASIS.
    Provides the brain with a unified view of system balance.
    """
    zones = homeo.get("health_zones", {})
    interventions = homeo.get("interventions_count", {})
    fire_summary = homeo.get("fire_ledger_summary", {})

    # Find the weakest zone
    zone_scores = {z: zd.get("score", 0) for z, zd in zones.items()}
    weakest = min(zone_scores, key=zone_scores.get) if zone_scores else "unknown"

    return {
        "equilibrium": _safe_float(homeo.get("equilibrium", 0)),
        "trend": homeo.get("trend", "unknown"),
        "zone_scores": zone_scores,
        "weakest_zone": weakest,
        "weakest_score": zone_scores.get(weakest, 0),
        "critical_interventions": interventions.get("critical", 0),
        "warning_interventions": interventions.get("warning", 0),
        "total_interventions": interventions.get("total", 0),
        "fire_overlap_detected": fire_summary.get("overlap_detected", False),
        "recently_fired_count": len(fire_summary.get("recently_fired_engines", [])),
    }


# ---------------------------------------------------------------------------
# PHASE 2: Assess -- Score every strategic dimension
# ---------------------------------------------------------------------------
def _assess_risk_posture(bus_intel, mesh_intel, markets_intel, metab_intel):
    """
    Determine risk posture: aggressive / moderate / conservative.

    Scoring factors (each 0-100, weighted):
      - Regime signal (RISK_ON = +40, RISK_OFF = -40, NEUTRAL = 0)
      - Mesh conviction (high conviction in bullish = aggressive)
      - Ecosystem health (healthy ecosystem = can afford risk)
      - Capital level (more capital = can absorb losses)
      - Self-funding ratio (self-sustaining = can take more risk)
    """
    score = 50  # Start neutral

    # Regime influence (strongest signal)
    regime = markets_intel.get("regime", "NEUTRAL")
    if regime == "RISK_ON":
        score += 25
    elif regime == "RISK_OFF":
        score -= 30
    # regime_score is typically -100 to +100
    regime_score = markets_intel.get("regime_score", 0)
    score += regime_score * 0.15

    # Mesh conviction in bullish direction
    conviction = mesh_intel.get("conviction_score", 0)
    direction = mesh_intel.get("dominant_direction", "neutral")
    if direction in ("bullish", "opportunity"):
        score += conviction * 0.15
    elif direction == "bearish":
        score -= conviction * 0.2

    # Ecosystem health bonus
    eco_health = metab_intel.get("ecosystem_health", 0)
    if eco_health > 60:
        score += 10
    elif eco_health < 20:
        score -= 10

    # Self-funding bonus (can afford to be aggressive)
    self_funding = metab_intel.get("self_funding_ratio", 0)
    if self_funding >= 1.0:
        score += 8  # Self-sustaining -- unlocks aggression
    elif self_funding < 0.3:
        score -= 5

    # Capital level influence
    total_cap = bus_intel.get("total_capital_usd", 0)
    if total_cap > 100:
        score += 5
    elif total_cap < 10:
        score -= 10  # Low capital = must be conservative

    score = _clamp(score, 0, 100)

    if score >= AGGRESSIVE_THRESHOLD:
        posture = "aggressive"
    elif score <= CONSERVATIVE_THRESHOLD:
        posture = "conservative"
    else:
        posture = "moderate"

    return posture, round(score, 1)


def _assess_capital_allocation(posture, markets_intel, mesh_intel, bus_intel):
    """
    Determine capital allocation percentages across platforms.

    Base allocation comes from risk posture, then adjusted by:
      - Market open status (boost Alpaca when open)
      - Kalshi opportunity count (boost Kalshi when edges exist)
      - SOL yield rates (boost Solana when yields are high)
      - Regime-specific tilts
    """
    # Start with posture-based baseline
    if posture == "aggressive":
        alloc = dict(ALLOC_AGGRESSIVE)
    elif posture == "conservative":
        alloc = dict(ALLOC_CONSERVATIVE)
    else:
        alloc = dict(ALLOC_MODERATE)

    # Adjust for Alpaca market hours
    alpaca_props = bus_intel.get("alpaca_props", {})
    market_open = alpaca_props.get("market_open", False)
    if market_open:
        # Shift 5% from Kalshi to Alpaca when market is open
        alloc["alpaca_pct"] += 5
        alloc["kalshi_pct"] -= 5

    # Adjust for opportunity density
    top_opp = markets_intel.get("top_opportunity")
    if top_opp:
        opp_platform = top_opp.get("platform", "").lower()
        if "kalshi" in opp_platform and top_opp.get("score", 0) > 70:
            alloc["kalshi_pct"] += 5
            alloc["alpaca_pct"] -= 3
            alloc["solana_pct"] -= 2
        elif "alpaca" in opp_platform and top_opp.get("score", 0) > 70:
            alloc["alpaca_pct"] += 5
            alloc["kalshi_pct"] -= 3
            alloc["solana_pct"] -= 2
        elif "sol" in opp_platform or "phantom" in opp_platform:
            alloc["solana_pct"] += 5
            alloc["kalshi_pct"] -= 3
            alloc["alpaca_pct"] -= 2

    # Regime-based tilt
    regime = markets_intel.get("regime", "NEUTRAL")
    if regime == "RISK_OFF":
        # In risk-off, favor Alpaca (hedging instruments) over prediction markets
        alloc["alpaca_pct"] += 5
        alloc["kalshi_pct"] -= 5
    elif regime == "RISK_ON":
        # In risk-on, favor prediction markets (high edge) and DeFi
        alloc["kalshi_pct"] += 3
        alloc["solana_pct"] += 2
        alloc["alpaca_pct"] -= 5

    # Ensure non-negative and normalize to 100%
    alloc["kalshi_pct"] = max(10, alloc["kalshi_pct"])
    alloc["alpaca_pct"] = max(10, alloc["alpaca_pct"])
    alloc["solana_pct"] = max(5, alloc["solana_pct"])

    total = alloc["kalshi_pct"] + alloc["alpaca_pct"] + alloc["solana_pct"]
    if total != 100 and total > 0:
        factor = 100.0 / total
        alloc["kalshi_pct"] = round(alloc["kalshi_pct"] * factor)
        alloc["alpaca_pct"] = round(alloc["alpaca_pct"] * factor)
        alloc["solana_pct"] = 100 - alloc["kalshi_pct"] - alloc["alpaca_pct"]

    return alloc


def _assess_growth_priority(mesh_intel, metab_intel, proprio_intel, reflex_intel):
    """
    Determine where to invest attention: trading vs ecosystem vs infrastructure.

    Scoring:
      Trading score:  mesh strength + urgency + opportunity count
      Ecosystem score: ecosystem health deficit + revenue velocity
      Infra score:    coordination deficit + engine staleness + fire rate anomaly
    """
    # Trading score
    trading_score = 0
    trading_score += mesh_intel.get("composite_strength", 0) * 0.3
    trading_score += mesh_intel.get("urgency", 0) * 0.3
    trading_score += min(40, mesh_intel.get("total_opportunities", 0) * 4)
    trading_score *= WEIGHT_TRADING

    # Ecosystem score (higher when ecosystem NEEDS attention)
    eco_score = 0
    eco_health = metab_intel.get("ecosystem_health", 50)
    # Invert: low health = high need for attention
    eco_deficit = max(0, 80 - eco_health)
    eco_score += eco_deficit * 0.6
    if metab_intel.get("circuit_status", "open") == "open":
        eco_score += 20  # Open circuit needs attention
    if metab_intel.get("self_funding_ratio", 0) < 0.5:
        eco_score += 15  # Not self-funding yet
    rev_velocity = metab_intel.get("revenue_velocity_hr", 0)
    if rev_velocity == 0:
        eco_score += 10  # Zero revenue velocity = ecosystem needs work
    eco_score *= WEIGHT_ECOSYSTEM

    # Infrastructure score (higher when infrastructure needs attention)
    infra_score = 0
    coordination = proprio_intel.get("coordination_score", 50)
    coord_deficit = max(0, 80 - coordination)
    infra_score += coord_deficit * 0.4
    evolution = proprio_intel.get("evolution_label", "UNKNOWN")
    if evolution == "LOW":
        infra_score += 25
    elif evolution == "UNKNOWN":
        infra_score += 15
    # High fire rate = system is stressed, needs infrastructure attention
    fire_rate = reflex_intel.get("fire_rate_pct", 0)
    if fire_rate > FIRE_RATE_HIGH:
        infra_score += 20
    elif fire_rate < FIRE_RATE_LOW:
        infra_score += 10  # Too quiet = maybe engines are down
    infra_score *= WEIGHT_INFRASTRUCTURE

    # Pick the winner
    scores = {
        "trading": round(trading_score, 1),
        "ecosystem": round(eco_score, 1),
        "infrastructure": round(infra_score, 1),
    }
    priority = max(scores, key=scores.get)

    return priority, scores


def _assess_system_health(bus_intel, mesh_intel, metab_intel, proprio_intel, reflex_intel):
    """
    Compute overall system health score (0-100) and find weakest engine.

    Components:
      - Engine liveness (% alive)
      - Neural connectivity (signal mesh)
      - Ecosystem health (metabolism)
      - Coordination score (proprioception)
      - Reflex responsiveness (arc_response_ms)
    """
    components = {}

    # Engine liveness
    total_engines = bus_intel.get("engines_total", 1)
    alive = bus_intel.get("engines_alive", 0)
    liveness = round((alive / max(total_engines, 1)) * 100, 1)
    components["engine_liveness"] = liveness

    # Neural connectivity
    connectivity = mesh_intel.get("neural_connectivity", 0)
    components["neural_connectivity"] = connectivity

    # Ecosystem health
    eco_health = metab_intel.get("ecosystem_health", 0)
    components["ecosystem_health"] = eco_health

    # Coordination
    coordination = proprio_intel.get("coordination_score", 0)
    components["coordination"] = coordination

    # Reflex responsiveness (lower ms = better, cap at 500ms)
    arc_ms = reflex_intel.get("arc_response_ms", 0)
    if arc_ms > 0:
        reflex_health = _clamp(100 - (arc_ms / 5), 0, 100)
    else:
        reflex_health = 50  # No data = neutral
    components["reflex_responsiveness"] = round(reflex_health, 1)

    # Weighted overall score
    overall = (
        liveness * 0.25 +
        connectivity * 0.20 +
        eco_health * 0.25 +
        coordination * 0.15 +
        reflex_health * 0.15
    )
    overall = round(_clamp(overall, 0, 100), 1)

    # Find weakest component
    weakest_component = min(components, key=components.get)

    # Find weakest engine (dead with most expected emissions)
    weakest_engine = "none"
    engine_statuses = bus_intel.get("engine_statuses", {})
    dead_engines = {
        name: data for name, data in engine_statuses.items()
        if data.get("status") == "dead"
    }
    if dead_engines:
        # The dead engine with the most emissions historically = most missed
        weakest_engine = max(
            dead_engines, key=lambda n: dead_engines[n].get("emissions", 0)
        )
    elif bus_intel.get("engines_stale", 0) > 0:
        stale_engines = {
            name: data for name, data in engine_statuses.items()
            if data.get("status") == "stale"
        }
        if stale_engines:
            weakest_engine = max(
                stale_engines, key=lambda n: stale_engines[n].get("age_sec", 0)
            )

    # Generate recommendations
    recommendations = []
    if liveness < 50:
        recommendations.append(
            f"CRITICAL: Only {alive}/{total_engines} engines alive -- restart dead engines"
        )
    if connectivity < 40:
        recommendations.append(
            f"Signal mesh connectivity low ({connectivity}%) -- check signal sources"
        )
    if eco_health < HEALTH_CRITICAL:
        recommendations.append(
            f"Ecosystem health critical ({eco_health}%) -- prioritize revenue generation"
        )
    if coordination < 40:
        recommendations.append(
            f"Low coordination ({coordination}%) -- engines are not emitting to bus"
        )
    if arc_ms > 200:
        recommendations.append(
            f"Slow reflex response ({arc_ms}ms) -- check for I/O bottlenecks"
        )
    if metab_intel.get("circuit_status", "open") == "open":
        recommendations.append(
            "Metabolism circuit OPEN -- close the feedback loop"
        )
    if not recommendations:
        recommendations.append("System healthy -- maintain current operations")

    return {
        "overall_score": overall,
        "components": components,
        "weakest_component": weakest_component,
        "weakest_engine": weakest_engine,
        "recommendations": recommendations,
    }


# ---------------------------------------------------------------------------
# PHASE 3: Decide -- Pick the single best action
# ---------------------------------------------------------------------------
def _decide_top_action(
    posture, alloc, priority, priority_scores,
    mesh_intel, markets_intel, reflex_intel, metab_intel, bus_intel, health,
    exec_intel=None, homeo_intel=None
):
    """
    Synthesize all assessments into the SINGLE best action to take right now.

    Candidates are generated from each dimension, scored, and the top one wins.
    LEARNING LOOP: Engines that recently failed are penalized.
    HOMEOSTASIS: Weakest health zones generate intervention candidates.
    """
    exec_intel = exec_intel or {}
    homeo_intel = homeo_intel or {}
    candidates = []

    # Candidate 1: Best trading opportunity from SIGNAL_MESH
    top_opps = mesh_intel.get("top_opportunities", [])
    if top_opps:
        best_opp = top_opps[0]
        opp_name = best_opp.get("market", best_opp.get("pair",
                   best_opp.get("action", best_opp.get("type", "unknown"))))
        opp_platform = best_opp.get("platform", "?")
        opp_score = _safe_float(best_opp.get("composite_score", 0))
        urgency = mesh_intel.get("urgency", 0)
        # Score: opportunity score + urgency + posture bonus
        action_score = opp_score * 0.5 + urgency * 0.3
        if posture == "aggressive":
            action_score *= 1.2
        elif posture == "conservative":
            action_score *= 0.7
        candidates.append({
            "description": f"Execute top opportunity: {opp_name} on {opp_platform}",
            "engine": f"TURBO_TRADER" if "kalshi" in opp_platform.lower() else (
                "ALPACA_TRADER" if "alpaca" in opp_platform.lower() else
                "CROSS_POLLINATOR"
            ),
            "urgency": round(_clamp(action_score, 0, 100)),
            "score": round(action_score, 1),
            "category": "trading",
        })

    # Candidate 2: Best opportunity from GLOBAL_MARKETS
    markets_top = markets_intel.get("top_opportunity")
    if markets_top:
        m_name = markets_top.get("name", "?")
        m_platform = markets_top.get("platform", "?")
        m_score = _safe_float(markets_top.get("score", 0))
        action_score = m_score * 0.6
        regime = markets_intel.get("regime", "NEUTRAL")
        if regime == "RISK_ON":
            action_score *= 1.15
        elif regime == "RISK_OFF":
            action_score *= 0.8
        candidates.append({
            "description": f"Deploy to global opportunity: {m_name} ({m_platform})",
            "engine": "GLOBAL_MARKETS",
            "urgency": round(_clamp(action_score, 0, 100)),
            "score": round(action_score, 1),
            "category": "trading",
        })

    # Candidate 3: Fix weakest engine (if health is bad)
    if health["overall_score"] < HEALTH_WARNING:
        weakest = health.get("weakest_engine", "none")
        if weakest != "none":
            severity = 100 - health["overall_score"]
            candidates.append({
                "description": f"Restart/fix weakest engine: {weakest}",
                "engine": "REFLEX_ARC",
                "urgency": round(_clamp(severity, 0, 100)),
                "score": round(severity * 0.8, 1),
                "category": "infrastructure",
            })

    # Candidate 4: Close metabolism circuit (if open)
    if metab_intel.get("circuit_status", "open") == "open":
        eco_deficit = max(0, 80 - metab_intel.get("ecosystem_health", 0))
        candidates.append({
            "description": "Close metabolism circuit -- connect revenue to nervous system",
            "engine": "METABOLISM_LOOP",
            "urgency": round(_clamp(eco_deficit, 0, 100)),
            "score": round(eco_deficit * 0.7, 1),
            "category": "ecosystem",
        })

    # Candidate 5: Boost ecosystem revenue (if stalling)
    rev_velocity = metab_intel.get("revenue_velocity_hr", 0)
    if rev_velocity == 0 and metab_intel.get("self_funding_ratio", 0) < 0.5:
        candidates.append({
            "description": "Generate revenue -- ecosystem has zero velocity",
            "engine": "FLYWHEEL",
            "urgency": 60,
            "score": 45.0,
            "category": "ecosystem",
        })

    # Candidate 6: Rebalance capital (if allocation is significantly off)
    total_cap = bus_intel.get("total_capital_usd", 0)
    if total_cap > 5:
        kalshi_actual = bus_intel.get("kalshi_balance", 0)
        alpaca_actual = bus_intel.get("alpaca_value", 0)
        kalshi_target_pct = alloc.get("kalshi_pct", 50) / 100
        alpaca_target_pct = alloc.get("alpaca_pct", 35) / 100
        kalshi_actual_pct = kalshi_actual / total_cap if total_cap else 0
        alpaca_actual_pct = alpaca_actual / total_cap if total_cap else 0
        drift = abs(kalshi_actual_pct - kalshi_target_pct) + abs(alpaca_actual_pct - alpaca_target_pct)
        if drift > 0.25:  # >25% off target
            candidates.append({
                "description": f"Rebalance capital: {drift*100:.0f}% drift from target allocation",
                "engine": "AUTO_DEPOSIT",
                "urgency": round(_clamp(drift * 100, 0, 100)),
                "score": round(drift * 60, 1),
                "category": "trading",
            })

    # Candidate 7: Address high reflex fire rate (system stress)
    fire_rate = reflex_intel.get("fire_rate_pct", 0)
    if fire_rate > FIRE_RATE_HIGH:
        hottest = reflex_intel.get("hottest_reflex", "unknown")
        candidates.append({
            "description": f"Investigate high reflex fire rate ({fire_rate}%) -- hottest: {hottest}",
            "engine": "REFLEX_ARC",
            "urgency": round(_clamp(fire_rate, 0, 100)),
            "score": round(fire_rate * 0.5, 1),
            "category": "infrastructure",
        })

    # Candidate 8: HOMEOSTASIS weakest zone intervention
    weakest_zone = homeo_intel.get("weakest_zone", "")
    weakest_score = homeo_intel.get("weakest_score", 100)
    if weakest_score < 30:
        zone_to_engine = {
            "nervous_system": "SYNAPTIC_BUS",
            "ecosystem": "METABOLISM_LOOP",
            "trading": "CROSS_POLLINATOR",
            "infrastructure": "PROPRIOCEPTION",
        }
        target = zone_to_engine.get(weakest_zone, "HOMEOSTASIS")
        candidates.append({
            "description": f"Fix weakest zone: {weakest_zone} at {weakest_score}/100",
            "engine": target,
            "urgency": round(_clamp(100 - weakest_score, 0, 100)),
            "score": round((100 - weakest_score) * 0.75, 1),
            "category": "infrastructure",
        })

    # LEARNING LOOP: Penalize candidates whose engine recently failed
    recent_failures = set(exec_intel.get("recent_failures", []))
    cooldown_engines = set(exec_intel.get("active_cooldowns", []))
    for c in candidates:
        eng = c.get("engine", "")
        if eng in recent_failures:
            c["score"] *= 0.5  # 50% penalty for recently failed engines
            c["urgency"] = max(0, c["urgency"] - 15)
            c["description"] += " [PENALIZED: recently failed]"
        if eng in cooldown_engines:
            c["score"] *= 0.3  # Heavy penalty for engines on cooldown
            c["description"] += " [ON COOLDOWN]"

    # Pick the winner
    if not candidates:
        return {
            "description": "System idle -- no actionable opportunities detected",
            "engine": "NEURAL_CORTEX",
            "urgency": 0,
        }

    candidates.sort(key=lambda c: c["score"], reverse=True)
    winner = candidates[0]
    return {
        "description": winner["description"],
        "engine": winner["engine"],
        "urgency": winner["urgency"],
    }


# ---------------------------------------------------------------------------
# PHASE 4: Compute decision confidence
# ---------------------------------------------------------------------------
def _compute_confidence(
    bus_intel, mesh_intel, markets_intel, metab_intel, proprio_intel, health
):
    """
    How confident are we in the overall strategic output?

    Factors:
      - Data freshness (more alive sources = more confident)
      - Signal agreement (high conviction = high confidence)
      - System health (healthy system = trustworthy signals)
      - Information coverage (more sources with data = better picture)
    """
    # Data freshness (0-25)
    alive_ratio = bus_intel.get("engines_alive", 0) / max(bus_intel.get("engines_total", 1), 1)
    freshness_score = alive_ratio * 25

    # Signal agreement (0-25)
    conviction = mesh_intel.get("conviction_score", 0)
    agreement_score = conviction * 0.25

    # System health (0-25)
    health_score = health.get("overall_score", 0) * 0.25

    # Information coverage (0-25)
    active_signals = mesh_intel.get("active_signals", 0)
    total_signals = mesh_intel.get("total_signals", 1)
    coverage = (active_signals / max(total_signals, 1)) * 25

    confidence = round(_clamp(
        freshness_score + agreement_score + health_score + coverage, 0, 100
    ), 1)

    return confidence


# ---------------------------------------------------------------------------
# PHASE 5: Build reasoning chain
# ---------------------------------------------------------------------------
def _build_reasoning(
    posture, risk_score, alloc, priority, priority_scores,
    top_action, markets_intel, mesh_intel, metab_intel, health
):
    """Generate the human-readable reasoning chain for the strategy."""
    reasons = []

    # Regime context
    regime = markets_intel.get("regime", "NEUTRAL")
    reasons.append(
        f"Market regime is {regime} (score {markets_intel.get('regime_score', 0)}) "
        f"-> risk posture: {posture.upper()} ({risk_score}/100)"
    )

    # Signal context
    direction = mesh_intel.get("dominant_direction", "neutral")
    conviction = mesh_intel.get("conviction_score", 0)
    reasons.append(
        f"Signal mesh reads {direction.upper()} with {conviction}% conviction "
        f"across {mesh_intel.get('active_signals', 0)} active sources"
    )

    # Health context
    overall = health.get("overall_score", 0)
    if overall >= HEALTH_GOOD:
        reasons.append(f"System health GOOD ({overall}/100) -- full capacity available")
    elif overall >= HEALTH_WARNING:
        reasons.append(
            f"System health OK ({overall}/100) -- "
            f"weakest: {health.get('weakest_component', '?')}"
        )
    else:
        reasons.append(
            f"System health WARNING ({overall}/100) -- "
            f"fix {health.get('weakest_engine', '?')} before aggressive deployment"
        )

    # Priority context
    reasons.append(
        f"Growth priority: {priority.upper()} "
        f"(trading={priority_scores.get('trading', 0)}, "
        f"ecosystem={priority_scores.get('ecosystem', 0)}, "
        f"infra={priority_scores.get('infrastructure', 0)})"
    )

    # Top action
    reasons.append(
        f"Top action: {top_action.get('description', 'none')} "
        f"(urgency {top_action.get('urgency', 0)}/100)"
    )

    return reasons


# ---------------------------------------------------------------------------
# Console output
# ---------------------------------------------------------------------------
def _print_summary(state):
    """Print a formatted summary of the neural cortex output."""
    strategy = state.get("strategy", {})
    health = state.get("system_health", {})
    intel = state.get("intelligence_summary", {})

    W = 60
    print()
    print("=" * W)
    print("  NEURAL CORTEX -- Strategic Brain Output")
    print("=" * W)

    # Strategy
    print(f"\n  RISK POSTURE:    {strategy.get('risk_posture', '?').upper()}")
    alloc = strategy.get("capital_allocation", {})
    print(f"  CAPITAL SPLIT:   Kalshi {alloc.get('kalshi_pct', 0)}% | "
          f"Alpaca {alloc.get('alpaca_pct', 0)}% | "
          f"Solana {alloc.get('solana_pct', 0)}%")
    print(f"  GROWTH FOCUS:    {strategy.get('growth_priority', '?').upper()}")

    # Top action
    action = strategy.get("top_action", {})
    print(f"\n  TOP ACTION:      {action.get('description', 'none')}")
    print(f"    Engine:        {action.get('engine', '?')}")
    print(f"    Urgency:       {action.get('urgency', 0)}/100")

    # Reasoning
    reasons = strategy.get("reasoning", [])
    if reasons:
        print(f"\n  REASONING:")
        for i, r in enumerate(reasons, 1):
            print(f"    {i}. {r}")

    # Health
    print(f"\n  SYSTEM HEALTH:   {health.get('overall_score', 0)}/100")
    print(f"    Weakest:       {health.get('weakest_engine', 'none')}")
    recs = health.get("recommendations", [])
    if recs:
        print(f"    Recommendations:")
        for rec in recs[:3]:
            print(f"      - {rec}")

    # Intelligence summary
    print(f"\n  INTELLIGENCE:")
    print(f"    Regime:        {intel.get('regime', '?')}")
    print(f"    Signal:        {intel.get('signal_strength', 0)}/100")
    print(f"    Conviction:    {intel.get('conviction', 0)}/100")
    print(f"    Eco health:    {intel.get('ecosystem_health', 0)}/100")
    print(f"    Engines alive: {intel.get('engines_alive', 0)}")
    print(f"    Total capital: ${intel.get('total_capital_usd', 0):.2f}")
    print(f"    Confidence:    {state.get('decision_confidence', 0)}/100")

    print(f"\n  ETHICS: {state.get('ethics', '99% mutual aid / 1% node fuel')}")
    print("=" * W)


# ===========================================================================
# MAIN ENTRY POINT
# ===========================================================================
def run():
    """
    Execute the full Neural Cortex decision pipeline:
    Ingest -> Assess -> Decide -> Output -> Emit

    Returns the complete neural_cortex_state dict.

    Ethics: 99% mutual aid / 1% node fuel
    """
    t0 = time.time()

    # ----- PHASE 1: INGEST (target: <50ms) -----
    bus_raw     = _load(BUS_FILE)
    mesh_raw    = _load(MESH_FILE)
    markets_raw = _load(MARKETS_FILE)
    proprio_raw = _load(PROPRIO_FILE)
    metab_raw   = _load(METAB_FILE)
    reflex_raw  = _load(REFLEX_FILE)
    exec_raw    = _load(EXEC_FILE)
    homeo_raw   = _load(HOMEO_FILE)

    bus_intel     = _ingest_bus(bus_raw)
    mesh_intel    = _ingest_mesh(mesh_raw)
    markets_intel = _ingest_markets(markets_raw)
    proprio_intel = _ingest_proprioception(proprio_raw)
    metab_intel   = _ingest_metabolism(metab_raw)
    reflex_intel  = _ingest_reflex(reflex_raw)
    exec_intel    = _ingest_executive(exec_raw)
    homeo_intel   = _ingest_homeostasis(homeo_raw)

    ingest_ms = _ms_since(t0)

    # ----- PHASE 2: ASSESS (target: <50ms) -----
    t_assess = time.time()

    posture, risk_score = _assess_risk_posture(
        bus_intel, mesh_intel, markets_intel, metab_intel
    )
    alloc = _assess_capital_allocation(
        posture, markets_intel, mesh_intel, bus_intel
    )
    priority, priority_scores = _assess_growth_priority(
        mesh_intel, metab_intel, proprio_intel, reflex_intel
    )
    health = _assess_system_health(
        bus_intel, mesh_intel, metab_intel, proprio_intel, reflex_intel
    )

    # LEARNING LOOP: Adjust health based on EXECUTIVE_FUNCTION success history
    if exec_intel.get("total_executions", 0) > 0:
        exec_rate = exec_intel.get("success_rate", 100)
        if exec_rate < 50:
            health["recommendations"].insert(0,
                f"WARNING: Execution success rate low ({exec_rate}%) -- brain decisions may need recalibration"
            )
        # Penalize health if execution quality is declining
        if exec_intel.get("execution_trend") == "declining":
            health["overall_score"] = max(0, health["overall_score"] - 5)
            health["recommendations"].append(
                "WARNING: Execution quality declining -- review top_action recommendations"
            )
        # Boost confidence if execution trend is improving
        elif exec_intel.get("execution_trend") == "improving":
            health["overall_score"] = min(100, health["overall_score"] + 3)

    # HOMEOSTASIS integration: Use equilibrium data to inform health
    if homeo_intel.get("equilibrium", 0) > 0:
        # If HOMEOSTASIS reports critical interventions, escalate
        if homeo_intel.get("critical_interventions", 0) > 0:
            health["recommendations"].insert(0,
                f"CRITICAL: HOMEOSTASIS reports {homeo_intel['critical_interventions']} critical interventions -- weakest zone: {homeo_intel.get('weakest_zone', '?')} ({homeo_intel.get('weakest_score', 0)}/100)"
            )
        # Blend HOMEOSTASIS equilibrium into overall health
        homeo_eq = homeo_intel["equilibrium"]
        health["overall_score"] = round(
            health["overall_score"] * 0.6 + homeo_eq * 0.4, 1
        )

    assess_ms = _ms_since(t_assess)

    # ----- PHASE 3: DECIDE (target: <50ms) -----
    t_decide = time.time()

    top_action = _decide_top_action(
        posture, alloc, priority, priority_scores,
        mesh_intel, markets_intel, reflex_intel, metab_intel, bus_intel, health,
        exec_intel, homeo_intel
    )
    confidence = _compute_confidence(
        bus_intel, mesh_intel, markets_intel, metab_intel, proprio_intel, health
    )
    reasoning = _build_reasoning(
        posture, risk_score, alloc, priority, priority_scores,
        top_action, markets_intel, mesh_intel, metab_intel, health
    )

    decide_ms = _ms_since(t_decide)
    total_ms = _ms_since(t0)

    # ----- PHASE 4: BUILD OUTPUT -----
    state = {
        "timestamp": _now_iso(),
        "engine": "NEURAL_CORTEX",
        "status": "active",
        "strategy": {
            "risk_posture": posture,
            "risk_score": risk_score,
            "capital_allocation": alloc,
            "growth_priority": priority,
            "growth_scores": priority_scores,
            "top_action": top_action,
            "reasoning": reasoning,
        },
        "system_health": {
            "overall_score": health["overall_score"],
            "components": health["components"],
            "weakest_component": health["weakest_component"],
            "weakest_engine": health["weakest_engine"],
            "recommendations": health["recommendations"],
        },
        "intelligence_summary": {
            "regime": markets_intel.get("regime", "NEUTRAL"),
            "regime_score": markets_intel.get("regime_score", 0),
            "signal_strength": mesh_intel.get("composite_strength", 0),
            "conviction": mesh_intel.get("conviction_score", 0),
            "urgency": mesh_intel.get("urgency", 0),
            "ecosystem_health": metab_intel.get("ecosystem_health", 0),
            "reflex_fire_rate": reflex_intel.get("fire_rate_pct", 0),
            "engines_alive": bus_intel.get("engines_alive", 0),
            "engines_total": bus_intel.get("engines_total", 0),
            "total_capital_usd": bus_intel.get("total_capital_usd", 0),
            "neural_connectivity": mesh_intel.get("neural_connectivity", 0),
            "sources_alive": mesh_intel.get("sources_alive", 0),
        },
        "performance": {
            "ingest_ms": ingest_ms,
            "assess_ms": assess_ms,
            "decide_ms": decide_ms,
            "total_ms": total_ms,
        },
        "decision_confidence": confidence,
        "ethics": "99% mutual aid / 1% node fuel",
    }

    # ----- PHASE 5: PRINT SUMMARY -----
    _print_summary(state)

    print(f"\n  [PERF] ingest={ingest_ms}ms assess={assess_ms}ms "
          f"decide={decide_ms}ms total={total_ms}ms")

    # ----- PHASE 6: SAVE STATE -----
    _save(STATE_FILE, state)

    # ----- PHASE 7: EMIT TO SYNAPTIC_BUS -----
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_batch("NEURAL_CORTEX", {
            "status": "active",
            "risk_posture": posture,
            "risk_score": risk_score,
            "capital_kalshi_pct": alloc.get("kalshi_pct", 0),
            "capital_alpaca_pct": alloc.get("alpaca_pct", 0),
            "capital_solana_pct": alloc.get("solana_pct", 0),
            "growth_priority": priority,
            "top_action": top_action.get("description", "none"),
            "top_action_engine": top_action.get("engine", "none"),
            "top_action_urgency": top_action.get("urgency", 0),
            "system_health": health["overall_score"],
            "weakest_engine": health["weakest_engine"],
            "decision_confidence": confidence,
            "regime": markets_intel.get("regime", "NEUTRAL"),
            "signal_direction": mesh_intel.get("dominant_direction", "neutral"),
            "total_ms": total_ms,
        }, silent=False)
    except Exception:
        pass  # Bus unavailable -- degrade gracefully

    return state


if __name__ == "__main__":
    run()
