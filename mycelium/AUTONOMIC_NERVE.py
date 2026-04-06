#!/usr/bin/env python3
"""
AUTONOMIC_NERVE.py -- The heartbeat that never stops
=====================================================
v1 (2026-04-06): SolarPunk's autonomic nervous system.

PROBLEM:
  Claude scheduled tasks only fire into ACTIVE sessions.
  When a session ends, NERVE_LOOP stalls, TURBO_TRADER idles,
  trades don't compound, the whole system flatlines.

SOLUTION:
  A standalone Python daemon that runs FOREVER, independent of Claude.
  Uses local Ollama (FREE, always-on) for AI decisions.
  Falls back through: Ollama -> Groq -> raw logic (never stops).

  Like the autonomic nervous system -- keeps the heart beating
  even when the conscious mind (Claude) is asleep.

HOW IT WORKS:
  1. HEARTBEAT: Runs every N minutes, checks all engine states
  2. DETECT STALL: If any engine is past its deadline, re-run it
  3. TRADE CYCLE: TURBO_TRADER every 15 min, ALPACA_TRADER every 30 min
  4. FULL LOOP: NERVE_LOOP every 60 min
  5. AI OVERSEER: Ollama analyzes system state, makes strategic decisions
  6. SELF-HEAL: If an engine crashes, log it, skip it, keep going

RUNNING:
  # Foreground (see output):
  python mycelium/AUTONOMIC_NERVE.py

  # Background (Windows, no window):
  pythonw mycelium/AUTONOMIC_NERVE.py

  # As Windows Task Scheduler (survives reboots):
  schtasks /create /tn "SolarPunk_Autonomic" /tr "pythonw AUTONOMIC_NERVE.py" /sc onstart

MODELS (priority order):
  1. mycelium:latest  -- custom SolarPunk model (7.2B)
  2. deepseek-r1:8b   -- reasoning model
  3. qwen2.5-coder:7b -- code-aware
  4. llama3.2:latest   -- fast fallback (3.2B)

Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)

Called by: Windows Task Scheduler, manual launch, or any process manager
Reads: all engine state files
Writes: data/autonomic_state.json, runs engines directly
"""

import json
import sys
import time
import os
import traceback
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Ensure we can import mycelium engines
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "mycelium"))
os.chdir(str(REPO_ROOT))

DATA = Path("data")
DATA.mkdir(exist_ok=True)
LOG_DIR = DATA / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ================================================================
# CONFIGURATION
# ================================================================

# Default schedule (overridden by data/task_queue.json if it exists)
DEFAULT_SCHEDULE = {
    "TURBO_TRADER":     15,   # Every 15 min -- fast market compounding
    "TRADING_WIRE":     15,   # Every 15 min -- wire data after trades
    "ALPACA_TRADER":    30,   # Every 30 min -- stock market (slower)
    "CROSS_POLLINATOR": 30,   # Every 30 min -- capital routing between platforms
    "PULSE":            30,   # Every 30 min -- system vital signs snapshot
    "SIGNAL_MESH":      15,   # Every 15 min -- aggregate multi-source signals
    "SYNAPTIC_BUS":      5,   # Every 5 min -- refresh shared consciousness
    "REFLEX_ARC":        5,   # Every 5 min -- fast reflexive responses
    "PROPRIOCEPTION":   15,   # Every 15 min -- self-awareness body scan
    "SETTLEMENT_WATCHER": 5,  # Every 5 min -- detect settled positions, redeploy cash
    "AUTO_DEPOSIT":     10,   # Every 10 min -- smart capital split when new money arrives
    "METABOLISM_LOOP":  15,   # Every 15 min -- circular metabolism (nervous -> ecosystem -> back)
    "GLOBAL_MARKETS":   15,   # Every 15 min -- cross-platform regime detection + opportunity ranking
    "NEURAL_CORTEX":    10,   # Every 10 min -- strategic brain (reads everything, decides everything)
    "NERVE_LOOP":       60,   # Every 60 min -- full ecosystem cycle
}


_schedule_cache = {"data": None, "loaded_at": 0}
_SCHEDULE_TTL = 60  # seconds


