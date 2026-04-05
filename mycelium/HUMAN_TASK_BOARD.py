#!/usr/bin/env python3
"""HUMAN_TASK_BOARD -- Consolidate every human-action-required task across
the entire SolarPunk data layer into a single, prioritised, deduplicated
task board.

Scans all data/*.json files for patterns that indicate a human needs to
do something (create account, paste text, visit URL, upload file, etc.).
Aggregates into categories, prioritises by revenue impact, deduplicates,
and groups by time-session.

Outputs:
  data/human_task_board.json   -- full structured task board
  docs/tasks.html              -- interactive dark-themed dashboard

Zero secrets. Zero paid APIs. Pure file scanning.
"""

import json
import time
import re
import hashlib
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
DOCS = Path("docs")
DOCS.mkdir(exist_ok=True)

# -----------------------------------------------------------------------
# Detection patterns
# -----------------------------------------------------------------------

# Keys that signal human action
ACTION_KEYS = {
    "human_action", "human_action_required", "action_needed", "manual_step",
    "next_step", "blocker", "critical_path", "checklist", "todo", "steps",
    "fix", "action", "recommended_fixes", "pending_actions", "suggestions",
    "infrastructure_queue", "investments", "product_pipeline", "allocation",
    "buy_url", "setup_time",
}

# Value substrings that signal human action (case-insensitive matching)
ACTION_VALUE_PATTERNS = [
    r"\bHUMAN\b", r"\bmanual\b", r"\bcreate account\b", r"\bsign up\b",
    r"\bsignup\b", r"\bpaste\b", r"\bclick\b", r"\bgo to\b", r"\bvisit\b",
    r"\bupload\b", r"\blog in\b", r"\blogin\b", r"\bopen\b.*\bdashboard\b",
    r"\bpublish\b", r"\bset price\b", r"\badd tags?\b", r"\bverify\b",
    r"\bpost\b.*\blink\b", r"\bshare\b.*\blink\b", r"\bdownload\b",
    r"\bapply\b", r"\bsubmit\b", r"\bregister\b", r"\bconfigure\b",
    r"\bsetup\b", r"\bset up\b", r"\bbuy\b", r"\bpurchase\b",
    r"\bfile\b.*\bDBA\b", r"\btrademark\b", r"\bLLC\b",
    r"\bAPI key\b", r"\bapp password\b", r"\baccess token\b",
    r"\bfix\b.*\blink\b", r"\bfix\b.*\bURL\b", r"\bredirect\b",
]
_compiled_patterns = [re.compile(p, re.IGNORECASE) for p in ACTION_VALUE_PATTERNS]

# Category classification keywords
CATEGORY_RULES = [
    ("REVENUE",        ["list", "product", "sell", "price", "shop", "store",
                        "buy link", "buy button", "storefront", "gumroad",
                        "ko-fi", "kofi", "revenue", "sale", "first dollar",
                        "listing", "payment"]),
    ("OUTREACH",       ["post", "social", "twitter", "bluesky", "mastodon",
                        "reddit", "dev.to", "community", "share", "tweet",
                        "thread", "discussion", "announce", "promotion"]),
    ("INFRASTRUCTURE", ["api key", "token", "domain", "hosting", "vps",
                        "credential", "app password", "github token",
                        "groq", "devto", "notion", "seo", "meta tag"]),
    ("LEGAL",          ["dba", "trademark", "llc", "legal", "filing",
                        "business name", "ein"]),
    ("GRANTS",         ["grant", "funding", "ngo", "application",
                        "foundation", "award"]),
    ("CONTENT",        ["article", "publish", "write", "draft", "newsletter",
                        "email", "content", "calendar", "dev.to article"]),
]


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _rj(name, fallback=None):
    p = DATA / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return fallback if fallback is not None else {}


def _ts():
    return datetime.now(timezone.utc).isoformat()


def _value_matches(value):
    """Return True if a string value contains a human-action pattern."""
    if not isinstance(value, str):
        return False
    for pat in _compiled_patterns:
        if pat.search(value):
            return True
    return False


def _classify(text):
    """Return the best-fit category for a task description string."""
    low = text.lower()
    scores = {}
    for cat, keywords in CATEGORY_RULES:
        hits = sum(1 for kw in keywords if kw in low)
        if hits > 0:
            scores[cat] = hits
    if not scores:
        return "INFRASTRUCTURE"  # default bucket
    return max(scores, key=scores.get)


