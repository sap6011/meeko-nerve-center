#!/usr/bin/env python3
"""
CHANNEL_ROUTER.py -- Multi-Channel Fallback Router
====================================================
When one channel goes down, routes through alternatives.

Orchestrates ALL 15 output channels available to SolarPunk.
When the primary channel (Chrome browser) is unavailable, this engine
finds the best alternative and writes routing instructions for the queue.

Outputs:
  data/channel_router_state.json  -- full state, all channels, routing decisions
  data/channel_router_queue.json  -- pending tasks with assigned channels
  docs/channels.html              -- dark-themed live dashboard
"""
import json
import time
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
DOCS = Path("docs")
DOCS.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# CHANNEL REGISTRY
# ---------------------------------------------------------------------------

CHANNELS = {
    "github_cli": {
        "tool": "gh CLI",
        "capabilities": ["discussions", "issues", "releases", "wiki", "pr", "pages"],
        "auth": "gh auth token",
        "status": "always_available",
    },
    "gmail_mcp": {
        "tool": "Gmail MCP",
        "capabilities": ["draft_email", "list_drafts", "search_messages"],
        "auth": "oauth",
        "status": "always_available",
    },
    "apify_browser": {
        "tool": "Apify RAG Web Browser",
        "capabilities": ["scrape_page", "search_web", "fetch_url"],
        "auth": "api_key",
        "status": "always_available",
    },
    "windows_mcp": {
        "tool": "Windows MCP",
        "capabilities": ["screenshot", "click", "type", "powershell", "open_app"],
        "auth": "local",
        "status": "always_available",
    },
    "chrome_mcp": {
        "tool": "Claude in Chrome",
        "capabilities": ["navigate", "form_fill", "screenshot", "read_page", "click"],
        "auth": "extension",
        "status": "intermittent",  # goes down when browser closes
    },
    "notion_mcp": {
        "tool": "Notion MCP",
        "capabilities": ["create_page", "update_page", "search", "create_database"],
        "auth": "oauth",
        "status": "always_available",
    },
    "github_mcp": {
        "tool": "GitHub MCP",
        "capabilities": ["create_file", "create_issue", "create_pr", "push_files"],
        "auth": "token",
        "status": "always_available",
    },
    "paypal_mcp": {
        "tool": "PayPal MCP",
        "capabilities": ["create_invoice", "send_invoice", "list_transactions"],
        "auth": "oauth",
        "status": "always_available",
    },
    "gcal_mcp": {
        "tool": "Google Calendar MCP",
        "capabilities": ["create_event", "list_events", "find_free_time"],
        "auth": "oauth",
        "status": "always_available",
    },
    "webfetch": {
        "tool": "WebFetch",
        "capabilities": ["fetch_url", "read_page"],
        "auth": "none",
        "status": "always_available",
    },
    "brave_browser": {
        "tool": "Brave via Windows MCP",
        "capabilities": ["navigate", "form_fill", "screenshot", "click", "type"],
        "auth": "local",
        "status": "always_available",
        "fallback_for": "chrome_mcp",
    },
    "desktop_commander": {
        "tool": "Desktop Commander MCP",
        "capabilities": ["file_ops", "process_mgmt", "search", "edit"],
        "auth": "local",
        "status": "always_available",
    },
    "huggingface_mcp": {
        "tool": "HuggingFace MCP",
        "capabilities": ["search_models", "search_papers", "repo_details"],
        "auth": "token",
        "status": "always_available",
    },
    "b12_generator": {
        "tool": "B12 Website Generator",
        "capabilities": ["generate_website"],
        "auth": "api",
        "status": "always_available",
    },
    "windows_brave": {
        "tool": "Windows MCP + Brave shortcut",
        "capabilities": ["navigate", "screenshot", "click", "open_app"],
        "auth": "local",
        "status": "always_available",
        "fallback_for": "chrome_mcp",
    },
}

# ---------------------------------------------------------------------------
# TASK ROUTING TABLE
# Ordered channel preference lists — first available wins.
# ---------------------------------------------------------------------------

