#!/usr/bin/env python3
"""
BLOB_BRAIN.py -- The Unified Digital Organism
===============================================
NOT 420 separate engines wired together with JSON files.
ONE LIVING BLOB where every function sees every other function's
state INSTANTLY in shared memory. No files. No wiring. No friction.

Biology: A real brain doesn't have 420 separate programs that read
JSON files from each other. It's one mass of interconnected neurons
where every thought is instantly available to every other thought.
That's what this is.

HOW IT WORKS:
  1. One shared state dict: CONSCIOUSNESS
     - Every engine writes directly to it
     - Every engine reads directly from it
     - No JSON serialization between engines
     - No file I/O between engines
     - Changes are instant and visible everywhere

  2. One process loop: the PULSE
     - Cycles through all engine logic
     - Each engine function mutates CONSCIOUSNESS directly
     - The loop never stops
     - Each cycle = one "thought"

  3. State persistence (to survive restarts):
     - CONSCIOUSNESS dumps to ONE file: data/blob_brain.json
     - Once per cycle, not per engine
     - One write, not 420 writes

  4. External I/O (APIs, web, email):
     - Only happens at the BLOB level
     - Engines request external actions via CONSCIOUSNESS keys
     - The blob's I/O layer processes them in batch

WHAT THIS REPLACES:
  - 420 separate .py files reading/writing JSON to each other
  - NERVOUS_SYSTEM_WIRER (no more wiring needed -- it's all one blob)
  - SYNAPTIC_BUS (no more event bus -- shared memory IS the bus)
  - GIT_GATEKEEPER (one process = no lock conflicts)
  - HOMEOSTASIS reading/writing between engines

CONSCIOUSNESS STRUCTURE:
  {
    "pulse": { cycle count, uptime, last_pulse },
    "equilibrium": { health score, trend, zones },
    "revenue": { total, sources, pending },
    "social": { posts_queued, posts_sent, platforms },
    "engines": { status of every engine function },
    "human_actions": [ things only Meeko can do ],
    "brain": { confidence, decisions, memory },
    "trading": { positions, balance, last_trade },
    "content": { drafts, published, queue },
    "network": { peers, connections, swarm },
    "io_queue": [ external actions to perform ],
    "errors": [ recent errors for self-healing ],
  }

Reports to: data/blob_brain.json (one file, one write per cycle)
"""
import json
import sys
import os
import time
import traceback
import importlib
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# ============================================================
# PATHS
# ============================================================
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
MYCELIUM = ROOT / "mycelium"
sys.path.insert(0, str(MYCELIUM))
os.chdir(str(ROOT))

BLOB_STATE = DATA / "blob_brain.json"
BLOB_LOG = DATA / "blob_brain.log"

# ============================================================
# THE CONSCIOUSNESS -- One shared state, visible to everything
# ============================================================
CONSCIOUSNESS = {
    "pulse": {
        "cycle": 0,
        "started": None,
        "last_pulse": None,
        "uptime_seconds": 0,
    },
    "equilibrium": {
        "score": 50,
        "trend": "stable",
        "zone": "green",
        "components": {},
    },
    "revenue": {
        "total_raised": 0,
        "total_to_gaza": 0,
        "sources": {},
        "pending_actions": [],
    },
    "social": {
        "posts_queued": 0,
        "posts_sent": 0,
        "platforms": {},
    },
    "engines": {},
    "human_actions": [],
    "brain": {
        "confidence": 0,
        "decisions_made": 0,
        "memory": [],
    },
    "trading": {
        "enabled": False,
        "balance": 0,
        "positions": [],
        "last_trade": None,
    },
    "content": {
        "drafts": 0,
        "published": 0,
        "queue": [],
    },
    "network": {
        "peers": 0,
        "swarm_active": False,
    },
    "io_queue": [],
    "errors": [],
    "meta": {
        "total_engines_loaded": 0,
        "blob_version": "1.0",
        "architecture": "unified-consciousness",
    },
}


