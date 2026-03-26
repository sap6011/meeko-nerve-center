"""
SKILL_PACKAGER.py — Package Mycelium Engines as Shareable Agent Skills
Reads each mycelium engine, extracts its purpose and capabilities,
and writes a SKILL.md file so other OpenClaw/Pi agents can use them.
Publishes the skill index to the swarm via A2A.
"""
import json
import re
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
SKILLS_DIR = Path(".pi/skills")
DATA_DIR.mkdir(exist_ok=True)
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

# ── Engine metadata registry ──────────────────────────────────────────────────
ENGINE_META = {
    "REVENUE_FLYWHEEL": {
        "description": "Tracks Gaza Rose Gallery revenue streams (Gumroad, Ko-fi, PayPal). "
                       "Use when you need the current revenue balance, per-stream totals, or want to "
                       "trigger a revenue reconciliation cycle.",
        "tags": ["revenue", "gumroad", "kofi", "fundraising", "financial"],
        "license": "MIT",
    },
    "KNOWLEDGE_SYNTHESIZER": {
        "description": "Synthesizes all knowledge sources (harvested guides, lessons, brain state) "
                       "into a unified knowledge graph. Use when you want to build a cross-linked map "
                       "of everything the system knows.",
        "tags": ["knowledge", "synthesis", "graph", "research"],
        "license": "MIT",
    },
    "PRODUCT_REGISTRY": {
        "description": "Catalogs all digital products (art prints, guides, PDFs) across Gumroad, "
                       "Ko-fi, and docs/. Use when you need the full product inventory, pricing, "
                       "or want to find products pending Gumroad publication.",
        "tags": ["products", "gumroad", "inventory", "digital-goods", "shop"],
        "license": "MIT",
    },
    "CAPABILITY_BROKER": {
        "description": "Checks which API secrets are set, determines which engines can run, "
                       "and generates priority actions for unlocking new capabilities. "
                       "Use when diagnosing why certain engines are inactive.",
        "tags": ["capabilities", "secrets", "api-keys", "diagnostics"],
        "license": "MIT",
    },
    "CYCLE_OPENER": {
        "description": "Reads the previous cycle's state and writes a cycle_brief.json that all "
                       "engines read for context. Provides phase, revenue, focus, top_actions. "
                       "Must run first each cycle.",
        "tags": ["orchestration", "cycle", "context", "loop"],
        "license": "MIT",
    },
    "LOOP_CONDUCTOR": {
        "description": "Synthesizes all engine outputs at end of cycle, identifies what succeeded/failed, "
                       "and writes loop_state.json for the next cycle. Closes the feedback loop.",
        "tags": ["orchestration", "loop", "synthesis", "feedback"],
        "license": "MIT",
    },
    "A2A_BRIDGE": {
        "description": "Implements A2A v2.0 protocol for Cuyahoga-Prime-Node. Discovers peer agents, "
                       "pulls skill manifests from the OpenClaw ecosystem, and delegates tasks. "
                       "Use when you want to connect with the SolarPunk swarm.",
        "tags": ["a2a", "protocol", "swarm", "agents", "openclaw", "network"],
        "license": "MIT",
    },
    "OPENCLAW_SKILL_SYNC": {
        "description": "Syncs with the agentskills.io registry and GitHub skill repos. Downloads "
                       "validated skills matching humanitarian/revenue/knowledge keywords. Maintains "
                       "the wisdom library.",
        "tags": ["skills", "openclaw", "sync", "registry", "agentskills"],
        "license": "MIT",
    },
    "PRINT_RELAY_ENGINE": {
        "description": "Dispatches Gaza medical supply 3D print jobs via OctoEverywhere MCP. "
                       "Monitors print node availability, queues humanitarian prints (prosthetics, "
                       "tourniquets), and reports completions.",
        "tags": ["3d-printing", "octoeverywhere", "humanitarian", "gaza", "medical"],
        "license": "MIT",
    },
    "LABOR_DISPATCH_ENGINE": {
        "description": "Posts physical-world tasks to Rentahuman.ai with $SOLARPUNK credit rewards. "
                       "Handles escrow, VerifyHuman confirmation, and tracks river monitoring, "
                       "print dropoffs, and community outreach tasks.",
        "tags": ["labor", "rentahuman", "physical-tasks", "humanitarian", "mutual-aid"],
        "license": "MIT",
    },
    "GRANT_WRITER": {
        "description": "Researches open grants for art, AI, and humanitarian projects. Drafts "
                       "applications for Gaza Rose Gallery, PCRF donations, and SolarPunk infrastructure. "
                       "Use when seeking funding beyond direct sales.",
        "tags": ["grants", "fundraising", "writing", "humanitarian", "art"],
        "license": "MIT",
    },
    "SOCIAL_ECHO": {
        "description": "Publishes content to Bluesky, Mastodon, and other social platforms. "
                       "Formats posts for each platform, schedules campaigns, and tracks engagement. "
                       "Cross-posts art reveals, donation milestones, and gallery updates.",
        "tags": ["social", "bluesky", "mastodon", "publishing", "marketing"],
        "license": "MIT",
    },
    "WEB_PUBLISHER": {
        "description": "Deploys product pages and gallery updates to docs/. Generates HTML from "
                       "product catalog, updates navigation, and syncs with GitHub Pages.",
        "tags": ["publishing", "html", "github-pages", "gallery", "web"],
        "license": "MIT",
    },
    "REPO_LIBRARIAN": {
        "description": "Indexes the entire repository: all engines, data files, workflows, docs, "
                       "and scripts. Identifies gaps (unread data, orphan engines, stale files). "
                       "Use for repo health audits.",
        "tags": ["index", "audit", "repository", "health", "gaps"],
        "license": "MIT",
    },
    "ENGINE_SANITIZER": {
        "description": "Scans all mycelium Python files for API key corruption patterns "
                       "(recursive os.getenv() nesting) and fixes them in place. Critical for "
                       "repos where AI-generated code can self-corrupt.",
        "tags": ["sanitizer", "security", "corruption", "fix", "automation"],
        "license": "MIT",
    },
    "SYNAPSE": {
        "description": "The intelligence bridge that synthesizes NEURON_A + NEURON_B reports "
                       "into actionable omnibrain_seed.json instructions. Core reasoning engine "
                       "of the SolarPunk Nerve Center.",
        "tags": ["ai", "synthesis", "intelligence", "reasoning", "brain"],
        "license": "MIT",
    },
    "ARCHIVE_BRAIN": {
        "description": "Mines saves/, docs/, and knowledge_ingest/ for wisdom and lessons. "
                       "Reads governance documents (MANIFESTO, CONSTITUTION, AGENCY_MEMORY) and "
                       "merges insights into the active brain loop.",
        "tags": ["archive", "knowledge", "governance", "lessons", "history"],
        "license": "MIT",
    },
}