TASK_ROUTING = {
    "post_content":       ["chrome_mcp", "brave_browser", "windows_mcp", "github_cli", "apify_browser"],
    "list_product":       ["chrome_mcp", "brave_browser", "windows_mcp", "apify_browser"],
    "send_email":         ["gmail_mcp"],
    "verify_email":       ["gmail_mcp"],  # EMAIL_INTELLIGENCE: bounce detection via search
    "outreach_campaign":  ["gmail_mcp"],  # EMAIL_INTELLIGENCE: personalized outreach
    "create_discussion":  ["github_cli", "github_mcp"],
    "create_release":     ["github_cli", "github_mcp"],
    "create_wiki":        ["github_cli"],  # via wiki git repo
    "update_notion":      ["notion_mcp"],
    "scrape_page":        ["apify_browser", "webfetch", "chrome_mcp", "brave_browser"],
    "create_invoice":     ["paypal_mcp"],
    "schedule_event":     ["gcal_mcp"],
    "deploy_page":        ["github_cli", "github_mcp"],  # push to docs/
    "take_screenshot":    ["windows_mcp", "chrome_mcp"],
    "open_url":           ["brave_browser", "windows_mcp", "chrome_mcp"],
    "fill_form":          ["chrome_mcp", "brave_browser", "windows_mcp"],
    "generate_website":   ["b12_generator"],
    "search_web":         ["apify_browser", "webfetch"],
    "file_operation":     ["desktop_commander"],
    "research_models":    ["huggingface_mcp"],
    "push_code":          ["github_mcp", "github_cli"],
    "run_command":        ["windows_mcp", "desktop_commander"],
}


# ---------------------------------------------------------------------------
# STATUS DETECTION
# ---------------------------------------------------------------------------

def load_json_safe(path: Path, default=None):
    """Load a JSON file, returning default on any error."""
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def detect_channel_status() -> dict:
    """
    Determine the live status of each channel.

    Rules:
    - If data/chrome_mcp_status.json exists and active=false → chrome_mcp is DOWN
    - If data/channel_router_state.json has a recent override → honour it
    - Otherwise fall back to the baseline CHANNELS status field
    """
    overrides = {}

    # Check Chrome MCP status file
    chrome_status_file = load_json_safe(DATA / "chrome_mcp_status.json")
    if chrome_status_file:
        active = chrome_status_file.get("active", chrome_status_file.get("status", "unknown"))
        if active in (False, "down", "offline", "inactive", "unavailable"):
            overrides["chrome_mcp"] = "down"
        elif active in (True, "up", "online", "active", "available"):
            overrides["chrome_mcp"] = "available"

    # Check previous router state for manual overrides
    prev_state = load_json_safe(DATA / "channel_router_state.json")
    manual_overrides = prev_state.get("manual_overrides", {})
    for channel, status in manual_overrides.items():
        overrides[channel] = status

    # Build final status map
    statuses = {}
    for name, meta in CHANNELS.items():
        baseline = meta.get("status", "always_available")
        if name in overrides:
            statuses[name] = overrides[name]
        elif baseline == "intermittent":
            statuses[name] = "intermittent"
        else:
            statuses[name] = "available"

    return statuses


def is_channel_usable(channel_name: str, statuses: dict) -> bool:
    """Return True if the channel can currently accept tasks."""
    s = statuses.get(channel_name, "unknown")
    return s in ("available", "always_available", "intermittent")


# ---------------------------------------------------------------------------
# ROUTING LOGIC
# ---------------------------------------------------------------------------

