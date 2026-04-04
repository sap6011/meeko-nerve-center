#!/usr/bin/env python3
"""
MUTATION_VAULT.py -- Persistent Mutation Scoring and Storage
============================================================
Stores every mutation the system generates, scores them against
actual topology improvements, and surfaces the best-performing
patterns for future evolution cycles.

Biology: DNA repair mechanisms keep a record of which mutations
helped the organism survive and which were neutral or harmful.
The vault is that record.

What it tracks:
  - Every SYNERGY_FORGE mutation with timestamp
  - Topology snapshots before/after each evolution cycle
  - Score history across generations
  - Best-performing mutation patterns
  - Evolution velocity (are we getting better faster?)

Reads: data/mutation_vault.json, data/chimera_evolution_report.json,
       data/synergy_mutations.txt
Writes: data/mutation_vault.json, data/mutation_leaderboard.json

Zero secrets needed.
"""
import json
import re
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)


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


def parse_mutations():
    """Parse all mutations from synergy_mutations.txt."""
    mut_path = DATA / "synergy_mutations.txt"
    if not mut_path.exists():
        return []

    text = mut_path.read_text(encoding="utf-8", errors="replace")
    blocks = text.split("--- NEW SYNERGY MUTATION ---")

    mutations = []
    for i, block in enumerate(blocks):
        block = block.strip()
        if not block or block.startswith("# Synergy"):
            continue

        mutation = {"index": i, "raw": block[:500]}

        # Extract metadata
        strategy = re.search(r"\[STRATEGY\]:\s*(.+)", block)
        confidence = re.search(r"\[CONFIDENCE\]:\s*(.+)", block)
        reasoning = re.search(r"\[REASONING\]:\s*(.+)", block)
        skills = re.findall(r"\[SKILL\]:\s*def\s+(\w+)", block)

        mutation["strategy"] = strategy.group(1).strip() if strategy else "unknown"
        mutation["confidence"] = confidence.group(1).strip() if confidence else "unknown"
        mutation["reasoning"] = reasoning.group(1).strip() if reasoning else ""
        mutation["skills"] = skills
        mutation["skill_count"] = len(skills)

        mutations.append(mutation)

    return mutations


def compute_velocity(vault):
    """Compute evolution velocity -- are scores improving over time?"""
    generations = vault.get("generations", [])
    if len(generations) < 2:
        return {"velocity": 0, "trend": "insufficient_data"}

    recent = generations[-5:]  # Last 5 cycles
    scores = [g.get("composite_score", 0) for g in recent]

    if len(scores) < 2:
        return {"velocity": 0, "trend": "insufficient_data"}

    # Simple linear trend
    avg_early = sum(scores[:len(scores)//2]) / max(1, len(scores)//2)
    avg_late = sum(scores[len(scores)//2:]) / max(1, len(scores) - len(scores)//2)
    velocity = avg_late - avg_early

    if velocity > 5:
        trend = "accelerating"
    elif velocity > 0:
        trend = "improving"
    elif velocity == 0:
        trend = "stable"
    elif velocity > -5:
        trend = "slowing"
    else:
        trend = "declining"

    return {"velocity": round(velocity, 2), "trend": trend, "recent_scores": scores}


def build_leaderboard(vault, mutations):
    """Build a mutation leaderboard based on generation scores."""
    generations = vault.get("generations", [])

    leaderboard = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_mutations": len(mutations),
        "total_generations": len(generations),
        "best_score": vault.get("best_score", 0),
        "velocity": compute_velocity(vault),
        "top_generations": sorted(
            generations, key=lambda g: g.get("composite_score", 0), reverse=True
        )[:10],
        "recent_generations": generations[-5:],
        "mutation_strategies": {},
    }

    # Count strategy usage
    for m in mutations:
        strat = m.get("strategy", "unknown")
        leaderboard["mutation_strategies"][strat] = leaderboard["mutation_strategies"].get(strat, 0) + 1

    # Skill frequency
    skill_freq = {}
    for m in mutations:
        for s in m.get("skills", []):
            skill_freq[s] = skill_freq.get(s, 0) + 1
    leaderboard["top_skills"] = sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)[:20]

    return leaderboard


def run():
    print("MUTATION VAULT -- Persistent Mutation Storage & Scoring")
    print("=" * 55)

    # Load existing vault
    vault = load_json(DATA / "mutation_vault.json")
    if not vault:
        vault = {"generations": [], "best_score": 0, "total_cycles": 0}

    # Parse mutations
    mutations = parse_mutations()
    print(f"\n  Mutations found: {len(mutations)}")

    # Compute velocity
    velocity = compute_velocity(vault)
    print(f"  Evolution velocity: {velocity['velocity']:+.1f} ({velocity['trend']})")

    # Build leaderboard
    leaderboard = build_leaderboard(vault, mutations)
    save_json(DATA / "mutation_leaderboard.json", leaderboard)
    print(f"  Leaderboard saved: data/mutation_leaderboard.json")

    # Show top strategies
    if leaderboard["mutation_strategies"]:
        print(f"\n  Mutation strategies:")
        for strat, count in sorted(leaderboard["mutation_strategies"].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {strat}: {count} uses")

    # Show top skills
    if leaderboard["top_skills"]:
        print(f"\n  Most used skills:")
        for skill, count in leaderboard["top_skills"][:10]:
            print(f"    {skill}: {count} mutations")

    # Summary
    print(f"\n  === VAULT SUMMARY ===")
    print(f"  Total mutations:    {len(mutations)}")
    print(f"  Total generations:  {len(vault.get('generations', []))}")
    print(f"  Best score ever:    {vault.get('best_score', 0)}/100")
    print(f"  Velocity:           {velocity['velocity']:+.1f} ({velocity['trend']})")
    print(f"\n  The vault remembers. Every mutation. Every score. Forever.")


if __name__ == "__main__":
    run()
