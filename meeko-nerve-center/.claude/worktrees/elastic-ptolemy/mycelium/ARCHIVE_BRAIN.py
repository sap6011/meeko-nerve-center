#!/usr/bin/env python3
"""
ARCHIVE_BRAIN.py — Connects saves/, knowledge_ingest/processed/, and docs/
back into the active brain loop. Nothing valuable gets forgotten.

The archive holds:
  saves/last_good_state.json           (145KB system snapshot)
  saves/LEGAL_MANIFEST.md              (legal framework)
  knowledge_ingest/processed/*.md      (setup guides, manifesto, conventions)
  knowledge_ingest/processed/*.json    (MYCELIUM_KNOWLEDGE_BASE.json etc.)
  docs/MANIFESTO.md                    (public manifesto)
  docs/CONSTITUTION.md                 (governance)
  docs/AGENCY_MEMORY.md               (agent memory)
  docs/OPEN_BOUNTIES.md               (bounties)

Extracts key intelligence and surfaces it to:
  data/archive_intelligence.json       (what was in the archive this cycle)
  data/lessons.json                    (critical lessons from archive)
  data/consolidated_knowledge.json     (merged with archive knowledge)
"""
import json, re, os
from pathlib import Path
from datetime import datetime, timezone

DATA  = Path("data")
DOCS  = Path("docs")
SAVES = Path("saves")
KINGEST = Path("knowledge_ingest/processed")
DATA.mkdir(exist_ok=True)

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def load_text(p):
    try:
        f = Path(p)
        if f.exists():
            return f.read_text(encoding="utf-8", errors="ignore")
    except Exception: pass
    return ""

def extract_from_last_good_state():
    """Pull key intelligence from saves/last_good_state.json."""
    state = load_json("saves/last_good_state.json")
    if not state:
        return {}
    ts = state.get("timestamp","")
    files = state.get("files", {})
    # Find the most important files in the snapshot
    important = {}
    for fname, content in files.items():
        if any(k in fname for k in ["brain_state","flywheel","lessons","capability","knowledge_map"]):
            important[fname] = content
    return {
        "snapshot_timestamp": ts,
        "snapshot_file_count": len(files),
        "key_files": important,
    }

def extract_from_guides():
    """Extract actionable intelligence from knowledge_ingest/processed/ guides."""
    guides = {}
    if not KINGEST.exists():
        return guides

    priority_guides = [
        "COMPLETE_AUTONOMY_GUIDE.md",
        "LOCAL_AI_SETUP.md",
        "QUICK_START.md",
        "SHOP_SETUP.md",
        "AI_TO_AI_HANDOFF_GUIDE.md",
        "CONVENTIONS.md",
        "MANIFESTO.md",
        "MYCELIUM_KNOWLEDGE_BASE.json",
    ]

    for guide_name in priority_guides:
        p = KINGEST / guide_name
        if not p.exists():
            continue
        if p.suffix == ".json":
            content = load_json(p)
            guides[guide_name] = {
                "type": "json",
                "keys": list(content.keys())[:8] if isinstance(content, dict) else "list",
                "next_actions": content.get("next_actions_priority", [])[:5] if isinstance(content, dict) else [],
                "revenue_streams": list(content.get("revenue_streams", {}).keys()) if isinstance(content, dict) else [],
            }
        else:
            text = load_text(p)
            if not text: continue
            # Extract headings as structure
            headings = re.findall(r"^#{1,3}\s+(.+)", text, re.MULTILINE)
            # Extract action items
            actions = re.findall(r"[-*]\s+\*\*(.+?)\*\*", text)
            actions += re.findall(r"^\d+\.\s+(.+)", text, re.MULTILINE)
            guides[guide_name] = {
                "type": "markdown",
                "headings": headings[:8],
                "actions": [a[:100] for a in actions[:5]],
                "word_count": len(text.split()),
            }

    return guides

def extract_from_docs_knowledge():
    """Surface key docs that aren't product pages."""
    knowledge_docs = {}
    if not DOCS.exists():
        return knowledge_docs

    priority_docs = [
        "MANIFESTO.md", "CONSTITUTION.md", "AGENCY_MEMORY.md",
        "GOVERNANCE.md", "OPEN_BOUNTIES.md", "DECISION_LOG.md",
        "LEGAL_NOTICE.md", "COMMUNITY_BLUEPRINT.md",
    ]

    for doc_name in priority_docs:
        p = DOCS / doc_name
        if not p.exists():
            continue
        text = load_text(p)
        if not text: continue
        headings = re.findall(r"^#{1,3}\s+(.+)", text, re.MULTILINE)
        knowledge_docs[doc_name] = {
            "type": "governance",
            "headings": headings[:5],
            "first_paragraph": text.strip()[:300],
        }
    return knowledge_docs