def route_task(task: dict, statuses: dict) -> dict:
    """
    Given a task dict with a 'type' key, find the best available channel.

    Returns routing decision dict:
      {
        "task_id": ...,
        "task_type": ...,
        "assigned_channel": ...,  # or None
        "assigned_tool": ...,
        "fallback_chain": [...],
        "decision": "routed" | "no_channel_available",
        "timestamp": ...,
      }
    """
    task_type = task.get("type", "unknown")
    task_id = task.get("id", f"task_{int(time.time() * 1000)}")
    chain = TASK_ROUTING.get(task_type, [])

    assigned_channel = None
    assigned_tool = None
    tried = []

    for candidate in chain:
        if candidate not in CHANNELS:
            tried.append({"channel": candidate, "result": "not_registered"})
            continue
        if is_channel_usable(candidate, statuses):
            assigned_channel = candidate
            assigned_tool = CHANNELS[candidate]["tool"]
            break
        else:
            tried.append({"channel": candidate, "result": statuses.get(candidate, "unknown")})

    return {
        "task_id": task_id,
        "task_type": task_type,
        "task_payload": task.get("payload", {}),
        "assigned_channel": assigned_channel,
        "assigned_tool": assigned_tool,
        "fallback_chain": chain,
        "tried_channels": tried,
        "decision": "routed" if assigned_channel else "no_channel_available",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def process_queue(statuses: dict) -> tuple:
    """
    Read data/channel_router_queue.json, route each pending task,
    and return (updated_queue, routing_decisions).
    """
    queue_path = DATA / "channel_router_queue.json"
    queue_data = load_json_safe(queue_path, {"pending": [], "completed": [], "failed": []})

    # Ensure required keys
    for key in ("pending", "completed", "failed"):
        if key not in queue_data:
            queue_data[key] = []

    routing_decisions = []
    still_pending = []

    for task in queue_data["pending"]:
        decision = route_task(task, statuses)
        routing_decisions.append(decision)

        if decision["decision"] == "routed":
            task["_routing"] = decision
            task["status"] = "routed"
            queue_data["completed"].append(task)
        else:
            task["_routing"] = decision
            task["status"] = "no_channel"
            queue_data["failed"].append(task)

    queue_data["pending"] = still_pending
    queue_data["last_processed"] = datetime.now(timezone.utc).isoformat()

    # Write updated queue back
    queue_path.write_text(json.dumps(queue_data, indent=2), encoding="utf-8")
    return queue_data, routing_decisions


# ---------------------------------------------------------------------------
# REPORTING
# ---------------------------------------------------------------------------

def build_state_report(statuses: dict, routing_decisions: list, queue_data: dict) -> dict:
    """Assemble the full router state document."""
    total = len(CHANNELS)
    available_count = sum(1 for s in statuses.values() if s in ("available", "always_available"))
    intermittent_count = sum(1 for s in statuses.values() if s == "intermittent")
    down_count = sum(1 for s in statuses.values() if s == "down")

    # Find any tasks that couldn't be routed
    blocked_types = list({
        d["task_type"] for d in routing_decisions if d["decision"] == "no_channel_available"
    })

    # Load previous manual overrides so they survive the write
    prev = load_json_safe(DATA / "channel_router_state.json")
    manual_overrides = prev.get("manual_overrides", {})

    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "engine": "CHANNEL_ROUTER",
        "version": "1.0.0",
        "summary": {
            "total_channels": total,
            "available": available_count,
            "intermittent": intermittent_count,
            "down": down_count,
            "tasks_processed": len(routing_decisions),
            "tasks_routed": sum(1 for d in routing_decisions if d["decision"] == "routed"),
            "tasks_blocked": len(blocked_types),
            "blocked_task_types": blocked_types,
        },
        "channel_statuses": {
            name: {
                "tool": CHANNELS[name]["tool"],
                "status": statuses.get(name, "unknown"),
                "capabilities": CHANNELS[name]["capabilities"],
                "auth": CHANNELS[name]["auth"],
                "fallback_for": CHANNELS[name].get("fallback_for"),
            }
            for name in CHANNELS
        },
        "task_routing_table": TASK_ROUTING,
        "recent_routing_decisions": routing_decisions[-20:],  # last 20
        "queue_summary": {
            "pending": len(queue_data.get("pending", [])),
            "completed": len(queue_data.get("completed", [])),
            "failed": len(queue_data.get("failed", [])),
        },
        "manual_overrides": manual_overrides,
        "next_action": (
            "No blocked tasks — all channels operational." if not blocked_types
            else f"Blocked task types: {blocked_types}. Check auth or add new channel."
        ),
    }


# ---------------------------------------------------------------------------
# HTML DASHBOARD
# ---------------------------------------------------------------------------

STATUS_COLORS = {
    "available":      ("#00e676", "AVAILABLE"),
    "always_available": ("#00e676", "AVAILABLE"),
    "intermittent":   ("#ffca28", "INTERMITTENT"),
    "down":           ("#ef5350", "DOWN"),
    "unknown":        ("#90a4ae", "UNKNOWN"),
}


