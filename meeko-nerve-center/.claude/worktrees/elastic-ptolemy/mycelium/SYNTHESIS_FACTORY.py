#!/usr/bin/env python3
"""
SYNTHESIS_FACTORY — Auto-builds new engines using Claude API
PATCHED v2: Hard boundaries. Can NEVER touch .github/ or delete existing files.
Only creates NEW .py files in mycelium/ and writes to data/.
NO git merge. NO git checkout. NO git rm. Add only.
"""
import os, json, requests, subprocess
from pathlib import Path
from datetime import datetime
_ak = "ANTHROP" + "IC_API_KEY"

API_KEY  = os.environ.get(_ak, "")
FORBIDDEN_PATHS = [".github", ".git", "GUARDIAN", "OMNIBRAIN", "SOLARPUNK_LOOP", "BUILD_YOURSELF"]
ALLOWED_DIRS    = ["mycelium", "data"]

def safe_to_write(filepath: str) -> bool:
    """Returns True ONLY if path is safe to write."""
    fp = filepath.replace("\\", "/").lower()
    for forbidden in FORBIDDEN_PATHS:
        if forbidden.lower() in fp:
            print(f"⛔ BLOCKED write to forbidden path: {filepath}")
            return False
    for allowed in ALLOWED_DIRS:
        if fp.startswith(allowed + "/") or fp.startswith("./" + allowed + "/"):
            return True
    print(f"⛔ BLOCKED write outside allowed dirs: {filepath}")
    return False

def safe_git_add_only():
    """Only git add mycelium/ and data/ — never anything else."""
    subprocess.run(["git", "add", "mycelium/", "data/"], capture_output=True)

def get_gen_number():
    log_f = Path("data/synthesis_log.json")
    if log_f.exists():
        try:
            log = json.loads(log_f.read_text())
            return log.get("gen_count", 0) + 1
        except: pass
    return 1

def discover_opportunities():
    """What engine combinations don't exist yet but should?"""
    myc = Path("mycelium")
    existing = sorted([f.name for f in myc.glob("*.py") if not f.name.startswith("__")]) if myc.exists() else []
    data_f = Path("data")
    data_files = sorted([f.name for f in data_f.glob("*.json")]) if data_f.exists() else []
    brain_state = {}
    bf = Path("data/brain_state.json")
    if bf.exists():
        try: brain_state = json.loads(bf.read_text())
        except: pass
    # LOOP INTEGRATION: enrich brain_state with cycle_brief context
    cb = Path("data/cycle_brief.json")
    if cb.exists():
        try:
            brief = json.loads(cb.read_text())
            brain_state["top_priority"] = brief.get("focus_this_cycle", "")
            brain_state["phase"] = brief.get("phase", "")
            brain_state["cycle_actions"] = brief.get("top_actions", [])
        except: pass
    seed = {}
    sf = Path("data/omnibrain_seed.json")
    if sf.exists():
        try: seed = json.loads(sf.read_text())
        except: pass
    brave_intel, getscreen_queue = {}, {}
    for fpath, target in [("data/brave_bridge_report.json", "brave"),
                          ("data/getscreen_report.json", "getscreen")]:
        fp = Path(fpath)
        if fp.exists():
            try:
                obj = json.loads(fp.read_text())
                if target == "brave": brave_intel = obj.get("intelligence", {})
                else: getscreen_queue = {"pending": obj.get("pending_tasks", 0),
                                         "top_task": obj.get("synthesis", {}).get("top_task", "")}
            except: pass
    critical_lessons = []
    lf = Path("data/lessons.json")
    if lf.exists():
        try:
            ls = json.loads(lf.read_text())
            critical_lessons = [l.get("lesson","") for l in (ls if isinstance(ls, list) else [])
                                 if l.get("priority") in ("critical", "high")][:5]
        except: pass
    return existing, data_files, brain_state, seed, brave_intel, getscreen_queue, critical_lessons

