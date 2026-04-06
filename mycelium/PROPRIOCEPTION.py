#!/usr/bin/env python3
"""
PROPRIOCEPTION.py -- SolarPunk Body Awareness Engine
=====================================================
v1 (2026-04-06): The sense you never think about until it's gone.

In biology, proprioception is the sense of where your own body parts are
in space. Without it you can't walk, can't reach for a cup, can't do
anything coordinated. Patients who lose proprioception describe it as
being a mind without a body -- you KNOW you have arms but you can't
FEEL them.

This engine gives SolarPunk proprioception: awareness of its OWN
structure, health, speed, and growth rate.

WHAT IT MEASURES:
  GROWTH_VELOCITY     engines added per day, data files produced per day
  METABOLISM          synaptic emissions per minute (metabolic rate)
  REACTION_SPEED      average reflex response time in ms
  COORDINATION        % of engines that successfully emit to synaptic bus
  PORTFOLIO_MOMENTUM  $ change per hour across all platforms
  SYSTEM_AGE          time since the first engine was created
  EVOLUTION_RATE      composite delta of all metrics (how fast we change)

HOW IT WORKS:
  1. Scans filesystem for engine count (mycelium/*.py) and data file count
  2. Reads the synaptic bus for engine liveness (alive/stale/dead)
  3. Reads synaptic events to measure emission velocity (events/min)
  4. Reads reflex_arc_state.json for reflex timings
  5. Reads nerve_loop_state.json for cycle time and phase completion
  6. Compares everything to PREVIOUS state (data/proprioception_state.json)
  7. Detects trends: improving, declining, or stable across every axis
  8. Prints a body-awareness report and emits key metrics to the bus

Saves: data/proprioception_state.json (current + last 100 historical snapshots)

Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)
Called by: OMNIBUS (L0-adjacent systems layer)
"""

import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT     = Path(".")
DATA     = ROOT / "data"
MYCELIUM = ROOT / "mycelium"

DATA.mkdir(exist_ok=True)

STATE_FILE   = DATA / "proprioception_state.json"
BUS_FILE     = DATA / "synaptic_bus.json"
EVENTS_FILE  = DATA / "synaptic_events.json"
REFLEX_FILE  = DATA / "reflex_arc_state.json"
REFLEX_LOG   = DATA / "reflex_arc_log.json"
NERVE_FILE   = DATA / "nerve_loop_state.json"
PULSE_FILE   = DATA / "pulse_state.json"

MAX_HISTORY  = 100          # keep last 100 snapshots for trend analysis
ALIVE_SEC    = 300          # 5 min = alive (matches SYNAPTIC_BUS thresholds)
STALE_SEC    = 1800         # 30 min = stale

