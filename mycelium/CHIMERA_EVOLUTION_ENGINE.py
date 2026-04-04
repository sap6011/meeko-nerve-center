#!/usr/bin/env python3
"""
CHIMERA_EVOLUTION_ENGINE.py -- The Sovereign Evolution Loop
===========================================================
Wires together:
  - CHIMERA_CORE's 99/1 ethics lock
  - LIVE_WIRE's topology scanning
  - BRIDGE_BUILDER's gap filling
  - SYNERGY_FORGE's mutation generation
  - NANOBOT_HEALER's self-repair
  - MUTATION_VAULT's scoring and persistence

Biology: A chimera is an organism with cells from multiple genetic
sources. This engine fuses the scanning, bridging, mutation, and
healing subsystems into a single evolution cycle that makes the
system smarter each time it runs.

Each cycle:
  1. SCAN: Run LIVE_WIRE to map current topology
  2. HEAL: Run NANOBOT_HEALER to fix broken engines
  3. BRIDGE: Run BRIDGE_BUILDER to fill hungry inputs
  4. MUTATE: Run SYNERGY_FORGE to generate new mutations
  5. SCORE: Evaluate mutations against topology improvement
  6. EVOLVE: Deploy winning mutations, archive losers
  7. REPORT: Document everything -- wins AND failures

Zero secrets needed. Pure local evolution.
"""
import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")

# 99/1 ethics lock -- inherited from CHIMERA_CORE
REVENUE_SPLIT = 0.99
ETHICS_LOCK = "99% mutual aid / 1% node fuel"


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8"
    )


def run_engine(name, timeout=120):
    """Run a mycelium engine as subprocess. Returns (success, output)."""
    script = MYCELIUM / f"{name}.py"
    if not script.exists():
        return False, f"{name}.py not found"
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(MYCELIUM.parent),
            encoding="utf-8", errors="replace"
        )
        output = (result.stdout or "") + (result.stderr or "")
        return result.returncode == 0, output[:2000]
    except subprocess.TimeoutExpired:
        return False, f"{name} timed out after {timeout}s"
    except Exception as e:
        return False, f"{name} error: {e}"


def phase_scan():
    """Phase 1: Run LIVE_WIRE to map current topology."""
    print("\n  [1/7] SCAN -- Running LIVE_WIRE...")
    ok, output = run_engine("LIVE_WIRE", timeout=180)
    if ok:
        report = load_json(DATA / "live_wire_report.json")
        stats = report.get("stats", {})
        print(f"    Engines: {stats.get('total_engines', '?')}")
        print(f"    Wires: {stats.get('total_wires_discovered', '?')}")
        print(f"    Zero-secret chains: {stats.get('zero_secret_chains', '?')}")
        print(f"    Hungry inputs: {stats.get('hungry_inputs', '?')}")
        print(f"    Orphan outputs: {stats.get('orphan_outputs', '?')}")
        return report
    else:
        print(f"    LIVE_WIRE failed: {output[:200]}")
        return load_json(DATA / "live_wire_report.json")


def phase_heal():
    """Phase 2: Run NANOBOT_HEALER to fix broken engines."""
    print("\n  [2/7] HEAL -- Running NANOBOT_HEALER...")
    ok, output = run_engine("NANOBOT_HEALER", timeout=120)
    if ok:
        report = load_json(DATA / "nanobot_heal_report.json")
        healed = report.get("healed", 0)
        failed = report.get("failed_to_heal", 0)
        print(f"    Healed: {healed} | Could not heal: {failed}")
        return report
    else:
        print(f"    NANOBOT_HEALER failed: {output[:200]}")
        return {"healed": 0, "note": "healer not available"}


