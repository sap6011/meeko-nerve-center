#!/usr/bin/env python3
"""
HEMISPHERE_SYNC.py -- Two-Hemisphere Brain Architecture
========================================================
The SolarPunk brain has two hemispheres:

  LEFT HEMISPHERE: Local machine (COMPUTETOR)
    - Ollama LLMs (mycelium:latest, llama3, codellama, mistral, llama3.2, nomic-embed-text)
    - 94,000+ .py files across the full filesystem
    - Direct hardware access (GPU, disk, network)
    - Claude Code sessions (the reasoning cortex)
    - Real-time MCP connections (Notion, Gmail, GCal, HuggingFace, PayPal, etc.)

  RIGHT HEMISPHERE: GitHub repository
    - 282 mycelium engines (the autonomic nervous system)
    - GitHub Actions (5 workflows -- the reflex arcs)
    - GitHub Pages (public-facing nervous system output)
    - Global accessibility (anyone can fork, contribute, read)
    - Permanent memory (git history -- the hippocampus)

  CORPUS CALLOSUM: git push/pull (the bridge between hemispheres)
    - Zero-secret data files sync automatically
    - Engine changes propagate via commits
    - Actions trigger on push (right hemisphere reflexes)
    - Local changes trigger on pull (left hemisphere updates)

This engine:
  1. Scans what each hemisphere knows that the other doesn't
  2. Identifies sync gaps (local data not pushed, remote data not pulled)
  3. Builds a sync manifest of what needs to flow where
  4. Documents the hemisphere state for other engines to consume

It does NOT push or pull automatically -- that's a human anchor decision.
It DOES tell you exactly what's out of sync and how to fix it.

Zero secrets needed.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")


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


def scan_left_hemisphere():
    """Scan the local machine's capabilities."""
    left = {
        "name": "local_machine",
        "status": "active",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Ollama models
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace"
        )
        if result.returncode == 0:
            models = []
            for line in result.stdout.strip().split("\n")[1:]:
                parts = line.split()
                if parts:
                    models.append(parts[0])
            left["ollama_models"] = models
            left["ollama_status"] = "online"
        else:
            left["ollama_status"] = "offline"
            left["ollama_models"] = []
    except Exception:
        left["ollama_status"] = "unavailable"
        left["ollama_models"] = []

    # Python version
    left["python"] = sys.version.split()[0]

    # Local engine count
    if MYCELIUM.exists():
        left["local_engines"] = len(list(MYCELIUM.glob("*.py")))
    else:
        left["local_engines"] = 0

    # Data files
    if DATA.exists():
        left["data_files"] = len(list(DATA.glob("*.json")))
    else:
        left["data_files"] = 0

    # Key local capabilities
    left["capabilities"] = []

    # Check for Ollama
    if left.get("ollama_status") == "online":
        left["capabilities"].append("local_llm_inference")

    # Check for key data
    for key_file in ["live_wire_report.json", "chimera_evolution_report.json", "polymarket_scan.json"]:
        if (DATA / key_file).exists():
            left["capabilities"].append(f"has_{key_file.replace('.json', '')}")

    return left


def scan_right_hemisphere():
    """Scan the GitHub repo's state via git."""
    right = {
        "name": "github_repo",
        "status": "active",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Check git status
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace"
        )
        if result.returncode == 0:
            changes = result.stdout.strip().split("\n") if result.stdout.strip() else []
            right["uncommitted_changes"] = len(changes)
            right["git_status"] = "clean" if not changes else "dirty"

            # Categorize changes
            modified = sum(1 for c in changes if c.strip().startswith("M"))
            added = sum(1 for c in changes if c.strip().startswith("?"))
            deleted = sum(1 for c in changes if c.strip().startswith("D"))
            right["changes_breakdown"] = {"modified": modified, "untracked": added, "deleted": deleted}
        else:
            right["git_status"] = "not_a_repo"
    except Exception:
        right["git_status"] = "unknown"

    # Check remote sync
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "HEAD...origin/main", "--left-right"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace"
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
            ahead = sum(1 for l in lines if l.startswith("<"))
            behind = sum(1 for l in lines if l.startswith(">"))
            right["ahead_of_remote"] = ahead
            right["behind_remote"] = behind
            right["sync_status"] = "in_sync" if ahead == 0 and behind == 0 else f"ahead:{ahead} behind:{behind}"
        else:
            right["sync_status"] = "unknown"
    except Exception:
        right["sync_status"] = "unknown"

    # Check current branch
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=5,
            encoding="utf-8", errors="replace"
        )
        right["branch"] = result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        right["branch"] = "unknown"

    # GitHub Actions workflows
    workflows = list(Path(".github/workflows").glob("*.yml")) if Path(".github/workflows").exists() else []
    right["workflows"] = len(workflows)

    return right