def load_schedule():
    """
    Load schedule from SolarPunk's own task queue.
    Falls back to DEFAULT_SCHEDULE if task_queue.json doesn't exist.
    Cached with 60-second TTL so we don't re-read the file every heartbeat.

    This means SolarPunk controls its OWN schedule -- no Claude needed.
    Edit data/task_queue.json to add/remove/change tasks.
    """
    now = time.time()
    if _schedule_cache["data"] is not None and (now - _schedule_cache["loaded_at"]) < _SCHEDULE_TTL:
        return _schedule_cache["data"]

    try:
        queue = json.loads((DATA / "task_queue.json").read_text(encoding="utf-8"))
    except Exception:
        queue = {}
    tasks = queue.get("scheduled_tasks", [])

    if not tasks:
        result = DEFAULT_SCHEDULE.copy()
    else:
        schedule = {}
        for task in tasks:
            if task.get("enabled", True):
                engine = task.get("engine", "")
                interval = task.get("interval_minutes", 60)
                if engine:
                    schedule[engine] = interval
        result = schedule if schedule else DEFAULT_SCHEDULE.copy()

    _schedule_cache["data"] = result
    _schedule_cache["loaded_at"] = now
    return result


# Load schedule (refreshed via TTL cache)
SCHEDULE = load_schedule()

# Ollama models in priority order
# NOTE: Models >4GB hit a corruption boundary (tensor offset exceeds file size).
# Corrupted 7B+ models were removed 2026-04-06. Only sub-4GB models are safe.
OLLAMA_MODELS = [
    "llama3.2:latest",     # 3.2B (2.0GB) -- primary, proven stable
    "phi3:mini",           # 3.8B (2.2GB) -- secondary, under 4GB boundary
]

OLLAMA_URL = "http://localhost:11434"

# Stall detection: if engine hasn't run in 2x its schedule, it's stalled
STALL_MULTIPLIER = 2.0

# Heartbeat interval (seconds)
HEARTBEAT_INTERVAL = 60  # Check every 60 seconds

# Thermal management thresholds
THERMAL_CPU_THROTTLE = 85     # Throttle if CPU% above this
THERMAL_CPU_RESUME = 60       # Resume when CPU% drops below this
THERMAL_RAM_THROTTLE = 90     # Throttle if RAM% above this
THERMAL_RAM_RESUME = 75       # Resume when RAM% drops below this
THERMAL_COOLDOWN_SEC = 120    # How long to wait when throttled


def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def log(msg, level="INFO"):
    """Log to console and file."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)

    # Append to daily log file
    log_file = LOG_DIR / f"autonomic_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ================================================================
# THERMAL MANAGEMENT -- Keep the machine alive
# ================================================================

def get_system_vitals():
    """
    Read CPU%, RAM%, and temperature if available.
    Uses psutil (pure Python, already installed).
    """
    vitals = {
        "cpu_pct": 0,
        "ram_pct": 0,
        "ram_used_gb": 0,
        "ram_total_gb": 0,
        "cpu_count": 1,
        "temp_c": None,  # None = not available
    }
    try:
        import psutil
        vitals["cpu_pct"] = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        vitals["ram_pct"] = mem.percent
        vitals["ram_used_gb"] = round(mem.used / (1024**3), 1)
        vitals["ram_total_gb"] = round(mem.total / (1024**3), 1)
        vitals["cpu_count"] = psutil.cpu_count()

        # Try to get temperature on Windows
        try:
            import subprocess
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance -Namespace root/WMI -ClassName "
                 "MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue)"
                 ".CurrentTemperature"],
                capture_output=True, text=True, timeout=5
            )
            if r.stdout.strip().isdigit():
                # WMI returns tenths of Kelvin
                kelvin_tenths = int(r.stdout.strip())
                vitals["temp_c"] = round((kelvin_tenths / 10) - 273.15, 1)
        except Exception:
            pass

    except ImportError:
        pass

    return vitals


def should_throttle(vitals):
    """
    Decide if the system should throttle (pause engines) to cool down.
    Returns (should_throttle: bool, reason: str)
    """
    cpu = vitals.get("cpu_pct", 0)
    ram = vitals.get("ram_pct", 0)
    temp = vitals.get("temp_c")

    if cpu >= THERMAL_CPU_THROTTLE:
        return True, f"CPU at {cpu}% (threshold: {THERMAL_CPU_THROTTLE}%)"
    if ram >= THERMAL_RAM_THROTTLE:
        return True, f"RAM at {ram}% (threshold: {THERMAL_RAM_THROTTLE}%)"
    if temp is not None and temp >= 85:
        return True, f"CPU temp {temp}C (threshold: 85C)"
    return False, ""


def can_resume(vitals):
    """Check if system has cooled enough to resume."""
    cpu = vitals.get("cpu_pct", 0)
    ram = vitals.get("ram_pct", 0)
    temp = vitals.get("temp_c")

    if cpu > THERMAL_CPU_RESUME:
        return False
    if ram > THERMAL_RAM_RESUME:
        return False
    if temp is not None and temp > 75:
        return False
    return True


# ================================================================
# OLLAMA AI INTERFACE
# ================================================================

def ollama_available():
    """Check if Ollama is running."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read())
            models = [m["name"] for m in data.get("models", [])]
            return True, models
    except Exception:
        return False, []


