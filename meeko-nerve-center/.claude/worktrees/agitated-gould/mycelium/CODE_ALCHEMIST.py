#!/usr/bin/env python3
"""
CODE_ALCHEMIST.py -- Digital Alchemy Engine for SolarPunk
==========================================================
Discovers what can be combined into something NEW.
Takes two (or more) existing code patterns, synthesizes a hybrid,
tests it safely, and commits working experiments to mycelium/experiments/.

RULES OF ALCHEMY:
  - NEVER modifies existing files. Only creates new ones.
  - All experiments run in try/except sandboxes -- crash = log + skip
  - Max 3 new experiments per cycle (volatility budget)
  - New files go in mycelium/experiments/
  - Must pass syntax check before being saved
  - Must produce some non-trivial output when run standalone
  - Nothing network-calling without ALLOW_NETWORK=true env var
  - Every experiment is annotated with what it combined and why

ALCHEMY CATEGORIES:
  - FUSION    : merge two engines into one unified tool
  - MUTATION  : take one engine, evolve a new variant
  - CHIMERA   : combine patterns from 3+ sources into hybrid architecture
  - CATALYST  : make one engine accelerate/enhance another
  - RESONANCE : find two tools that share hidden structure, make it explicit

LOOP: runs every 12h via SOLARPUNK_LOOP.yml
      or: python mycelium/CODE_ALCHEMIST.py
"""

import ast
import os
import sys
import json
import time
import random
import hashlib
import inspect
import importlib
import traceback
import subprocess
import datetime
from pathlib import Path
from typing import Any

ROOT        = Path(__file__).resolve().parent.parent
MYCELIUM    = ROOT / "mycelium"
EXPERIMENTS = MYCELIUM / "experiments"
DATA        = ROOT / "data"
LOG_FILE    = DATA / "alchemy_log.jsonl"
LEDGER_FILE = DATA / "alchemy_ledger.json"

EXPERIMENTS.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

VOLATILITY_BUDGET = 3   # max new experiments per cycle
ALLOW_NETWORK     = os.getenv("ALLOW_NETWORK", "false").lower() == "true"

# ── Colour codes for terminal (stripped on Windows if needed) ────────────────
def _c(code, text): return f"\033[{code}m{text}\033[0m" if sys.platform != "win32" else text
GOLD   = lambda t: _c("33",  t)
GREEN  = lambda t: _c("32",  t)
CYAN   = lambda t: _c("36",  t)
RED    = lambda t: _c("31",  t)
DIM    = lambda t: _c("2",   t)
BOLD   = lambda t: _c("1",   t)

def log(msg): print(f"[ALCHEMIST] {msg}", flush=True)

# ============================================================
# STEP 1 — SCAN: read every Python file in mycelium/
# ============================================================

