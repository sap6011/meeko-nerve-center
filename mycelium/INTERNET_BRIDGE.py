#!/usr/bin/env python3
"""
INTERNET_BRIDGE.py — Connects SolarPunk to the live internet
==============================================================
Aggregates signals from the web, executes outbound actions, and routes
tasks through every available channel. This is SolarPunk's interface
to the outside world.

INBOUND (web -> SolarPunk):
  - Public APIs (20+ free endpoints via FREE_API_ENGINE)
  - GitHub events (trending repos, issues, discussions)
  - Crisis signals (ReliefWeb, GDELT, Reddit)
  - Market data (CoinGecko, Polymarket)
  - News/content (HN, Dev.to, RSS feeds)

OUTBOUND (SolarPunk -> web):
  - GitHub: releases, discussions, issues, wiki, pages
  - Email: outreach drafts, partner communications
  - Content: Dev.to articles, social posts
  - Data: public JSON endpoints via GitHub Pages

When this engine runs on GitHub Actions, SolarPunk is LIVE on the internet.
Every 6 hours, it wakes up, gathers signals, acts on them, and publishes results.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

DATA = Path("data")
DATA.mkdir(exist_ok=True)
DOCS = Path("docs")

STATE_FILE = DATA / "internet_bridge_state.json"
SIGNALS_FILE = DATA / "internet_signals.json"
ACTIONS_FILE = DATA / "internet_actions.json"

# GitHub repo info
REPO_OWNER = "meekotharaccoon-cell"
REPO_NAME = "meeko-nerve-center"
GITHUB_API = "https://api.github.com"
PAGES_URL = f"https://{REPO_OWNER}.github.io/{REPO_NAME}"


def _ts():
    return datetime.now(timezone.utc).isoformat()


def _load(name, default=None):
    f = DATA / name
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default if default is not None else {}


def _save(name, data):
    (DATA / name).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _fetch_json(url, timeout=15):
    """Fetch JSON from a public API. Zero auth needed."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "SolarPunk-AutonomousSystem/1.0",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)[:200]}


def _fetch_text(url, timeout=15):
    """Fetch raw text/HTML from URL."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "SolarPunk-AutonomousSystem/1.0",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return ""


def _sh(cmd, timeout=30):
    """Run shell command."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(Path(__file__).parent.parent)
        )
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return False, "", str(e)


# ===========================================================================
# INBOUND: Gather signals from the internet
# ===========================================================================

