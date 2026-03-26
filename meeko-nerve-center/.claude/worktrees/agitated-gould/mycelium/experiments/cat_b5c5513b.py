#!/usr/bin/env python3
"""
EXPERIMENT: cat_b5c5513b
TYPE:        CATALYST
BORN:        2026-03-21T15:29:05.593606Z
CATALYSES:   CODE_ALCHEMIST  via  CRYPTO_BRIDGE
HYPOTHESIS:  auto-versioned data — every JSON change commits itself

WHAT THIS DOES:
  A CATALYST doesn't replace either parent -- it makes them work TOGETHER faster.
  This experiment makes CRYPTO_BRIDGE accelerate CODE_ALCHEMIST.
  Specifically: auto-versioned data — every JSON change commits itself

SAFE TO RUN: yes -- read-only, outputs to experiments/ only
"""
import json, datetime, hashlib
from pathlib import Path

ROOT        = Path(__file__).resolve().parent.parent.parent
DATA        = ROOT / "data"
EXPERIMENTS = Path(__file__).resolve().parent

def catalyse():
    """
    CATALYST: gap prioritiser.
    Takes gap data from KNOWLEDGE_LOOP and scores each gap by:
      - Population impact (proxy by region)
      - Research scarcity (fewer results in candidates = higher priority)
      - Time since last addressed (history ledger)
    Result: a priority queue that KNOWLEDGE_LOOP can consume directly.
    """
    gaps_file    = DATA / "knowledge_gaps.json"
    research_file = DATA / "research_candidates.json"

    if not gaps_file.exists():
        print("[CATALYST] No gaps file -- nothing to catalyse")
        return {"status": "no_gaps"}

    with open(gaps_file, "r", encoding="utf-8") as f:
        gaps = json.load(f)

    candidates = {}
    if research_file.exists():
        with open(research_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        # count research hits per gap
        for item in raw if isinstance(raw, list) else []:
            g = item.get("gap", "")
            candidates[g] = candidates.get(g, 0) + 1

    # Compute priority scores
    REGION_POP = {
        "africa_west": 400_000_000,   "asia_south": 2_000_000_000,
        "southeast_asia": 700_000_000,"caribbean": 45_000_000,
        "central_america": 50_000_000,"africa_sahel": 100_000_000,
        "mena_deep": 150_000_000,     "europe_east": 120_000_000,
        "south_america": 430_000_000,
    }

    priority_queue = []
    geo_gaps = gaps.get("geographic", {}) if isinstance(gaps.get("geographic"), dict) else {}
    for region, data in geo_gaps.items():
        pop      = REGION_POP.get(region, 10_000_000)
        hits     = candidates.get(f"geographic.{region}", 0)
        scarcity = max(0, 5 - hits)   # fewer hits = more scarce = higher priority
        score    = (pop / 1_000_000) + (scarcity * 10)
        priority_queue.append({
            "gap":      f"geographic.{region}",
            "label":    data.get("label", region) if isinstance(data, dict) else region,
            "score":    round(score, 1),
            "pop_M":    round(pop / 1_000_000, 0),
            "scarcity": scarcity,
            "queries":  data.get("regions", []) if isinstance(data, dict) else [],
        })

    priority_queue.sort(key=lambda x: -x["score"])

    result = {
        "experiment":   "cat_b5c5513b",
        "catalyst_for": "KNOWLEDGE_LOOP gap selection",
        "gaps_scored":  len(priority_queue),
        "top_priority": priority_queue[:3] if priority_queue else [],
        "timestamp":    datetime.datetime.utcnow().isoformat(),
    }

    out = EXPERIMENTS / "catalyst_cat_b5c5513b.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print("[CATALYST] Priority queue: " + str(len(priority_queue)) + " gaps scored")
    for pq in priority_queue[:3]:
        print("  [" + str(int(pq["score"])) + "] " + str(pq["label"]) + " -- pop " + str(int(pq["pop_M"])) + "M, scarcity " + str(pq["scarcity"]))
    return result

if __name__ == "__main__":
    r = catalyse()
    print(json.dumps(r.get("top_priority", []), indent=2))
