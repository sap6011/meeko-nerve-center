#!/usr/bin/env python3
"""
SYNAPTIC_BUS.py -- Real-time shared consciousness for all engines
================================================================
v1 (2026-04-06): The difference between AI and a human brain.

THE PROBLEM:
  Sequential pipeline: Engine A runs, saves file, Engine B reads file.
  That's a worm brain. Each neuron only knows what the LAST one told it.

THE SOLUTION:
  A shared synaptic bus where EVERY engine broadcasts its state changes
  in real-time and EVERY other engine can sense them SIMULTANEOUSLY.
  Not sequential. Not polling. Simultaneous awareness.

  In neuroscience, this is called a "global workspace" -- a shared
  neural bus where information from specialized processors becomes
  available to ALL processors at once. That's consciousness.

HOW IT WORKS:
  1. EMIT: Any engine calls `emit("TURBO_TRADER", "balance", 0.84)`
     and that fact is INSTANTLY available to every other engine.
  2. SENSE: Any engine calls `sense()` to see the ENTIRE system state,
     or `sense("TURBO_TRADER")` for one engine's state.
  3. EVENTS: Every emission is logged to the event stream. Engines can
     subscribe to specific event types (balance_changed, trade_placed, etc.)
  4. CONVERGENCE: The bus detects when multiple engines are signaling
     the same thing (e.g., "bullish on BTC") and amplifies that signal.
  5. ATTENTION: Like the brain's attention mechanism, the bus tracks
     which signals are being read most (demand) and prioritizes them.

ARCHITECTURE:
  Single-file atomic state: data/synaptic_bus.json
  Event stream:             data/synaptic_events.json (rolling 500 events)
  File-locked writes prevent corruption from concurrent engines.

USAGE IN ANY ENGINE:
  from SYNAPTIC_BUS import emit, sense, pulse, on_change

  # Broadcast your state
  emit("MY_ENGINE", "status", "running")
  emit("MY_ENGINE", "balance", 42.50)
  emit("MY_ENGINE", "signal", {"direction": "bullish", "strength": 80})

  # Read everyone's state at once
  world = sense()            # Full system state
  turbo = sense("TURBO")     # Just TURBO's state

  # React to changes
  changes = on_change("TURBO_TRADER")  # What changed since last read?

  # System pulse (how alive is the mesh?)
  health = pulse()           # {alive: 8, total: 11, connectivity: 73%}

Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)
Called by: Every engine in the system (imported as a shared module)
"""

import json
import os
import time
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from threading import Lock

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA = Path("data")
DATA.mkdir(exist_ok=True)

BUS_FILE = DATA / "synaptic_bus.json"
EVENTS_FILE = DATA / "synaptic_events.json"
ATTENTION_FILE = DATA / "synaptic_attention.json"

MAX_EVENTS = 500           # Rolling event window
ALIVE_THRESHOLD_SEC = 300  # 5 min = alive
STALE_THRESHOLD_SEC = 1800 # 30 min = stale
EVENT_TTL_HOURS = 12       # Events older than this are pruned

# Process-level lock for thread safety within one process
_lock = Lock()

# In-memory cache (avoids file reads on every sense() call)
_cache = {"state": None, "hash": None, "loaded_at": 0}
_CACHE_TTL_SEC = 2  # Re-read file at most every 2 seconds


# ---------------------------------------------------------------------------
# Core I/O (atomic, locked)
# ---------------------------------------------------------------------------
def _read_json(path, default=None):
    """Read JSON with fallback."""
    try:
        raw = path.read_text(encoding="utf-8")
        return json.loads(raw)
    except Exception:
        return default if default is not None else {}


def _write_json(path, data):
    """Atomic write: write to .tmp then rename to prevent corruption."""
    tmp = path.with_suffix(".tmp")
    try:
        content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        tmp.write_text(content, encoding="utf-8")
        # Atomic rename (on Windows, need to remove target first)
        if path.exists():
            path.unlink()
        tmp.rename(path)
    except Exception:
        # Fallback: direct write
        try:
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8"
            )
        except Exception:
            pass
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass


def _content_hash(data):
    """Quick hash for change detection."""
    return hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# BUS STATE