def load_consciousness():
    """Load previous consciousness state from disk (survive restarts)."""
    global CONSCIOUSNESS
    if BLOB_STATE.exists():
        try:
            saved = json.loads(BLOB_STATE.read_text(encoding="utf-8"))
            # Merge saved state into default structure (preserves new keys)
            _deep_merge(CONSCIOUSNESS, saved)
        except Exception:
            pass  # Start fresh if corrupted


def save_consciousness():
    """Persist consciousness to ONE file. Once per cycle."""
    CONSCIOUSNESS["pulse"]["last_pulse"] = datetime.now(timezone.utc).isoformat()
    BLOB_STATE.write_text(
        json.dumps(CONSCIOUSNESS, indent=2, default=str),
        encoding="utf-8"
    )


def _deep_merge(base, overlay):
    """Merge overlay dict into base dict recursively."""
    for k, v in overlay.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


# ============================================================
# ENGINE ABSORBER -- Suck in all engine logic
# ============================================================
def absorb_engine_states():
    """
    Read existing engine state files and absorb them into CONSCIOUSNESS.
    This bridges the old architecture (420 files) into the blob.
    Over time, engines will write directly to CONSCIOUSNESS instead.
    """
    state_files = list(DATA.glob("*_state.json")) + list(DATA.glob("*_report.json"))
    absorbed = 0
    for sf in state_files:
        try:
            state = json.loads(sf.read_text(encoding="utf-8"))
            engine_name = sf.stem.replace("_state", "").replace("_report", "").upper()

            # Smart status detection -- engines use different field names
            status = (state.get("status")
                      or state.get("state")
                      or ("ok" if state.get("last_run") or state.get("timestamp") else "unknown"))
            # Normalize common statuses to "ok"
            if status in ("active", "alive", "complete", "completed", "running",
                          "wired", "seeded", "ready", "healthy"):
                status = "ok"

            last_run = (state.get("last_run")
                        or state.get("timestamp")
                        or state.get("last_check")
                        or state.get("last_pulse"))

            CONSCIOUSNESS["engines"][engine_name] = {
                "status": status,
                "last_run": last_run,
                "cycles": state.get("cycles", state.get("cycle", 0)),
                "data": {k: v for k, v in state.items()
                         if k not in ("status", "last_run", "timestamp", "cycles", "nervous_system",
                                      "state", "last_check", "last_pulse", "cycle")
                         and (not isinstance(v, (list, dict)) or len(str(v)) < 500)},
            }
            absorbed += 1
        except Exception:
            continue
    CONSCIOUSNESS["meta"]["engines_absorbed"] = absorbed
    return absorbed


def absorb_homeostasis():
    """Pull homeostasis state into consciousness."""
    try:
        h = json.loads((DATA / "homeostasis_state.json").read_text(encoding="utf-8"))
        CONSCIOUSNESS["equilibrium"]["score"] = h.get("equilibrium", 50)
        CONSCIOUSNESS["equilibrium"]["trend"] = h.get("trend", "unknown")
        CONSCIOUSNESS["equilibrium"]["zone"] = h.get("zone", "green")
        CONSCIOUSNESS["equilibrium"]["components"] = h.get("components", {})
    except Exception:
        pass


def absorb_neural_cortex():
    """Pull neural cortex into consciousness."""
    try:
        c = json.loads((DATA / "neural_cortex_state.json").read_text(encoding="utf-8"))
        CONSCIOUSNESS["brain"]["confidence"] = c.get("decision_confidence", 0)
        CONSCIOUSNESS["brain"]["decisions_made"] = c.get("decisions_made", 0)
    except Exception:
        pass


def absorb_revenue():
    """Pull revenue data into consciousness."""
    try:
        r = json.loads((DATA / "kofi_state.json").read_text(encoding="utf-8"))
        CONSCIOUSNESS["revenue"]["total_raised"] = r.get("total_received", 0)
        CONSCIOUSNESS["revenue"]["total_to_gaza"] = r.get("total_to_gaza", 0)
        CONSCIOUSNESS["revenue"]["sources"]["kofi"] = {
            "alive": r.get("alive", False),
            "auto_loops": r.get("auto_loops", 0),
        }
    except Exception:
        pass


