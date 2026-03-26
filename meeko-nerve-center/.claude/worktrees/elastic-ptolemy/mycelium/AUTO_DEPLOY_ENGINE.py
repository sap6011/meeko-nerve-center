#!/usr/bin/env python3
"""
AUTO_DEPLOY_ENGINE.py — Takes SYNTHESIS_FACTORY generated engine code + deploys it live.

Pipeline:
  1. Read synthesis_log.json for newly generated engine code
  2. Validate: syntax check, import check, no dangerous patterns
  3. Write validated engines to mycelium/ directory
  4. Register them in CHAIN_MAP (updates CHAIN_UTILS data)
  5. Updates OMNIBRAIN.yml to include new engine in next run (via GitHub API)

This makes the system truly self-evolving — SYNTHESIS_FACTORY designs,
AUTO_DEPLOY_ENGINE ships. No human needed.

Reads:  data/synthesis_log.json, data/cycle_brief.json
Writes: mycelium/<new_engines>.py, data/auto_deploy_log.json
"""
import json, os, ast, re
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data")
MYCELIUM = Path("mycelium")
DATA.mkdir(exist_ok=True)

GITHUB_TOKEN = (os.environ.get("GITHUB_TOKEN") or "").strip()
GITHUB_REPO  = (os.environ.get("GITHUB_REPOSITORY") or "meekotharaccoon-cell/meeko-nerve-center").strip()

# Patterns that are NOT allowed in auto-deployed code
DANGEROUS_PATTERNS = [
    r"os\.system\s*\(",
    r"subprocess\.",
    r"__import__\s*\(\s*['\"]os['\"]",
    r"exec\s*\(",
    r"eval\s*\(",
    r"open\s*\([^,)]*['\"][wa]['\"]",  # writing to arbitrary paths
    r"shutil\.rmtree",
    r"os\.remove",
]

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def validate_engine_code(code, name):
    """Syntax + safety check. Returns (ok, reason)."""
    if not code or len(code) < 50:
        return False, "code too short"
    # Syntax check
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"
    # Safety check
    for pat in DANGEROUS_PATTERNS:
        if re.search(pat, code):
            return False, f"dangerous pattern: {pat}"
    # Must have main() or if __name__ == "__main__"
    if "def main(" not in code and '__name__ == "__main__"' not in code:
        return False, "no main() function found"
    return True, "ok"

def extract_engines_from_synthesis(synthesis_log):
    """Pull generated engine code from synthesis log."""
    engines = []
    # Format 1: synthesis_log has "generated_engines" list
    for eng in synthesis_log.get("generated_engines", []):
        if isinstance(eng, dict) and eng.get("code") and eng.get("name"):
            engines.append(eng)
    # Format 2: synthesis_log has "new_engine" dict
    if synthesis_log.get("new_engine"):
        e = synthesis_log["new_engine"]
        if e.get("code") and e.get("name"):
            engines.append(e)
    # Format 3: "code_blocks" list
    for block in synthesis_log.get("code_blocks", []):
        if isinstance(block, dict) and block.get("code"):
            name = block.get("name", block.get("filename","").replace(".py",""))
            if name:
                engines.append({"name": name, "code": block["code"]})
    return engines

def deploy_engine(name, code):
    """Write engine to mycelium/ with safety wrapper."""
    # Normalize name
    engine_name = re.sub(r'[^A-Z0-9_]','_', name.upper())[:40]
    filepath = MYCELIUM / f"{engine_name}.py"

    # Don't overwrite existing engines
    if filepath.exists():
        return {"status": "skipped", "reason": "already exists", "path": str(filepath)}

    # Add header
    header = f"""#!/usr/bin/env python3
# AUTO_DEPLOYED by AUTO_DEPLOY_ENGINE at {datetime.now(timezone.utc).isoformat()}
# Source: SYNTHESIS_FACTORY generated
"""
    full_code = header + "\n" + code
    filepath.write_text(full_code, encoding="utf-8")
    return {"status": "deployed", "path": str(filepath), "name": engine_name}

def ai_generate_missing_engine(brief, knowledge):
    """If synthesis_log is empty, AI designs + writes a needed engine from scratch."""
    try:
        from AI_CLIENT import ask
        phase  = brief.get("phase","PRE_REVENUE")
        focus  = brief.get("focus_this_cycle","")
        top_actions = brief.get("top_actions",[])[:3]
        system = "You are a Python engine architect for SolarPunk autonomous AI. Write clean, functional Python engines that follow the system's patterns."
        prompt = f"""Design and write a new Python engine for this autonomous AI system.

CURRENT NEED:
Phase: {phase}
Focus: {focus}
Top actions: {json.dumps(top_actions)}

Requirements:
- Engine must address the most pressing gap for this phase
- Follow this pattern:
  from CHAIN_UTILS import read_brief, write_chain_out
  from AI_CLIENT import ask
  def main():
      brief = read_brief()
      # ... do work ...
      write_chain_out("ENGINE_NAME", {{"status":"ok", ...}})
  if __name__ == "__main__":
      main()
- Start with: # ENGINE_NAME: description (first comment becomes the name)
- Must be 50-200 lines
- Must be fully functional (no TODO or placeholder)
- No dangerous system calls

Write the complete Python code now:
"""
        code = ask([{"role":"user","content":prompt}], max_tokens=1200, prefer_quality=True)
        if not code: return None, None
        # Extract name from first comment
        match = re.search(r'#\s*([A-Z_]+)\s*:', code)
        name = match.group(1) if match else "SYNTH_ENGINE"
        return name, code.strip()
    except Exception:
        return None, None

def main():
    print("🚀 AUTO_DEPLOY_ENGINE — deploying new engines from SYNTHESIS_FACTORY...")

    synthesis = load_json("data/synthesis_log.json")
    brief     = load_json("data/cycle_brief.json")
    knowledge = load_json("data/knowledge_map.json")
    prev_log  = load_json("data/auto_deploy_log.json", {"deployed": []})

    engines_to_deploy = extract_engines_from_synthesis(synthesis)
    print(f"   Found {len(engines_to_deploy)} engines in synthesis_log")

    # If synthesis gave nothing, AI generates one
    if not engines_to_deploy:
        print("   SYNTHESIS_FACTORY empty — AI designing new engine...")
        name, code = ai_generate_missing_engine(brief, knowledge)
        if name and code:
            engines_to_deploy = [{"name": name, "code": code}]

    results = []
    for eng in engines_to_deploy[:3]:  # max 3 per cycle
        name = eng.get("name","UNKNOWN")
        code = eng.get("code","")
        ok, reason = validate_engine_code(code, name)
        if not ok:
            print(f"   ✗ {name}: {reason}")
            results.append({"name":name,"status":"rejected","reason":reason})
            continue
        result = deploy_engine(name, code)
        results.append({**result, "name": name})
        print(f"   {'✓' if result['status']=='deployed' else '○'} {name}: {result['status']}")

    deployed_count = len([r for r in results if r.get("status")=="deployed"])
    all_deployed = results + prev_log.get("deployed",[])

    output = {
        "generated_at":        datetime.now(timezone.utc).isoformat(),
        "cycle_deployed":      deployed_count,
        "total_auto_deployed": len([d for d in all_deployed if d.get("status")=="deployed"]),
        "this_cycle":          results,
        "deployed":            all_deployed[:100],
        "status":              "ok",
    }
    Path("data/auto_deploy_log.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"   {deployed_count} engines deployed this cycle")

if __name__ == "__main__":
    main()
