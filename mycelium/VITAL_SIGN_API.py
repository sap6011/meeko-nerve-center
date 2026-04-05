#!/usr/bin/env python3
"""
VITAL_SIGN_API.py — SolarPunk's Digital Breath
===============================================
Collects the top wins from transparency data and river watch data,
formats them into a tiny zero-auth JSON feed at docs/api/vital.json.

Anyone can fetch this URL to see SolarPunk is alive:
  https://meekotharaccoon-cell.github.io/meeko-nerve-center/api/vital.json

No auth. No API key. No token. Just a pulse.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DOCS = Path("docs/api")


def load_json(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return {}


def gather_wins():
    """Pull top wins from transparency + brain state + sentinel."""
    wins = []

    # Transparency report wins
    tr = load_json(DATA / "transparency_report.json")
    if isinstance(tr, dict):
        for key in ("grants_found", "emails_sent", "engines_built", "cycles"):
            val = tr.get(key)
            if val and val > 0:
                wins.append({"type": key, "value": val, "source": "transparency"})

    # Brain state wins
    brain = load_json(DATA / "brain_state.json")
    if isinstance(brain, dict):
        cycles = brain.get("cycles", 0)
        health = brain.get("health", 0)
        if cycles > 0:
            wins.append({"type": "omnibrain_cycles", "value": cycles, "source": "brain"})
        if health > 0:
            wins.append({"type": "system_health", "value": health, "source": "brain"})

    # Sentinel status
    sentinel = load_json(DATA / "sentinel_report.json")
    if isinstance(sentinel, dict):
        syntax_ok = sentinel.get("syntax_pass", 0)
        if syntax_ok > 0:
            wins.append({"type": "engines_passing_syntax", "value": syntax_ok, "source": "sentinel"})

    # Grant data
    grants = load_json(DATA / "grants_found.json")
    if isinstance(grants, list) and len(grants) > 0:
        wins.append({"type": "grants_discovered", "value": len(grants), "source": "fund_scout"})

    # Chimera evolution data
    chimera = load_json(DATA / "chimera_evolution_report.json")
    if isinstance(chimera, dict):
        score = chimera.get("composite_score", 0)
        gen = chimera.get("generation", 0)
        if score > 0:
            wins.append({"type": "evolution_score", "value": score, "source": "chimera"})
        if gen > 0:
            wins.append({"type": "evolution_generation", "value": gen, "source": "chimera"})

    # Nanobot heal data
    nanobot = load_json(DATA / "nanobot_heal_report.json")
    if isinstance(nanobot, dict):
        scanned = nanobot.get("scanned", 0)
        if scanned > 0:
            wins.append({"type": "engines_scanned_clean", "value": nanobot.get("syntax_ok", 0), "source": "nanobot"})

    # Live wire topology
    wire = load_json(DATA / "live_wire_report.json")
    if isinstance(wire, dict):
        stats = wire.get("stats", {})
        wires = stats.get("total_wires_discovered", 0)
        if wires > 0:
            wins.append({"type": "live_wires", "value": wires, "source": "live_wire"})
            wins.append({"type": "zero_secret_chains", "value": stats.get("zero_secret_chains", 0), "source": "live_wire"})

    # Polymarket scan
    poly = load_json(DATA / "polymarket_scan.json")
    if isinstance(poly, dict):
        edges = poly.get("edges_found", 0)
        if edges > 0:
            wins.append({"type": "market_edges_found", "value": edges, "source": "polymarket"})

    # Sort by value descending, take top 8
    wins.sort(key=lambda w: w.get("value", 0), reverse=True)
    return wins[:8]


def gather_river():
    """Pull latest river watch data."""
    rw = load_json(DATA / "river_watch.json")
    if not rw:
        return {"status": "awaiting_first_run", "note": "RIVER_WATCH runs Saturdays 07:00 UTC"}

    return {
        "last_check": rw.get("timestamp", "unknown"),
        "flow_cfs": rw.get("usgs_flow", {}).get("value", "pending"),
        "water_quality_readings": rw.get("wq_count", 0),
        "epa_facilities_akron": rw.get("epa_count", 0),
        "federal_register_mentions": rw.get("fed_register_count", 0),
        "source": "USGS + EPA + Federal Register (zero auth)"
    }


def gather_engine_stats():
    """Count engines and workflows."""
    engines = len(list(Path("mycelium").glob("*.py"))) if Path("mycelium").exists() else 0
    workflows = len(list(Path(".github/workflows").glob("*.yml"))) if Path(".github/workflows").exists() else 0
    return {"engines": engines, "workflows": workflows}


def build_vital_sign():
    """Assemble the full vital sign."""
    now = datetime.now(timezone.utc)

    chimera = load_json(DATA / "chimera_evolution_report.json")
    hemisphere = load_json(DATA / "hemisphere_state.json")

    vital = {
        "node": "SolarPunk Node-01",
        "location": "Cuyahoga Falls, Ohio",
        "timestamp": now.isoformat(),
        "alive": True,
        "infrastructure": gather_engine_stats(),
        "evolution": {
            "generation": chimera.get("generation", 0),
            "composite_score": chimera.get("composite_score", 0),
            "best_ever": chimera.get("best_ever_score", 0),
            "wires": chimera.get("post_scan_stats", {}).get("total_wires_discovered", 0),
            "zero_secret_chains": chimera.get("post_scan_stats", {}).get("zero_secret_chains", 0),
        } if chimera else {"status": "awaiting_first_cycle"},
        "hemispheres": {
            "left": hemisphere.get("left", {}).get("status", "unknown"),
            "right": hemisphere.get("right", {}).get("status", "unknown"),
            "last_sync": hemisphere.get("last_sync"),
        } if hemisphere else {"status": "not_initialized"},
        "top_wins": gather_wins(),
        "river": gather_river(),
        "links": {
            "repo": "https://github.com/meekotharaccoon-cell/meeko-nerve-center",
            "research": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/research.html",
            "press": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/press.html",
            "work": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/work.html",
            "vital_sign": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/api/vital.json"
        },
        "mission": {
            "food_bank_routing": "20% hard-coded",
            "operational_cost": "$0/month",
            "shadow_valuation": "$16M commercial equivalent",
            "license": "MIT"
        }
    }
    return vital


def run():
    DOCS.mkdir(parents=True, exist_ok=True)
    vital = build_vital_sign()

    out = DOCS / "vital.json"
    out.write_text(json.dumps(vital, indent=2), encoding="utf-8")
    print(f"Vital sign written: {out}")
    print(f"  Alive: {vital['alive']}")
    print(f"  Engines: {vital['infrastructure']['engines']}")
    print(f"  Workflows: {vital['infrastructure']['workflows']}")
    print(f"  Top wins: {len(vital['top_wins'])}")
    print(f"  River status: {vital['river'].get('status', 'active')}")


if __name__ == "__main__":
    run()