def ollama_ask(prompt, model=None, timeout=60):
    """
    Ask Ollama a question. Tries models in priority order.
    Returns the response text or None.
    """
    if model:
        models_to_try = [model]
    else:
        models_to_try = OLLAMA_MODELS[:]

    for m in models_to_try:
        try:
            body = json.dumps({
                "model": m,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 500,
                }
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{OLLAMA_URL}/api/generate",
                data=body,
                method="POST"
            )
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=timeout) as r:
                result = json.loads(r.read())
                response = result.get("response", "").strip()
                if response:
                    return response, m
        except Exception as e:
            log(f"Ollama model {m} failed: {e}", "WARN")
            continue

    return None, None


def ai_analyze_system(state_summary):
    """
    Use Ollama to analyze system state and recommend actions.
    Falls back to rule-based logic if Ollama is down.
    """
    # Build compact state for AI
    compact = {}
    for eng, info in state_summary.items():
        compact[eng] = f"{info.get('minutes_since_run',0):.0f}m/{info.get('schedule_minutes',0)}m"
        if info.get("stalled"):
            compact[eng] += " STALLED"
        if info.get("due"):
            compact[eng] += " DUE"

    prompt = f"""Respond with ONLY a JSON object. Which engines should run?
State (minutes_since/schedule): {json.dumps(compact)}
Run engines that are DUE or STALLED. Format: {{"actions":["ENGINE_NAME"],"reasoning":"why"}}"""

    response, model = ollama_ask(prompt)
    if response:
        try:
            # Try to extract JSON from response
            clean = response.strip()
            # Handle markdown code blocks
            if "```" in clean:
                parts = clean.split("```")
                for part in parts[1:]:
                    if part.strip().startswith("json"):
                        clean = part.strip()[4:].strip()
                        break
                    elif part.strip().startswith("{"):
                        clean = part.strip()
                        break
            # Find the JSON object
            start = clean.find("{")
            if start >= 0:
                clean = clean[start:]
            # Fix truncated JSON: add missing closing braces
            open_braces = clean.count("{") - clean.count("}")
            open_brackets = clean.count("[") - clean.count("]")
            # Strip trailing incomplete strings
            if clean.endswith('"') and open_braces > 0:
                clean = clean.rsplit('"', 2)[0] + '""'
            clean += "]" * max(0, open_brackets)
            clean += "}" * max(0, open_braces)
            result = json.loads(clean)
            result["ai_model"] = model
            # Track tokens (Ollama is free but track usage)
            track_ai_cost(f"ollama:{model}", len(prompt.split()) + len(response.split()), 0)
            return result
        except Exception:
            log(f"AI response not valid JSON, using rules. Response: {response[:200]}", "WARN")

    # Fallback 2: Try Groq FREE tier (10 req/sec, no cost)
    groq_result = groq_analyze(state_summary)
    if groq_result:
        return groq_result

    # Fallback 3: rule-based logic (always works, no AI needed)
    return None


