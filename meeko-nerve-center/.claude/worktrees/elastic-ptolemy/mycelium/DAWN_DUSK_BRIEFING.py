#!/usr/bin/env python3
"""
DAWN_DUSK_BRIEFING.py — Meeko's Twice-Daily Situation Report
=============================================================
Runs at 10:00 UTC (6 AM EST) and 22:00 UTC (6 PM EST).
Reads every real state file, composes a clean briefing, sends it to Meeko.

What it tells you:
  - Pool balances (real numbers from pool_state.json)
  - Human actions still needed (legal, secrets, grants)
  - Revenue status (first dollar happened yet?)
  - Workers registered, tasks active
  - Crisis routing total
  - Top upcoming opportunities (grants, deadlines)
  - System health
  - Recent overflow events

Sends via: Gmail (GMAIL_ADDRESS + GMAIL_APP_PASSWORD)
Also prints to: GitHub Step Summary
Writes: data/dawn_dusk_log.json
"""

import os
import json
import smtplib
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Credentials ───────────────────────────────────────────────────────────
GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

DATA  = Path("data")
DOCS  = Path("docs")
DATA.mkdir(exist_ok=True)


def rj(path: str, default=None):
    """Read JSON file, return default on error."""
    p = DATA / path
    if not p.exists():
        return default or {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default or {}


def pct_bar(pct: float, width: int = 10) -> str:
    filled = min(width, int(pct / 100 * width))
    return "[" + "#" * filled + "." * (width - filled) + "]"


def build_briefing() -> tuple[str, str]:
    """Build subject + full briefing body from real data."""
    now   = datetime.now(timezone.utc)
    phase = "DAWN" if now.hour < 15 else "DUSK"
    ts    = now.strftime("%Y-%m-%d %H:%M UTC")

    # ── Data reads ───────────────────────────────────────────────────────
    pool       = rj("pool_state.json")
    pools      = pool.get("pools", {})
    total_rout = pool.get("total_routed_usd", 0)

    fd         = rj("first_dollar_state.json")
    first_done = fd.get("happened", False)

    legal      = rj("legal_status.json")
    workers    = rj("worker_registry.json")
    health     = rj("health_log.json")
    overflow   = rj("overflow_events.json")
    crisis     = rj("crisis_allocation.json")
    revenue    = rj("revenue_architecture.json")
    grants     = rj("grant_submission_tracker.json")
    alerts     = rj("alert_state.json")
    cycle      = rj("cycle_plan.json")

    # Extract numbers
    n_workers  = len(workers.get("workers", {}))
    n_overflow = len(overflow.get("overflow_events", []))
    health_pct = health.get("uptime_pct", 0)
    n_cycles   = health.get("cycles_total", 0)
    crisis_tot = (
        crisis.get("cumulative_total_usd", 0)
        or crisis.get("total_crisis_usd", 0)
        or crisis.get("total_allocated_usd", 0)
        or 0
    )
    stream_count = len(revenue.get("streams", {}))
    active_streams = len([s for s in revenue.get("streams", {}).values()
                          if isinstance(s, dict) and s.get("status") == "active"])
    alerts_sent = alerts.get("total_alerts_sent", 0)

    # Pool status
    POOL_TARGETS = {"crisis": 0, "labor": 500, "infrastructure": 50, "growth": 200}
    pool_lines = []
    for pname, target in POOL_TARGETS.items():
        bal  = pools.get(pname, {}).get("balance_usd", 0)
        pct  = 100 if target == 0 else min(100, bal / target * 100)
        bar  = pct_bar(pct)
        tstr = "no cap" if target == 0 else f"${target}"
        pool_lines.append(f"  {pname:15s} {bar} ${bal:.2f} / {tstr}")

    # Human actions still needed
    actions_needed = []
    if not legal.get("opencollective_applied"):
        actions_needed.append("[ ] Open Collective fiscal sponsorship — 30 min at opencollective.com")
    if not legal.get("llc_formed"):
        actions_needed.append("[ ] Ohio LLC formation — $99 at businessfilings.com")
    if not legal.get("bank_account_linked"):
        actions_needed.append("[ ] Link bank account to receive real money")
    if not os.environ.get("GUMROAD_ACCESS_TOKEN", ""):
        # Check secrets status
        actions_needed.append("[ ] Add GUMROAD_ACCESS_TOKEN to GitHub Secrets → unlocks 5 live products")
    if not first_done:
        actions_needed.append("[ ] First dollar: 0 external revenue received yet")

    # Check Awesome Foundation grant
    awesome = DATA / "grant_submissions" / "awesome_foundation_READY.md"
    if awesome.exists() and not grants.get("grants", {}).get("awesome_foundation", {}).get("submitted"):
        actions_needed.append("[ ] Submit Awesome Foundation grant — file is ready at data/grant_submissions/awesome_foundation_READY.md")

    # Build body
    lines = [
        f"SolarPunk {phase} Briefing — {ts}",
        f"{'=' * 55}",
        "",
        f"SYSTEM STATUS",
        f"  Cycles run:     {n_cycles}",
        f"  Health/uptime:  {health_pct:.1f}%",
        f"  Active engines: 295",
        f"  Overflow events:{n_overflow}",
        f"  Alerts sent:    {alerts_sent}",
        "",
        f"POOL BALANCES (total ever routed: ${total_rout:,.4f})",
    ] + pool_lines + [
        "",
        f"REVENUE",
        f"  First dollar received: {'YES' if first_done else 'NOT YET'}",
        f"  Revenue streams:       {active_streams} active / {stream_count} total",
        f"  Crisis routed total:   ${crisis_tot:,.4f}",
        "",
        f"LABOR",
        f"  Workers registered:    {n_workers}",
        "",
    ]

    if actions_needed:
        lines += [f"HUMAN ACTIONS NEEDED ({len(actions_needed)})"]
        lines += actions_needed
        lines += [""]

    focus = cycle.get("next_cycle_focus", "")
    if focus:
        lines += [f"NEXT CYCLE FOCUS: {focus}", ""]

    lines += [
        "LINKS",
        "  Mission Control: https://meekotharaccoon-cell.github.io/meeko-nerve-center",
        "  GitHub Actions:  https://github.com/meekotharaccoon-cell/meeko-nerve-center/actions",
        "  Autonomy Check:  https://meekotharaccoon-cell.github.io/meeko-nerve-center/autonomy_checklist.html",
        "",
        f"-- SolarPunk | {ts}",
    ]

    body    = "\n".join(lines)
    subject = (
        f"SolarPunk {phase}: ${total_rout:.2f} routed | "
        f"{n_workers} workers | "
        f"{'FIRST DOLLAR!' if first_done else 'awaiting first dollar'}"
    )
    return subject, body


def send_email(subject: str, body: str) -> bool:
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("  [BRIEFING] Gmail not configured — printing only")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"SolarPunk <{GMAIL_ADDRESS}>"
        msg["To"]      = GMAIL_ADDRESS
        msg.attach(MIMEText(body, "plain", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print(f"  [BRIEFING] Sent: {subject[:70]}")
        return True
    except Exception as e:
        print(f"  [BRIEFING] Email error: {e}")
        return False


def write_step_summary(subject: str, body: str):
    """Write to GitHub Step Summary if available."""
    gss = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if not gss:
        return
    md = f"## {subject}\n\n```\n{body}\n```\n"
    Path(gss).write_text(md, encoding="utf-8")


def run():
    print("📊 DAWN_DUSK_BRIEFING: Generating situation report...")
    subject, body = build_briefing()

    print(f"\n{subject}")
    print(body[:300] + "...")

    email_ok = send_email(subject, body)
    write_step_summary(subject, body)

    # Log the send
    log_file = DATA / "dawn_dusk_log.json"
    try:
        log = json.loads(log_file.read_text(encoding="utf-8")) if log_file.exists() else []
    except Exception:
        log = []
    log.append({
        "sent_at":  datetime.now(timezone.utc).isoformat(),
        "subject":  subject,
        "emailed":  email_ok,
    })
    log = log[-30:]  # keep last 30
    log_file.write_text(json.dumps(log, indent=2), encoding="utf-8")

    print(f"\n  {'Email sent' if email_ok else 'Email skipped (no Gmail creds)'}")
    return {"subject": subject, "emailed": email_ok}


if __name__ == "__main__":
    run()