def _estimate_time(text):
    """Extract or estimate time from text."""
    low = text.lower()
    # Try to find explicit time mentions
    m = re.search(r"(\d+)\s*(minute|min|m)\b", low)
    if m:
        mins = int(m.group(1))
        return "%d min" % mins, mins
    m = re.search(r"(\d+)\s*(hour|hr|h)\b", low)
    if m:
        hrs = int(m.group(1))
        return "%d hr" % hrs, hrs * 60
    m = re.search(r"(\d+)\s*(day|d)\b", low)
    if m:
        days = int(m.group(1))
        return "%d day" % days, days * 480
    m = re.search(r"(\d+)\s*(week|wk|w)\b", low)
    if m:
        wks = int(m.group(1))
        return "%d wk" % wks, wks * 2400
    m = re.search(r"(\d+)\s*(month|mo)\b", low)
    if m:
        mos = int(m.group(1))
        return "%d mo" % mos, mos * 10000
    # Heuristic based on content
    if any(w in low for w in ["click", "paste", "verify", "share"]):
        return "5 min", 5
    if any(w in low for w in ["create account", "sign up", "api key", "token"]):
        return "10 min", 10
    if any(w in low for w in ["upload", "publish", "configure"]):
        return "15 min", 15
    if any(w in low for w in ["article", "write", "draft"]):
        return "1 hr", 60
    return "15 min", 15


def _extract_url(obj):
    """Try to find a URL from a dict or string."""
    if isinstance(obj, str):
        m = re.search(r"https?://[^\s\"',<>]+", obj)
        return m.group(0) if m else ""
    if isinstance(obj, dict):
        for k in ("url", "buy_url", "link", "fallback_url", "kofi_shop"):
            v = obj.get(k, "")
            if v and isinstance(v, str) and v.startswith("http"):
                return v
    return ""


def _task_fingerprint(action_text, url=""):
    """Create a dedup fingerprint from task text."""
    # Normalise: lowercase, strip whitespace, remove articles
    norm = re.sub(r"\b(the|a|an|to|on|in|at|for|of|and|or)\b", "",
                  action_text.lower().strip())
    norm = re.sub(r"\s+", " ", norm).strip()
    # Include domain from URL if present
    domain = ""
    if url:
        m = re.search(r"https?://([^/]+)", url)
        if m:
            domain = m.group(1)
    raw = norm + "|" + domain
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _is_revenue_generating(text):
    """Does this task directly lead to revenue?"""
    low = text.lower()
    return any(w in low for w in [
        "list", "product", "sell", "price", "shop", "store", "buy",
        "payment", "revenue", "sale", "gumroad", "ko-fi", "kofi",
        "first dollar", "storefront",
    ])


def _is_zero_cost(text):
    """Is this a zero-cost action?"""
    low = text.lower()
    if any(w in low for w in ["buy", "purchase", "$12", "$50", "$6", "$5"]):
        return False
    if "free" in low or "$0" in low or "0.0" in low:
        return True
    # Actions like clicking, pasting, posting are free
    if any(w in low for w in ["click", "paste", "post", "share", "sign up",
                               "create account", "api key", "token"]):
        return True
    return True  # default assumption: most tasks are free


def _is_blocking(text):
    """Is this task a blocker for other systems?"""
    low = text.lower()
    return any(w in low for w in [
        "block", "critical", "unlock", "dead", "404", "broken", "zero",
    ])


# -----------------------------------------------------------------------
# Task Extraction: deep-walk all JSON data
# -----------------------------------------------------------------------