def build_archive_lessons(guides, docs_knowledge, last_good):
    """Extract key lessons from archive content."""
    lessons = []

    # From MYCELIUM_KNOWLEDGE_BASE next actions
    kb = guides.get("MYCELIUM_KNOWLEDGE_BASE.json", {})
    for action in kb.get("next_actions", [])[:3]:
        if action:
            lessons.append({
                "lesson": str(action)[:200],
                "priority": "high",
                "source": "MYCELIUM_KNOWLEDGE_BASE",
                "added_at": datetime.now(timezone.utc).isoformat(),
            })

    # From QUICK_START guide
    qs = guides.get("QUICK_START.md", {})
    for action in qs.get("actions", [])[:2]:
        lessons.append({
            "lesson": f"Quick start action: {action}",
            "priority": "medium",
            "source": "QUICK_START_GUIDE",
            "added_at": datetime.now(timezone.utc).isoformat(),
        })

    return lessons

def merge_to_consolidated(guides, archive_intel):
    """Merge archive intelligence into consolidated_knowledge.json."""
    ck = load_json("data/consolidated_knowledge.json")
    ck.setdefault("archive", {})
    ck["archive"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    ck["archive"]["guides_indexed"] = list(guides.keys())
    ck["archive"]["snapshot_ts"] = archive_intel.get("last_good_state", {}).get("snapshot_timestamp","")

    # Merge MYCELIUM_KNOWLEDGE_BASE revenue streams
    kb = guides.get("MYCELIUM_KNOWLEDGE_BASE.json", {})
    if kb.get("revenue_streams"):
        ck.setdefault("mycelium_kb", {}).setdefault("revenue_streams", {})
        for stream in kb["revenue_streams"]:
            ck["mycelium_kb"]["revenue_streams"].setdefault(stream, {"status": "tracked"})

    Path("data/consolidated_knowledge.json").write_text(
        json.dumps(ck, indent=2), encoding="utf-8"
    )

def main():
    print("📦 ARCHIVE_BRAIN — surfacing archive intelligence to active loop...")

    last_good = extract_from_last_good_state()
    guides    = extract_from_guides()
    docs_knowledge = extract_from_docs_knowledge()
    archive_lessons = build_archive_lessons(guides, docs_knowledge, last_good)

    # Merge archive lessons into lessons.json
    existing_lessons = load_json("data/lessons.json", [])
    if not isinstance(existing_lessons, list):
        existing_lessons = []
    new_lessons = archive_lessons + existing_lessons
    # Deduplicate
    seen = set()
    deduped = []
    for l in new_lessons:
        key = l.get("lesson","")[:80]
        if key not in seen:
            seen.add(key)
            deduped.append(l)
    Path("data/lessons.json").write_text(
        json.dumps(deduped[:30], indent=2), encoding="utf-8"
    )

    archive_intel = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "last_good_state": {
            "snapshot_timestamp": last_good.get("snapshot_timestamp",""),
            "file_count": last_good.get("snapshot_file_count", 0),
        },
        "guides": {k: {"type": v.get("type"), "headings": v.get("headings",[])[:3]} for k, v in guides.items()},
        "docs_knowledge": {k: {"headings": v.get("headings",[])[:3]} for k, v in docs_knowledge.items()},
        "archive_lessons_added": len(archive_lessons),
        "summary": {
            "guides_indexed": len(guides),
            "governance_docs": len(docs_knowledge),
            "has_last_good_snapshot": bool(last_good),
        }
    }

    Path("data/archive_intelligence.json").write_text(
        json.dumps(archive_intel, indent=2), encoding="utf-8"
    )
    merge_to_consolidated(guides, archive_intel)

    print(f"   Guides indexed: {len(guides)} | Governance docs: {len(docs_knowledge)}")
    print(f"   Archive lessons added: {len(archive_lessons)}")
    print(f"   Last good snapshot: {last_good.get('snapshot_timestamp','none')}")
    print(f"   archive_intelligence.json written → KNOWLEDGE_SYNTHESIZER reads this")

if __name__ == "__main__":
    main()