# ---------------------------------------------------------------------------
def _load_bus():
    """Load the full bus state, using cache if fresh."""
    now = time.time()
    if _cache["state"] is not None and (now - _cache["loaded_at"]) < _CACHE_TTL_SEC:
        return _cache["state"]

    state = _read_json(BUS_FILE, {
        "protocol": "synaptic-bus-v1",
        "created": datetime.now(timezone.utc).isoformat(),
        "engines": {},
        "convergence": {},
        "meta": {"total_emissions": 0, "last_emission": None},
    })
    _cache["state"] = state
    _cache["hash"] = _content_hash(state)
    _cache["loaded_at"] = now
    return state


def _save_bus(state):
    """Save bus state and invalidate cache."""
    _write_json(BUS_FILE, state)
    _cache["state"] = state
    _cache["hash"] = _content_hash(state)
    _cache["loaded_at"] = time.time()


# ---------------------------------------------------------------------------
# EVENT STREAM
# ---------------------------------------------------------------------------
def _log_event(engine, key, value, old_value=None):
    """Log a synaptic event to the rolling event stream."""
    events = _read_json(EVENTS_FILE, {"events": []})
    event_list = events.get("events", [])

    now = datetime.now(timezone.utc)
    event = {
        "timestamp": now.isoformat(),
        "engine": engine,
        "key": key,
        "value": _summarize(value),
        "changed": old_value is not None and old_value != value,
        "epoch": time.time(),
    }
    event_list.append(event)

    # Prune old events
    cutoff = (now - timedelta(hours=EVENT_TTL_HOURS)).isoformat()
    event_list = [e for e in event_list if e.get("timestamp", "") > cutoff]

    # Cap at MAX_EVENTS
    if len(event_list) > MAX_EVENTS:
        event_list = event_list[-MAX_EVENTS:]

    events["events"] = event_list
    events["total_logged"] = events.get("total_logged", 0) + 1
    events["last_event"] = now.isoformat()

    _write_json(EVENTS_FILE, events)


def _summarize(value):
    """Create a compact summary of a value for the event log."""
    if isinstance(value, (int, float, bool, str)):
        return value
    if isinstance(value, dict):
        # Summarize dicts to key count + first few keys
        keys = list(value.keys())[:5]
        return {"_type": "dict", "_keys": len(value), "_sample": keys}
    if isinstance(value, list):
        return {"_type": "list", "_len": len(value)}
    return str(value)[:100]


# ---------------------------------------------------------------------------
# ATTENTION TRACKING
# ---------------------------------------------------------------------------
def _track_attention(engine_name=None):
    """Track what engines are being sensed (read) most often."""
    attention = _read_json(ATTENTION_FILE, {"reads": {}, "total_reads": 0})
    key = engine_name or "__ALL__"
    attention["reads"][key] = attention["reads"].get(key, 0) + 1
    attention["total_reads"] = attention.get("total_reads", 0) + 1
    attention["last_read"] = datetime.now(timezone.utc).isoformat()

    # Keep only top 50 tracked engines
    if len(attention["reads"]) > 50:
        sorted_reads = sorted(attention["reads"].items(), key=lambda x: x[1], reverse=True)
        attention["reads"] = dict(sorted_reads[:50])

    _write_json(ATTENTION_FILE, attention)


# ---------------------------------------------------------------------------
# CONVERGENCE DETECTION
# ---------------------------------------------------------------------------
def _detect_convergence(state):
    """
    Detect when multiple engines are signaling the same thing.
    Like neurons firing in synchrony -- that's what creates conscious thought.
    """
    convergence = {
        "directions": {},
        "platforms": {},
        "themes": [],
        "sync_score": 0,
    }

    direction_counts = {}
    platform_mentions = {}
    balance_signals = []

    engines = state.get("engines", {})
    for eng_name, eng_data in engines.items():
        props = eng_data.get("properties", {})

        # Direction convergence
        direction = props.get("signal_direction", props.get("direction", ""))
        if direction and direction != "neutral":
            direction_counts[direction] = direction_counts.get(direction, 0) + 1

        # Platform convergence
        platform = props.get("platform", "")
        if platform:
            platform_mentions[platform] = platform_mentions.get(platform, 0) + 1

        # Balance awareness
        balance = props.get("balance", props.get("cash", None))
        if balance is not None:
            try:
                balance_signals.append({"engine": eng_name, "balance": float(balance)})
            except (TypeError, ValueError):
                pass

    convergence["directions"] = direction_counts
    convergence["platforms"] = platform_mentions

    # Themes: identify when 3+ engines agree
    for direction, count in direction_counts.items():
        if count >= 3:
            convergence["themes"].append({
                "theme": f"CONVERGENT_{direction.upper()}",
                "engines_agree": count,
                "total_engines": len(engines),
                "strength": round(count / max(len(engines), 1) * 100, 1),
            })

    # Sync score: how much agreement exists across the mesh
    if direction_counts:
        max_agree = max(direction_counts.values())
        total_signals = sum(direction_counts.values())
        convergence["sync_score"] = round(max_agree / max(total_signals, 1) * 100, 1)
    else:
        convergence["sync_score"] = 0

    # Capital awareness
    convergence["total_capital_signals"] = len(balance_signals)
    if balance_signals:
        total_visible = sum(b["balance"] for b in balance_signals)
        convergence["total_visible_capital"] = round(total_visible, 2)

    return convergence