def _extract_tasks_from_value(value, source_file, key_path="", parent_obj=None):
    """Recursively walk a JSON value and extract tasks."""
    tasks = []

    if isinstance(value, dict):
        # Check if this dict itself is a task-like object
        action_text = ""
        for ak in ("action", "fix", "suggestion", "detail", "name",
                    "message", "description"):
            if ak in value and isinstance(value[ak], str):
                action_text = value[ak]
                break

        if action_text and _value_matches(action_text):
            url = _extract_url(value)
            time_str, time_mins = _estimate_time(
                action_text + " " + value.get("time_to_fix", "")
                + " " + value.get("setup_time", "")
                + " " + value.get("time", "")
                + " " + value.get("time_to_build", "")
                + " " + value.get("time_to_revenue", ""))
            category = _classify(action_text + " " + key_path)
            cost = value.get("cost", 0.0)
            if isinstance(cost, str):
                try:
                    cost = float(cost.replace("$", ""))
                except Exception:
                    cost = 0.0

            # What it unblocks
            unblocks = []
            for uk in ("impact", "engines_unlocked", "revenue_enabled",
                       "blocking", "wires_to"):
                uv = value.get(uk)
                if uv:
                    if isinstance(uv, list):
                        unblocks.extend([str(x) for x in uv])
                    elif isinstance(uv, str):
                        unblocks.append(uv)
                    elif isinstance(uv, bool) and uv:
                        unblocks.append("blocking dependency")

            tasks.append({
                "action": action_text,
                "url": url,
                "time_estimate": time_str,
                "time_minutes": time_mins,
                "category": category,
                "source_file": source_file,
                "source_key": key_path,
                "cost": float(cost) if cost else 0.0,
                "unblocks": unblocks[:5],
                "priority_hint": value.get("priority", value.get("roi_rank", 99)),
                "severity": value.get("severity", value.get("priority", "")),
                "revenue_generating": _is_revenue_generating(action_text),
                "zero_cost": _is_zero_cost(action_text + " " + str(cost)),
                "blocking": _is_blocking(action_text + " " + str(value)),
            })

        # Check for action keys that contain lists of tasks
        for k, v in value.items():
            new_path = "%s.%s" % (key_path, k) if key_path else k
            if k.lower() in ACTION_KEYS or k.lower().replace("_", "") in {
                    ak.replace("_", "") for ak in ACTION_KEYS}:
                sub = _extract_tasks_from_value(v, source_file, new_path, value)
                tasks.extend(sub)
            elif isinstance(v, (dict, list)):
                sub = _extract_tasks_from_value(v, source_file, new_path, value)
                tasks.extend(sub)

    elif isinstance(value, list):
        for i, item in enumerate(value):
            new_path = "%s[%d]" % (key_path, i)
            sub = _extract_tasks_from_value(item, source_file, new_path, parent_obj)
            tasks.extend(sub)

    elif isinstance(value, str) and _value_matches(value):
        url = ""
        m = re.search(r"https?://[^\s\"',<>]+", value)
        if m:
            url = m.group(0)
        time_str, time_mins = _estimate_time(value)
        tasks.append({
            "action": value,
            "url": url,
            "time_estimate": time_str,
            "time_minutes": time_mins,
            "category": _classify(value + " " + key_path),
            "source_file": source_file,
            "source_key": key_path,
            "cost": 0.0,
            "unblocks": [],
            "priority_hint": 99,
            "severity": "",
            "revenue_generating": _is_revenue_generating(value),
            "zero_cost": True,
            "blocking": _is_blocking(value),
        })

    return tasks


def scan_all_data():
    """Scan every data/*.json file and extract human tasks."""
    all_tasks = []
    files_scanned = 0

    for jf in sorted(DATA.glob("*.json")):
        files_scanned += 1
        try:
            raw = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        tasks = _extract_tasks_from_value(raw, jf.name)
        all_tasks.extend(tasks)

    return all_tasks, files_scanned


# -----------------------------------------------------------------------
# Deduplication
# -----------------------------------------------------------------------

def _safe_hint(val):
    """Coerce priority_hint to int for comparison."""
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        try:
            return int(val)
        except ValueError:
            pass
    return 99


def deduplicate(tasks):
    """Remove near-duplicate tasks, keeping the highest-priority version."""
    seen = {}
    for t in tasks:
        fp = _task_fingerprint(t["action"], t.get("url", ""))
        if fp not in seen:
            seen[fp] = t
        else:
            existing = seen[fp]
            # Keep the one with more information or higher priority
            if (_safe_hint(t.get("priority_hint", 99)) < _safe_hint(existing.get("priority_hint", 99))
                    or len(t.get("unblocks", [])) > len(existing.get("unblocks", []))):
                seen[fp] = t
    return list(seen.values())


# -----------------------------------------------------------------------
# Prioritisation
# -----------------------------------------------------------------------

