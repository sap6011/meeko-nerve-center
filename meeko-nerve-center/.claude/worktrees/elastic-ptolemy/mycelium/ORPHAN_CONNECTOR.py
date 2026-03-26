#!/usr/bin/env python3
"""
ORPHAN_CONNECTOR.py — Finds unconnected data + engines and wires them.
Reads repo_index.json to find gaps, then creates the missing connections.

Every cycle it:
1. Finds data files written but never read → picks highest-value ones to surface
2. Finds engines with no outputs → logs them for SYNTHESIS_FACTORY to fix
3. Finds knowledge files not connected to the brain loop → links them
4. Reads scripts/ folder scripts → extracts any useful intelligence
5. Reads knowledge_ingest/processed/ for useful guides → surfaces them

Writes:
  - data/orphan_connections.json — what was connected this cycle
  - data/scripts_intelligence.json — useful intelligence from scripts/ folder
  - data/knowledge_ingest_index.json — what's in knowledge_ingest/processed/
  - Appends findings to data/lessons.json
"""
import json, os, re
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data")
SCRIPTS  = Path("scripts")
KINGEST  = Path("knowledge_ingest/processed")
DATA.mkdir(exist_ok=True)

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def surface_unread_data():
    """Find data files that engines write but nothing reads — surface their content."""
    repo_index = load_json("data/repo_index.json")
    gaps = repo_index.get("gaps", {})
    unread = gaps.get("data_files_never_read", [])

    surfaced = {}
    for fpath in unread[:15]:
        p = Path(fpath)
        if not p.exists():
            continue
        try:
            content = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            # Extract key signals
            if isinstance(content, dict):
                key_fields = {k: v for k, v in content.items()
                             if k not in ("generated_at","timestamp","_engine","_written_at")
                             and not isinstance(v, (dict, list))}
                surfaced[fpath] = {"type": "dict", "keys": list(content.keys())[:8], "signals": key_fields}
            elif isinstance(content, list):
                surfaced[fpath] = {"type": "list", "count": len(content), "sample": content[:2]}
        except Exception:
            pass
    return surfaced

def read_scripts_intelligence():
    """Extract useful intelligence from scripts/ folder."""
    intelligence = []
    if not SCRIPTS.exists():
        return intelligence

    for f in sorted(SCRIPTS.glob("*.py")):
        try:
            code = f.read_text(encoding="utf-8", errors="ignore")
            if len(code) < 50:
                continue
            # Get function names and docstrings
            funcs = re.findall(r"def (\w+)\(", code)
            doc = re.search(r'"""(.*?)"""', code, re.DOTALL)
            desc = doc.group(1).strip()[:150] if doc else ""
            # Get any hardcoded URLs or API endpoints
            urls = re.findall(r"https?://[^\s\"']+", code)[:3]
            intelligence.append({
                "file": f.name,
                "functions": funcs[:5],
                "description": desc,
                "urls": urls,
            })
        except Exception:
            pass
    return intelligence[:20]

def index_knowledge_ingest():
    """Index what's in knowledge_ingest/processed/ that's useful."""
    index = {"files": [], "guides": [], "data": []}
    if not KINGEST.exists():
        return index

    for f in sorted(KINGEST.iterdir()):
        if f.suffix == ".json":
            try:
                content = json.loads(f.read_text(encoding="utf-8", errors="ignore"))
                keys = list(content.keys()) if isinstance(content, dict) else []
                index["data"].append({"file": f.name, "keys": keys[:6], "size": f.stat().st_size})
            except Exception:
                index["files"].append({"file": f.name, "size": f.stat().st_size})
        elif f.suffix in (".md", ".txt"):
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                first_line = text.strip().split("\n")[0].replace("#","").strip()[:80]
                index["guides"].append({"file": f.name, "title": first_line, "size": f.stat().st_size})
            except Exception:
                pass

    # Read the MYCELIUM_KNOWLEDGE_BASE.json specifically
    mkb_path = KINGEST / "MYCELIUM_KNOWLEDGE_BASE.json"
    if mkb_path.exists():
        mkb = load_json(mkb_path)
        index["mycelium_kb_summary"] = {
            "version": mkb.get("version",""),
            "generated": mkb.get("generated",""),
            "keys": list(mkb.keys()),
            "revenue_streams": list(mkb.get("revenue_streams",{}).keys()) if isinstance(mkb.get("revenue_streams"),dict) else [],
            "next_actions": mkb.get("next_actions_priority",[])[:5],
        }
    return index

