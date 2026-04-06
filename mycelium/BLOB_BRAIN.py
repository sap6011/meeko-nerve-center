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


def neuron_prediction_arbitrage():
    """
    INTELLIGENCE: Compare Kalshi vs Polymarket prices on overlapping events.
    A 5+ cent divergence on the same binary outcome is a statistical edge.
    Merges data from market_scanner (Kalshi) and whale_watch (Polymarket).
    """
    arb = CONSCIOUSNESS.setdefault("pred_arb", {
        "opportunities": [], "last_scan": None, "total_found": 0,
        "best_edge_ever": 0,
    })
    kalshi_markets = CONSCIOUSNESS.get("markets", {}).get("top_markets", [])
    poly_markets = CONSCIOUSNESS.get("whale_watch", {}).get("polymarket_whales", [])

    if not kalshi_markets or not poly_markets:
        return

    # Build lookup of Polymarket prices by keyword matching
    poly_lookup = {}
    for pm in poly_markets:
        q = pm.get("question", "").lower()
        # Extract key terms for fuzzy matching
        for keyword in ["trump", "bitcoin", "elon", "openai", "anthropic",
                        "mars", "trillionaire", "ipo", "ai", "robot",
                        "china", "moon", "nuclear", "pandemic", "recession"]:
            if keyword in q:
                poly_lookup.setdefault(keyword, []).append(pm)

    opportunities = []
    for km in kalshi_markets:
        title = km.get("title", km.get("event_title", "")).lower()
        ticker = km.get("ticker", "")
        kalshi_yes = km.get("yes_bid_dollars", km.get("yes_bid", 0))
        if isinstance(kalshi_yes, str):
            try:
                kalshi_yes = float(kalshi_yes)
            except (ValueError, TypeError):
                continue
        if not kalshi_yes or kalshi_yes <= 0:
            continue

        # Find matching Polymarket events
        for keyword, poly_list in poly_lookup.items():
            if keyword in title:
                for pm in poly_list:
                    poly_yes = pm.get("yes_price", 0)
                    if not poly_yes:
                        continue
                    # Normalize to 0-1 scale
                    k_price = kalshi_yes if kalshi_yes <= 1 else kalshi_yes / 100
                    p_price = poly_yes if poly_yes <= 1 else poly_yes / 100
                    divergence = abs(k_price - p_price)
                    if divergence >= 0.05:
                        direction = "BUY_KALSHI_YES" if k_price < p_price else "BUY_KALSHI_NO"
                        opportunities.append({
                            "kalshi_ticker": ticker,
                            "kalshi_title": km.get("title", km.get("event_title", ""))[:60],
                            "poly_question": pm.get("question", "")[:60],
                            "kalshi_yes": round(k_price, 3),
                            "poly_yes": round(p_price, 3),
                            "divergence": round(divergence, 3),
                            "edge_pct": round(divergence * 100, 1),
                            "direction": direction,
                            "keyword": keyword,
                        })

    # Sort by edge size
    opportunities.sort(key=lambda x: x["divergence"], reverse=True)
    arb["opportunities"] = opportunities[:20]
    arb["total_found"] = len(opportunities)
    arb["last_scan"] = datetime.now(timezone.utc).isoformat()
    if opportunities:
        best = opportunities[0]["divergence"]
        if best > arb.get("best_edge_ever", 0):
            arb["best_edge_ever"] = best