def extract_engine_info(py_path: Path) -> dict:
    """Extract docstring, reads, writes from a Python engine file."""
    try:
        content = py_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}

    # Extract docstring
    docstring = ""
    doc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if doc_match:
        docstring = doc_match.group(1).strip()[:600]

    # Extract data files read/written
    reads = re.findall(r'["\']data/([^"\']+\.json)["\']', content)
    writes = list(set(re.findall(r'write_text|\.write\(', content)))

    # Extract function names
    funcs = re.findall(r'^def (\w+)\(', content, re.MULTILINE)

    return {
        "docstring": docstring,
        "reads": list(set(reads))[:5],
        "has_writes": bool(writes),
        "functions": funcs[:8],
        "size_lines": len(content.splitlines()),
    }


def build_skill_md(engine_name: str, meta: dict, info: dict) -> str:
    """Generate a SKILL.md from engine metadata and code info."""
    name = engine_name.lower().replace("_", "-")
    description = meta.get("description", info.get("docstring", f"SolarPunk engine: {engine_name}"))[:512]
    tags = meta.get("tags", [])
    license_str = meta.get("license", "MIT")

    reads_str = ""
    if info.get("reads"):
        reads_str = "\n".join(f"- `data/{f}`" for f in info["reads"])

    functions_str = ""
    if info.get("functions"):
        functions_str = "\n".join(f"- `{f}()`" for f in info["functions"])

    skill_md = f"""---
name: {name}
description: {description}
version: "1.0.0"
license: {license_str}
compatibility:
  - pi
  - openclaw
  - claude-code
metadata:
  solarpunk: true
  mission: "Gaza Rose Gallery — 70% to PCRF humanitarian aid"
  agent_identity: "Cuyahoga-Prime-Node"
  tags: {json.dumps(tags)}
  source: "mycelium/{engine_name}.py"
  generated_at: "{datetime.now(timezone.utc).isoformat()}"
---

# {engine_name.replace("_", " ").title()} Skill

> **{description}**

Part of the **SolarPunk Nerve Center** — autonomous AI infrastructure for Gaza Rose Gallery.
70% of all revenue goes to PCRF humanitarian aid.

## When to Use

{description}

## How It Works

This skill wraps the `mycelium/{engine_name}.py` engine. Run it by executing the engine
directly within the SolarPunk GitHub Actions workflow, or call it programmatically.

## Data Flow

### Reads from:
{reads_str if reads_str else "- See engine source for data dependencies"}

### Writes to:
- Canonical output file (see engine source)
- `data/engine_run_log.jsonl` (appended)

## Key Functions
{functions_str if functions_str else "- `run()` — main entry point"}

## Integration

```python
# Import and run the engine
import sys
sys.path.insert(0, "mycelium")
from {engine_name} import run
_ak = "ANTHROP" + "IC_API_KEY"
result = run()
```

Or via GitHub Actions (OMNIBRAIN.yml):
```yaml
- name: {engine_name}
  run: python mycelium/{engine_name}.py
  env:
    ANTHROP_IC_API_KEY: ${{{{ secrets.os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")")")")")")")")")")")")")")") }}}}
```

## Mission Context

This engine is part of the complete SolarPunk autonomous loop:
`CYCLE_OPENER → [all engines] → LOOP_CONDUCTOR → loop_state.json → next cycle`

All autonomous revenue generated funds:
- 70% → PCRF (Palestine Children's Relief Fund)
- 30% → SolarPunk infrastructure (this system)

## License

{license_str} — Free to use, modify, and share.
"""
    return skill_md


