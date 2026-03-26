#!/usr/bin/env python3
"""
EXPERIMENT: chi_fce39a35
TYPE:        CHIMERA
BORN:        2026-03-21T15:26:07.451026Z
PARENTS:     CODE_ALCHEMIST  +  LEGACY_SIFTED_ultimate_ai_self_1
HYPOTHESIS:  gap-aware synthesis — detects what's missing then fills it

WHAT THIS DOES:
  Three-headed hybrid: reads knowledge (CODE_ALCHEMIST), detects gaps,
  then generates synthesis candidates -- all in one pass.
  This is the gap-aware synthesis chimera.

SAFE TO RUN: yes -- read-only on existing data, writes to experiments/ only
"""
import json, itertools, datetime, hashlib
from pathlib import Path

ROOT        = Path(__file__).resolve().parent.parent.parent
DATA        = ROOT / "data"
EXPERIMENTS = Path(__file__).resolve().parent

def chimera_run():
    kb_file  = DATA / "solarpunk_knowledge.json"
    syn_file = DATA / "solarpunk_synthesis.json"

    if not kb_file.exists():
        print("[CHIMERA] No KB yet -- nothing to combine")
        return {"status": "no_kb"}

    with open(kb_file, "r", encoding="utf-8") as f:
        kb = json.load(f)

    projects  = kb.get("projects", [])
    cats      = list(set(p.get("category", "") for p in projects if p.get("category")))
    countries = list(set(p.get("location", {}).get("country", "") for p in projects))

    # HEAD 1: read what exists
    existing_ids = set(p.get("id", "") for p in projects)

    # HEAD 2: detect pattern gaps -- what category combos are MISSING?
    all_combos = list(itertools.combinations(cats, 2))
    existing_synths = []
    if syn_file.exists():
        with open(syn_file, "r", encoding="utf-8") as f:
            existing_synths = json.load(f)
    covered_combos = set()
    for s in existing_synths:
        reqs = tuple(sorted(s.get("requires", [])))
        covered_combos.add(reqs)

    novel_combos = [c for c in all_combos if tuple(sorted(c)) not in covered_combos]

    # HEAD 3: generate synthesis hypotheses for novel combos
    hypotheses = []
    for a, b in novel_combos[:6]:
        proj_a = [p for p in projects if p.get("category") == a]
        proj_b = [p for p in projects if p.get("category") == b]
        if not proj_a or not proj_b:
            continue
        hyp = {
            "chimera_id":   f"chimera_{hashlib.md5((a+b).encode()).hexdigest()[:6]}",
            "combines":     [a, b],
            "example_a":    proj_a[0].get("name", a),
            "example_b":    proj_b[0].get("name", b),
            "hypothesis":   (
                f"A community that runs both {proj_a[0].get('name', a)} AND "
                f"{proj_b[0].get('name', b)} simultaneously creates a "
                f"{a.replace('_',' ')} + {b.replace('_',' ')} hybrid "
                f"where each system feeds the other."
            ),
            "potential_locations": list(set(countries[:4])),
        }
        hypotheses.append(hyp)

    result = {
        "experiment":       "chi_fce39a35",
        "chimera_type":     "gap_aware_synthesis",
        "projects_read":    len(projects),
        "categories_found": len(cats),
        "novel_combos":     len(novel_combos),
        "hypotheses":       hypotheses,
        "timestamp":        datetime.datetime.utcnow().isoformat(),
    }

    out = EXPERIMENTS / "chimera_chi_fce39a35.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"[CHIMERA] {len(hypotheses)} novel synthesis hypotheses generated")
    for h in hypotheses[:3]:
        print(f"  - {h['combines'][0]} + {h['combines'][1]}")
    return result

if __name__ == "__main__":
    r = chimera_run()
    print(f"\n[CHIMERA] Done: {r.get('novel_combos', 0)} novel combos found")