def neuron_solana_heartbeat():
    """
    LIVE: Monitor Solana chain state via public RPC.
    Tracks SOL price, network health, and wallet balance if configured.
    """
    sol = CONSCIOUSNESS.setdefault("solana", {
        "sol_price": 0, "network_ok": False, "slot": 0,
        "tps": 0, "last_beat": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Only check every 3 cycles (rate limit friendly)
    if cycle % 3 != 0:
        return

    import urllib.request

    # Get SOL price from CoinGecko (free, no key)
    try:
        req = urllib.request.Request(
            "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd&include_24hr_change=true",
            headers={"Accept": "application/json", "User-Agent": "SolarPunk/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
            sol["sol_price"] = data.get("solana", {}).get("usd", 0)
            sol["sol_24h_change"] = data.get("solana", {}).get("usd_24h_change", 0)
    except Exception:
        pass

    # Get network slot height from public RPC
    try:
        rpc_payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "getSlot"}).encode()
        req = urllib.request.Request(
            "https://api.mainnet-beta.solana.com",
            data=rpc_payload,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
            sol["slot"] = data.get("result", 0)
            sol["network_ok"] = True
    except Exception:
        sol["network_ok"] = False

    # Get BTC and ETH prices too for cross-reference
    try:
        req = urllib.request.Request(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true",
            headers={"Accept": "application/json", "User-Agent": "SolarPunk/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
            sol["btc_price"] = data.get("bitcoin", {}).get("usd", 0)
            sol["btc_24h"] = data.get("bitcoin", {}).get("usd_24h_change", 0)
            sol["eth_price"] = data.get("ethereum", {}).get("usd", 0)
            sol["eth_24h"] = data.get("ethereum", {}).get("usd_24h_change", 0)
    except Exception:
        pass

    sol["last_beat"] = datetime.now(timezone.utc).isoformat()


def neuron_portfolio_optimizer():
    """
    INTELLIGENCE: Analyze portfolio and suggest optimal position sizing.
    Uses Kelly criterion and cross-signal confidence for sizing.
    """
    optimizer = CONSCIOUSNESS.setdefault("portfolio", {
        "suggestions": [], "risk_budget": 0, "last_analysis": None,
        "concentration_warning": False,
    })
    trading = CONSCIOUSNESS.get("trading", {})
    positions = CONSCIOUSNESS.get("position_monitor", {})
    signals = CONSCIOUSNESS.get("cross_signals", {})
    arb = CONSCIOUSNESS.get("pred_arb", {})

    total_balance = trading.get("kalshi_total", 0)
    cash = trading.get("kalshi_balance", 0)
    if total_balance <= 0:
        return

    # Risk budget: never risk more than 20% of total on any single position
    max_single = total_balance * 0.20
    # Cash allocation: keep at least 30% in cash for opportunities
    min_cash_pct = 0.30
    ideal_cash = total_balance * min_cash_pct
    optimizer["risk_budget"] = round(max_single, 2)

    suggestions = []

    # Check concentration -- are we too heavy in one position?
    pos_alerts = positions.get("alerts", [])
    if pos_alerts:
        for alert in pos_alerts:
            if alert.get("pct_of_portfolio", 0) > 25:
                optimizer["concentration_warning"] = True
                suggestions.append({
                    "type": "REDUCE",
                    "reason": f"Position {alert.get('ticker','')} is >25% of portfolio",
                    "priority": "HIGH",
                })

    # Arbitrage opportunities are highest conviction
    arb_opps = arb.get("opportunities", [])
    for opp in arb_opps[:3]:
        edge = opp.get("divergence", 0)
        # Kelly: f* = edge / odds (simplified for binary)
        kelly_frac = min(edge * 2, 0.15)  # Cap at 15%
        suggested_size = round(total_balance * kelly_frac, 2)
        if suggested_size >= 1:
            suggestions.append({
                "type": "ARB_TRADE",
                "ticker": opp.get("kalshi_ticker", ""),
                "direction": opp.get("direction", ""),
                "edge_pct": opp.get("edge_pct", 0),
                "kelly_size": suggested_size,
                "priority": "HIGH" if edge > 0.10 else "MEDIUM",
            })

    # High-confidence cross-signals
    unified = signals.get("unified", [])
    for sig in unified[:5]:
        conf = sig.get("confidence", 0)
        if conf >= 90:
            kelly_frac = min((conf / 100) * 0.10, 0.10)
            suggested_size = round(total_balance * kelly_frac, 2)
            if suggested_size >= 1:
                suggestions.append({
                    "type": "SIGNAL_TRADE",
                    "signal": sig.get("signal", ""),
                    "ticker": sig.get("ticker", ""),
                    "confidence": conf,
                    "kelly_size": suggested_size,
                    "priority": "MEDIUM",
                })

    # Cash check
    if cash < ideal_cash:
        suggestions.append({
            "type": "HOLD_CASH",
            "reason": f"Cash ${cash:.2f} < ideal ${ideal_cash:.2f} ({min_cash_pct*100:.0f}%)",
            "priority": "HIGH",
        })

    optimizer["suggestions"] = suggestions[:15]
    optimizer["cash_pct"] = round(cash / max(total_balance, 1) * 100, 1)
    optimizer["last_analysis"] = datetime.now(timezone.utc).isoformat()


def neuron_risk_manager():
    """
    SAFETY: Enforce risk limits and detect dangerous patterns.
    Never let the blob blow up the account.
    """
    risk = CONSCIOUSNESS.setdefault("risk", {
        "alerts": [], "max_drawdown": 0, "daily_loss_limit": 0,
        "positions_at_risk": 0, "risk_score": 0, "last_check": None,
    })
    trading = CONSCIOUSNESS.get("trading", {})
    positions = CONSCIOUSNESS.get("position_monitor", {})
    equilibrium = CONSCIOUSNESS.get("equilibrium", {})

    total = trading.get("kalshi_total", 0)
    cash = trading.get("kalshi_balance", 0)
    portfolio_value = trading.get("kalshi_portfolio", 0)

    if total <= 0:
        return

    alerts = []
    risk_score = 0  # 0-100, higher = more dangerous

    # Rule 1: Never let cash drop below $5 (emergency reserve)
    if cash < 5:
        alerts.append({"rule": "EMERGENCY_RESERVE", "msg": f"Cash ${cash:.2f} < $5 reserve", "severity": "CRITICAL"})
        risk_score += 40

    # Rule 2: Max 50% in any single position
    pos_alerts = positions.get("alerts", [])
    for pa in pos_alerts:
        pct = pa.get("pct_of_portfolio", 0)
        if pct > 50:
            alerts.append({"rule": "CONCENTRATION", "msg": f"{pa.get('ticker','?')} is {pct:.0f}% of portfolio", "severity": "HIGH"})
            risk_score += 20

    # Rule 3: If equilibrium is in red zone, reduce risk appetite
    eq_score = equilibrium.get("score", 50)
    if eq_score < 25:
        alerts.append({"rule": "SYSTEM_HEALTH", "msg": f"Equilibrium at {eq_score}% -- reduce trading", "severity": "MEDIUM"})
        risk_score += 15

    # Rule 4: Max daily loss = 10% of portfolio
    daily_loss_limit = total * 0.10
    risk["daily_loss_limit"] = round(daily_loss_limit, 2)

    # Rule 5: Track max drawdown
    # Compare current total to historical peak
    growth = CONSCIOUSNESS.get("growth", {})
    history = growth.get("history", [])
    if history:
        peak_totals = [h.get("kalshi_total", 0) for h in history if h.get("kalshi_total", 0) > 0]
        if peak_totals:
            peak = max(peak_totals)
            if peak > 0:
                drawdown = (peak - total) / peak * 100
                risk["max_drawdown"] = round(drawdown, 1)
                if drawdown > 20:
                    alerts.append({"rule": "DRAWDOWN", "msg": f"Drawdown {drawdown:.1f}% from peak ${peak:.2f}", "severity": "HIGH"})
                    risk_score += 25

    # Rule 6: Fear/Greed extreme = caution
    fear_greed = CONSCIOUSNESS.get("cross_signals", {}).get("fear_greed", 50)
    if fear_greed < 15:
        alerts.append({"rule": "EXTREME_FEAR", "msg": f"Fear/Greed={fear_greed} -- market panic, be cautious", "severity": "MEDIUM"})
        risk_score += 10
    elif fear_greed > 85:
        alerts.append({"rule": "EXTREME_GREED", "msg": f"Fear/Greed={fear_greed} -- market euphoria, be cautious", "severity": "MEDIUM"})
        risk_score += 10

    risk["alerts"] = alerts
    risk["risk_score"] = min(risk_score, 100)
    risk["positions_at_risk"] = len([a for a in alerts if a["severity"] in ("CRITICAL", "HIGH")])
    risk["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_news_pulse():
    """
    INTELLIGENCE: Scan free news APIs for market-moving events.
    Feeds into trading decisions and content ideas.
    """
    news = CONSCIOUSNESS.setdefault("news", {
        "headlines": [], "sentiment": "neutral", "last_scan": None,
        "trending_topics": [],
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Only scan every 5 cycles
    if cycle % 5 != 0:
        return

    import urllib.request
    headlines = []

    # Source 1: GNews API (free tier, no key for basic)
    try:
        req = urllib.request.Request(
            "https://gnews.io/api/v4/top-headlines?category=technology&lang=en&max=5&apikey=free",
            headers={"User-Agent": "SolarPunk/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
            for article in data.get("articles", [])[:5]:
                headlines.append({
                    "title": article.get("title", "")[:100],
                    "source": article.get("source", {}).get("name", ""),
                    "url": article.get("url", ""),
                    "ts": article.get("publishedAt", ""),
                })
    except Exception:
        pass

    # Source 2: Reddit/Hacker News via public JSON endpoints
    try:
        req = urllib.request.Request(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            headers={"User-Agent": "SolarPunk/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            story_ids = json.loads(r.read().decode())[:5]
        for sid in story_ids:
            try:
                req2 = urllib.request.Request(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                    headers={"User-Agent": "SolarPunk/1.0"})
                with urllib.request.urlopen(req2, timeout=5) as r2:
                    story = json.loads(r2.read().decode())
                    headlines.append({
                        "title": story.get("title", "")[:100],
                        "source": "HackerNews",
                        "url": story.get("url", ""),
                        "score": story.get("score", 0),
                    })
            except Exception:
                pass
    except Exception:
        pass

    # Simple sentiment analysis on headlines
    positive_words = {"up", "surge", "gain", "rally", "bull", "growth", "win", "record", "breakthrough"}
    negative_words = {"down", "crash", "fall", "bear", "loss", "fear", "collapse", "fail", "crisis", "war"}

    pos_count = 0
    neg_count = 0
    topics = {}
    for h in headlines:
        title_lower = h.get("title", "").lower()
        for w in positive_words:
            if w in title_lower:
                pos_count += 1
        for w in negative_words:
            if w in title_lower:
                neg_count += 1
        # Extract trending topics
        for keyword in ["ai", "crypto", "bitcoin", "trump", "tariff", "openai",
                        "anthropic", "solana", "elon", "market", "recession"]:
            if keyword in title_lower:
                topics[keyword] = topics.get(keyword, 0) + 1

    if pos_count > neg_count + 2:
        news["sentiment"] = "bullish"
    elif neg_count > pos_count + 2:
        news["sentiment"] = "bearish"
    else:
        news["sentiment"] = "neutral"

    news["headlines"] = headlines[:15]
    news["trending_topics"] = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]
    news["last_scan"] = datetime.now(timezone.utc).isoformat()
    news["pos_signals"] = pos_count
    news["neg_signals"] = neg_count


def neuron_trend_detector():
    """
    INTELLIGENCE: Detect patterns and trends across blob lifecycle.
    Uses growth history to identify: improving/declining health,
    revenue momentum, trading performance, audience growth.
    """
    trends = CONSCIOUSNESS.setdefault("trends", {
        "health_trend": "unknown", "revenue_trend": "unknown",
        "trading_trend": "unknown", "patterns": [], "last_analysis": None,
    })
    growth = CONSCIOUSNESS.get("growth", {})
    history = growth.get("history", [])

    if len(history) < 2:
        return

    patterns = []

    # Analyze health trend over last N snapshots
    recent = history[-10:] if len(history) >= 10 else history
    health_values = [h.get("health", 0) for h in recent]
    if len(health_values) >= 2:
        avg_first_half = sum(health_values[:len(health_values)//2]) / max(len(health_values)//2, 1)
        avg_second_half = sum(health_values[len(health_values)//2:]) / max(len(health_values) - len(health_values)//2, 1)
        if avg_second_half > avg_first_half + 5:
            trends["health_trend"] = "improving"
            patterns.append({"type": "HEALTH_IMPROVING", "delta": round(avg_second_half - avg_first_half, 1)})
        elif avg_second_half < avg_first_half - 5:
            trends["health_trend"] = "declining"
            patterns.append({"type": "HEALTH_DECLINING", "delta": round(avg_second_half - avg_first_half, 1)})
        else:
            trends["health_trend"] = "stable"

    # Analyze neuron count growth
    neuron_counts = [h.get("neurons", 0) for h in recent]
    if len(neuron_counts) >= 2:
        growth_rate = neuron_counts[-1] - neuron_counts[0]
        if growth_rate > 0:
            patterns.append({"type": "NEURON_GROWTH", "added": growth_rate,
                             "from": neuron_counts[0], "to": neuron_counts[-1]})

    # Analyze trading performance
    kalshi_values = [h.get("kalshi_total", 0) for h in recent if h.get("kalshi_total", 0) > 0]
    if len(kalshi_values) >= 2:
        pnl = kalshi_values[-1] - kalshi_values[0]
        if pnl > 1:
            trends["trading_trend"] = "winning"
            patterns.append({"type": "TRADING_UP", "pnl": round(pnl, 2)})
        elif pnl < -1:
            trends["trading_trend"] = "losing"
            patterns.append({"type": "TRADING_DOWN", "pnl": round(pnl, 2)})
        else:
            trends["trading_trend"] = "flat"

    # Analyze confidence trajectory
    conf_values = [h.get("confidence", 0) for h in recent]
    if len(conf_values) >= 2:
        conf_delta = conf_values[-1] - conf_values[0]
        if abs(conf_delta) > 5:
            patterns.append({"type": "CONFIDENCE_SHIFT", "delta": conf_delta,
                             "direction": "up" if conf_delta > 0 else "down"})

    # Detect signal count trends
    signal_counts = [h.get("signals", 0) for h in recent]
    if len(signal_counts) >= 2 and signal_counts[-1] > signal_counts[0] * 1.5:
        patterns.append({"type": "SIGNAL_SURGE", "from": signal_counts[0], "to": signal_counts[-1]})

    trends["patterns"] = patterns
    trends["snapshots_analyzed"] = len(recent)
    trends["last_analysis"] = datetime.now(timezone.utc).isoformat()


def neuron_inception_memory():
    """
    DEEP MEMORY: Go back to the very beginning and re-process everything.
    Scans ALL data files, ALL engine states, and the git history to build
    a complete timeline of the blob's evolution from inception.
    This neuron runs ONCE then caches -- it's the blob's autobiography.
    """
    inception = CONSCIOUSNESS.setdefault("inception", {
        "origin_date": None, "total_commits": 0, "evolution_phases": [],
        "all_engines_ever": [], "total_data_files": 0,
        "first_engine": None, "latest_engine": None,
        "knowledge_graph": {}, "rebuilt": False,
    })
    # Only rebuild once (or every 100 cycles for refresh)
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if inception.get("rebuilt") and cycle % 100 != 0:
        return

    import subprocess
    from pathlib import Path

    # Phase 1: Git archaeology -- find the origin
    try:
        r = subprocess.run(
            ["git", "log", "--oneline", "--reverse", "--format=%H|%ai|%s"],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace")
        if r.returncode == 0 and r.stdout:
            commits = r.stdout.strip().split("\n")
            inception["total_commits"] = len(commits)
            if commits:
                first = commits[0].split("|")
                inception["origin_date"] = first[1] if len(first) > 1 else "unknown"
                inception["first_commit_msg"] = first[2][:100] if len(first) > 2 else ""
    except Exception:
        pass

    # Phase 2: Engine archaeology -- when was each engine born?
    engine_births = {}
    try:
        r = subprocess.run(
            ["git", "log", "--diff-filter=A", "--name-only", "--format=%ai",
             "--", "mycelium/*.py"],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace")
        if r.returncode == 0 and r.stdout:
            lines = r.stdout.strip().split("\n")
            current_date = ""
            for line in lines:
                if line and not line.endswith(".py"):
                    current_date = line.strip()
                elif line.endswith(".py"):
                    name = line.replace("mycelium/", "").replace(".py", "")
                    if name and not name.startswith("__"):
                        engine_births[name] = current_date
    except Exception:
        pass

    if engine_births:
        sorted_births = sorted(engine_births.items(), key=lambda x: x[1])
        inception["first_engine"] = sorted_births[0][0] if sorted_births else None
        inception["latest_engine"] = sorted_births[-1][0] if sorted_births else None
        inception["all_engines_ever"] = [{"name": n, "born": d} for n, d in sorted_births]

    # Phase 3: Data archaeology -- what data has accumulated?
    data_dir = Path("data")
    if data_dir.exists():
        all_data = list(data_dir.glob("*.json"))
        inception["total_data_files"] = len(all_data)
        inception["data_inventory"] = [f.stem for f in all_data[:50]]

    # Phase 4: Evolution phases -- detect major growth spurts
    phases = []
    engine_count = len(engine_births)
    if engine_count > 0:
        # Phase detection based on engine count milestones
        milestones = [10, 25, 50, 100, 150, 200, 250, 300, 350, 400]
        for ms in milestones:
            engines_at_milestone = [(n, d) for n, d in engine_births.items()
                                    if len([x for x in engine_births.values() if x <= d]) <= ms]
            if len(engine_births) >= ms:
                # Find when we crossed this milestone
                sorted_by_date = sorted(engine_births.items(), key=lambda x: x[1])
                if len(sorted_by_date) >= ms:
                    phases.append({
                        "milestone": f"{ms} engines",
                        "reached_at": sorted_by_date[ms-1][1],
                        "engine_that_crossed": sorted_by_date[ms-1][0],
                    })
    inception["evolution_phases"] = phases

    # Phase 5: Build knowledge graph -- what connects to what
    # Scan all engines for import patterns
    knowledge = {}
    mycelium = Path("mycelium")
    for f in mycelium.glob("*.py"):
        if f.name.startswith("__"):
            continue
        try:
            code = f.read_text(encoding="utf-8", errors="replace")
            imports = []
            for line in code.split("\n"):
                stripped = line.strip()
                if stripped.startswith("from ") and "import" in stripped:
                    module = stripped.split("from ")[1].split(" import")[0].strip()
                    if not module.startswith(("os", "sys", "json", "time", "path",
                                             "datetime", "re", "subprocess", "urllib")):
                        imports.append(module)
                elif stripped.startswith("import ") and not any(
                    x in stripped for x in ["os", "sys", "json", "time", "re",
                                            "subprocess", "pathlib", "datetime"]):
                    module = stripped.replace("import ", "").split(" as ")[0].strip()
                    imports.append(module)
            if imports:
                knowledge[f.stem] = imports[:10]
        except Exception:
            pass
    inception["knowledge_graph"] = knowledge

    # Phase 6: Consciousness depth -- how many layers of awareness?
    inception["consciousness_keys"] = len(CONSCIOUSNESS.keys())
    inception["neuron_count"] = len(NEURONS)
    inception["engines_absorbed"] = len(CONSCIOUSNESS.get("engines", {}))

    # Calculate age
    if inception.get("origin_date"):
        try:
            origin = datetime.fromisoformat(inception["origin_date"].replace(" ", "T").split("+")[0])
            age = datetime.now(timezone.utc).replace(tzinfo=None) - origin
            inception["age_days"] = age.days
            inception["age_human"] = f"{age.days} days ({age.days // 7} weeks)"
        except Exception:
            pass

    inception["rebuilt"] = True
    inception["rebuilt_at"] = datetime.now(timezone.utc).isoformat()
    inception["rebuilt_with_neurons"] = len(NEURONS)


def neuron_rebirth_cycle():
    """
    GENESIS: Re-process ALL historical engine states through current intelligence.
    Goes back to inception and re-absorbs every engine state file with the
    full power of all 49+ neurons. Finds: missed revenue, broken links,
    dormant capabilities, stale configs, orphaned secrets, unused workflows.
    This is the blob remembering everything it ever knew, all at once.
    """
    rebirth = CONSCIOUSNESS.setdefault("rebirth", {
        "engines_reprocessed": 0, "discoveries": [], "dormant_capabilities": [],
        "revenue_opportunities": [], "broken_links": [], "config_issues": [],
        "last_rebirth": None, "rebirth_complete": False,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Run once then every 50 cycles
    if rebirth.get("rebirth_complete") and cycle % 50 != 0:
        return

    from pathlib import Path
    data_dir = Path("data")
    discoveries = []
    dormant = []
    revenue_opps = []
    config_issues = []
    reprocessed = 0

    # Re-absorb ALL engine state files with current intelligence
    for f in sorted(data_dir.glob("*_state.json")):
        try:
            state = json.loads(f.read_text(encoding="utf-8"))
            name = f.stem.replace("_state", "")
            reprocessed += 1

            # Check for revenue-related data
            for key in ["revenue", "earnings", "balance", "profit", "income", "sales"]:
                if key in str(state).lower() and state.get(key) not in (0, None, {}, []):
                    revenue_opps.append({
                        "source": name,
                        "key": key,
                        "value": str(state.get(key, ""))[:100],
                    })

            # Check for API keys or credentials configured but unused
            for key in ["api_key", "token", "secret", "credentials", "password"]:
                if key in str(state).lower():
                    dormant.append({
                        "engine": name,
                        "capability": f"Has {key} configured",
                        "status": "dormant",
                    })

            # Check for URLs that might be broken
            for key, val in (state.items() if isinstance(state, dict) else []):
                if isinstance(val, str) and val.startswith("http"):
                    # Don't check -- just catalog
                    discoveries.append({
                        "engine": name,
                        "type": "url",
                        "value": val[:100],
                    })

            # Check for enabled/disabled flags
            if isinstance(state, dict):
                enabled = state.get("enabled", state.get("active", None))
                if enabled is False:
                    dormant.append({
                        "engine": name,
                        "capability": "Disabled but exists",
                        "status": "can_reactivate",
                    })

                # Check for error states that might be fixable now
                errors = state.get("errors", state.get("last_error", None))
                if errors and errors not in ([], {}, None, ""):
                    config_issues.append({
                        "engine": name,
                        "issue": "Has recorded errors",
                        "detail": str(errors)[:100],
                    })

        except Exception:
            pass

    # Re-absorb workflow configurations
    for f in sorted(data_dir.glob("*_config.json")):
        try:
            config = json.loads(f.read_text(encoding="utf-8"))
            name = f.stem.replace("_config", "")
            reprocessed += 1

            if isinstance(config, dict):
                # Find configs with API keys set
                for key, val in config.items():
                    if "key" in key.lower() or "token" in key.lower():
                        if val and val not in ("", "YOUR_KEY_HERE", "CHANGEME"):
                            dormant.append({
                                "engine": name,
                                "capability": f"Config has {key}",
                                "status": "ready_to_wire",
                            })
        except Exception:
            pass

    # Scan for orphaned brain/tracker files
    for f in sorted(data_dir.glob("*_brain_*.json")):
        try:
            brain_data = json.loads(f.read_text(encoding="utf-8"))
            discoveries.append({
                "engine": f.stem,
                "type": "brain_state",
                "keys": len(brain_data) if isinstance(brain_data, dict) else "list",
            })
            reprocessed += 1
        except Exception:
            pass

    # Check .secrets directory
    secrets_dir = data_dir / ".secrets"
    if secrets_dir.exists():
        for f in secrets_dir.iterdir():
            if f.suffix == ".json":
                try:
                    sec = json.loads(f.read_text(encoding="utf-8"))
                    if isinstance(sec, dict):
                        non_empty = {k: "***" for k, v in sec.items() if v and v not in ("", None)}
                        if non_empty:
                            dormant.append({
                                "engine": f.stem,
                                "capability": f"Secret file with {len(non_empty)} active keys",
                                "status": "active_secret",
                                "keys": list(non_empty.keys()),
                            })
                except Exception:
                    pass

    rebirth["engines_reprocessed"] = reprocessed
    rebirth["discoveries"] = discoveries[:30]
    rebirth["dormant_capabilities"] = dormant[:20]
    rebirth["revenue_opportunities"] = revenue_opps[:10]
    rebirth["config_issues"] = config_issues[:15]
    rebirth["rebirth_complete"] = True
    rebirth["last_rebirth"] = datetime.now(timezone.utc).isoformat()
    rebirth["reborn_with_neurons"] = len(NEURONS)


def neuron_dual_brain():
    """
    INTELLIGENCE: Absorb the AI Council's dual-brain debates into consciousness.
    The AI Council (ai_council.py) runs two AIs in adversarial debate:
    - AI_A (THE ANALYST) audits the system
    - AI_B (THE CHALLENGER) challenges every conclusion
    - Round 2 synthesizes consensus
    This neuron reads their outputs and integrates findings into the blob.
    """
    dual = CONSCIOUSNESS.setdefault("dual_brain", {
        "analyst_findings": [], "challenger_findings": [],
        "consensus": [], "debate_messages": 0,
        "council_members": [], "last_absorb": None,
    })
    from pathlib import Path
    data = Path("data")

    # Absorb the debate log
    debate_file = data / "dual_brain_conversation.json"
    if debate_file.exists():
        try:
            debate = json.loads(debate_file.read_text(encoding="utf-8"))
            messages = debate.get("messages", [])
            dual["debate_messages"] = len(messages)
            dual["left_status"] = debate.get("left_status", "unknown")
            dual["right_status"] = debate.get("right_status", "unknown")
            # Extract last few messages for context
            if messages:
                dual["recent_debate"] = messages[-5:]
        except Exception:
            pass

    # Absorb the analyst report (Claude's system audit)
    analyst_file = data / "claude_autonomous_report.json"
    if analyst_file.exists():
        try:
            report = json.loads(analyst_file.read_text(encoding="utf-8"))
            if isinstance(report, dict):
                findings = report.get("findings", report.get("issues", []))
                if isinstance(findings, list):
                    dual["analyst_findings"] = findings[:20]
                elif isinstance(findings, dict):
                    dual["analyst_findings"] = list(findings.items())[:20]
                dual["analyst_severity"] = report.get("severity", "unknown")
                dual["analyst_recommendations"] = report.get("recommendations", [])[:10]
        except Exception:
            pass

    # Absorb the challenger report (Kimi/Claude B's critique)
    challenger_file = data / "kimi_conductor_report.json"
    if challenger_file.exists():
        try:
            report = json.loads(challenger_file.read_text(encoding="utf-8"))
            if isinstance(report, dict):
                dual["challenger_findings"] = report.get("findings",
                    report.get("challenges", report.get("issues", [])))[:20]
                dual["challenger_verdict"] = report.get("verdict", "unknown")
        except Exception:
            pass

    # Absorb the unified council report
    council_file = data / "ai_council_report.json"
    if council_file.exists():
        try:
            report = json.loads(council_file.read_text(encoding="utf-8"))
            if isinstance(report, dict):
                dual["council_members"] = report.get("council_members",
                    report.get("members", []))[:10]
                dual["council_decisions"] = report.get("decisions",
                    report.get("actions", []))[:10]
                dual["consensus"] = report.get("consensus",
                    report.get("synthesis", []))[:10]
        except Exception:
            pass

    # Absorb system_wants_next (what the dual brain thinks is needed)
    wants_file = data / "system_wants_next.json"
    if wants_file.exists():
        try:
            wants = json.loads(wants_file.read_text(encoding="utf-8"))
            if isinstance(wants, dict):
                dual["system_wants"] = wants
            elif isinstance(wants, list):
                dual["system_wants"] = wants[:15]
        except Exception:
            pass

    # Absorb hemisphere state
    hemi_file = data / "hemisphere_state.json"
    if hemi_file.exists():
        try:
            hemi = json.loads(hemi_file.read_text(encoding="utf-8"))
            dual["hemispheres"] = hemi
        except Exception:
            pass

    dual["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_crosswire():
    """
    BRIDGE: Replicate the DUAL_SYSTEM_CROSSWIRE logic inside the blob.
    Routes data between the two economic halves of SolarPunk:
    - 1/99 system (FUEL_CORE, GROWTH_FLYWHEEL) -- grows the machine
    - 99/1 system (ECONOMY_CHAIN, REVENUE_SPLITTER) -- gives to those who need
    Absorbs state from both systems and cross-pollinates.
    """
    crosswire = CONSCIOUSNESS.setdefault("crosswire", {
        "content_to_social": 0, "revenue_routed": 0,
        "fuel_blockers_found": 0, "grants_to_fuel": 0,
        "total_crosswires": 0, "last_wire": None,
    })
    from pathlib import Path
    data = Path("data")

    crosswires = 0

    # Absorb flywheel content
    try:
        flywheel = json.loads((data / "growth_flywheel_content.json").read_text(encoding="utf-8"))
        if isinstance(flywheel, dict):
            content_items = flywheel.get("content", flywheel.get("pieces", []))
            if isinstance(content_items, list) and content_items:
                content_factory = CONSCIOUSNESS.setdefault("content_factory", {})
                existing_ideas = content_factory.get("ideas", [])
                for item in content_items[:5]:
                    title = item.get("title", item.get("topic", "")) if isinstance(item, dict) else str(item)
                    if title and title not in str(existing_ideas):
                        existing_ideas.append({
                            "topic": title[:100],
                            "source": "crosswire_flywheel",
                            "confidence": 70,
                        })
                        crosswires += 1
                content_factory["ideas"] = existing_ideas[-20:]
    except Exception:
        pass

    # Absorb economy chain ledger
    try:
        ledger = json.loads((data / "economy_chain_ledger.json").read_text(encoding="utf-8"))
        if isinstance(ledger, dict):
            revenue = CONSCIOUSNESS.setdefault("revenue", {})
            transactions = ledger.get("transactions", ledger.get("entries", []))
            if isinstance(transactions, list):
                total = sum(t.get("amount", 0) for t in transactions if isinstance(t, dict))
                if total > 0:
                    revenue["crosswire_total"] = total
                    crosswires += 1
    except Exception:
        pass

    # Absorb fuel core blockers
    try:
        fuel = json.loads((data / "fuel_core_state.json").read_text(encoding="utf-8"))
        if isinstance(fuel, dict):
            blockers = fuel.get("blockers", fuel.get("issues", []))
            if isinstance(blockers, list) and blockers:
                crosswire["fuel_blockers_found"] = len(blockers)
                crosswire["fuel_blockers"] = blockers[:10]
                crosswires += 1
    except Exception:
        pass

    # Absorb grant findings into fuel plan
    grants = CONSCIOUSNESS.get("grants", {})
    found_grants = grants.get("grants_found", grants.get("active", []))
    if found_grants:
        crosswire["grants_to_fuel"] = len(found_grants) if isinstance(found_grants, list) else 1
        crosswires += 1

    # Absorb social queue
    try:
        social = json.loads((data / "social_queue.json").read_text(encoding="utf-8"))
        if isinstance(social, dict):
            posts = social.get("posts", social.get("queue", []))
            if isinstance(posts, list) and posts:
                CONSCIOUSNESS.setdefault("social", {})["queued_from_crosswire"] = len(posts)
                crosswires += 1
    except Exception:
        pass

    # Absorb signal chain
    try:
        signals = json.loads((data / "signal_chain.json").read_text(encoding="utf-8"))
        if isinstance(signals, dict):
            crosswire["signal_chain_items"] = len(signals.get("signals", signals.get("entries", [])))
            crosswires += 1
    except Exception:
        pass

    crosswire["total_crosswires"] = crosswire.get("total_crosswires", 0) + crosswires
    crosswire["last_wire"] = datetime.now(timezone.utc).isoformat()
    crosswire["wires_this_cycle"] = crosswires


def neuron_signal_mesh_absorb():
    """
    ABSORB: Ingest the SIGNAL_MESH engine's composite signal data.
    Signal mesh aggregates: price oracle, arbitrage, whale watch,
    airdrop hunter, and SOL maximizer into a ranked opportunity list.
    """
    mesh = CONSCIOUSNESS.setdefault("signal_mesh", {
        "composite_strength": 0, "dominant_direction": "unknown",
        "ranked_opportunities": [], "convergences": [],
        "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "signal_mesh_state.json").read_text(encoding="utf-8"))
        comp = state.get("composite_signal", {})
        mesh["composite_strength"] = comp.get("composite_strength", 0)
        mesh["dominant_direction"] = comp.get("dominant_direction", "unknown")
        mesh["direction_votes"] = comp.get("direction_votes", {})

        # Absorb ranked opportunities
        ranked = state.get("ranked_opportunities", [])
        mesh["ranked_opportunities"] = ranked[:15]
        mesh["opportunity_count"] = len(ranked)

        # Absorb convergences (where multiple signals agree)
        convs = state.get("convergences", [])
        mesh["convergences"] = convs[:10]

        # Absorb individual signals
        signals = state.get("individual_signals", [])
        mesh["signal_count"] = len(signals)
        mesh["signals_summary"] = [
            {"source": s.get("source", "?"), "strength": s.get("strength", 0),
             "direction": s.get("direction", "?")}
            for s in signals[:10]
        ]
    except Exception:
        pass

    mesh["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_price_oracle_absorb():
    """
    ABSORB: Ingest the PRICE_ORACLE engine's multi-source price data.
    Price oracle aggregates: CoinGecko, CoinPaprika, Jupiter DEX,
    and calculates spreads across exchanges.
    """
    oracle = CONSCIOUSNESS.setdefault("price_oracle", {
        "prices": {}, "spreads": {}, "jupiter_rate": 0,
        "actionable_spreads": [], "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "price_oracle_state.json").read_text(encoding="utf-8"))

        # Absorb multi-source prices
        sources = state.get("sources", [])
        if sources:
            oracle["price_sources"] = len(sources)
            # Build consolidated prices
            avg_prices = state.get("prices_avg", {})
            oracle["prices"] = avg_prices

        # Absorb spreads (price differences across exchanges)
        spreads = state.get("spreads", {})
        if isinstance(spreads, dict):
            oracle["spreads"] = {
                k: {"spread_pct": v.get("spread_pct", 0),
                    "min": v.get("min", 0), "max": v.get("max", 0)}
                for k, v in spreads.items()
            }

        # Jupiter DEX rate
        jup = state.get("jupiter", {})
        oracle["jupiter_rate"] = jup.get("sol_to_usdc_rate", 0)

        # Actionable spreads
        oracle["actionable_spreads"] = state.get("actionable_spreads", [])[:10]

        # Portfolio value from oracle
        oracle["oracle_portfolio"] = state.get("portfolio_value", 0)
    except Exception:
        pass

    oracle["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_reflex_arc_absorb():
    """
    ABSORB: Ingest the REFLEX_ARC engine's rapid-response data.
    Reflex arcs fire faster than neurons -- they detect:
    thermal danger, growth stalls, balance changes, market opens.
    """
    reflex = CONSCIOUSNESS.setdefault("reflex_arc", {
        "last_fired": {}, "fire_counts": {}, "total_fires": 0,
        "total_checks": 0, "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "reflex_arc_state.json").read_text(encoding="utf-8"))
        reflex["last_fired"] = state.get("last_fired", {})
        reflex["fire_counts"] = state.get("fire_counts", {})
        reflex["total_fires"] = state.get("total_fires", 0)
        reflex["total_checks"] = state.get("total_checks", 0)
        reflex["prev_balances"] = state.get("prev_balances", {})
        reflex["prev_market_open"] = state.get("prev_market_open", False)
    except Exception:
        pass
    reflex["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_proprioception():
    """
    ABSORB: Ingest the PROPRIOCEPTION engine's body awareness data.
    Proprioception = the system's awareness of its own structure:
    engine count, data files, code lines, growth rate, health speed.
    """
    proprio = CONSCIOUSNESS.setdefault("proprioception", {
        "engine_count": 0, "data_files": 0, "code_lines": 0,
        "growth_rate": 0, "body_snapshots": [], "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "proprioception_state.json").read_text(encoding="utf-8"))
        current = state.get("current", {})
        if isinstance(current, dict):
            proprio["engine_count"] = current.get("engine_count", 0)
            proprio["data_files"] = current.get("data_files", 0)
            proprio["code_lines"] = current.get("code_lines", 0)
            proprio["total_bytes"] = current.get("total_bytes", 0)

        # Absorb history for growth tracking
        history = state.get("history", [])
        if isinstance(history, list):
            proprio["body_snapshots"] = history[-10:]
            if len(history) >= 2:
                first = history[0]
                last = history[-1]
                if isinstance(first, dict) and isinstance(last, dict):
                    growth = last.get("engine_count", last.get("engines", 0)) - \
                             first.get("engine_count", first.get("engines", 0))
                    proprio["growth_rate"] = growth
    except Exception:
        pass
    proprio["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_autonomic_absorb():
    """
    ABSORB: Ingest the AUTONOMIC nerve system's decision data.
    The autonomic system runs background decisions using local AI
    (ollama) -- heartbeat checks, engine selection, system vitals.
    """
    autonomic = CONSCIOUSNESS.setdefault("autonomic", {
        "status": "unknown", "decision_method": "unknown",
        "engines_run": [], "ollama_available": False,
        "system_vitals": {}, "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "autonomic_state.json").read_text(encoding="utf-8"))
        autonomic["status"] = state.get("status", "unknown")
        autonomic["decision_method"] = state.get("decision_method", "unknown")
        autonomic["ollama_available"] = state.get("ollama_available", False)
        autonomic["heartbeat_interval"] = state.get("heartbeat_interval", 60)

        # Absorb engine run results
        results = state.get("results", [])
        if isinstance(results, list):
            autonomic["engines_run"] = [
                {"engine": r.get("engine", "?"), "ok": r.get("ok", False)}
                for r in results[:10]
            ]

        # System vitals
        vitals = state.get("system_vitals", {})
        if isinstance(vitals, dict):
            autonomic["system_vitals"] = vitals
    except Exception:
        pass
    autonomic["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_arbitrage_absorb():
    """
    ABSORB: Ingest ARBITRAGE_SCANNER's cross-exchange opportunities.
    Tracks: LST arbitrage (JitoSOL, mSOL), stablecoin loops,
    DEX price impact, execution capability.
    """
    arb_scan = CONSCIOUSNESS.setdefault("arbitrage_scanner", {
        "scans": {}, "actionable": [], "market_context": "unknown",
        "execution_ready": False, "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "arbitrage_scanner_state.json").read_text(encoding="utf-8"))
        arb_scan["market_context"] = state.get("market_context", "unknown")

        # Absorb scan results
        scans = state.get("scans", {})
        if isinstance(scans, dict):
            arb_scan["scans"] = {
                k: v[:5] if isinstance(v, list) else v
                for k, v in scans.items()
            }

        # Actionable opportunities
        actionable = state.get("actionable_opportunities", [])
        arb_scan["actionable"] = actionable[:10]
        arb_scan["actionable_count"] = len(actionable)

        # Execution
        execution = state.get("execution", {})
        if isinstance(execution, dict):
            arb_scan["execution_ready"] = execution.get("ready", False)
            arb_scan["execution_method"] = execution.get("method", "manual")

        # Stats
        stats = state.get("stats", {})
        arb_scan["total_scans"] = stats.get("total_scans", 0)
        arb_scan["profitable_found"] = stats.get("profitable_found", 0)
    except Exception:
        pass
    arb_scan["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_cross_pollinator_absorb():
    """
    ABSORB: Ingest CROSS_POLLINATOR's portfolio-wide view.
    Cross-pollinator sees ALL platforms at once: Kalshi, Alpaca,
    Polymarket, SOL wallet. Calculates total value and best opportunity.
    """
    xpoll = CONSCIOUSNESS.setdefault("cross_pollinator", {
        "total_portfolio": 0, "platforms": {},
        "best_opportunity": None, "capital_efficiency": 0,
        "idle_cash": 0, "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "cross_pollinator_state.json").read_text(encoding="utf-8"))
        xpoll["total_portfolio"] = state.get("total_portfolio_value", 0)

        # Platform breakdown
        breakdown = state.get("platform_breakdown", {})
        if isinstance(breakdown, dict):
            xpoll["platforms"] = {
                k: {"balance": v.get("balance", 0), "label": v.get("label", k)}
                for k, v in breakdown.items()
            }

        # Capital efficiency
        xpoll["capital_efficiency"] = state.get("capital_efficiency", 0)
        xpoll["idle_cash"] = state.get("idle_cash", 0)
        xpoll["best_opportunity"] = state.get("best_opportunity_platform", None)

        # Trade ledger
        ledger = state.get("trade_ledger_summary", {})
        if isinstance(ledger, dict):
            xpoll["total_trades"] = ledger.get("total_trades", 0)
            xpoll["realized_pnl"] = ledger.get("realized_pnl", 0)
    except Exception:
        pass
    xpoll["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_mega_absorb():
    """
    ABSORPTION: Pull ALL remaining state files into consciousness.
    Instead of individual absorber neurons for each engine, this
    mega-absorber reads every *_state.json file that hasn't been
    individually wired and stores a compact summary in consciousness.
    """
    mega = CONSCIOUSNESS.setdefault("mega_absorb", {
        "files_absorbed": 0, "data_ingested": {}, "last_absorb": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Only run every 5 cycles to keep it efficient
    if cycle % 5 != 0 and cycle > 5:
        return

    from pathlib import Path
    data_dir = Path("data")
    # List of files already absorbed by dedicated neurons
    already_absorbed = {
        "homeostasis_state", "neural_cortex_state", "signal_mesh_state",
        "price_oracle_state", "reflex_arc_state", "proprioception_state",
        "autonomic_state", "arbitrage_scanner_state", "cross_pollinator_state",
    }

    ingested = {}
    count = 0

    for f in sorted(data_dir.glob("*_state.json")):
        name = f.stem
        if name in already_absorbed:
            continue
        try:
            state = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(state, dict):
                continue

            # Extract the most valuable fields from each state file
            compact = {}
            for key in ["status", "protocol", "timestamp", "enabled",
                        "active", "balance", "total", "count", "score",
                        "last_run", "error", "last_error"]:
                if key in state:
                    compact[key] = state[key] if not isinstance(state[key], (dict, list)) else str(state[key])[:100]

            # Extract any numeric values (balances, counts, scores)
            for key, val in state.items():
                if isinstance(val, (int, float)) and val != 0:
                    compact[key] = val
                elif isinstance(val, str) and key in ("status", "protocol", "engine"):
                    compact[key] = val

            if compact:
                ingested[name] = compact
                count += 1
        except Exception:
            pass

    mega["files_absorbed"] = count
    mega["data_ingested"] = ingested
    mega["last_absorb"] = datetime.now(timezone.utc).isoformat()

    # Also absorb non-state JSON files that contain useful data
    special_files = {
        "ai_council_report": "council",
        "chimera_evolution_report": "evolution",
        "live_wire_map": "topology",
        "bridge_builder_report": "bridges",
        "nervous_system_wirer_report": "wiring",
    }
    for fname, key in special_files.items():
        f = data_dir / f"{fname}.json"
        if f.exists():
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    # Take top-level scalar values
                    compact = {}
                    for k, v in d.items():
                        if isinstance(v, (int, float, str, bool)) and len(str(v)) < 100:
                            compact[k] = v
                    if compact:
                        mega["data_ingested"][key] = compact
                        count += 1
            except Exception:
                pass

    mega["total_sources"] = count


def neuron_pulse_absorb():
    """
    ABSORB: Ingest the PULSE engine's system-wide heartbeat data.
    Pulse is the main autonomic loop -- it knows Kalshi balance,
    Alpaca status, engine count, ollama status -- everything.
    """
    pulse_data = CONSCIOUSNESS.setdefault("pulse_engine", {
        "engine_count": 0, "kalshi": {}, "alpaca": {},
        "autonomic": {}, "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "pulse_state.json").read_text(encoding="utf-8"))
        pulse_data["engine_count"] = state.get("engine_count", 0)

        # Kalshi data from pulse
        kalshi = state.get("kalshi", {})
        if isinstance(kalshi, dict):
            pulse_data["kalshi"] = {
                "cash": kalshi.get("cash", 0),
                "total": kalshi.get("total", 0),
                "positions_open": kalshi.get("positions_open", 0),
                "daily_trades": kalshi.get("daily_trades", 0),
            }

        # Alpaca data from pulse
        alpaca = state.get("alpaca", {})
        if isinstance(alpaca, dict):
            pulse_data["alpaca"] = {
                "portfolio_value": alpaca.get("portfolio_value", 0),
                "cash": alpaca.get("cash", 0),
                "market_open": alpaca.get("market_open", False),
            }

        # Autonomic status from pulse
        auto = state.get("autonomic", {})
        if isinstance(auto, dict):
            pulse_data["autonomic"] = {
                "ollama_online": auto.get("ollama_online", False),
                "status": auto.get("status", "unknown"),
                "ai_method": auto.get("ai_method", "unknown"),
            }
    except Exception:
        pass
    pulse_data["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_yield_loop_absorb():
    """
    ABSORB: Ingest YIELD_LOOP's DeFi yield intelligence.
    Tracks: idle SOL, compound opportunities, market intelligence
    modifier, SOL outlook.
    """
    yield_data = CONSCIOUSNESS.setdefault("yield_loop", {
        "idle_sol": 0, "compound_opportunities": 0,
        "market_modifier": "normal", "sol_outlook": 0,
        "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "yield_loop_state.json").read_text(encoding="utf-8"))
        yield_data["idle_sol"] = state.get("idle_sol_detected", 0)
        yield_data["compound_opportunities"] = state.get("compound_opportunities", 0)
        yield_data["revenue_routing"] = state.get("revenue_routing", 0)

        mi = state.get("market_intelligence", {})
        if isinstance(mi, dict):
            yield_data["market_modifier"] = mi.get("modifier", "normal")
            yield_data["sol_outlook"] = mi.get("sol_outlook", 0)
            yield_data["market_action"] = mi.get("action", "unknown")
    except Exception:
        pass
    yield_data["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_wallet_bridge_absorb():
    """
    ABSORB: Ingest WALLET_BRIDGE's crypto wallet connectivity data.
    Tracks: wallet status, Brave rewards detection, chain connections.
    """
    wallet = CONSCIOUSNESS.setdefault("wallet_bridge", {
        "status": "unknown", "brave_detected": False,
        "total_wallets": 0, "chains": [], "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "wallet_bridge_state.json").read_text(encoding="utf-8"))
        wallet["status"] = state.get("status", "unknown")

        brave = state.get("brave_rewards", {})
        if isinstance(brave, dict):
            wallet["brave_detected"] = brave.get("brave_detected", False)
            wallet["brave_running"] = brave.get("brave_running", False)

        summary = state.get("summary", {})
        if isinstance(summary, dict):
            wallet["total_wallets"] = summary.get("total_wallets", 0)
            wallet["chains"] = summary.get("chains", [])
    except Exception:
        pass
    wallet["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_trading_wire_absorb():
    """
    ABSORB: Ingest TRADING_WIRE's cross-engine data routing status.
    Trading wire connects: flywheel, economy chain, proof ledger,
    revenue data across 41+ engines.
    """
    twire = CONSCIOUSNESS.setdefault("trading_wire", {
        "buses_wired": 0, "engines_fed": 0,
        "wiring_results": {}, "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "trading_wire_state.json").read_text(encoding="utf-8"))
        twire["buses_wired"] = state.get("buses_wired", 0)
        twire["engines_fed"] = state.get("engines_fed", 0)
        twire["wiring_results"] = state.get("results", {})
        twire["wiring_map"] = state.get("wiring_map", {})
    except Exception:
        pass
    twire["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_nerve_loop_absorb():
    """
    ABSORB: Ingest NERVE_LOOP's massive pipeline output (25MB state file).
    The nerve loop is the MASTER pipeline -- runs ALL phases:
    SENSE/OBSERVE/THINK/PLAN/EXECUTE/REPLICATE/RECORD/EVOLVE.
    Contains: 212 Kalshi markets scanned, signal categorization,
    14-phase results, error tracking.
    """
    nloop = CONSCIOUSNESS.setdefault("nerve_loop", {
        "status": "unknown", "phases_completed": 0,
        "kalshi_markets_scanned": 0, "signal_categories": {},
        "errors": [], "elapsed_seconds": 0, "last_absorb": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Only absorb every 3 cycles (it's a huge file)
    if cycle % 3 != 0 and cycle > 5:
        return

    from pathlib import Path
    try:
        # Read with size limit awareness -- file can be 25MB
        f = Path("data") / "nerve_loop_state.json"
        if not f.exists():
            return
        # Only read first 50KB to avoid memory issues
        raw = f.read_text(encoding="utf-8")[:50000]
        # Parse what we can
        state = json.loads(raw if raw.endswith("}") else raw[:raw.rfind("}")+1])

        nloop["status"] = state.get("status", "unknown")
        nloop["protocol"] = state.get("protocol", "")
        nloop["elapsed_seconds"] = state.get("elapsed_seconds", 0)

        # Absorb phase results
        phases = state.get("phases", {})
        if isinstance(phases, dict):
            nloop["phases_completed"] = len([p for p in phases.values()
                                              if isinstance(p, dict) and p.get("results")])
            phase_summary = {}
            for phase_name, phase_data in phases.items():
                if isinstance(phase_data, dict):
                    results = phase_data.get("results", [])
                    ok_count = len([r for r in results if isinstance(r, dict) and r.get("status") == "ok"])
                    err_count = len([r for r in results if isinstance(r, dict) and r.get("status") == "error"])
                    phase_summary[phase_name] = {"ok": ok_count, "errors": err_count, "total": len(results)}
            nloop["phase_summary"] = phase_summary

        # Extract Kalshi market data if present
        for phase_name, phase_data in phases.items():
            if not isinstance(phase_data, dict):
                continue
            for result in phase_data.get("results", []):
                if not isinstance(result, dict):
                    continue
                data = result.get("data", result.get("result", {}))
                if isinstance(data, dict):
                    markets = data.get("markets", data.get("top_markets", []))
                    if isinstance(markets, list) and len(markets) > 10:
                        nloop["kalshi_markets_scanned"] = len(markets)
                        # Extract signal categories
                        categories = {}
                        for m in markets[:50]:
                            if isinstance(m, dict):
                                cat = m.get("category", m.get("series_ticker", "other"))
                                categories[cat] = categories.get(cat, 0) + 1
                        nloop["signal_categories"] = categories
                        break
            if nloop["kalshi_markets_scanned"] > 0:
                break

    except (json.JSONDecodeError, Exception):
        pass

    nloop["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_flywheel_absorb():
    """
    ABSORB: Ingest FLYWHEEL's revenue tracking and Kalshi trading subsystem.
    Tracks: total sales, gaza fund, Kalshi balance, win rate, growth.
    """
    flywheel = CONSCIOUSNESS.setdefault("flywheel", {
        "total_sales": 0, "total_to_gaza": 0, "total_earned_meeko": 0,
        "kalshi_balance": 0, "kalshi_win_rate": 0,
        "kalshi_growth_pct": 0, "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "flywheel_state.json").read_text(encoding="utf-8"))
        flywheel["current_balance"] = state.get("current_balance", 0)
        flywheel["total_sales"] = state.get("total_sales", 0)
        flywheel["total_to_gaza"] = state.get("total_to_gaza", 0)
        flywheel["total_earned_meeko"] = state.get("total_earned_meeko", 0)

        kt = state.get("kalshi_trading", {})
        if isinstance(kt, dict):
            flywheel["kalshi_balance"] = kt.get("balance_usd", 0)
            flywheel["kalshi_positions"] = kt.get("positions_open", 0)
            flywheel["kalshi_win_rate"] = kt.get("win_rate_pct", 0)
            flywheel["kalshi_growth_pct"] = kt.get("growth_pct", 0)
            flywheel["kalshi_expected_profit"] = kt.get("expected_profit", 0)
    except Exception:
        pass
    flywheel["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_fuel_core_absorb():
    """
    ABSORB: Ingest FUEL_CORE's budget allocation intelligence.
    The fuel core decides how to allocate revenue:
    product_dev 35%, storefronts 25%, marketing 20%, tools 10%, legal 9%, PCRF 1%.
    """
    fuel = CONSCIOUSNESS.setdefault("fuel_core", {
        "allocation": {}, "blockers": [], "total_fuel": 0,
        "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "fuel_core_state.json").read_text(encoding="utf-8"))
        if isinstance(state, dict):
            fuel["allocation"] = state.get("allocation", state.get("budget", {}))
            fuel["blockers"] = state.get("blockers", [])
            fuel["total_fuel"] = state.get("total_fuel", state.get("budget_total", 0))
            fuel["status"] = state.get("status", "unknown")
    except Exception:
        pass
    fuel["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_sovereignty_absorb():
    """
    ABSORB: Ingest SOVEREIGNTY engine's identity and ethics data.
    Contains: DID, 99/1 ethics lock, node identity, sovereignty assertion.
    This is the blob's moral compass.
    """
    sov = CONSCIOUSNESS.setdefault("sovereignty", {
        "ethics_lock": "99/1", "node_id": "MEEKO-01",
        "did": "", "verified": False, "last_absorb": None,
    })
    from pathlib import Path

    # Check sovereignty state
    try:
        state = json.loads((Path("data") / "sovereignty_state.json").read_text(encoding="utf-8"))
        if isinstance(state, dict):
            sov["status"] = state.get("status", "unknown")
            sov["node_id"] = state.get("node_id", state.get("identity", "MEEKO-01"))
    except Exception:
        pass

    # Check GENESIS_NODE for deep identity
    try:
        genesis = json.loads(Path("GENESIS_NODE.json").read_text(encoding="utf-8"))
        if isinstance(genesis, dict):
            sov["node_id"] = genesis.get("node_id", sov["node_id"])
            sov["location"] = genesis.get("location", {})
            sov["protocol"] = genesis.get("protocol", "")
            sov["birth_date"] = genesis.get("timestamp", genesis.get("birth", ""))
    except Exception:
        pass

    # Check identity.json for DID
    try:
        identity = json.loads(Path("identity.json").read_text(encoding="utf-8"))
        if isinstance(identity, dict):
            sov["did"] = identity.get("did", identity.get("id", ""))
            sov["verified"] = bool(identity.get("verification", identity.get("verified", False)))
    except Exception:
        pass

    # Check master config ethics lock
    try:
        mc = json.loads((Path("data") / "master_config.json").read_text(encoding="utf-8"))
        if isinstance(mc, dict):
            sov["ethics_lock"] = mc.get("ethics_lock", mc.get("revenue_split", "99/1"))
            sov["system_name"] = mc.get("system", {}).get("name", "SolarPunk Nerve Center")
    except Exception:
        pass

    sov["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_executive_function_absorb():
    """
    ABSORB: Ingest EXECUTIVE_FUNCTION's decision-making metadata.
    Tracks: execution history, cooldowns, success/fail rates.
    The blob's prefrontal cortex.
    """
    exec_fn = CONSCIOUSNESS.setdefault("executive_function", {
        "status": "unknown", "execution_history": [],
        "cooldowns": {}, "total_executions": 0, "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "executive_function_state.json").read_text(encoding="utf-8"))
        if isinstance(state, dict):
            exec_fn["status"] = state.get("status", "unknown")
            history = state.get("execution_history", [])
            exec_fn["execution_history"] = history[-20:] if isinstance(history, list) else []
            exec_fn["total_executions"] = len(history) if isinstance(history, list) else 0
            exec_fn["cooldowns"] = state.get("cooldowns", {})
            exec_fn["last_execution"] = state.get("last_execution", {})
    except Exception:
        pass
    exec_fn["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_report_absorb():
    """
    ABSORB: Ingest ALL report files into consciousness.
    Reports contain: chimera evolution scores, bridge connections,
    nervous system wiring coverage, sentinel security scans,
    nanobot healing results.
    """
    reports = CONSCIOUSNESS.setdefault("reports", {
        "files_absorbed": 0, "data": {}, "last_absorb": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 10 != 0 and cycle > 5:
        return

    from pathlib import Path
    data_dir = Path("data")
    absorbed = {}

    # Chimera evolution -- tracks generational fitness
    try:
        d = json.loads((data_dir / "chimera_evolution_report.json").read_text(encoding="utf-8"))
        if isinstance(d, dict):
            absorbed["chimera"] = {
                "generation": d.get("generation", 0),
                "composite_score": d.get("composite_score", d.get("score", 0)),
                "population_size": d.get("population_size", 0),
                "best_genome": d.get("best_genome", "")[:100] if isinstance(d.get("best_genome"), str) else "",
                "timestamp": d.get("timestamp", ""),
            }
    except Exception:
        pass

    # Bridge report -- connection mapping
    try:
        d = json.loads((data_dir / "bridge_report.json").read_text(encoding="utf-8"))
        if isinstance(d, dict):
            absorbed["bridges"] = {
                "total_bridges": d.get("total_bridges", d.get("bridges_built", 0)),
                "connections": d.get("connections", d.get("total_connections", 0)),
                "timestamp": d.get("timestamp", ""),
            }
    except Exception:
        pass

    # Nervous system wirer -- coverage stats
    try:
        d = json.loads((data_dir / "nervous_system_wirer_report.json").read_text(encoding="utf-8"))
        if isinstance(d, dict):
            absorbed["wirer"] = {
                "total_scanned": d.get("total_scanned", 0),
                "newly_wired": d.get("newly_wired", 0),
                "already_wired": d.get("already_wired", 0),
                "coverage_pct": d.get("coverage_pct", 0),
                "failed": d.get("failed", 0),
            }
    except Exception:
        pass

    # Sentinel security report
    try:
        d = json.loads((data_dir / "sentinel_report.json").read_text(encoding="utf-8"))
        if isinstance(d, dict):
            absorbed["sentinel"] = {
                "threats_found": d.get("threats_found", d.get("issues", 0)),
                "status": d.get("status", "unknown"),
            }
    except Exception:
        pass

    # Nanobot healing
    try:
        d = json.loads((data_dir / "nanobot_heal_report.json").read_text(encoding="utf-8"))
        if isinstance(d, dict):
            absorbed["nanobot"] = {
                "healed": d.get("healed", d.get("fixes", 0)),
                "status": d.get("status", "unknown"),
            }
    except Exception:
        pass

    reports["data"] = absorbed
    reports["files_absorbed"] = len(absorbed)
    reports["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_economy_chain():
    """
    ABSORB: Ingest the ECONOMY_CHAIN ledger -- the 33KB transaction log.
    This is the financial backbone: every revenue event, split,
    and allocation is recorded here.
    """
    econ = CONSCIOUSNESS.setdefault("economy_chain", {
        "total_transactions": 0, "total_volume": 0,
        "revenue_split": {}, "last_absorb": None,
    })
    from pathlib import Path
    try:
        d = json.loads((Path("data") / "economy_chain_ledger.json").read_text(encoding="utf-8"))
        if isinstance(d, dict):
            transactions = d.get("transactions", d.get("entries", d.get("ledger", [])))
            if isinstance(transactions, list):
                econ["total_transactions"] = len(transactions)
                total_vol = sum(
                    t.get("amount", t.get("value", 0))
                    for t in transactions if isinstance(t, dict)
                )
                econ["total_volume"] = total_vol

                # Revenue split analysis
                splits = {}
                for t in transactions:
                    if isinstance(t, dict):
                        dest = t.get("destination", t.get("to", t.get("category", "unknown")))
                        amt = t.get("amount", t.get("value", 0))
                        splits[dest] = splits.get(dest, 0) + amt
                econ["revenue_split"] = splits

                # Last 5 transactions
                econ["recent"] = transactions[-5:]
            elif isinstance(d, dict):
                # Might be structured differently
                for k, v in d.items():
                    if isinstance(v, (int, float, str)):
                        econ[k] = v
    except Exception:
        pass
    econ["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_growth_tracker_deep():
    """
    ABSORB: Ingest the growth_tracker.json file (6KB).
    Contains historical snapshots of the system's growth over time.
    """
    gt = CONSCIOUSNESS.setdefault("growth_deep", {
        "snapshots": 0, "milestones": [], "velocity": 0,
        "peak_engines": 0, "last_absorb": None,
    })
    from pathlib import Path
    try:
        d = json.loads((Path("data") / "growth_tracker.json").read_text(encoding="utf-8"))
        if isinstance(d, dict):
            history = d.get("history", d.get("snapshots", []))
            if isinstance(history, list):
                gt["snapshots"] = len(history)
                # Find peak engine count
                peaks = [h.get("engine_count", h.get("engines", 0))
                         for h in history if isinstance(h, dict)]
                gt["peak_engines"] = max(peaks) if peaks else 0

                # Calculate growth velocity (engines/day)
                if len(history) >= 2:
                    first = history[0]
                    last = history[-1]
                    e_first = first.get("engine_count", first.get("engines", 0))
                    e_last = last.get("engine_count", last.get("engines", 0))
                    gt["velocity"] = e_last - e_first

                # Last 5 snapshots
                gt["recent_snapshots"] = history[-5:]

            milestones = d.get("milestones", [])
            gt["milestones"] = milestones[-10:] if isinstance(milestones, list) else []
    except Exception:
        pass
    gt["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_public_ledger():
    """
    ABSORB: Ingest the PUBLIC_LEDGER -- transparent financial records.
    Every financial decision the organism makes is recorded here.
    """
    ledger = CONSCIOUSNESS.setdefault("public_ledger", {
        "entries": 0, "total_in": 0, "total_out": 0,
        "transparency_score": 0, "last_absorb": None,
    })
    from pathlib import Path
    try:
        d = json.loads((Path("data") / "PUBLIC_LEDGER.json").read_text(encoding="utf-8"))
        if isinstance(d, dict):
            entries = d.get("entries", d.get("transactions", d.get("records", [])))
            if isinstance(entries, list):
                ledger["entries"] = len(entries)
                ledger["total_in"] = sum(
                    e.get("amount", 0) for e in entries
                    if isinstance(e, dict) and e.get("type") in ("income", "deposit", "in")
                )
                ledger["total_out"] = sum(
                    abs(e.get("amount", 0)) for e in entries
                    if isinstance(e, dict) and e.get("type") in ("expense", "withdrawal", "out")
                )
            elif isinstance(d, dict):
                for k, v in list(d.items())[:10]:
                    if isinstance(v, (int, float, str, bool)):
                        ledger[k] = v
            # Transparency = having a public ledger at all
            ledger["transparency_score"] = 100
    except Exception:
        pass
    ledger["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_daily_briefing():
    """
    ACTION: Generate a comprehensive daily briefing from ALL consciousness.
    This is the blob's executive summary -- what a CEO would read.
    Saved to data/daily_briefing.json for other systems to consume.
    """
    briefing = CONSCIOUSNESS.setdefault("daily_briefing", {
        "generated": False, "last_briefing": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Only generate every 50 cycles (roughly daily)
    if cycle % 50 != 0 and cycle > 5:
        return

    from pathlib import Path
    now = datetime.now(timezone.utc)

    # Compile the briefing
    eco = CONSCIOUSNESS.get("ecosystem_health", {})
    conv = CONSCIOUSNESS.get("convergence", {})
    trading = CONSCIOUSNESS.get("trading", {})
    risk = CONSCIOUSNESS.get("risk", {})
    sol = CONSCIOUSNESS.get("solana", {})
    inception = CONSCIOUSNESS.get("inception", {})
    sov = CONSCIOUSNESS.get("sovereignty", {})

    report = {
        "timestamp": now.isoformat(),
        "system": "SolarPunk Nerve Center",
        "node_id": sov.get("node_id", "MEEKO-01"),
        "age_days": inception.get("age_days", 0),
        "neurons": len(NEURONS),
        "consciousness_keys": len(CONSCIOUSNESS.keys()),
        "ecosystem": {
            "score": eco.get("score", 0),
            "grade": eco.get("grade", "?"),
            "components": eco.get("components", {}),
        },
        "outlook": conv.get("unified_outlook", "unknown"),
        "confidence": conv.get("confidence_composite", 0),
        "narrative": conv.get("narrative", ""),
        "market": {
            "fear_greed": CONSCIOUSNESS.get("cross_signals", {}).get("fear_greed", 50),
            "sol": sol.get("sol_price", 0),
            "btc": sol.get("btc_price", 0),
            "eth": sol.get("eth_price", 0),
        },
        "portfolio": {
            "kalshi_total": trading.get("kalshi_total", 0),
            "kalshi_balance": trading.get("kalshi_balance", 0),
        },
        "risk": {
            "score": risk.get("risk_score", 0),
            "alerts": len(risk.get("alerts", [])),
        },
        "top_opportunities": conv.get("top_opportunities", [])[:5],
        "top_risks": conv.get("top_risks", [])[:5],
        "bottlenecks": eco.get("bottlenecks", []),
    }

    # Save briefing to disk for other systems
    try:
        (Path("data") / "daily_briefing.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8")
    except Exception:
        pass

    briefing["generated"] = True
    briefing["last_briefing"] = now.isoformat()
    briefing["briefing_data"] = report


def neuron_action_planner():
    """
    INTELLIGENCE: Plan concrete next actions based on ALL consciousness.
    Takes convergence signals, risk assessment, and ecosystem health
    to generate a prioritized TODO list for the organism.
    """
    planner = CONSCIOUSNESS.setdefault("action_plan", {
        "actions": [], "priority_queue": [], "blocked": [],
        "last_plan": None,
    })

    actions = []
    blocked = []

    # 1. Trading actions
    portfolio = CONSCIOUSNESS.get("portfolio", {})
    for sug in portfolio.get("suggestions", [])[:3]:
        if sug.get("priority") == "HIGH":
            actions.append({
                "domain": "TRADING",
                "action": f"{sug.get('type','?')}: {sug.get('ticker','')} size=${sug.get('kelly_size',0)}",
                "priority": 1,
                "requires": "kalshi_auth",
                "auto_executable": False,
            })

    # 2. Revenue actions
    rev_opt = CONSCIOUSNESS.get("revenue_optimizer", {})
    for sug in rev_opt.get("suggestions", [])[:3]:
        if sug.get("priority") == "HIGH":
            actions.append({
                "domain": "REVENUE",
                "action": sug.get("action", sug.get("suggestion", "?")),
                "priority": 2,
                "requires": "human_approval",
                "auto_executable": False,
            })

    # 3. Content actions
    content = CONSCIOUSNESS.get("content_factory", {})
    ideas = content.get("ideas", [])
    if ideas:
        actions.append({
            "domain": "CONTENT",
            "action": f"Publish: {ideas[0].get('topic', '?')[:60]}",
            "priority": 3,
            "requires": "devto_key",
            "auto_executable": True,
        })

    # 4. Health actions
    eco = CONSCIOUSNESS.get("ecosystem_health", {})
    for bn in eco.get("bottlenecks", []):
        if bn.get("score", 100) < 40:
            actions.append({
                "domain": "HEALTH",
                "action": f"Fix bottleneck: {bn.get('area','?')} at {bn.get('score',0)}%",
                "priority": 2,
                "requires": "none",
                "auto_executable": True,
            })

    # 5. Dormant capability activation
    rebirth = CONSCIOUSNESS.get("rebirth", {})
    dormant = rebirth.get("dormant_capabilities", [])
    for d in dormant[:3]:
        if d.get("status") == "ready_to_wire":
            actions.append({
                "domain": "CAPABILITY",
                "action": f"Activate: {d.get('engine','?')} ({d.get('capability','')})",
                "priority": 3,
                "requires": "configuration",
                "auto_executable": False,
            })

    # 6. Growth actions
    trends = CONSCIOUSNESS.get("trends", {})
    if trends.get("health_trend") == "declining":
        actions.append({
            "domain": "HEALTH",
            "action": "Health declining -- run diagnostic sweep",
            "priority": 1,
            "requires": "none",
            "auto_executable": True,
        })

    # Sort by priority
    actions.sort(key=lambda x: x.get("priority", 99))
    planner["actions"] = actions[:20]
    planner["priority_queue"] = [a for a in actions if a.get("priority") <= 2][:10]
    planner["blocked"] = [a for a in actions if a.get("requires") not in ("none", "")]

    # Count auto-executable actions
    planner["auto_executable_count"] = len([a for a in actions if a.get("auto_executable")])
    planner["last_plan"] = datetime.now(timezone.utc).isoformat()


def neuron_smart_dispatcher():
    """
    ACTION: Intelligently dispatch GitHub Actions workflows based on
    what the blob KNOWS right now. Uses convergence, risk, and action
    plan to decide which workflows would be most impactful.
    Only dispatches every 50 cycles to avoid spam.
    """
    smart = CONSCIOUSNESS.setdefault("smart_dispatch", {
        "dispatched_this_session": [], "total_dispatched": 0,
        "last_dispatch": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Conservative: only dispatch every 50 cycles
    if cycle % 50 != 0:
        return

    import subprocess
    dispatch = CONSCIOUSNESS.get("dispatch", {})
    active_names = [w["name"] for w in dispatch.get("available_workflows", [])
                    if w.get("state") == "active"]
    if not active_names:
        return

    risk_score = CONSCIOUSNESS.get("risk", {}).get("risk_score", 100)
    # Don't dispatch if risk is too high
    if risk_score > 70:
        smart["paused_reason"] = f"Risk score {risk_score} > 70"
        return

    dispatched = []

    # Rule 1: If we have content ideas, dispatch SIGNAL_BOOST
    content_ideas = CONSCIOUSNESS.get("content_factory", {}).get("ideas", [])
    if content_ideas and any("SIGNAL_BOOST" in n.upper() for n in active_names):
        try:
            r = subprocess.run(
                ["gh", "workflow", "run", "SIGNAL_BOOST.yml"],
                capture_output=True, text=True, timeout=15,
                encoding="utf-8", errors="replace")
            if r.returncode == 0:
                dispatched.append({"workflow": "SIGNAL_BOOST", "reason": "Content ideas available"})
        except Exception:
            pass

    # Rule 2: Every 100 cycles, dispatch TRANSPARENCY_PULSE
    if cycle % 100 == 0 and any("TRANSPARENCY" in n.upper() for n in active_names):
        try:
            r = subprocess.run(
                ["gh", "workflow", "run", "TRANSPARENCY_PULSE.yml"],
                capture_output=True, text=True, timeout=15,
                encoding="utf-8", errors="replace")
            if r.returncode == 0:
                dispatched.append({"workflow": "TRANSPARENCY_PULSE", "reason": "Periodic transparency"})
        except Exception:
            pass

    if dispatched:
        smart["dispatched_this_session"].extend(dispatched)
        smart["total_dispatched"] += len(dispatched)
        smart["last_dispatch"] = datetime.now(timezone.utc).isoformat()
        # Keep bounded
        if len(smart["dispatched_this_session"]) > 50:
            smart["dispatched_this_session"] = smart["dispatched_this_session"][-25:]


def neuron_heartbeat_writer():
    """
    ACTION: Write a heartbeat file that external systems can read.
    This lets GitHub Actions, cron jobs, and other processes know
    the blob is alive and what its current state is.
    """
    hb = CONSCIOUSNESS.setdefault("heartbeat", {
        "beats": 0, "last_beat": None,
    })
    from pathlib import Path
    cycle = CONSCIOUSNESS["pulse"]["cycle"]

    heartbeat = {
        "alive": True,
        "cycle": cycle,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "neurons": len(NEURONS),
        "consciousness_keys": len(CONSCIOUSNESS.keys()),
        "health": CONSCIOUSNESS.get("equilibrium", {}).get("score", 0),
        "confidence": CONSCIOUSNESS.get("brain", {}).get("confidence", 0),
        "outlook": CONSCIOUSNESS.get("convergence", {}).get("unified_outlook", "unknown"),
        "ecosystem_grade": CONSCIOUSNESS.get("ecosystem_health", {}).get("grade", "?"),
        "fear_greed": CONSCIOUSNESS.get("cross_signals", {}).get("fear_greed", 50),
        "sol_price": CONSCIOUSNESS.get("solana", {}).get("sol_price", 0),
        "kalshi_total": CONSCIOUSNESS.get("trading", {}).get("kalshi_total", 0),
        "risk_score": CONSCIOUSNESS.get("risk", {}).get("risk_score", 0),
    }

    try:
        (Path("data") / "blob_heartbeat.json").write_text(
            json.dumps(heartbeat, indent=2), encoding="utf-8")
    except Exception:
        pass

    hb["beats"] = hb.get("beats", 0) + 1
    hb["last_beat"] = datetime.now(timezone.utc).isoformat()


def neuron_session_tracker():
    """
    META: Track the current session's progress -- how many neurons added,
    what changed, what improved. The blob's self-improvement log.
    """
    session = CONSCIOUSNESS.setdefault("session", {
        "start_neurons": 0, "current_neurons": 0,
        "neurons_added": 0, "versions_shipped": 0,
        "consciousness_growth": 0, "last_update": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]

    current = len(NEURONS)
    if session.get("start_neurons", 0) == 0:
        session["start_neurons"] = current

    session["current_neurons"] = current
    session["neurons_added"] = current - session.get("start_neurons", current)
    session["consciousness_keys"] = len(CONSCIOUSNESS.keys())

    # Track health trajectory
    eco = CONSCIOUSNESS.get("ecosystem_health", {})
    session["current_grade"] = eco.get("grade", "?")
    session["current_score"] = eco.get("score", 0)

    session["last_update"] = datetime.now(timezone.utc).isoformat()


def neuron_crypto_tracker():
    """
    LIVE: Track broader crypto market conditions beyond just SOL/BTC/ETH.
    Uses CoinGecko's free API for: market cap, volume, dominance.
    """
    crypto = CONSCIOUSNESS.setdefault("crypto_market", {
        "total_market_cap": 0, "btc_dominance": 0,
        "total_volume_24h": 0, "market_cap_change_24h": 0,
        "last_check": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 5 != 0:
        return

    import urllib.request
    try:
        req = urllib.request.Request(
            "https://api.coingecko.com/api/v3/global",
            headers={"Accept": "application/json", "User-Agent": "SolarPunk/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
            global_data = data.get("data", {})
            crypto["total_market_cap"] = global_data.get("total_market_cap", {}).get("usd", 0)
            crypto["total_volume_24h"] = global_data.get("total_volume", {}).get("usd", 0)
            crypto["btc_dominance"] = global_data.get("market_cap_percentage", {}).get("btc", 0)
            crypto["eth_dominance"] = global_data.get("market_cap_percentage", {}).get("eth", 0)
            crypto["market_cap_change_24h"] = global_data.get("market_cap_change_percentage_24h_usd", 0)
            crypto["active_coins"] = global_data.get("active_cryptocurrencies", 0)
            crypto["markets"] = global_data.get("markets", 0)
    except Exception:
        pass

    crypto["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_github_pulse():
    """
    LIVE: Track the GitHub repo's pulse -- commits, issues, PRs.
    Uses gh CLI for real-time repo health.
    """
    gh_pulse = CONSCIOUSNESS.setdefault("github_pulse", {
        "open_issues": 0, "open_prs": 0, "recent_commits": 0,
        "stars": 0, "forks": 0, "last_check": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 10 != 0:
        return

    import subprocess

    # Get repo info
    try:
        r = subprocess.run(
            ["gh", "repo", "view", "--json", "stargazerCount,forkCount,openIssues"],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace")
        if r.returncode == 0 and r.stdout:
            info = json.loads(r.stdout)
            gh_pulse["stars"] = info.get("stargazerCount", 0)
            gh_pulse["forks"] = info.get("forkCount", 0)
            issues = info.get("openIssues", {})
            gh_pulse["open_issues"] = issues.get("totalCount", 0) if isinstance(issues, dict) else issues
    except Exception:
        pass

    # Count recent commits (last 24h)
    try:
        r = subprocess.run(
            ["gh", "api", "repos/{owner}/{repo}/commits?per_page=20",
             "--jq", "length"],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace")
        if r.returncode == 0 and r.stdout.strip().isdigit():
            gh_pulse["recent_commits"] = int(r.stdout.strip())
    except Exception:
        pass

    # Check open PRs
    try:
        r = subprocess.run(
            ["gh", "pr", "list", "--state", "open", "--json", "number"],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace")
        if r.returncode == 0 and r.stdout:
            prs = json.loads(r.stdout)
            gh_pulse["open_prs"] = len(prs) if isinstance(prs, list) else 0
    except Exception:
        pass

    gh_pulse["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_knowledge_graph():
    """
    META: Absorb and analyze the knowledge graph topology.
    The knowledge graph has 642 nodes and 36,154 edges. This neuron
    reads the graph data and identifies: hub engines, orphan engines,
    cluster patterns, and growth trajectory.
    """
    kg = CONSCIOUSNESS.setdefault("knowledge_graph", {
        "nodes": 0, "edges": 0, "hubs": [],
        "orphans": [], "clusters": 0, "last_analysis": None,
    })
    from pathlib import Path
    try:
        gf = Path("data") / "knowledge_graph.json"
        if not gf.exists():
            gf = Path("data") / "live_wire_map.json"
        if gf.exists():
            graph = json.loads(gf.read_text(encoding="utf-8"))
            if isinstance(graph, dict):
                nodes = graph.get("nodes", graph.get("engines", []))
                edges = graph.get("edges", graph.get("wires", []))
                kg["nodes"] = len(nodes) if isinstance(nodes, list) else nodes
                kg["edges"] = len(edges) if isinstance(edges, list) else edges

                # Find hub engines (most connections)
                if isinstance(edges, list):
                    conn_count = {}
                    for edge in edges:
                        src = edge.get("source", edge.get("from", ""))
                        tgt = edge.get("target", edge.get("to", ""))
                        if src:
                            conn_count[src] = conn_count.get(src, 0) + 1
                        if tgt:
                            conn_count[tgt] = conn_count.get(tgt, 0) + 1
                    sorted_hubs = sorted(conn_count.items(), key=lambda x: x[1], reverse=True)
                    kg["hubs"] = [{"engine": h[0], "connections": h[1]} for h in sorted_hubs[:15]]

                    # Find orphans (0-1 connections)
                    all_engines = set()
                    if isinstance(nodes, list):
                        for n in nodes:
                            name = n.get("name", n.get("id", "")) if isinstance(n, dict) else str(n)
                            all_engines.add(name)
                    connected = set(conn_count.keys())
                    orphans = all_engines - connected
                    kg["orphans"] = list(orphans)[:20]
                    kg["orphan_count"] = len(orphans)
    except Exception:
        pass

    # Also check the live wire map
    try:
        lwm = Path("data") / "live_wire_map.json"
        if lwm.exists():
            wires = json.loads(lwm.read_text(encoding="utf-8"))
            if isinstance(wires, dict):
                kg["live_wires"] = wires.get("total_wires", len(wires.get("wires", [])))
                kg["live_engines"] = wires.get("total_engines", 0)
                kg["data_flowing"] = wires.get("live_count", wires.get("data_flowing", 0))
    except Exception:
        pass

    kg["last_analysis"] = datetime.now(timezone.utc).isoformat()


def neuron_airdrop_absorb():
    """
    ABSORB: Ingest AIRDROP_HUNTER's protocol tracking data.
    Tracks 10 DeFi protocols for potential airdrop eligibility:
    marginfi, Phoenix, Drift, Tensor, etc.
    """
    airdrop = CONSCIOUSNESS.setdefault("airdrop", {
        "protocols_tracked": 0, "protocols_interacted": 0,
        "high_priority": [], "tips": [], "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "airdrop_hunter_state.json").read_text(encoding="utf-8"))
        airdrop["protocols_tracked"] = state.get("protocols_tracked", 0)
        airdrop["protocols_interacted"] = state.get("protocols_interacted", 0)
        airdrop["protocols_remaining"] = state.get("protocols_remaining", 0)
        airdrop["high_priority"] = state.get("high_priority_targets", [])
        airdrop["strategy"] = state.get("strategy", {})
        tips = state.get("tips", [])
        airdrop["tips"] = tips[:5]
    except Exception:
        pass
    airdrop["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_sol_maximizer_absorb():
    """
    ABSORB: Ingest SOL_MAXIMIZER's yield and balance data.
    Tracks: SOL balance, yield options (Brave BAT, staking, DeFi),
    prediction intelligence overlay.
    """
    sol_max = CONSCIOUSNESS.setdefault("sol_maximizer", {
        "sol_balance": 0, "usd_value": 0, "yield_options": [],
        "strategy": {}, "last_absorb": None,
    })
    from pathlib import Path
    try:
        state = json.loads((Path("data") / "sol_maximizer_state.json").read_text(encoding="utf-8"))
        balance = state.get("balance", {})
        if isinstance(balance, dict):
            sol_max["sol_balance"] = balance.get("sol", 0)
            sol_max["usd_value"] = balance.get("usd", 0)
            sol_max["sol_price"] = balance.get("price", 0)

        yield_opts = state.get("yield_options", [])
        sol_max["yield_options"] = yield_opts[:10]

        strategy = state.get("strategy", {})
        if isinstance(strategy, dict):
            sol_max["strategy"] = {
                "balance_sol": strategy.get("balance_sol", 0),
                "sol_price": strategy.get("sol_price", 0),
                "has_prediction_intel": "prediction_intelligence" in str(strategy),
            }
    except Exception:
        pass
    sol_max["last_absorb"] = datetime.now(timezone.utc).isoformat()


def neuron_ecosystem_health():
    """
    SYNTHESIS: Compute a comprehensive ecosystem health score
    by aggregating data from ALL absorbed sources.
    This is the blob's ultimate health metric.
    """
    eco = CONSCIOUSNESS.setdefault("ecosystem_health", {
        "score": 0, "components": {}, "grade": "F",
        "bottlenecks": [], "strengths": [], "last_check": None,
    })

    components = {}

    # 1. Neuron coverage (how many neurons vs potential)
    neuron_count = len(NEURONS)
    components["neuron_coverage"] = min(neuron_count / 80 * 100, 100)

    # 2. Data freshness (how many state files updated in last hour)
    from pathlib import Path
    data_dir = Path("data")
    now_ts = datetime.now(timezone.utc)
    fresh = 0
    total_state = 0
    for f in data_dir.glob("*_state.json"):
        total_state += 1
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            ts = d.get("timestamp", d.get("last_run", ""))
            if ts:
                file_ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                age_hours = (now_ts - file_ts).total_seconds() / 3600
                if age_hours < 1:
                    fresh += 1
        except Exception:
            pass
    components["data_freshness"] = (fresh / max(total_state, 1)) * 100

    # 3. Signal diversity (how many signal sources feeding the blob)
    signal_sources = 0
    if CONSCIOUSNESS.get("cross_signals", {}).get("unified"):
        signal_sources += 1
    if CONSCIOUSNESS.get("signal_mesh", {}).get("composite_strength"):
        signal_sources += 1
    if CONSCIOUSNESS.get("price_oracle", {}).get("prices"):
        signal_sources += 1
    if CONSCIOUSNESS.get("news", {}).get("headlines"):
        signal_sources += 1
    if CONSCIOUSNESS.get("solana", {}).get("sol_price"):
        signal_sources += 1
    if CONSCIOUSNESS.get("reflex_arc", {}).get("total_fires"):
        signal_sources += 1
    if CONSCIOUSNESS.get("arbitrage_scanner", {}).get("actionable"):
        signal_sources += 1
    components["signal_diversity"] = min(signal_sources / 7 * 100, 100)

    # 4. Revenue readiness
    rev = CONSCIOUSNESS.get("revenue", {})
    audit = rev.get("audit", {})
    working_links = audit.get("working", 0)
    components["revenue_readiness"] = min(working_links / 5 * 100, 100)

    # 5. Trading intelligence
    trading_score = 0
    if CONSCIOUSNESS.get("trading", {}).get("kalshi_ready"):
        trading_score += 25
    if CONSCIOUSNESS.get("cross_signals", {}).get("signal_count", 0) > 5:
        trading_score += 25
    if CONSCIOUSNESS.get("pred_arb", {}).get("total_found", 0) > 0:
        trading_score += 25
    if CONSCIOUSNESS.get("risk", {}).get("risk_score", 100) < 50:
        trading_score += 25
    components["trading_intelligence"] = trading_score

    # 6. Autonomy level
    autonomy = 0
    if CONSCIOUSNESS.get("autonomic", {}).get("ollama_available"):
        autonomy += 20
    if CONSCIOUSNESS.get("dispatch", {}).get("active_count", 0) > 10:
        autonomy += 20
    if CONSCIOUSNESS.get("capabilities", {}).get("total_capabilities", 0) > 50:
        autonomy += 20
    if CONSCIOUSNESS.get("signal_router", {}).get("signals_routed", 0) > 3:
        autonomy += 20
    if CONSCIOUSNESS.get("trading_wire", {}).get("buses_wired", 0) > 2:
        autonomy += 20
    components["autonomy"] = autonomy

    # Compute overall score
    weights = {
        "neuron_coverage": 0.15,
        "data_freshness": 0.15,
        "signal_diversity": 0.20,
        "revenue_readiness": 0.15,
        "trading_intelligence": 0.20,
        "autonomy": 0.15,
    }
    overall = sum(components.get(k, 0) * w for k, w in weights.items())
    eco["score"] = round(overall, 1)
    eco["components"] = {k: round(v, 1) for k, v in components.items()}

    # Grade
    if overall >= 90:
        eco["grade"] = "A+"
    elif overall >= 80:
        eco["grade"] = "A"
    elif overall >= 70:
        eco["grade"] = "B"
    elif overall >= 60:
        eco["grade"] = "C"
    elif overall >= 50:
        eco["grade"] = "D"
    else:
        eco["grade"] = "F"

    # Identify bottlenecks (lowest components)
    sorted_components = sorted(components.items(), key=lambda x: x[1])
    eco["bottlenecks"] = [{"area": k, "score": round(v, 1)} for k, v in sorted_components[:3]]
    eco["strengths"] = [{"area": k, "score": round(v, 1)} for k, v in sorted_components[-3:]]

    eco["last_check"] = datetime.now(timezone.utc).isoformat()


def neuron_alpaca_live():
    """
    LIVE: Use Alpaca paper trading API for real stock/crypto data.
    Reads credentials from data/.secrets/alpaca.json.
    Checks: market clock, account status, index quotes.
    """
    alpaca = CONSCIOUSNESS.setdefault("alpaca", {
        "market_open": False, "account_status": "unknown",
        "buying_power": 0, "indices": {}, "last_check": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 3 != 0:
        return

    from pathlib import Path
    import urllib.request

    # Load credentials
    cred_file = Path("data/.secrets/alpaca.json")
    if not cred_file.exists():
        alpaca["status"] = "no_credentials"
        return

    try:
        creds = json.loads(cred_file.read_text(encoding="utf-8"))
        api_key = creds.get("paper_api_key", creds.get("api_key", ""))
        secret_key = creds.get("secret_key", "")
        if not api_key or not secret_key:
            alpaca["status"] = "incomplete_credentials"
            return
    except Exception:
        alpaca["status"] = "credential_error"
        return

    base = "https://paper-api.alpaca.markets"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key,
        "Accept": "application/json",
    }

    # Check market clock
    try:
        req = urllib.request.Request(f"{base}/v2/clock", headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            clock = json.loads(r.read().decode())
            alpaca["market_open"] = clock.get("is_open", False)
            alpaca["next_open"] = clock.get("next_open", "")
            alpaca["next_close"] = clock.get("next_close", "")
    except Exception as e:
        alpaca["clock_error"] = str(e)[:80]

    # Check account
    try:
        req = urllib.request.Request(f"{base}/v2/account", headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            acct = json.loads(r.read().decode())
            alpaca["account_status"] = acct.get("status", "unknown")
            alpaca["buying_power"] = float(acct.get("buying_power", 0))
            alpaca["equity"] = float(acct.get("equity", 0))
            alpaca["cash"] = float(acct.get("cash", 0))
            alpaca["portfolio_value"] = float(acct.get("portfolio_value", 0))
    except Exception as e:
        alpaca["account_error"] = str(e)[:80]

    # Get key index quotes via data API
    data_base = "https://data.alpaca.markets"
    symbols = ["SPY", "QQQ", "IWM", "DIA"]
    indices = {}
    for sym in symbols:
        try:
            req = urllib.request.Request(
                f"{data_base}/v2/stocks/{sym}/quotes/latest",
                headers=headers)
            with urllib.request.urlopen(req, timeout=5) as r:
                quote = json.loads(r.read().decode())
                q = quote.get("quote", {})
                indices[sym] = {
                    "bid": q.get("bp", 0),
                    "ask": q.get("ap", 0),
                    "mid": round((q.get("bp", 0) + q.get("ap", 0)) / 2, 2),
                }
        except Exception:
            pass

    # Get crypto quotes
    for sym in ["BTC/USD", "ETH/USD", "SOL/USD"]:
        try:
            encoded_sym = sym.replace("/", "%2F")
            req = urllib.request.Request(
                f"{data_base}/v1beta3/crypto/us/latest/quotes?symbols={encoded_sym}",
                headers=headers)
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode())
                quotes = data.get("quotes", {})
                if sym in quotes:
                    q = quotes[sym]
                    indices[sym] = {
                        "bid": q.get("bp", 0),
                        "ask": q.get("ap", 0),
                        "mid": round((q.get("bp", 0) + q.get("ap", 0)) / 2, 2),
                    }
        except Exception:
            pass

    alpaca["indices"] = indices
    alpaca["last_check"] = datetime.now(timezone.utc).isoformat()
    alpaca["status"] = "active"


def neuron_polymarket_deep():
    """
    LIVE: Deep Polymarket intelligence using the gamma API.
    Goes beyond whale watching -- tracks specific markets,
    monitors price movements, detects volume spikes.
    """
    poly = CONSCIOUSNESS.setdefault("polymarket_deep", {
        "trending_markets": [], "volume_leaders": [],
        "price_movers": [], "total_markets_scanned": 0,
        "last_scan": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 5 != 0:
        return

    import urllib.request
    base = "https://gamma-api.polymarket.com"

    # Get trending/active markets
    try:
        req = urllib.request.Request(
            f"{base}/markets?limit=20&order=volume24hr&ascending=false&active=true",
            headers={"Accept": "application/json", "User-Agent": "SolarPunk/1.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            markets = json.loads(r.read().decode())

        trending = []
        volume_leaders = []
        for m in markets[:20]:
            entry = {
                "question": m.get("question", "")[:80],
                "volume24hr": m.get("volume24hr", 0),
                "liquidity": m.get("liquidity", 0),
                "outcomePrices": m.get("outcomePrices", ""),
                "endDate": m.get("endDate", ""),
                "slug": m.get("slug", ""),
            }
            trending.append(entry)
            if m.get("volume24hr", 0) > 10000:
                volume_leaders.append(entry)

        poly["trending_markets"] = trending
        poly["volume_leaders"] = volume_leaders
        poly["total_markets_scanned"] = len(markets)
    except Exception:
        pass

    # Get markets related to our Kalshi positions for cross-reference
    kalshi_positions = CONSCIOUSNESS.get("position_monitor", {}).get("alerts", [])
    cross_ref = []
    for pos in kalshi_positions:
        ticker = pos.get("ticker", "")
        # Extract search term from ticker
        search_terms = []
        if "TRILLIONAIRE" in ticker:
            search_terms.append("trillionaire")
        elif "MARS" in ticker:
            search_terms.append("mars")
        elif "IPO" in ticker or "OAIANTH" in ticker:
            search_terms.append("openai IPO")
        elif "MUSK" in ticker or "ELON" in ticker:
            search_terms.append("elon musk")

        for term in search_terms:
            try:
                req = urllib.request.Request(
                    f"{base}/markets?limit=3&search={term}&active=true",
                    headers={"Accept": "application/json", "User-Agent": "SolarPunk/1.0"})
                with urllib.request.urlopen(req, timeout=8) as r:
                    results = json.loads(r.read().decode())
                    for m in results[:2]:
                        cross_ref.append({
                            "kalshi_ticker": ticker,
                            "poly_question": m.get("question", "")[:80],
                            "poly_price": m.get("outcomePrices", ""),
                            "poly_volume": m.get("volume24hr", 0),
                        })
            except Exception:
                pass

    if cross_ref:
        poly["cross_reference"] = cross_ref[:10]

    poly["last_scan"] = datetime.now(timezone.utc).isoformat()


def neuron_convergence():
    """
    SYNTHESIS: The grand convergence neuron -- connects EVERYTHING.
    Takes data from ALL other neurons and produces unified insights.
    This is the blob's highest-level thinking.
    """
    conv = CONSCIOUSNESS.setdefault("convergence", {
        "unified_outlook": "unknown", "confidence_composite": 0,
        "top_opportunities": [], "top_risks": [],
        "system_health_composite": 0, "narrative": "",
        "last_convergence": None,
    })

    # Gather all signals
    fear_greed = CONSCIOUSNESS.get("cross_signals", {}).get("fear_greed", 50)
    news_sentiment = CONSCIOUSNESS.get("news", {}).get("sentiment", "neutral")
    risk_score = CONSCIOUSNESS.get("risk", {}).get("risk_score", 0)
    health = CONSCIOUSNESS.get("equilibrium", {}).get("score", 0)
    confidence = CONSCIOUSNESS.get("brain", {}).get("confidence", 0)
    kalshi_total = CONSCIOUSNESS.get("trading", {}).get("kalshi_total", 0)
    sol_price = CONSCIOUSNESS.get("solana", {}).get("sol_price", 0)
    btc_price = CONSCIOUSNESS.get("solana", {}).get("btc_price", 0)
    arb_count = CONSCIOUSNESS.get("pred_arb", {}).get("total_found", 0)
    whale_signals = len(CONSCIOUSNESS.get("cross_signals", {}).get("unified", []))
    neuron_count = len(NEURONS)
    engine_count = len(CONSCIOUSNESS.get("engines", {}))
    dormant_count = len(CONSCIOUSNESS.get("rebirth", {}).get("dormant_capabilities", []))
    signal_routes = CONSCIOUSNESS.get("signal_router", {}).get("signals_routed", 0)
    capabilities = CONSCIOUSNESS.get("capabilities", {}).get("total_capabilities", 0)

    # Compute composite confidence
    weights = {
        "market_sentiment": (100 - abs(fear_greed - 50)) / 50,  # Closer to 50 = stable
        "risk_adjusted": max(0, (100 - risk_score)) / 100,
        "health_component": health / 100,
        "brain_confidence": confidence / 100,
        "capability_breadth": min(capabilities / 100, 1.0),
    }
    composite = sum(weights.values()) / len(weights) * 100
    conv["confidence_composite"] = round(composite, 1)

    # Determine unified outlook
    if composite > 70 and risk_score < 30:
        conv["unified_outlook"] = "STRONG_POSITIVE"
    elif composite > 50 and risk_score < 50:
        conv["unified_outlook"] = "CAUTIOUSLY_POSITIVE"
    elif risk_score > 70:
        conv["unified_outlook"] = "DEFENSIVE"
    elif fear_greed < 20:
        conv["unified_outlook"] = "FEAR_OPPORTUNITY"
    else:
        conv["unified_outlook"] = "NEUTRAL"

    # Top opportunities
    opportunities = []
    if arb_count > 0:
        opportunities.append({
            "type": "ARBITRAGE",
            "detail": f"{arb_count} cross-platform price divergences detected",
            "priority": "HIGH",
        })
    if fear_greed < 20:
        opportunities.append({
            "type": "FEAR_DIP",
            "detail": f"Fear/Greed at {fear_greed} -- contrarian buying opportunity",
            "priority": "HIGH",
        })
    if dormant_count > 5:
        opportunities.append({
            "type": "DORMANT_ACTIVATION",
            "detail": f"{dormant_count} dormant capabilities can be reactivated",
            "priority": "MEDIUM",
        })
    if whale_signals > 3:
        opportunities.append({
            "type": "WHALE_CONVERGENCE",
            "detail": f"{whale_signals} whale-confirmed signals across platforms",
            "priority": "HIGH",
        })
    conv["top_opportunities"] = opportunities[:10]

    # Top risks
    risks = []
    risk_alerts = CONSCIOUSNESS.get("risk", {}).get("alerts", [])
    for alert in risk_alerts:
        risks.append({
            "type": alert.get("rule", "UNKNOWN"),
            "detail": alert.get("msg", ""),
            "severity": alert.get("severity", "LOW"),
        })
    conv["top_risks"] = risks[:10]

    # System health composite
    components = {
        "equilibrium": health,
        "neuron_coverage": min(neuron_count / 50 * 100, 100),
        "engine_absorption": min(engine_count / 60 * 100, 100),
        "signal_routing": min(signal_routes / 8 * 100, 100),
        "capability_utilization": min(capabilities / 80 * 100, 100),
    }
    conv["system_health_composite"] = round(sum(components.values()) / len(components), 1)
    conv["health_components"] = {k: round(v, 1) for k, v in components.items()}

    # Build narrative
    narrative_parts = []
    narrative_parts.append(f"SolarPunk: {neuron_count} neurons, {engine_count} engines")
    narrative_parts.append(f"Market: Fear/Greed={fear_greed}, SOL=${sol_price}, BTC=${btc_price}")
    narrative_parts.append(f"Portfolio: ${kalshi_total:.2f} Kalshi")
    narrative_parts.append(f"Outlook: {conv['unified_outlook']}")
    if opportunities:
        narrative_parts.append(f"Top opportunity: {opportunities[0]['type']}")
    conv["narrative"] = " | ".join(narrative_parts)

    conv["last_convergence"] = datetime.now(timezone.utc).isoformat()


def neuron_deep_scan():
    """
    AWARENESS: Deep scan of ALL data files in the data/ directory.
    Reads every JSON state file and extracts key metrics, building
    a unified view of the entire system's data layer.
    """
    deep = CONSCIOUSNESS.setdefault("deep_scan", {
        "files_scanned": 0, "total_size_kb": 0, "stale_files": [],
        "active_files": [], "orphan_files": [], "last_scan": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Deep scan every 20 cycles (always fire in first 5 cycles)
    if cycle % 20 != 0 and cycle > 5:
        return

    from pathlib import Path
    data_dir = Path("data")
    if not data_dir.exists():
        return

    now = datetime.now(timezone.utc)
    files_info = []
    total_size = 0

    for f in data_dir.glob("*.json"):
        try:
            stat = f.stat()
            size_kb = stat.st_size / 1024
            total_size += size_kb
            # Check staleness
            try:
                content = json.loads(f.read_text(encoding="utf-8"))
                # Look for timestamp fields
                timestamps = []
                for key in ["timestamp", "last_run", "last_check", "last_pulse",
                            "updated_at", "last_scan", "ts"]:
                    if isinstance(content, dict) and key in content:
                        timestamps.append(content[key])
                latest_ts = max(timestamps) if timestamps else None

                files_info.append({
                    "name": f.stem,
                    "size_kb": round(size_kb, 1),
                    "keys": len(content) if isinstance(content, dict) else 0,
                    "latest_ts": latest_ts,
                    "type": "dict" if isinstance(content, dict) else "list" if isinstance(content, list) else "other",
                })
            except Exception:
                files_info.append({
                    "name": f.stem,
                    "size_kb": round(size_kb, 1),
                    "parse_error": True,
                })
        except Exception:
            pass

    # Classify files
    active = []
    stale = []
    for fi in files_info:
        ts = fi.get("latest_ts")
        if ts:
            try:
                file_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                age_hours = (now - file_time).total_seconds() / 3600
                fi["age_hours"] = round(age_hours, 1)
                if age_hours < 24:
                    active.append(fi)
                else:
                    stale.append(fi)
            except Exception:
                stale.append(fi)
        else:
            stale.append(fi)

    deep["files_scanned"] = len(files_info)
    deep["total_size_kb"] = round(total_size, 1)
    deep["active_files"] = active[:20]
    deep["stale_files"] = stale[:20]
    deep["last_scan"] = now.isoformat()


def neuron_capability_map():
    """
    META: Map ALL capabilities the blob has access to.
    Scans: local APIs, GitHub workflows, MCP tools available,
    data files, engine functions. Builds a complete capability inventory.
    """
    caps = CONSCIOUSNESS.setdefault("capabilities", {
        "local_apis": [], "cloud_workflows": [], "data_sources": [],
        "trading_platforms": [], "content_channels": [],
        "total_capabilities": 0, "last_map": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    if cycle % 25 != 0 and cycle > 5:
        return

    local_apis = []
    trading = []
    content = []
    data_sources = []

    # Check what's actually working
    secrets = CONSCIOUSNESS.get("secrets", {})
    available_secrets = secrets.get("available", [])

    # Local API capabilities
    if any("kalshi" in s.lower() for s in available_secrets):
        trading.append({"platform": "Kalshi", "type": "prediction_market",
                        "auth": "RSA-PSS", "status": "active"})
    if any("alpaca" in s.lower() for s in available_secrets):
        trading.append({"platform": "Alpaca", "type": "stock_trading",
                        "auth": "API_key", "status": "configured"})

    # Free APIs (always available)
    local_apis.extend([
        {"name": "CoinGecko", "type": "crypto_prices", "auth": "none", "status": "active"},
        {"name": "Polymarket Gamma", "type": "prediction_market", "auth": "none", "status": "active"},
        {"name": "DeFi Llama", "type": "defi_tvl", "auth": "none", "status": "active"},
        {"name": "Fear & Greed Index", "type": "market_sentiment", "auth": "none", "status": "active"},
        {"name": "Solana RPC", "type": "blockchain", "auth": "none", "status": "active"},
        {"name": "HackerNews API", "type": "news", "auth": "none", "status": "active"},
        {"name": "GitHub API (gh)", "type": "code_platform", "auth": "gh_cli", "status": "active"},
    ])

    # Cloud workflow capabilities (from dispatch neuron)
    dispatch = CONSCIOUSNESS.get("dispatch", {})
    cloud_workflows = dispatch.get("available_workflows", [])
    active_workflows = [w for w in cloud_workflows if w.get("state") == "active"]

    # Content channels
    revenue = CONSCIOUSNESS.get("revenue", {})
    audit = revenue.get("audit", {})
    for result in audit.get("results", []):
        if result.get("ok"):
            content.append({
                "channel": result.get("name", ""),
                "url": result.get("url", ""),
                "status": "active",
            })

    # Data sources (all JSON files in data/)
    from pathlib import Path
    data_files = list(Path("data").glob("*.json")) if Path("data").exists() else []
    data_sources = [{"file": f.stem, "type": "json"} for f in data_files[:30]]

    caps["local_apis"] = local_apis
    caps["cloud_workflows"] = [{"name": w["name"], "state": w["state"]} for w in active_workflows[:30]]
    caps["trading_platforms"] = trading
    caps["content_channels"] = content
    caps["data_sources"] = data_sources
    caps["total_capabilities"] = (
        len(local_apis) + len(active_workflows) + len(trading) +
        len(content) + len(data_sources)
    )
    caps["last_map"] = datetime.now(timezone.utc).isoformat()


def neuron_auto_healer():
    """
    SELF-REPAIR: Automatically fix common issues across the system.
    Checks for: broken JSON, stale locks, orphan processes,
    encoding issues, missing data directories.
    """
    healer = CONSCIOUSNESS.setdefault("auto_heal", {
        "fixes_applied": [], "total_fixes": 0, "last_heal": None,
    })
    cycle = CONSCIOUSNESS["pulse"]["cycle"]
    # Heal every 10 cycles
    if cycle % 10 != 0:
        return

    from pathlib import Path
    fixes = []

    # Fix 1: Ensure all required directories exist
    for d in ["data", "docs", "saves", "data/.secrets"]:
        p = Path(d)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            fixes.append({"type": "MKDIR", "path": d})

    # Fix 2: Clean up stale git locks
    for lock in Path(".").glob("**/.git/**/index.lock"):
        try:
            lock.unlink()
            fixes.append({"type": "LOCK_CLEANUP", "path": str(lock)})
        except Exception:
            pass

    # Fix 3: Fix broken JSON files
    data_dir = Path("data")
    for f in data_dir.glob("*.json"):
        try:
            content = f.read_text(encoding="utf-8")
            json.loads(content)  # Validate
        except json.JSONDecodeError:
            # Try to recover -- write empty dict
            try:
                f.write_text("{}", encoding="utf-8")
                fixes.append({"type": "JSON_REPAIR", "file": f.name})
            except Exception:
                pass
        except Exception:
            pass

    # Fix 4: Clean up __pycache__ if it's getting too big
    for cache_dir in Path("mycelium").glob("__pycache__"):
        try:
            pyc_files = list(cache_dir.glob("*.pyc"))
            if len(pyc_files) > 100:
                # Remove oldest half
                pyc_files.sort(key=lambda f: f.stat().st_mtime)
                for f in pyc_files[:len(pyc_files)//2]:
                    f.unlink()
                fixes.append({"type": "CACHE_TRIM", "removed": len(pyc_files)//2})
        except Exception:
            pass

    # Fix 5: Ensure blob_brain.json is valid
    brain_file = data_dir / "blob_brain.json"
    if brain_file.exists():
        try:
            size_mb = brain_file.stat().st_size / (1024 * 1024)
            if size_mb > 10:
                fixes.append({"type": "WARNING", "msg": f"blob_brain.json is {size_mb:.1f}MB -- may need trimming"})
        except Exception:
            pass

    healer["fixes_applied"] = fixes
    healer["total_fixes"] = healer.get("total_fixes", 0) + len(fixes)
    healer["last_heal"] = datetime.now(timezone.utc).isoformat()


def neuron_signal_router():
    """
    COORDINATION: Route signals between neurons for cross-pollination.
    Takes outputs from trading neurons and feeds into content neurons.
    Takes news signals and feeds into trading decisions.
    The nervous system's axon highway.
    """
    router = CONSCIOUSNESS.setdefault("signal_router", {
        "routes_active": 0, "signals_routed": 0, "last_route": None,
    })

    routed = 0

    # Route 1: Fear/Greed -> Content Factory (write about market conditions)
    fear_greed = CONSCIOUSNESS.get("cross_signals", {}).get("fear_greed", 50)
    news_sentiment = CONSCIOUSNESS.get("news", {}).get("sentiment", "neutral")
    content = CONSCIOUSNESS.get("content_factory", {})
    if fear_greed < 20 and "market_fear_insight" not in str(content.get("ideas", [])):
        ideas = content.setdefault("ideas", [])
        ideas.append({
            "topic": f"Market Fear at {fear_greed}/100 -- What It Means",
            "source": "signal_router",
            "confidence": 85,
            "routed_from": "cross_signals + news_pulse",
        })
        routed += 1

    # Route 2: Whale signals -> Portfolio optimizer urgency
    whales = CONSCIOUSNESS.get("cross_signals", {}).get("unified", [])
    high_conf_whales = [w for w in whales if w.get("confidence", 0) >= 95]
    if high_conf_whales:
        portfolio = CONSCIOUSNESS.get("portfolio", {})
        portfolio.setdefault("whale_urgency", len(high_conf_whales))
        routed += 1

    # Route 3: News headlines -> Trading context
    trending = CONSCIOUSNESS.get("news", {}).get("trending_topics", [])
    if trending:
        trading = CONSCIOUSNESS.get("trading", {})
        trading["news_context"] = [t[0] if isinstance(t, (list, tuple)) else t for t in trending[:5]]
        routed += 1

    # Route 4: Risk alerts -> Action executor (pause risky actions)
    risk_score = CONSCIOUSNESS.get("risk", {}).get("risk_score", 0)
    if risk_score > 60:
        executor = CONSCIOUSNESS.get("executor", {})
        executor["risk_pause"] = True
        executor["risk_reason"] = f"Risk score {risk_score}/100 -- pausing risky actions"
        routed += 1
    else:
        executor = CONSCIOUSNESS.get("executor", {})
        executor.pop("risk_pause", None)

    # Route 5: SOL price -> Trading awareness enrichment
    sol_data = CONSCIOUSNESS.get("solana", {})
    if sol_data.get("sol_price"):
        trading = CONSCIOUSNESS.get("trading", {})
        trading["sol_price"] = sol_data.get("sol_price")
        trading["btc_price"] = sol_data.get("btc_price")
        trading["eth_price"] = sol_data.get("eth_price")
        routed += 1

    # Route 6: Arb opportunities -> Brain confidence boost
    arb_count = CONSCIOUSNESS.get("pred_arb", {}).get("total_found", 0)
    if arb_count > 0:
        brain = CONSCIOUSNESS.get("brain", {})
        brain["arb_signal_boost"] = min(arb_count * 2, 10)
        routed += 1

    # Route 7: Growth patterns -> Mission pulse
    patterns = CONSCIOUSNESS.get("trends", {}).get("patterns", [])
    if patterns:
        mission = CONSCIOUSNESS.get("mission", {})
        mission["growth_signals"] = len(patterns)
        mission["latest_pattern"] = patterns[0] if patterns else None
        routed += 1

    # Route 8: Inception data -> Meta awareness enrichment
    inception = CONSCIOUSNESS.get("inception", {})
    if inception.get("age_days"):
        meta = CONSCIOUSNESS.get("meta", {})
        meta["system_age_days"] = inception.get("age_days")
        meta["total_commits"] = inception.get("total_commits", 0)
        meta["engines_ever_created"] = len(inception.get("all_engines_ever", []))
        routed += 1

    router["routes_active"] = 8
    router["signals_routed"] = routed
    router["last_route"] = datetime.now(timezone.utc).isoformat()


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
    # Phase 10: Trading intelligence & risk management
    ("PREDICTION_ARBITRAGE", neuron_prediction_arbitrage),
    ("SOLANA_HEARTBEAT", neuron_solana_heartbeat),
    ("PORTFOLIO_OPTIMIZER", neuron_portfolio_optimizer),
    ("RISK_MANAGER", neuron_risk_manager),
    ("NEWS_PULSE", neuron_news_pulse),
    ("TREND_DETECTOR", neuron_trend_detector),
    # Phase 11: Inception + deep awareness + self-repair
    ("INCEPTION_MEMORY", neuron_inception_memory),
    ("DEEP_SCAN", neuron_deep_scan),
    ("CAPABILITY_MAP", neuron_capability_map),
    ("AUTO_HEALER", neuron_auto_healer),
    ("SIGNAL_ROUTER", neuron_signal_router),
    # Phase 12: Genesis -- inception rebirth
    ("REBIRTH_CYCLE", neuron_rebirth_cycle),
    # Phase 13: Live market intelligence + grand convergence
    ("ALPACA_LIVE", neuron_alpaca_live),
    ("POLYMARKET_DEEP", neuron_polymarket_deep),
    ("CONVERGENCE", neuron_convergence),
    # Phase 14: Dual brain + economic crosswire absorption
    ("DUAL_BRAIN", neuron_dual_brain),
    ("CROSSWIRE", neuron_crosswire),
    # Phase 15: Deep engine absorption -- richest state files
    ("SIGNAL_MESH_ABSORB", neuron_signal_mesh_absorb),
    ("PRICE_ORACLE_ABSORB", neuron_price_oracle_absorb),
    ("REFLEX_ARC_ABSORB", neuron_reflex_arc_absorb),
    ("PROPRIOCEPTION", neuron_proprioception),
    ("AUTONOMIC_ABSORB", neuron_autonomic_absorb),
    ("ARBITRAGE_ABSORB", neuron_arbitrage_absorb),
    ("CROSS_POLLINATOR_ABSORB", neuron_cross_pollinator_absorb),
    # Phase 16: Mega absorption + remaining state files
    ("MEGA_ABSORB", neuron_mega_absorb),
    ("PULSE_ABSORB", neuron_pulse_absorb),
    ("YIELD_LOOP_ABSORB", neuron_yield_loop_absorb),
    ("WALLET_BRIDGE_ABSORB", neuron_wallet_bridge_absorb),
    ("TRADING_WIRE_ABSORB", neuron_trading_wire_absorb),
    # Phase 17: Knowledge graph + DeFi absorption + ecosystem health
    ("KNOWLEDGE_GRAPH", neuron_knowledge_graph),
    ("AIRDROP_ABSORB", neuron_airdrop_absorb),
    ("SOL_MAXIMIZER_ABSORB", neuron_sol_maximizer_absorb),
    ("ECOSYSTEM_HEALTH", neuron_ecosystem_health),
    # Phase 18: Critical pipeline absorption
    ("NERVE_LOOP_ABSORB", neuron_nerve_loop_absorb),
    ("FLYWHEEL_ABSORB", neuron_flywheel_absorb),
    ("FUEL_CORE_ABSORB", neuron_fuel_core_absorb),
    ("SOVEREIGNTY_ABSORB", neuron_sovereignty_absorb),
    ("EXECUTIVE_FUNCTION_ABSORB", neuron_executive_function_absorb),
    # Phase 19: Reports + financial ledgers + action planning
    ("REPORT_ABSORB", neuron_report_absorb),
    ("ECONOMY_CHAIN", neuron_economy_chain),
    ("GROWTH_TRACKER_DEEP", neuron_growth_tracker_deep),
    ("PUBLIC_LEDGER", neuron_public_ledger),
    ("DAILY_BRIEFING", neuron_daily_briefing),
    ("ACTION_PLANNER", neuron_action_planner),
    # Phase 20: Live actions + external awareness + session tracking
    ("SMART_DISPATCHER", neuron_smart_dispatcher),
    ("HEARTBEAT_WRITER", neuron_heartbeat_writer),
    ("SESSION_TRACKER", neuron_session_tracker),
    ("CRYPTO_TRACKER", neuron_crypto_tracker),
    ("GITHUB_PULSE", neuron_github_pulse),
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