# ================================================================
# GROQ FREE TIER FALLBACK
# ================================================================

def groq_analyze(state_summary):
    """
    Use Groq FREE API as AI fallback when Ollama fails.
    Groq: 10 req/sec, FREE tier, no credit card.
    """
    # Try loading Groq API key from secrets or env
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        secrets = _load(DATA / ".secrets" / "groq.json")
        api_key = secrets.get("api_key", "")
    if not api_key:
        return None

    compact = {}
    for eng, info in state_summary.items():
        compact[eng] = f"{info.get('minutes_since_run',0):.0f}m/{info.get('schedule_minutes',0)}m"
        if info.get("stalled"):
            compact[eng] += " STALLED"
        if info.get("due"):
            compact[eng] += " DUE"

    body = json.dumps({
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Respond ONLY with JSON. No other text."},
            {"role": "user", "content": f'Which engines to run? State: {json.dumps(compact)}. '
                f'Format: {{"actions":["ENGINE"],"reasoning":"why"}}'},
        ],
        "temperature": 0.1,
        "max_tokens": 200,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=body, method="POST"
        )
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
            content = result["choices"][0]["message"]["content"].strip()
            # Track tokens for self-funding
            usage = result.get("usage", {})
            track_ai_cost("groq", usage.get("total_tokens", 0), 0)  # Groq is FREE
            parsed = json.loads(content)
            parsed["ai_model"] = "groq:llama-3.1-8b-instant"
            return parsed
    except Exception as e:
        log(f"Groq fallback failed: {e}", "WARN")
        return None


# ================================================================
# SELF-FUNDING TOKEN TRACKER
# ================================================================

def track_ai_cost(provider, tokens, cost_usd):
    """
    Track AI token usage and cost. Trading profits fund these costs.

    The self-sustaining loop:
      Trading profits -> fund AI tokens -> AI makes better trades -> more profits

    Cost tracking enables:
      1. See exactly how much AI costs per cycle
      2. Compare against trading profits
      3. Prove the system pays for itself
    """
    tracker = _load(DATA / "ai_cost_tracker.json", {
        "total_tokens": 0,
        "total_cost_usd": 0,
        "total_trading_profit": 0,
        "self_sustaining": False,
        "providers": {},
        "daily": {},
    })

    # Update totals
    tracker["total_tokens"] = tracker.get("total_tokens", 0) + tokens
    tracker["total_cost_usd"] = round(tracker.get("total_cost_usd", 0) + cost_usd, 6)

    # Per-provider tracking
    if provider not in tracker.get("providers", {}):
        tracker["providers"][provider] = {"tokens": 0, "cost_usd": 0, "calls": 0}
    tracker["providers"][provider]["tokens"] += tokens
    tracker["providers"][provider]["cost_usd"] = round(
        tracker["providers"][provider]["cost_usd"] + cost_usd, 6)
    tracker["providers"][provider]["calls"] += 1

    # Daily tracking
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if today not in tracker.get("daily", {}):
        tracker["daily"][today] = {"tokens": 0, "cost_usd": 0, "calls": 0}
    tracker["daily"][today]["tokens"] += tokens
    tracker["daily"][today]["cost_usd"] = round(
        tracker["daily"][today]["cost_usd"] + cost_usd, 6)
    tracker["daily"][today]["calls"] += 1

    # Pull trading profit from trade ledger
    ledger = _load(DATA / "trade_ledger.json", {"trades": []})
    total_profit = sum(
        t.get("order_details", {}).get("expected_profit", 0)
        for t in ledger.get("trades", [])
        if t.get("success")
    )
    tracker["total_trading_profit"] = round(total_profit, 4)
    tracker["self_sustaining"] = total_profit > tracker["total_cost_usd"]
    tracker["profit_minus_ai_cost"] = round(total_profit - tracker["total_cost_usd"], 4)

    # Keep only last 30 days of daily data
    daily = tracker.get("daily", {})
    if len(daily) > 30:
        sorted_days = sorted(daily.keys())
        for old_day in sorted_days[:-30]:
            del daily[old_day]

    tracker["last_updated"] = datetime.now(timezone.utc).isoformat()
    _save(DATA / "ai_cost_tracker.json", tracker)


