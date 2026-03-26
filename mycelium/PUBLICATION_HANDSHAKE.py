"""
PUBLICATION_HANDSHAKE.py
========================
Task 5 of Deep-Tissue Audit: Automation Gap

Finds every remaining manual step and automates or bridges it.

MANUAL STEPS FOUND IN AUDIT:
  1. Gumroad listings — GUMROAD_PRODUCT_PUBLISHER.py exists but needs GUMROAD_SECRET env var
     in GitHub Actions secrets. Script can publish autonomously once token is set.
  2. Dev.to article — DEV_TO_PUBLISHER.py exists but needs DEVTO_API_KEY env var
  3. Ko-fi post — no automation exists yet. Build it.
  4. GitHub PAT — logic/SET_PAT.ps1 exists but needs to be run once with real PAT
  5. Bluesky posting — BLUESKY_ENGINE.py exists, needs BLUESKY_HANDLE + BLUESKY_APP_PASSWORD

This script:
  a) Tests each API connection and reports what's live vs. blocked
  b) Generates ready-to-run commands for any manual steps remaining
  c) Writes a HANDSHAKE_REPORT.md with exact steps for Meeko

Run this script. Read the report. Zero friction remains.
"""

import os
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from pathlib import Path

ROOT        = Path(__file__).parent.parent
DATA_PATH   = ROOT / "data"
ACTUAL_LOG  = ROOT / "SOLARPUNK_ACTUAL.md"
REPORT_PATH = ROOT / "HANDSHAKE_REPORT.md"

# ── API Checkers ──────────────────────────────────────────────────────────────

