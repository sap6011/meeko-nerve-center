#!/usr/bin/env python3
"""
WEEKEND_PULSE.py — Autonomous Heartbeat While Meeko Sleeps
===========================================================
SolarPunk doesn't sleep. When Meeko goes AFK, this engine keeps
a running pulse of everything the system does:

  - What crisis signals fired
  - What survival telegrams were generated
  - What amplification posts are queued
  - What NGO handshakes are waiting
  - Engine health (count, integrity)
  - Revenue events (if any)

Writes: data/weekend_pulse.json, docs/pulse.html
Reads: data/*.json (aggregates from all engines)

The pulse page is a single lightweight HTML file that Meeko can
check from a phone. No login needed. Just the facts.

"The system that runs while you dream."
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DOCS = Path("docs")
DATA.mkdir(exist_ok=True)
DOCS.mkdir(exist_ok=True)

PULSE_FILE = DATA / "weekend_pulse.json"
PULSE_HTML = DOCS / "pulse.html"


def safe_load(filepath):
    """Load JSON safely, return empty dict on failure."""
    try:
        if filepath.exists():
            return json.loads(filepath.read_text())
    except Exception:
        pass
    return {}


def gather_pulse():
    """Aggregate status from all engine outputs."""
    pulse = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sections": [],
    }

    # ── Engine Health ────────────────────────────────────────────
    anchor = safe_load(DATA / "worktree_anchor.json")
    engine_count = anchor.get("engine_count", "?")
    sovereign = anchor.get("sovereignty", "?")
    pulse["engine_count"] = engine_count
    pulse["sovereignty"] = sovereign
    pulse["sections"].append({
        "title": "System Health",
        "icon": "heartbeat",
        "items": [
            f"Engines: {engine_count}",
            f"Sovereignty: {sovereign}",
            f"Branch: {anchor.get('git_branch', '?')}",
            f"Anchor: {anchor.get('timestamp', '?')[:19]}",
        ],
    })

    # ── Crisis Signals ───────���───────────────────────────────────
    crisis = safe_load(DATA / "crisis_signals.json")
    total_signals = crisis.get("total", 0)
    by_urgency = crisis.get("by_urgency", {})
    critical = by_urgency.get("CRITICAL", 0)
    high = by_urgency.get("HIGH", 0)
    top_signals = []
    for s in crisis.get("signals", [])[:5]:
        top_signals.append(f"[{s.get('urgency','?')}] {s.get('title','')[:100]}")
    pulse["sections"].append({
        "title": "Crisis Monitor",
        "icon": "alert",
        "items": [
            f"Total signals: {total_signals}",
            f"CRITICAL: {critical} | HIGH: {high}",
        ] + top_signals[:3],
    })

    # ── Triggers & Handshakes ────────────────────────────────────
    triggers = safe_load(DATA / "crisis_triggers.json")
    handshakes = safe_load(DATA / "ngo_handshakes.json")
    pulse["sections"].append({
        "title": "Action Pipeline",
        "icon": "fire",
        "items": [
            f"Triggers fired: {triggers.get('count', 0)}",
            f"Target engines: {', '.join(triggers.get('target_engines', [])[:5])}",
            f"NGO handshakes queued: {handshakes.get('count', 0)}",
            f"Orgs targeted: {', '.join(handshakes.get('orgs_targeted', [])[:5])}",
        ],
    })

    # ── Resource Kits ─────────────���──────────────────────────────
    kits = safe_load(DATA / "resource_kits.json")
    telegrams = safe_load(DATA / "survival_telegrams.json")
    pulse["sections"].append({
        "title": "Liquid Data",
        "icon": "water",
        "items": [
            f"Kits: {kits.get('kit_count', 0)} ({kits.get('active_count', 0)} active)",
            f"Formats: {kits.get('total_formats', 0)} per kit",
            f"SMS segments: {telegrams.get('total_sms_segments', 0)}",
            f"Telegram bytes: {telegrams.get('total_bytes', 0)}",
        ],
    })

    # ── Amplification ────────────────────────────────────────────
    amplify = safe_load(DATA / "amplification_queue.json")
    social = safe_load(DATA / "social_queue.json")
    reddit = safe_load(DATA / "reddit_outreach_queue.json")
    broadcast = safe_load(DATA / "broadcast_queue.json")
    murmur_log = safe_load(DATA / "murmuration_log.json")
    pulse["sections"].append({
        "title": "Amplification",
        "icon": "megaphone",
        "items": [
            f"Social posts queued: {len(social.get('posts', []))}",
            f"Reddit posts queued: {reddit.get('new_this_cycle', 0)} new",
            f"Broadcast items: {broadcast.get('new_this_cycle', 0)} new",
            f"Amplify posts: {amplify.get('count', 0)}",
            f"Murmuration relays: {len(murmur_log.get('relays', []))}",
        ],
    })

    # ── Email Outreach ─────────���─────────────────────────────────
    outreach = safe_load(DATA / "outreach_state.json")
    total_sent = len([e for e in outreach.get("sent", []) if e.get("sent")])
    pulse["sections"].append({
        "title": "Outreach",
        "icon": "email",
        "items": [
            f"Outreach cycles: {outreach.get('cycles', 0)}",
            f"Emails sent (all-time): {total_sent}",
        ],
    })

    # ── Signal Boost ─────���───────────────────────────────────────
    boost = safe_load(DATA / "signal_boost_log.json")
    pulse["sections"].append({
        "title": "Signal Boost",
        "icon": "record",
        "items": [
            f"GitHub Issues created: {len(boost.get('issues_created', []))}",
        ],
    })

    # ── Dark Watch ───────────────────────────────────────────────
    dark_alert = safe_load(DATA / "dark_watch_alert.json")
    if dark_alert:
        pulse["sections"].append({
            "title": "DARK WATCH ALERT",
            "icon": "skull",
            "items": [
                f"Alert type: {dark_alert.get('type', '?')}",
                f"Signals: {len(dark_alert.get('signals', []))}",
                f"Time: {dark_alert.get('timestamp', '?')[:19]}",
            ],
        })
    else:
        pulse["sections"].append({
            "title": "Dark Watch",
            "icon": "moon",
            "items": ["Status: Silent. All clear."],
        })

    # ── Revenue ────��─────────────────────────────────────────────
    revenue = safe_load(DATA / "revenue_state.json")
    proof = safe_load(DATA / "proof_ledger.json")
    proof_count = len(proof.get("entries", [])) if isinstance(proof, dict) else len(proof) if isinstance(proof, list) else 0
    pulse["sections"].append({
        "title": "Revenue",
        "icon": "dollar",
        "items": [
            f"Products: {revenue.get('product_count', '?') if isinstance(revenue, dict) else '?'}",
            f"Proof entries: {proof_count}",
        ],
    })

    return pulse


def build_pulse_html(pulse):
    """Build a lightweight pulse page for mobile viewing."""
    ts = pulse["timestamp"][:19].replace("T", " ")

    icons = {
        "heartbeat": "&#x1F49A;", "alert": "&#x1F6A8;", "fire": "&#x1F525;",
        "water": "&#x1F4A7;", "megaphone": "&#x1F4E3;", "email": "&#x1F4E7;",
        "record": "&#x1F4CC;", "moon": "&#x1F319;", "skull": "&#x1F480;",
        "dollar": "&#x1F4B2;",
    }

    sections_html = ""
    for section in pulse.get("sections", []):
        icon = icons.get(section.get("icon", ""), "")
        is_alert = "ALERT" in section["title"]
        border_color = "#ff4444" if is_alert else "#00ff88"
        sections_html += f"""
        <div style="background:#161b22;border-left:4px solid {border_color};
                    padding:14px;margin:12px 0;border-radius:6px;">
            <h3 style="color:#eee;margin:0 0 8px 0;">{icon} {section['title']}</h3>