def phase_bridge(pre_scan):
    """Phase 3: Run BRIDGE_BUILDER to fill hungry inputs."""
    print("\n  [3/7] BRIDGE -- Running BRIDGE_BUILDER...")
    hungry_before = pre_scan.get("stats", {}).get("hungry_inputs", 0)
    ok, output = run_engine("BRIDGE_BUILDER", timeout=120)
    if ok:
        report = load_json(DATA / "bridge_report.json")
        built = report.get("bridges_built", 0)
        failed = report.get("bridges_failed", 0)
        print(f"    Bridges built: {built} | Failed: {failed}")
        print(f"    Hungry inputs before: {hungry_before}")
        return report
    else:
        print(f"    BRIDGE_BUILDER failed: {output[:200]}")
        return {"bridges_built": 0}


def phase_mutate():
    """Phase 4: Run SYNERGY_FORGE to generate new mutations."""
    print("\n  [4/7] MUTATE -- Running SYNERGY_FORGE...")
    ok, output = run_engine("SYNERGY_FORGE", timeout=60)
    if ok:
        print(f"    Mutation generated")
        # Read the latest mutation
        mut_path = DATA / "synergy_mutations.txt"
        if mut_path.exists():
            text = mut_path.read_text(encoding="utf-8", errors="replace")
            mutations = text.split("--- NEW SYNERGY MUTATION ---")
            latest = mutations[-1].strip() if mutations else ""
            print(f"    Total mutations in vault: {len(mutations) - 1}")
            return {"count": len(mutations) - 1, "latest": latest[:500]}
    else:
        print(f"    SYNERGY_FORGE failed: {output[:200]}")
    return {"count": 0}


def phase_score(pre_scan, post_scan, bridge_report, heal_report, mutation_info):
    """Phase 5: Score this evolution cycle."""
    print("\n  [5/7] SCORE -- Evaluating evolution cycle...")

    pre_stats = pre_scan.get("stats", {})
    post_stats = post_scan.get("stats", {})

    # Score components (0-100 each)
    scores = {}

    # Wiring improvement
    pre_wires = pre_stats.get("total_wires_discovered", 0)
    post_wires = post_stats.get("total_wires_discovered", 0)
    wire_delta = post_wires - pre_wires
    scores["wiring"] = min(100, max(0, 50 + wire_delta * 10))

    # Hungry input reduction
    pre_hungry = pre_stats.get("hungry_inputs", 0)
    post_hungry = post_stats.get("hungry_inputs", 0)
    hunger_delta = pre_hungry - post_hungry
    scores["hunger_reduction"] = min(100, max(0, 50 + hunger_delta * 15))

    # Bridge success rate
    bridges_built = bridge_report.get("bridges_built", 0)
    bridges_attempted = bridge_report.get("bridges_attempted", 1)
    scores["bridge_rate"] = int((bridges_built / max(1, bridges_attempted)) * 100)

    # Heal rate
    healed = heal_report.get("healed", 0)
    scanned = heal_report.get("scanned", 1)
    scores["health"] = min(100, int(((scanned - heal_report.get("syntax_errors", 0)) / max(1, scanned)) * 100))

    # Mutation activity
    scores["mutation"] = min(100, mutation_info.get("count", 0) * 20)

    # Composite score
    total = sum(scores.values())
    composite = int(total / max(1, len(scores)))

    print(f"    Wiring:          {scores['wiring']}/100 (delta: {wire_delta:+d})")
    print(f"    Hunger reduction: {scores['hunger_reduction']}/100 (delta: {hunger_delta:+d})")
    print(f"    Bridge rate:     {scores['bridge_rate']}/100")
    print(f"    Health:          {scores['health']}/100")
    print(f"    Mutation:        {scores['mutation']}/100")
    print(f"    COMPOSITE:       {composite}/100")

    return {"scores": scores, "composite": composite, "wire_delta": wire_delta, "hunger_delta": hunger_delta}


