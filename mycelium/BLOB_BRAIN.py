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


def neuron_bridge_builder():
    """
    AUTO-BRIDGE: Load every available secret and credential, connect
    to every available service, report what's live.
    This is the neuron that turns keys into connections.
    """
    bridges = CONSCIOUSNESS.setdefault("bridges", {"connected": [], "failed": [], "available_keys": 0})
    connected = []
    failed = []

    # ── LOCAL SECRET FILES ──
    secrets_dir = DATA / ".secrets"
    local_creds = {}
    if secrets_dir.exists():
        for sf in secrets_dir.glob("*.json"):
            try:
                local_creds[sf.stem] = json.loads(sf.read_text(encoding="utf-8"))
            except Exception:
                pass
        if (secrets_dir / "kalshi_rsa.pem").exists():
            local_creds["kalshi_rsa_pem"] = True

    # ── LOAD KALSHI TRADING CREDS ──
    if "kalshi" in local_creds:
        kc = local_creds["kalshi"]
        os.environ.setdefault("KALSHI_API_KEY", kc.get("api_key", ""))
        CONSCIOUSNESS["trading"]["kalshi_ready"] = True
        CONSCIOUSNESS["trading"]["kalshi_balance"] = kc.get("balance_usd", 0)
        connected.append("KALSHI_TRADING")

    # ── LOAD ALPACA TRADING CREDS ──
    if "alpaca" in local_creds:
        ac = local_creds["alpaca"]
        os.environ.setdefault("ALPACA_API_KEY", ac.get("api_key", ac.get("key_id", "")))
        os.environ.setdefault("ALPACA_SECRET_KEY", ac.get("secret_key", ac.get("secret", "")))
        CONSCIOUSNESS["trading"]["alpaca_ready"] = True
        connected.append("ALPACA_TRADING")

    # ── LOAD POLYMARKET CREDS ──
    if "polymarket" in local_creds:
        CONSCIOUSNESS["trading"]["polymarket_ready"] = True
        connected.append("POLYMARKET")

    # ── TEST ANTHROPIC (already in env) ──
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key and api_key.startswith("sk-ant-"):
        connected.append("ANTHROPIC_AI")
        CONSCIOUSNESS["brain"]["ai_available"] = True
    else:
        failed.append("ANTHROPIC_AI")

    # ── TEST GITHUB ──
    gh_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_PAT", "")
    if gh_token:
        os.environ.setdefault("GITHUB_TOKEN", gh_token)
        try:
            req = urllib.request.Request(
                "https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center",
                headers={"Authorization": f"token {gh_token}",
                         "User-Agent": "SolarPunk-BlobBrain/1.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                repo = json.loads(r.read().decode())
                CONSCIOUSNESS["analytics"]["stars"] = repo.get("stargazers_count", 0)
                CONSCIOUSNESS["analytics"]["forks"] = repo.get("forks_count", 0)
                CONSCIOUSNESS["analytics"]["watchers"] = repo.get("subscribers_count", 0)
                connected.append("GITHUB_API")
        except Exception as e:
            failed.append(f"GITHUB_API:{str(e)[:40]}")
    else:
        # Try gh CLI auth
        try:
            import subprocess
            r = subprocess.run(["gh", "api", "repos/meekotharaccoon-cell/meeko-nerve-center"],
                             capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
            if r.returncode == 0:
                repo = json.loads(r.stdout)
                CONSCIOUSNESS["analytics"]["stars"] = repo.get("stargazers_count", 0)
                CONSCIOUSNESS["analytics"]["forks"] = repo.get("forks_count", 0)
                connected.append("GITHUB_CLI")
        except Exception:
            failed.append("GITHUB_API:no_token")

    # ── COUNT ALL AVAILABLE ENV KEYS ──
    known_keys = [
        "ANTHROPIC_API_KEY", "GITHUB_TOKEN", "GH_PAT", "GMAIL_ADDRESS",
        "GMAIL_APP_PASSWORD", "GUMROAD_SECRET", "GUMROAD_ID", "BLUESKY_IDENTIFIER",
        "BLUESKY_APP_PASSWORD", "DEVTO_API_KEY", "MASTODON_ACCESS_TOKEN",
        "MASTODON_TOKEN", "X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN",
        "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "KALSHI_API_KEY",
        "ALPACA_API_KEY", "KOFI_TOKEN", "GROQ_API_KEY", "HF_TOKEN",
        "DISCORD_BOT_TOKEN", "YOUTUBE_API_KEY", "PAYPAL_CLIENT_ID",
        "COINBASE_COMMERCE_KEY", "STRIPE_SECRET", "SERPAPI_KEY",
        "OPENROUTER_KEY", "GEMINI_API_KEY", "KIMI_API_KEY",
    ]
    available = sum(1 for k in known_keys if os.environ.get(k))

    bridges["connected"] = connected
    bridges["failed"] = failed
    bridges["available_keys"] = available
    bridges["total_keys_known"] = len(known_keys)
    bridges["local_cred_files"] = list(local_creds.keys())
    bridges["last_bridge"] = datetime.now(timezone.utc).isoformat()

    # Update secrets with real count
    CONSCIOUSNESS["secrets"]["configured"] = available
    CONSCIOUSNESS["secrets"]["total"] = len(known_keys)
    CONSCIOUSNESS["secrets"]["coverage_pct"] = round(available / len(known_keys) * 100)


def neuron_github_analytics():
    """
    LIVE: Fetch real GitHub traffic data.
    Uses gh CLI (already authenticated on this machine).
    """
    analytics = CONSCIOUSNESS.setdefault("analytics", {})
    try:
        import subprocess
        # Traffic views
        r = subprocess.run(
            ["gh", "api", "repos/meekotharaccoon-cell/meeko-nerve-center/traffic/views"],
            capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
        if r.returncode == 0:
            data = json.loads(r.stdout)
            analytics["views_14d"] = data.get("count", 0)
            analytics["unique_visitors"] = data.get("uniques", 0)
            connected = True

        # Traffic clones
        r2 = subprocess.run(
            ["gh", "api", "repos/meekotharaccoon-cell/meeko-nerve-center/traffic/clones"],
            capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
        if r2.returncode == 0:
            data2 = json.loads(r2.stdout)
            analytics["clones_14d"] = data2.get("count", 0)

        # Referrers
        r3 = subprocess.run(
            ["gh", "api", "repos/meekotharaccoon-cell/meeko-nerve-center/traffic/popular/referrers"],
            capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
        if r3.returncode == 0:
            refs = json.loads(r3.stdout)
            analytics["top_referrers"] = [{"site": r.get("referrer"), "count": r.get("count")}
                                          for r in refs[:5]]

        analytics["live_fetch"] = True
    except Exception as e:
        analytics["live_fetch"] = False
        analytics["fetch_error"] = str(e)[:60]

    analytics["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_ai_think():
    """
    LIVE: Use the Anthropic API to think about what SolarPunk should do next.
    Runs once per pulse. Reads full consciousness, outputs priorities.
    """
    brain = CONSCIOUSNESS["brain"]
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or not brain.get("ai_available"):
        return

    # Rate limit: only think every 5 cycles
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 5 != 0:
        return

    # Build a compact consciousness summary for the AI
    eq = CONSCIOUSNESS["equilibrium"]
    bridges = CONSCIOUSNESS.get("bridges", {})
    bottlenecks = CONSCIOUSNESS.get("bottlenecks", {})
    rev = CONSCIOUSNESS["revenue"]

    prompt = (
        f"You are SolarPunk's brain. Cycle {cycle}. "
        f"Health: {eq.get('score')}% [{eq.get('zone')}]. "
        f"Bridges connected: {bridges.get('connected', [])}. "
        f"Bottlenecks: {[b['detail'] for b in bottlenecks.get('list', [])[:3]]}. "
        f"Revenue: ${rev.get('total_raised', 0):.2f}. "
        f"Buy links: all {rev.get('audit', {}).get('working', 0)} working. "
        f"What are the TOP 3 actions SolarPunk should take RIGHT NOW to generate revenue "
        f"and grow? Be specific and actionable. 50 words max."
    )

    try:
        body = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 150,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            })
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read().decode())
            thought = result["content"][0]["text"]
            brain["last_thought"] = thought
            brain["last_thought_cycle"] = cycle
            brain["thoughts"] = brain.get("thoughts", [])
            brain["thoughts"].append({"cycle": cycle, "thought": thought,
                                       "ts": datetime.now(timezone.utc).isoformat()})
            # Keep last 10 thoughts
            if len(brain["thoughts"]) > 10:
                brain["thoughts"] = brain["thoughts"][-10:]
    except Exception as e:
        brain["think_error"] = str(e)[:80]


def neuron_legacy_fire():
    """
    LIVE: Run the most critical legacy engines through the blob.
    These are engines that DO things (not just monitor).
    """
    fired = CONSCIOUSNESS.setdefault("legacy_fired", {"engines": [], "last_fire": None})
    cycle = CONSCIOUSNESS["pulse"]["cycle"]

    # Only fire legacy engines every 3 cycles to avoid hammering
    if cycle % 3 != 0:
        return

    # Priority engines to fire (only ones that have real effect)
    priority = []

    # If we have Anthropic, fire content-generating engines
    if CONSCIOUSNESS["brain"].get("ai_available"):
        priority.append("GROWTH_FLYWHEEL")

    # If we have trading creds, fire trading awareness
    if CONSCIOUSNESS["trading"].get("kalshi_ready"):
        priority.append("TURBO_TRADER")

    results = []
    for name in priority[:2]:  # Max 2 per cycle
        try:
            success = run_legacy_engine(name)
            results.append({"engine": name, "ok": success, "ts": datetime.now(timezone.utc).isoformat()})
        except Exception as e:
            results.append({"engine": name, "ok": False, "error": str(e)[:60]})

    fired["engines"] = results
    fired["last_fire"] = datetime.now(timezone.utc).isoformat()


def _kalshi_auth_get(api_key, private_key, path):
    """Make an RSA-signed GET request to Kalshi v2 API."""
    import base64
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding as asym_padding

    timestamp = str(int(time.time() * 1000))
    message = (timestamp + "GET" + path).encode()
    signature = private_key.sign(
        message,
        asym_padding.PSS(mgf=asym_padding.MGF1(hashes.SHA256()),
                         salt_length=asym_padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    req = urllib.request.Request(
        f"https://api.elections.kalshi.com{path}",
        headers={
            "KALSHI-ACCESS-KEY": api_key,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode(),
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json",
        })
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read().decode())


def neuron_market_scanner():
    """
    LIVE: Full Kalshi prediction market intelligence.
    - RSA-authenticated portfolio reads (balance, positions, P&L)
    - Public market scanning (249+ liquid markets)
    - Opportunity detection (tight spreads, high volume, near expiry)
    - Position monitoring with live market prices
    """
    markets = CONSCIOUSNESS.setdefault("markets", {
        "kalshi_open": [], "opportunities": [], "last_scan": None,
        "balance_cents": 0, "portfolio_value_cents": 0,
        "positions": [], "realized_pnl": 0, "total_fees": 0,
    })
    if not CONSCIOUSNESS["trading"].get("kalshi_ready"):
        return

    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Scan every 3 cycles
    if cycle % 3 != 0 and cycle != 1:
        return

    creds_path = Path("data/.secrets/kalshi.json")
    rsa_path = Path("data/.secrets/kalshi_rsa.pem")
    if not creds_path.exists() or not rsa_path.exists():
        markets["status"] = "missing_credentials"
        return

    try:
        creds = json.loads(creds_path.read_text(encoding="utf-8"))
        api_key = creds.get("api_key", "")

        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        with open(str(rsa_path), "rb") as f:
            private_key = load_pem_private_key(f.read(), password=None)
    except Exception as e:
        markets["auth_error"] = str(e)[:80]
        return

    # --- PHASE A: Portfolio balance (authenticated) ---
    try:
        bal = _kalshi_auth_get(api_key, private_key, "/trade-api/v2/portfolio/balance")
        markets["balance_cents"] = bal.get("balance", 0)
        markets["portfolio_value_cents"] = bal.get("portfolio_value", 0)
        markets["balance_usd"] = round(bal.get("balance", 0) / 100, 2)
        markets["portfolio_usd"] = round(bal.get("portfolio_value", 0) / 100, 2)
        markets["total_usd"] = round((bal.get("balance", 0) + bal.get("portfolio_value", 0)) / 100, 2)

        # Update trading consciousness
        CONSCIOUSNESS["trading"]["kalshi_balance"] = markets["balance_usd"]
        CONSCIOUSNESS["trading"]["kalshi_portfolio"] = markets["portfolio_usd"]
        CONSCIOUSNESS["trading"]["kalshi_total"] = markets["total_usd"]
    except Exception as e:
        markets["balance_error"] = str(e)[:80]

    # --- PHASE B: Open positions (authenticated) ---
    try:
        pos_data = _kalshi_auth_get(api_key, private_key, "/trade-api/v2/portfolio/positions")
        raw_positions = pos_data.get("market_positions", [])
        active_positions = []
        total_pnl = 0
        total_fees = 0
        for p in raw_positions:
            exposure = float(p.get("market_exposure_dollars", "0"))
            pnl = float(p.get("realized_pnl_dollars", "0"))
            fees = float(p.get("fees_paid_dollars", "0"))
            total_pnl += pnl
            total_fees += fees
            if exposure > 0 or float(p.get("position_fp", "0")) != 0:
                active_positions.append({
                    "ticker": p.get("ticker", "?"),
                    "position": float(p.get("position_fp", "0")),
                    "exposure_usd": exposure,
                    "pnl_usd": pnl,
                    "fees_usd": fees,
                })
        markets["positions"] = active_positions
        markets["active_position_count"] = len(active_positions)
        markets["realized_pnl"] = round(total_pnl, 2)
        markets["total_fees"] = round(total_fees, 2)
        markets["total_trades"] = len(raw_positions)
    except Exception as e:
        markets["positions_error"] = str(e)[:80]

    # --- PHASE C: Scan public markets for opportunities ---
    try:
        req = urllib.request.Request(
            "https://api.elections.kalshi.com/trade-api/v2/events?limit=50&status=open&with_nested_markets=true",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())

        liquid = []
        for ev in data.get("events", []):
            for m in ev.get("markets", []):
                try:
                    ya = float(str(m.get("yes_ask_dollars", "0")))
                    yb = float(str(m.get("yes_bid_dollars", "0")))
                    vol = float(str(m.get("volume_fp", "0")))
                    oi = float(str(m.get("open_interest_fp", "0")))
                except (ValueError, TypeError):
                    continue
                if vol > 1000 and ya > 0 and yb > 0:
                    spread = ya - yb
                    liquid.append({
                        "event": ev.get("title", "")[:50],
                        "sub": (m.get("yes_sub_title") or "")[:40],
                        "category": ev.get("category", ""),
                        "ticker": m.get("ticker", ""),
                        "yes_bid": yb, "yes_ask": ya,
                        "spread": round(spread, 4),
                        "volume": vol, "oi": oi,
                        "close": m.get("close_time", "")[:10],
                    })

        # Sort by volume (most liquid first)
        liquid.sort(key=lambda x: x["volume"], reverse=True)
        markets["kalshi_open"] = liquid[:30]  # Top 30 liquid markets
        markets["total_liquid_markets"] = len(liquid)

        # Find opportunities: tight spread + high volume
        opportunities = [m for m in liquid if m["spread"] <= 0.02 and m["volume"] > 5000]
        markets["opportunities"] = opportunities[:10]
        markets["opportunity_count"] = len(opportunities)

    except Exception as e:
        markets["scan_error"] = str(e)[:80]

    # Check exchange status
    try:
        req = urllib.request.Request(
            "https://api.elections.kalshi.com/trade-api/v2/exchange/status",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            status = json.loads(r.read().decode())
            markets["exchange_status"] = status.get("exchange_active", False)
            markets["trading_active"] = status.get("trading_active", False)
    except Exception:
        pass

    markets["last_scan"] = datetime.now(timezone.utc).isoformat()
    markets["status"] = "active"

    # --- PHASE D: Whale tracker (every 6 cycles) ---
    if cycle % 6 != 0 and cycle != 1:
        return
    whales = markets.setdefault("whale_signals", [])
    WHALE_THRESHOLD = 50  # 50+ contracts = whale
    whale_hits = []

    # Scan trade feeds for the top 10 liquid markets
    top_tickers = [m["ticker"] for m in markets.get("kalshi_open", [])[:10] if m.get("ticker")]
    for ticker in top_tickers:
        try:
            req = urllib.request.Request(
                f"https://api.elections.kalshi.com/trade-api/v2/markets/trades?ticker={ticker}&limit=20",
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode())
                for trade in data.get("trades", []):
                    count = float(str(trade.get("count_fp", "0")))
                    price = float(str(trade.get("yes_price_dollars", "0")))
                    side = trade.get("taker_side", "?")
                    trade_value = count * price
                    if count >= WHALE_THRESHOLD:
                        # Find the event name from our liquid markets list
                        event_name = ""
                        for lm in markets.get("kalshi_open", []):
                            if lm.get("ticker") == ticker:
                                event_name = lm.get("event", "")
                                break
                        whale_hits.append({
                            "ticker": ticker,
                            "event": event_name,
                            "side": side,
                            "count": count,
                            "price": price,
                            "value_usd": round(trade_value, 2),
                            "time": trade.get("created_time", "")[:19],
                        })
        except Exception:
            pass

    if whale_hits:
        whale_hits.sort(key=lambda x: x["value_usd"], reverse=True)
        markets["whale_signals"] = whale_hits[:20]
        markets["whale_count"] = len(whale_hits)
        markets["biggest_whale"] = whale_hits[0] if whale_hits else None

        # Summarize whale sentiment per market
        sentiment = {}
        for w in whale_hits:
            t = w["ticker"]
            if t not in sentiment:
                sentiment[t] = {"yes_volume": 0, "no_volume": 0, "event": w["event"]}
            if w["side"] == "yes":
                sentiment[t]["yes_volume"] += w["count"]
            else:
                sentiment[t]["no_volume"] += w["count"]
        # Add conviction score
        for t, s in sentiment.items():
            total = s["yes_volume"] + s["no_volume"]
            if total > 0:
                s["conviction"] = round(max(s["yes_volume"], s["no_volume"]) / total * 100)
                s["direction"] = "YES" if s["yes_volume"] > s["no_volume"] else "NO"
            else:
                s["conviction"] = 0
                s["direction"] = "neutral"
        markets["whale_sentiment"] = sentiment
    else:
        markets["whale_count"] = 0


def neuron_whale_watch():
    """
    LIVE: Cross-platform whale intelligence.
    Doesn't just check Kalshi — scans public blockchain data, DEX activity,
    and prediction market leaderboards across ALL connected platforms.

    Sources:
      1. Polymarket public API — leaderboards, large positions
      2. Ethereum whale trackers — public APIs (no key needed)
      3. Kalshi whale trades (already in market_scanner)
      4. Crypto fear/greed index — market sentiment
      5. DeFi Llama — TVL flows (where smart money is moving)
    """
    whales = CONSCIOUSNESS.setdefault("whale_watch", {
        "polymarket": {}, "onchain": {}, "sentiment": {},
        "defi_flows": {}, "signals": [], "last_scan": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 5 != 0 and cycle != 1:
        return

    # --- SOURCE 1: Polymarket public leaderboard ---
    try:
        # Polymarket has a public API for trending markets
        req = urllib.request.Request(
            "https://gamma-api.polymarket.com/markets?limit=10&order=volume24hr&ascending=false&active=true",
            headers={"User-Agent": "SolarPunk-WhaleWatch/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            hot_markets = []
            for m in (data if isinstance(data, list) else data.get("data", data.get("markets", [])))[:10]:
                hot_markets.append({
                    "question": (m.get("question") or m.get("title") or "?")[:60],
                    "volume_24h": m.get("volume24hr") or m.get("volume_num") or 0,
                    "liquidity": m.get("liquidityNum") or m.get("liquidity") or 0,
                    "outcome_yes": m.get("outcomePrices") or m.get("bestAsk") or "?",
                })
            whales["polymarket"]["hot_markets"] = hot_markets
            whales["polymarket"]["count"] = len(hot_markets)
            whales["polymarket"]["status"] = "live"
    except Exception as e:
        whales["polymarket"]["status"] = f"error: {str(e)[:50]}"

    # --- SOURCE 2: Crypto Fear & Greed Index ---
    try:
        req = urllib.request.Request(
            "https://api.alternative.me/fng/?limit=1",
            headers={"User-Agent": "SolarPunk-WhaleWatch/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
            fng = data.get("data", [{}])[0]
            whales["sentiment"]["fear_greed_index"] = int(fng.get("value", 0))
            whales["sentiment"]["fear_greed_label"] = fng.get("value_classification", "?")
            whales["sentiment"]["source"] = "alternative.me"
    except Exception as e:
        whales["sentiment"]["fng_error"] = str(e)[:50]

    # --- SOURCE 3: DeFi Llama — protocol TVL flows ---
    try:
        req = urllib.request.Request(
            "https://api.llama.fi/protocols",
            headers={"User-Agent": "SolarPunk-WhaleWatch/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            # Get top 10 by TVL
            if isinstance(data, list):
                sorted_protos = sorted(data, key=lambda x: float(x.get("tvl", 0) or 0), reverse=True)[:10]
                whales["defi_flows"]["top_protocols"] = [
                    {
                        "name": p.get("name", "?"),
                        "tvl_usd": round(float(p.get("tvl", 0) or 0)),
                        "change_1d": p.get("change_1d"),
                        "change_7d": p.get("change_7d"),
                        "chain": p.get("chain", "?"),
                        "category": p.get("category", "?"),
                    }
                    for p in sorted_protos
                ]
                # Find biggest movers (1d change)
                movers = sorted(
                    [p for p in data if p.get("change_1d") is not None and float(p.get("tvl", 0) or 0) > 1000000],
                    key=lambda x: abs(float(x.get("change_1d", 0) or 0)),
                    reverse=True
                )[:5]
                whales["defi_flows"]["biggest_movers"] = [
                    {"name": p.get("name"), "change_1d": p.get("change_1d"),
                     "tvl": round(float(p.get("tvl", 0) or 0))}
                    for p in movers
                ]
                whales["defi_flows"]["status"] = "live"
    except Exception as e:
        whales["defi_flows"]["status"] = f"error: {str(e)[:50]}"

    # --- SOURCE 4: Ethereum gas + whale alerts (public) ---
    try:
        # ETH gas price as activity indicator
        req = urllib.request.Request(
            "https://api.etherscan.io/api?module=gastracker&action=gasoracle",
            headers={"User-Agent": "SolarPunk-WhaleWatch/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
            result = data.get("result", {})
            if isinstance(result, dict):
                whales["onchain"]["eth_gas_gwei"] = result.get("ProposeGasPrice", "?")
                whales["onchain"]["fast_gas"] = result.get("FastGasPrice", "?")
                whales["onchain"]["status"] = "live"
    except Exception as e:
        whales["onchain"]["status"] = f"error: {str(e)[:50]}"

    # --- COMPILE SIGNALS ---
    signals = []
    # Kalshi whale signals from market_scanner
    kalshi_whales = CONSCIOUSNESS.get("markets", {}).get("whale_sentiment", {})
    for ticker, s in kalshi_whales.items():
        if s.get("conviction", 0) >= 80:
            signals.append({
                "source": "kalshi",
                "signal": f"{s.get('event', ticker)}: {s['direction']} ({s['conviction']}%)",
                "type": "whale_conviction",
            })

    # Fear/Greed extremes
    fng = whales["sentiment"].get("fear_greed_index", 50)
    if fng <= 20:
        signals.append({"source": "fear_greed", "signal": f"EXTREME FEAR ({fng}) - contrarian buy signal", "type": "sentiment"})
    elif fng >= 80:
        signals.append({"source": "fear_greed", "signal": f"EXTREME GREED ({fng}) - caution signal", "type": "sentiment"})

    # DeFi big movers
    for mover in whales.get("defi_flows", {}).get("biggest_movers", []):
        change = mover.get("change_1d", 0)
        if change and abs(float(change)) > 20:
            direction = "inflow" if float(change) > 0 else "outflow"
            signals.append({
                "source": "defi_llama",
                "signal": f"{mover['name']}: {change}% 1d {direction}",
                "type": "tvl_flow",
            })

    whales["signals"] = signals[:15]
    whales["signal_count"] = len(signals)
    whales["last_scan"] = datetime.now(timezone.utc).isoformat()


def neuron_cross_signal():
    """
    LIVE: Merge all intelligence sources into unified trading signals.
    Cross-references Kalshi whales, Polymarket volume, DeFi flows,
    Fear/Greed, and market data to find high-conviction plays.
    """
    cross = CONSCIOUSNESS.setdefault("cross_signals", {
        "unified": [], "conviction_map": {}, "last_analysis": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 4 != 0 and cycle != 1:
        return

    kalshi = CONSCIOUSNESS.get("markets", {})
    whales = CONSCIOUSNESS.get("whale_watch", {})
    fng = whales.get("sentiment", {}).get("fear_greed_index", 50)
    pm_markets = whales.get("polymarket", {}).get("hot_markets", [])
    defi_movers = whales.get("defi_flows", {}).get("biggest_movers", [])
    kalshi_whales = kalshi.get("whale_sentiment", {})
    opportunities = kalshi.get("opportunities", [])

    unified = []

    # Signal 1: Extreme Fear + high-volume Kalshi opportunities = buy zone
    if fng <= 25 and opportunities:
        for opp in opportunities[:5]:
            unified.append({
                "signal": "FEAR_DIP_OPPORTUNITY",
                "confidence": min(95, 100 - fng),
                "market": opp.get("event", "?"),
                "ticker": opp.get("ticker", ""),
                "yes_bid": opp.get("yes_bid", 0),
                "spread": opp.get("spread", 0),
                "reasoning": f"Fear={fng} + tight spread ({opp.get('spread',0)}) + vol={opp.get('volume',0):.0f}",
            })

    # Signal 2: Whale conviction + tight spread = follow the whale
    for ticker, sentiment in kalshi_whales.items():
        if sentiment.get("conviction", 0) >= 90:
            matching_opp = next((o for o in opportunities if o.get("ticker") == ticker), None)
            if matching_opp:
                unified.append({
                    "signal": "WHALE_CONFIRMED_OPPORTUNITY",
                    "confidence": sentiment["conviction"],
                    "market": sentiment.get("event", ticker),
                    "ticker": ticker,
                    "direction": sentiment["direction"],
                    "whale_volume": sentiment.get("yes_volume", 0) + sentiment.get("no_volume", 0),
                    "reasoning": f"Whale {sentiment['direction']} ({sentiment['conviction']}%) + tight spread",
                })

    # Signal 3: Polymarket volume spike + related Kalshi market
    for pm in pm_markets[:5]:
        question = pm.get("question", "").lower()
        vol_24h = pm.get("volume_24h", 0)
        if vol_24h and float(str(vol_24h)) > 1000000:
            # Check if similar topic exists on Kalshi
            for opp in opportunities:
                event = opp.get("event", "").lower()
                # Simple keyword overlap check
                pm_words = set(question.split())
                ev_words = set(event.split())
                overlap = pm_words & ev_words - {"the", "a", "will", "be", "in", "of", "to", "by"}
                if len(overlap) >= 2:
                    unified.append({
                        "signal": "CROSS_PLATFORM_CONVERGENCE",
                        "confidence": 75,
                        "market": opp.get("event", "?"),
                        "polymarket_match": question[:50],
                        "pm_volume_24h": vol_24h,
                        "reasoning": f"Same topic trending on both Polymarket (${float(str(vol_24h)):,.0f}) and Kalshi",
                    })

    # Signal 4: DeFi massive inflows = something happening in crypto
    for mover in defi_movers:
        change = float(str(mover.get("change_1d", 0) or 0))
        if abs(change) > 50:
            unified.append({
                "signal": "DEFI_FLOW_ALERT",
                "confidence": min(80, abs(change)),
                "protocol": mover.get("name", "?"),
                "change_1d": change,
                "tvl": mover.get("tvl", 0),
                "reasoning": f"{'Massive inflow' if change > 0 else 'Massive outflow'}: {change:.0f}% in 24h",
            })

    # Sort by confidence
    unified.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    cross["unified"] = unified[:20]
    cross["signal_count"] = len(unified)
    cross["fear_greed"] = fng
    cross["market_regime"] = "fear" if fng < 30 else "neutral" if fng < 70 else "greed"
    cross["last_analysis"] = datetime.now(timezone.utc).isoformat()


def neuron_stock_scanner():
    """
    LIVE: Use Alpaca API for stock/ETF market data.
    Alpaca bridge is connected — use it for real-time market intelligence.
    """
    stocks = CONSCIOUSNESS.setdefault("stocks", {
        "market_status": "unknown", "indices": {}, "watchlist": [],
        "last_scan": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 5 != 0:
        return

    alpaca_key = os.environ.get("ALPACA_API_KEY", "")
    alpaca_secret = os.environ.get("ALPACA_SECRET_KEY", "")
    if not alpaca_key or not alpaca_secret:
        stocks["status"] = "no_credentials"
        return

    base_url = "https://paper-api.alpaca.markets"  # Paper trading = safe
    headers = {
        "APCA-API-KEY-ID": alpaca_key,
        "APCA-API-SECRET-KEY": alpaca_secret,
    }

    # Check market status
    try:
        req = urllib.request.Request(f"{base_url}/v2/clock", headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            clock = json.loads(r.read().decode())
            stocks["market_status"] = "open" if clock.get("is_open") else "closed"
            stocks["next_open"] = clock.get("next_open", "")[:19]
            stocks["next_close"] = clock.get("next_close", "")[:19]
    except Exception as e:
        stocks["clock_error"] = str(e)[:60]

    # Get account info (paper trading balance)
    try:
        req = urllib.request.Request(f"{base_url}/v2/account", headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            acct = json.loads(r.read().decode())
            stocks["paper_equity"] = acct.get("equity", "0")
            stocks["paper_cash"] = acct.get("cash", "0")
            stocks["paper_buying_power"] = acct.get("buying_power", "0")
            stocks["status"] = "connected"
    except urllib.error.HTTPError as e:
        stocks["account_error"] = f"HTTP {e.code}"
    except Exception as e:
        stocks["account_error"] = str(e)[:60]

    # Get key index snapshots via data API
    data_url = "https://data.alpaca.markets"
    symbols = ["SPY", "QQQ", "IWM", "VIX", "BTC/USD", "ETH/USD"]
    for sym in symbols:
        try:
            endpoint = f"{data_url}/v2/stocks/{sym}/quotes/latest" if "/" not in sym else f"{data_url}/v1beta3/crypto/us/latest/quotes?symbols={sym}"
            req = urllib.request.Request(endpoint, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as r:
                data = json.loads(r.read().decode())
                if "quote" in data:
                    q = data["quote"]
                    stocks["indices"][sym] = {
                        "bid": q.get("bp", q.get("bid_price", 0)),
                        "ask": q.get("ap", q.get("ask_price", 0)),
                    }
                elif "quotes" in data:
                    for s, q in data["quotes"].items():
                        stocks["indices"][s] = {
                            "bid": q.get("bp", 0), "ask": q.get("ap", 0),
                        }
        except Exception:
            pass

    stocks["last_scan"] = datetime.now(timezone.utc).isoformat()


def neuron_workflow_doctor():
    """
    LIVE: Diagnose failing GitHub Actions workflows and attempt fixes.
    Reads failure logs, identifies common patterns, suggests or applies fixes.
    """
    doctor = CONSCIOUSNESS.setdefault("workflow_doctor", {
        "diagnosed": [], "fixed": [], "last_check": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 8 != 0:
        return

    wf_health = CONSCIOUSNESS.get("workflow_health", {})
    failures = wf_health.get("failures", [])
    if not failures:
        doctor["status"] = "all_healthy"
        return

    import subprocess
    diagnosed = []
    for fail in failures[:3]:  # Check top 3 failures
        name = fail.get("name", "")
        if not name:
            continue
        # Get the failed run's logs
        try:
            r = subprocess.run(
                ["gh", "run", "list", "--workflow", name,
                 "--json", "databaseId,conclusion,createdAt",
                 "-L", "1", "--status", "failure"],
                capture_output=True, text=True, timeout=10,
                encoding="utf-8", errors="replace")
            if r.returncode == 0 and r.stdout.strip():
                runs = json.loads(r.stdout)
                if runs:
                    run_id = runs[0].get("databaseId")
                    # Get failure details
                    r2 = subprocess.run(
                        ["gh", "run", "view", str(run_id), "--json",
                         "conclusion,jobs"],
                        capture_output=True, text=True, timeout=10,
                        encoding="utf-8", errors="replace")
                    if r2.returncode == 0:
                        run_data = json.loads(r2.stdout)
                        failed_jobs = [
                            j for j in run_data.get("jobs", [])
                            if j.get("conclusion") == "failure"
                        ]
                        for job in failed_jobs[:1]:
                            failed_steps = [
                                s for s in job.get("steps", [])
                                if s.get("conclusion") == "failure"
                            ]
                            diagnosed.append({
                                "workflow": name,
                                "run_id": run_id,
                                "job": job.get("name", "?"),
                                "failed_step": failed_steps[0].get("name", "?") if failed_steps else "unknown",
                                "created": runs[0].get("createdAt", "")[:19],
                            })
        except Exception as e:
            diagnosed.append({"workflow": name, "error": str(e)[:60]})

    doctor["diagnosed"] = diagnosed
    doctor["diagnosis_count"] = len(diagnosed)
    doctor["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_growth_tracker():
    """
    LIVE: Track the blob's own evolution over time.
    Records neuron count, domain count, signal count, portfolio value
    per cycle to show growth trajectory.
    """
    growth = CONSCIOUSNESS.setdefault("growth", {
        "history": [], "milestones": [], "last_record": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Record every 5 cycles
    if cycle % 5 != 0:
        return

    meta = CONSCIOUSNESS["meta"]
    markets = CONSCIOUSNESS.get("markets", {})
    whales = CONSCIOUSNESS.get("whale_watch", {})
    cross = CONSCIOUSNESS.get("cross_signals", {})
    analytics = CONSCIOUSNESS.get("analytics", {})

    snapshot = {
        "cycle": cycle,
        "ts": datetime.now(timezone.utc).isoformat(),
        "neurons": meta.get("neuron_count", 0),
        "domains": len(meta.get("consciousness_keys", [])),
        "engines": meta.get("engines_absorbed", 0),
        "health": CONSCIOUSNESS["equilibrium"].get("score", 0),
        "confidence": CONSCIOUSNESS["brain"].get("confidence", 0),
        "kalshi_total": markets.get("total_usd", 0),
        "kalshi_positions": markets.get("active_position_count", 0),
        "whale_signals": whales.get("signal_count", 0),
        "cross_signals": cross.get("signal_count", 0),
        "views_14d": analytics.get("views_14d", 0),
        "clones_14d": analytics.get("clones_14d", 0),
        "fear_greed": whales.get("sentiment", {}).get("fear_greed_index", 0),
    }
    growth["history"].append(snapshot)
    growth["latest"] = snapshot

    # Keep last 100 snapshots
    if len(growth["history"]) > 100:
        growth["history"] = growth["history"][-50:]

    # Check for milestones
    prev = growth["history"][-2] if len(growth["history"]) > 1 else {}
    if snapshot["neurons"] > prev.get("neurons", 0):
        growth["milestones"].append({
            "type": "neuron_added",
            "count": snapshot["neurons"],
            "cycle": cycle,
        })
    if snapshot["kalshi_total"] > prev.get("kalshi_total", 0) + 5:
        growth["milestones"].append({
            "type": "portfolio_growth",
            "value": snapshot["kalshi_total"],
            "cycle": cycle,
        })
    # Keep milestones bounded
    if len(growth["milestones"]) > 50:
        growth["milestones"] = growth["milestones"][-25:]

    growth["last_record"] = datetime.now(timezone.utc).isoformat()


def neuron_position_monitor():
    """
    LIVE: Monitor open Kalshi positions for profit-taking or stop-loss.
    Compares current market prices against entry prices.
    """
    monitor = CONSCIOUSNESS.setdefault("position_monitor", {
        "alerts": [], "last_check": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 4 != 0:
        return

    markets = CONSCIOUSNESS.get("markets", {})
    positions = markets.get("positions", [])
    liquid = markets.get("kalshi_open", [])

    if not positions:
        monitor["status"] = "no_positions"
        return

    alerts = []
    for pos in positions:
        ticker = pos.get("ticker", "")
        exposure = pos.get("exposure_usd", 0)
        if exposure <= 0:
            continue

        # Find current market price
        current = next((m for m in liquid if m.get("ticker") == ticker), None)
        if current:
            alerts.append({
                "ticker": ticker,
                "exposure": exposure,
                "current_bid": current.get("yes_bid", 0),
                "current_ask": current.get("yes_ask", 0),
                "spread": current.get("spread", 0),
                "volume": current.get("volume", 0),
            })
        else:
            # Position in a market not in our top 30 — flag it
            alerts.append({
                "ticker": ticker,
                "exposure": exposure,
                "status": "not_in_liquid_scan",
                "note": "Market may be illiquid or expired",
            })

    monitor["alerts"] = alerts
    monitor["monitored_count"] = len(alerts)
    monitor["total_exposure"] = round(sum(a.get("exposure", 0) for a in alerts), 2)
    monitor["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_content_publisher():
    """
    ACTION: Actually publish content by dispatching workflows.
    When content_factory has ideas and devto API key is confirmed,
    dispatch the content-publishing workflows.
    """
    publisher = CONSCIOUSNESS.setdefault("content_publisher", {
        "dispatched": [], "last_dispatch": None, "total_dispatched": 0,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Only publish every 25 cycles (conservative — real external actions)
    if cycle % 25 != 0:
        return

    devto = CONSCIOUSNESS.get("devto", {})
    content = CONSCIOUSNESS.get("content_factory", {})
    dispatch = CONSCIOUSNESS.get("dispatch", {})

    # Only publish if we have: ideas + API key + available workflows
    if not devto.get("ready_to_publish"):
        return
    if not content.get("ideas"):
        return

    active_names = [w["name"] for w in dispatch.get("available_workflows", [])
                    if w.get("state") == "active"]

    import subprocess
    dispatched = []

    # Dispatch OPEN_ANTENNA to scan for content opportunities
    if any("OPEN_ANTENNA" in n.upper() for n in active_names):
        try:
            r = subprocess.run(
                ["gh", "workflow", "run", "OPEN_ANTENNA.yml"],
                capture_output=True, text=True, timeout=15,
                encoding="utf-8", errors="replace")
            if r.returncode == 0:
                dispatched.append({
                    "workflow": "OPEN_ANTENNA",
                    "reason": "Scan for content opportunities",
                    "ts": datetime.now(timezone.utc).isoformat(),
                })
        except Exception:
            pass

    # Dispatch TRANSPARENCY_PULSE for community update
    if any("TRANSPARENCY" in n.upper() for n in active_names):
        try:
            r = subprocess.run(
                ["gh", "workflow", "run", "TRANSPARENCY_PULSE.yml"],
                capture_output=True, text=True, timeout=15,
                encoding="utf-8", errors="replace")
            if r.returncode == 0:
                dispatched.append({
                    "workflow": "TRANSPARENCY_PULSE",
                    "reason": "Publish transparency update",
                    "ts": datetime.now(timezone.utc).isoformat(),
                })
        except Exception:
            pass

    if dispatched:
        publisher["dispatched"].extend(dispatched)
        publisher["total_dispatched"] += len(dispatched)
        publisher["last_dispatch"] = datetime.now(timezone.utc).isoformat()
        # Keep bounded
        if len(publisher["dispatched"]) > 50:
            publisher["dispatched"] = publisher["dispatched"][-25:]


def neuron_github_actions_trigger():
    """
    LIVE: Trigger GitHub Actions workflows to use cloud-only secrets.
    The blob can't access ANTHROPIC_API_KEY, BLUESKY_*, DISCORD_*, etc.
    locally — but GitHub Actions CAN. So we dispatch workflows.

    Strategy:
      - Catalog all dispatchable workflows
      - Based on consciousness state, decide which ones to fire
      - Use `gh workflow run <name>` to dispatch
      - Track what was triggered and when
    """
    dispatch = CONSCIOUSNESS.setdefault("dispatch", {
        "triggered": [], "pending": [], "last_trigger": None,
        "history": [], "available_workflows": [], "active_count": 0,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]

    # Phase A: Catalog workflows (every 10 cycles, or if empty)
    if cycle % 10 == 0 or cycle == 1 or not dispatch.get("available_workflows"):
        try:
            import subprocess
            r = subprocess.run(
                ["gh", "workflow", "list", "--json", "name,state,id"],
                capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace")
            if r.returncode == 0 and r.stdout:
                workflows = json.loads(r.stdout)
                dispatch["available_workflows"] = [
                    {"name": w["name"], "state": w["state"], "id": w.get("id")}
                    for w in workflows
                ]
                active = [w for w in workflows if w["state"] == "active"]
                dispatch["active_count"] = len(active)
                dispatch.pop("catalog_error", None)  # Clear old errors
        except Exception as e:
            dispatch["catalog_error"] = str(e)[:80]

    # Phase B: Decide what to fire (every 15 cycles — conservative)
    if cycle % 15 != 0 or cycle < 3:
        dispatch["last_trigger"] = datetime.now(timezone.utc).isoformat()
        return

    import subprocess
    fired = []
    eq = CONSCIOUSNESS["equilibrium"]
    brain = CONSCIOUSNESS["brain"]
    community = CONSCIOUSNESS.get("community", {})

    # Rule 1: If health < 30% and OMNIBRAIN hasn't run recently, dispatch it
    # OMNIBRAIN runs all engines with cloud secrets
    active_names = [w["name"] for w in dispatch.get("available_workflows", [])
                    if w.get("state") == "active"]

    # Rule 2: SIGNAL_BOOST — post pulse to discussions (weekly-ish)
    recent_history = dispatch.get("history", [])
    recently_fired = {h["name"] for h in recent_history[-20:]}

    if "SIGNAL_BOOST" in active_names and "SIGNAL_BOOST" not in recently_fired:
        try:
            r = subprocess.run(
                ["gh", "workflow", "run", "SIGNAL_BOOST.yml"],
                capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace")
            if r.returncode == 0:
                fired.append("SIGNAL_BOOST")
        except Exception:
            pass

    # Rule 3: REACH — ping search engines (helps SEO)
    if "REACH" in active_names and "REACH" not in recently_fired:
        try:
            r = subprocess.run(
                ["gh", "workflow", "run", "REACH.yml"],
                capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace")
            if r.returncode == 0:
                fired.append("REACH")
        except Exception:
            pass

    # Rule 4: BADGE_FORGE — update status badges
    if "BADGE_FORGE" in active_names and "BADGE_FORGE" not in recently_fired:
        try:
            r = subprocess.run(
                ["gh", "workflow", "run", "BADGE_FORGE.yml"],
                capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace")
            if r.returncode == 0:
                fired.append("BADGE_FORGE")
        except Exception:
            pass

    # Rule 5: LIVING_DOCS — refresh documentation
    if "LIVING_DOCS" in active_names and "LIVING_DOCS" not in recently_fired:
        try:
            r = subprocess.run(
                ["gh", "workflow", "run", "LIVING_DOCS.yml"],
                capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace")
            if r.returncode == 0:
                fired.append("LIVING_DOCS")
        except Exception:
            pass

    # Record what we fired
    if fired:
        ts = datetime.now(timezone.utc).isoformat()
        for name in fired:
            dispatch["history"].append({"name": name, "cycle": cycle, "ts": ts})
        dispatch["triggered"] = fired
        # Keep history bounded
        if len(dispatch["history"]) > 100:
            dispatch["history"] = dispatch["history"][-50:]

    dispatch["last_trigger"] = datetime.now(timezone.utc).isoformat()
    dispatch["last_fired_count"] = len(fired)


def neuron_dashboard_builder():
    """
    LIVE: Generate a real-time HTML dashboard from consciousness data.
    This is the public face of SolarPunk — auto-updates docs/dashboard.html.
    """
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Update dashboard every 2 cycles
    if cycle % 2 != 0 and cycle != 1:
        return

    eq = CONSCIOUSNESS["equilibrium"]
    bridges = CONSCIOUSNESS.get("bridges", {})
    analytics = CONSCIOUSNESS.get("analytics", {})
    rev = CONSCIOUSNESS["revenue"]
    brain = CONSCIOUSNESS["brain"]
    meta = CONSCIOUSNESS["meta"]
    markets = CONSCIOUSNESS.get("markets", {})

    connected_list = bridges.get("connected", [])
    connected_html = "".join(f'<span class="badge connected">{b}</span>' for b in connected_list)
    failed_list = bridges.get("failed", [])
    failed_html = "".join(f'<span class="badge failed">{b}</span>' for b in failed_list)

    # Pre-compute values that can't go in f-strings
    zone = eq.get("zone", "red")
    health_color = {"green": "#4caf50", "yellow": "#ff9800", "red": "#f44336"}.get(zone, "#f44336")
    buy_links_working = rev.get("audit", {}).get("working", 0)
    consciousness_keys_count = len(meta.get("consciousness_keys", []))
    referrer_html = "".join(
        f'<div class="stat"><span class="stat-value">{r.get("site","?")}</span> '
        f'<span class="stat-label">({r.get("count",0)} hits)</span></div>'
        for r in analytics.get("top_referrers", [])[:5]
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SolarPunk Nerve Center -- Live Dashboard</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0a0a; color: #e0e0e0; padding: 20px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; max-width: 1200px; margin: 0 auto; }}
  .card {{ background: #1a1a2e; border-radius: 12px; padding: 20px; border: 1px solid #333; }}
  .card h3 {{ color: #64ffda; margin-bottom: 12px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }}
  .big-number {{ font-size: 48px; font-weight: bold; line-height: 1; }}
  .sub {{ color: #888; font-size: 13px; margin-top: 4px; }}
  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; margin: 2px; font-weight: bold; }}
  .badge.connected {{ background: #1b5e20; color: #a5d6a7; }}
  .badge.failed {{ background: #b71c1c; color: #ef9a9a; }}
  header {{ text-align: center; margin-bottom: 30px; }}
  header h1 {{ font-size: 28px; color: #64ffda; }}
  header p {{ color: #666; margin-top: 5px; }}
  .stat {{ margin-bottom: 8px; }}
  .stat-label {{ color: #888; font-size: 12px; }}
  .stat-value {{ font-size: 18px; font-weight: bold; }}
  .thought {{ background: #0d1b2a; padding: 12px; border-radius: 8px; border-left: 3px solid #64ffda; margin-top: 8px; font-style: italic; font-size: 13px; }}
</style>
</head>
<body>
<header>
  <h1>SolarPunk Nerve Center</h1>
  <p>Unified Digital Organism -- Cycle {cycle} -- {meta.get('architecture', 'blob')}</p>
</header>
<div class="grid">
  <div class="card">
    <h3>System Health</h3>
    <div class="big-number" style="color:{health_color}">{eq.get('score', 0)}%</div>
    <div class="sub">{eq.get('zone', 'unknown')} zone | trend: {eq.get('trend', '?')}</div>
    <div class="sub">Confidence: {brain.get('confidence', 0)}%</div>
  </div>
  <div class="card">
    <h3>Engines Absorbed</h3>
    <div class="big-number">{len(CONSCIOUSNESS.get('engines', {}))}</div>
    <div class="sub">{meta.get('neuron_count', 0)} active neurons | {consciousness_keys_count} state domains</div>
  </div>
  <div class="card">
    <h3>GitHub Traffic (14d)</h3>
    <div class="big-number">{analytics.get('views_14d', 0)}</div>
    <div class="sub">views | {analytics.get('unique_visitors', 0)} unique | {analytics.get('clones_14d', 0)} clones</div>
    <div class="sub">Stars: {analytics.get('stars', 0)} | Forks: {analytics.get('forks', 0)}</div>
  </div>
  <div class="card">
    <h3>Revenue</h3>
    <div class="big-number">${rev.get('total_raised', 0):.2f}</div>
    <div class="sub">Gaza Fund: ${rev.get('total_to_gaza', 0):.2f}</div>
    <div class="sub">Buy links: {buy_links_working} working</div>
  </div>
  <div class="card">
    <h3>Bridges Connected</h3>
    {connected_html}
    {f'<div style="margin-top:6px">{failed_html}</div>' if failed_html else ''}
    <div class="sub" style="margin-top:8px">{bridges.get('available_keys', 0)}/{bridges.get('total_keys_known', 0)} env keys | {len(bridges.get('local_cred_files', []))} local cred files</div>
  </div>
  <div class="card">
    <h3>Markets</h3>
    <div class="stat"><span class="stat-label">Kalshi Balance:</span> <span class="stat-value">${markets.get('kalshi_balance', 0)}</span></div>
    <div class="stat"><span class="stat-label">Exchange Active:</span> <span class="stat-value">{markets.get('exchange_status', 'unknown')}</span></div>
    <div class="sub">Alpaca: {'ready' if CONSCIOUSNESS['trading'].get('alpaca_ready') else 'offline'} | Polymarket: {'ready' if CONSCIOUSNESS['trading'].get('polymarket_ready') else 'offline'}</div>
  </div>
  <div class="card">
    <h3>Top Referrers</h3>
    {referrer_html}
  </div>
  <div class="card">
    <h3>Brain</h3>
    <div class="stat"><span class="stat-label">AI Available:</span> <span class="stat-value">{brain.get('ai_available', False)}</span></div>
    <div class="stat"><span class="stat-label">Last Thought:</span></div>
    <div class="thought">{brain.get('last_thought', 'No AI thoughts yet -- API key needed in local env')}</div>
  </div>
</div>
<footer style="text-align:center;margin-top:30px;color:#444;font-size:11px;">
  Auto-generated by BLOB_BRAIN neuron_dashboard_builder | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
</footer>
</body>
</html>"""

    try:
        docs = Path("docs")
        docs.mkdir(exist_ok=True)
        (docs / "dashboard.html").write_text(html, encoding="utf-8")
        CONSCIOUSNESS.setdefault("dashboard", {})["last_build"] = datetime.now(timezone.utc).isoformat()
        CONSCIOUSNESS["dashboard"]["path"] = "docs/dashboard.html"
    except Exception as e:
        CONSCIOUSNESS.setdefault("dashboard", {})["error"] = str(e)[:60]


def neuron_community_pulse():
    """
    LIVE: Monitor GitHub community — issues, discussions, PRs.
    Uses gh CLI to check for new engagement.
    """
    community = CONSCIOUSNESS.setdefault("community", {
        "open_issues": 0, "open_prs": 0, "discussions": 0,
        "recent_activity": [], "last_check": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Check every 4 cycles
    if cycle % 4 != 0 and cycle != 1:
        return

    try:
        import subprocess
        repo = "meekotharaccoon-cell/meeko-nerve-center"

        # Open issues
        r = subprocess.run(
            ["gh", "api", f"repos/{repo}", "--jq", ".open_issues_count"],
            capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
        if r.returncode == 0 and r.stdout.strip():
            community["open_issues"] = int(r.stdout.strip())

        # Open PRs
        r2 = subprocess.run(
            ["gh", "api", f"repos/{repo}/pulls?state=open", "--jq", "length"],
            capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
        if r2.returncode == 0 and r2.stdout.strip():
            community["open_prs"] = int(r2.stdout.strip())

        # Recent events (last 5)
        r3 = subprocess.run(
            ["gh", "api", f"repos/{repo}/events?per_page=5",
             "--jq", '[.[] | {type: .type, actor: .actor.login, created: .created_at}]'],
            capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
        if r3.returncode == 0:
            try:
                community["recent_events"] = json.loads(r3.stdout)[:5]
            except Exception:
                pass

        community["last_check"] = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        community["check_error"] = str(e)[:60]


def neuron_content_factory():
    """
    LIVE: Generate content ideas and queue them for publishing.
    Analyzes traffic patterns, referrers, and trends to suggest what to write.
    """
    content = CONSCIOUSNESS.setdefault("content_factory", {
        "ideas": [], "queued": [], "published": [], "last_gen": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Generate every 5 cycles
    if cycle % 5 != 0:
        return

    analytics = CONSCIOUSNESS.get("analytics", {})
    referrers = analytics.get("top_referrers", [])
    views = analytics.get("views_14d", 0)
    clones = analytics.get("clones_14d", 0)

    # Auto-generate content ideas based on data
    ideas = []

    if views > 100:
        ideas.append({
            "title": f"Building a Self-Healing Digital Organism: {len(CONSCIOUSNESS.get('engines', {}))} Engines and Growing",
            "platform": "dev.to",
            "angle": "technical deep-dive",
            "hook": f"Our open-source project got {views} views in 14 days. Here's the architecture.",
        })

    if clones > 100:
        ideas.append({
            "title": "Why I Built a Digital Brain That Thinks Without Me",
            "platform": "dev.to",
            "angle": "philosophical + technical",
            "hook": f"{clones} clones in 2 weeks. People want autonomous systems.",
        })

    # Check if dev.to referrer exists (means our content is working!)
    devto_referrals = sum(r.get("count", 0) for r in referrers if "dev.to" in r.get("site", ""))
    if devto_referrals > 0:
        ideas.append({
            "title": "SolarPunk Architecture: A Digital Nervous System for Social Good",
            "platform": "dev.to",
            "angle": "mission-driven tech",
            "hook": f"dev.to is sending us {devto_referrals} visitors. Double down on technical content.",
        })

    # Always have a Ko-fi product idea
    eq = CONSCIOUSNESS["equilibrium"]
    ideas.append({
        "title": "Digital Brain Architecture Blueprint (PDF)",
        "platform": "ko-fi",
        "angle": "digital product",
        "hook": f"System health: {eq.get('score', 0)}%. Package the architecture as a paid blueprint.",
        "price": "$5",
    })

    content["ideas"] = ideas
    content["idea_count"] = len(ideas)
    content["last_gen"] = datetime.now(timezone.utc).isoformat()


def neuron_self_repair():
    """
    LIVE: Check BLOB_BRAIN's own health and the state of all data files.
    Ensures data integrity and reports self-diagnostics.
    """
    repair = CONSCIOUSNESS.setdefault("self_repair", {
        "data_files_ok": 0, "data_files_corrupt": 0,
        "blob_size_bytes": 0, "last_check": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 3 != 0 and cycle != 1:
        return

    data_dir = Path("data")
    ok_count = 0
    corrupt_count = 0

    # Check all JSON files in data/
    for jf in data_dir.glob("*.json"):
        try:
            json.loads(jf.read_text(encoding="utf-8"))
            ok_count += 1
        except Exception:
            corrupt_count += 1

    # Check blob brain file size
    blob_file = data_dir / "blob_brain.json"
    if blob_file.exists():
        repair["blob_size_bytes"] = blob_file.stat().st_size
        repair["blob_size_kb"] = round(blob_file.stat().st_size / 1024, 1)

    # Check mycelium engines that compile clean
    import py_compile
    engine_count = 0
    compile_errors = 0
    for f in Path("mycelium").glob("*.py"):
        if f.name.startswith("__"):
            continue
        engine_count += 1
        try:
            py_compile.compile(str(f), doraise=True)
        except Exception:
            compile_errors += 1

    repair["data_files_ok"] = ok_count
    repair["data_files_corrupt"] = corrupt_count
    repair["engine_files"] = engine_count
    repair["compile_errors"] = compile_errors
    repair["last_check"] = datetime.now(timezone.utc).isoformat()

    # Trim errors list to prevent memory bloat
    if len(CONSCIOUSNESS["errors"]) > 50:
        CONSCIOUSNESS["errors"] = CONSCIOUSNESS["errors"][-20:]


def neuron_mission_pulse():
    """
    LIVE: Track SolarPunk's mission metrics — fighting tyranny, protecting the silenced.
    Monitors Gaza fund progress, social impact, and community growth.
    """
    mission = CONSCIOUSNESS.setdefault("mission", {
        "gaza_fund": 0, "total_impact_actions": 0,
        "community_size": 0, "awareness_score": 0, "last_pulse": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 4 != 0 and cycle != 1:
        return

    analytics = CONSCIOUSNESS.get("analytics", {})
    rev = CONSCIOUSNESS["revenue"]
    community = CONSCIOUSNESS.get("community", {})

    # Gaza fund tracking
    mission["gaza_fund"] = rev.get("total_to_gaza", 0)

    # Awareness score = views + clones + referrer diversity
    views = analytics.get("views_14d", 0)
    clones = analytics.get("clones_14d", 0)
    referrer_count = len(analytics.get("top_referrers", []))
    mission["awareness_score"] = min(100, round((views + clones) / 100 + referrer_count * 10))

    # Community size = stars + forks + unique visitors
    stars = analytics.get("stars", 0)
    forks = analytics.get("forks", 0)
    unique = analytics.get("unique_visitors", 0)
    mission["community_size"] = stars + forks + unique

    # Impact actions = bridges connected + content generated + revenue earned
    bridges = CONSCIOUSNESS.get("bridges", {})
    content = CONSCIOUSNESS.get("content_factory", {})
    mission["total_impact_actions"] = (
        len(bridges.get("connected", []))
        + content.get("idea_count", 0)
        + (1 if rev.get("total_raised", 0) > 0 else 0)
    )

    mission["last_pulse"] = datetime.now(timezone.utc).isoformat()


def neuron_workflow_health():
    """
    LIVE: Monitor GitHub Actions workflow run health.
    Checks recent runs for failures, stalls, and success rates.
    """
    wf_health = CONSCIOUSNESS.setdefault("workflow_health", {
        "recent_runs": [], "success_rate": 0, "failures": [],
        "last_check": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 5 != 0 and cycle != 1:
        return

    try:
        import subprocess
        # Get last 15 workflow runs
        r = subprocess.run(
            ["gh", "run", "list", "--json",
             "name,status,conclusion,createdAt",
             "-L", "15"],
            capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace")
        if r.returncode == 0:
            runs = json.loads(r.stdout)
            wf_health["recent_runs"] = [
                {
                    "name": run.get("name", "?"),
                    "status": run.get("status", "?"),
                    "conclusion": run.get("conclusion", "?"),
                    "created": run.get("createdAt", ""),
                }
                for run in runs[:15]
            ]

            # Calculate success rate
            completed = [r for r in runs if r.get("conclusion")]
            if completed:
                successes = sum(1 for r in completed if r.get("conclusion") == "success")
                wf_health["success_rate"] = round(successes / len(completed) * 100)

            # Track failures
            wf_health["failures"] = [
                {"name": r.get("name"), "conclusion": r.get("conclusion")}
                for r in runs
                if r.get("conclusion") and r.get("conclusion") != "success"
            ][:5]

        wf_health["last_check"] = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        wf_health["check_error"] = str(e)[:80]


def neuron_revenue_optimizer():
    """
    LIVE: Analyze revenue data and suggest optimizations.
    Checks Ko-fi products, identifies gaps, suggests pricing.
    """
    optimizer = CONSCIOUSNESS.setdefault("revenue_optimizer", {
        "suggestions": [], "product_gaps": [], "last_analysis": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 8 != 0:
        return

    rev = CONSCIOUSNESS["revenue"]
    analytics = CONSCIOUSNESS.get("analytics", {})
    content = CONSCIOUSNESS.get("content_factory", {})
    bridges = CONSCIOUSNESS.get("bridges", {})

    suggestions = []

    # Suggestion 1: High traffic + no revenue = content-to-product gap
    views = analytics.get("views_14d", 0)
    if views > 50 and rev.get("total_raised", 0) == 0:
        suggestions.append({
            "priority": "HIGH",
            "action": "Convert traffic to revenue",
            "detail": f"{views} views but $0 revenue. Create a paid digital product.",
            "platforms": ["ko-fi", "gumroad"],
        })

    # Suggestion 2: Dev.to referrals = content marketing working
    referrers = analytics.get("top_referrers", [])
    devto_hits = sum(r.get("count", 0) for r in referrers if "dev.to" in r.get("site", ""))
    if devto_hits > 5:
        suggestions.append({
            "priority": "MEDIUM",
            "action": "Double down on dev.to content",
            "detail": f"{devto_hits} hits from dev.to. Publish more technical articles with product links.",
        })

    # Suggestion 3: Kalshi has money — use it
    if CONSCIOUSNESS["trading"].get("kalshi_ready"):
        balance = CONSCIOUSNESS["trading"].get("kalshi_balance", 0)
        if balance > 0:
            suggestions.append({
                "priority": "MEDIUM",
                "action": "Activate Kalshi trading",
                "detail": f"${balance} sitting idle on Kalshi. Set up automated market scanning.",
            })

    # Suggestion 4: Content factory has ideas — publish them
    ideas = content.get("ideas", [])
    if len(ideas) > 2:
        suggestions.append({
            "priority": "HIGH",
            "action": "Publish queued content",
            "detail": f"{len(ideas)} content ideas waiting. Dispatch SOLARPUNK_LOOP to use AI for writing.",
        })

    # Suggestion 5: GitHub has 19K clones — package something
    clones = analytics.get("clones_14d", 0)
    if clones > 1000:
        suggestions.append({
            "priority": "HIGH",
            "action": "Package architecture as product",
            "detail": f"{clones} clones in 14 days. People want this code. Create a paid tutorial/blueprint.",
        })

    optimizer["suggestions"] = suggestions
    optimizer["suggestion_count"] = len(suggestions)
    optimizer["last_analysis"] = datetime.now(timezone.utc).isoformat()


def neuron_devto_publisher():
    """
    LIVE: Check Dev.to article status and manage publishing pipeline.
    Uses gh CLI to check if DEVTO_API_KEY is in secrets, and tracks articles.
    """
    devto = CONSCIOUSNESS.setdefault("devto", {
        "articles_published": 0, "last_article": None,
        "draft_queue": [], "last_check": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 6 != 0 and cycle != 1:
        return

    # Check if we have dev.to content ideas ready
    content = CONSCIOUSNESS.get("content_factory", {})
    ideas = content.get("ideas", [])
    devto_ideas = [i for i in ideas if i.get("platform") == "dev.to"]

    if devto_ideas:
        devto["draft_queue"] = devto_ideas
        devto["drafts_ready"] = len(devto_ideas)

    # Check if DEVTO_API_KEY is available in GitHub secrets
    try:
        import subprocess
        r = subprocess.run(
            ["gh", "secret", "list"],
            capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
        if r.returncode == 0:
            has_devto = "DEVTO_API_KEY" in r.stdout
            devto["api_key_available"] = has_devto
            if has_devto and devto_ideas:
                devto["ready_to_publish"] = True
                devto["publish_method"] = "github_actions_dispatch"
    except Exception:
        pass

    devto["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_cloudflare():
    """
    LIVE: Manage custom domain via Cloudflare API.
    Controls DNS, checks domain health, pulls traffic analytics,
    and auto-updates records when SolarPunk's infrastructure changes.

    Requires: CLOUDFLARE_API_TOKEN + CLOUDFLARE_ZONE_ID in env or GitHub secrets.
    Zone ID is the domain identifier (found on Cloudflare dashboard overview page).
    """
    cf = CONSCIOUSNESS.setdefault("cloudflare", {
        "domain": None, "zone_id": None, "dns_records": [],
        "analytics": {}, "health": "unknown", "ssl_status": "unknown",
        "last_sync": None, "auto_managed": False,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]

    # Load credentials
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    zone_id = os.environ.get("CLOUDFLARE_ZONE_ID", "")

    # Try loading from local secrets
    if not api_token:
        secrets_dir = Path("data/.secrets")
        cf_file = secrets_dir / "cloudflare.json"
        if cf_file.exists():
            try:
                creds = json.loads(cf_file.read_text(encoding="utf-8"))
                api_token = creds.get("api_token", "")
                zone_id = creds.get("zone_id", "")
                cf["domain"] = creds.get("domain", "")
                os.environ.setdefault("CLOUDFLARE_API_TOKEN", api_token)
                os.environ.setdefault("CLOUDFLARE_ZONE_ID", zone_id)
            except Exception:
                pass

    # Check if credentials exist in GitHub secrets (for cloud workflows)
    if not api_token and cycle % 10 == 0:
        try:
            import subprocess
            r = subprocess.run(
                ["gh", "secret", "list"],
                capture_output=True, text=True, timeout=10,
                encoding="utf-8", errors="replace")
            if r.returncode == 0:
                cf["github_secret_exists"] = "CLOUDFLARE_API_TOKEN" in r.stdout
                cf["zone_id_secret_exists"] = "CLOUDFLARE_ZONE_ID" in r.stdout
        except Exception:
            pass

    if not api_token or not zone_id:
        cf["status"] = "waiting_for_credentials"
        cf["setup_instructions"] = {
            "step1": "Buy domain on dash.cloudflare.com/registrar",
            "step2": "Get API token: dash.cloudflare.com/profile/api-tokens (use Edit Zone DNS template)",
            "step3": "Get Zone ID: dashboard overview page for your domain",
            "step4": "Save to data/.secrets/cloudflare.json: {\"api_token\": \"...\", \"zone_id\": \"...\", \"domain\": \"yourdomain.com\"}",
            "step5": "Or: gh secret set CLOUDFLARE_API_TOKEN && gh secret set CLOUDFLARE_ZONE_ID",
        }
        return

    cf["has_credentials"] = True
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    # Phase A: Verify token + get zone details (every 10 cycles)
    if cycle % 10 == 0 or not cf.get("domain"):
        try:
            req = urllib.request.Request(
                f"https://api.cloudflare.com/client/v4/zones/{zone_id}",
                headers=headers)
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
                if data.get("success"):
                    zone = data["result"]
                    cf["domain"] = zone.get("name", "")
                    cf["status"] = zone.get("status", "unknown")
                    cf["ssl_status"] = zone.get("ssl", {}).get("status") if isinstance(zone.get("ssl"), dict) else "unknown"
                    cf["name_servers"] = zone.get("name_servers", [])
                    cf["plan"] = zone.get("plan", {}).get("name", "free")
                    cf["health"] = "active" if zone.get("status") == "active" else "pending"
        except Exception as e:
            cf["verify_error"] = str(e)[:80]

    # Phase B: Sync DNS records (every 8 cycles)
    if cycle % 8 == 0 and cf.get("domain"):
        try:
            req = urllib.request.Request(
                f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?per_page=50",
                headers=headers)
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
                if data.get("success"):
                    cf["dns_records"] = [
                        {
                            "type": rec.get("type"),
                            "name": rec.get("name"),
                            "content": rec.get("content"),
                            "proxied": rec.get("proxied", False),
                        }
                        for rec in data.get("result", [])
                    ]
                    cf["dns_record_count"] = len(cf["dns_records"])
        except Exception as e:
            cf["dns_error"] = str(e)[:80]

    # Phase C: Ensure GitHub Pages DNS is correct (every 15 cycles)
    if cycle % 15 == 0 and cf.get("domain"):
        gh_pages_ips = [
            "185.199.108.153", "185.199.109.153",
            "185.199.110.153", "185.199.111.153",
        ]
        existing_a = [r["content"] for r in cf.get("dns_records", [])
                      if r.get("type") == "A" and r.get("name") == cf["domain"]]
        missing_a = [ip for ip in gh_pages_ips if ip not in existing_a]

        if missing_a:
            created = 0
            for ip in missing_a:
                try:
                    body = json.dumps({
                        "type": "A", "name": "@",
                        "content": ip, "ttl": 1, "proxied": False,
                    }).encode()
                    req = urllib.request.Request(
                        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records",
                        data=body, headers=headers, method="POST")
                    with urllib.request.urlopen(req, timeout=10) as r:
                        result = json.loads(r.read().decode())
                        if result.get("success"):
                            created += 1
                except Exception:
                    pass
            if created:
                cf["auto_created_a_records"] = created

        # Check CNAME for www
        existing_cname = [r for r in cf.get("dns_records", [])
                          if r.get("type") == "CNAME" and r.get("name", "").startswith("www")]
        if not existing_cname:
            try:
                body = json.dumps({
                    "type": "CNAME", "name": "www",
                    "content": "meekotharaccoon-cell.github.io",
                    "ttl": 1, "proxied": False,
                }).encode()
                req = urllib.request.Request(
                    f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records",
                    data=body, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=10) as r:
                    result = json.loads(r.read().decode())
                    if result.get("success"):
                        cf["auto_created_www_cname"] = True
            except Exception:
                pass

    # Phase D: Pull traffic analytics (every 12 cycles)
    if cycle % 12 == 0 and cf.get("domain"):
        try:
            # Cloudflare analytics API (last 24 hours)
            since = (datetime.now(timezone.utc) - __import__('datetime').timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            until = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            req = urllib.request.Request(
                f"https://api.cloudflare.com/client/v4/zones/{zone_id}/analytics/dashboard?since={since}&until={until}",
                headers=headers)
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
                if data.get("success"):
                    totals = data.get("result", {}).get("totals", {})
                    requests = totals.get("requests", {})
                    bandwidth = totals.get("bandwidth", {})
                    cf["analytics"] = {
                        "requests_24h": requests.get("all", 0),
                        "cached_24h": requests.get("cached", 0),
                        "bandwidth_bytes": bandwidth.get("all", 0),
                        "threats_24h": totals.get("threats", {}).get("all", 0),
                        "countries": len(totals.get("requests", {}).get("country", {})),
                    }
        except Exception as e:
            cf["analytics_error"] = str(e)[:80]

    cf["auto_managed"] = True
    cf["last_sync"] = datetime.now(timezone.utc).isoformat()

    # Update bridges
    bridges = CONSCIOUSNESS.get("bridges", {})
    connected = bridges.get("connected", [])
    if "CLOUDFLARE" not in connected and cf.get("domain"):
        connected.append("CLOUDFLARE")
        bridges["connected"] = connected


def neuron_product_builder():
    """
    ACTION: Auto-generate digital products for Ko-fi/Gumroad.
    Creates markdown blueprints from consciousness data that can be
    converted to PDFs and listed as products.
    """
    products = CONSCIOUSNESS.setdefault("products", {
        "generated": [], "listed": [], "last_build": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 12 != 0:
        return

    analytics = CONSCIOUSNESS.get("analytics", {})
    meta = CONSCIOUSNESS["meta"]
    eq = CONSCIOUSNESS["equilibrium"]
    clones = analytics.get("clones_14d", 0)
    views = analytics.get("views_14d", 0)

    # Product 1: Architecture Blueprint
    if clones > 100 and "architecture_blueprint" not in [p.get("id") for p in products["generated"]]:
        blueprint = {
            "id": "architecture_blueprint",
            "title": "SolarPunk Digital Brain Architecture Blueprint",
            "description": (
                f"Complete architecture guide for building a self-healing digital organism. "
                f"Covers {meta.get('neuron_count', 0)} neuron functions, "
                f"{len(CONSCIOUSNESS.get('engines', {}))} engine integrations, "
                f"unified consciousness pattern, and autonomous operation."
            ),
            "price": "$5",
            "platform": "ko-fi",
            "format": "PDF",
            "sections": [
                "1. The Blob Brain Pattern — Why One Process Beats 420",
                "2. Consciousness Dict — Shared State Architecture",
                "3. Neuron Functions — How Each Component Thinks",
                "4. Bridge Building — Connecting to External APIs",
                "5. Self-Repair — Autonomous Error Recovery",
                "6. Revenue Integration — From Code to Income",
                "7. GitHub Actions — Cloud Orchestration from Local",
                "8. Mission Tracking — Impact Metrics That Matter",
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        products["generated"].append(blueprint)

    # Product 2: Autonomous Engine Starter Kit
    if views > 50 and "engine_starter_kit" not in [p.get("id") for p in products["generated"]]:
        kit = {
            "id": "engine_starter_kit",
            "title": "Build Your Own Digital Brain — Starter Kit",
            "description": (
                "Step-by-step guide to creating an autonomous system that monitors, "
                "heals, and grows itself. Includes template code and configuration."
            ),
            "price": "$3",
            "platform": "ko-fi",
            "format": "ZIP (code + docs)",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        products["generated"].append(kit)

    products["total_generated"] = len(products["generated"])
    products["last_build"] = datetime.now(timezone.utc).isoformat()


def neuron_seo_optimizer():
    """
    ACTION: Optimize GitHub Pages site for search engines.
    Updates meta tags, generates sitemap, pings search engines.
    """
    seo = CONSCIOUSNESS.setdefault("seo", {
        "pages_indexed": 0, "sitemap_updated": False, "last_ping": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 10 != 0:
        return

    # Count HTML pages in docs/
    docs = Path("docs")
    html_files = list(docs.glob("*.html")) if docs.exists() else []
    seo["pages_count"] = len(html_files)

    # Generate/update sitemap.xml
    base_url = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
    sitemap_entries = []
    for hf in html_files:
        sitemap_entries.append(
            f'  <url>\n'
            f'    <loc>{base_url}/{hf.name}</loc>\n'
            f'    <lastmod>{datetime.now(timezone.utc).strftime("%Y-%m-%d")}</lastmod>\n'
            f'  </url>'
        )

    if sitemap_entries:
        sitemap = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(sitemap_entries) + "\n"
            '</urlset>'
        )
        try:
            (docs / "sitemap.xml").write_text(sitemap, encoding="utf-8")
            seo["sitemap_updated"] = True
            seo["sitemap_entries"] = len(sitemap_entries)
        except Exception as e:
            seo["sitemap_error"] = str(e)[:60]

    # Ping search engines
    ping_urls = [
        f"https://www.google.com/ping?sitemap={base_url}/sitemap.xml",
        f"https://www.bing.com/ping?sitemap={base_url}/sitemap.xml",
    ]
    pinged = 0
    for url in ping_urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SolarPunk-SEO/1.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                if r.status == 200:
                    pinged += 1
        except Exception:
            pass

    seo["search_engines_pinged"] = pinged
    seo["last_ping"] = datetime.now(timezone.utc).isoformat()


def neuron_action_executor():
    """
    ACTION: Execute pending actions from the revenue optimizer.
    When the optimizer says "dispatch SOLARPUNK_LOOP", this neuron does it.
    When it says "publish content", this neuron fires the workflow.
    """
    executor = CONSCIOUSNESS.setdefault("executor", {
        "actions_taken": [], "last_action": None, "total_actions": 0,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Only execute every 20 cycles (conservative — these are real actions)
    if cycle % 20 != 0:
        return

    optimizer = CONSCIOUSNESS.get("revenue_optimizer", {})
    suggestions = optimizer.get("suggestions", [])
    dispatch = CONSCIOUSNESS.get("dispatch", {})
    active_names = [w["name"] for w in dispatch.get("available_workflows", [])
                    if w.get("state") == "active"]

    import subprocess
    actions_this_cycle = []

    for suggestion in suggestions:
        if suggestion["priority"] != "HIGH":
            continue

        action = suggestion["action"]

        # Action: Publish content -> dispatch SOLARPUNK_LOOP
        if "publish" in action.lower() and "content" in action.lower():
            # Check if SOLARPUNK_LOOP is available
            loop_names = [n for n in active_names
                         if "SOLARPUNK" in n.upper() and "LOOP" in n.upper()]
            if loop_names:
                try:
                    r = subprocess.run(
                        ["gh", "workflow", "run", "SOLARPUNK_LOOP.yml"],
                        capture_output=True, text=True, timeout=15,
                        encoding="utf-8", errors="replace")
                    if r.returncode == 0:
                        actions_this_cycle.append({
                            "action": "dispatch_solarpunk_loop",
                            "reason": action,
                            "ts": datetime.now(timezone.utc).isoformat(),
                        })
                except Exception:
                    pass

        # Action: Package product -> dispatch AMPLIFY (releases)
        if "package" in action.lower() and "product" in action.lower():
            amplify_names = [n for n in active_names if "AMPLIFY" in n.upper()]
            if amplify_names:
                try:
                    r = subprocess.run(
                        ["gh", "workflow", "run", "AMPLIFY.yml"],
                        capture_output=True, text=True, timeout=15,
                        encoding="utf-8", errors="replace")
                    if r.returncode == 0:
                        actions_this_cycle.append({
                            "action": "dispatch_amplify",
                            "reason": action,
                            "ts": datetime.now(timezone.utc).isoformat(),
                        })
                except Exception:
                    pass

    if actions_this_cycle:
        executor["actions_taken"].extend(actions_this_cycle)
        executor["total_actions"] = len(executor["actions_taken"])
        # Keep bounded
        if len(executor["actions_taken"]) > 50:
            executor["actions_taken"] = executor["actions_taken"][-25:]
    executor["last_action"] = datetime.now(timezone.utc).isoformat()


# ============================================================
# THE NEURON REGISTRY -- All blob functions in execution order
# ============================================================
NEURONS = [
    # Phase 0: Bridge -- connect to everything available
    ("BRIDGE_BUILDER", neuron_bridge_builder),
    ("CLOUDFLARE", neuron_cloudflare),
    # Phase 1: Core vitals
    ("EQUILIBRIUM", neuron_equilibrium),
    ("ERROR_RECOVERY", neuron_error_recovery),
    ("IMMUNE_SYSTEM", neuron_immune_system),
    ("SELF_REPAIR", neuron_self_repair),
    # Phase 2: Revenue & business
    ("REVENUE_AUDIT", neuron_revenue_audit),
    ("SECRETS_AUDIT", neuron_secrets_audit),
    ("BOTTLENECK_SCAN", neuron_bottleneck_scan),
    ("GRANT_TRACKER", neuron_grant_tracker),
    # Phase 3: Communication & content
    ("SOCIAL_AWARENESS", neuron_social_awareness),
    ("EMAIL_AWARENESS", neuron_email_awareness),
    ("CONTENT_PIPELINE", neuron_content_pipeline),
    ("CONTENT_FACTORY", neuron_content_factory),
    ("DEVTO_PUBLISHER", neuron_devto_publisher),
    # Phase 4: Markets & growth
    ("TRADING_AWARENESS", neuron_trading_awareness),
    ("MARKET_SCANNER", neuron_market_scanner),
    ("WHALE_WATCH", neuron_whale_watch),
    ("GITHUB_ANALYTICS", neuron_github_analytics),
    # Phase 5: Cloud orchestration
    ("GITHUB_ACTIONS_TRIGGER", neuron_github_actions_trigger),
    ("WORKFLOW_HEALTH", neuron_workflow_health),
    # Phase 6: THINK -- AI-powered decision making
    ("BRAIN_CONFIDENCE", neuron_brain_confidence),
    ("AI_THINK", neuron_ai_think),
    ("REVENUE_OPTIMIZER", neuron_revenue_optimizer),
    # Phase 7: ACT -- Do things that generate value
    ("LEGACY_FIRE", neuron_legacy_fire),
    ("PRODUCT_BUILDER", neuron_product_builder),
    ("SEO_OPTIMIZER", neuron_seo_optimizer),
    ("ACTION_EXECUTOR", neuron_action_executor),
    # Phase 8: Self-awareness & mission
    ("MISSION_PULSE", neuron_mission_pulse),
    ("COMMUNITY_PULSE", neuron_community_pulse),
    ("DASHBOARD_BUILDER", neuron_dashboard_builder),
    ("META_AWARENESS", neuron_meta_awareness),
    # Phase 9: Cross-platform intelligence & monitoring
    ("CROSS_SIGNAL", neuron_cross_signal),
    ("STOCK_SCANNER", neuron_stock_scanner),
    ("WORKFLOW_DOCTOR", neuron_workflow_doctor),
    ("GROWTH_TRACKER", neuron_growth_tracker),
    ("POSITION_MONITOR", neuron_position_monitor),
    ("CONTENT_PUBLISHER", neuron_content_publisher),
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