def synthesize_new_engine(existing, data_files, brain_state, seed, brave_intel=None, getscreen_queue=None, critical_lessons=None):
    if not API_KEY:
        print("No API key — skipping synthesis")
        return None
    gen = get_gen_number()
    seed_instrs = seed.get("instructions", [])
    priority    = brain_state.get("top_priority", "")
    web_priority = (brave_intel or {}).get("priority_action", "")
    desktop_task = (getscreen_queue or {}).get("top_task", "")
    lessons_context = critical_lessons or []
    prompt = f"""You are SYNTHESIS_FACTORY gen {gen} for SolarPunk — Meeko's autonomous income system.

YOUR JOB: Build ONE new Python engine that doesn't exist yet.
This engine will run in GitHub Actions and create passive income for Meeko.

EXISTING ENGINES: {existing}
AVAILABLE DATA: {data_files}
CURRENT PRIORITY: {priority}
SEED INSTRUCTIONS: {seed_instrs}
WEB INTELLIGENCE: {web_priority}
DESKTOP QUEUE: {desktop_task}
CRITICAL LESSONS (do NOT repeat failed approaches): {lessons_context}

INCOME STREAMS TO BUILD FOR:
1. Gaza Rose Gallery — Gumroad automation, product listings, sales tracking
2. Medium Partner Program — daily AI articles auto-published
3. Substack newsletter — auto-written and scheduled
4. Affiliate marketing — auto-blog posts with affiliate links
5. WhatsApp automation — build and sell bot services
6. Prompt packs on Gumroad — generate and list AI templates
7. RapidAPI — wrap free APIs, sell value-add tier

RULES YOU MUST FOLLOW:
- Engine must write output to data/[engine_name]_output.json
- Engine reads config from os.environ (GitHub Secrets)
- Only import: os, json, requests, datetime, pathlib, smtplib, email, re, urllib, time, random
- Engine must be fully functional and self-contained
- NO subprocess calls that use git merge, git checkout, git rm, or git reset
- Do NOT write anything to .github/ directory
- If engine needs an API key, read from os.environ and handle missing gracefully

Pick the engine that provides the MOST value toward first passive income dollar.

Respond ONLY with valid JSON (no markdown, no fences):
{{
  "filename": "engine_name.py",
  "description": "one sentence",
  "income_stream": "which stream this serves",
  "how_it_makes_money": "specific mechanism",
  "code": "complete python file as string — production ready"
}}"""
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API_KEY,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-6","max_tokens":6000,
                  "messages":[{"role":"user","content":prompt}]},timeout=120)
        r.raise_for_status()
        text = r.json()["content"][0]["text"]
        s,e = text.find("{"), text.rfind("}")+1
        if s < 0: return None
        return json.loads(text[s:e])
    except Exception as ex:
        print(f"Synthesis API error: {ex}")
        return None

def sanitize_code(code: str) -> str:
    """Strip recursive os.getenv nesting corruption before writing any engine.
    Also fixes stale model names.
    """
    import re as _re
    KEYS = ["os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")")")")")")")")")")")")")")")")")")")")", "GROQ_API_KEY", "HF_TOKEN", "OPENROUTER_KEY",
            "GEMINI_API_KEY", "GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "GUMROAD_ACCESS_TOKEN",
            "X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET",
            "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "GITHUB_TOKEN"]
    lines = code.split("\n")
    fixed = []
    for line in lines:
        for key in KEYS:
            p1 = r'os\.environ\.get\("(?:os\.[^"]*"[^"]*"[^"]*)*' + _re.escape(key) + r'(?:[^"]*"[^"]*"[^"]*)*"'
            if _re.search(p1, line):
                line = _re.sub(p1, f'os.environ.get("{key}"', line)
            p2 = r'os\.getenv\("(?:os\.[^"]*"[^"]*"[^"]*)*' + _re.escape(key) + r'(?:[^"]*"[^"]*"[^"]*)*"\)'
            if _re.search(p2, line):
                line = _re.sub(p2, key, line)
        fixed.append(line)
    code = "\n".join(fixed)
    # Fix stale model names (split strings avoid self-corruption when sanitizer is scanned)
    code = code.replace("claude-sonnet-4-2" + "0250514", "claude-sonnet-4-6")
    code = code.replace("claude-3-5-sonnet-2" + "0241022", "claude-sonnet-4-6")
    code = code.replace("claude-3-haiku-2" + "0240307", "claude-haiku-4-5-20251001")
    return code


def write_engine(result):
    if not result: return False
    fname = result.get("filename","")
    code  = result.get("code","")
    if not fname or not code: return False
    if not fname.endswith(".py"):
        print(f"⛔ BLOCKED non-py: {fname}")
        return False
    # Strip any path components — filename only
    fname = Path(fname).name
    target_path = f"mycelium/{fname}"
    if not safe_to_write(target_path):
        return False
    # Sanitize before writing — block corruption at the gate
    code = sanitize_code(code)
    target = Path("mycelium") / fname
    target.write_text(code)
    print(f"✅ Synthesized: {fname}")
    print(f"   → {result.get('description','')}")
    print(f"   💰 {result.get('income_stream','')}")
    return True

def update_log(result, gen):
    log_f = Path("data/synthesis_log.json")
    log = {"gen_count": 0, "built": []}
    if log_f.exists():
        try: log = json.loads(log_f.read_text())
        except: pass
    if result:
        log["built"].append({
            "gen": gen, "filename": result.get("filename",""),
            "description": result.get("description",""),
            "income_stream": result.get("income_stream",""),
            "built_at": datetime.now().isoformat()
        })
    log["gen_count"] = gen
    log["last_run"] = datetime.now().isoformat()
    Path("data").mkdir(exist_ok=True)
    log_f.write_text(json.dumps(log, indent=2))

def main():
    gen = get_gen_number()
    print(f"🏭 SYNTHESIS_FACTORY gen {gen} activating...")
    print(f"   Safety: ONLY writing to mycelium/ and data/")
    existing, data_files, brain_state, seed, brave_intel, getscreen_queue, critical_lessons = discover_opportunities()
    print(f"   Existing engines: {len(existing)} | Critical lessons: {len(critical_lessons)}")
    result = synthesize_new_engine(existing, data_files, brain_state, seed, brave_intel, getscreen_queue, critical_lessons)
    wrote  = write_engine(result)
    update_log(result if wrote else None, gen)
    if wrote:
        # Safe git add ONLY — never touches .github/
        safe_git_add_only()
        print(f"   Staged for commit (mycelium/ and data/ only)")
    else:
        print("   Nothing new synthesized this run")

if __name__ == "__main__":
    main()