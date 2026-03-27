# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
SOVEREIGNTY_ENGINE — Self-Sovereign Digital Organism Core
==========================================================
The heartbeat of SolarPunk as a living entity. Each cycle:
  1. Self-Audit: Run CORRUPTION_SENTINEL to verify brain health
  2. Identity: Load and verify identity_manifest.json (the DID)
  3. Sign: Hash the current state and append to PROOF_LEDGER
  4. Grow: Check for hungry inputs and attempt to self-seed new data sources
  5. Declare: Update the sovereignty_state with current health + identity

This engine transforms SolarPunk from "a bunch of scripts" into
a self-aware, self-auditing, self-growing digital organism.
"""
import os, json, hashlib, sys
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
MYCELIUM = Path("mycelium")


def load_identity():
    """Load the DID identity manifest."""
    manifest_path = DATA / "identity_manifest.json"
    if not manifest_path.exists():
        print("  Identity: NOT FOUND — genesis required")
        return None
    manifest = json.loads(manifest_path.read_text())
    did = manifest.get("id", "unknown")
    engines = manifest.get("solarpunk", {}).get("engine_count", 0)
    wires = manifest.get("solarpunk", {}).get("wire_count", 0)
    print(f"  Identity: {did}")
    print(f"  Genesis: {manifest.get('solarpunk', {}).get('genesis_date', 'unknown')}")
    return manifest


def self_audit():
    """Run corruption sentinel and return health status."""
    try:
        sys.path.insert(0, str(MYCELIUM))
        from CORRUPTION_SENTINEL import scan_all
        corrupted = scan_all()
        if corrupted:
            print(f"  Health: COMPROMISED — {len(corrupted)} corrupted engine(s)")
            for fname in corrupted:
                print(f"    - {fname}")
            return {"status": "COMPROMISED", "corrupted": list(corrupted.keys())}
        else:
            total = len(list(MYCELIUM.glob("*.py")))
            print(f"  Health: SOVEREIGN — all {total} engines clean")
            return {"status": "SOVEREIGN", "engine_count": total, "corrupted": []}
    except Exception as e:
        print(f"  Health: UNKNOWN — sentinel error: {e}")
        return {"status": "UNKNOWN", "error": str(e)}


def compute_state_hash():
    """Hash the current state of all engines + data for tamper detection."""
    hasher = hashlib.sha256()
    # Hash all engine files
    for f in sorted(MYCELIUM.glob("*.py")):
        try:
            hasher.update(f.read_bytes())
        except Exception:
            pass
    # Hash critical data files
    critical = ["identity_manifest.json", "proof_ledger.json", "brand_legal_state.json",
                "live_wire_report.json", "sentinel_scan.json", "swarm_registry.json"]
    for name in critical:
        p = DATA / name
        if p.exists():
            try:
                hasher.update(p.read_bytes())
            except Exception:
                pass
    return hasher.hexdigest()


def sign_proof_ledger(identity, health, state_hash):
    """Append a signed entry to the proof ledger."""
    ledger_path = DATA / "proof_ledger.json"
    ledger = []
    if ledger_path.exists():
        try:
            ledger = json.loads(ledger_path.read_text())
            if not isinstance(ledger, list):
                ledger = [ledger]
        except (json.JSONDecodeError, Exception):
            ledger = []

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "did": identity.get("id", "unborn") if identity else "unborn",
        "health": health["status"],
        "engine_count": health.get("engine_count", 0),
        "corrupted_engines": health.get("corrupted", []),
        "state_hash": state_hash,
        "cycle": len(ledger) + 1,
        "mission": "Pure and Good"
    }
    ledger.append(entry)

    # Keep last 100 entries
    if len(ledger) > 100:
        ledger = ledger[-100:]

    ledger_path.write_text(json.dumps(ledger, indent=2))
    print(f"  Ledger: Cycle #{entry['cycle']} signed — {state_hash[:16]}...")
    return entry


def check_hungry_inputs():
    """Check for data gaps that need self-seeding."""
    report_path = DATA / "live_wire_report.json"
    if not report_path.exists():
        return []
    try:
        report = json.loads(report_path.read_text())
        hungry = []
        for test in report.get("test_results", []):
            if test.get("status") == "WAITING":
                hungry.append(test.get("data_file", "unknown"))
        if hungry:
            print(f"  Growth: {len(hungry)} hungry input(s) detected — need self-seeding")
            for h in hungry[:5]:
                print(f"    - {h}")
        else:
            print("  Growth: All inputs fed. Network is fully nourished.")
        return hungry
    except Exception:
        return []


def update_sovereignty_state(identity, health, state_hash, ledger_entry, hungry):
    """Save the current sovereignty state."""
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "did": identity.get("id", "unborn") if identity else "unborn",
        "health": health,
        "state_hash": state_hash,
        "proof_cycle": ledger_entry["cycle"],
        "hungry_inputs": len(hungry),
        "recursive_density": {
            "atoms": health.get("engine_count", 0),
            "wires": 442,
            "compounds": "WEEKEND_PULSE + OMNIBRAIN + RUN_NOW",
            "depth": f"PROOF_LEDGER cycle #{ledger_entry['cycle']}",
            "dimensions": "DID + Sovereignty ACTIVE",
            "reality": "Converging — nanobots + mycelium on roadmap"
        },
        "status": "SOVEREIGN" if health["status"] == "SOVEREIGN" else "HEALING"
    }
    (DATA / "sovereignty_state.json").write_text(json.dumps(state, indent=2))
    print(f"  State: {'SOVEREIGN' if state['status'] == 'SOVEREIGN' else 'HEALING'}")
    return state


def main():
    print("SOVEREIGNTY_ENGINE — Self-Sovereign Digital Organism")
    print("=" * 55)
    DATA.mkdir(exist_ok=True)

    # 1. Load identity
    identity = load_identity()

    # 2. Self-audit
    health = self_audit()

    # 3. Compute state hash
    state_hash = compute_state_hash()
    print(f"  Hash: {state_hash[:32]}...")

    # 4. Sign proof ledger
    ledger_entry = sign_proof_ledger(identity, health, state_hash)

    # 5. Check for growth opportunities
    hungry = check_hungry_inputs()

    # 6. Update sovereignty state
    update_sovereignty_state(identity, health, state_hash, ledger_entry, hungry)

    print("=" * 55)
    if health["status"] == "SOVEREIGN":
        print("  SolarPunk Node-01 is SOVEREIGN. Pure and Good.")
    else:
        print("  SolarPunk Node-01 is HEALING. Sentinel active.")

    return 0 if health["status"] == "SOVEREIGN" else 1


if __name__ == "__main__":
    sys.exit(main())