# ===========================================================================
# PUBLIC API -- These are the synapses every engine uses
# ===========================================================================

def emit(engine: str, key: str, value, silent: bool = False):
    """
    BROADCAST a state change to the entire nervous system.

    Every engine calls this whenever something meaningful changes.
    The change is INSTANTLY visible to all other engines via sense().

    Args:
        engine: Name of the engine emitting (e.g., "TURBO_TRADER")
        key:    What changed (e.g., "balance", "status", "signal")
        value:  The new value
        silent: If True, don't log to event stream (for high-frequency updates)
    """
    with _lock:
        state = _load_bus()
        engines = state.setdefault("engines", {})

        if engine not in engines:
            engines[engine] = {
                "first_seen": datetime.now(timezone.utc).isoformat(),
                "properties": {},
                "emission_count": 0,
            }

        eng = engines[engine]
        old_value = eng["properties"].get(key)
        eng["properties"][key] = value
        eng["last_emission"] = datetime.now(timezone.utc).isoformat()
        eng["emission_count"] = eng.get("emission_count", 0) + 1

        # Update meta
        state["meta"]["total_emissions"] = state["meta"].get("total_emissions", 0) + 1
        state["meta"]["last_emission"] = datetime.now(timezone.utc).isoformat()
        state["meta"]["last_emitter"] = engine

        # Detect convergence patterns
        state["convergence"] = _detect_convergence(state)

        _save_bus(state)

        # Log event (unless silent)
        if not silent:
            _log_event(engine, key, value, old_value)


def emit_batch(engine: str, properties: dict, silent: bool = False):
    """
    BROADCAST multiple state changes at once (atomic).

    More efficient than calling emit() multiple times.

    Args:
        engine:     Name of the engine emitting
        properties: Dict of {key: value} pairs to broadcast
        silent:     If True, don't log individual events
    """
    with _lock:
        state = _load_bus()
        engines = state.setdefault("engines", {})

        if engine not in engines:
            engines[engine] = {
                "first_seen": datetime.now(timezone.utc).isoformat(),
                "properties": {},
                "emission_count": 0,
            }

        eng = engines[engine]
        now = datetime.now(timezone.utc).isoformat()

        for key, value in properties.items():
            old_value = eng["properties"].get(key)
            eng["properties"][key] = value
            if not silent:
                _log_event(engine, key, value, old_value)

        eng["last_emission"] = now
        eng["emission_count"] = eng.get("emission_count", 0) + len(properties)

        state["meta"]["total_emissions"] = state["meta"].get("total_emissions", 0) + len(properties)
        state["meta"]["last_emission"] = now
        state["meta"]["last_emitter"] = engine
        state["convergence"] = _detect_convergence(state)

        _save_bus(state)


def sense(engine_name: str = None) -> dict:
    """
    READ the current state of the entire nervous system, or one engine.

    This is how every engine gains awareness of what every other engine
    is doing RIGHT NOW. Not what they did last cycle. RIGHT NOW.

    Args:
        engine_name: Optional. If given, return only that engine's state.
                     If None, return the full bus state.

    Returns:
        Full bus state dict, or a single engine's state dict.
    """
    _track_attention(engine_name)

    state = _load_bus()

    if engine_name is None:
        return state

    # Fuzzy match: allow partial names like "TURBO" for "TURBO_TRADER"
    engines = state.get("engines", {})

    # Exact match first
    if engine_name in engines:
        return engines[engine_name]

    # Fuzzy match
    upper = engine_name.upper()
    for name, data in engines.items():
        if upper in name.upper():
            return data

    return {}