"""
        for item in section.get("items", []):
            color = "#ff4444" if "CRITICAL" in item else "#ccc"
            sections_html += f'            <div style="color:{color};font-size:14px;margin:4px 0;font-family:monospace;">{item}</div>\n'
        sections_html += "        </div>\n"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="300">
<title>SolarPunk Pulse</title>
<style>
body {{ background:#0d1117; color:#c9d1d9; font-family:-apple-system,sans-serif;
       max-width:600px; margin:0 auto; padding:16px; }}
h1 {{ color:#00ff88; text-align:center; font-size:1.5em; margin-bottom:4px; }}
.ts {{ text-align:center; color:#666; font-size:12px; margin-bottom:20px; }}
.badge {{ display:inline-block; background:#00ff88; color:#000; padding:2px 10px;
          border-radius:12px; font-size:12px; font-weight:bold; }}
.footer {{ text-align:center; margin-top:30px; color:#444; font-size:11px;
           border-top:1px solid #222; padding-top:12px; }}
</style>
</head>
<body>
<h1>SolarPunk Pulse</h1>
<div class="ts">{ts} UTC &middot; <span class="badge">{pulse.get('engine_count', '?')} engines</span></div>
{sections_html}
<div class="footer">
<p>Auto-refreshes every 5 minutes</p>
<p><a href="index.html" style="color:#58a6ff;">Dashboard</a> &middot;
<a href="emergency_kits.html" style="color:#58a6ff;">Emergency Kits</a> &middot;
<a href="store.html" style="color:#58a6ff;">Store</a> &middot;
<a href="crisis_dashboard.html" style="color:#58a6ff;">Crisis Monitor</a></p>
<p style="color:#333;">SolarPunk — the system that runs while you dream</p>
</div>
</body>
</html>"""
    return html


def main():
    print("WEEKEND_PULSE — Generating system heartbeat...")

    pulse = gather_pulse()

    # Write JSON
    PULSE_FILE.write_text(json.dumps(pulse, indent=2), encoding="utf-8")

    # Write HTML
    html = build_pulse_html(pulse)
    PULSE_HTML.write_text(html, encoding="utf-8")

    # Summary
    print(f"  Engines: {pulse.get('engine_count', '?')}")
    print(f"  Sovereignty: {pulse.get('sovereignty', '?')}")
    for section in pulse.get("sections", []):
        items = section.get("items", [])
        summary = items[0] if items else "—"
        print(f"  {section['title']}: {summary}")

    print(f"\n  Pulse page: docs/pulse.html")
    print(f"  Pulse data: data/weekend_pulse.json")
    print("WEEKEND_PULSE done.")


if __name__ == "__main__":
    main()
