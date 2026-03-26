#!/usr/bin/env python3
"""
EXPERIMENT: mut_03e0c0c5
TYPE:        MUTATION
BORN:        2026-03-21T15:26:42.031081Z
PARENT:      CODE_ALCHEMIST
MUTATION OF: json_io, http_fetch, file_io, git_ops, loop_engine
HYPOTHESIS:  self-warming loop that deepens its own KB

WHAT THIS DOES:
  Takes the core pattern from CODE_ALCHEMIST and evolves a new variant.
  Original patterns: json_io, http_fetch, file_io, git_ops, loop_engine
  Mutation vector:   json_io, http_fetch, file_io, git_ops, loop_engine (from LEGACY_SIFTED_ultimate_ai_self)
  Result: a hybrid that does what CODE_ALCHEMIST does but through a LEGACY_SIFTED_ultimate_ai_self lens.

SAFE TO RUN: yes -- outputs to stdout + experiments/ only
"""
import json, hashlib, datetime, sys
from pathlib import Path

ROOT        = Path(__file__).resolve().parent.parent.parent
DATA        = ROOT / "data"
EXPERIMENTS = Path(__file__).resolve().parent

def mutate_gap_detector():
    """
    MUTATION: gap detection evolved with scoring lens.
    Original (KNOWLEDGE_LOOP): detects geographic gaps as flat list.
    Mutation: scores gaps by urgency, population impact, research scarcity.
    """
    gaps_file = DATA / "knowledge_gaps.json"
    kb_file   = DATA / "solarpunk_knowledge.json"

    if not gaps_file.exists():
        print("[MUTATION] No gaps file yet -- creating seed")
        gaps = {"geographic": [], "categorical": [], "history": []}
    else:
        with open(gaps_file, "r", encoding="utf-8") as f:
            gaps = json.load(f)

    covered = []
    if kb_file.exists():
        with open(kb_file, "r", encoding="utf-8") as f:
            kb = json.load(f)
        covered = [p.get("location", {}).get("country", "") for p in kb.get("projects", [])]

    # Score every gap by urgency
    URGENCY_WEIGHTS = {
        "South Asia":     10,  # 2 billion people, near-zero coverage
        "Southeast Asia":  9,
        "West Africa":     8,
        "Sahel":           9,  # climate frontline
        "Caribbean":       7,  # hurricane resilience urgency
        "Central America": 6,
        "Eastern Europe":  5,
    }

    scored_gaps = []
    for region, data in (gaps.get("geographic") or {}).items() if isinstance(gaps.get("geographic"), dict) else []:
        urgency  = URGENCY_WEIGHTS.get(data.get("label", region), 3)
        pop_est  = urgency * 200_000_000  # rough proxy
        scored_gaps.append({
            "region":    region,
            "label":     data.get("label", region),
            "urgency":   urgency,
            "pop_proxy": pop_est,
            "queries":   data.get("regions", []),
        })

    scored_gaps.sort(key=lambda x: -x["urgency"])

    result = {
        "experiment":    "mut_03e0c0c5",
        "mutation_type": "gap_urgency_scorer",
        "gaps_scored":   len(scored_gaps),
        "top_3":         scored_gaps[:3],
        "covered_count": len([c for c in covered if c]),
        "timestamp":     datetime.datetime.utcnow().isoformat(),
    }

    out = EXPERIMENTS / "mutation_mut_03e0c0c5.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"[MUTATION] Gap urgency scores written to {out.name}")
    print(f"  Top gap: {scored_gaps[0]['label'] if scored_gaps else 'none'}")
    return result

if __name__ == "__main__":
    r = mutate_gap_detector()
    print(json.dumps(r, indent=2))
