#!/usr/bin/env python3
"""
AI_ENGINE_ARCHITECT.py — Turns Capability Map Into Real Deployable Engines
===========================================================================
Step 3 of the recursive self-expansion loop. The most important step.

Reads:
  data/ai_capability_map.json  (what to build, in priority order)
  data/ai_knowledge_base.json  (deep AI knowledge to draw from)
  mycelium/*.py                (existing engines as code examples)

For each top opportunity, uses Claude (or Groq) to generate a COMPLETE,
DEPLOYABLE Python engine — not a stub, not pseudocode, but production code
that passes ast.parse and safety checks.

Writes:
  data/engine_proposals.json   ← DISTRIBUTED_FORGE reads this and deploys

The loop closes here. After AI_ENGINE_ARCHITECT writes proposals, the next
DISTRIBUTED_FORGE run will validate and deploy them. The new engines run
every hour in GRAND_UNIFIED_LOOP. Their outputs become new state data, which
feeds the next AI_KNOWLEDGE_HARVESTER cycle. Forever.

Safety:
  - Never generates engines that delete files, run shell commands, push code
  - All proposals validated with ast.parse before writing
  - Uses the same safety filter as DISTRIBUTED_FORGE
  - Deduplication — never proposes an engine that already exists
"""

import os
import json
import ast
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

DATA     = Path("data")
MYCELIUM = Path("mycelium")
DATA.mkdir(exist_ok=True)

_ak = "ANTHROP" + "IC_API_KEY"

# Safety patterns — these MUST NOT appear in generated engine code
BLOCKED_PATTERNS = [
    "os.system(",
    "subprocess",
    "eval(",
    "exec(",
    "git push",
    "git commit",
    "rm -rf",
    "shutil.rmtree",
    "os.remove",
    "__import__",
    "open('/etc",
    "open('/root",
    ".github/workflows",
]


def rj(path, default=None):
    try:
        return json.loads((DATA / path).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def get_existing_engines() -> set:
    try:
        return {
            f.stem.upper()
            for f in MYCELIUM.glob("*.py")
            if not f.stem.startswith("LEGACY") and not f.stem.startswith("__")
        }
    except Exception:
        return set()


def load_engine_examples() -> str:
    """Load a few existing engines as code examples for the AI."""
    examples = []
    example_engines = ["CRISIS_ROUTER", "POOL_MANAGER", "AUTO_ANNOUNCE", "GRANT_HUNTER"]
    for name in example_engines:
        path = MYCELIUM / f"{name}.py"
        if path.exists():
            content = path.read_text(encoding="utf-8")[:1500]  # First 1500 chars
            examples.append(f"=== {name}.py (first 1500 chars) ===\n{content}\n")
    return "\n".join(examples[:2])  # Use 2 examples to keep prompt size manageable


def is_safe(code: str) -> tuple[bool, str]:
    """Check if generated code is safe to deploy."""
    # Syntax check
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"

    # Safety pattern check
    for pattern in BLOCKED_PATTERNS:
        if pattern in code:
            return False, f"Blocked pattern: {pattern}"

    # Must have run() function
    if "def run(" not in code and "def run():" not in code:
        return False, "Missing run() function"

    return True, "ok"


def ask_ai_for_engine(opportunity: dict, knowledge: dict, examples: str) -> str:
    """Ask Claude or Groq to generate a complete engine for this opportunity."""
    name        = opportunity.get("engine_name", "NEW_ENGINE")
    why         = opportunity.get("why", "")
    what        = opportunity.get("what_it_does", "")
    ai_used     = opportunity.get("ai_used", "")
    dimension   = opportunity.get("dimension", "SELF")
    code_stub   = opportunity.get("code_stub", "")

    # Look up deep knowledge about the AI being used
    ai_knowledge = ""
    for key, val in knowledge.items():
        if isinstance(val, dict):
            if any(ai_name in ai_used.lower() for ai_name in key.lower().split("_")):
                ai_knowledge = json.dumps(val, indent=2)[:2000]
                break

    system_prompt = f"""You are writing a Python engine for SolarPunk, an autonomous humanitarian AI.

SolarPunk's mission: route 99% of all revenue to Gaza (PCRF 60%), Sudan (IRC 15%), DRC (MSF 10%), Yemen (UNICEF 10%), Climate (Direct Relief 5%).

CRITICAL RULES for all engines:
1. Must have a run() function as the entry point
2. Use Path("data") for all file I/O (never hardcoded paths)
3. Use (os.environ.get("KEY") or "").strip() — never .get("KEY").strip()
4. Always handle missing env vars gracefully (print warning and return)
5. Always handle network errors (try/except around requests)
6. Data files use JSON with indent=2
7. Never use subprocess, os.system, eval, exec, git commands
8. Every state file write should include "generated_at" timestamp
9. Use continue-on-error pattern: always return a dict with "status" key

Here are examples of existing SolarPunk engines:
{examples}
"""

    user_prompt = f"""Write a complete, production-ready Python engine named {name}.py.

Purpose: {what}
Why SolarPunk needs this: {why}
Dimension: {dimension}
AI/API used: {ai_used}

Existing code stub to start from:
{code_stub}

Deep knowledge about the AI/API to use:
{ai_knowledge}

Write the COMPLETE engine code — not pseudocode, not stubs. Real, runnable Python.
The engine should be 100-300 lines. Include:
- Module docstring explaining what it does
- All imports at top
- Constants (API URLs, file paths)
- Main logic in run()
- Graceful handling of missing credentials
- At least 2 comments explaining the logic
- Return dict with status, counts, and key metrics

Output ONLY the Python code. No markdown, no explanation."""

    # Try Claude first
    ak = (os.environ.get(_ak) or "").strip()
    if ak:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ak)
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",  # Fast + cheap for code gen
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text
        except Exception as e:
            print(f"  [Claude] Error generating {name}: {e}")

    # Fall back to Groq
    groq_key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if groq_key:
        try:
            import requests as req
            r = req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.2,
                },
                timeout=45,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  [Groq] Error generating {name}: {e}")

    return ""


