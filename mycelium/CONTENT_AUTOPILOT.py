#!/usr/bin/env python3
"""
CONTENT_AUTOPILOT.py -- The Infinite Content Machine
=====================================================
Every OMNIBUS cycle, this engine:
  1. Picks a random engine from mycelium/
  2. Reads its source code and docstring
  3. Generates a short dev.to article draft about it
  4. Queues it for DEV_TO_PUBLISHER to post

The system writes articles about itself. Forever.
Each article links to the ebook and shop.
Traffic -> Sales -> Mission funded.

Also generates "engine spotlight" social posts for the social queue.

Reads: mycelium/*.py, data/brain_state.json, data/live_wire_report.json,
       data/devto_state.json, data/content_autopilot_state.json
Writes: data/content_autopilot_state.json, data/article_drafts.json,
        data/social_queue.json (append)
"""
import json
import os
import sys
import random
import hashlib
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
PRODUCTS = Path("products")
SHOP_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center/shop.html"
REPO_URL = "https://github.com/meekotharaccoon-cell/meeko-nerve-center"

sys.path.insert(0, str(Path(__file__).parent))
try:
    from AI_CLIENT import ask, ai_available
except ImportError:
    def ask(messages, **kw): return ""
    def ai_available(): return False


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8"
    )


def load_state():
    state = load_json(DATA / "content_autopilot_state.json")
    if not state:
        state = {"articles_generated": 0, "engines_covered": [], "last_run": None}
    return state


def save_state(state):
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    save_json(DATA / "content_autopilot_state.json", state)