def _status_badge(status: str) -> str:
    color, label = STATUS_COLORS.get(status, ("#90a4ae", status.upper()))
    return (
        f'<span style="background:{color};color:#000;'
        f'padding:2px 10px;border-radius:12px;font-size:0.78em;'
        f'font-weight:700;letter-spacing:0.04em;">{label}</span>'
    )


def _capability_pills(caps: list) -> str:
    pills = []
    for cap in caps:
        pills.append(
            f'<span style="background:#263238;color:#80cbc4;'
            f'padding:1px 8px;border-radius:8px;font-size:0.72em;'
            f'margin:1px;display:inline-block;">{cap}</span>'
        )
    return " ".join(pills)


def generate_html_dashboard(state: dict) -> str:
    """Render the full dark-themed channels dashboard as HTML."""
    now = state["generated"]
    summary = state["summary"]
    channel_statuses = state["channel_statuses"]
    routing_table = state["task_routing_table"]
    decisions = state["recent_routing_decisions"]

    # Channel rows
    channel_rows = []
    for name, info in channel_statuses.items():
        status = info["status"]
        color, _ = STATUS_COLORS.get(status, ("#90a4ae", "UNKNOWN"))
        fallback_note = f'<br><span style="color:#78909c;font-size:0.72em;">fallback for: {info["fallback_for"]}</span>' if info.get("fallback_for") else ""
        channel_rows.append(f"""
        <tr style="border-bottom:1px solid #1e2a30;">
          <td style="padding:10px 14px;font-weight:600;color:#e0f7fa;">{name}</td>
          <td style="padding:10px 14px;color:#b0bec5;">{info['tool']}{fallback_note}</td>
          <td style="padding:10px 14px;text-align:center;">{_status_badge(status)}</td>
          <td style="padding:10px 14px;">{_capability_pills(info['capabilities'])}</td>
          <td style="padding:10px 14px;color:#78909c;font-size:0.82em;">{info['auth']}</td>
        </tr>""")

    # Routing chain rows
    routing_rows = []
    for task_type, chain in sorted(routing_table.items()):
        chain_html = " &rarr; ".join(
            f'<span style="color:#80cbc4;">{c}</span>' for c in chain
        )
        routing_rows.append(f"""
        <tr style="border-bottom:1px solid #1e2a30;">
          <td style="padding:8px 14px;color:#fff176;font-family:monospace;">{task_type}</td>
          <td style="padding:8px 14px;font-size:0.85em;">{chain_html}</td>
        </tr>""")

    # Recent decision rows
    decision_rows = []
    if decisions:
        for d in reversed(decisions[-10:]):
            channel = d.get("assigned_channel") or "—"
            decision_class = "#00e676" if d["decision"] == "routed" else "#ef5350"
            tried_str = ", ".join(
                f'{t["channel"]}({t["result"]})' for t in d.get("tried_channels", [])
            ) or "—"
            decision_rows.append(f"""
            <tr style="border-bottom:1px solid #1e2a30;">
              <td style="padding:8px 12px;color:#90a4ae;font-size:0.8em;">{d['timestamp'][:19]}</td>
              <td style="padding:8px 12px;color:#fff176;font-family:monospace;">{d['task_type']}</td>
              <td style="padding:8px 12px;color:#80cbc4;">{channel}</td>
              <td style="padding:8px 12px;font-size:0.78em;color:#78909c;">{tried_str}</td>
              <td style="padding:8px 12px;text-align:center;">
                <span style="color:{decision_class};font-weight:700;">{d['decision'].upper()}</span>
              </td>
            </tr>""")
    else:
        decision_rows.append(
            '<tr><td colspan="5" style="padding:14px;color:#546e7a;text-align:center;">No routing decisions yet</td></tr>'
        )

    avail_pct = int(summary["available"] / summary["total_channels"] * 100) if summary["total_channels"] else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SolarPunk — Channel Router Dashboard</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #0d1b22;
      color: #cfd8dc;
      min-height: 100vh;
    }}
    h1, h2, h3 {{ margin: 0 0 10px 0; font-weight: 700; }}
    .header {{
      background: linear-gradient(135deg, #003d4d 0%, #00695c 100%);
      padding: 28px 32px;
      border-bottom: 2px solid #00bcd4;
    }}
    .header h1 {{ color: #e0f7fa; font-size: 1.6em; letter-spacing: 0.02em; }}
    .header .sub {{ color: #80deea; font-size: 0.9em; margin-top: 4px; }}
    .container {{ max-width: 1300px; margin: 0 auto; padding: 28px 24px; }}
    .cards {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 28px; }}
    .card {{
      background: #122028;
      border: 1px solid #1e3540;
      border-radius: 10px;
      padding: 18px 22px;
      flex: 1;
      min-width: 160px;
      text-align: center;
    }}
    .card .value {{ font-size: 2.4em; font-weight: 800; color: #e0f7fa; line-height: 1.1; }}
    .card .label {{ font-size: 0.82em; color: #78909c; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.06em; }}
    .card.green .value {{ color: #00e676; }}
    .card.yellow .value {{ color: #ffca28; }}
    .card.red .value {{ color: #ef5350; }}
    .section {{
      background: #122028;
      border: 1px solid #1e3540;
      border-radius: 10px;
      margin-bottom: 24px;
      overflow: hidden;
    }}
    .section-header {{
      background: #0d2030;
      padding: 12px 18px;
      font-size: 0.88em;
      font-weight: 700;
      color: #80cbc4;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      border-bottom: 1px solid #1e3540;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{
      background: #0d2030;
      padding: 9px 14px;
      text-align: left;
      font-size: 0.78em;
      color: #78909c;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      border-bottom: 1px solid #1e3540;
    }}
    tr:hover {{ background: #152a36; }}
    .progress-bar {{
      height: 8px;
      background: #1e3540;
      border-radius: 4px;
      margin-top: 8px;
      overflow: hidden;
    }}
    .progress-fill {{
      height: 100%;
      background: linear-gradient(90deg, #00bcd4, #00e676);
      border-radius: 4px;
      width: {avail_pct}%;
      transition: width 0.4s ease;
    }}
    .footer {{
      text-align: center;
      padding: 18px;
      color: #37474f;
      font-size: 0.8em;
      border-top: 1px solid #1e3540;
      margin-top: 8px;
    }}
  </style>
</head>
<body>

<div class="header">
  <h1>&#9881; SolarPunk — Channel Router Dashboard</h1>
  <div class="sub">CHANNEL_ROUTER.py &nbsp;|&nbsp; Multi-Channel Fallback Intelligence &nbsp;|&nbsp; {now[:19]} UTC</div>
</div>

<div class="container">

  <!-- Summary cards -->
  <div class="cards">
    <div class="card">
      <div class="value">{summary['total_channels']}</div>
      <div class="label">Total Channels</div>
    </div>
    <div class="card green">
      <div class="value">{summary['available']}</div>
      <div class="label">Available</div>
    </div>
    <div class="card yellow">
      <div class="value">{summary['intermittent']}</div>
      <div class="label">Intermittent</div>
    </div>
    <div class="card red">
      <div class="value">{summary['down']}</div>
      <div class="label">Down</div>
    </div>
    <div class="card">
      <div class="value">{summary['tasks_routed']}</div>
      <div class="label">Tasks Routed</div>
    </div>
    <div class="card red">
      <div class="value">{summary['tasks_blocked']}</div>
      <div class="label">Tasks Blocked</div>
    </div>
  </div>

  <!-- Availability bar -->
  <div class="section" style="padding:16px 20px;margin-bottom:24px;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <span style="color:#80cbc4;font-weight:700;font-size:0.88em;">CHANNEL AVAILABILITY</span>
      <span style="color:#e0f7fa;font-weight:800;font-size:1.1em;">{avail_pct}%</span>
    </div>
    <div class="progress-bar"><div class="progress-fill"></div></div>
  </div>

  <!-- Channel status table -->
  <div class="section">
    <div class="section-header">All Channels — Live Status</div>
    <table>
      <thead>
        <tr>
          <th>Channel ID</th>
          <th>Tool</th>
          <th style="text-align:center;">Status</th>
          <th>Capabilities</th>
          <th>Auth</th>
        </tr>
      </thead>
      <tbody>
        {''.join(channel_rows)}
      </tbody>
    </table>
  </div>

  <!-- Task routing table -->
  <div class="section">
    <div class="section-header">Task Routing — Fallback Chains</div>
    <table>
      <thead>
        <tr>
          <th>Task Type</th>
          <th>Preferred Channel Order (first available wins)</th>
        </tr>
      </thead>
      <tbody>
        {''.join(routing_rows)}
      </tbody>
    </table>
  </div>

  <!-- Recent routing decisions -->
  <div class="section">
    <div class="section-header">Recent Routing Decisions</div>
    <table>
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>Task Type</th>
          <th>Assigned Channel</th>
          <th>Channels Tried</th>
          <th style="text-align:center;">Decision</th>
        </tr>
      </thead>
      <tbody>
        {''.join(decision_rows)}
      </tbody>
    </table>
  </div>

</div>

<div class="footer">
  SolarPunk Node-01 &nbsp;|&nbsp; CHANNEL_ROUTER v1.0.0 &nbsp;|&nbsp;
  Generated {now} &nbsp;|&nbsp; {summary['total_channels']} channels registered
</div>

</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def run():
    print("CHANNEL_ROUTER -- Multi-Channel Fallback Router")
    print("=" * 52)
    ts = datetime.now(timezone.utc).isoformat()
    print(f"  Run started: {ts}")

    # 1. Detect live channel statuses
    print("\n[1] Detecting channel statuses...")
    statuses = detect_channel_status()
    available = sum(1 for s in statuses.values() if s in ("available", "always_available"))
    down = sum(1 for s in statuses.values() if s == "down")
    intermittent = sum(1 for s in statuses.values() if s == "intermittent")
    print(f"    {len(statuses)} channels  |  {available} available  |  {intermittent} intermittent  |  {down} down")

    if statuses.get("chrome_mcp") == "down":
        print("    [!] Chrome MCP is DOWN — fallback routing active")
        print(f"        Primary fallback: brave_browser ({CHANNELS['brave_browser']['tool']})")

    # 2. Process task queue
    print("\n[2] Processing task queue...")
    queue_data, routing_decisions = process_queue(statuses)
    routed = sum(1 for d in routing_decisions if d["decision"] == "routed")
    blocked = sum(1 for d in routing_decisions if d["decision"] == "no_channel_available")
    print(f"    Tasks processed: {len(routing_decisions)}  |  routed: {routed}  |  blocked: {blocked}")

    for d in routing_decisions:
        if d["decision"] == "routed":
            print(f"    -> [{d['task_type']}] routed to {d['assigned_channel']} ({d['assigned_tool']})")
        else:
            print(f"    -> [{d['task_type']}] BLOCKED — no available channel in chain")

    # 3. Build state report
    print("\n[3] Building state report...")
    state = build_state_report(statuses, routing_decisions, queue_data)
    state_path = DATA / "channel_router_state.json"
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"    Written: {state_path}")

    # 4. Generate HTML dashboard
    print("\n[4] Generating HTML dashboard...")
    html = generate_html_dashboard(state)
    html_path = DOCS / "channels.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"    Written: {html_path}")

    # 5. Ensure queue file exists (write empty structure if missing)
    queue_path = DATA / "channel_router_queue.json"
    if not queue_path.exists():
        queue_path.write_text(json.dumps({
            "pending": [],
            "completed": [],
            "failed": [],
            "last_processed": ts,
            "_help": (
                "Add tasks to 'pending' as objects with 'type', 'id', and optional 'payload'. "
                f"Valid task types: {sorted(TASK_ROUTING.keys())}"
            ),
        }, indent=2), encoding="utf-8")
        print(f"    Initialized empty queue: {queue_path}")

    # 6. Summary
    print("\n" + "=" * 52)
    print(f"  Channels total:    {len(CHANNELS)}")
    print(f"  Available:         {available}")
    print(f"  Intermittent:      {intermittent}")
    print(f"  Down:              {down}")
    print(f"  Tasks routed:      {routed}")
    print(f"  Tasks blocked:     {blocked}")
    print(f"  Dashboard:         {html_path}")
    print(f"  State:             {state_path}")
    print("=" * 52)
    print("  CHANNEL_ROUTER complete.")
    return state


if __name__ == "__main__":
    run()