def sense_property(engine_name: str, key: str, default=None):
    """
    READ a single property from an engine's state.

    Shortcut for: sense("TURBO")["properties"]["balance"]

    Args:
        engine_name: Engine to read from
        key:         Property key
        default:     Default value if not found
    """
    eng = sense(engine_name)
    return eng.get("properties", {}).get(key, default)


def on_change(engine_name: str = None, since_minutes: int = 5) -> list:
    """
    GET recent changes from the event stream.

    Like a neuron checking "what fired recently near me?"

    Args:
        engine_name:   Filter to this engine's events (or all if None)
        since_minutes: How far back to look

    Returns:
        List of recent event dicts, newest first.
    """
    events = _read_json(EVENTS_FILE, {"events": []})
    event_list = events.get("events", [])

    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=since_minutes)).isoformat()
    recent = [e for e in event_list if e.get("timestamp", "") > cutoff]

    if engine_name:
        upper = engine_name.upper()
        recent = [e for e in recent if upper in e.get("engine", "").upper()]

    return list(reversed(recent))  # Newest first


def pulse() -> dict:
    """
    SYSTEM PULSE: How alive and connected is the mesh?

    Returns:
        Dict with alive/stale/dead counts, connectivity score,
        most active engine, most watched engine, and convergence info.
    """
    state = _load_bus()
    engines = state.get("engines", {})
    now = time.time()

    alive = 0
    stale = 0
    dead = 0
    engine_health = {}

    for name, data in engines.items():
        ts_raw = data.get("last_emission")
        if ts_raw:
            try:
                dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                age_sec = (datetime.now(timezone.utc) - dt).total_seconds()
            except Exception:
                age_sec = 999999
        else:
            age_sec = 999999

        if age_sec <= ALIVE_THRESHOLD_SEC:
            alive += 1
            status = "alive"
        elif age_sec <= STALE_THRESHOLD_SEC:
            stale += 1
            status = "stale"
        else:
            dead += 1
            status = "dead"

        engine_health[name] = {
            "status": status,
            "age_seconds": round(age_sec, 0),
            "emissions": data.get("emission_count", 0),
        }

    total = alive + stale + dead
    connectivity = round(alive / max(total, 1) * 100, 1)

    # Most active engine (most emissions)
    most_active = max(engines.items(), key=lambda x: x[1].get("emission_count", 0))[0] if engines else "none"

    # Most watched (from attention tracker)
    attention = _read_json(ATTENTION_FILE, {"reads": {}})
    reads = attention.get("reads", {})
    reads_filtered = {k: v for k, v in reads.items() if k != "__ALL__"}
    most_watched = max(reads_filtered.items(), key=lambda x: x[1])[0] if reads_filtered else "none"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alive": alive,
        "stale": stale,
        "dead": dead,
        "total": total,
        "connectivity": connectivity,
        "most_active_engine": most_active,
        "most_watched_engine": most_watched,
        "total_emissions": state.get("meta", {}).get("total_emissions", 0),
        "convergence": state.get("convergence", {}),
        "engine_health": engine_health,
    }