def scan_codebase() -> list[dict]:
    """
    Parse every .py file in mycelium/ (excluding experiments/).
    Extract: name, path, functions, classes, docstring, patterns.
    """
    modules = []
    for p in MYCELIUM.rglob("*.py"):
        if "experiments" in str(p) or "__pycache__" in str(p):
            continue
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(src)
            funcs   = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            imports = [ast.dump(n) for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
            doc = ast.get_docstring(tree) or ""
            patterns = _extract_patterns(src)
            modules.append({
                "name":     p.stem,
                "path":     str(p),
                "rel":      str(p.relative_to(ROOT)),
                "funcs":    funcs,
                "classes":  classes,
                "imports":  imports[:20],
                "doc":      doc[:300],
                "patterns": patterns,
                "lines":    src.count("\n"),
                "hash":     hashlib.md5(src.encode()).hexdigest()[:8],
            })
        except Exception as e:
            log(DIM(f"  skip {p.name}: {e}"))
    return modules


def _extract_patterns(src: str) -> list[str]:
    """Tag a source file with high-level patterns it uses."""
    tags = []
    checks = {
        "json_io":       ["json.load", "json.dump", "json.dumps", "json.loads"],
        "http_fetch":    ["urllib", "requests", "httpx", "BeautifulSoup"],
        "file_io":       ["open(", "Path(", "read_text", "write_text"],
        "git_ops":       ["subprocess", "git commit", "git push", "git add"],
        "loop_engine":   ["while True", "for _ in range", "time.sleep"],
        "data_scoring":  ["score", "weight", "rank", "priority"],
        "html_gen":      ["<html", "<div", "<!DOCTYPE", "f\"<"],
        "agent_pattern": ["agent", "Agent", "AgentBase", "dispatch"],
        "synthesis":     ["synthesis", "combine", "merge", "hybrid"],
        "gap_detect":    ["gap", "missing", "coverage", "detect"],
        "knowledge_base":["knowledge", "projects", "json.load", "kb"],
        "web_scrape":    ["BeautifulSoup", "lxml", "html.parser", "DuckDuckGo"],
        "async_tasks":   ["asyncio", "async def", "await ", "aiohttp"],
        "crypto":        ["hashlib", "hmac", "sha256", "md5"],
        "config_driven": ["os.getenv", "os.environ", ".env", "config"],
    }
    for tag, signals in checks.items():
        if any(s in src for s in signals):
            tags.append(tag)
    return tags

# ============================================================
# STEP 2 — COMPATIBILITY: find combinable pairs/triples
# ============================================================

ALCHEMY_AFFINITIES = {
    # pattern pair -> alchemy type + reason
    ("json_io",        "html_gen"):        ("FUSION",    "data pipeline that writes live HTML"),
    ("data_scoring",   "web_scrape"):      ("FUSION",    "scraper that auto-ranks what it finds"),
    ("gap_detect",     "synthesis"):       ("CHIMERA",   "gap-aware synthesis — detects what's missing then fills it"),
    ("loop_engine",    "knowledge_base"):  ("MUTATION",  "self-warming loop that deepens its own KB"),
    ("git_ops",        "json_io"):         ("CATALYST",  "auto-versioned data — every JSON change commits itself"),
    ("agent_pattern",  "data_scoring"):    ("CHIMERA",   "scoring agent that self-selects its own tasks"),
    ("html_gen",       "knowledge_base"):  ("RESONANCE", "KB that renders itself as a living document"),
    ("web_scrape",     "gap_detect"):      ("FUSION",    "gap-guided scraper — only fetches what's actually missing"),
    ("config_driven",  "loop_engine"):     ("MUTATION",  "config-hot-reloading loop — changes behaviour without restart"),
    ("data_scoring",   "gap_detect"):      ("CATALYST",  "gap prioritiser — scores gaps by urgency not just presence"),
    ("synthesis",      "knowledge_base"):  ("CHIMERA",   "synthesis engine that reads its own output as new input"),
    ("json_io",        "git_ops"):         ("FUSION",    "atomic JSON+git — write + commit in one transaction"),
    ("loop_engine",    "html_gen"):        ("RESONANCE", "loop that paints its own progress as live HTML"),
    ("agent_pattern",  "loop_engine"):     ("CATALYST",  "agent swarm scheduler — loop spawns agents by priority"),
    ("crypto",         "knowledge_base"):  ("MUTATION",  "content-addressed KB — entries identified by hash"),
}


def find_combinations(modules: list[dict], ledger: dict | None = None) -> list[dict]:
    """Return ranked list of module pairs worth combining.

    Collects ALL matching alchemy types for each pair, stores them as
    `candidate_types`. The main loop then picks the type that is most
    underrepresented in the ledger, ensuring all 5 types get exercised.
    """
    combos = []
    seen   = set()

    for i, a in enumerate(modules):
        for j, b in enumerate(modules):
            if i >= j:
                continue
            key = tuple(sorted([a["name"], b["name"]]))
            if key in seen:
                continue
            seen.add(key)

            # Check ALL pattern affinities (collect every match, not just first)
            a_pats = set(a["patterns"])
            b_pats = set(b["patterns"])
            best_score     = 0
            candidate_types = []   # list of (score, atype, reason)

            for (pa, pb), (atype, reason) in ALCHEMY_AFFINITIES.items():
                if pa in a_pats and pb in b_pats:
                    score = 2
                elif pb in a_pats and pa in b_pats:
                    score = 2
                elif pa in a_pats | b_pats and pb in a_pats | b_pats:
                    score = 1
                else:
                    score = 0
                if score > 0:
                    candidate_types.append((score, atype, reason))
                if score > best_score:
                    best_score = score

            # Also score by shared functions (hints at compatible interfaces)
            shared_funcs  = set(a["funcs"]) & set(b["funcs"])
            shared_pats   = a_pats & b_pats
            diversity     = len(a_pats ^ b_pats)   # how different they are
            combo_score   = best_score * 3 + len(shared_pats) + diversity // 2

            if combo_score > 0 or candidate_types:
                # Default: pick the highest-score candidate
                candidate_types.sort(key=lambda x: -x[0])
                default_type   = candidate_types[0][1] if candidate_types else "FUSION"
                default_reason = candidate_types[0][2] if candidate_types else f"shared patterns: {shared_pats}"
                combos.append({
                    "a":               a,
                    "b":               b,
                    "type":            default_type,
                    "reason":          default_reason,
                    "score":           combo_score,
                    "shared_funcs":    list(shared_funcs),
                    "shared_pats":     list(shared_pats),
                    "candidate_types": candidate_types,   # all viable types for this pair
                })

    combos.sort(key=lambda x: -x["score"])
    return combos[:20]  # top 20 candidates


def rebalance_types(combos: list[dict], ledger: dict) -> list[dict]:
    """
    Reassign alchemy types to under-represented categories.

    Counts how many experiments of each type exist in the ledger,
    then for each combo that has multiple candidate_types, picks the
    type with the lowest count — so all 5 types get exercised evenly.
    """
    type_counts = {}
    for exp in ledger.get("experiments", []):
        t = exp.get("type", "FUSION")
        type_counts[t] = type_counts.get(t, 0) + 1

    ALL_TYPES = ["MUTATION", "CHIMERA", "CATALYST", "RESONANCE", "FUSION"]

    rebalanced = []
    for combo in combos:
        candidates = combo.get("candidate_types", [])
        if len(candidates) > 1:
            # Among all viable types for this pair, pick the rarest in ledger
            best_type   = combo["type"]
            best_reason = combo["reason"]
            best_count  = type_counts.get(best_type, 0)
            for score, atype, reason in candidates:
                if score == candidates[0][0]:   # only among top-score matches
                    count = type_counts.get(atype, 0)
                    if count < best_count:
                        best_type   = atype
                        best_reason = reason
                        best_count  = count
            combo = {**combo, "type": best_type, "reason": best_reason}
        rebalanced.append(combo)

    # Sort: prefer rarest type first (within same affinity score)
    rebalanced.sort(key=lambda c: (
        -c["score"],
        type_counts.get(c["type"], 0),   # rarer types first
    ))
    return rebalanced

# ============================================================
# STEP 3 — ALCHEMY: generate hybrid source code
# ============================================================

EXPERIMENT_TEMPLATES = {
    "FUSION": '''\
#!/usr/bin/env python3
"""
EXPERIMENT: {exp_id}
TYPE:        FUSION
BORN:        {timestamp}
PARENTS:     {parent_a}  +  {parent_b}
HYPOTHESIS:  {reason}

WHAT THIS DOES:
  Fuses the core logic of {parent_a} and {parent_b} into one unified tool.
  {parent_a} contributes: {pats_a}
  {parent_b} contributes: {pats_b}

SAFE TO RUN: yes -- no network calls, no file mutations outside experiments/
"""
import json, os, sys, hashlib, datetime
from pathlib import Path

ROOT        = Path(__file__).resolve().parent.parent.parent
DATA        = ROOT / "data"
EXPERIMENTS = Path(__file__).resolve().parent

def load_knowledge():
    """Pull from {parent_a} pattern -- read the knowledge base."""
    kb_file = DATA / "solarpunk_knowledge.json"
    if kb_file.exists():
        with open(kb_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {{"meta": {{}}, "projects": []}}

def score_entries(entries: list) -> list:
    """Pull from {parent_b} pattern -- score + rank each entry."""
    scored = []
    for e in entries:
        s = 0
        # richness score
        s += len(e.get("sources", [])) * 2
        s += len(e.get("how_to_replicate", [])) * 1
        s += 1 if e.get("metrics") else 0
        s += 1 if e.get("contacts") else 0
        s += 1 if e.get("status") == "live" else 0
        scored.append({{**e, "_score": s}})
    scored.sort(key=lambda x: -x["_score"])
    return scored

def fuse_and_report():
    """The fusion: load KB, score it, write a ranked HTML snapshot."""
    kb     = load_knowledge()
    projs  = kb.get("projects", [])
    ranked = score_entries(projs)

    ts      = datetime.datetime.utcnow().isoformat()
    out_html = EXPERIMENTS / "fusion_{exp_id}.html"

    lines = [
        "<!DOCTYPE html><html><head><meta charset='UTF-8'>",
        "<style>body{{font-family:monospace;background:#0a0c0a;color:#9ec89e;padding:2rem}}",
        "h1{{color:#f0b429}} .row{{border-bottom:1px solid #1a2a1a;padding:.4rem 0}}",
        ".score{{color:#f0b429;font-weight:bold}} .dead{{opacity:.4}}</style></head><body>",
        f"<h1>FUSION: {exp_id}</h1>",
        f"<p style='color:#5a9e6f'>Born: {{ts}} | Parents: {parent_a} + {parent_b}</p>",
        f"<p>Hypothesis: {reason}</p><hr>",
        "<p>Projects ranked by replication richness (" + str(len(ranked)) + " total):</p>",
    ]
    for r in ranked:
        cls    = "" if r.get("status") == "live" else " dead"
        score  = r.get("_score", 0)
        name   = r.get("name", "?")
        cat    = r.get("category", "")
        cntry  = r.get("location", {{}}).get("country", "")
        lines.append(
            "<div class='row" + cls + "'>"
            "<span class='score'>[" + str(score).zfill(2) + "]</span> "
            "<b>" + name + "</b> "
            "<span style='color:#666'>" + cat + " | " + cntry + "</span>"
            "</div>"
        )
    lines.append("</body></html>")

    out_html.write_text("\\n".join(lines), encoding="utf-8")
    print(f"[FUSION] Wrote {{out_html.name}} -- {{len(ranked)}} projects ranked")
    return {{"projects_ranked": len(ranked), "output": str(out_html)}}

if __name__ == "__main__":
    result = fuse_and_report()
    print(json.dumps(result, indent=2))
''',

    "MUTATION": '''\
#!/usr/bin/env python3
"""
EXPERIMENT: {exp_id}
TYPE:        MUTATION
BORN:        {timestamp}
PARENT:      {parent_a}
MUTATION OF: {pats_a}
HYPOTHESIS:  {reason}

WHAT THIS DOES:
  Takes the core pattern from {parent_a} and evolves a new variant.
  Original patterns: {pats_a}
  Mutation vector:   {pats_b} (from {parent_b})
  Result: a hybrid that does what {parent_a} does but through a {parent_b} lens.

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
        gaps = {{"geographic": [], "categorical": [], "history": []}}
    else:
        with open(gaps_file, "r", encoding="utf-8") as f:
            gaps = json.load(f)

    covered = []
    if kb_file.exists():
        with open(kb_file, "r", encoding="utf-8") as f:
            kb = json.load(f)
        covered = [p.get("location", {{}}).get("country", "") for p in kb.get("projects", [])]

    # Score every gap by urgency
    URGENCY_WEIGHTS = {{
        "South Asia":     10,  # 2 billion people, near-zero coverage
        "Southeast Asia":  9,
        "West Africa":     8,
        "Sahel":           9,  # climate frontline
        "Caribbean":       7,  # hurricane resilience urgency
        "Central America": 6,
        "Eastern Europe":  5,
    }}

    scored_gaps = []
    for region, data in (gaps.get("geographic") or {{}}).items() if isinstance(gaps.get("geographic"), dict) else []:
        urgency  = URGENCY_WEIGHTS.get(data.get("label", region), 3)
        pop_est  = urgency * 200_000_000  # rough proxy
        scored_gaps.append({{
            "region":    region,
            "label":     data.get("label", region),
            "urgency":   urgency,
            "pop_proxy": pop_est,
            "queries":   data.get("regions", []),
        }})

    scored_gaps.sort(key=lambda x: -x["urgency"])

    result = {{
        "experiment":    "{exp_id}",
        "mutation_type": "gap_urgency_scorer",
        "gaps_scored":   len(scored_gaps),
        "top_3":         scored_gaps[:3],
        "covered_count": len([c for c in covered if c]),
        "timestamp":     datetime.datetime.utcnow().isoformat(),
    }}

    out = EXPERIMENTS / "mutation_{exp_id}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"[MUTATION] Gap urgency scores written to {{out.name}}")
    print(f"  Top gap: {{scored_gaps[0]['label'] if scored_gaps else 'none'}}")
    return result

if __name__ == "__main__":
    r = mutate_gap_detector()
    print(json.dumps(r, indent=2))
''',

    "CHIMERA": '''\
#!/usr/bin/env python3
"""
EXPERIMENT: {exp_id}
TYPE:        CHIMERA
BORN:        {timestamp}
PARENTS:     {parent_a}  +  {parent_b}
HYPOTHESIS:  {reason}

WHAT THIS DOES:
  Three-headed hybrid: reads knowledge ({parent_a}), detects gaps,
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
        return {{"status": "no_kb"}}

    with open(kb_file, "r", encoding="utf-8") as f:
        kb = json.load(f)

    projects  = kb.get("projects", [])
    cats      = list(set(p.get("category", "") for p in projects if p.get("category")))
    countries = list(set(p.get("location", {{}}).get("country", "") for p in projects))

    # HEAD 1: read what exists
    existing_ids = set(p.get("id", "") for p in projects)

    # HEAD 2: detect pattern gaps -- what category combos are MISSING?
    all_combos = list(itertools.combinations(cats, 2))
    existing_synths = []
    if syn_file.exists():
        with open(syn_file, "r", encoding="utf-8") as f:
            raw_syn = json.load(f)
        # Handle both list format and dict-with-syntheses-key format
        if isinstance(raw_syn, list):
            existing_synths = raw_syn
        elif isinstance(raw_syn, dict):
            existing_synths = raw_syn.get("syntheses", [])
    covered_combos = set()
    for s in existing_synths:
        if isinstance(s, dict):
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
        hyp = {{
            "chimera_id":   f"chimera_{{hashlib.md5((a+b).encode()).hexdigest()[:6]}}",
            "combines":     [a, b],
            "example_a":    proj_a[0].get("name", a),
            "example_b":    proj_b[0].get("name", b),
            "hypothesis":   (
                f"A community that runs both {{proj_a[0].get('name', a)}} AND "
                f"{{proj_b[0].get('name', b)}} simultaneously creates a "
                f"{{a.replace('_',' ')}} + {{b.replace('_',' ')}} hybrid "
                f"where each system feeds the other."
            ),
            "potential_locations": list(set(countries[:4])),
        }}
        hypotheses.append(hyp)

    result = {{
        "experiment":       "{exp_id}",
        "chimera_type":     "gap_aware_synthesis",
        "projects_read":    len(projects),
        "categories_found": len(cats),
        "novel_combos":     len(novel_combos),
        "hypotheses":       hypotheses,
        "timestamp":        datetime.datetime.utcnow().isoformat(),
    }}

    out = EXPERIMENTS / "chimera_{exp_id}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"[CHIMERA] {{len(hypotheses)}} novel synthesis hypotheses generated")
    for h in hypotheses[:3]:
        print(f"  - {{h['combines'][0]}} + {{h['combines'][1]}}")
    return result

if __name__ == "__main__":
    r = chimera_run()
    print(f"\\n[CHIMERA] Done: {{r.get('novel_combos', 0)}} novel combos found")
''',

    "CATALYST": '''\
#!/usr/bin/env python3
"""
EXPERIMENT: {exp_id}
TYPE:        CATALYST
BORN:        {timestamp}
CATALYSES:   {parent_a}  via  {parent_b}
HYPOTHESIS:  {reason}

WHAT THIS DOES:
  A CATALYST doesn't replace either parent -- it makes them work TOGETHER faster.
  This experiment makes {parent_b} accelerate {parent_a}.
  Specifically: {reason}

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
        return {{"status": "no_gaps"}}

    with open(gaps_file, "r", encoding="utf-8") as f:
        gaps = json.load(f)

    candidates = {{}}
    if research_file.exists():
        with open(research_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        # count research hits per gap
        for item in raw if isinstance(raw, list) else []:
            g = item.get("gap", "")
            candidates[g] = candidates.get(g, 0) + 1

    # Compute priority scores
    REGION_POP = {{
        "africa_west": 400_000_000,   "asia_south": 2_000_000_000,
        "southeast_asia": 700_000_000,"caribbean": 45_000_000,
        "central_america": 50_000_000,"africa_sahel": 100_000_000,
        "mena_deep": 150_000_000,     "europe_east": 120_000_000,
        "south_america": 430_000_000,
    }}

    priority_queue = []
    geo_gaps = gaps.get("geographic", {{}}) if isinstance(gaps.get("geographic"), dict) else {{}}
    for region, data in geo_gaps.items():
        pop      = REGION_POP.get(region, 10_000_000)
        hits     = candidates.get(f"geographic.{{region}}", 0)
        scarcity = max(0, 5 - hits)   # fewer hits = more scarce = higher priority
        score    = (pop / 1_000_000) + (scarcity * 10)
        priority_queue.append({{
            "gap":      f"geographic.{{region}}",
            "label":    data.get("label", region) if isinstance(data, dict) else region,
            "score":    round(score, 1),
            "pop_M":    round(pop / 1_000_000, 0),
            "scarcity": scarcity,
            "queries":  data.get("regions", []) if isinstance(data, dict) else [],
        }})

    priority_queue.sort(key=lambda x: -x["score"])

    result = {{
        "experiment":   "{exp_id}",
        "catalyst_for": "KNOWLEDGE_LOOP gap selection",
        "gaps_scored":  len(priority_queue),
        "top_priority": priority_queue[:3] if priority_queue else [],
        "timestamp":    datetime.datetime.utcnow().isoformat(),
    }}

    out = EXPERIMENTS / "catalyst_{exp_id}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print("[CATALYST] Priority queue: " + str(len(priority_queue)) + " gaps scored")
    for pq in priority_queue[:3]:
        print("  [" + str(int(pq["score"])) + "] " + str(pq["label"]) + " -- pop " + str(int(pq["pop_M"])) + "M, scarcity " + str(pq["scarcity"]))
    return result

if __name__ == "__main__":
    r = catalyse()
    print(json.dumps(r.get("top_priority", []), indent=2))
''',

    "RESONANCE": '''\
#!/usr/bin/env python3
"""
EXPERIMENT: {exp_id}
TYPE:        RESONANCE
BORN:        {timestamp}
RESONATES:   {parent_a}  <->  {parent_b}
HYPOTHESIS:  {reason}

WHAT THIS DOES:
  RESONANCE finds the hidden shared structure between {parent_a} and {parent_b}
  and makes it explicit. When two things resonate, they can synchronise.
  Result: a bridge module that lets both sides call each other's core logic.

SAFE TO RUN: yes -- structural analysis only, outputs to experiments/
"""
import ast, json, datetime
from pathlib import Path

ROOT        = Path(__file__).resolve().parent.parent.parent
MYCELIUM    = ROOT / "mycelium"
EXPERIMENTS = Path(__file__).resolve().parent

def find_resonance():
    """
    Analyse {parent_a} and {parent_b} for structural resonance.
    Resonance = shared function signatures, data shapes, or loop patterns.
    """
    results = {{}}
    for name in ["{parent_a}", "{parent_b}"]:
        p = MYCELIUM / f"{{name}}.py"
        if not p.exists():
            results[name] = {{"error": "not found"}}
            continue
        try:
            src  = p.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(src)
            funcs  = {{n.name: ast.dump(n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}}
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            ret_types = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Return) and node.value:
                    ret_types.append(type(node.value).__name__)
            results[name] = {{
                "funcs":    list(funcs.keys()),
                "classes":  classes,
                "returns":  list(set(ret_types)),
                "lines":    src.count("\\n"),
            }}
        except Exception as e:
            results[name] = {{"error": str(e)}}

    # Find resonance: shared function names, return types
    names = list(results.keys())
    shared_funcs = []
    if len(names) == 2 and "error" not in results[names[0]] and "error" not in results[names[1]]:
        shared_funcs = list(set(results[names[0]]["funcs"]) & set(results[names[1]]["funcs"]))

    resonance = {{
        "experiment":    "{exp_id}",
        "resonance_type":"{reason}",
        "modules":       results,
        "shared_funcs":  shared_funcs,
        "bridge_proposal": (
            f"A bridge module could expose: "
            + (", ".join(f"{{f}}()" for f in shared_funcs[:3]) or "no direct overlap -- indirect bridge via data format")
        ),
        "timestamp":     datetime.datetime.utcnow().isoformat(),
    }}

    out = EXPERIMENTS / "resonance_{exp_id}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(resonance, f, indent=2)

    print(f"[RESONANCE] Found {{len(shared_funcs)}} shared function signatures")
    print(f"  Bridge proposal: {{resonance['bridge_proposal'][:120]}}")
    return resonance

if __name__ == "__main__":
    r = find_resonance()
    print(f"\\n[RESONANCE] {exp_id} complete")
'''
}

# ============================================================
# STEP 4 — SYNTHESISE: fill template and validate
# ============================================================

def synthesise_experiment(combo: dict, ledger: dict) -> dict | None:
    """Generate source, syntax-check it, test-run it, return metadata."""
    a     = combo["a"]
    b     = combo["b"]
    atype = combo["type"]

    # Build unique ID
    raw_id    = f"{a['name']}_{b['name']}_{atype}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    exp_id    = f"{atype[:3].lower()}_{hashlib.md5(raw_id.encode()).hexdigest()[:8]}"
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    # Skip if we already made this exact combo
    combo_key = f"{a['name']}+{b['name']}+{atype}"
    if combo_key in ledger.get("completed", []):
        log(DIM(f"  skip (already alchemised): {combo_key}"))
        return None

    template = EXPERIMENT_TEMPLATES.get(atype, EXPERIMENT_TEMPLATES["FUSION"])
    src = template.format(
        exp_id    = exp_id,
        timestamp = timestamp,
        parent_a  = a["name"],
        parent_b  = b["name"],
        pats_a    = ", ".join(a["patterns"][:5]) or "general",
        pats_b    = ", ".join(b["patterns"][:5]) or "general",
        reason    = combo["reason"],
    )

    # 1. Syntax check
    try:
        ast.parse(src)
    except SyntaxError as e:
        log(RED(f"  SYNTAX FAIL: {exp_id}: {e}"))
        return None

    # 2. Save to experiments/
    out_path = EXPERIMENTS / f"{exp_id}.py"
    out_path.write_text(src, encoding="utf-8")
    log(GREEN(f"  SAVED: {out_path.name}"))

    # 3. Safe test run (subprocess, timeout 15s)
    result = _safe_run(out_path)

    return {
        "exp_id":      exp_id,
        "type":        atype,
        "parent_a":    a["name"],
        "parent_b":    b["name"],
        "reason":      combo["reason"],
        "path":        str(out_path),
        "ran_ok":      result["ok"],
        "output":      result["output"][:500],
        "combo_key":   combo_key,
        "timestamp":   timestamp,
        "score":       combo["score"],
    }


def _safe_run(script_path: Path) -> dict:
    """Run a script in a subprocess with timeout and capture output."""
    try:
        env = {**os.environ, "PYTHONUTF8": "1", "ALLOW_NETWORK": "false"}
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True, text=True, timeout=15, env=env
        )
        ok  = proc.returncode == 0
        out = (proc.stdout + proc.stderr).strip()
        if ok:
            log(GREEN(f"    RUN OK  --> {out[:80]}"))
        else:
            log(RED(f"    RUN FAIL --> {out[:80]}"))
        return {"ok": ok, "output": out}
    except subprocess.TimeoutExpired:
        log(RED(f"    TIMEOUT (15s)"))
        return {"ok": False, "output": "TIMEOUT"}
    except Exception as e:
        log(RED(f"    ERROR: {e}"))
        return {"ok": False, "output": str(e)}