def prioritise(tasks):
    """Sort tasks by composite priority score (lower = do first)."""
    def score(t):
        s = 0
        # Revenue-generating tasks first (subtract 1000)
        if t.get("revenue_generating"):
            s -= 1000
        # Zero-cost before paid (subtract 500)
        if t.get("zero_cost"):
            s -= 500
        # Blocking tasks before nice-to-haves (subtract 800)
        if t.get("blocking"):
            s -= 800
        # Shorter tasks before longer ones
        s += t.get("time_minutes", 15)
        # Use the engine's own priority hint
        hint = _safe_hint(t.get("priority_hint", 99))
        s += hint * 10
        # Critical severity bonus
        sev = str(t.get("severity", "")).lower()
        if sev == "critical":
            s -= 600
        elif sev == "high":
            s -= 300
        return s

    tasks.sort(key=score)
    # Assign final rank
    for i, t in enumerate(tasks):
        t["rank"] = i + 1
    return tasks


# -----------------------------------------------------------------------
# Session grouping
# -----------------------------------------------------------------------

def group_by_session(tasks):
    """Group tasks into time-based sessions."""
    quick = []    # <= 15 min total
    medium = []   # 15 min - 1 hr
    deep = []     # 1 hr+
    ongoing = []  # multi-day

    cumulative = 0
    for t in tasks:
        mins = t.get("time_minutes", 15)
        if mins <= 10:
            quick.append(t)
        elif mins <= 30:
            medium.append(t)
        elif mins <= 120:
            deep.append(t)
        else:
            ongoing.append(t)

    return {
        "quick_wins": {"label": "Quick Wins (5-10 min each)", "tasks": quick},
        "one_hour": {"label": "One-Hour Sprint", "tasks": medium},
        "half_day": {"label": "Half-Day Deep Work", "tasks": deep},
        "ongoing": {"label": "Ongoing / Multi-Day", "tasks": ongoing},
    }


# -----------------------------------------------------------------------
# Category summary
# -----------------------------------------------------------------------

def group_by_category(tasks):
    """Group tasks by category."""
    cats = {}
    for t in tasks:
        c = t.get("category", "OTHER")
        if c not in cats:
            cats[c] = []
        cats[c].append(t)
    return cats


# -----------------------------------------------------------------------
# HTML dashboard
# -----------------------------------------------------------------------

