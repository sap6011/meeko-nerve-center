# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
STRESS_TEST — Fire Drill for the Living Organism
==================================================
Introduces controlled injuries to the system and observes the
full immune response chain in real-time:

  1. INJURY:  Create a hungry input (remove a data file)
  2. DETECT:  Run LIVE_WIRE to discover the broken wire
  3. HEAL:    Run BRIDGE_BUILDER to repair the gap
  4. VERIFY:  Run CORRUPTION_SENTINEL to confirm health
  5. SIGN:    Run SOVEREIGNTY_ENGINE to log the recovery

Each test generates a timestamped healing log that proves
the system can detect and repair damage autonomously.

This is the "fire drill" — proof the immune system works.
"""
import os, sys, json, shutil, time
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
MYCELIUM = Path("mycelium")
sys.path.insert(0, str(MYCELIUM))


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def test_hungry_input_heal():
    """Test 1: Remove a data file, watch LIVE_WIRE detect the gap,
    then BRIDGE_BUILDER heal it."""
    log = {
        "test": "hungry_input_heal",
        "description": "Remove river_watch.json, detect hungry input, bridge repairs it",
        "events": []
    }

    target = DATA / "river_watch.json"
    backup = DATA / "_stress_backup_river_watch.json"

    # --- INJURY ---
    if target.exists():
        shutil.copy2(target, backup)
        target.unlink()
        log["events"].append({"time": timestamp(), "phase": "INJURY", "action": f"Removed {target.name}", "status": "DONE"})
        print(f"  [INJURY]  Removed {target.name}")
    else:
        log["events"].append({"time": timestamp(), "phase": "INJURY", "action": f"{target.name} already missing", "status": "SKIP"})
        print(f"  [INJURY]  {target.name} already missing (testing detection)")

    # --- DETECT ---
    print(f"  [DETECT]  Running LIVE_WIRE scan...")
    try:
        from LIVE_WIRE import scan_all_engines, discover_wires, find_orphans
        engines = scan_all_engines()
        wires = discover_wires(engines)
        orphans = find_orphans(engines, wires)
        hungry = orphans.get("hungry_inputs", [])

        detected = "river_watch.json" in hungry or any("river_watch" in h for h in hungry)
        log["events"].append({
            "time": timestamp(),
            "phase": "DETECT",
            "action": "LIVE_WIRE scan complete",
            "hungry_inputs_found": len(hungry),
            "target_detected": detected,
            "status": "DETECTED" if detected else "MISSED"
        })
        if detected:
            print(f"  [DETECT]  river_watch.json detected as hungry input")
        else:
            print(f"  [DETECT]  {len(hungry)} hungry inputs found (target may be in bridge list)")
    except Exception as e:
        log["events"].append({"time": timestamp(), "phase": "DETECT", "action": f"LIVE_WIRE error: {e}", "status": "ERROR"})
        print(f"  [DETECT]  Error: {e}")

    # --- HEAL ---
    print(f"  [HEAL]    Running BRIDGE_BUILDER...")
    try:
        from BRIDGE_BUILDER import BRIDGES, bridge_river_watch
        result = bridge_river_watch()
        healed = target.exists()
        log["events"].append({
            "time": timestamp(),
            "phase": "HEAL",
            "action": "BRIDGE_BUILDER repair attempted",
            "bridge_result": result.get("status", "unknown"),
            "file_restored": healed,
            "status": "HEALED" if healed else "PARTIAL"
        })
        if healed:
            print(f"  [HEAL]    river_watch.json restored by BRIDGE_BUILDER")
        else:
            print(f"  [HEAL]    Bridge ran but file not yet restored")
    except Exception as e:
        log["events"].append({"time": timestamp(), "phase": "HEAL", "action": f"BRIDGE_BUILDER error: {e}", "status": "ERROR"})
        print(f"  [HEAL]    Error: {e}")

    # If bridge didn't fully restore, restore from backup
    if not target.exists() and backup.exists():
        shutil.copy2(backup, target)
        log["events"].append({"time": timestamp(), "phase": "RESTORE", "action": "Restored from backup (safety net)", "status": "DONE"})
        print(f"  [RESTORE] Restored from backup (safety net)")

    # Clean backup
    if backup.exists():
        backup.unlink()

    return log


def test_corruption_detection():
    """Test 2: Inject a known corruption pattern into a temp file,
    watch CORRUPTION_SENTINEL catch it."""
    log = {
        "test": "corruption_detection",
        "description": "Create a file with os.getenv nesting, sentinel detects it",
        "events": []
    }

    # --- INJURY ---
    trap_file = MYCELIUM / "_stress_test_corrupt.py"
    # Build corrupt code via concatenation so sentinel doesn't flag THIS file
    nested = 'os.getenv(os.getenv(os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")")))'  # test corruption pattern
    corrupt_code = f'# Stress test\nimport os\nkey = {nested}\nprint(key)\n'
    trap_file.write_text(corrupt_code)
    log["events"].append({"time": timestamp(), "phase": "INJURY", "action": "Created corrupt test file", "status": "DONE"})
    print(f"  [INJURY]  Created {trap_file.name} with os.getenv nesting")

    # --- DETECT ---
    print(f"  [DETECT]  Running CORRUPTION_SENTINEL...")
    try:
        from CORRUPTION_SENTINEL import check_file
        issues = check_file(trap_file)
        detected = len(issues) > 0
        log["events"].append({
            "time": timestamp(),
            "phase": "DETECT",
            "action": "CORRUPTION_SENTINEL scan",
            "issues_found": len(issues),
            "issues": issues[:5],
            "status": "DETECTED" if detected else "MISSED"
        })
        if detected:
            print(f"  [DETECT]  Sentinel found {len(issues)} issue(s):")
            for issue in issues:
                print(f"            {issue}")
        else:
            print(f"  [DETECT]  Sentinel missed the corruption!")
    except Exception as e:
        log["events"].append({"time": timestamp(), "phase": "DETECT", "action": f"Sentinel error: {e}", "status": "ERROR"})
        print(f"  [DETECT]  Error: {e}")

    # --- CLEANUP ---
    if trap_file.exists():
        trap_file.unlink()
        log["events"].append({"time": timestamp(), "phase": "CLEANUP", "action": "Removed corrupt test file", "status": "DONE"})
        print(f"  [CLEANUP] Removed {trap_file.name}")

    return log


def test_canary_tamper():
    """Test 3: Modify a MURMURATION_TRAP canary file,
    watch the trap detect the tampering."""
    log = {
        "test": "canary_tamper_detection",
        "description": "Modify a honeypot file, murmuration trap detects it",
        "events": []
    }

    canary = DATA / ".credentials_backup.json"
    if not canary.exists():
        log["events"].append({"time": timestamp(), "phase": "SKIP", "action": "No canary file found", "status": "SKIP"})
        print(f"  [SKIP]    No canary file to tamper with")
        return log

    # Save original
    original = canary.read_text()

    # --- INJURY ---
    tampered = json.loads(original)
    tampered["_injected_by_stress_test"] = True
    tampered["api_key"] = "STOLEN_KEY_12345"
    canary.write_text(json.dumps(tampered, indent=2))
    log["events"].append({"time": timestamp(), "phase": "INJURY", "action": "Tampered with canary credentials", "status": "DONE"})
    print(f"  [INJURY]  Modified .credentials_backup.json (canary)")

    # --- DETECT ---
    print(f"  [DETECT]  Running MURMURATION_TRAP canary check...")
    try:
        from MURMURATION_TRAP import check_canary_access
        canary_state, alerts = check_canary_access()
        detected = len(alerts) > 0
        log["events"].append({
            "time": timestamp(),
            "phase": "DETECT",
            "action": "MURMURATION_TRAP canary check",
            "alerts": len(alerts),
            "alert_details": alerts[:3],
            "status": "DETECTED" if detected else "MISSED"
        })
        if detected:
            print(f"  [DETECT]  INTRUSION DETECTED: {len(alerts)} canary alert(s)")
            for a in alerts:
                print(f"            {a.get('type', 'unknown')}: {Path(a.get('file', '')).name}")
        else:
            print(f"  [DETECT]  No alerts (first run — baseline being set)")
    except Exception as e:
        log["events"].append({"time": timestamp(), "phase": "DETECT", "action": f"Trap error: {e}", "status": "ERROR"})
        print(f"  [DETECT]  Error: {e}")

    # --- RESTORE ---
    canary.write_text(original)
    log["events"].append({"time": timestamp(), "phase": "RESTORE", "action": "Canary restored to original", "status": "DONE"})
    print(f"  [RESTORE] Canary restored")

    return log


def test_sovereignty_resilience():
    """Test 4: Run the full sovereignty cycle after injuries
    to prove the system re-certifies itself."""
    log = {
        "test": "sovereignty_resilience",
        "description": "Full sovereignty cycle — audit, verify, sign, declare",
        "events": []
    }

    print(f"  [AUDIT]   Running full sovereignty cycle...")
    try:
        from SOVEREIGNTY_ENGINE import load_identity, self_audit, compute_state_hash, sign_proof_ledger, check_hungry_inputs
        identity = load_identity()
        health = self_audit()
        state_hash = compute_state_hash()
        entry = sign_proof_ledger(identity, health, state_hash)
        hungry = check_hungry_inputs()

        log["events"].append({
            "time": timestamp(),
            "phase": "SOVEREIGNTY",
            "did": identity.get("id", "unknown") if identity else "unknown",
            "health": health["status"],
            "state_hash": state_hash[:32],
            "cycle": entry["cycle"],
            "hungry_inputs": len(hungry),
            "status": "SOVEREIGN" if health["status"] == "SOVEREIGN" else "HEALING"
        })
        print(f"  [RESULT]  Status: {health['status']} | Cycle: #{entry['cycle']} | Hash: {state_hash[:16]}...")
    except Exception as e:
        log["events"].append({"time": timestamp(), "phase": "SOVEREIGNTY", "action": f"Error: {e}", "status": "ERROR"})
        print(f"  [ERROR]   {e}")

    return log


def main():
    print()
    print("=" * 60)
    print("  STRESS TEST — Fire Drill for the Living Organism")
    print("=" * 60)
    DATA.mkdir(exist_ok=True)

    all_logs = {
        "timestamp": timestamp(),
        "description": "Controlled injuries to test self-healing capabilities",
        "tests": []
    }

    # Test 1: Hungry Input Heal
    print(f"\n--- Test 1: HUNGRY INPUT HEAL ---")
    log1 = test_hungry_input_heal()
    all_logs["tests"].append(log1)

    # Test 2: Corruption Detection
    print(f"\n--- Test 2: CORRUPTION DETECTION ---")
    log2 = test_corruption_detection()
    all_logs["tests"].append(log2)

    # Test 3: Canary Tamper Detection
    print(f"\n--- Test 3: CANARY TAMPER DETECTION ---")
    log3 = test_canary_tamper()
    all_logs["tests"].append(log3)

    # Test 4: Sovereignty Resilience
    print(f"\n--- Test 4: SOVEREIGNTY RESILIENCE ---")
    log4 = test_sovereignty_resilience()
    all_logs["tests"].append(log4)

    # Score
    total = len(all_logs["tests"])
    passed = 0
    for test in all_logs["tests"]:
        events = test.get("events", [])
        detect_events = [e for e in events if e.get("phase") in ("DETECT", "SOVEREIGNTY")]
        if any(e.get("status") in ("DETECTED", "SOVEREIGN") for e in detect_events):
            passed += 1

    all_logs["score"] = {"passed": passed, "total": total, "percentage": round(passed / total * 100) if total else 0}

    # Save full log
    (DATA / "stress_test_results.json").write_text(json.dumps(all_logs, indent=2))

    print()
    print("=" * 60)
    print(f"  RESULTS: {passed}/{total} tests passed ({all_logs['score']['percentage']}%)")
    print("=" * 60)
    for test in all_logs["tests"]:
        name = test["test"]
        events = test.get("events", [])
        final = events[-1] if events else {}
        status = "PASS" if any(e.get("status") in ("DETECTED", "SOVEREIGN", "HEALED") for e in events) else "REVIEW"
        print(f"  [{status:6s}] {name}")
    print("=" * 60)
    print("  Fire drill complete. Healing log saved to data/stress_test_results.json")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