# ================================================================
# ENGINE RUNNER
# ================================================================

def _bus_cache_get():
    """
    Load the SYNAPTIC_BUS once per heartbeat (single file read).
    Returns the full bus state dict or None if the bus file is
    missing / stale (>5 min old).
    """
    bus_path = DATA / "synaptic_bus.json"
    try:
        raw = bus_path.read_text(encoding="utf-8")
        bus = json.loads(raw)
        # Staleness check: if the bus hasn't been updated in 5 min, fall back
        last = bus.get("meta", {}).get("last_emission")
        if last:
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - last_dt).total_seconds() > 300:
                return None  # stale bus -- fall back to individual files
        return bus
    except Exception:
        return None

# Module-level bus snapshot -- refreshed once per heartbeat in build_state_summary()
_bus_snapshot = None


def get_engine_state(engine_name):
    """
    Read an engine's state, preferring the SYNAPTIC_BUS (1 file for all
    engines) and falling back to individual state files only when the
    bus is unavailable or stale.
    """
    global _bus_snapshot

    # --- Fast path: read from the synaptic bus snapshot ---
    if _bus_snapshot is not None:
        eng = _bus_snapshot.get("engines", {}).get(engine_name, {})
        if eng:
            # Reconstruct a state-file-like dict from bus properties
            props = eng.get("properties", {})
            state = dict(props)
            # Use bus emission timestamp as the canonical timestamp
            state.setdefault("timestamp", eng.get("last_emission", ""))
            return state

    # --- Slow path: individual state files ---
    state_files = {
        "TURBO_TRADER":     DATA / "turbo_trader_state.json",
        "TRADING_WIRE":     DATA / "trading_wire_state.json",
        "ALPACA_TRADER":    DATA / "alpaca_trader_state.json",
        "CROSS_POLLINATOR": DATA / "cross_pollinator_state.json",
        "PULSE":            DATA / "pulse_state.json",
        "NERVE_LOOP":       DATA / "nerve_loop_state.json",
        "SIGNAL_MESH":      DATA / "signal_mesh_state.json",
        "SYNAPTIC_BUS":     DATA / "synaptic_bus.json",
        "REFLEX_ARC":       DATA / "reflex_arc_state.json",
        "PROPRIOCEPTION":   DATA / "proprioception_state.json",
    }
    path = state_files.get(engine_name)
    if not path:
        return None
    state = _load(path)
    return state


def get_last_run_time(engine_name):
    """Get when an engine last ran (UTC datetime)."""
    state = get_engine_state(engine_name)
    if not state:
        return None
    ts = state.get("timestamp", "")
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def is_stalled(engine_name):
    """Check if an engine has missed its scheduled run."""
    last = get_last_run_time(engine_name)
    if not last:
        return True  # Never ran = stalled

    schedule_min = SCHEDULE.get(engine_name, 60)
    deadline = last + timedelta(minutes=schedule_min * STALL_MULTIPLIER)
    now = datetime.now(timezone.utc)
    return now > deadline


def minutes_since_last_run(engine_name):
    """Minutes since engine last ran."""
    last = get_last_run_time(engine_name)
    if not last:
        return 9999
    delta = datetime.now(timezone.utc) - last
    return delta.total_seconds() / 60