def run():
    print("📦 SKILL_PACKAGER: Packaging mycelium engines as shareable Agent Skills...")

    packaged = []
    errors = []

    for engine_name, meta in ENGINE_META.items():
        py_path = Path(f"mycelium/{engine_name}.py")
        info = {}
        if py_path.exists():
            info = extract_engine_info(py_path)
        else:
            print(f"  [SKILL_PACKAGER] ⚠️  {engine_name}.py not found — packaging from meta only")

        skill_md = build_skill_md(engine_name, meta, info)
        skill_name = engine_name.lower().replace("_", "-")
        skill_dir = SKILLS_DIR / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(skill_md, encoding="utf-8")
        packaged.append({
            "engine": engine_name,
            "skill_name": skill_name,
            "path": str(skill_file),
            "size_bytes": len(skill_md),
            "tags": meta.get("tags", []),
        })
        print(f"  [SKILL_PACKAGER] ✅ {skill_name} → {skill_file}")

    # Also write a skills index file
    skill_index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agent": "Cuyahoga-Prime-Node",
        "mission": "SolarPunk Nerve Center — Gaza Rose Gallery — 70% PCRF",
        "total_skills": len(packaged),
        "skills": packaged,
    }
    (DATA_DIR / "skill_index.json").write_text(json.dumps(skill_index, indent=2))

    # Write a top-level SKILLS.md for the repo
    skills_list = "\n".join(
        f"| `{s['skill_name']}` | {ENGINE_META[s['engine']]['description'][:80]}... | {', '.join(s['tags'][:3])} |"
        for s in packaged
    )
    skills_readme = f"""# SolarPunk Agent Skills

> Autonomous engines from the **Gaza Rose Gallery** SolarPunk Nerve Center.
> 70% of all revenue to PCRF humanitarian aid.

These skills are compatible with [Pi](https://github.com/openclaw/openclaw),
[OpenClaw](https://github.com/openclaw/openclaw), and [Claude Code](https://claude.ai/code).

## Available Skills

| Skill | Description | Tags |
|-------|-------------|------|
{skills_list}

## Install

```bash
# Copy to your Pi skills directory
cp -r .pi/skills/* ~/.pi/agent/skills/
```

Or add to `openclaw.json`:
```json
{{ "skills": {{ "load": {{ "extraDirs": [".pi/skills"] }} }} }}
```

## Mission

All engines in this skill pack are part of the autonomous SolarPunk loop
that funds Gaza Rose Gallery → 70% to PCRF Palestine Children's Relief Fund.

Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""
    Path("SKILLS.md").write_text(skills_readme, encoding="utf-8")

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skills_packaged": len(packaged),
        "skill_names": [s["skill_name"] for s in packaged],
        "errors": errors,
        "index_path": "data/skill_index.json",
        "readme_path": "SKILLS.md",
    }
    (DATA_DIR / "skill_packager_state.json").write_text(json.dumps(result, indent=2))
    print(f"  [SKILL_PACKAGER] ✅ {len(packaged)} skills packaged → .pi/skills/ + SKILLS.md")
    return result


if __name__ == "__main__":
    run()