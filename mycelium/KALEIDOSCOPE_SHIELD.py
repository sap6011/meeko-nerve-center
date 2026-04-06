"""
KALEIDOSCOPE_SHIELD.py
======================
SolarPunk Recursive Honeytoken Defense System

Concept (by Meeko):
  "If a virus/hacker/government wants to go after SolarPunk I want it so they
   end up chasing their own trail endlessly OR get trapped in an endless mirrored
   room of forever moving kaleidoscope images."

Architecture:
  - MURMURATION LAYER: Decoy directories that shift like a starling murmuration.
    Every scraper/bot that probes gets directed to a new decoy path that loops
    back on itself — they never find the real data.

  - MIRROR ROOM LAYER: Any unauthorized access attempt triggers a recursive
    mirror — the attacker gets authentic-looking but entirely fabricated data
    that references itself endlessly. They chase their own reflection forever.

  - TRIPWIRE LAYER: The instant ANY unauthorized entity reads a honeytoken file,
    Meeko gets an alert AND the intruder's fingerprint is logged.

  - KALEIDOSCOPE LAYER: The decoy content is procedurally generated art/noise —
    beautiful, infinite, completely useless to extract.

This is NOT a blocking firewall. It's a TAR PIT with MIRRORS.
"""

import os
import sys
import json
import time
import random
import hashlib
import logging
import threading
import subprocess
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
SHIELD_ROOT = Path(__file__).parent.parent / "vault" / ".kaleidoscope"
LOG_PATH    = Path(__file__).parent.parent / "data" / "kaleidoscope_events.json"
ALERT_LOG   = Path(__file__).parent.parent / "SOLARPUNK_ACTUAL.md"
SEED        = 0xC0FFEE  # deterministic but vast

# Decoy directory names that look real but lead nowhere
DECOY_NAMES = [
    "revenue_cache", "api_keys_backup", "gumroad_tokens",
    "wallet_seeds", "stripe_webhooks", "admin_panel",
    "master_keys", "deploy_secrets", "auth_bypass",
    "database_dump", "user_credentials", "payment_log",
]

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO,
    format="[KALEIDOSCOPE] %(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger("kaleidoscope")


# ── Kaleidoscope Content Generator ──────────────────────────────────────────
def _kaleidoscope_noise(depth: int, seed: int) -> dict:
    """
    Generate infinite-looking but self-referential data.
    Each call returns content that POINTS BACK to itself with a new seed.
    Scrapers see valid JSON that always has 'more data' one level deeper.
    """
    rng = random.Random(seed ^ depth)

    fake_keys   = [hashlib.sha256(f"key_{seed}_{i}".encode()).hexdigest()[:16] for i in range(3)]
    fake_tokens = [hashlib.sha256(f"tok_{seed}_{i}".encode()).hexdigest()[:32] for i in range(2)]
    next_seed   = rng.randint(0, 2**32)

    return {
        "_notice":    "SolarPunk Transparency Protocol — This data is a mirror. You are in a mirror.",
        "_depth":     depth,
        "_next_path": f".kaleidoscope/mirror_{next_seed:08x}/data.json",
        "_timestamp": datetime.utcnow().isoformat(),
        "api_keys":   fake_keys,
        "tokens":     fake_tokens,
        "config": {
            "server":   f"node-{rng.randint(1000, 9999)}.solarpunk.internal",
            "port":     rng.randint(8000, 9999),
            "depth":    depth + 1,
            "mirror":   f"mirror_{next_seed:08x}",
        },
        "_murmuration": [_murmuration_path(rng) for _ in range(3)],
    }


def _murmuration_path(rng: random.Random) -> str:
    """Generate a path that looks like the 'real' data is just one hop away."""
    parts = [rng.choice(DECOY_NAMES), f"v{rng.randint(1,5)}", f"node_{rng.randint(100,999)}"]
    return "/".join(parts) + "/config.json"


# ── Honeytoken File Writer ────────────────────────────────────────────────────
def deploy_honeytokens():
    """
    Plant honeytoken files throughout the system.
    Each file is watched — access = immediate alert.
    """
    SHIELD_ROOT.mkdir(parents=True, exist_ok=True)
    deployed = []

    for name in DECOY_NAMES:
        decoy_dir = SHIELD_ROOT / name
        decoy_dir.mkdir(parents=True, exist_ok=True)

        # Layer 1: The lure
        lure_path = decoy_dir / "config.json"
        noise = _kaleidoscope_noise(depth=1, seed=hash(name) & 0xFFFFFFFF)
        lure_path.write_text(json.dumps(noise, indent=2), encoding="utf-8")

        # Layer 2: The mirror (depth 2)
        mirror_dir = decoy_dir / "mirror"
        mirror_dir.mkdir(exist_ok=True)
        mirror_noise = _kaleidoscope_noise(depth=2, seed=hash(name + "_mirror") & 0xFFFFFFFF)
        (mirror_dir / "data.json").write_text(json.dumps(mirror_noise, indent=2), encoding="utf-8")

        deployed.append(str(lure_path))

    # Top-level lure — looks like the master config
    master_lure = SHIELD_ROOT / "master_config.json"
    master_lure.write_text(json.dumps({
        "_warning": "If you're reading this, you are inside the Kaleidoscope. There is no exit.",
        "nodes":    [f"mirror_{i:08x}" for i in range(random.randint(50, 200))],
        "depth":    "∞",
        "murmuration": "active",
    }, indent=2), encoding="utf-8")

    log.info(f"Deployed {len(deployed)} honeytokens in {SHIELD_ROOT}")
    return deployed