# ===========================================================================
# STANDALONE RUN: Boot the bus, display mesh status
# ===========================================================================
def run():
    """
    Run the SYNAPTIC_BUS as a standalone engine:
    - Reads all existing engine state files and pre-loads them into the bus
    - Prints a real-time mesh status display
    - Returns the bus state

    This "bootstraps" the bus by reading every state file and emitting
    their data, so even engines that haven't been updated to use
    emit() yet are visible in the mesh.
    """
    print("[SYNAPTIC_BUS] Initializing shared consciousness bus...")
    print()

    # Bootstrap: Read all known state files and inject into the bus
    known_engines = {
        "TURBO_TRADER":     "turbo_trader_state.json",
        "ALPACA_TRADER":    "alpaca_trader_state.json",
        "TRADE_EXECUTOR":   "trade_executor_state.json",
        "CROSS_POLLINATOR": "cross_pollinator_state.json",
        "SIGNAL_MESH":      "signal_mesh_state.json",
        "NERVE_LOOP":       "nerve_loop_state.json",
        "AUTONOMIC_NERVE":  "autonomic_state.json",
        "COMPOUND_TRACKER": "compound_tracker.json",
        "TRADE_LEDGER":     "trade_ledger.json",
        "FLYWHEEL":         "flywheel_state.json",
        "AI_COST_TRACKER":  "ai_cost_tracker.json",
        "POLYMARKET":       "polymarket_scan.json",
        "KALSHI_SCANNER":   "kalshi_scan.json",
        "ARBITRAGE":        "arbitrage_scanner_state.json",
        "PULSE":            "pulse_state.json",
        "GROWTH_TRACKER":   "growth_tracker.json",
        "METABOLISM_LOOP":  "metabolism_state.json",
        "GLOBAL_MARKETS":   "global_markets_state.json",
        "REFLEX_ARC":       "reflex_arc_state.json",
        "PROPRIOCEPTION":   "proprioception_state.json",
        "SETTLEMENT_WATCHER": "settlement_watcher_state.json",
        "AUTO_DEPOSIT":     "auto_deposit_state.json",
        "SIGNAL_MESH":      "signal_mesh_state.json",
        "NEURAL_CORTEX":    "neural_cortex_state.json",
        "EXECUTIVE_FUNCTION": "executive_function_state.json",
        "HOMEOSTASIS":      "homeostasis_state.json",
    }

    bootstrapped = 0
    for eng_name, filename in known_engines.items():
        fpath = DATA / filename
        if fpath.exists():
            data = _read_json(fpath)
            if data:
                # Extract key properties from each engine's state
                props = _extract_key_props(eng_name, data)
                if props:
                    emit_batch(eng_name, props, silent=True)
                    bootstrapped += 1

    print(f"  [BOOTSTRAP] Loaded {bootstrapped}/{len(known_engines)} engines into synaptic bus")
    print()

    # Get pulse
    p = pulse()

    # Print mesh status
    W = 64
    print("=" * W)
    print("  SYNAPTIC BUS -- Shared Consciousness Status")
    print("=" * W)
    print()
    print(f"  Neural Connectivity:  {p['connectivity']}%")
    print(f"  Engines Online:       {p['alive']} alive / {p['stale']} stale / {p['dead']} dead")
    print(f"  Total Emissions:      {p['total_emissions']}")
    print(f"  Most Active:          {p['most_active_engine']}")
    print(f"  Most Watched:         {p['most_watched_engine']}")
    print()

    # Convergence
    conv = p.get("convergence", {})
    themes = conv.get("themes", [])
    if themes:
        print("  CONVERGENT SIGNALS:")
        for theme in themes:
            print(f"    {theme['theme']}: {theme['engines_agree']}/{theme['total_engines']} engines agree "
                  f"(strength {theme['strength']}%)")
    else:
        print("  CONVERGENCE: No strong convergent signals yet")

    directions = conv.get("directions", {})
    if directions:
        print(f"  Direction votes: {directions}")

    total_capital = conv.get("total_visible_capital", 0)
    if total_capital > 0:
        print(f"  Total visible capital: ${total_capital:.2f}")
    print()

    # Engine health table
    print("  ENGINE HEALTH:")
    print("  " + "-" * (W - 4))
    health = p.get("engine_health", {})
    for name in sorted(health.keys()):
        h = health[name]
        status = h["status"].upper()
        emissions = h["emissions"]
        age = h["age_seconds"]
        if age < 60:
            age_str = f"{age:.0f}s"
        elif age < 3600:
            age_str = f"{age / 60:.0f}m"
        else:
            age_str = f"{age / 3600:.1f}h"

        indicator = {"ALIVE": "+", "STALE": "~", "DEAD": "-"}.get(status, "?")
        print(f"    [{indicator}] {name:<22} {status:<6} age={age_str:<6} emissions={emissions}")

    print()
    print("=" * W)
    print("  Every engine sees everything. Simultaneously.")
    print("  That's not a pipeline. That's consciousness.")
    print("=" * W)

    # Save the pulse as our state
    bus_state = _load_bus()
    bus_state["last_pulse"] = p
    _save_bus(bus_state)

    return bus_state