def find_valuable_connections(surfaced_data, scripts_intel, ki_index):
    """Identify the most valuable new connections to make."""
    connections = []

    # Surface any affiliate data to REVENUE_FLYWHEEL
    for fpath, info in surfaced_data.items():
        if "affiliate" in fpath.lower():
            signals = info.get("signals", {})
            if signals:
                connections.append({
                    "from": fpath,
                    "to": "REVENUE_FLYWHEEL",
                    "type": "revenue_data",
                    "value": "affiliate revenue signals",
                    "signals": signals,
                })

    # Surface scripts with URLs to SCAVENGER_WEB
    for script in scripts_intel:
        if script["urls"]:
            connections.append({
                "from": f"scripts/{script['file']}",
                "to": "SCAVENGER_WEB",
                "type": "url_targets",
                "value": f"found {len(script['urls'])} URLs",
                "data": script["urls"],
            })

    # Surface knowledge_ingest guides to KNOWLEDGE_SYNTHESIZER
    for guide in ki_index.get("guides", [])[:5]:
        connections.append({
            "from": f"knowledge_ingest/processed/{guide['file']}",
            "to": "KNOWLEDGE_SYNTHESIZER",
            "type": "knowledge_guide",
            "value": guide["title"],
        })

    return connections

def append_to_lessons(connections, surfaced_data):
    """Add new discoveries to lessons.json for brain loop."""
    lessons = load_json("data/lessons.json", [])
    if not isinstance(lessons, list):
        lessons = []

    new_lessons = []

    # Add lessons from unread data
    for fpath, info in list(surfaced_data.items())[:3]:
        sigs = info.get("signals", {})
        if sigs and any(v for v in sigs.values()):
            new_lessons.append({
                "lesson": f"Unread data file {fpath} contains: {list(sigs.keys())[:4]}",
                "priority": "medium",
                "added_at": datetime.now(timezone.utc).isoformat(),
                "source": "ORPHAN_CONNECTOR",
            })

    # Add useful lessons from new connections
    for conn in connections[:3]:
        new_lessons.append({
            "lesson": f"New connection found: {conn['from']} → {conn['to']} ({conn['value']})",
            "priority": "low",
            "added_at": datetime.now(timezone.utc).isoformat(),
            "source": "ORPHAN_CONNECTOR",
        })

    if new_lessons:
        lessons = new_lessons + lessons
        lessons = lessons[:25]  # Keep max 25 lessons
        Path("data/lessons.json").write_text(
            json.dumps(lessons, indent=2), encoding="utf-8"
        )

def main():
    print("🔗 ORPHAN_CONNECTOR — wiring unconnected data, scripts, and knowledge...")

    surfaced_data = surface_unread_data()
    scripts_intel = read_scripts_intelligence()
    ki_index      = index_knowledge_ingest()
    connections   = find_valuable_connections(surfaced_data, scripts_intel, ki_index)

    # Append useful lessons
    append_to_lessons(connections, surfaced_data)

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "surfaced_unread_data": surfaced_data,
        "scripts_intelligence": scripts_intel,
        "knowledge_ingest_index": ki_index,
        "new_connections": connections,
        "summary": {
            "unread_data_surfaced": len(surfaced_data),
            "scripts_analyzed": len(scripts_intel),
            "knowledge_files_indexed": len(ki_index.get("guides", [])) + len(ki_index.get("data", [])),
            "connections_made": len(connections),
        }
    }

    Path("data/orphan_connections.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    Path("data/scripts_intelligence.json").write_text(
        json.dumps(scripts_intel, indent=2), encoding="utf-8"
    )
    Path("data/knowledge_ingest_index.json").write_text(
        json.dumps(ki_index, indent=2), encoding="utf-8"
    )

    s = result["summary"]
    print(f"   Unread data surfaced: {s['unread_data_surfaced']}")
    print(f"   Scripts analyzed: {s['scripts_analyzed']}")
    print(f"   Knowledge files indexed: {s['knowledge_files_indexed']}")
    print(f"   New connections made: {s['connections_made']}")

if __name__ == "__main__":
    main()