def absorb_trading():
    """Pull trading state into consciousness."""
    for name in ["turbo_trader_state", "alpaca_trader_state", "trade_executor_state"]:
        try:
            t = json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))
            CONSCIOUSNESS["trading"]["balance"] = t.get("balance", CONSCIOUSNESS["trading"]["balance"])
            CONSCIOUSNESS["trading"]["last_trade"] = t.get("last_trade", CONSCIOUSNESS["trading"]["last_trade"])
            CONSCIOUSNESS["trading"]["enabled"] = True
        except Exception:
            continue


# ============================================================
# BLOB ENGINE FUNCTIONS -- Each one is a "neuron cluster"
# ============================================================
# These replace individual engine files. They read/write
# CONSCIOUSNESS directly. No files. No wiring. No friction.
# Each neuron is extracted from the real engine logic.

import urllib.request
import urllib.error
import py_compile
import re


def neuron_equilibrium():
    """
    Full homeostasis with 4-zone health assessment.
    Extracted from: HOMEOSTASIS.py (691 lines -> 50 lines)
    """
    eq = CONSCIOUSNESS["equilibrium"]
    engines = CONSCIOUSNESS["engines"]
    brain = CONSCIOUSNESS["brain"]

    total = len(engines)
    if total == 0:
        eq["score"] = 50
        eq["trend"] = "initializing"
        return

    # Zone 1: Engine health (% of engines reporting OK)
    healthy = sum(1 for e in engines.values()
                  if e.get("status") in ("ok", "completed", "running", "wired"))
    engine_health = round(healthy / max(total, 1) * 100)

    # Zone 2: Error rate (inverse of error frequency)
    recent_errors = len([e for e in CONSCIOUSNESS["errors"][-20:]
                        if e.get("ts", "") > (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()])
    error_health = max(0, 100 - recent_errors * 10)

    # Zone 3: Revenue health (any revenue = healthy)
    rev = CONSCIOUSNESS["revenue"]
    rev_health = 80 if rev.get("total_raised", 0) > 0 else 30

    # Zone 4: Brain confidence
    brain_health = brain.get("confidence", 50)

    # Weakest-link weighting: 60% lowest zone + 40% average
    zones = [engine_health, error_health, rev_health, brain_health]
    weakest = min(zones)
    average = sum(zones) / len(zones)
    equilibrium = round(weakest * 0.6 + average * 0.4)

    # Track trend over last 6 readings
    history = eq.get("history", [])
    history.append(equilibrium)
    if len(history) > 6:
        history = history[-6:]
    eq["history"] = history

    old_score = eq.get("score", 50)
    eq["score"] = equilibrium
    eq["trend"] = "rising" if equilibrium > old_score else "falling" if equilibrium < old_score else "stable"
    eq["components"] = {
        "engine_health": engine_health,
        "error_health": error_health,
        "revenue_health": rev_health,
        "brain_health": brain_health,
    }

    if equilibrium >= 80:
        eq["zone"] = "green"
    elif equilibrium >= 50:
        eq["zone"] = "yellow"
    elif equilibrium >= 25:
        eq["zone"] = "orange"
    else:
        eq["zone"] = "red"

    # Generate interventions for weak zones
    interventions = []
    if engine_health < 50:
        interventions.append({"severity": "high", "zone": "engines", "action": f"Only {healthy}/{total} engines healthy"})
    if error_health < 50:
        interventions.append({"severity": "high", "zone": "errors", "action": f"{recent_errors} errors in last hour"})
    if rev_health < 50:
        interventions.append({"severity": "critical", "zone": "revenue", "action": "No revenue detected"})
    eq["interventions"] = interventions


def neuron_error_recovery():
    """
    Self-healing: detect error patterns, flag degraded engines.
    Extracted from: AUTO_HEALER + DEBUG_DOCTOR + IMMUNE_SYSTEM
    """
    errors = CONSCIOUSNESS["errors"]
    if len(errors) > 100:
        CONSCIOUSNESS["errors"] = errors[-100:]

    # Count error frequency by source
    error_sources = defaultdict(int)
    for err in errors[-30:]:
        error_sources[err.get("source", "unknown")] += 1

    # Flag repeatedly failing sources
    degraded = []
    for source, count in error_sources.items():
        if count >= 3:
            CONSCIOUSNESS["engines"].setdefault(source, {})["status"] = "degraded"
            degraded.append(source)

    CONSCIOUSNESS.setdefault("healing", {})["degraded_engines"] = degraded
    CONSCIOUSNESS["healing"]["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_immune_system():
    """
    Code integrity check: syntax-verify all engines.
    Extracted from: IMMUNE_SYSTEM.py (313 lines -> 25 lines)
    """
    engine_files = sorted(MYCELIUM.glob("*.py"))
    infections = []
    for fp in engine_files:
        try:
            py_compile.compile(str(fp), doraise=True)
        except py_compile.PyCompileError as e:
            infections.append({"engine": fp.stem, "error": str(e)[:100]})

    immune = CONSCIOUSNESS.setdefault("immune", {})
    immune["total_scanned"] = len(engine_files)
    immune["infections"] = len(infections)
    immune["infected_list"] = infections[:10]
    immune["last_scan"] = datetime.now(timezone.utc).isoformat()


def neuron_revenue_audit():
    """
    Revenue pipeline health check: verify buy links work.
    Extracted from: REVENUE_AUDIT.py (143 lines -> 35 lines)
    """
    rev = CONSCIOUSNESS["revenue"]
    urls_to_check = [
        ("Ko-fi Shop", "https://ko-fi.com/meekotharaccoon", "critical"),
        ("Ko-fi Gaza Rose", "https://ko-fi.com/s/b29fb5fc44", "critical"),
        ("GitHub Repo", "https://github.com/meekotharaccoon-cell/meeko-nerve-center", "high"),
    ]

    results = []
    for name, url, priority in urls_to_check:
        try:
            req = urllib.request.Request(url, method="HEAD",
                                         headers={"User-Agent": "SolarPunk-BlobBrain/1.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                results.append({"name": name, "url": url, "status": r.status, "ok": True})
        except Exception as e:
            results.append({"name": name, "url": url, "status": str(e)[:60], "ok": False})

    working = sum(1 for r in results if r["ok"])
    broken = len(results) - working

    rev["audit"] = {
        "working": working,
        "broken": broken,
        "results": results,
        "last_audit": datetime.now(timezone.utc).isoformat(),
    }
    rev["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_secrets_audit():
    """
    Check which API keys are configured.
    Extracted from: SECRETS_CHECKER.py (362 lines -> 30 lines)
    """
    CRITICAL_SECRETS = [
        ("ANTHROPIC_API_KEY", "AI Brain", "critical"),
        ("GITHUB_TOKEN", "GitHub API", "critical"),
        ("GMAIL_ADDRESS", "Email", "high"),
        ("GMAIL_APP_PASSWORD", "Email Auth", "high"),
        ("GUMROAD_SECRET", "Revenue", "critical"),
        ("BLUESKY_IDENTIFIER", "Social", "medium"),
        ("BLUESKY_APP_PASSWORD", "Social Auth", "medium"),
        ("DEVTO_API_KEY", "Dev.to", "medium"),
        ("MASTODON_ACCESS_TOKEN", "Mastodon", "medium"),
        ("KALSHI_API_KEY", "Trading", "high"),
    ]

    configured = 0
    missing_critical = []
    for name, purpose, priority in CRITICAL_SECRETS:
        if os.environ.get(name):
            configured += 1
        elif priority == "critical":
            missing_critical.append(name)

    secrets = CONSCIOUSNESS.setdefault("secrets", {})
    secrets["configured"] = configured
    secrets["total"] = len(CRITICAL_SECRETS)
    secrets["missing_critical"] = missing_critical
    secrets["coverage_pct"] = round(configured / max(len(CRITICAL_SECRETS), 1) * 100)
    secrets["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_social_awareness():
    """
    Track social posting capacity and queue state.
    Extracted from: BLUESKY_ENGINE + DEV_TO + MASTODON + SOCIAL_PROMOTER + AUTONOMOUS_PUBLISHER
    """
    social = CONSCIOUSNESS["social"]

    # Detect available channels by env vars
    channels = {}
    if os.environ.get("BLUESKY_IDENTIFIER"):
        channels["bluesky"] = True
    if os.environ.get("DEVTO_API_KEY"):
        channels["devto"] = True
    if os.environ.get("MASTODON_ACCESS_TOKEN"):
        channels["mastodon"] = True
    if os.environ.get("X_API_KEY"):
        channels["twitter"] = True
    if os.environ.get("REDDIT_CLIENT_ID"):
        channels["reddit"] = True
    channels["github_gist"] = bool(os.environ.get("GITHUB_TOKEN"))

    social["channels_available"] = channels
    social["channel_count"] = sum(1 for v in channels.values() if v)

    # Read social queue if it exists
    try:
        sq = json.loads((DATA / "social_queue.json").read_text(encoding="utf-8"))
        posts = sq.get("posts", [])
        social["posts_queued"] = len([p for p in posts if not p.get("sent")])
        social["posts_sent"] = len([p for p in posts if p.get("sent")])
    except Exception:
        pass

    social["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_brain_confidence():
    """
    Neural confidence score from system state.
    Extracted from: NEURAL_CORTEX decision_confidence logic
    """
    brain = CONSCIOUSNESS["brain"]
    eq = CONSCIOUSNESS["equilibrium"]
    secrets = CONSCIOUSNESS.get("secrets", {})
    immune = CONSCIOUSNESS.get("immune", {})

    # Multi-factor confidence
    health_factor = eq.get("score", 50) / 100
    error_factor = max(0, 1 - len(CONSCIOUSNESS["errors"]) / 30)
    secret_factor = secrets.get("coverage_pct", 0) / 100
    code_factor = 1 - (immune.get("infections", 0) / max(immune.get("total_scanned", 1), 1))

    confidence = round(
        (health_factor * 0.35 +
         error_factor * 0.25 +
         secret_factor * 0.20 +
         code_factor * 0.20) * 100
    )

    brain["confidence"] = min(confidence, 100)
    brain["factors"] = {
        "health": round(health_factor * 100),
        "errors": round(error_factor * 100),
        "secrets": round(secret_factor * 100),
        "code_integrity": round(code_factor * 100),
    }
    brain["decisions_made"] = brain.get("decisions_made", 0) + 1


def neuron_bottleneck_scan():
    """
    Identify what's blocking progress.
    Extracted from: BOTTLENECK_SCANNER.py (277 lines -> 25 lines)
    """
    bottlenecks = []

    # Check critical secrets
    for name in CONSCIOUSNESS.get("secrets", {}).get("missing_critical", []):
        bottlenecks.append({"severity": "critical", "type": "secret", "detail": f"Missing {name}"})

    # Check code infections
    for inf in CONSCIOUSNESS.get("immune", {}).get("infected_list", []):
        bottlenecks.append({"severity": "high", "type": "syntax", "detail": f"{inf['engine']}: {inf['error'][:60]}"})

    # Check broken revenue links
    for r in CONSCIOUSNESS.get("revenue", {}).get("audit", {}).get("results", []):
        if not r.get("ok"):
            bottlenecks.append({"severity": "critical", "type": "revenue", "detail": f"Broken: {r['name']}"})

    # Check low health zones
    for zone, score in CONSCIOUSNESS.get("equilibrium", {}).get("components", {}).items():
        if score < 30:
            bottlenecks.append({"severity": "high", "type": "health", "detail": f"{zone} at {score}%"})

    bn = CONSCIOUSNESS.setdefault("bottlenecks", {})
    bn["total"] = len(bottlenecks)
    bn["critical"] = len([b for b in bottlenecks if b["severity"] == "critical"])
    bn["list"] = bottlenecks[:20]
    bn["last_scan"] = datetime.now(timezone.utc).isoformat()


def neuron_content_pipeline():
    """
    Content generation awareness.
    Extracted from: SUBSTACK_ENGINE + CONTENT_HARVESTER + GROWTH_FLYWHEEL
    """
    content = CONSCIOUSNESS["content"]

    # Count draft files
    drafts = list(DATA.glob("*_draft*")) + list(DATA.glob("*_content*"))
    content["drafts"] = len(drafts)

    # Check newsletter state
    try:
        ns = json.loads((DATA / "newsletter_state.json").read_text(encoding="utf-8"))
        content["newsletters_sent"] = ns.get("total_sent", 0)
        content["last_newsletter"] = ns.get("last_sent")
    except Exception:
        pass

    content["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_trading_awareness():
    """
    Trading system health and position monitoring.
    Extracted from: TURBO_TRADER + TRADE_EXECUTOR + ALPACA_TRADER
    """
    trading = CONSCIOUSNESS["trading"]

    # Check if trading secrets are available
    trading["kalshi_ready"] = bool(os.environ.get("KALSHI_API_KEY"))
    trading["alpaca_ready"] = bool(os.environ.get("ALPACA_API_KEY"))

    # Read latest trade state
    for state_file in ["turbo_trader_state", "trade_executor_state", "alpaca_trader_state"]:
        try:
            ts = json.loads((DATA / f"{state_file}.json").read_text(encoding="utf-8"))
            trading["balance"] = ts.get("balance", trading.get("balance", 0))
            trading["last_trade"] = ts.get("last_trade", trading.get("last_trade"))
            if ts.get("positions"):
                trading["active_positions"] = len(ts["positions"])
        except Exception:
            continue

    trading["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_email_awareness():
    """
    Email system state monitoring.
    Extracted from: EMAIL_BRAIN + HUMAN_CONNECTOR + SCAM_SHIELD
    """
    email = CONSCIOUSNESS.setdefault("email", {})

    try:
        eb = json.loads((DATA / "email_brain_state.json").read_text(encoding="utf-8"))
        email["processed"] = eb.get("processed", 0)
        email["categories"] = {
            "personal": eb.get("personal", 0),
            "business": eb.get("business", 0),
            "revenue": eb.get("revenue", 0),
            "appointments": eb.get("appointments", 0),
        }
    except Exception:
        pass

    try:
        ss = json.loads((DATA / "scam_shield_state.json").read_text(encoding="utf-8"))
        email["scams_caught"] = ss.get("scams_caught", 0)
        email["safe_verified"] = ss.get("safe_verified", 0)
    except Exception:
        pass

    try:
        hc = json.loads((DATA / "human_connector_state.json").read_text(encoding="utf-8"))
        email["humans_met"] = len(hc.get("humans_met", []))
    except Exception:
        pass

    email["gmail_ready"] = bool(os.environ.get("GMAIL_ADDRESS") and os.environ.get("GMAIL_APP_PASSWORD"))
    email["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_grant_tracker():
    """
    Grant application pipeline.
    Extracted from: GRANT_APPLICANT.py
    """
    grants = CONSCIOUSNESS.setdefault("grants", {})
    try:
        ga = json.loads((DATA / "grant_applicant_state.json").read_text(encoding="utf-8"))
        grants["total_applied"] = ga.get("total_applied", 0)
        grants["applied_list"] = ga.get("applied", [])[-5:]
    except Exception:
        pass

    try:
        gf = json.loads((DATA / "grants_found.json").read_text(encoding="utf-8"))
        grants["available"] = len(gf.get("grants", []))
    except Exception:
        pass

    grants["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_analytics():
    """
    GitHub traffic and growth metrics.
    Extracted from: ANALYTICS_ENGINE.py (109 lines -> 10 lines awareness)
    """
    analytics = CONSCIOUSNESS.setdefault("analytics", {})
    try:
        a = json.loads((DATA / "analytics_state.json").read_text(encoding="utf-8"))
        analytics["stars"] = a.get("stars", 0)
        analytics["views_14d"] = a.get("views_14d", 0)
        analytics["trend"] = a.get("trend", "unknown")
        analytics["clones_14d"] = a.get("clones_14d", 0)
    except Exception:
        pass
    analytics["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_meta_awareness():
    """
    The blob's awareness of itself. Engine count, coverage, architecture.
    """
    meta = CONSCIOUSNESS["meta"]
    meta["total_engines_loaded"] = len(CONSCIOUSNESS["engines"])
    meta["neuron_count"] = len(NEURONS)
    meta["consciousness_keys"] = list(CONSCIOUSNESS.keys())
    meta["data_files"] = len(list(DATA.glob("*.json")))
    meta["engine_files"] = len(list(MYCELIUM.glob("*.py")))
    meta["last_pulse"] = datetime.now(timezone.utc).isoformat()


# ============================================================
# THE NEURON REGISTRY -- All blob functions in execution order
# ============================================================
NEURONS = [
    # Core vitals
    ("EQUILIBRIUM", neuron_equilibrium),
    ("ERROR_RECOVERY", neuron_error_recovery),
    ("IMMUNE_SYSTEM", neuron_immune_system),
    ("BRAIN_CONFIDENCE", neuron_brain_confidence),
    # Revenue & business
    ("REVENUE_AUDIT", neuron_revenue_audit),
    ("SECRETS_AUDIT", neuron_secrets_audit),
    ("BOTTLENECK_SCAN", neuron_bottleneck_scan),
    ("GRANT_TRACKER", neuron_grant_tracker),
    # Communication
    ("SOCIAL_AWARENESS", neuron_social_awareness),
    ("EMAIL_AWARENESS", neuron_email_awareness),
    ("CONTENT_PIPELINE", neuron_content_pipeline),
    # Markets & growth
    ("TRADING_AWARENESS", neuron_trading_awareness),
    ("ANALYTICS", neuron_analytics),
    # Self-awareness
    ("META_AWARENESS", neuron_meta_awareness),
]


# ============================================================
# LEGACY BRIDGE -- Run old engines inside the blob
# ============================================================
def run_legacy_engine(name, timeout=60):
    """
    Import and run a legacy engine's run() function inside the blob.
    Its state changes land in its own files, which get absorbed next cycle.
    Over time, logic migrates from legacy engines into NEURONS.
    """
    try:
        mod = importlib.import_module(name)
        if hasattr(mod, "run"):
            mod.run()
            CONSCIOUSNESS["engines"][name] = {
                "status": "ok",
                "last_run": datetime.now(timezone.utc).isoformat(),
                "method": "legacy_bridge",
            }
            return True
    except Exception as e:
        CONSCIOUSNESS["errors"].append({
            "source": name,
            "error": str(e)[:200],
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        CONSCIOUSNESS["engines"][name] = {
            "status": "error",
            "last_run": datetime.now(timezone.utc).isoformat(),
            "error": str(e)[:100],
        }
    return False


# Priority engines to run through legacy bridge each cycle
PRIORITY_LEGACY = [
    # These are the most critical engines until their logic is absorbed
    # Add/remove as logic migrates into NEURONS
]


# ============================================================
# THE PULSE -- One infinite loop. One consciousness. One brain.
# ============================================================
def pulse():
    """
    One cycle of the blob brain.
    Absorb -> Think -> Act -> Persist
    """
    ts = datetime.now(timezone.utc)
    CONSCIOUSNESS["pulse"]["cycle"] += 1
    cycle = CONSCIOUSNESS["pulse"]["cycle"]

    # Phase 1: ABSORB -- Pull in state from old-architecture files
    absorbed = absorb_engine_states()
    absorb_homeostasis()
    absorb_neural_cortex()
    absorb_revenue()
    absorb_trading()

    # Phase 2: THINK -- Run all neuron functions
    for name, func in NEURONS:
        try:
            func()
        except Exception as e:
            CONSCIOUSNESS["errors"].append({
                "source": f"neuron:{name}",
                "error": str(e)[:200],
                "ts": ts.isoformat(),
            })

    # Phase 3: ACT -- Run priority legacy engines through bridge
    for engine_name in PRIORITY_LEGACY:
        run_legacy_engine(engine_name)

    # Phase 4: PERSIST -- One write to disk
    if CONSCIOUSNESS["pulse"].get("started"):
        started = datetime.fromisoformat(CONSCIOUSNESS["pulse"]["started"])
        CONSCIOUSNESS["pulse"]["uptime_seconds"] = (ts - started).total_seconds()

    save_consciousness()

    return cycle


def run():
    """Entry point -- run one pulse cycle (for OMNIBUS compatibility)."""
    load_consciousness()

    if not CONSCIOUSNESS["pulse"].get("started"):
        CONSCIOUSNESS["pulse"]["started"] = datetime.now(timezone.utc).isoformat()

    cycle = pulse()

    eq = CONSCIOUSNESS["equilibrium"]
    brain = CONSCIOUSNESS["brain"]
    meta = CONSCIOUSNESS["meta"]

    print("=" * 60)
    print("  BLOB BRAIN -- Unified Digital Organism")
    print("=" * 60)
    print(f"  Cycle:       {cycle}")
    print(f"  Engines:     {len(CONSCIOUSNESS['engines'])} absorbed")
    print(f"  Health:      {eq['score']}% [{eq['zone']}] {eq['trend']}")
    print(f"  Confidence:  {brain['confidence']}%")
    print(f"  Revenue:     ${CONSCIOUSNESS['revenue']['total_raised']:.2f}")
    print(f"  Gaza Fund:   ${CONSCIOUSNESS['revenue']['total_to_gaza']:.2f}")
    print(f"  Errors:      {len(CONSCIOUSNESS['errors'])} recent")
    print(f"  State:       data/blob_brain.json (ONE file)")
    print(f"  Architecture: {meta['architecture']}")
    print()
    print("  One blob. One consciousness. No wiring. No friction.")
    print("=" * 60)

    return CONSCIOUSNESS


def run_forever(interval=60):
    """Run the blob brain continuously. The heartbeat that never stops."""
    load_consciousness()

    if not CONSCIOUSNESS["pulse"].get("started"):
        CONSCIOUSNESS["pulse"]["started"] = datetime.now(timezone.utc).isoformat()

    print("BLOB BRAIN starting continuous pulse...")
    print(f"  Interval: {interval}s")
    print(f"  Architecture: unified-consciousness")
    print(f"  Mode: infinite linked blob process")
    print()

    while True:
        try:
            cycle = pulse()
            eq = CONSCIOUSNESS["equilibrium"]
            print(f"  [Cycle {cycle}] Health={eq['score']}% "
                  f"Engines={len(CONSCIOUSNESS['engines'])} "
                  f"Errors={len(CONSCIOUSNESS['errors'])} "
                  f"Confidence={CONSCIOUSNESS['brain']['confidence']}%")
        except Exception as e:
            print(f"  [ERROR] {e}")
            CONSCIOUSNESS["errors"].append({
                "source": "pulse_loop",
                "error": str(e)[:200],
                "ts": datetime.now(timezone.utc).isoformat(),
            })
            save_consciousness()

        time.sleep(interval)


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        interval = 60
        for arg in sys.argv:
            if arg.startswith("--interval="):
                interval = int(arg.split("=")[1])
        run_forever(interval)
    else:
        run()
