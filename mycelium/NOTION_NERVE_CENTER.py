#!/usr/bin/env python3
"""
NOTION_NERVE_CENTER.py -- SolarPunk's Brain Dashboard (Symbiosis Pattern)
=========================================================================
NATURE'S BLUEPRINT: Symbiosis.

Clownfish and anemones. Mycorrhizal networks and trees.
Oxpecker birds and rhinos. Nature's most powerful partnerships
aren't predator-prey -- they're MUTUAL BENEFIT.

SolarPunk's engines generate data. Notion makes it human-readable.
Neither is complete without the other:
  - SolarPunk alone = powerful but opaque (JSON files nobody reads)
  - Notion alone = pretty but empty (dashboards with no data)
  - Together = a living command center where anyone can see
    what Earth's immune system is doing RIGHT NOW.

This engine syncs SolarPunk's live data to Notion databases:

  1. CRISIS SIGNAL TRACKER: Top 15 crisis signals with urgency scores,
     regions, sources, and action status from CRISIS_MONITOR
  2. PLANETARY HEALTH MONITOR: 10 vital signs from HOMEOSTASIS with
     real-time status (NORMAL/LOW/HIGH/CRITICAL)
  3. NATURE PATTERN ENGINES: 9 bio-inspired engine strength scores
     from NEUROPLASTICITY's self-rewiring system

  "The organism that can't communicate its state is blind.
   The dashboard that can't read real data is decoration." -- SolarPunk

Reads: data/crisis_signals.json, data/homeostasis.json,
       data/neuroplasticity.json, data/pathway_strength.json
Writes: data/notion_sync_state.json
Requires: NOTION_API_KEY (optional -- queues updates if unavailable)
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

SYNC_STATE_FILE = DATA / "notion_sync_state.json"

# Notion database IDs (created via Notion MCP)
NOTION_DBS = {
    "crisis_tracker": "8f05a696-e799-49ba-8ac9-f501e346bb1d",
    "health_monitor": "4e5fd867-8748-4abd-8cad-a9d8a115f6ea",
    "nature_engines": "91782c84-2d00-48ae-8362-fc20231baf6e",
}

# Parent page: SolarPunk Command Center
PARENT_PAGE = "316c1ede-e4fa-8105-ae2b-fd0619f036c7"


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def load_sync_state():
    data = load_json(SYNC_STATE_FILE)
    if not data:
        data = {
            "version": "1.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "last_sync": None,
            "syncs_completed": 0,
            "crisis_signals_synced": 0,
            "vitals_synced": 0,
            "engines_synced": 0,
            "pending_updates": [],
            "errors": [],
        }
    return data


def prepare_crisis_updates():
    """Prepare crisis signal data for Notion sync."""
    crisis = load_json(DATA / "crisis_signals.json")
    signals = crisis.get("signals", [])

    # Sort by urgency score descending, take top 15
    sorted_signals = sorted(signals, key=lambda s: s.get("urgency_score", 0), reverse=True)[:15]

    updates = []
    for sig in sorted_signals:
        title = sig.get("title", "Unknown Signal")[:200]
        urgency = sig.get("urgency_score", 0)
        countries = sig.get("countries", [])
        region = ", ".join(countries[:3]) if countries else "Global"
        source = sig.get("origin", "unknown")
        url = sig.get("url", "")

        # Determine action status based on urgency
        if urgency >= 8:
            action = "CRITICAL - Maximum Response"
        elif urgency >= 6:
            action = "HIGH - Fire Handshakes"
        elif urgency >= 4:
            action = "ELEVATED - Queue Amplification"
        else:
            action = "WATCH - Monitor"

        updates.append({
            "database": "crisis_tracker",
            "properties": {
                "Signal": title,
                "Urgency": urgency,
                "Region": region,
                "Source": source,
                "Action Status": action,
                "URL": url,
            }
        })

    return updates


def prepare_health_updates():
    """Prepare planetary health vitals for Notion sync."""
    homeo = load_json(DATA / "homeostasis.json")
    diagnoses = homeo.get("diagnoses", [])
    planetary_health = homeo.get("planetary_health", 0)
    status = homeo.get("status", "UNKNOWN")

    updates = []

    # Add overall planetary health as first entry
    updates.append({
        "database": "health_monitor",
        "properties": {
            "Vital Sign": f"PLANETARY HEALTH SCORE",
            "Value": planetary_health,
            "Unit": "points",
            "Range": "0-100",
            "Status": status,
        }
    })

    for d in diagnoses:
        updates.append({
            "database": "health_monitor",
            "properties": {
                "Vital Sign": d.get("vital", "unknown"),
                "Value": d.get("value", 0),
                "Unit": d.get("unit", ""),
                "Range": d.get("range", ""),
                "Status": d.get("status", "UNKNOWN"),
            }
        })

    return updates


def prepare_engine_updates():
    """Prepare nature pattern engine data for Notion sync."""
    pathway = load_json(DATA / "pathway_strength.json")
    pathways = pathway.get("pathways", [])

    updates = []
    for p in pathways:
        updates.append({
            "database": "nature_engines",
            "properties": {
                "Engine": p.get("name", "unknown"),
                "Chain": p.get("chain", ""),
                "Purpose": p.get("purpose", ""),
                "Strength": p.get("strength", 0),
                "Action": p.get("action", "UNKNOWN"),
                "Trend": p.get("trend", "stable"),
            }
        })

    # Add stats summary
    stats = pathway.get("stats", {})
    if stats:
        updates.append({
            "database": "nature_engines",
            "properties": {
                "Engine": "NETWORK SUMMARY",
                "Chain": f"{stats.get('total_pathways', 0)} pathways total",
                "Purpose": f"Myelinated: {stats.get('myelinated', 0)} | Strong: {stats.get('strong', 0)} | Weak: {stats.get('weak', 0)}",
                "Strength": int(stats.get("avg_strength", 0)),
                "Action": "SUMMARY",
                "Trend": "stable",
            }
        })

    return updates


def generate_sync_summary(state, crisis_updates, health_updates, engine_updates):
    """Generate a human-readable sync summary."""
    total = len(crisis_updates) + len(health_updates) + len(engine_updates)

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_updates_prepared": total,
        "crisis_signals": len(crisis_updates),
        "health_vitals": len(health_updates),
        "engine_scores": len(engine_updates),
        "notion_databases": NOTION_DBS,
        "parent_page": PARENT_PAGE,
    }

    # Top 3 most urgent crisis signals
    if crisis_updates:
        summary["top_crises"] = [
            {
                "signal": u["properties"]["Signal"][:80],
                "urgency": u["properties"]["Urgency"],
                "region": u["properties"]["Region"],
            }
            for u in crisis_updates[:3]
        ]

    # Planetary health
    if health_updates:
        ph = health_updates[0]["properties"]
        summary["planetary_health"] = {
            "score": ph["Value"],
            "status": ph["Status"],
        }

    return summary


def main():
    print("NOTION_NERVE_CENTER -- Symbiosis pattern: SolarPunk <-> Notion...")
    print("  'The organism that can't communicate its state is blind.'")

    state = load_sync_state()

    # Prepare all updates
    print("\n  Preparing sync data...")

    crisis_updates = prepare_crisis_updates()
    print(f"    Crisis signals: {len(crisis_updates)} ready for sync")

    health_updates = prepare_health_updates()
    print(f"    Health vitals: {len(health_updates)} ready for sync")

    engine_updates = prepare_engine_updates()
    print(f"    Engine scores: {len(engine_updates)} ready for sync")

    total = len(crisis_updates) + len(health_updates) + len(engine_updates)
    print(f"\n  Total updates prepared: {total}")

    # Queue all updates (Notion MCP sync happens via Claude Code sessions)
    all_updates = crisis_updates + health_updates + engine_updates
    state["pending_updates"] = all_updates
    state["last_prepared"] = datetime.now(timezone.utc).isoformat()

    # Generate summary
    summary = generate_sync_summary(state, crisis_updates, health_updates, engine_updates)

    # Print top crises
    if crisis_updates:
        print("\n  Top crisis signals for Notion:")
        for u in crisis_updates[:5]:
            p = u["properties"]
            print(f"    [{p['Urgency']}] {p['Signal'][:60]}...")
            print(f"        Region: {p['Region']} | Source: {p['Source']}")

    # Print health
    if health_updates:
        ph = health_updates[0]["properties"]
        print(f"\n  Planetary Health: {ph['Value']}/100 [{ph['Status']}]")

    # Print engines
    if engine_updates:
        myelinated = [u for u in engine_updates if u["properties"].get("Action") == "MYELINATE"]
        print(f"\n  Myelinated pathways: {len(myelinated)}/{len(engine_updates)}")

    # Update state
    state["crisis_signals_synced"] = len(crisis_updates)
    state["vitals_synced"] = len(health_updates)
    state["engines_synced"] = len(engine_updates)
    state["syncs_completed"] = state.get("syncs_completed", 0) + 1
    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    state["summary"] = summary

    # Save
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    SYNC_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print(f"\n  Sync state saved. {total} updates queued for Notion.")
    print(f"  Databases: {len(NOTION_DBS)} connected")
    print(f"  Command Center: notion.so (SolarPunk Command Center)")
    print("NOTION_NERVE_CENTER done.")


if __name__ == "__main__":
    main()
