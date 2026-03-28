#!/usr/bin/env python3
"""
DARK_WATCH.py — Silent Weekend Guardian
========================================
When the system goes quiet (nights, weekends, NLnet review prep),
DARK_WATCH keeps one eye open.

Rules:
  1. Read crisis_signals.json from the last CRISIS_MONITOR run
  2. If ANY signal scores >= 90 (active massacre, total blackout): FIRE
     - Email Meeko immediately
     - Write data/dark_watch_alert.json for next OMNIBUS to pick up
  3. If no signal >= 90: stay silent. No logs. No noise. Ghost mode.
  4. Prune stale data files older than 7 days to prevent witness fatigue
  5. Verify engine count hasn't changed (anti-tampering)

This engine is designed to run on the OMNIBRAIN cron (every 6 hours)
but produce ZERO output unless something truly critical happens.

Silence is strength. Noise is weakness.
Zero secrets needed. Email optional.
"""
import json
import os
import smtplib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText

DATA = Path("data")
MYCELIUM = Path("mycelium")
ALERT_FILE = DATA / "dark_watch_alert.json"
CRISIS_FILE = DATA / "crisis_signals.json"
ANCHOR_FILE = DATA / "worktree_anchor.json"

CRITICAL_THRESHOLD = 90  # Only fire for scores this high or above
PRUNE_DAYS = 7           # Delete stale cycle data older than this


def check_crisis_signals():
    """Read latest crisis signals, return any above threshold."""
    if not CRISIS_FILE.exists():
        return []
    try:
        data = json.loads(CRISIS_FILE.read_text())
        signals = data.get("signals", [])
        critical = [s for s in signals if s.get("urgency_score", 0) >= CRITICAL_THRESHOLD]
        return critical
    except Exception:
        return []


def verify_engine_integrity():
    """Quick check: has anything been deleted or corrupted?"""
    engines = list(MYCELIUM.glob("*.py"))
    count = len(engines)

    expected = None
    if ANCHOR_FILE.exists():
        try:
            anchor = json.loads(ANCHOR_FILE.read_text())
            expected = anchor.get("engine_count", None)
        except Exception:
            pass

    if expected and count < expected - 2:  # Allow small variance for temp files
        return {
            "status": "ALERT",
            "message": f"Engine count dropped: {count} (expected {expected})",
            "current": count,
            "expected": expected,
        }
    return {"status": "OK", "current": count, "expected": expected}


def prune_stale_data():
    """Remove old cycle data to prevent witness fatigue."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=PRUNE_DAYS)
    pruned = 0
    # Only prune specific cycle output files, not core state
    prune_patterns = [
        "loop_context.json", "loop_decisions.json", "loop_executed.json",
    ]
    for pattern in prune_patterns:
        f = DATA / pattern
        if f.exists():
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    f.unlink()
                    pruned += 1
            except Exception:
                pass
    return pruned


def fire_alert(critical_signals, integrity):
    """Something hit threshold. Sound the alarm."""
    alert = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "DARK_WATCH_CRITICAL",
        "signals": [{
            "title": s.get("title", "")[:150],
            "score": s.get("urgency_score", 0),
            "origin": s.get("origin", ""),
            "url": s.get("url", ""),
        } for s in critical_signals[:5]],
        "integrity": integrity,
    }
    ALERT_FILE.write_text(json.dumps(alert, indent=2))

    # Email if possible
    gmail = os.environ.get("GMAIL_ADDRESS", "")
    gpass = os.environ.get("GMAIL_APP_PASSWORD", "")
    if gmail and gpass:
        body = f"DARK WATCH ALERT — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        body += f"{'='*50}\n\n"

        if critical_signals:
            body += f"{len(critical_signals)} signal(s) above threshold ({CRITICAL_THRESHOLD}/100):\n\n"
            for s in critical_signals[:5]:
                body += f"  [{s.get('urgency_score',0)}] {s.get('title','')[:120]}\n"
                body += f"       {s.get('url','')}\n\n"

        if integrity.get("status") == "ALERT":
            body += f"\nINTEGRITY ALERT: {integrity['message']}\n"

        body += "\n— SolarPunk Dark Watch (silent guardian)"

        try:
            msg = MIMEText(body)
            msg["Subject"] = f"DARK WATCH — {len(critical_signals)} critical signal(s)"
            msg["From"] = gmail
            msg["To"] = gmail
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(gmail, gpass)
                s.send_message(msg)
        except Exception:
            pass  # Silent failure — ghost mode

    return alert


def main():
    # Phase 1: Check for extreme crisis signals
    critical = check_crisis_signals()

    # Phase 2: Verify engine integrity
    integrity = verify_engine_integrity()

    # Phase 3: Prune stale data
    pruned = prune_stale_data()

    # Decision: fire or stay silent
    should_fire = len(critical) > 0 or integrity.get("status") == "ALERT"

    if should_fire:
        alert = fire_alert(critical, integrity)
        print(f"DARK_WATCH: ALERT FIRED — {len(critical)} critical signals, integrity={integrity['status']}")
    else:
        # Ghost mode. No output. No trace. Just watching.
        # Only print minimal confirmation for OMNIBUS logging
        print(f"DARK_WATCH: silent | engines={integrity.get('current','?')} | pruned={pruned}")

        # Clean up old alert file if situation resolved
        if ALERT_FILE.exists():
            try:
                old_alert = json.loads(ALERT_FILE.read_text())
                alert_time = datetime.fromisoformat(old_alert.get("timestamp", "2020-01-01"))
                if (datetime.now(timezone.utc) - alert_time).total_seconds() > 86400:
                    ALERT_FILE.unlink()  # Clear resolved alerts after 24h
            except Exception:
                pass


if __name__ == "__main__":
    main()