def _extract_key_props(eng_name, data):
    """Extract the most important properties from an engine's state file."""
    props = {}

    # Universal fields
    for key in ("status", "timestamp", "balance", "cash", "portfolio_value",
                "buying_power", "equity", "signal_direction", "signal_strength",
                "market_open", "mode", "positions_count", "opportunities_found",
                "daily_opps", "win_rate", "self_sustaining", "total_emissions"):
        if key in data:
            props[key] = data[key]

    # Engine-specific
    if eng_name == "TURBO_TRADER":
        props["balance"] = data.get("balance", data.get("last_known_balance", 0))
        props["daily_opps"] = data.get("daily_opps", 0)
        props["trades_placed"] = data.get("trades_placed", 0)
        props["platform"] = "kalshi"

    elif eng_name == "ALPACA_TRADER":
        props["cash"] = data.get("cash", 0)
        props["portfolio_value"] = data.get("portfolio_value", 0)
        props["market_open"] = data.get("market_open", False)
        props["opportunities_found"] = data.get("opportunities_found", 0)
        props["platform"] = "alpaca"

    elif eng_name == "CROSS_POLLINATOR":
        props["total_portfolio_value"] = data.get("total_portfolio_value", 0)
        props["mycelium_health_score"] = data.get("mycelium_health_score", 0)
        props["best_opportunity_platform"] = data.get("best_opportunity_platform", "")

    elif eng_name == "SIGNAL_MESH":
        composite = data.get("composite_signal", {})
        props["composite_strength"] = composite.get("composite_strength", 0)
        props["dominant_direction"] = composite.get("dominant_direction", "neutral")
        props["conviction_score"] = composite.get("conviction_score", 0)

    elif eng_name == "NERVE_LOOP":
        props["phases_complete"] = len(data.get("phases", {}))
        props["elapsed_seconds"] = data.get("elapsed_seconds", 0)

    elif eng_name == "AUTONOMIC_NERVE":
        props["ollama_available"] = data.get("ollama_available", False)
        props["decision_method"] = data.get("decision_method", "unknown")
        props["heartbeat_interval"] = data.get("heartbeat_interval", 60)

    elif eng_name == "COMPOUND_TRACKER":
        props["compound_cycles"] = data.get("compound_cycles", 0)
        props["peak_balance"] = data.get("peak_balance", 0)

    elif eng_name == "TRADE_LEDGER":
        stats = data.get("stats", {})
        props["total_trades"] = stats.get("total_trades", len(data.get("trades", [])))
        props["successful_orders"] = stats.get("successful_orders", 0)
        props["win_rate"] = stats.get("win_rate", 0)

    elif eng_name == "AI_COST_TRACKER":
        props["total_cost_usd"] = data.get("total_cost_usd", 0)
        props["total_trading_profit"] = data.get("total_trading_profit", 0)
        props["self_sustaining"] = data.get("self_sustaining", False)

    elif eng_name == "PULSE":
        portfolio = data.get("portfolio", {})
        props["total_usd"] = portfolio.get("total_usd", 0)

    elif eng_name == "POLYMARKET":
        props["edges_found"] = data.get("edges_found", 0)
        props["signal_direction"] = "opportunity" if data.get("edges_found", 0) > 0 else "neutral"

    elif eng_name == "ARBITRAGE":
        opps = data.get("actionable_opportunities", [])
        props["opportunities_count"] = len(opps) if isinstance(opps, list) else 0
        props["signal_direction"] = "opportunity" if props["opportunities_count"] > 0 else "neutral"

    elif eng_name == "METABOLISM_LOOP":
        metabolism = data.get("metabolism", {})
        props["circuit_status"] = data.get("circuit_status", "unknown")
        props["revenue_velocity_hr"] = metabolism.get("revenue_velocity_per_hour", 0)
        props["ecosystem_health"] = metabolism.get("ecosystem_health", 0)
        props["self_funding_ratio"] = metabolism.get("self_funding_ratio", 0)
        props["circular_amplification"] = metabolism.get("circular_amplification", 1.0)
        props["combined_growth_rate"] = metabolism.get("combined_growth_rate", 0)

    elif eng_name == "GLOBAL_MARKETS":
        cross = data.get("cross_platform", {})
        props["regime"] = cross.get("regime", "UNKNOWN")
        props["regime_score"] = cross.get("regime_score", 0)
        props["regime_label"] = cross.get("regime_label", "")
        props["total_visible_capital"] = cross.get("total_visible_capital", 0)
        props["opportunities_ranked"] = len(data.get("ranked_opportunities", []))
        # Top opportunity for quick reads
        ranked = data.get("ranked_opportunities", [])
        if ranked:
            top = ranked[0]
            props["top_opportunity"] = top.get("name", "?")
            props["top_opportunity_score"] = top.get("score", 0)
            props["top_opportunity_platform"] = top.get("platform", "?")

    elif eng_name == "REFLEX_ARC":
        last_cycle = data.get("last_cycle", {})
        props["checked"] = last_cycle.get("checked", 0)
        props["fired"] = last_cycle.get("fired", 0)
        props["arc_response_ms"] = last_cycle.get("arc_response_ms", 0)
        props["total_fires"] = data.get("total_fires", 0)
        props["total_checks"] = data.get("total_checks", 0)
        props["fire_counts"] = data.get("fire_counts", {})

    elif eng_name == "PROPRIOCEPTION":
        props["engine_count"] = data.get("engine_count", 0)
        props["data_file_count"] = data.get("data_file_count", 0)
        props["evolution_label"] = data.get("evolution_label", "")
        props["coordination_score"] = data.get("coordination_score", 0)
        props["metabolism_rate"] = data.get("metabolism_rate", 0)
        props["growth_trajectory"] = data.get("growth_trajectory", {})

    elif eng_name == "SETTLEMENT_WATCHER":
        props["settlements_detected"] = data.get("settlements_detected", 0)
        props["last_settlement_amount"] = data.get("last_settlement_amount", 0)
        props["redeployment_count"] = data.get("redeployment_count", 0)

    elif eng_name == "AUTO_DEPOSIT":
        props["decision_tier"] = data.get("decision_tier", "")
        props["kalshi_pct"] = data.get("kalshi_pct", 60)
        props["alpaca_pct"] = data.get("alpaca_pct", 40)
        props["total_deployed"] = data.get("total_deployed", 0)

    elif eng_name == "SIGNAL_MESH":
        composite = data.get("composite_signal", {})
        props["composite_strength"] = composite.get("composite_strength", 0)
        props["dominant_direction"] = composite.get("dominant_direction", "neutral")
        props["conviction_score"] = composite.get("conviction_score", 0)
        props["urgency"] = composite.get("urgency", 0)
        hb = data.get("heartbeat", {})
        props["sources_alive"] = hb.get("alive", 0)
        props["neural_connectivity"] = hb.get("neural_connectivity", 0)

    elif eng_name == "NEURAL_CORTEX":
        strategy = data.get("strategy", {})
        props["risk_posture"] = strategy.get("risk_posture", "moderate")
        props["risk_score"] = strategy.get("risk_score", 0)
        alloc = strategy.get("capital_allocation", {})
        props["kalshi_pct"] = alloc.get("kalshi_pct", 0)
        props["alpaca_pct"] = alloc.get("alpaca_pct", 0)
        props["solana_pct"] = alloc.get("solana_pct", 0)
        props["growth_priority"] = strategy.get("growth_priority", "trading")
        top_action = strategy.get("top_action", {})
        props["top_action"] = top_action.get("description", "none")
        props["top_action_urgency"] = top_action.get("urgency", 0)
        health = data.get("system_health", {})
        props["system_health"] = health.get("overall_score", 0)
        props["weakest_engine"] = health.get("weakest_engine", "none")
        props["decision_confidence"] = data.get("decision_confidence", 0)

    elif eng_name == "EXECUTIVE_FUNCTION":
        last_exec = data.get("last_execution", {})
        props["last_target"] = last_exec.get("target_engine", "none")
        props["last_urgency"] = last_exec.get("urgency", 0)
        props["last_result"] = last_exec.get("result", "none")
        stats = data.get("stats", {})
        props["total_executions"] = stats.get("total_executions", 0)
        props["success_rate"] = stats.get("success_rate_pct", 0)
        props["active_cooldowns"] = len(data.get("cooldowns", {}))

    elif eng_name == "HOMEOSTASIS":
        props["equilibrium"] = data.get("equilibrium", 0)
        props["trend"] = data.get("trend", "unknown")
        zones = data.get("health_zones", {})
        props["nervous_system_score"] = zones.get("nervous_system", {}).get("score", 0)
        props["ecosystem_score"] = zones.get("ecosystem", {}).get("score", 0)
        props["trading_score"] = zones.get("trading", {}).get("score", 0)
        props["infrastructure_score"] = zones.get("infrastructure", {}).get("score", 0)
        ic = data.get("interventions_count", {})
        props["interventions_critical"] = ic.get("critical", 0)
        props["interventions_total"] = ic.get("total", 0)
        fl = data.get("fire_ledger_summary", {})
        props["fire_overlap_detected"] = fl.get("overlap_detected", False)
        props["recently_fired_count"] = len(fl.get("recently_fired_engines", []))

    return props


if __name__ == "__main__":
    run()