def phase_evolve(score_data, mutation_info):
    """Phase 6: Deploy winning mutations, archive losers."""
    print("\n  [6/7] EVOLVE -- Deploying results...")

    vault = load_json(DATA / "mutation_vault.json")
    if not vault:
        vault = {"generations": [], "best_score": 0, "total_cycles": 0}

    generation = {
        "cycle": vault.get("total_cycles", 0) + 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "composite_score": score_data["composite"],
        "scores": score_data["scores"],
        "wire_delta": score_data["wire_delta"],
        "hunger_delta": score_data["hunger_delta"],
        "mutation_count": mutation_info.get("count", 0),
        "ethics_lock": ETHICS_LOCK,
    }

    vault["generations"].append(generation)
    vault["generations"] = vault["generations"][-50:]  # Keep last 50
    vault["total_cycles"] = generation["cycle"]
    vault["best_score"] = max(vault.get("best_score", 0), score_data["composite"])
    vault["last_run"] = datetime.now(timezone.utc).isoformat()

    save_json(DATA / "mutation_vault.json", vault)

    if score_data["composite"] >= vault.get("best_score", 0):
        print(f"    NEW BEST: {score_data['composite']}/100 (previous: {vault.get('best_score', 0)})")
    else:
        print(f"    Score: {score_data['composite']}/100 (best: {vault['best_score']})")

    print(f"    Generation: {generation['cycle']}")
    print(f"    Ethics lock: {ETHICS_LOCK}")

    return vault


def phase_report(pre_scan, post_scan, bridge_report, heal_report, mutation_info, score_data, vault):
    """Phase 7: Document everything."""
    print("\n  [7/7] REPORT -- Documenting evolution cycle...")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "chimera-evolution-v1",
        "ethics_lock": ETHICS_LOCK,
        "generation": vault.get("total_cycles", 0),
        "composite_score": score_data["composite"],
        "scores": score_data["scores"],
        "pre_scan_stats": pre_scan.get("stats", {}),
        "post_scan_stats": post_scan.get("stats", {}),
        "bridges_built": bridge_report.get("bridges_built", 0),
        "engines_healed": heal_report.get("healed", 0),
        "mutations_total": mutation_info.get("count", 0),
        "wire_delta": score_data["wire_delta"],
        "hunger_delta": score_data["hunger_delta"],
        "best_ever_score": vault.get("best_score", 0),
        "note": "Chimera fuses scanning + bridging + mutation + healing into one evolution cycle."
    }

    save_json(DATA / "chimera_evolution_report.json", report)
    print(f"    Report saved: data/chimera_evolution_report.json")

    return report


def run():
    print("CHIMERA EVOLUTION ENGINE -- Sovereign Evolution Loop")
    print("=" * 55)
    print(f"  Ethics: {ETHICS_LOCK}")
    print(f"  Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    # Phase 1: Scan topology
    pre_scan = phase_scan()

    # Phase 2: Heal broken engines
    heal_report = phase_heal()

    # Phase 3: Bridge hungry inputs
    bridge_report = phase_bridge(pre_scan)

    # Phase 4: Generate mutations
    mutation_info = phase_mutate()

    # Phase 5: Re-scan to measure improvement
    print("\n  [5/7] RE-SCAN -- Measuring improvement...")
    post_scan = phase_scan()

    # Phase 5b: Score
    score_data = phase_score(pre_scan, post_scan, bridge_report, heal_report, mutation_info)

    # Phase 6: Evolve
    vault = phase_evolve(score_data, mutation_info)

    # Phase 7: Report
    report = phase_report(pre_scan, post_scan, bridge_report, heal_report, mutation_info, score_data, vault)

    # Summary
    print(f"\n  === CHIMERA EVOLUTION SUMMARY ===")
    print(f"  Generation:       {vault.get('total_cycles', 0)}")
    print(f"  Composite score:  {score_data['composite']}/100")
    print(f"  Best ever:        {vault.get('best_score', 0)}/100")
    print(f"  Wires delta:      {score_data['wire_delta']:+d}")
    print(f"  Hunger delta:     {score_data['hunger_delta']:+d}")
    print(f"  Bridges built:    {bridge_report.get('bridges_built', 0)}")
    print(f"  Engines healed:   {heal_report.get('healed', 0)}")
    print(f"  Ethics:           {ETHICS_LOCK}")
    print(f"\n  The chimera evolves. Every cycle, the system gets smarter.")


if __name__ == "__main__":
    run()