def run_engine(engine_name):
    """
    Import and run an engine. Returns (success, result_or_error).
    Each engine has a run() function that does everything.
    """
    log(f">> Running {engine_name}...")
    start = time.time()

    try:
        if engine_name == "TURBO_TRADER":
            from mycelium.TURBO_TRADER import run
            result = run()
        elif engine_name == "TRADING_WIRE":
            from mycelium.TRADING_WIRE import run
            result = run()
        elif engine_name == "ALPACA_TRADER":
            from mycelium.ALPACA_TRADER import run
            result = run()
        elif engine_name == "CROSS_POLLINATOR":
            from mycelium.CROSS_POLLINATOR import run
            result = run()
        elif engine_name == "PULSE":
            from mycelium.PULSE import run
            result = run()
        elif engine_name == "NERVE_LOOP":
            from mycelium.NERVE_LOOP import run
            result = run()
        elif engine_name == "SIGNAL_MESH":
            from mycelium.SIGNAL_MESH import run
            result = run()
        elif engine_name == "SYNAPTIC_BUS":
            from mycelium.SYNAPTIC_BUS import run
            result = run()
        elif engine_name == "REFLEX_ARC":
            from mycelium.REFLEX_ARC import run
            result = run()
        elif engine_name == "PROPRIOCEPTION":
            from mycelium.PROPRIOCEPTION import run
            result = run()
        elif engine_name == "SETTLEMENT_WATCHER":
            from mycelium.SETTLEMENT_WATCHER import run
            result = run()
        elif engine_name == "AUTO_DEPOSIT":
            from mycelium.AUTO_DEPOSIT import run
            result = run()
        elif engine_name == "METABOLISM_LOOP":
            from mycelium.METABOLISM_LOOP import run
            result = run()
        elif engine_name == "GLOBAL_MARKETS":
            from mycelium.GLOBAL_MARKETS import run
            result = run()
        elif engine_name == "NEURAL_CORTEX":
            from mycelium.NEURAL_CORTEX import run
            result = run()
        else:
            return False, f"Unknown engine: {engine_name}"

        elapsed = time.time() - start
        status = result.get("status", "?") if isinstance(result, dict) else "?"
        log(f"<< {engine_name} complete ({elapsed:.1f}s) | status={status}")
        return True, result

    except Exception as e:
        elapsed = time.time() - start
        error = f"{type(e).__name__}: {e}"
        log(f"<< {engine_name} CRASHED ({elapsed:.1f}s) | {error}", "ERROR")
        # Log full traceback to file
        tb = traceback.format_exc()
        crash_file = LOG_DIR / f"crash_{engine_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
        try:
            crash_file.write_text(f"{error}\n\n{tb}", encoding="utf-8")
        except Exception:
            pass
        return False, error


# ================================================================
# HEARTBEAT -- The core loop
# ================================================================

def build_state_summary():
    """Build a summary of all engine states for AI analysis."""
    # Refresh the bus snapshot once -- avoids N individual file reads
    global _bus_snapshot
    _bus_snapshot = _bus_cache_get()

    summary = {}
    for engine_name in SCHEDULE:
        state = get_engine_state(engine_name) or {}
        mins = minutes_since_last_run(engine_name)
        stalled = is_stalled(engine_name)
        schedule = SCHEDULE[engine_name]

        summary[engine_name] = {
            "status": state.get("status", "unknown"),
            "minutes_since_run": round(mins, 1),
            "schedule_minutes": schedule,
            "stalled": stalled,
            "due": mins >= schedule,
        }

        # Add key metrics per engine
        if engine_name == "TURBO_TRADER":
            summary[engine_name]["balance"] = state.get("balance", 0)
            summary[engine_name]["positions"] = state.get("positions_count", 0)
            summary[engine_name]["pending_payout"] = state.get("total_pending_payout", 0)
        elif engine_name == "ALPACA_TRADER":
            summary[engine_name]["portfolio"] = state.get("portfolio_value", 0)
            summary[engine_name]["market_open"] = state.get("market_open", False)
            summary[engine_name]["opportunities"] = state.get("opportunities_found", 0)
        elif engine_name == "NERVE_LOOP":
            phases = state.get("phases", {})
            summary[engine_name]["phases_complete"] = len(phases)

    return summary


