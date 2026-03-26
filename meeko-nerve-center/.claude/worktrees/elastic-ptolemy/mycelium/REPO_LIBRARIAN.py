#!/usr/bin/env python3
"""
REPO_LIBRARIAN.py — Full repo state indexer. Knows where everything lives.
Creates the complete map of this repo so any engine can query it.

The Librarian reads EVERYTHING:
  - All mycelium/ engine names, sizes, what they write
  - All data/ files and their sizes/ages
  - All docs/ pages and product URLs
  - All workflow .yml files
  - saves/last_good_state.json
  - scripts/ folder
  - knowledge_ingest/processed/ key files

Writes:
  - data/repo_index.json — complete repo manifest
    Every engine can read this to know what exists, what's missing, what's stale.

Used by:
  - LOOP_CONDUCTOR (knows what data files were written)
  - NEURON_A (knows what engines exist)
  - BOTTLENECK_SCANNER (knows what's stale)
  - SYNTHESIS_FACTORY (knows what to build next)
"""
import json, os
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA    = Path("data")
MYCELIUM = Path("mycelium")
DOCS    = Path("docs")
DATA.mkdir(exist_ok=True)

STALE_THRESHOLD_DAYS = 3  # Files not updated in 3+ days are "stale"

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def age_days(path):
    try:
        mtime = Path(path).stat().st_mtime
        age = (datetime.now().timestamp() - mtime) / 86400
        return round(age, 1)
    except Exception:
        return None

def index_engines():
    """Map all mycelium engines."""
    engines = {}
    for f in sorted(MYCELIUM.glob("*.py")):
        if f.name.startswith("__"):
            continue
        try:
            code = f.read_text(encoding="utf-8", errors="ignore")
            lines = len(code.split("\n"))
            # Extract what this engine writes (data files)
            import re
            writes = re.findall(r'"(data/[^"]+\.json)"', code)
            imports = re.findall(r"^from\s+(\w+)\s+import", code, re.MULTILINE)
            reads = re.findall(r'load_json\("(data/[^"]+\.json)"', code)
            is_legacy = "LEGACY" in f.name or "SIFTED" in f.name
        except Exception:
            lines, writes, imports, reads, is_legacy = 0, [], [], [], False
        engines[f.stem] = {
            "file": f.name,
            "lines": lines,
            "writes": list(set(writes))[:5],
            "reads": list(set(reads))[:5],
            "imports_from": imports[:3],
            "is_legacy": is_legacy,
            "age_days": age_days(f),
        }
    return engines

def index_data_files():
    """Map all data/ JSON files."""
    files = {}
    now = datetime.now()
    for f in sorted(DATA.glob("*.json")):
        age = age_days(f)
        files[f.name] = {
            "size_bytes": f.stat().st_size,
            "age_days": age,
            "stale": age is not None and age > STALE_THRESHOLD_DAYS,
            "empty": f.stat().st_size < 20,
        }
    return files

def index_docs():
    """Map all docs/ pages."""
    pages = {}
    if not DOCS.exists():
        return pages
    for f in DOCS.glob("*.html"):
        pages[f.name] = {"type": "root", "size": f.stat().st_size}
    for d in sorted(DOCS.iterdir()):
        if d.is_dir() and not d.name.startswith((".", "_")):
            html = d / "index.html"
            if html.exists():
                pages[d.name + "/"] = {
                    "type": "product",
                    "url": f"https://meekotharaccoon-cell.github.io/meeko-nerve-center/{d.name}/",
                    "size": html.stat().st_size,
                    "age_days": age_days(html),
                }
    return pages

