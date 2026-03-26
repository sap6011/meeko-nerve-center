#!/usr/bin/env python3
"""
EXPERIMENT: fus_b2eb3944
TYPE:        FUSION
BORN:        2026-03-21T15:23:26.071745Z
PARENTS:     CODE_ALCHEMIST  +  CRYPTO_BRIDGE
HYPOTHESIS:  data pipeline that writes live HTML

WHAT THIS DOES:
  Fuses the core logic of CODE_ALCHEMIST and CRYPTO_BRIDGE into one unified tool.
  CODE_ALCHEMIST contributes: json_io, http_fetch, file_io, git_ops, loop_engine
  CRYPTO_BRIDGE contributes: json_io, http_fetch, file_io, loop_engine, data_scoring

SAFE TO RUN: yes -- no network calls, no file mutations outside experiments/
"""
import json, os, sys, hashlib, datetime
from pathlib import Path

ROOT        = Path(__file__).resolve().parent.parent.parent
DATA        = ROOT / "data"
EXPERIMENTS = Path(__file__).resolve().parent

def load_knowledge():
    """Pull from CODE_ALCHEMIST pattern -- read the knowledge base."""
    kb_file = DATA / "solarpunk_knowledge.json"
    if kb_file.exists():
        with open(kb_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"meta": {}, "projects": []}

def score_entries(entries: list) -> list:
    """Pull from CRYPTO_BRIDGE pattern -- score + rank each entry."""
    scored = []
    for e in entries:
        s = 0
        # richness score
        s += len(e.get("sources", [])) * 2
        s += len(e.get("how_to_replicate", [])) * 1
        s += 1 if e.get("metrics") else 0
        s += 1 if e.get("contacts") else 0
        s += 1 if e.get("status") == "live" else 0
        scored.append({**e, "_score": s})
    scored.sort(key=lambda x: -x["_score"])
    return scored

def fuse_and_report():
    """The fusion: load KB, score it, write a ranked HTML snapshot."""
    kb     = load_knowledge()
    projs  = kb.get("projects", [])
    ranked = score_entries(projs)

    ts      = datetime.datetime.utcnow().isoformat()
    out_html = EXPERIMENTS / "fusion_fus_b2eb3944.html"

    lines = [
        "<!DOCTYPE html><html><head><meta charset='UTF-8'>",
        "<style>body{font-family:monospace;background:#0a0c0a;color:#9ec89e;padding:2rem}",
        "h1{color:#f0b429} .row{border-bottom:1px solid #1a2a1a;padding:.4rem 0}",
        ".score{color:#f0b429;font-weight:bold} .dead{opacity:.4}</style></head><body>",
        f"<h1>FUSION: fus_b2eb3944</h1>",
        f"<p style='color:#5a9e6f'>Born: {ts} | Parents: CODE_ALCHEMIST + CRYPTO_BRIDGE</p>",
        f"<p>Hypothesis: data pipeline that writes live HTML</p><hr>",
        "<p>Projects ranked by replication richness (" + str(len(ranked)) + " total):</p>",
    ]
    for r in ranked:
        cls    = "" if r.get("status") == "live" else " dead"
        score  = r.get("_score", 0)
        name   = r.get("name", "?")
        cat    = r.get("category", "")
        cntry  = r.get("location", {}).get("country", "")
        lines.append(
            "<div class='row" + cls + "'>"
            "<span class='score'>[" + str(score).zfill(2) + "]</span> "
            "<b>" + name + "</b> "
            "<span style='color:#666'>" + cat + " | " + cntry + "</span>"
            "</div>"
        )
    lines.append("</body></html>")

    out_html.write_text("\n".join(lines), encoding="utf-8")
    print(f"[FUSION] Wrote {out_html.name} -- {len(ranked)} projects ranked")
    return {"projects_ranked": len(ranked), "output": str(out_html)}

if __name__ == "__main__":
    result = fuse_and_report()
    print(json.dumps(result, indent=2))