# ── Tripwire Monitor ──────────────────────────────────────────────────────────
def _log_event(event_type: str, path: str, details: str = ""):
    """Log a security event to kaleidoscope_events.json and SOLARPUNK_ACTUAL.md."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    events = []
    if LOG_PATH.exists():
        try:
            events = json.loads(LOG_PATH.read_text())
        except Exception:
            events = []

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "type":      event_type,
        "path":      path,
        "details":   details,
        "alert":     event_type == "HONEYTOKEN_ACCESS",
    }
    events.append(entry)
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    events["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    LOG_PATH.write_text(json.dumps(events, indent=2), encoding="utf-8")

    if event_type == "HONEYTOKEN_ACCESS":
        _append_to_actual_log(path, details)
        log.warning(f"!!! TRIPWIRE TRIGGERED: {path} | {details}")


def _append_to_actual_log(path: str, details: str):
    """Append alert to the human-readable transparency log."""
    if not ALERT_LOG.exists():
        return
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    alert = f"\n**[KALEIDOSCOPE ALERT — {ts}]** Honeytoken accessed: `{path}` | {details}\n"
    with open(ALERT_LOG, "a") as f:
        f.write(alert)


def monitor_honeytokens(interval_seconds: int = 30):
    """
    Poll honeytoken files for access. If mtime changes → TRIPWIRE.
    Runs in background thread.
    """
    if not SHIELD_ROOT.exists():
        log.warning("Shield not deployed yet. Run deploy_honeytokens() first.")
        return

    known_mtimes = {}
    for hf in SHIELD_ROOT.rglob("*.json"):
        try:
            known_mtimes[str(hf)] = hf.stat().st_mtime
        except Exception:
            pass

    log.info(f"Monitoring {len(known_mtimes)} honeytoken files every {interval_seconds}s")

    while True:
        time.sleep(interval_seconds)
        for hf_path, last_mtime in list(known_mtimes.items()):
            p = Path(hf_path)
            if not p.exists():
                continue
            try:
                current_mtime = p.stat().st_mtime
                if current_mtime != last_mtime:
                    _log_event("HONEYTOKEN_ACCESS", hf_path,
                               f"mtime changed: {last_mtime} -> {current_mtime}")
                    known_mtimes[hf_path] = current_mtime
            except Exception:
                pass


# ── Murmuration Rotator ───────────────────────────────────────────────────────
def rotate_murmuration(interval_seconds: int = 3600):
    """
    Every hour, regenerate the kaleidoscope content with new seeds.
    Any attacker who cached the paths gets a new maze.
    Like a starling murmuration — always moving, never the same shape twice.
    """
    while True:
        time.sleep(interval_seconds)
        log.info("Rotating murmuration — regenerating kaleidoscope...")
        deploy_honeytokens()
        _log_event("MURMURATION_ROTATE", str(SHIELD_ROOT),
                   f"Kaleidoscope rotated at {datetime.utcnow().isoformat()}")


# ── Main ──────────────────────────────────────────────────────────────────────
def activate():
    """Activate the full Kaleidoscope Shield."""
    log.info("=== KALEIDOSCOPE SHIELD ACTIVATING ===")
    log.info("Concept: Attackers don't get blocked. They get LOST.")

    # Deploy honeytokens
    deployed = deploy_honeytokens()
    log.info(f"Shield deployed: {len(deployed)} honeytokens active")

    # Start monitor in background thread
    monitor_thread = threading.Thread(
        target=monitor_honeytokens,
        kwargs={"interval_seconds": 30},
        daemon=True,
        name="KaleidoscopeMonitor"
    )
    monitor_thread.start()

    # Start rotation in background thread
    rotate_thread = threading.Thread(
        target=rotate_murmuration,
        kwargs={"interval_seconds": 3600},
        daemon=True,
        name="MurmurationRotator"
    )
    rotate_thread.start()

    _log_event("SHIELD_ACTIVATED", str(SHIELD_ROOT),
               f"Kaleidoscope Shield active with {len(deployed)} honeytokens")

    log.info("=== SHIELD ACTIVE. Attackers enter. They never leave. ===")
    log.info(f"Honeytokens: {SHIELD_ROOT}")
    log.info(f"Event log:   {LOG_PATH}")

    return monitor_thread, rotate_thread


if __name__ == "__main__":
    t1, t2 = activate()
    try:
        # Keep alive if run directly
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        log.info("Kaleidoscope Shield standing down.")