def decide_what_to_run(state_summary):
    """
    Decide which engines need to run right now.
    Uses AI (Ollama) if available, falls back to rule-based logic.
    """
    # Try AI analysis first
    ai_result = ai_analyze_system(state_summary)
    if ai_result and "actions" in ai_result:
        actions = ai_result["actions"]
        reasoning = ai_result.get("reasoning", "AI decision")
        model = ai_result.get("ai_model", "unknown")
        log(f"AI ({model}): {reasoning}")
        # Validate actions are real engine names
        valid = [a for a in actions if a in SCHEDULE]
        if valid:
            return valid, f"ai:{model}"

    # Rule-based fallback (always works)
    to_run = []
    for engine_name, info in state_summary.items():
        mins = info.get("minutes_since_run", 9999)
        schedule = info.get("schedule_minutes", 60)
        stalled = info.get("stalled", False)

        # Run if due or stalled
        if mins >= schedule or stalled:
            to_run.append(engine_name)

    # Priority order: trades first, then wire, then full loop
    priority = ["TURBO_TRADER", "ALPACA_TRADER", "TRADING_WIRE", "NERVE_LOOP"]
    to_run.sort(key=lambda x: priority.index(x) if x in priority else 99)

    return to_run, "rules"


def heartbeat():
    """
    One heartbeat cycle. Check everything, run what's needed.
    Called every HEARTBEAT_INTERVAL seconds.

    Thermal-aware: checks CPU/RAM/temp before running engines.
    If the machine is too hot, pause and wait for cooldown.
    """
    now = datetime.now(timezone.utc)

    # === THERMAL CHECK ===
    vitals = get_system_vitals()
    cpu = vitals.get("cpu_pct", 0)
    ram = vitals.get("ram_pct", 0)
    temp_str = f" | {vitals['temp_c']}C" if vitals.get("temp_c") is not None else ""

    throttle, reason = should_throttle(vitals)
    if throttle:
        log(f"THERMAL THROTTLE: {reason} | CPU={cpu}% RAM={ram}%{temp_str}", "WARN")
        log(f"Cooling down for {THERMAL_COOLDOWN_SEC}s...")
        # Save thermal state
        _save(DATA / "autonomic_state.json", {
            "timestamp": now.isoformat(),
            "status": "thermal_throttle",
            "reason": reason,
            "vitals": vitals,
            "cooldown_seconds": THERMAL_COOLDOWN_SEC,
        })
        time.sleep(THERMAL_COOLDOWN_SEC)
        # Re-check after cooldown
        vitals = get_system_vitals()
        if not can_resume(vitals):
            log(f"Still hot after cooldown: CPU={vitals['cpu_pct']}% RAM={vitals['ram_pct']}%", "WARN")
            return {"status": "thermal_throttle", "vitals": vitals}
        log("Cooled down -- resuming operations")

    # Refresh schedule from task_queue.json (live-reloadable!)
    global SCHEDULE
    SCHEDULE = load_schedule()

    # Build state summary
    summary = build_state_summary()

    # Quick status line
    statuses = []
    for eng, info in summary.items():
        mins = info.get("minutes_since_run", 9999)
        flag = "!!" if info.get("stalled") else ("*" if info.get("due") else "ok")
        statuses.append(f"{eng}:{mins:.0f}m({flag})")
    log(f"HEARTBEAT | CPU={cpu}% RAM={ram}%{temp_str} | " + " | ".join(statuses))

    # Decide what to run
    to_run, method = decide_what_to_run(summary)

    if not to_run:
        return {"ran": [], "method": method}

    # === Emit AI decision to the synaptic bus so other engines can see it ===
    try:
        from mycelium.SYNAPTIC_BUS import emit_batch as _bus_emit_batch
        _bus_emit_batch("AUTONOMIC_NERVE", {
            "decision_method": method,
            "engines_to_run": to_run,
            "timestamp": now.isoformat(),
            "status": "executing",
        }, silent=True)
    except Exception:
        pass  # Bus unavailable -- keep going

    log(f"RUNNING ({method}): {', '.join(to_run)}")

    # Execute engines
    results = {}
    for engine_name in to_run:
        success, result = run_engine(engine_name)
        results[engine_name] = {
            "success": success,
            "status": result.get("status", "?") if isinstance(result, dict) else str(result)[:100],
        }

        # Small pause between engines to avoid overwhelming
        time.sleep(2)

    # Always run TRADING_WIRE after any trade engine
    traded = any(e in to_run for e in ("TURBO_TRADER", "ALPACA_TRADER"))
    if traded and "TRADING_WIRE" not in to_run:
        log("Auto-wiring TRADING_WIRE after trades...")
        success, result = run_engine("TRADING_WIRE")
        results["TRADING_WIRE_auto"] = {"success": success}

    # === Refresh shared consciousness with fresh data ===
    # Lazy import to avoid circular deps; bus reads all state files
    # and broadcasts to the mesh so every engine sees the latest.
    try:
        from mycelium.SYNAPTIC_BUS import run as _bus_refresh
        _bus_refresh()
        log("SYNAPTIC_BUS refreshed after engine cycle")
    except Exception as e:
        log(f"SYNAPTIC_BUS refresh failed (non-fatal): {e}", "WARN")

    # Save autonomic state
    state = {
        "timestamp": now.isoformat(),
        "protocol": "autonomic-nerve-v1",
        "status": "alive",
        "heartbeat_interval": HEARTBEAT_INTERVAL,
        "decision_method": method,
        "engines_run": list(results.keys()),
        "results": results,
        "system_summary": summary,
        "ollama_available": ollama_available()[0],
        "system_vitals": vitals,
    }
    _save(DATA / "autonomic_state.json", state)

    return state