# ============================================================
# STEP 5 — LEDGER: track what's been made
# ============================================================

def load_ledger() -> dict:
    if LEDGER_FILE.exists():
        try:
            with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"completed": [], "experiments": [], "total_created": 0}


def update_ledger(ledger: dict, results: list[dict]) -> dict:
    for r in results:
        if r and r.get("combo_key"):
            ledger["completed"].append(r["combo_key"])
            ledger["experiments"].append(r)
            ledger["total_created"] = ledger.get("total_created", 0) + 1
    ledger["last_run"]   = datetime.datetime.utcnow().isoformat() + "Z"
    ledger["total_files"] = len(list(EXPERIMENTS.glob("*.py")))
    # Keep last 200 entries
    ledger["completed"]   = ledger["completed"][-200:]
    ledger["experiments"] = ledger["experiments"][-100:]
    with open(LEDGER_FILE, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)
    return ledger

# ============================================================
# STEP 6 — REPORT: update experiments/README.md
# ============================================================

def write_readme(ledger: dict, new_results: list[dict]):
    """Write/update mycelium/experiments/README.md with what's been created."""
    readme = EXPERIMENTS / "README.md"
    experiments = list(EXPERIMENTS.glob("*.py"))
    total = len(experiments)

    lines = [
        "# SolarPunk Digital Alchemy Lab",
        "",
        f"> Auto-generated by CODE_ALCHEMIST.py — {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
        "",
        f"**{total} experiments** across {ledger.get('total_created', total)} alchemy cycles.",
        "",
        "## What is this?",
        "",
        "The CODE_ALCHEMIST scans all Python in `mycelium/`, finds combinable patterns,",
        "generates hybrid code, tests it safely, and commits what works.",
        "Nothing here touches existing files. Everything is additive.",
        "",
        "## Alchemy Types",
        "",
        "| Type | What it does |",
        "|------|-------------|",
        "| **FUSION** | Merges two engines into one unified tool |",
        "| **MUTATION** | Evolves a new variant of an existing engine |",
        "| **CHIMERA** | Three-headed hybrid from 3+ patterns |",
        "| **CATALYST** | Makes one engine accelerate another |",
        "| **RESONANCE** | Finds hidden shared structure and makes it explicit |",
        "",
        "## Experiments",
        "",
    ]

    all_exps = sorted(ledger.get("experiments", []), key=lambda x: x.get("timestamp", ""), reverse=True)
    for e in all_exps[:30]:
        status = "OK" if e.get("ran_ok") else "FAIL"
        icon   = "✅" if e.get("ran_ok") else "⚠️"
        lines.append(
            f"- {icon} `{e['exp_id']}.py` — **{e['type']}**: "
            f"{e['parent_a']} + {e['parent_b']} → _{e['reason'][:80]}_"
        )

    lines += [
        "",
        "## Safety Rules",
        "",
        "- Never modifies existing files",
        "- All runs in try/except sandbox with 15s timeout",
        "- Max 3 new experiments per 12h cycle",
        "- Syntax check before save",
        "- No network calls unless ALLOW_NETWORK=true",
        "",
        "## How to run an experiment",
        "",
        "```bash",
        "python mycelium/experiments/<exp_id>.py",
        "```",
        "",
        "## Run the alchemist manually",
        "",
        "```bash",
        "python mycelium/CODE_ALCHEMIST.py",
        "```",
    ]

    readme.write_text("\n".join(lines), encoding="utf-8")
    log(GREEN(f"  README updated: {total} experiments documented"))

