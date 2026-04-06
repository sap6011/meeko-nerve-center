#!/usr/bin/env python3
"""
SIGNAL_MESH.py -- Central nervous system signal bus
====================================================
v1 (2026-04-06): Signal aggregation engine. Reads EVERY intelligence source,
                 produces a single weighted composite signal per opportunity.

This is the nerve center's signal mesh -- the layer that sits above all
individual scanners and traders and answers one question:

    "Right now, across EVERY platform and EVERY data source,
     what is the single best thing to do with the next dollar?"

SIGNAL SOURCES (13 total):
  1. prediction_intelligence.json  -- Kalshi/prediction market merged intel
  2. polymarket_scan.json          -- Polymarket edges & opportunities
  3. kalshi_scan.json              -- Kalshi scanner results
  4. arbitrage_scanner_state.json  -- Cross-platform arbitrage detection
  5. cross_pollinator_state.json   -- Capital routing & mycelium health
  6. turbo_trader_state.json       -- TURBO high-freq compounding state
  7. alpaca_trader_state.json      -- Alpaca stocks/ETFs/crypto state
  8. trade_ledger.json             -- Historical trade ledger
  9. compound_tracker.json         -- Compound growth tracking
  10. flywheel_state.json          -- Revenue flywheel state
  11. ai_cost_tracker.json         -- AI cost vs profit tracking
  12. metabolism_state.json         -- METABOLISM_LOOP circular flow (revenue velocity, ecosystem health)
  13. global_markets_state.json    -- GLOBAL_MARKETS cross-platform regime + ranked opportunities

OUTPUT: data/signal_mesh_state.json
  - Composite signal (weighted average, dominant direction, conviction)
  - Ranked opportunities across ALL platforms
  - Urgency score (time-sensitivity of best opportunities)
  - System heartbeat (alive / stale / dead sources)
  - Neural connectivity score

ETHICS: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)
Called by: NERVE_LOOP Phase 10, OMNIBUS, task_queue (every 15 min)
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Signal source definitions
# ---------------------------------------------------------------------------
SIGNAL_SOURCES = [
    {"id": "prediction_intel",  "file": "prediction_intelligence.json",  "weight": 1.0,  "label": "Prediction Intelligence"},
    {"id": "polymarket",        "file": "polymarket_scan.json",          "weight": 0.9,  "label": "Polymarket Scanner"},
    {"id": "kalshi",            "file": "kalshi_scan.json",              "weight": 0.9,  "label": "Kalshi Scanner"},
    {"id": "arbitrage",         "file": "arbitrage_scanner_state.json",  "weight": 1.0,  "label": "Arbitrage Scanner"},
    {"id": "cross_pollinator",  "file": "cross_pollinator_state.json",   "weight": 0.7,  "label": "Cross-Pollinator"},
    {"id": "turbo",             "file": "turbo_trader_state.json",       "weight": 0.85, "label": "TURBO Trader"},
    {"id": "alpaca",            "file": "alpaca_trader_state.json",      "weight": 0.8,  "label": "Alpaca Trader"},
    {"id": "trade_ledger",      "file": "trade_ledger.json",             "weight": 0.5,  "label": "Trade Ledger"},
    {"id": "compound_tracker",  "file": "compound_tracker.json",         "weight": 0.6,  "label": "Compound Tracker"},
    {"id": "flywheel",          "file": "flywheel_state.json",           "weight": 0.5,  "label": "Revenue Flywheel"},
    {"id": "ai_cost",           "file": "ai_cost_tracker.json",          "weight": 0.4,  "label": "AI Cost Tracker"},
    {"id": "metabolism",        "file": "metabolism_state.json",          "weight": 0.7,  "label": "Metabolism Loop"},
    {"id": "global_markets",    "file": "global_markets_state.json",      "weight": 0.9,  "label": "Global Markets"},
    {"id": "reflex_arc",        "file": "reflex_arc_state.json",          "weight": 0.6,  "label": "Reflex Arc"},
    {"id": "proprioception",    "file": "proprioception_state.json",      "weight": 0.5,  "label": "Proprioception"},
    {"id": "neural_cortex",     "file": "neural_cortex_state.json",       "weight": 0.85, "label": "Neural Cortex"},
    {"id": "executive_fn",      "file": "executive_function_state.json",  "weight": 0.5,  "label": "Executive Function"},
]

# Freshness decay thresholds
FRESH_THRESHOLD_MINUTES = 60       # < 1 hour = full weight
STALE_THRESHOLD_MINUTES = 240      # 1-4 hours = decaying weight
DEAD_THRESHOLD_HOURS = 24          # > 24 hours = effectively zero weight


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
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


# ---------------------------------------------------------------------------
# Timestamp utilities
# ---------------------------------------------------------------------------
def _parse_timestamp(raw):
    """Parse an ISO timestamp string into a timezone-aware datetime, or None."""
    if not raw or not isinstance(raw, str):
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _age_minutes(ts_str, now):
    """Return age of a timestamp in minutes, or None if unparseable."""
    dt = _parse_timestamp(ts_str)
    if dt is None:
        return None
    delta = now - dt
    return max(0, delta.total_seconds() / 60)


def _freshness_weight(age_min):
    """
    Compute a freshness multiplier (0.0 - 1.0) based on signal age.
      < 60 min  -> 1.0 (full weight)
      60-240 min -> linear decay from 1.0 to 0.05
      > 240 min  -> 0.05 (nearly zero)
    """
    if age_min is None:
        return 0.1  # Unknown age -- treat as stale
    if age_min <= FRESH_THRESHOLD_MINUTES:
        return 1.0
    if age_min >= STALE_THRESHOLD_MINUTES:
        return 0.05
    # Linear decay
    span = STALE_THRESHOLD_MINUTES - FRESH_THRESHOLD_MINUTES
    progress = (age_min - FRESH_THRESHOLD_MINUTES) / span
    return max(0.05, 1.0 - progress * 0.95)


def _classify_freshness(age_min):
    """Classify a source as alive, stale, or dead."""
    if age_min is None:
        return "dead"
    if age_min <= FRESH_THRESHOLD_MINUTES:
        return "alive"
    if age_min <= DEAD_THRESHOLD_HOURS * 60:
        return "stale"
    return "dead"


# ---------------------------------------------------------------------------
# Signal extraction per source
# ---------------------------------------------------------------------------
def _find_timestamp(data):
    """Search common timestamp keys in a data dict."""
    for key in ("timestamp", "last_scan", "last_run", "updated_at", "ts",
                "last_update", "scanned_at", "completed", "recorded_at"):
        val = data.get(key)
        if val:
            return val
    return None


def _extract_signal(source_def, data, now):
    """
    Extract normalized signal from a source's data.
    Returns a dict with signal_strength, signal_direction, freshness info,
    specific opportunities, and effective weight.
    """
    sid = source_def["id"]
    base_weight = source_def["weight"]
    ts_raw = _find_timestamp(data)
    age = _age_minutes(ts_raw, now)
    freshness_mult = _freshness_weight(age)
    freshness_class = _classify_freshness(age)

    signal = {
        "source_id": sid,
        "label": source_def["label"],
        "file": source_def["file"],
        "timestamp": ts_raw,
        "age_minutes": round(age, 1) if age is not None else None,
        "freshness": freshness_class,
        "freshness_weight": round(freshness_mult, 3),
        "base_weight": base_weight,
        "effective_weight": round(base_weight * freshness_mult, 3),
        "signal_strength": 0,
        "signal_direction": "neutral",
        "opportunities": [],
        "has_data": bool(data),
    }

    if not data:
        return signal

    # -----------------------------------------------------------------------
    # Source-specific extraction
    # -----------------------------------------------------------------------
    if sid == "prediction_intel":
        sentiment = data.get("sentiment", {})
        action = sentiment.get("recommended_action", "hold")
        sol_outlook = sentiment.get("sol_outlook", "neutral")
        bullish = sentiment.get("crypto_bullish", False)
        sources = data.get("sources", [])
        signal["signal_strength"] = min(80, len(sources) * 20 + (30 if bullish else 0))
        signal["signal_direction"] = "bullish" if bullish else ("bearish" if action == "sell" else "neutral")
        if action not in ("hold", "none", ""):
            signal["opportunities"].append({
                "type": "prediction_market",
                "action": action,
                "sol_outlook": sol_outlook,
                "platform": "multi",
            })

    elif sid == "polymarket":
        edges = data.get("edges", data.get("opportunities", []))
        if isinstance(edges, list):
            signal["signal_strength"] = min(90, len(edges) * 15)
            for e in edges[:5]:
                signal["opportunities"].append({
                    "type": "polymarket_edge",
                    "market": e.get("title", e.get("market", "?")),
                    "edge": e.get("edge", e.get("edge_pct", 0)),
                    "platform": "polymarket",
                })
        signal["signal_direction"] = "opportunity" if edges else "neutral"

    elif sid == "kalshi":
        opps = data.get("opportunities", data.get("top_markets", []))
        if isinstance(opps, list):
            signal["signal_strength"] = min(90, len(opps) * 12)
            for o in opps[:5]:
                signal["opportunities"].append({
                    "type": "kalshi_market",
                    "market": o.get("title", o.get("ticker", "?")),
                    "edge": o.get("edge", o.get("expected_value", 0)),
                    "platform": "kalshi",
                })
        signal["signal_direction"] = "opportunity" if opps else "neutral"

    elif sid == "arbitrage":
        arbs = data.get("actionable_opportunities", data.get("opportunities", []))
        if isinstance(arbs, list):
            signal["signal_strength"] = min(100, len(arbs) * 25)
            for a in arbs[:5]:
                signal["opportunities"].append({
                    "type": "arbitrage",
                    "pair": a.get("pair", a.get("market", "?")),
                    "spread": a.get("spread", a.get("profit_pct", 0)),
                    "urgency": a.get("urgency", "medium"),
                    "platform": "cross-platform",
                })
        signal["signal_direction"] = "opportunity" if arbs else "neutral"

    elif sid == "cross_pollinator":
        health = data.get("mycelium_health", {})
        score = health.get("score", 0)
        recs = data.get("transfer_recommendations", [])
        total_val = data.get("total_portfolio_value", 0)
        signal["signal_strength"] = min(70, score)
        signal["signal_direction"] = "opportunity" if recs else "neutral"
        for r in (recs if isinstance(recs, list) else [])[:3]:
            signal["opportunities"].append({
                "type": "capital_routing",
                "recommendation": r.get("action", r.get("description", "rebalance")),
                "platform": r.get("platform", "multi"),
            })

    elif sid == "turbo":
        daily_opps = data.get("daily_opps", 0)
        trades = data.get("trades_placed", 0)
        balance = data.get("balance", 0) or 0
        deposit = data.get("deposit_detected", False)
        signal["signal_strength"] = min(85, daily_opps * 10 + (20 if deposit else 0))
        signal["signal_direction"] = "opportunity" if daily_opps > 0 else "neutral"
        if daily_opps > 0:
            signal["opportunities"].append({
                "type": "turbo_daily",
                "daily_opps": daily_opps,
                "balance": balance,
                "deposit_detected": deposit,
                "platform": "kalshi",
            })

    elif sid == "alpaca":
        opps = data.get("opportunities_found", 0)
        market_open = data.get("market_open", False)
        portfolio = data.get("portfolio_value", 0)
        mode = data.get("mode", "unknown")
        signal["signal_strength"] = min(75, opps * 15 + (20 if market_open else 0))
        signal["signal_direction"] = "opportunity" if opps > 0 and market_open else "neutral"
        if opps > 0:
            signal["opportunities"].append({
                "type": "stock_etf_crypto",
                "opportunities": opps,
                "market_open": market_open,
                "portfolio_value": portfolio,
                "mode": mode,
                "platform": "alpaca",
            })

    elif sid == "trade_ledger":
        entries = data.get("entries", data.get("trades", []))
        if isinstance(entries, list):
            recent = [e for e in entries if _age_minutes(
                e.get("timestamp", e.get("recorded_at", "")), now
            ) is not None and _age_minutes(
                e.get("timestamp", e.get("recorded_at", "")), now
            ) < 120]
            win_rate = 0
            if recent:
                wins = sum(1 for e in recent if e.get("profit", e.get("expected_profit", 0)) > 0)
                win_rate = wins / len(recent) * 100
            signal["signal_strength"] = min(60, len(recent) * 10)
            signal["signal_direction"] = "bullish" if win_rate > 60 else ("bearish" if win_rate < 40 else "neutral")

    elif sid == "compound_tracker":
        total_compound = data.get("total_compounded", data.get("compound_total", 0))
        streak = data.get("compound_streak", data.get("streak", 0))
        signal["signal_strength"] = min(50, streak * 10 + (20 if total_compound else 0))
        signal["signal_direction"] = "bullish" if streak > 2 else "neutral"

    elif sid == "flywheel":
        momentum = data.get("momentum", data.get("flywheel_momentum", 0))
        revenue = data.get("total_revenue", data.get("revenue_30d", 0))
        signal["signal_strength"] = min(50, int(momentum * 10) if isinstance(momentum, (int, float)) else 0)
        signal["signal_direction"] = "bullish" if revenue else "neutral"

    elif sid == "ai_cost":
        profit = data.get("net_profit", data.get("profit", 0)) or 0
        cost = data.get("total_cost", data.get("cost_30d", 0)) or 0
        ratio = (profit / cost * 100) if cost > 0 else 0
        signal["signal_strength"] = min(40, int(ratio))
        signal["signal_direction"] = "bullish" if profit > 0 else ("bearish" if cost > profit else "neutral")

    elif sid == "metabolism":
        rev_velocity = data.get("revenue_velocity", 0) or 0
        eco_health = data.get("ecosystem_health", 0) or 0
        circuit = data.get("circuit_status", "open")
        metabolism = data.get("metabolism", {})
        amplification = metabolism.get("circular_amplification", 1.0) or 1.0
        self_funding = metabolism.get("self_funding_ratio", 0) or 0
        # Strength from ecosystem health + self-funding progress
        strength = min(80, int(eco_health * 0.5 + min(self_funding, 2.0) * 20))
        signal["signal_strength"] = strength
        signal["signal_direction"] = "bullish" if circuit == "closed" and eco_health > 40 else (
            "opportunity" if eco_health > 20 else "neutral"
        )
        if rev_velocity > 0 or eco_health > 0:
            signal["opportunities"].append({
                "type": "metabolism_circular",
                "revenue_velocity_hr": rev_velocity,
                "ecosystem_health": eco_health,
                "circuit_status": circuit,
                "amplification": amplification,
                "platform": "solarpunk",
            })

    elif sid == "global_markets":
        cross = data.get("cross_market", data.get("cross_platform", {}))
        regime = cross.get("regime", "NEUTRAL")
        regime_score = cross.get("regime_score", 0)
        total_opps = len(data.get("ranked_opportunities", []))
        total_cap = cross.get("total_visible_capital", 0)
        strength = min(90, abs(regime_score) * 2 + total_opps * 2)
        signal["signal_strength"] = int(strength)
        signal["signal_direction"] = "bullish" if regime == "RISK_ON" else (
            "bearish" if regime == "RISK_OFF" else "opportunity" if total_opps > 5 else "neutral"
        )
        recs = cross.get("recommendations", [])
        for r in recs[:3]:
            signal["opportunities"].append({
                "type": "global_market_deploy",
                "action": r.get("action", ""),
                "platform": r.get("platform", "multi"),
                "capital": r.get("capital", ""),
                "regime": regime,
            })

    elif sid == "reflex_arc":
        # Reflex fire rate and response time as system health signals
        last_cycle = data.get("last_cycle", {})
        total_fires = data.get("total_fires", 0)
        total_checks = data.get("total_checks", 0)
        fired_this_cycle = last_cycle.get("fired", 0)
        arc_ms = last_cycle.get("arc_response_ms", 0)
        fire_counts = data.get("fire_counts", {})

        # High fire rate = system is actively responding = "opportunity" signal
        # Very high fire rate = too many triggers = potential stress
        fire_rate = (total_fires / max(total_checks, 1)) * 100 if total_checks else 0
        signal["signal_strength"] = min(60, int(fire_rate * 3 + (10 if fired_this_cycle > 0 else 0)))
        signal["signal_direction"] = "opportunity" if 5 < fire_rate < 50 else (
            "bearish" if fire_rate >= 50 else "neutral"
        )

        # Report the hottest reflex as an opportunity signal
        if fire_counts:
            hottest = max(fire_counts, key=fire_counts.get)
            signal["opportunities"].append({
                "type": "reflex_activity",
                "hottest_reflex": hottest,
                "fire_count": fire_counts[hottest],
                "arc_response_ms": arc_ms,
                "fire_rate_pct": round(fire_rate, 1),
                "platform": "solarpunk",
            })

    elif sid == "proprioception":
        # Growth trajectory and system self-awareness as meta-signal
        engine_count = data.get("engine_count", 0)
        data_file_count = data.get("data_file_count", 0)
        evolution_label = data.get("evolution_label", "")
        coordination = data.get("coordination_score", 0)
        trajectory = data.get("growth_trajectory", {})
        portfolio_7d = trajectory.get("portfolio_7d", 0)
        engines_7d = trajectory.get("engines_7d", 0)

        # Strength from coordination + evolution rate
        evo_bonus = {"HIGH": 30, "MEDIUM": 15, "LOW": 0}.get(evolution_label, 5)
        strength = min(50, int(coordination * 0.3 + evo_bonus + min(engine_count, 500) * 0.02))
        signal["signal_strength"] = strength
        signal["signal_direction"] = "bullish" if evolution_label in ("HIGH", "MEDIUM") else (
            "bearish" if evolution_label == "LOW" else "neutral"
        )

        if engine_count > 0:
            signal["opportunities"].append({
                "type": "system_growth",
                "engine_count": engine_count,
                "data_files": data_file_count,
                "evolution": evolution_label,
                "coordination": coordination,
                "projected_engines_7d": engines_7d,
                "projected_portfolio_7d": portfolio_7d,
                "platform": "solarpunk",
            })

    elif sid == "neural_cortex":
        # The brain's strategic output feeds back into signal aggregation
        strategy = data.get("strategy", {})
        intel = data.get("intelligence_summary", {})
        confidence = data.get("decision_confidence", 0)
        risk = strategy.get("risk_posture", "moderate")
        growth_pri = strategy.get("growth_priority", "")
        top_action = strategy.get("top_action", {})
        health_score = data.get("system_health", {}).get("overall_score", 0)

        # Strength from confidence + health
        strength = min(85, int(confidence * 0.5 + health_score * 0.3))
        signal["signal_strength"] = strength
        signal["signal_direction"] = (
            "bullish" if risk == "aggressive" else
            "bearish" if risk == "conservative" else
            "opportunity" if confidence > 60 else "neutral"
        )

        if top_action:
            signal["opportunities"].append({
                "type": "strategic_decision",
                "action": top_action.get("description", ""),
                "target_engine": top_action.get("engine", ""),
                "urgency": top_action.get("urgency", 0),
                "risk_posture": risk,
                "growth_priority": growth_pri,
                "confidence": confidence,
                "platform": "solarpunk",
            })

    elif sid == "executive_fn":
        # Execution feedback: did the motor cortex succeed?
        last_exec = data.get("last_execution", {})
        stats = data.get("stats", {})
        total_execs = stats.get("total_executions", 0)
        success_rate = stats.get("success_rate_pct", 0)
        last_result = last_exec.get("result", "")

        signal["signal_strength"] = min(50, int(success_rate * 0.3 + total_execs * 0.5))
        signal["signal_direction"] = (
            "bullish" if success_rate > 80 else
            "bearish" if success_rate < 40 and total_execs > 3 else "neutral"
        )

        if total_execs > 0:
            signal["opportunities"].append({
                "type": "execution_feedback",
                "last_engine": last_exec.get("target_engine", "?"),
                "last_result": last_result,
                "success_rate": success_rate,
                "total_executions": total_execs,
                "platform": "solarpunk",
            })

    return signal


# ---------------------------------------------------------------------------
# Composite signal computation
# ---------------------------------------------------------------------------
def _compute_composite(signals):
    """
    Compute the composite signal from all individual signals.
    Returns a dict with weighted average strength, dominant direction,
    conviction score, and urgency.
    """
    total_weight = 0.0
    weighted_strength_sum = 0.0
    direction_votes = {"bullish": 0, "bearish": 0, "neutral": 0, "opportunity": 0}
    active_signals = 0
    agreeing_signals = 0

    for s in signals:
        w = s["effective_weight"]
        strength = s["signal_strength"]
        direction = s["signal_direction"]

        if s["has_data"] and strength > 0:
            active_signals += 1
            weighted_strength_sum += strength * w
            total_weight += w
            direction_votes[direction] = direction_votes.get(direction, 0) + w

    # Weighted average signal strength
    composite_strength = round(weighted_strength_sum / total_weight, 1) if total_weight > 0 else 0

    # Dominant direction (highest weighted vote)
    dominant_direction = max(direction_votes, key=direction_votes.get) if any(direction_votes.values()) else "neutral"
    dominant_weight = direction_votes.get(dominant_direction, 0)
    total_direction_weight = sum(direction_votes.values()) or 1

    # Conviction: what fraction of weighted signals agree on the dominant direction
    conviction = round(dominant_weight / total_direction_weight * 100, 1)

    # Count how many individual signals point the same way
    same_direction_count = sum(
        1 for s in signals
        if s["has_data"] and s["signal_strength"] > 0 and s["signal_direction"] == dominant_direction
    )
    agreeing_signals = same_direction_count

    # Urgency: factors in time-sensitive opportunities (arbitrage, daily contracts, market hours)
    urgency = 0
    for s in signals:
        for opp in s.get("opportunities", []):
            opp_type = opp.get("type", "")
            if opp_type == "arbitrage":
                urgency += 30  # Arb windows close fast
            elif opp_type == "turbo_daily":
                urgency += 25  # Daily contracts expire
            elif opp_type == "stock_etf_crypto" and opp.get("market_open"):
                urgency += 20  # Market hours limited
            elif opp_type in ("kalshi_market", "polymarket_edge"):
                urgency += 15  # Prediction market edges decay
            elif opp_type == "capital_routing":
                urgency += 10  # Less urgent but still actionable
    urgency = min(100, urgency)

    return {
        "composite_strength": composite_strength,
        "dominant_direction": dominant_direction,
        "direction_votes": {k: round(v, 2) for k, v in direction_votes.items()},
        "conviction_score": conviction,
        "agreeing_signals": agreeing_signals,
        "active_signals": active_signals,
        "total_signals": len(signals),
        "urgency": urgency,
    }


# ---------------------------------------------------------------------------
# Opportunity ranking & convergence detection
# ---------------------------------------------------------------------------
def _rank_opportunities(signals):
    """
    Collect all opportunities across all signal sources, rank them by
    a combined score of signal strength, freshness, and edge size.
    """
    all_opps = []
    for s in signals:
        for opp in s.get("opportunities", []):
            score = s["signal_strength"] * s["freshness_weight"]
            edge = opp.get("edge", opp.get("spread", opp.get("edge_pct", 0))) or 0
            if isinstance(edge, (int, float)):
                score += edge * 10
            all_opps.append({
                **opp,
                "source": s["source_id"],
                "source_label": s["label"],
                "signal_strength": s["signal_strength"],
                "freshness": s["freshness"],
                "composite_score": round(score, 1),
            })
    all_opps.sort(key=lambda x: x["composite_score"], reverse=True)
    return all_opps[:20]  # Top 20


def _detect_convergence(signals):
    """
    Detect when multiple sources are pointing at the SAME opportunity.
    Convergence = higher confidence. If 3+ sources see the same thing,
    it's a strong signal.
    """
    platform_signals = {}
    for s in signals:
        if s["has_data"] and s["signal_strength"] > 10:
            for opp in s.get("opportunities", []):
                platform = opp.get("platform", "unknown")
                if platform not in platform_signals:
                    platform_signals[platform] = []
                platform_signals[platform].append({
                    "source": s["source_id"],
                    "strength": s["signal_strength"],
                    "direction": s["signal_direction"],
                    "type": opp.get("type", "unknown"),
                })

    convergences = []
    for platform, sigs in platform_signals.items():
        if len(sigs) >= 2:
            avg_strength = sum(s["strength"] for s in sigs) / len(sigs)
            directions = [s["direction"] for s in sigs]
            dominant = max(set(directions), key=directions.count)
            agreement = directions.count(dominant) / len(directions) * 100
            convergences.append({
                "platform": platform,
                "sources_count": len(sigs),
                "sources": [s["source"] for s in sigs],
                "avg_strength": round(avg_strength, 1),
                "dominant_direction": dominant,
                "agreement_pct": round(agreement, 1),
            })
    convergences.sort(key=lambda x: x["sources_count"] * x["avg_strength"], reverse=True)
    return convergences


# ---------------------------------------------------------------------------
# System heartbeat
# ---------------------------------------------------------------------------
def _compute_heartbeat(signals):
    """
    Count alive / stale / dead sources.
    Calculate neural connectivity score.
    """
    alive = [s for s in signals if s["freshness"] == "alive"]
    stale = [s for s in signals if s["freshness"] == "stale"]
    dead = [s for s in signals if s["freshness"] == "dead"]

    total = len(signals)
    alive_count = len(alive)
    stale_count = len(stale)
    dead_count = len(dead)

    # Neural connectivity: alive sources with data and nonzero signal
    connected = sum(1 for s in signals if s["has_data"] and s["signal_strength"] > 0)
    connectivity = round(connected / total * 100, 1) if total > 0 else 0

    return {
        "alive": alive_count,
        "stale": stale_count,
        "dead": dead_count,
        "total_sources": total,
        "alive_sources": [s["source_id"] for s in alive],
        "stale_sources": [s["source_id"] for s in stale],
        "dead_sources": [s["source_id"] for s in dead],
        "neural_connectivity": connectivity,
        "connected_sources": connected,
    }


# ---------------------------------------------------------------------------
# Console output
# ---------------------------------------------------------------------------
def _print_summary(state):
    """Print a formatted summary of the signal mesh status."""
    composite = state.get("composite_signal", {})
    heartbeat = state.get("heartbeat", {})
    ranked = state.get("ranked_opportunities", [])
    convergences = state.get("convergences", [])

    print("\n" + "=" * 60)
    print("  SIGNAL MESH -- Central Nervous System Signal Bus")
    print("=" * 60)

    # Heartbeat
    print(f"\n  HEARTBEAT:")
    print(f"    Sources: {heartbeat.get('alive', 0)} alive / "
          f"{heartbeat.get('stale', 0)} stale / "
          f"{heartbeat.get('dead', 0)} dead")
    print(f"    Neural connectivity: {heartbeat.get('neural_connectivity', 0)}%")

    if heartbeat.get("dead_sources"):
        print(f"    Dead: {', '.join(heartbeat['dead_sources'])}")

    # Composite signal
    print(f"\n  COMPOSITE SIGNAL:")
    print(f"    Strength: {composite.get('composite_strength', 0)}/100")
    print(f"    Direction: {composite.get('dominant_direction', 'neutral').upper()}")
    print(f"    Conviction: {composite.get('conviction_score', 0)}% "
          f"({composite.get('agreeing_signals', 0)}/{composite.get('active_signals', 0)} agree)")
    print(f"    Urgency: {composite.get('urgency', 0)}/100")

    # Top opportunities
    if ranked:
        print(f"\n  TOP OPPORTUNITIES ({len(ranked)}):")
        for i, opp in enumerate(ranked[:5], 1):
            market = opp.get("market", opp.get("pair", opp.get("action", opp.get("type", "?"))))
            platform = opp.get("platform", "?")
            score = opp.get("composite_score", 0)
            print(f"    {i}. [{platform}] {market} (score: {score})")

    # Convergence
    if convergences:
        print(f"\n  CONVERGENCE ({len(convergences)} clusters):")
        for c in convergences[:3]:
            print(f"    {c['platform']}: {c['sources_count']} sources agree "
                  f"({c['agreement_pct']}% {c['dominant_direction']})")

    # Ethics lock
    print(f"\n  ETHICS: 99% mutual aid / 1% node fuel")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def run():
    """
    Read all signal sources, normalize, weight, compute composite,
    detect convergence, print summary, save state, return state dict.
    """
    now = datetime.now(timezone.utc)
    signals = []

    # 1. Read all signal sources
    for source_def in SIGNAL_SOURCES:
        filepath = DATA / source_def["file"]
        data = _load(filepath, {})
        sig = _extract_signal(source_def, data, now)
        signals.append(sig)

    # 2. Compute composite signal
    composite = _compute_composite(signals)

    # 3. Rank opportunities across ALL platforms
    ranked_opps = _rank_opportunities(signals)

    # 4. Detect signal convergence
    convergences = _detect_convergence(signals)

    # 5. Compute system heartbeat
    heartbeat = _compute_heartbeat(signals)

    # 6. Build state
    state = {
        "timestamp": now.isoformat(),
        "engine": "SIGNAL_MESH",
        "version": 1,
        "ethics": "99% mutual aid / 1% node fuel",
        "composite_signal": composite,
        "heartbeat": heartbeat,
        "ranked_opportunities": ranked_opps,
        "convergences": convergences,
        "individual_signals": signals,
        "summary": {
            "best_opportunity": ranked_opps[0] if ranked_opps else None,
            "total_opportunities": len(ranked_opps),
            "neural_connectivity": heartbeat["neural_connectivity"],
            "composite_strength": composite["composite_strength"],
            "dominant_direction": composite["dominant_direction"],
            "conviction": composite["conviction_score"],
            "urgency": composite["urgency"],
        },
    }

    # 7. Print formatted summary
    _print_summary(state)

    # 8. Save state
    _save(DATA / "signal_mesh_state.json", state)

    # 9. Broadcast to synaptic bus -- every engine sees this INSTANTLY
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_batch("SIGNAL_MESH", {
            "composite_strength": composite["composite_strength"],
            "dominant_direction": composite["dominant_direction"],
            "conviction_score": composite["conviction_score"],
            "urgency": composite["urgency"],
            "neural_connectivity": heartbeat["neural_connectivity"],
            "alive_sources": heartbeat["alive"],
            "total_opportunities": len(ranked_opps),
            "best_opportunity": ranked_opps[0]["description"] if ranked_opps else "none",
            "status": "active",
            "signal_direction": composite["dominant_direction"],
        }, silent=False)
    except Exception:
        pass  # Bus not available -- degrade gracefully

    return state


if __name__ == "__main__":
    run()