# ================================================================
# MAIN DAEMON LOOP
# ================================================================

def run():
    """
    The autonomic nerve. Runs forever.
    Keeps SolarPunk alive when Claude is asleep.
    """
    log("=" * 60)
    log("AUTONOMIC NERVE -- The heartbeat that never stops")
    log("=" * 60)

    # System vitals
    vitals = get_system_vitals()
    log(f"System: CPU={vitals['cpu_pct']}% | RAM={vitals['ram_pct']}% "
        f"({vitals['ram_used_gb']}/{vitals['ram_total_gb']}GB) | "
        f"Cores={vitals['cpu_count']}")
    temp = vitals.get("temp_c")
    if temp:
        log(f"Temperature: {temp}C")
    log(f"Thermal: throttle at CPU>{THERMAL_CPU_THROTTLE}% or "
        f"RAM>{THERMAL_RAM_THROTTLE}%, resume at CPU<{THERMAL_CPU_RESUME}% "
        f"and RAM<{THERMAL_RAM_RESUME}%")

    # Check Ollama
    available, models = ollama_available()
    if available:
        log(f"Ollama: ONLINE | Models: {', '.join(models)}")
        for preferred in OLLAMA_MODELS:
            if preferred in models:
                log(f"Primary AI: {preferred}")
                break
    else:
        log("Ollama: OFFLINE -- using rule-based logic (still works!)", "WARN")

    # Initial state
    log(f"Schedule: " + " | ".join(f"{k}:{v}m" for k, v in SCHEDULE.items()))
    log(f"Heartbeat: every {HEARTBEAT_INTERVAL}s")
    log("")

    # Run initial heartbeat immediately
    heartbeat()

    # Main loop
    cycle = 0
    while True:
        try:
            time.sleep(HEARTBEAT_INTERVAL)
            cycle += 1
            heartbeat()

        except KeyboardInterrupt:
            log("Shutting down (Ctrl+C)...")
            state = _load(DATA / "autonomic_state.json", {})
            state["status"] = "stopped"
            state["stopped_at"] = datetime.now(timezone.utc).isoformat()
            state["reason"] = "keyboard_interrupt"
            _save(DATA / "autonomic_state.json", state)
            break

        except Exception as e:
            log(f"Heartbeat error: {e}", "ERROR")
            log(traceback.format_exc(), "ERROR")
            # Never die. Sleep and retry.
            time.sleep(30)


def run_once():
    """Run a single heartbeat cycle (for testing or cron)."""
    log("AUTONOMIC NERVE -- single heartbeat")
    available, models = ollama_available()
    log(f"Ollama: {'ONLINE (' + str(len(models)) + ' models)' if available else 'OFFLINE'}")
    return heartbeat()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_once()
    else:
        run()