# ============================================================
# STEP 7 — COMMIT
# ============================================================

def commit_experiments(new_results: list[dict]):
    """Git commit new experiment files."""
    if not new_results:
        return
    created = [r["exp_id"] for r in new_results if r and r.get("ran_ok")]
    if not created:
        log(DIM("  No passing experiments to commit."))
        return

    try:
        subprocess.run(["git", "-c", "commit.gpgsign=false", "add",
                        str(EXPERIMENTS), str(LEDGER_FILE)],
                       cwd=ROOT, check=True, capture_output=True)
        msg = (
            f"feat: CODE_ALCHEMIST cycle -- {len(created)} new experiments\n\n"
            + "\n".join(f"  - {eid}" for eid in created)
            + "\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
        )
        subprocess.run(["git", "-c", "commit.gpgsign=false", "commit", "-m", msg],
                       cwd=ROOT, check=True, capture_output=True)
        log(GREEN(f"  COMMITTED: {len(created)} experiments"))
    except subprocess.CalledProcessError as e:
        log(DIM(f"  git commit skipped: {e.stderr.decode()[:80] if e.stderr else ''}"))

# ============================================================
# MAIN LOOP
# ============================================================

def main():
    print(GOLD("=" * 60))
    print(GOLD("  CODE ALCHEMIST — Digital Alchemy Engine"))
    print(GOLD("  SolarPunk Nerve Center"))
    print(GOLD("=" * 60))
    start = time.time()

    # Step 1 — Scan
    log(CYAN("STEP 1: Scanning codebase..."))
    modules = scan_codebase()
    log(f"  Found {len(modules)} Python modules in mycelium/")
    for m in modules:
        log(DIM(f"    {m['name']:30s} [{len(m['funcs']):2d} funcs] patterns: {', '.join(m['patterns'][:4])}"))

    if len(modules) < 2:
        log(RED("  Not enough modules to combine. Exiting."))
        return

    # Step 2 — Find combinations
    log(CYAN("STEP 2: Finding combinable pairs..."))
    # Load ledger first so rebalance_types can see what types already exist
    ledger = load_ledger()
    combos = find_combinations(modules, ledger)
    combos = rebalance_types(combos, ledger)  # diversify alchemy types
    log(f"  {len(combos)} viable combinations ranked by affinity score")
    for c in combos[:5]:
        log(f"    [{c['score']:2d}] {c['a']['name']} + {c['b']['name']} -> {c['type']}: {c['reason'][:60]}")

    # Step 4 — Synthesise (up to VOLATILITY_BUDGET)
    log(CYAN(f"STEP 3: Synthesising (budget: {VOLATILITY_BUDGET} per cycle)..."))
    new_results = []
    budget_used = 0

    for combo in combos:
        if budget_used >= VOLATILITY_BUDGET:
            break
        log(f"  Attempting: {combo['a']['name']} + {combo['b']['name']} -> {combo['type']}")
        result = synthesise_experiment(combo, ledger)
        if result:
            new_results.append(result)
            budget_used += 1
            status = GREEN("OK") if result.get("ran_ok") else RED("FAIL (saved but did not run)")
            log(f"  {status}: {result['exp_id']}")

    # Step 5 — Update ledger + README
    log(CYAN("STEP 4: Updating ledger..."))
    ledger = update_ledger(ledger, new_results)
    write_readme(ledger, new_results)

    # Step 6 — Commit
    log(CYAN("STEP 5: Committing..."))
    commit_experiments(new_results)

    # Summary
    elapsed = time.time() - start
    ok_count   = sum(1 for r in new_results if r and r.get("ran_ok"))
    fail_count = len(new_results) - ok_count

    print(GOLD("=" * 60))
    print(GOLD(f"  ALCHEMY COMPLETE in {elapsed:.1f}s"))
    print(GOLD(f"  New experiments: {len(new_results)} ({ok_count} OK, {fail_count} failed)"))
    print(GOLD(f"  Total alchemised: {ledger.get('total_created', 0)}"))
    print(GOLD(f"  Lab: mycelium/experiments/"))
    print(GOLD("=" * 60))

    # Write JSONL log
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "cycle_ts":    datetime.datetime.utcnow().isoformat() + "Z",
            "modules":     len(modules),
            "combos":      len(combos),
            "created":     len(new_results),
            "ok":          ok_count,
            "elapsed_s":   round(elapsed, 2),
        }) + "\n")


if __name__ == "__main__":
    main()