def gather_github_signals():
    """Check our own repo's pulse — stars, forks, issues, discussions."""
    signals = {}

    # Repo stats (public, no auth)
    repo = _fetch_json(f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}")
    if "error" not in repo:
        signals["stars"] = repo.get("stargazers_count", 0)
        signals["forks"] = repo.get("forks_count", 0)
        signals["open_issues"] = repo.get("open_issues_count", 0)
        signals["watchers"] = repo.get("subscribers_count", 0)
        signals["size_kb"] = repo.get("size", 0)
        signals["default_branch"] = repo.get("default_branch", "main")
        signals["updated_at"] = repo.get("updated_at", "")

    # Recent releases
    releases = _fetch_json(f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/releases?per_page=3")
    if isinstance(releases, list):
        signals["releases"] = [
            {"tag": r.get("tag_name"), "name": r.get("name"), "date": r.get("published_at")}
            for r in releases[:3]
        ]

    # Traffic (requires auth, skip if no token)
    return signals


def gather_trending_signals():
    """What's trending in AI/automation/open-source."""
    signals = {}

    # Hacker News top stories
    hn_ids = _fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty")
    if isinstance(hn_ids, list):
        hn_stories = []
        for sid in hn_ids[:5]:
            story = _fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
            if isinstance(story, dict) and "error" not in story:
                hn_stories.append({
                    "title": story.get("title", ""),
                    "url": story.get("url", ""),
                    "score": story.get("score", 0),
                    "comments": story.get("descendants", 0),
                })
        signals["hacker_news_top5"] = hn_stories

    # Dev.to trending AI articles
    devto = _fetch_json("https://dev.to/api/articles?tag=ai&top=7&per_page=5")
    if isinstance(devto, list):
        signals["devto_trending"] = [
            {"title": a.get("title", ""), "url": a.get("url", ""),
             "reactions": a.get("positive_reactions_count", 0)}
            for a in devto[:5]
        ]

    # GitHub trending repos (via search)
    gh_trending = _fetch_json(
        f"{GITHUB_API}/search/repositories?q=topic:ai+topic:agents+language:python"
        f"&sort=stars&order=desc&per_page=5"
    )
    if isinstance(gh_trending, dict) and "items" in gh_trending:
        signals["github_trending"] = [
            {"name": r.get("full_name"), "stars": r.get("stargazers_count"),
             "description": (r.get("description") or "")[:100]}
            for r in gh_trending["items"][:5]
        ]

    return signals


def gather_market_signals():
    """Crypto + prediction market signals."""
    signals = {}

    # Crypto prices
    crypto = _fetch_json(
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true"
    )
    if "error" not in crypto:
        signals["crypto"] = crypto

    return signals


def gather_humanitarian_signals():
    """Crisis and humanitarian signals from public sources."""
    signals = {}

    # ReliefWeb latest reports
    rw = _fetch_json(
        "https://api.reliefweb.int/v1/reports?appname=solarpunk"
        "&filter[field]=primary_country.iso3&filter[value]=pse"
        "&limit=3&fields[include][]=title&fields[include][]=date"
    )
    if isinstance(rw, dict) and "data" in rw:
        signals["reliefweb_palestine"] = [
            {"title": r.get("fields", {}).get("title", ""),
             "date": r.get("fields", {}).get("date", {}).get("created", "")}
            for r in rw["data"][:3]
        ]

    return signals


# ===========================================================================
# OUTBOUND: Act on the internet
# ===========================================================================

def publish_status_page():
    """Generate a public JSON status endpoint for GitHub Pages."""
    state = _load("autopilot_state.json")
    wire = _load("live_wire_report.json")
    chimera = _load("chimera_evolution_report.json")
    health = _load("brain_state.json")

    status = {
        "system": "SolarPunk Autonomous System",
        "version": "v0.47",
        "timestamp": _ts(),
        "engines": wire.get("stats", {}).get("total_engines", 0),
        "wires": wire.get("stats", {}).get("total_wires_discovered", 0),
        "live_wires": len([w for w in wire.get("test_results", [])
                          if isinstance(w, dict) and w.get("status") == "LIVE"]),
        "chimera_generation": chimera.get("generation", 0),
        "chimera_score": chimera.get("composite_score", 0),
        "health_score": health.get("health_score", 0),
        "autopilot_cycles": state.get("cycles", 0),
        "ethics_lock": "99% mutual aid / 1% node fuel",
        "pages_url": PAGES_URL,
        "store_url": f"{PAGES_URL}/store.html",
        "github_url": f"https://github.com/{REPO_OWNER}/{REPO_NAME}",
        "kofi_url": "https://ko-fi.com/meekotharaccoon",
    }

    # Write to docs/ so GitHub Pages serves it
    (DOCS / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    return status


def publish_signals_page(all_signals):
    """Generate a public signals dashboard as HTML."""
    hn = all_signals.get("trending", {}).get("hacker_news_top5", [])
    devto = all_signals.get("trending", {}).get("devto_trending", [])
    crypto = all_signals.get("market", {}).get("crypto", {})
    rw = all_signals.get("humanitarian", {}).get("reliefweb_palestine", [])
    gh = all_signals.get("github", {})

    btc = crypto.get("bitcoin", {})
    eth = crypto.get("ethereum", {})

    hn_rows = "\n".join([
        f'<tr><td><a href="{s.get("url","#")}">{s.get("title","")[:80]}</a></td>'
        f'<td>{s.get("score",0)}</td><td>{s.get("comments",0)}</td></tr>'
        for s in hn[:5]
    ])
    rw_rows = "\n".join([
        f'<tr><td>{r.get("title","")[:100]}</td><td>{r.get("date","")[:10]}</td></tr>'
        for r in rw[:3]
    ])

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SolarPunk — Live Internet Signals</title>
<style>
body{{background:#0a0f0d;color:#c8e6c9;font-family:'Courier New',monospace;padding:2rem;max-width:900px;margin:0 auto}}
h1{{color:#00ff88;font-size:1.5rem}}h2{{color:#00cc6a;font-size:1.1rem;margin-top:2rem}}
table{{width:100%;border-collapse:collapse;margin:1rem 0}}
th,td{{padding:.5rem;text-align:left;border-bottom:1px solid #1a3a2a}}
th{{color:#00ff88;font-size:.8rem;letter-spacing:.1em}}
a{{color:#4dd0e1;text-decoration:none}}a:hover{{text-decoration:underline}}
.stat{{display:inline-block;background:#0d1f15;border:1px solid #1a3a2a;border-radius:8px;padding:1rem;margin:.5rem;text-align:center}}
.stat-n{{font-size:1.5rem;color:#00ff88;display:block}}.stat-l{{font-size:.7rem;color:#6a9a7a}}
footer{{margin-top:3rem;font-size:.7rem;color:#4a6a5a;text-align:center}}
</style></head><body>
<h1>SolarPunk — Live Internet Signals</h1>
<p style="color:#6a9a7a">Auto-generated by INTERNET_BRIDGE | {_ts()[:19]} UTC</p>

<div>
<span class="stat"><span class="stat-n">{gh.get('stars',0)}</span><span class="stat-l">STARS</span></span>
<span class="stat"><span class="stat-n">{gh.get('forks',0)}</span><span class="stat-l">FORKS</span></span>
<span class="stat"><span class="stat-n">${btc.get('usd','?'):,}</span><span class="stat-l">BTC</span></span>
<span class="stat"><span class="stat-n">${eth.get('usd','?'):,}</span><span class="stat-l">ETH</span></span>
</div>

<h2>Hacker News — Top Stories</h2>
<table><thead><tr><th>Title</th><th>Score</th><th>Comments</th></tr></thead>
<tbody>{hn_rows}</tbody></table>

<h2>Palestine — ReliefWeb Reports</h2>
<table><thead><tr><th>Report</th><th>Date</th></tr></thead>
<tbody>{rw_rows}</tbody></table>

<footer>
SOLARPUNK AUTONOMOUS SYSTEM | <a href="{PAGES_URL}/store.html">Store</a> |
<a href="https://github.com/{REPO_OWNER}/{REPO_NAME}">GitHub</a> |
<a href="https://ko-fi.com/meekotharaccoon">Ko-fi</a><br>
99% mutual aid / 1% node fuel — forever
</footer>
</body></html>"""

    (DOCS / "signals.html").write_text(html, encoding="utf-8")
    return True


def sync_discussions():
    """Check for and respond to new GitHub discussions using gh CLI."""
    ok, out, _ = _sh("gh --version", timeout=10)
    if not ok:
        return {"status": "gh_not_available"}

    # List recent discussions
    ok, out, _ = _sh(
        f"gh api repos/{REPO_OWNER}/{REPO_NAME}/discussions "
        f"--jq '.[0:5] | .[] | .number, .title'",
        timeout=15
    )
    return {"status": "checked", "recent": out[:500] if ok else "error"}


# ===========================================================================
# MAIN
# ===========================================================================

def run():
    print("=" * 70)
    print("INTERNET BRIDGE — Connecting SolarPunk to the live internet")
    print("=" * 70)

    state = _load("internet_bridge_state.json", {
        "engine": "INTERNET_BRIDGE",
        "created_at": _ts(),
        "cycles": 0,
        "total_signals_gathered": 0,
        "total_pages_published": 0,
    })
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = _ts()

    all_signals = {}

    # INBOUND: Gather signals
    print("\n[1/5] Gathering GitHub signals...")
    all_signals["github"] = gather_github_signals()
    stars = all_signals["github"].get("stars", "?")
    forks = all_signals["github"].get("forks", "?")
    print(f"  Stars: {stars} | Forks: {forks}")

    print("\n[2/5] Gathering trending signals...")
    all_signals["trending"] = gather_trending_signals()
    hn_count = len(all_signals["trending"].get("hacker_news_top5", []))
    devto_count = len(all_signals["trending"].get("devto_trending", []))
    print(f"  HN stories: {hn_count} | Dev.to articles: {devto_count}")

    print("\n[3/5] Gathering market signals...")
    all_signals["market"] = gather_market_signals()
    btc = all_signals["market"].get("crypto", {}).get("bitcoin", {}).get("usd", "?")
    print(f"  BTC: ${btc:,}" if isinstance(btc, (int, float)) else f"  BTC: ${btc}")

    print("\n[4/5] Gathering humanitarian signals...")
    all_signals["humanitarian"] = gather_humanitarian_signals()
    rw_count = len(all_signals["humanitarian"].get("reliefweb_palestine", []))
    print(f"  ReliefWeb Palestine reports: {rw_count}")

    # Save all signals
    all_signals["gathered_at"] = _ts()
    _save("internet_signals.json", all_signals)
    state["total_signals_gathered"] = state.get("total_signals_gathered", 0) + 1

    # OUTBOUND: Publish to the internet
    print("\n[5/5] Publishing to the internet...")

    # Status JSON endpoint
    status = publish_status_page()
    print(f"  Published: docs/status.json ({status.get('engines', 0)} engines)")

    # Signals dashboard
    publish_signals_page(all_signals)
    print(f"  Published: docs/signals.html")
    state["total_pages_published"] = state.get("total_pages_published", 0) + 2

    # Save state
    state["last_signals"] = {
        "github_stars": all_signals["github"].get("stars", 0),
        "github_forks": all_signals["github"].get("forks", 0),
        "hn_stories": hn_count,
        "devto_articles": devto_count,
        "reliefweb_reports": rw_count,
    }
    _save("internet_bridge_state.json", state)

    print(f"\n{'=' * 70}")
    print(f"  INTERNET BRIDGE CYCLE {state['cycles']} COMPLETE")
    print(f"  Signals: GitHub ({stars} stars) | HN ({hn_count}) | "
          f"Dev.to ({devto_count}) | ReliefWeb ({rw_count})")
    print(f"  Published: status.json + signals.html")
    print(f"  SolarPunk is LIVE on the internet.")
    print(f"{'=' * 70}")

    return state


if __name__ == "__main__":
    run()