def index_workflows():
    """Map all .github/workflows."""
    wf_dir = Path(".github/workflows")
    workflows = {}
    if not wf_dir.exists():
        return workflows
    for f in sorted(wf_dir.glob("*.yml")):
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            import re
            crons  = re.findall(r"cron:\s+'([^']+)'", content)
            engines_used = re.findall(r"python3 mycelium/(\w+)\.py", content)
            on_keys = re.findall(r"^\s{2}(\w+):", content, re.MULTILINE)
        except Exception:
            crons, engines_used, on_keys = [], [], []
        workflows[f.name] = {
            "schedules": crons[:3],
            "engines_count": len(set(engines_used)),
            "engines": sorted(set(engines_used))[:10],
            "size": f.stat().st_size,
        }
    return workflows

def index_knowledge():
    """Key knowledge files."""
    ki = {}
    for fpath in [
        "knowledge_ingest/processed/MYCELIUM_KNOWLEDGE_BASE.json",
        "data/consolidated_knowledge.json",
        "data/knowledge_map.json",
        "data/knowledge_graph.json",
        "data/lessons.json",
        "data/capability_map.json",
        "data/active_capabilities.json",
        "saves/last_good_state.json",
    ]:
        p = Path(fpath)
        if p.exists():
            ki[fpath] = {"size": p.stat().st_size, "age_days": age_days(p)}
        else:
            ki[fpath] = {"missing": True}
    return ki

def index_scripts():
    """scripts/ folder."""
    scripts = {}
    for f in sorted(Path("scripts").glob("*.py")):
        scripts[f.name] = {"lines": len(f.read_text(encoding="utf-8",errors="ignore").split("\n")), "size": f.stat().st_size}
    return scripts

def find_gaps(engines, data_files):
    """Which engines have no data output? Which data files have no reader?"""
    # Engines that write nothing
    no_output_engines = [name for name, info in engines.items()
                         if not info["writes"] and not info["is_legacy"] and info["lines"] > 30]

    # Data files written but never read by any engine
    all_reads = set()
    all_writes = set()
    for info in engines.values():
        all_reads.update(info.get("reads", []))
        all_writes.update(info.get("writes", []))

    unread_files = [f for f in all_writes if f not in all_reads]
    missing_outputs = [f for f in all_reads if f not in data_files]

    return {
        "engines_with_no_output": no_output_engines[:10],
        "data_files_never_read": unread_files[:10],
        "data_files_read_but_missing": missing_outputs[:10],
        "stale_data_files": [f for f, info in data_files.items() if info.get("stale")],
    }

def main():
    print("📚 REPO_LIBRARIAN — indexing entire repository...")

    engines   = index_engines()
    data      = index_data_files()
    docs      = index_docs()
    workflows = index_workflows()
    knowledge = index_knowledge()
    scripts   = index_scripts()
    gaps      = find_gaps(engines, data)

    repo_index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_engines": len(engines),
            "active_engines": sum(1 for e in engines.values() if not e.get("is_legacy")),
            "data_files": len(data),
            "stale_data_files": len(gaps["stale_data_files"]),
            "docs_pages": len(docs),
            "product_pages": sum(1 for d in docs.values() if d.get("type")=="product"),
            "workflows": len(workflows),
            "scripts": len(scripts),
        },
        "engines":   engines,
        "data_files": data,
        "docs":      docs,
        "workflows": workflows,
        "knowledge": knowledge,
        "scripts":   {k: v for k, v in list(scripts.items())[:20]},
        "gaps":      gaps,
    }

    Path("data/repo_index.json").write_text(
        json.dumps(repo_index, indent=2), encoding="utf-8"
    )

    s = repo_index["summary"]
    print(f"   Engines: {s['total_engines']} total, {s['active_engines']} active")
    print(f"   Data files: {s['data_files']} ({s['stale_data_files']} stale)")
    print(f"   Docs: {s['product_pages']} product pages")
    print(f"   Workflows: {s['workflows']}")
    print(f"   Gaps found: {len(gaps['engines_with_no_output'])} engines with no output, "
          f"{len(gaps['data_files_never_read'])} unread data files")

if __name__ == "__main__":
    main()