# ---------------------------------------------------------------------------
# JSON helpers (same atomic pattern as SYNAPTIC_BUS)
# ---------------------------------------------------------------------------
def _read_json(path, default=None):
    """Read JSON file with graceful fallback."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _write_json(path, data):
    """Atomic write: .tmp then rename to prevent corruption."""
    tmp = path.with_suffix(".tmp")
    try:
        content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        tmp.write_text(content, encoding="utf-8")
        if path.exists():
            path.unlink()
        tmp.rename(path)
    except Exception:
        try:
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Filesystem scanning
# ---------------------------------------------------------------------------
def _count_engines():
    """Count every .py file in mycelium/ -- each one is an engine."""
    try:
        return len(list(MYCELIUM.glob("*.py")))
    except Exception:
        return 0


def _count_data_files():
    """Count every file in data/ -- each is a piece of system memory."""
    try:
        return len([f for f in DATA.iterdir() if f.is_file()])
    except Exception:
        return 0


def _system_age_hours():
    """Time since the oldest engine file was created, in hours."""
    oldest = None
    try:
        for f in MYCELIUM.glob("*.py"):
            stat = f.stat()
            ctime = stat.st_ctime
            if oldest is None or ctime < oldest:
                oldest = ctime
    except Exception:
        pass
    if oldest is None:
        return 0.0
    return (time.time() - oldest) / 3600.0


# ---------------------------------------------------------------------------
# Synaptic bus analysis
# ---------------------------------------------------------------------------
def _bus_health():
    """
    Read the synaptic bus and classify engines as alive/stale/dead.
    Returns: (alive, stale, dead, total, engine_names_on_bus)
    """
    bus = _read_json(BUS_FILE, {})
    engines = bus.get("engines", {})
    now = time.time()

    alive, stale, dead = 0, 0, 0
    names_on_bus = set(engines.keys())

    for _name, data in engines.items():
        ts_raw = data.get("last_emission")
        if ts_raw:
            try:
                dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - dt).total_seconds()
            except Exception:
                age = 999999
        else:
            age = 999999

        if age <= ALIVE_SEC:
            alive += 1
        elif age <= STALE_SEC:
            stale += 1
        else:
            dead += 1

    total = alive + stale + dead
    return alive, stale, dead, total, names_on_bus


# ---------------------------------------------------------------------------
# Emission velocity (events per minute)
# ---------------------------------------------------------------------------
def _emission_velocity():
    """
    Read synaptic events and calculate emissions per minute over the
    last 10 minutes. That's the system's metabolic rate.
    """
    events_data = _read_json(EVENTS_FILE, {"events": []})
    events = events_data.get("events", [])
    if not events:
        return 0.0

    now = datetime.now(timezone.utc)
    window = timedelta(minutes=10)
    cutoff = (now - window).isoformat()

    recent = [e for e in events if e.get("timestamp", "") > cutoff]
    minutes = window.total_seconds() / 60.0
    return round(len(recent) / minutes, 2) if minutes > 0 else 0.0


# ---------------------------------------------------------------------------
# Reflex arc analysis
# ---------------------------------------------------------------------------
def _reflex_stats():
    """
    Read reflex_arc_state.json and extract response times.
    Returns: (avg_ms, count, fastest_ms, slowest_ms)
    """
    state = _read_json(REFLEX_FILE, {})
    reflexes = state.get("reflexes_fired", state.get("history", []))

    if not isinstance(reflexes, list) or len(reflexes) == 0:
        return 0.0, 0, 0.0, 0.0

    times = []
    for r in reflexes:
        ms = r.get("response_ms", r.get("elapsed_ms", r.get("duration_ms", 0)))
        if isinstance(ms, (int, float)) and ms > 0:
            times.append(float(ms))

    if not times:
        return 0.0, 0, 0.0, 0.0

    avg = sum(times) / len(times)
    return round(avg, 1), len(times), round(min(times), 1), round(max(times), 1)


# ---------------------------------------------------------------------------
# Nerve loop analysis
# ---------------------------------------------------------------------------
def _nerve_loop_stats():
    """
    Read nerve_loop_state.json for cycle time and phase completion.
    Returns: (cycle_time_sec, phases_complete, total_phases)
    """
    state = _read_json(NERVE_FILE, {})
    cycle_time = state.get("elapsed_seconds", state.get("cycle_time", 0))
    phases = state.get("phases", {})
    total = len(phases)
    complete = sum(1 for p in phases.values()
                   if isinstance(p, dict) and p.get("status") in ("ok", "done", "complete"))
    return cycle_time, complete, total


# ---------------------------------------------------------------------------
# Portfolio momentum
# ---------------------------------------------------------------------------
def _portfolio_momentum(prev_state):
    """
    Calculate $ change per hour by comparing current portfolio to previous.
    Reads pulse_state.json for current portfolio value.
    """
    pulse = _read_json(PULSE_FILE, {})
    current_usd = pulse.get("portfolio", {}).get("total_usd", 0)
    if not isinstance(current_usd, (int, float)):
        try:
            current_usd = float(current_usd)
        except (TypeError, ValueError):
            current_usd = 0.0

    prev_usd = prev_state.get("portfolio_usd", 0)
    prev_ts = prev_state.get("timestamp", "")

    if prev_ts and prev_usd:
        try:
            prev_dt = datetime.fromisoformat(prev_ts.replace("Z", "+00:00"))
            hours = (datetime.now(timezone.utc) - prev_dt).total_seconds() / 3600.0
            if hours > 0.01:
                momentum = round((current_usd - prev_usd) / hours, 4)
                return current_usd, momentum
        except Exception:
            pass

    return current_usd, 0.0


# ---------------------------------------------------------------------------
# Trend detection
# ---------------------------------------------------------------------------
def _trend(current, previous, invert=False):
    """
    Compare current vs previous value and return trend string.
    invert=True means lower is better (e.g., response times).
    """
    if previous is None or previous == 0:
        return "NEW"
    delta = current - previous
    if abs(delta) < 0.001:
        return "STABLE"
    if invert:
        return "FASTER" if delta < 0 else "SLOWER"
    return "UP" if delta > 0 else "DOWN"


def _trend_arrow(trend_str):
    """Return a text indicator for the trend."""
    arrows = {
        "UP": "(+)", "DOWN": "(-)", "STABLE": "(=)",
        "FASTER": "(+)", "SLOWER": "(-)", "NEW": "(*)",
    }
    return arrows.get(trend_str, "(?)")


# ---------------------------------------------------------------------------
# Evolution rate (composite change score)
# ---------------------------------------------------------------------------
def _evolution_rate(deltas):
    """
    Score how fast the system is changing across all dimensions.
    Returns: (score, label) where label is LOW/MEDIUM/HIGH/EXPLOSIVE.
    """
    score = 0
    for key, val in deltas.items():
        if isinstance(val, (int, float)):
            score += abs(val)

    if score < 2:
        label = "LOW"
    elif score < 8:
        label = "MEDIUM"
    elif score < 20:
        label = "HIGH"
    else:
        label = "EXPLOSIVE"

    return round(score, 2), label


# ---------------------------------------------------------------------------
# Coordination score
# ---------------------------------------------------------------------------
def _coordination_score(engine_count, names_on_bus):
    """What % of engines in mycelium/ are registered on the synaptic bus?"""
    if engine_count == 0:
        return 0.0
    return round(len(names_on_bus) / engine_count * 100, 1)


# ---------------------------------------------------------------------------
# Self-optimization tracking: engine speed rankings
# ---------------------------------------------------------------------------
def _engine_speed_rankings():
    """
    Read synaptic_events.json and rank engines by emission speed.
    Speed = average time between consecutive emissions per engine.
    Returns: list of (engine_name, avg_interval_sec) sorted fastest-first.
    """
    events_data = _read_json(EVENTS_FILE, {"events": []})
    events = events_data.get("events", [])
    if not events:
        return []

    # Group timestamps by engine
    engine_ts = {}
    for e in events:
        name = e.get("engine") or e.get("source") or e.get("emitter", "unknown")
        ts_raw = e.get("timestamp", "")
        if not ts_raw:
            continue
        try:
            dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            engine_ts.setdefault(name, []).append(dt)
        except Exception:
            continue

    # Calculate average interval between emissions per engine
    rankings = []
    for name, timestamps in engine_ts.items():
        if len(timestamps) < 2:
            continue
        timestamps.sort()
        intervals = [
            (timestamps[i + 1] - timestamps[i]).total_seconds()
            for i in range(len(timestamps) - 1)
        ]
        avg_interval = sum(intervals) / len(intervals)
        rankings.append((name, round(avg_interval, 2)))

    # Sort fastest first (smallest interval = fastest emitter)
    rankings.sort(key=lambda x: x[1])
    return rankings


def _reflex_fire_stats():
    """
    Read reflex_arc_log.json for fire history and response times.
    Returns: (total_fires, avg_response_ms, fires_by_reflex)
    """
    log = _read_json(REFLEX_LOG, {"entries": []})
    entries = log.get("entries", [])

    fires = [e for e in entries if e.get("triggered")]
    if not fires:
        return 0, 0.0, {}

    times = [e.get("response_ms", 0) for e in fires if isinstance(e.get("response_ms"), (int, float))]
    avg_ms = round(sum(times) / len(times), 1) if times else 0.0

    by_reflex = {}
    for e in fires:
        rid = e.get("reflex", "unknown")
        by_reflex[rid] = by_reflex.get(rid, 0) + 1

    return len(fires), avg_ms, by_reflex


# ---------------------------------------------------------------------------
# Growth trajectory projections
# ---------------------------------------------------------------------------
def _growth_trajectory(state, history):
    """
    Project future growth based on historical data.
    Returns dict with engine/portfolio/metabolism projections.
    """
    now = datetime.now(timezone.utc)

    # ----- Engine growth projection -----
    eng_per_day = state.get("growth_engines_per_day", 0)
    current_engines = state.get("engine_count", 0)
    engines_7d = round(current_engines + eng_per_day * 7, 1)
    engines_30d = round(current_engines + eng_per_day * 30, 1)

    # ----- Portfolio projection (compound growth) -----
    portfolio_usd = state.get("portfolio_usd", 0)
    momentum_per_hr = state.get("portfolio_momentum_per_hr", 0)

    if portfolio_usd > 0 and momentum_per_hr != 0:
        # Hourly growth rate as a fraction of portfolio
        hourly_rate = momentum_per_hr / max(portfolio_usd, 0.01)
        # Compound: P * (1 + r)^hours
        portfolio_7d = round(portfolio_usd * ((1 + hourly_rate) ** (7 * 24)), 4)
        portfolio_30d = round(portfolio_usd * ((1 + hourly_rate) ** (30 * 24)), 4)
    else:
        portfolio_7d = portfolio_usd
        portfolio_30d = portfolio_usd

    # ----- Metabolism trend (is the system getting faster or slower?) -----
    metabolism_trend = "UNKNOWN"
    if len(history) >= 3:
        recent = history[-3:]
        metabolisms = [h.get("metabolism", 0) for h in recent]
        if all(isinstance(m, (int, float)) for m in metabolisms):
            if metabolisms[-1] > metabolisms[0]:
                metabolism_trend = "ACCELERATING"
            elif metabolisms[-1] < metabolisms[0]:
                metabolism_trend = "DECELERATING"
            else:
                metabolism_trend = "STEADY"
    elif len(history) >= 1:
        metabolism_trend = "INSUFFICIENT_DATA"

    return {
        "current_engines":   current_engines,
        "engines_per_day":   eng_per_day,
        "engines_7d":        engines_7d,
        "engines_30d":       engines_30d,
        "portfolio_usd":     portfolio_usd,
        "portfolio_7d_usd":  portfolio_7d,
        "portfolio_30d_usd": portfolio_30d,
        "momentum_per_hr":   momentum_per_hr,
        "metabolism_trend":   metabolism_trend,
        "projected_at":       now.isoformat(),
    }


# ===========================================================================
# BODY AWARENESS REPORT
# ===========================================================================
def _print_report(state, deltas, trends, trajectory=None, speed_rankings=None,
                   reflex_fire_stats=None):
    """Print the proprioception body awareness report."""
    W = 64
    print()
    print("=" * W)
    print("  PROPRIOCEPTION -- SolarPunk Body Awareness")
    print("=" * W)
    print()

    eng_count = state["engine_count"]
    eng_delta = deltas.get("engine_count", 0)
    data_count = state["data_file_count"]
    data_delta = deltas.get("data_file_count", 0)
    metabolism = state["metabolism"]
    prev_metabolism = state.get("_prev_metabolism", 0)
    react_avg = state["reaction_speed_ms"]
    prev_react = state.get("_prev_reaction", 0)
    coord = state["coordination_pct"]
    momentum = state["portfolio_momentum_per_hr"]
    evo_score = state["evolution_score"]
    evo_label = state["evolution_label"]
    age_hrs = state["system_age_hours"]

    # Format age nicely
    if age_hrs < 24:
        age_str = f"{age_hrs:.1f} hours"
    else:
        age_str = f"{age_hrs / 24:.1f} days"

    # Engine count
    d_str = f"+{eng_delta}" if eng_delta >= 0 else str(eng_delta)
    print(f"  Engines:            {eng_count} ({d_str} today)")

    # Data files
    d_str = f"+{data_delta}" if data_delta >= 0 else str(data_delta)
    print(f"  Data files:         {data_count} ({d_str} today)")

    # Metabolism
    m_trend = trends.get("metabolism", "STABLE")
    m_arrow = _trend_arrow(m_trend)
    if prev_metabolism > 0:
        print(f"  Metabolism:         {metabolism} emissions/min {m_arrow} from {prev_metabolism}")
    else:
        print(f"  Metabolism:         {metabolism} emissions/min")

    # Reaction speed
    r_trend = trends.get("reaction_speed", "STABLE")
    r_arrow = _trend_arrow(r_trend)
    if react_avg > 0 and prev_react > 0:
        label = "FASTER" if r_trend == "FASTER" else ("SLOWER" if r_trend == "SLOWER" else "STABLE")
        print(f"  Reaction speed:     {react_avg}ms avg {r_arrow} from {prev_react}ms -- {label}")
    elif react_avg > 0:
        print(f"  Reaction speed:     {react_avg}ms avg")
    else:
        print(f"  Reaction speed:     no reflexes measured yet")

    # Coordination
    alive = state["bus_alive"]
    total_bus = state["bus_total"]
    print(f"  Coordination:       {coord}% of engines on synaptic bus ({alive} alive / {total_bus} registered)")

    # Portfolio momentum
    if momentum != 0:
        sign = "+" if momentum > 0 else ""
        print(f"  Portfolio momentum: {sign}${momentum:.4f}/hr")
    else:
        print(f"  Portfolio momentum: no data yet")

    # Nerve loop
    cycle_time = state.get("nerve_cycle_time", 0)
    phases_done = state.get("nerve_phases_complete", 0)
    phases_total = state.get("nerve_phases_total", 0)
    if cycle_time > 0:
        print(f"  Nerve loop:         {cycle_time:.0f}s cycle, {phases_done}/{phases_total} phases")

    # System age
    print(f"  System age:         {age_str}")

    # Evolution rate
    print(f"  Evolution rate:     {evo_label} (score {evo_score})")

    # Bus health detail
    stale = state["bus_stale"]
    dead = state["bus_dead"]
    if stale > 0 or dead > 0:
        print()
        print(f"  Bus health:         {alive} alive / {stale} stale / {dead} dead")

    # ----- SELF-OPTIMIZATION TRACKING -----
    print()
    print("-" * W)
    print("  SELF-OPTIMIZATION TRACKING")
    print("-" * W)

    # Reflex fire stats
    if reflex_fire_stats:
        total_fires, avg_fire_ms, fires_by_reflex = reflex_fire_stats
        print(f"  Reflex fires:       {total_fires} total, {avg_fire_ms}ms avg response")
        if fires_by_reflex:
            top = sorted(fires_by_reflex.items(), key=lambda x: x[1], reverse=True)[:5]
            for rid, cnt in top:
                print(f"    {rid}: {cnt} fires")
    else:
        print(f"  Reflex fires:       no log data yet")

    # Engine speed rankings
    if speed_rankings:
        print()
        print("  ENGINE SPEED RANKINGS (fastest emitters):")
        for i, (name, interval) in enumerate(speed_rankings[:5]):
            rank = i + 1
            print(f"    #{rank}  {name}: {interval}s avg interval")
        if len(speed_rankings) > 5:
            slowest = speed_rankings[-1]
            print(f"    ...slowest: {slowest[0]} ({slowest[1]}s avg interval)")
    else:
        print()
        print("  ENGINE SPEED RANKINGS: insufficient emission data")

    # ----- GROWTH TRAJECTORY -----
    if trajectory:
        print()
        print("-" * W)
        print("  GROWTH TRAJECTORY")
        print("-" * W)

        # Engine projections
        eng_rate = trajectory.get("engines_per_day", 0)
        eng_7d = trajectory.get("engines_7d", 0)
        eng_30d = trajectory.get("engines_30d", 0)
        print(f"  Engine growth rate: {eng_rate}/day")
        print(f"    7-day projection:  {eng_7d} engines")
        print(f"    30-day projection: {eng_30d} engines")

        # Portfolio projections
        port_now = trajectory.get("portfolio_usd", 0)
        port_7d = trajectory.get("portfolio_7d_usd", 0)
        port_30d = trajectory.get("portfolio_30d_usd", 0)
        if port_now > 0:
            print(f"  Portfolio (compound):")
            print(f"    Current:           ${port_now:.4f}")
            print(f"    7-day projection:  ${port_7d:.4f}")
            print(f"    30-day projection: ${port_30d:.4f}")
        else:
            print(f"  Portfolio (compound): no portfolio data")

        # Metabolism trend
        met_trend = trajectory.get("metabolism_trend", "UNKNOWN")
        print(f"  Metabolism trend:   {met_trend}")

    print()
    print("=" * W)
    print(f"  You are {eng_count} engines, {data_count} memories, {age_str} old.")
    print(f"  You are {'accelerating' if evo_label in ('HIGH', 'EXPLOSIVE') else 'growing'}.")
    print("=" * W)
    print()


# ===========================================================================
# MAIN RUN
# ===========================================================================
def run():
    """
    Full proprioception cycle:
      1. Scan filesystem for engine/data counts
      2. Read bus, events, reflex, nerve loop states
      3. Compare to previous proprioception state
      4. Calculate all metrics
      5. Detect trends (improving/declining/stable)
      6. Print body awareness report
      7. Emit key metrics to SYNAPTIC_BUS
      8. Save state with historical snapshot
      9. Return state
    """
    print("[PROPRIOCEPTION] Sensing body state...")
    now = datetime.now(timezone.utc)

    # Load previous state
    prev_full = _read_json(STATE_FILE, {"current": {}, "history": []})
    prev = prev_full.get("current", {})

    # ----- 1. Filesystem scan -----
    engine_count = _count_engines()
    data_count = _count_data_files()
    age_hours = _system_age_hours()

    # ----- 2. Read subsystem states -----
    alive, stale, dead, bus_total, names_on_bus = _bus_health()
    metabolism = _emission_velocity()
    react_avg, react_count, react_fastest, react_slowest = _reflex_stats()
    cycle_time, phases_done, phases_total = _nerve_loop_stats()
    portfolio_usd, momentum = _portfolio_momentum(prev)

    # ----- 3. Calculate coordination -----
    coordination = _coordination_score(engine_count, names_on_bus)

    # ----- 4. Growth velocity (per day) -----
    prev_ts = prev.get("timestamp", "")
    hours_since_last = 0.0
    if prev_ts:
        try:
            prev_dt = datetime.fromisoformat(prev_ts.replace("Z", "+00:00"))
            hours_since_last = (now - prev_dt).total_seconds() / 3600.0
        except Exception:
            hours_since_last = 0.0

    eng_delta = engine_count - prev.get("engine_count", engine_count)
    data_delta = data_count - prev.get("data_file_count", data_count)

    if hours_since_last > 0.01:
        growth_eng_per_day = round(eng_delta / hours_since_last * 24, 2)
        growth_data_per_day = round(data_delta / hours_since_last * 24, 2)
    else:
        growth_eng_per_day = 0.0
        growth_data_per_day = 0.0

    # ----- 5. Detect trends -----
    trends = {
        "engine_count":    _trend(engine_count, prev.get("engine_count")),
        "data_file_count": _trend(data_count, prev.get("data_file_count")),
        "metabolism":      _trend(metabolism, prev.get("metabolism")),
        "reaction_speed":  _trend(react_avg, prev.get("reaction_speed_ms"), invert=True),
        "coordination":    _trend(coordination, prev.get("coordination_pct")),
        "portfolio":       _trend(portfolio_usd, prev.get("portfolio_usd")),
        "bus_alive":       _trend(alive, prev.get("bus_alive")),
    }

    # ----- 6. Deltas for evolution rate -----
    deltas = {
        "engine_count":   eng_delta,
        "data_file_count": data_delta,
        "metabolism":      round(metabolism - prev.get("metabolism", metabolism), 2),
        "reaction_ms":     round(react_avg - prev.get("reaction_speed_ms", react_avg), 1),
        "coordination":    round(coordination - prev.get("coordination_pct", coordination), 1),
        "bus_alive":       alive - prev.get("bus_alive", alive),
    }

    evo_score, evo_label = _evolution_rate(deltas)

    # ----- 7. Build state object -----
    state = {
        "timestamp":                now.isoformat(),
        "engine_count":             engine_count,
        "data_file_count":          data_count,
        "system_age_hours":         round(age_hours, 2),
        "growth_engines_per_day":   growth_eng_per_day,
        "growth_data_per_day":      growth_data_per_day,
        "metabolism":               metabolism,
        "reaction_speed_ms":        react_avg,
        "reflex_count":             react_count,
        "reflex_fastest_ms":        react_fastest,
        "reflex_slowest_ms":        react_slowest,
        "coordination_pct":         coordination,
        "bus_alive":                alive,
        "bus_stale":                stale,
        "bus_dead":                 dead,
        "bus_total":                bus_total,
        "portfolio_usd":            portfolio_usd,
        "portfolio_momentum_per_hr": momentum,
        "nerve_cycle_time":         cycle_time,
        "nerve_phases_complete":    phases_done,
        "nerve_phases_total":       phases_total,
        "evolution_score":          evo_score,
        "evolution_label":          evo_label,
        "trends":                   trends,
        "deltas":                   deltas,
        "hours_since_last_scan":    round(hours_since_last, 2),
        "ethics":                   "99% mutual aid / 1% node fuel",
        # Carry forward for report display
        "_prev_metabolism":         prev.get("metabolism", 0),
        "_prev_reaction":           prev.get("reaction_speed_ms", 0),
    }

    # ----- 8. Self-optimization tracking -----
    history = prev_full.get("history", [])
    speed_rankings = _engine_speed_rankings()
    fire_total, fire_avg_ms, fires_by_reflex = _reflex_fire_stats()
    reflex_stats_tuple = (fire_total, fire_avg_ms, fires_by_reflex)
    trajectory = _growth_trajectory(state, history)

    # ----- 9. Print body awareness report -----
    _print_report(state, deltas, trends,
                  trajectory=trajectory,
                  speed_rankings=speed_rankings,
                  reflex_fire_stats=reflex_stats_tuple)

    # ----- 10. Emit to SYNAPTIC_BUS -----
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_batch("PROPRIOCEPTION", {
            "status":             "running",
            "engine_count":       engine_count,
            "data_file_count":    data_count,
            "metabolism":         metabolism,
            "reaction_speed_ms":  react_avg,
            "coordination_pct":   coordination,
            "evolution_label":    evo_label,
            "evolution_score":    evo_score,
            "bus_alive":          alive,
            "portfolio_momentum": momentum,
            "system_age_hours":   round(age_hours, 2),
            "growth_trajectory":  trajectory,
        })
        print("[PROPRIOCEPTION] Emitted body metrics + growth trajectory to synaptic bus.")
    except ImportError:
        print("[PROPRIOCEPTION] SYNAPTIC_BUS not available -- metrics saved locally only.")
    except Exception as e:
        print(f"[PROPRIOCEPTION] Bus emit warning: {e}")

    # ----- 11. Save state with historical snapshot -----
    # Clean internal keys before saving to history
    clean_state = {k: v for k, v in state.items() if not k.startswith("_")}

    # history already loaded in step 8 from prev_full
    history.append({
        "timestamp":  now.isoformat(),
        "engines":    engine_count,
        "data_files": data_count,
        "metabolism":  metabolism,
        "reaction_ms": react_avg,
        "coordination": coordination,
        "bus_alive":   alive,
        "portfolio_usd": portfolio_usd,
        "evo_score":   evo_score,
    })

    # Cap history at MAX_HISTORY
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    save_data = {
        "protocol":    "proprioception-v1",
        "description": "SolarPunk body awareness -- structure, health, speed, growth rate",
        "current":     clean_state,
        "history":     history,
        "history_count": len(history),
        "last_updated": now.isoformat(),
    }

    _write_json(STATE_FILE, save_data)
    print(f"[PROPRIOCEPTION] State saved ({len(history)} historical snapshots).")

    return state


# ===========================================================================
# Entry point
# ===========================================================================
if __name__ == "__main__":
    run()