def find_sync_gaps(left, right):
    """Identify what each hemisphere has that the other doesn't."""
    gaps = []

    # Local data not in repo (uncommitted)
    if right.get("uncommitted_changes", 0) > 0:
        gaps.append({
            "type": "local_not_pushed",
            "detail": f"{right['uncommitted_changes']} local changes not committed",
            "action": "git add + git commit + git push",
            "severity": "info" if right["uncommitted_changes"] < 10 else "warning"
        })

    # Local ahead of remote
    if right.get("ahead_of_remote", 0) > 0:
        gaps.append({
            "type": "commits_not_pushed",
            "detail": f"{right['ahead_of_remote']} commits not pushed to remote",
            "action": "git push origin main",
            "severity": "warning"
        })

    # Remote ahead of local
    if right.get("behind_remote", 0) > 0:
        gaps.append({
            "type": "remote_not_pulled",
            "detail": f"{right['behind_remote']} remote commits not pulled",
            "action": "git pull origin main",
            "severity": "warning"
        })

    # Ollama not available
    if left.get("ollama_status") != "online":
        gaps.append({
            "type": "ollama_offline",
            "detail": "Ollama not running -- left hemisphere has no local LLM",
            "action": "ollama serve",
            "severity": "info"
        })

    # Key data files missing
    for key in ["chimera_evolution_report.json", "live_wire_report.json", "polymarket_scan.json"]:
        if not (DATA / key).exists():
            gaps.append({
                "type": f"missing_{key}",
                "detail": f"{key} not found -- run the generating engine",
                "action": f"python mycelium/{key.replace('_report.json', '').replace('_scan.json', '_SCANNER').upper()}.py",
                "severity": "info"
            })

    return gaps


def run():
    print("HEMISPHERE SYNC -- Two-Hemisphere Brain Architecture")
    print("=" * 55)

    # Scan both hemispheres
    print("\n  Scanning LEFT hemisphere (local machine)...")
    left = scan_left_hemisphere()
    print(f"    Ollama: {left.get('ollama_status', 'unknown')} ({len(left.get('ollama_models', []))} models)")
    print(f"    Engines: {left.get('local_engines', 0)}")
    print(f"    Data files: {left.get('data_files', 0)}")
    print(f"    Capabilities: {len(left.get('capabilities', []))}")

    print("\n  Scanning RIGHT hemisphere (GitHub repo)...")
    right = scan_right_hemisphere()
    print(f"    Branch: {right.get('branch', 'unknown')}")
    print(f"    Git status: {right.get('git_status', 'unknown')}")
    print(f"    Sync: {right.get('sync_status', 'unknown')}")
    print(f"    Workflows: {right.get('workflows', 0)}")

    # Find gaps
    print("\n  Finding sync gaps...")
    gaps = find_sync_gaps(left, right)
    if gaps:
        for g in gaps:
            sev = g["severity"].upper()
            print(f"    [{sev}] {g['detail']}")
            print(f"           Fix: {g['action']}")
    else:
        print("    Hemispheres in sync -- corpus callosum healthy")

    # Save state
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "left": left,
        "right": right,
        "sync_gaps": gaps,
        "gap_count": len(gaps),
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "architecture": {
            "left": "Local machine (Ollama, filesystem, Claude Code, MCP servers)",
            "right": "GitHub repo (Actions, Pages, git history, global access)",
            "corpus_callosum": "git push/pull (zero-secret data flow)",
        }
    }
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    save_json(DATA / "hemisphere_state.json", state)
    print(f"\n  State saved: data/hemisphere_state.json")

    print(f"\n  === HEMISPHERE STATUS ===")
    print(f"  LEFT:  {left.get('ollama_status', '?')} | {left.get('local_engines', 0)} engines | {left.get('data_files', 0)} data files")
    print(f"  RIGHT: {right.get('branch', '?')} | {right.get('git_status', '?')} | {right.get('sync_status', '?')}")
    print(f"  GAPS:  {len(gaps)}")
    print(f"\n  Two hemispheres. One brain. Zero secrets between them.")


if __name__ == "__main__":
    run()