def pick_engine(already_covered):
    """Pick an interesting engine that hasn't been covered yet."""
    engines = sorted(MYCELIUM.glob("*.py"))
    engines = [e for e in engines if not e.name.startswith("__")]

    # Skip boring/generated/legacy engines
    skip_prefixes = ("GENERATED_", "LEGACY_SIFTED_", "__")
    interesting = [e for e in engines
                   if not any(e.name.startswith(p) for p in skip_prefixes)
                   and e.stem not in already_covered]

    if not interesting:
        # All covered -- reset and pick from full list
        interesting = [e for e in engines
                       if not any(e.name.startswith(p) for p in skip_prefixes)]

    if not interesting:
        return None

    # Weight toward engines with longer docstrings (more interesting)
    weighted = []
    for e in interesting:
        try:
            content = e.read_text(encoding="utf-8", errors="replace")
            doc_start = content.find('"""')
            if doc_start >= 0:
                doc_end = content.find('"""', doc_start + 3)
                doc_len = doc_end - doc_start if doc_end > doc_start else 0
            else:
                doc_len = 0
            weight = max(1, doc_len // 50)
            weighted.extend([e] * weight)
        except Exception:
            weighted.append(e)

    return random.choice(weighted) if weighted else random.choice(interesting)


def extract_engine_info(filepath):
    """Extract useful information about an engine from its source."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    name = filepath.stem

    # Extract docstring
    docstring = ""
    doc_start = source.find('"""')
    if doc_start >= 0:
        doc_end = source.find('"""', doc_start + 3)
        if doc_end > doc_start:
            docstring = source[doc_start + 3:doc_end].strip()

    # Extract reads/writes from docstring
    reads = []
    writes = []
    for line in docstring.split("\n"):
        line = line.strip()
        if line.lower().startswith("reads:"):
            reads = [r.strip() for r in line[6:].split(",")]
        elif line.lower().startswith("writes:"):
            writes = [w.strip() for w in line[7:].split(",")]

    # Count functions
    func_count = source.count("\ndef ")
    line_count = len(source.split("\n"))

    # Check wire report for connections
    wire_report = load_json(DATA / "live_wire_report.json")
    engines = wire_report.get("engines", {})
    engine_info = engines.get(name, {})
    wire_reads = engine_info.get("reads", [])
    wire_writes = engine_info.get("writes", [])

    return {
        "name": name,
        "filename": filepath.name,
        "docstring": docstring[:500],
        "first_line": docstring.split("\n")[0] if docstring else name,
        "reads": reads or wire_reads,
        "writes": writes or wire_writes,
        "functions": func_count,
        "lines": line_count,
        "has_run": "def run()" in source,
    }


def generate_article_with_ai(info):
    """Use AI to generate an article draft."""
    prompt = (
        "Write a short, engaging dev.to article (400-600 words) about this engine "
        "from the SolarPunk autonomous AI system. Make it practical and interesting "
        "for developers. Include the actual purpose, how it works, and one code insight. "
        "End with a link to the full system.\n\n"
        "Engine: %s\n"
        "Description: %s\n"
        "Functions: %d\n"
        "Lines: %d\n"
        "Reads: %s\n"
        "Writes: %s\n\n"
        "Format as markdown with a catchy title. Add dev.to frontmatter with tags: "
        "python, ai, automation, opensource. Set published: false."
    ) % (
        info["name"],
        info["docstring"][:300],
        info["functions"],
        info["lines"],
        ", ".join(info["reads"][:5]),
        ", ".join(info["writes"][:3]),
    )

    try:
        return ask([{"role": "user", "content": prompt}], max_tokens=1500,
                   system="You write concise, practical dev.to articles about autonomous AI systems. No fluff. Real code insights.")
    except Exception as e:
        print("    AI generation failed: %s" % e)
        return None


def generate_article_template(info):
    """Generate a template article without AI."""
    title = "Inside SolarPunk: How %s Works" % info["name"]
    h = hashlib.md5(title.encode()).hexdigest()[:8]

    reads_str = ", ".join(info["reads"][:3]) if info["reads"] else "system state"
    writes_str = ", ".join(info["writes"][:3]) if info["writes"] else "processed output"

    body = []
    body.append("---")
    body.append("title: %s" % title)
    body.append("published: false")
    body.append("tags: python, ai, automation, opensource")
    body.append("series: solarpunk-engine-spotlights")
    body.append("---")
    body.append("")
    body.append("SolarPunk is a 300-engine autonomous AI system. This is how one of those engines works.")
    body.append("")
    body.append("## What %s Does" % info["name"])
    body.append("")
    body.append(info["first_line"] if info["first_line"] != info["name"] else "A core engine in the SolarPunk nervous system.")
    body.append("")

    if info["docstring"] and len(info["docstring"]) > 50:
        # Pull the most interesting paragraph from the docstring
        paragraphs = [p.strip() for p in info["docstring"].split("\n\n") if len(p.strip()) > 30]
        if paragraphs:
            body.append(paragraphs[0])
            body.append("")

    body.append("## The Numbers")
    body.append("")
    body.append("- **%d functions** across %d lines of Python" % (info["functions"], info["lines"]))
    body.append("- **Reads:** %s" % reads_str)
    body.append("- **Writes:** %s" % writes_str)
    body.append("- **Has run() entry point:** %s" % ("Yes" if info["has_run"] else "No"))
    body.append("")
    body.append("## How It Fits")
    body.append("")
    body.append("Every engine in SolarPunk follows the same pattern: read JSON, process, write JSON. ")
    body.append("No databases. No message queues. Just files and Python scripts.")
    body.append("")
    body.append("%s reads from %s and writes to %s. " % (info["name"], reads_str, writes_str))
    body.append("Other engines downstream pick up its output automatically.")
    body.append("")
    body.append("## Try It")
    body.append("")
    body.append("```bash")
    body.append("git clone %s" % REPO_URL)
    body.append("python mycelium/%s" % info["filename"])
    body.append("```")
    body.append("")
    body.append("Or run all 300 engines: `python mycelium/OMNIBUS.py`")
    body.append("")
    body.append("---")
    body.append("")
    body.append("*SolarPunk: 300 engines, 4,489 wires, zero paid APIs. 99%% mutual aid.*")
    body.append("*[Full guide](%s) | [Source](%s)*" % (SHOP_URL, REPO_URL))

    return "\n".join(body)


def generate_social_post(info):
    """Generate a short social media post about the engine."""
    templates = [
        "Engine spotlight: %s -- %s. Part of a 300-engine autonomous system running on zero paid APIs. %s",
        "How does a self-healing AI system work? One engine at a time. Today: %s -- %s %s",
        "%s: %d functions, %d lines of Python, reads %s, writes %s. One of 300 engines in SolarPunk. %s",
    ]

    t = random.choice(templates)
    first_line = info["first_line"][:80] if info["first_line"] != info["name"] else "autonomous engine"

    if "%d" in t:
        post = t % (info["name"], info["functions"], info["lines"],
                     ", ".join(info["reads"][:2]) or "data",
                     ", ".join(info["writes"][:1]) or "output",
                     REPO_URL)
    else:
        post = t % (info["name"], first_line, REPO_URL)

    return post[:280]


def run():
    print("CONTENT AUTOPILOT -- The Infinite Content Machine")
    print("=" * 50)

    state = load_state()
    print("  Articles generated so far: %d" % state["articles_generated"])
    print("  Engines covered: %d" % len(state.get("engines_covered", [])))

    # Pick an engine
    print("\n  [1/4] Picking an engine to spotlight...")
    engine_path = pick_engine(state.get("engines_covered", []))
    if not engine_path:
        print("    No engines available")
        save_state(state)
        return

    info = extract_engine_info(engine_path)
    if not info:
        print("    Could not extract info from %s" % engine_path.name)
        save_state(state)
        return

    print("    Selected: %s (%d lines, %d functions)" % (info["name"], info["lines"], info["functions"]))

    # Generate article
    print("\n  [2/4] Generating article draft...")
    article = None
    if ai_available():
        print("    Using AI generation...")
        article = generate_article_with_ai(info)

    if not article:
        print("    Using template generation...")
        article = generate_article_template(info)

    print("    Article: %d characters" % len(article))

    # Save article draft
    print("\n  [3/4] Saving article draft...")
    drafts = load_json(DATA / "article_drafts.json")
    if not isinstance(drafts, dict):
        drafts = {"drafts": []}
    if "drafts" not in drafts:
        drafts["drafts"] = []

    draft_entry = {
        "engine": info["name"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "content": article,
        "char_count": len(article),
        "status": "draft",
        "ai_generated": ai_available(),
    }
    drafts["drafts"].append(draft_entry)
    drafts["drafts"] = drafts["drafts"][-50:]  # Keep last 50
    save_json(DATA / "article_drafts.json", drafts)

    # Generate social post
    print("\n  [4/4] Generating social post...")
    social_post = generate_social_post(info)

    social_queue = load_json(DATA / "social_queue.json")
    if not isinstance(social_queue, dict):
        social_queue = {"queue": []}
    if "queue" not in social_queue:
        social_queue["queue"] = []

    social_queue["queue"].append({
        "text": social_post,
        "source": "CONTENT_AUTOPILOT",
        "engine": info["name"],
        "queued_at": datetime.now(timezone.utc).isoformat(),
    })
    social_queue["queue"] = social_queue["queue"][-100:]
    save_json(DATA / "social_queue.json", social_queue)
    print("    Social post queued: %s..." % social_post[:60])

    # Update state
    state["articles_generated"] = state.get("articles_generated", 0) + 1
    covered = state.get("engines_covered", [])
    if info["name"] not in covered:
        covered.append(info["name"])
    state["engines_covered"] = covered
    save_state(state)

    print("\n  === CONTENT AUTOPILOT SUMMARY ===")
    print("  Engine spotlighted:  %s" % info["name"])
    print("  Article length:      %d chars" % len(article))
    print("  Total articles:      %d" % state["articles_generated"])
    print("  Engines covered:     %d / ~300" % len(covered))
    print("  Social post queued:  Yes")
    print("\n  The system writes about itself. The content never stops.")


if __name__ == "__main__":
    run()