def build_html(board):
    """Generate docs/tasks.html -- interactive dark-themed dashboard."""
    tasks = board.get("tasks", [])
    sessions = board.get("sessions", {})
    categories = board.get("by_category", {})
    stats = board.get("stats", {})

    # Category pills
    cat_pills = ""
    cat_order = ["REVENUE", "INFRASTRUCTURE", "OUTREACH", "CONTENT", "LEGAL", "GRANTS"]
    for cat in cat_order:
        ct = categories.get(cat, [])
        if ct:
            cat_pills += '<span class="pill cat-%s" onclick="filterCat(\'%s\')">%s (%d)</span>\n' % (
                cat.lower(), cat, cat, len(ct))
    cat_pills += '<span class="pill cat-all" onclick="filterCat(\'ALL\')">ALL (%d)</span>\n' % len(tasks)

    # Stats bar
    stats_html = """<div class="stats-bar">
  <div class="stat"><span class="stat-n">%d</span><span class="stat-l">Tasks</span></div>
  <div class="stat"><span class="stat-n">%d</span><span class="stat-l">Files Scanned</span></div>
  <div class="stat"><span class="stat-n">%d</span><span class="stat-l">Revenue Tasks</span></div>
  <div class="stat"><span class="stat-n">%d</span><span class="stat-l">Free Tasks</span></div>
  <div class="stat"><span class="stat-n">%d</span><span class="stat-l">Blockers</span></div>
</div>""" % (
        stats.get("total_tasks", 0),
        stats.get("files_scanned", 0),
        stats.get("revenue_tasks", 0),
        stats.get("free_tasks", 0),
        stats.get("blocking_tasks", 0),
    )

    # Task rows
    task_rows = ""
    for t in tasks:
        cat = t.get("category", "OTHER")
        checked = ""
        url_link = ""
        if t.get("url"):
            url_link = '<a href="%s" target="_blank" class="task-url">%s</a>' % (
                t["url"], t["url"][:60] + ("..." if len(t["url"]) > 60 else ""))
        unblocks_html = ""
        if t.get("unblocks"):
            unblocks_html = '<div class="unblocks">Unblocks: %s</div>' % (
                ", ".join(str(u)[:40] for u in t["unblocks"][:3]))
        cost_badge = ""
        if t.get("cost", 0) > 0:
            cost_badge = '<span class="badge cost">$%.0f</span>' % t["cost"]
        else:
            cost_badge = '<span class="badge free">FREE</span>'
        sev_class = ""
        sev = str(t.get("severity", "")).lower()
        if sev == "critical":
            sev_class = "sev-critical"
        elif sev == "high":
            sev_class = "sev-high"
        rev_badge = ""
        if t.get("revenue_generating"):
            rev_badge = '<span class="badge rev">$$</span>'
        block_badge = ""
        if t.get("blocking"):
            block_badge = '<span class="badge blocker">BLOCKER</span>'

        source_short = t.get("source_file", "").replace(".json", "")

        task_rows += """<div class="task-row cat-item cat-%s %s" data-cat="%s">
  <label class="check-wrap">
    <input type="checkbox" onchange="toggleDone(this)"><span class="checkmark"></span>
  </label>
  <span class="rank">#%d</span>
  <div class="task-body">
    <div class="task-action">%s</div>
    %s%s
    <div class="task-meta">
      <span class="badge cat cat-%s">%s</span>
      %s%s%s
      <span class="badge time">%s</span>
      <span class="badge src">%s</span>
    </div>
  </div>
</div>\n""" % (
            cat.lower(), sev_class, cat,
            t.get("rank", 0),
            t.get("action", "").replace("<", "&lt;").replace(">", "&gt;"),
            url_link, unblocks_html,
            cat.lower(), cat,
            cost_badge, rev_badge, block_badge,
            t.get("time_estimate", "?"),
            source_short,
        )

    # Session sections
    session_html = ""
    for skey in ("quick_wins", "one_hour", "half_day", "ongoing"):
        sess = sessions.get(skey, {})
        stasks = sess.get("tasks", [])
        if not stasks:
            continue
        total_mins = sum(t.get("time_minutes", 0) for t in stasks)
        session_html += '<div class="session-group"><h3>%s <span class="session-count">%d tasks, ~%d min</span></h3></div>\n' % (
            sess.get("label", skey), len(stasks), total_mins)

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Human Task Board -- SolarPunk</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#0a0a0a;color:#d4d4d4;padding:20px;max-width:900px;margin:0 auto}
h1{color:#4ade80;margin-bottom:4px;font-size:1.8em}
h2{color:#86efac;margin:28px 0 12px;font-size:1.2em;border-bottom:1px solid #222;padding-bottom:6px}
h3{color:#a5f3c4;font-size:1em;margin:18px 0 8px}
.subtitle{color:#666;margin-bottom:16px;font-size:0.88em}
.stats-bar{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}
.stat{background:#111;border:1px solid #222;border-radius:8px;padding:10px 16px;text-align:center;flex:1;min-width:100px}
.stat-n{display:block;font-size:1.6em;font-weight:bold;color:#4ade80}
.stat-l{display:block;font-size:0.72em;color:#666;margin-top:2px}
.pills{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.pill{padding:5px 14px;border-radius:16px;font-size:0.78em;cursor:pointer;border:1px solid #333;transition:all 0.15s}
.pill:hover{border-color:#4ade80;color:#4ade80}
.pill.active{background:#14532d;border-color:#22c55e;color:#4ade80}
.cat-revenue{border-color:#22c55e;color:#4ade80}
.cat-infrastructure{border-color:#3b82f6;color:#60a5fa}
.cat-outreach{border-color:#a855f7;color:#c084fc}
.cat-content{border-color:#f59e0b;color:#fbbf24}
.cat-legal{border-color:#ef4444;color:#f87171}
.cat-grants{border-color:#14b8a6;color:#2dd4bf}
.cat-all{border-color:#666;color:#999}
.task-row{display:flex;gap:12px;align-items:flex-start;padding:12px 14px;margin-bottom:8px;background:#111;border:1px solid #1e1e1e;border-radius:8px;transition:all 0.15s}
.task-row:hover{border-color:#333;background:#151515}
.task-row.done{opacity:0.35;text-decoration:line-through}
.task-row.hidden{display:none}
.sev-critical{border-left:3px solid #ef4444}
.sev-high{border-left:3px solid #f97316}
.check-wrap{position:relative;cursor:pointer;flex-shrink:0;margin-top:2px}
.check-wrap input{opacity:0;position:absolute}
.checkmark{display:inline-block;width:20px;height:20px;border:2px solid #444;border-radius:4px;transition:all 0.15s}
.check-wrap input:checked+.checkmark{background:#4ade80;border-color:#4ade80}
.rank{color:#4ade80;font-weight:bold;font-size:0.82em;flex-shrink:0;width:32px;margin-top:2px}
.task-body{flex:1;min-width:0}
.task-action{font-size:0.92em;margin-bottom:4px;line-height:1.4}
.task-url{display:block;color:#60a5fa;font-size:0.78em;word-break:break-all;margin:3px 0}
.task-url:hover{color:#93c5fd}
.unblocks{color:#666;font-size:0.73em;margin:3px 0}
.task-meta{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}
.badge{padding:2px 8px;border-radius:10px;font-size:0.68em;font-weight:600;border:1px solid #333}
.badge.free{color:#4ade80;border-color:#14532d}
.badge.cost{color:#fbbf24;border-color:#713f12}
.badge.rev{color:#4ade80;border-color:#166534;background:#052e16}
.badge.blocker{color:#ef4444;border-color:#7f1d1d;background:#1c0a0a}
.badge.time{color:#999;border-color:#333}
.badge.src{color:#666;border-color:#222}
.badge.cat{font-weight:bold}
.session-group{margin:12px 0}
.session-group h3{font-size:0.95em}
.session-count{color:#666;font-weight:normal;font-size:0.85em}
.filter-bar{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap}
.filter-bar input{background:#111;border:1px solid #333;border-radius:6px;padding:8px 12px;color:#d4d4d4;font-size:0.85em;flex:1;min-width:200px}
.filter-bar input:focus{outline:none;border-color:#4ade80}
.pcrf{margin-top:32px;padding:12px;background:#1a1a0a;border:1px solid #444;border-radius:6px;color:#fbbf24;font-size:0.82em;text-align:center}
.ts{color:#444;font-size:0.7em;margin-top:16px;text-align:center}
.progress-bar{background:#1a1a1a;border-radius:8px;height:8px;margin:12px 0;overflow:hidden}
.progress-fill{height:100%%;background:linear-gradient(90deg,#4ade80,#22c55e);border-radius:8px;transition:width 0.3s}
</style>
</head>
<body>
<h1>Human Task Board</h1>
<p class="subtitle">Every action that needs a human, extracted from %d data files. Ranked by revenue impact.</p>

%s

<div class="progress-bar"><div class="progress-fill" id="progressBar" style="width:0%%"></div></div>
<p id="progressText" style="color:#666;font-size:0.75em;text-align:center;margin-bottom:16px">0 / %d tasks complete</p>

<div class="pills" id="catPills">
%s
</div>

<div class="filter-bar">
  <input type="text" id="searchBox" placeholder="Search tasks..." oninput="filterSearch(this.value)">
</div>

<h2>Session Planner</h2>
%s

<h2>All Tasks (Prioritised)</h2>
<div id="taskList">
%s
</div>

<div class="pcrf">15%% of all SolarPunk revenue goes to Palestinian Children's Relief Fund (PCRF, EIN: 93-1057665)</div>
<div class="ts">Generated %s by HUMAN_TASK_BOARD</div>

<script>
let activeCat = 'ALL';
function filterCat(cat) {
  activeCat = cat;
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('.cat-item').forEach(el => {
    if (cat === 'ALL' || el.dataset.cat === cat) {
      el.classList.remove('hidden');
    } else {
      el.classList.add('hidden');
    }
  });
  filterSearch(document.getElementById('searchBox').value);
}
function filterSearch(q) {
  const low = q.toLowerCase();
  document.querySelectorAll('.cat-item').forEach(el => {
    if (activeCat !== 'ALL' && el.dataset.cat !== activeCat) {
      el.classList.add('hidden');
      return;
    }
    if (!low) { el.classList.remove('hidden'); return; }
    const text = el.textContent.toLowerCase();
    el.classList.toggle('hidden', !text.includes(low));
  });
}
function toggleDone(cb) {
  const row = cb.closest('.task-row');
  row.classList.toggle('done', cb.checked);
  updateProgress();
  // Save to localStorage
  const key = 'htb_' + row.querySelector('.rank').textContent;
  localStorage.setItem(key, cb.checked ? '1' : '0');
}
function updateProgress() {
  const total = document.querySelectorAll('.task-row').length;
  const done = document.querySelectorAll('.task-row.done').length;
  const pct = total > 0 ? (done / total * 100) : 0;
  document.getElementById('progressBar').style.width = pct + '%%';
  document.getElementById('progressText').textContent = done + ' / ' + total + ' tasks complete';
}
// Restore state from localStorage
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.task-row').forEach(row => {
    const key = 'htb_' + row.querySelector('.rank').textContent;
    if (localStorage.getItem(key) === '1') {
      const cb = row.querySelector('input[type=checkbox]');
      cb.checked = true;
      row.classList.add('done');
    }
  });
  updateProgress();
});
</script>
</body>
</html>""" % (
        stats.get("files_scanned", 0),
        stats_html,
        len(tasks),
        cat_pills,
        session_html,
        task_rows,
        board.get("generated_at", ""),
    )
    return html


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def run():
    print("=" * 60)
    print("HUMAN_TASK_BOARD -- scanning all data files for human tasks")
    print("=" * 60)

    t0 = time.time()

    # 1. Scan all data files
    raw_tasks, files_scanned = scan_all_data()
    print("[scan] %d raw tasks extracted from %d files" % (len(raw_tasks), files_scanned))

    # 2. Deduplicate
    tasks = deduplicate(raw_tasks)
    print("[dedup] %d unique tasks (removed %d duplicates)" % (
        len(tasks), len(raw_tasks) - len(tasks)))

    # 3. Prioritise
    tasks = prioritise(tasks)

    # 4. Group by category
    by_category = group_by_category(tasks)
    for cat, ct in sorted(by_category.items(), key=lambda x: -len(x[1])):
        print("[category] %-16s %d tasks" % (cat, len(ct)))

    # 5. Group by session
    sessions = group_by_session(tasks)
    for skey, sess in sessions.items():
        stasks = sess.get("tasks", [])
        if stasks:
            total_mins = sum(t.get("time_minutes", 0) for t in stasks)
            print("[session] %-20s %d tasks, ~%d min" % (
                sess["label"][:20], len(stasks), total_mins))

    # 6. Stats
    stats = {
        "total_tasks": len(tasks),
        "files_scanned": files_scanned,
        "revenue_tasks": sum(1 for t in tasks if t.get("revenue_generating")),
        "free_tasks": sum(1 for t in tasks if t.get("zero_cost")),
        "blocking_tasks": sum(1 for t in tasks if t.get("blocking")),
        "categories": {cat: len(ct) for cat, ct in by_category.items()},
        "scan_time_ms": int((time.time() - t0) * 1000),
    }

    # 7. Build board
    board = {
        "generated_at": _ts(),
        "engine": "HUMAN_TASK_BOARD",
        "stats": stats,
        "tasks": tasks,
        "by_category": {cat: [t.get("rank") for t in ct] for cat, ct in by_category.items()},
        "sessions": {
            skey: {
                "label": sess["label"],
                "task_ranks": [t.get("rank") for t in sess["tasks"]],
                "count": len(sess["tasks"]),
                "total_minutes": sum(t.get("time_minutes", 0) for t in sess["tasks"]),
            }
            for skey, sess in sessions.items()
        },
    }

    # 8. Write data/human_task_board.json
    board_path = DATA / "human_task_board.json"
    board_path.write_text(json.dumps(board, indent=2), encoding="utf-8")
    print("\n[write] %s" % board_path)

    # 9. Write docs/tasks.html
    html = build_html(board)
    html_path = DOCS / "tasks.html"
    html_path.write_text(html, encoding="utf-8")
    print("[write] %s" % html_path)

    # 10. Print top 10 tasks
    print("\n" + "=" * 60)
    print("TOP 10 HUMAN TASKS (do these first)")
    print("=" * 60)
    for t in tasks[:10]:
        cost_tag = "FREE" if t.get("zero_cost") else "$%.0f" % t.get("cost", 0)
        flags = []
        if t.get("blocking"):
            flags.append("BLOCKER")
        if t.get("revenue_generating"):
            flags.append("$$")
        flag_str = " [%s]" % ", ".join(flags) if flags else ""
        action_safe = t.get("action", "")[:80].encode("ascii", "replace").decode()
        url_safe = t.get("url", "")[:80].encode("ascii", "replace").decode()
        print("  %2d. [%s] [%s] %s%s" % (
            t["rank"],
            t.get("category", "?")[:6],
            t.get("time_estimate", "?"),
            action_safe,
            flag_str,
        ))
        if t.get("url"):
            print("      -> %s" % url_safe)

    print("\n[done] %d tasks in %dms. Board written." % (
        len(tasks), stats["scan_time_ms"]))
    return board


if __name__ == "__main__":
    run()