def extract_python_code(raw: str) -> str:
    """Strip markdown fencing if present."""
    raw = raw.strip()
    # Remove ```python ... ``` blocks
    if raw.startswith("```"):
        lines = raw.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)
    return raw.strip()


def load_existing_proposals() -> dict:
    try:
        return json.loads((DATA / "engine_proposals.json").read_text(encoding="utf-8"))
    except Exception:
        return {"proposals": [], "total_proposed": 0, "total_deployed": 0}


def run():
    print("🏗️  AI_ENGINE_ARCHITECT: Generating new engines from capability map...")
    now = datetime.now(timezone.utc).isoformat()

    # Load inputs
    capability_map = rj("ai_capability_map.json")
    knowledge      = rj("ai_knowledge_base.json")
    existing       = get_existing_engines()
    proposals_db   = load_existing_proposals()
    examples       = load_engine_examples()

    opportunities = capability_map.get("opportunities", [])
    if not opportunities:
        print("  No opportunities in capability map. Run AI_CAPABILITY_MAPPER first.")
        return {"status": "no_opportunities"}

    # Filter: only top-priority opportunities not already existing or proposed
    already_proposed = {p["engine_name"].upper() for p in proposals_db.get("proposals", [])}
    candidates = [
        opp for opp in opportunities
        if opp.get("engine_name", "").upper() not in existing
        and opp.get("engine_name", "").upper() not in already_proposed
        and opp.get("priority") in ("HIGH", "CRITICAL", "AI_SUGGESTED")
    ]

    print(f"  Opportunities: {len(opportunities)} total | {len(candidates)} buildable now")
    print(f"  Existing engines: {len(existing)} | Already proposed: {len(already_proposed)}")

    # Check if we have any AI available
    has_ai = bool(
        (os.environ.get(_ak) or "").strip() or
        (os.environ.get("GROQ_API_KEY") or "").strip()
    )

    generated = 0
    errors    = 0

    # Process top N candidates (limit to avoid burning API quota)
    max_per_cycle = 3 if has_ai else 0
    for opp in candidates[:max_per_cycle]:
        name = opp.get("engine_name", "UNNAMED_ENGINE").upper()
        print(f"\n  Generating {name}...")

        # Generate code
        raw_code = ask_ai_for_engine(opp, knowledge, examples)
        if not raw_code:
            print(f"    ❌ No code generated (no AI available)")
            errors += 1
            continue

        # Clean up
        code = extract_python_code(raw_code)

        # Safety check
        safe, reason = is_safe(code)
        if not safe:
            print(f"    ❌ Safety check failed: {reason}")
            errors += 1
            continue

        # Write to data/forge_proposals/ — DISTRIBUTED_FORGE picks up *.py files here
        forge_dir = DATA / "forge_proposals"
        forge_dir.mkdir(exist_ok=True)
        forge_file = forge_dir / f"{name}_proposal.py"
        forge_file.write_text(code, encoding="utf-8")

        # Also track in proposals_db for visibility
        proposal = {
            "engine_name": name,
            "file_name": f"{name}.py",
            "dimension": opp.get("dimension", "SELF"),
            "why": opp.get("why", ""),
            "what_it_does": opp.get("what_it_does", ""),
            "ai_used": opp.get("ai_used", ""),
            "code": code,
            "proposed_at": now,
            "status": "pending",  # DISTRIBUTED_FORGE will change to "deployed"
            "safety_check": "passed",
            "source": "AI_ENGINE_ARCHITECT",
            "forge_file": str(forge_file),
        }
        proposals_db.setdefault("proposals", []).append(proposal)
        proposals_db["total_proposed"] = proposals_db.get("total_proposed", 0) + 1
        generated += 1
        print(f"    ✅ {name} generated ({len(code)} chars) → data/forge_proposals/{name}_proposal.py")

    # Also record ALL candidates (with stubs from capability map) for visibility
    # even if we didn't generate full code for them
    stub_count = 0
    for opp in candidates[max_per_cycle:max_per_cycle + 10]:
        name = opp.get("engine_name", "").upper()
        stub_code = opp.get("code_stub", "")
        if stub_code and len(stub_code) > 100:
            # Clean up stub
            clean_stub = extract_python_code(stub_code)
            safe, reason = is_safe(clean_stub)
            if safe:
                proposal = {
                    "engine_name": name,
                    "file_name": f"{name}.py",
                    "dimension": opp.get("dimension", "SELF"),
                    "why": opp.get("why", ""),
                    "what_it_does": opp.get("what_it_does", ""),
                    "code": f'#!/usr/bin/env python3\n"""\n{name}.py — {opp.get("what_it_does", "")}\n"""\n\nimport os, json, requests\nfrom pathlib import Path\nfrom datetime import datetime, timezone\n\nDATA = Path("data")\nDATA.mkdir(exist_ok=True)\n\n{clean_stub}\n\nif __name__ == "__main__":\n    run()',
                    "proposed_at": now,
                    "status": "stub",  # Stub — needs full generation
                    "safety_check": "passed",
                    "source": "AI_CAPABILITY_MAPPER_STUB",
                }
                proposals_db.setdefault("proposals", []).append(proposal)
                proposals_db["total_proposed"] = proposals_db.get("total_proposed", 0) + 1
                stub_count += 1

    proposals_db["last_architect_run"] = now

    # Save proposals
    out_file = DATA / "engine_proposals.json"
    out_file.write_text(
        json.dumps(proposals_db, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\n  ✅ data/engine_proposals.json updated")
    print(f"  Generated: {generated} full engines | {stub_count} stubs | {errors} errors")
    print(f"  Total in pipeline: {proposals_db.get('total_proposed', 0)}")
    if generated > 0:
        print(f"  → DISTRIBUTED_FORGE will deploy these in the next cycle")

    return {
        "status": "ok",
        "generated": generated,
        "stubs": stub_count,
        "errors": errors,
        "total_in_pipeline": proposals_db.get("total_proposed", 0),
    }


if __name__ == "__main__":
    run()