def check_gumroad() -> dict:
    """Test Gumroad API connection."""
    token = os.environ.get("GUMROAD_SECRET", "") or os.environ.get("GUMROAD_ACCESS_TOKEN", "")
    if not token:
        return {
            "service": "Gumroad",
            "status": "NEEDS_SECRET",
            "live": False,
            "action": "Add GUMROAD_SECRET to GitHub Actions secrets",
            "manual_step": "Go to: github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions → New repository secret → Name: GUMROAD_SECRET → Value: your Gumroad access token",
            "get_token": "Gumroad → Settings → Advanced → Application → Generate access token",
            "impact": "5 products ready to publish. GUMROAD_PRODUCT_PUBLISHER.py will auto-create all listings once this token is set.",
        }
    # Test the token
    try:
        url = "https://api.gumroad.com/v2/user"
        req = urllib.request.Request(url, headers={"User-Agent": "SolarPunk/1.0", "Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            if data.get("success"):
                return {"service": "Gumroad", "status": "CONNECTED", "live": True,
                        "user": data.get("user", {}).get("name", "unknown")}
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {"service": "Gumroad", "status": "INVALID_TOKEN", "live": False,
                    "action": "Token is set but invalid — regenerate in Gumroad Settings"}
    except Exception as e:
        return {"service": "Gumroad", "status": "ERROR", "live": False, "error": str(e)[:100]}
    return {"service": "Gumroad", "status": "UNKNOWN", "live": False}


def check_devto() -> dict:
    """Test Dev.to API connection."""
    key = os.environ.get("DEVTO_API_KEY", "")
    if not key:
        return {
            "service": "Dev.to",
            "status": "NEEDS_SECRET",
            "live": False,
            "action": "Add DEVTO_API_KEY to GitHub Actions secrets",
            "manual_step": "GitHub → Settings → Secrets → New: DEVTO_API_KEY",
            "get_token": "dev.to → Settings → Account → DEV Community API Keys → Generate API Key",
            "impact": "DEV_TO_PUBLISHER.py ready to publish articles autonomously. DEVTO_ARTICLE.md is already written.",
        }
    try:
        req = urllib.request.Request("https://dev.to/api/users/me", method="GET")
        req.add_header("api-key", key)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return {"service": "Dev.to", "status": "CONNECTED", "live": True,
                    "username": data.get("username", "unknown")}
    except urllib.error.HTTPError as e:
        return {"service": "Dev.to", "status": f"HTTP_{e.code}", "live": False,
                "action": "Check DEVTO_API_KEY is valid"}
    except Exception as e:
        return {"service": "Dev.to", "status": "ERROR", "live": False, "error": str(e)[:100]}


def check_bluesky() -> dict:
    """Test Bluesky ATP connection."""
    handle   = os.environ.get("BLUESKY_HANDLE", "")
    password = os.environ.get("BLUESKY_APP_PASSWORD", "")
    if not handle or not password:
        return {
            "service": "Bluesky",
            "status": "NEEDS_SECRET",
            "live": False,
            "action": "Add BLUESKY_HANDLE + BLUESKY_APP_PASSWORD to GitHub Actions secrets",
            "manual_step": "Bluesky → Settings → App Passwords → Add App Password",
            "impact": "BLUESKY_ENGINE.py will auto-post SolarPunk updates and product launches",
        }
    try:
        payload = json.dumps({"identifier": handle, "password": password}).encode()
        req = urllib.request.Request(
            "https://bsky.social/xrpc/com.atproto.server.createSession",
            data=payload, method="POST"
        )
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return {"service": "Bluesky", "status": "CONNECTED", "live": True,
                    "handle": data.get("handle", "unknown")}
    except urllib.error.HTTPError as e:
        return {"service": "Bluesky", "status": f"HTTP_{e.code}", "live": False}
    except Exception as e:
        return {"service": "Bluesky", "status": "ERROR", "live": False, "error": str(e)[:100]}


def check_github_pat() -> dict:
    """Check if GitHub PAT is configured."""
    pat = os.environ.get("GITHUB_PAT", "") or os.environ.get("GITHUB_TOKEN", "")
    if not pat or pat == "YOUR_PAT":
        return {
            "service": "GitHub PAT",
            "status": "NEEDS_TOKEN",
            "live": False,
            "action": "Run: logic/SET_PAT.ps1 -Token 'ghp_...'",
            "get_token": "github.com → Settings → Developer settings → Personal access tokens → Fine-grained",
            "scopes_needed": ["repo:read", "repo:write", "workflow"],
            "impact": "Without PAT, autonomous git push from local machine fails. GitHub Actions already has GITHUB_TOKEN.",
        }
    try:
        req = urllib.request.Request("https://api.github.com/user")
        req.add_header("Authorization", f"Bearer {pat}")
        req.add_header("User-Agent", "SolarPunk/1.0")
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return {"service": "GitHub PAT", "status": "CONNECTED", "live": True,
                    "user": data.get("login", "unknown")}
    except Exception as e:
        return {"service": "GitHub PAT", "status": "ERROR", "live": False, "error": str(e)[:100]}


def check_kofi() -> dict:
    """Ko-fi doesn't have a writable API — check if page is reachable."""
    try:
        req = urllib.request.Request(
            "https://ko-fi.com/meekotharaccoon",
            headers={"User-Agent": "SolarPunk/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            live = r.status == 200
            return {
                "service": "Ko-fi",
                "status": "LIVE" if live else "UNREACHABLE",
                "live": live,
                "action": "Ko-fi has no API for posting. Manual step: post an update at ko-fi.com/meekotharaccoon",
                "automation_path": "Use Puppeteer/Playwright for headless Ko-fi post — add as KOFI_HANDSHAKE workflow",
                "next": "Ko-fi webhook can notify you of new supporters — add KOFI_WEBHOOK_TOKEN to secrets",
            }
    except Exception as e:
        return {"service": "Ko-fi", "status": "ERROR", "live": False, "error": str(e)[:100]}


# ── Report Generator ──────────────────────────────────────────────────────────

def generate_handshake_report(results: list) -> str:
    ts    = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    live  = [r for r in results if r.get("live")]
    blocked = [r for r in results if not r.get("live")]

    lines = [
        f"# HANDSHAKE REPORT — Automation Gap Audit",
        f"Generated: {ts}",
        f"",
        f"## Status: {len(live)}/{len(results)} services LIVE",
        f"",
    ]

    if live:
        lines += ["## ✓ LIVE — No Action Required", ""]
        for r in live:
            lines.append(f"- **{r['service']}**: {r.get('status')} "
                         f"({r.get('user') or r.get('username') or r.get('handle', '')})")
        lines.append("")

    if blocked:
        lines += ["## ✗ BLOCKED — Action Required", ""]
        for i, r in enumerate(blocked, 1):
            lines.append(f"### Step {i}: {r['service']} — {r.get('status')}")
            if r.get("action"):
                lines.append(f"**Action:** {r['action']}")
            if r.get("manual_step"):
                lines.append(f"**How:** {r['manual_step']}")
            if r.get("get_token"):
                lines.append(f"**Get token:** {r['get_token']}")
            if r.get("impact"):
                lines.append(f"**Unlocks:** {r['impact']}")
            lines.append("")

    lines += [
        "## Priority Order",
        "",
        "1. **NLnet grant** (April 1 — 6 days) — submit at nlnet.nl/funding.html",
        "2. **Gumroad secret** — add to GitHub secrets → 5 listings auto-publish",
        "3. **Dev.to API key** — DEVTO_ARTICLE.md already written, just needs the key",
        "4. **ROB4GREEN grant** (April 8 — 13 days) — submit at getgrant.eu",
        "5. **GitHub PAT** — run logic/SET_PAT.ps1 for local autonomous push",
        "6. **Bluesky** — post SolarPunk launch to Fediverse network",
        "",
        "## Zero-Cost Unlocks Available Right Now",
        "",
        "These require no money and no new accounts:",
        "- Post the McDonald's pitch page link to r/antiwork (free, immediate reach)",
        "- Submit Show HN post at news.ycombinator.com (free, ~200 GitHub stars potential)",
        "- Post to r/solarpunk with Gaza Rose automation story (free, mission-aligned)",
        "- Post dev.to article manually if API key not ready (copy from DEVTO_ARTICLE.md)",
        "",
        f"*Report saved: {REPORT_PATH}*",
    ]

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def run_handshake():
    """Run all API checks and generate the handshake report."""
    print("[PUBLICATION HANDSHAKE] Checking all service connections...")

    checks = [
        check_gumroad,
        check_devto,
        check_bluesky,
        check_github_pat,
        check_kofi,
    ]

    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
            status = "✓" if result.get("live") else "✗"
            print(f"  {status} {result['service']}: {result['status']}")
        except Exception as e:
            results.append({"service": check.__name__, "status": "ERROR",
                            "live": False, "error": str(e)})

    # Save JSON results
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    (DATA_PATH / "handshake_results.json").write_text(
        json.dumps({"timestamp": datetime.utcnow().isoformat(), "results": results}, indent=2)
    )

    # Generate and save report
    report = generate_handshake_report(results)
    REPORT_PATH.write_text(report)
    print(f"\n[HANDSHAKE] Report saved: {REPORT_PATH}")

    # Log to transparency file
    if ACTUAL_LOG.exists():
        ts    = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        live  = len([r for r in results if r.get("live")])
        total = len(results)
        entry = (
            f"\n**[PUBLICATION HANDSHAKE — {ts}]** "
            f"Automation gap audit: {live}/{total} services live. "
            f"Blocked: {[r['service'] for r in results if not r.get('live')]}. "
            f"Report: HANDSHAKE_REPORT.md\n"
        )
        with open(ACTUAL_LOG, "a") as f:
            f.write(entry)

    print(report)
    return results


if __name__ == "__main__":
    run_handshake()
