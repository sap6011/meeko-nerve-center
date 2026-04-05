#!/usr/bin/env python3
"""
INBOUND_LISTENER.py -- GitHub Inbound Activity Sensor
======================================================
Watches our repo for new stars, forks, issues, traffic, and referrers.
Detects CHANGES since last run and emits signals for TASK_FACTORY
and SIGNAL_CHAIN to act on.

Uses ONLY stdlib (urllib, json, os, pathlib). No requests.
Works without GITHUB_TOKEN (unauthenticated, 60 req/hr).
Works better WITH GITHUB_TOKEN (5000 req/hr + traffic/referrer data).

Reads:  data/inbound_listener_state.json (previous counts)
Writes: data/inbound_listener_state.json (updated counts + history)
        data/inbound_signals.json (new signals for other engines)

Signals emitted:
  new_star   -> SIGNAL_CHAIN tweets social proof
  new_fork   -> SIGNAL_CHAIN queues outreach
  new_issue  -> TASK_FACTORY creates triage task
  traffic_spike -> SIGNAL_CHAIN amplifies whatever is working
  new_referrer  -> TASK_FACTORY creates SEO/content task
"""
import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

STATE_FILE   = DATA / "inbound_listener_state.json"
SIGNALS_FILE = DATA / "inbound_signals.json"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_API       = "https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center"
USER_AGENT   = "SolarPunk-InboundListener/1.0"


# ---------------------------------------------------------------------------
# GitHub API helpers (urllib only)
# ---------------------------------------------------------------------------

def gh_get(path):
    """GET a GitHub API endpoint. Returns parsed JSON or None."""
    url = "%s%s" % (GH_API, path) if path.startswith("/") else path
    if not url.startswith("http"):
        url = "%s/%s" % (GH_API, path)
    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", USER_AGENT)
        if GITHUB_TOKEN:
            req.add_header("Authorization", "token %s" % GITHUB_TOKEN)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print("  API error %d on %s" % (e.code, url))
        return None
    except Exception as e:
        print("  Request failed: %s" % str(e)[:120])
        return None


def fetch_repo_info():
    """Fetch core repo stats: stars, forks, open_issues."""
    data = gh_get("")
    if not data:
        return {}
    return {
        "stars":       data.get("stargazers_count", 0),
        "forks":       data.get("forks_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "watchers":    data.get("subscribers_count", 0),
        "size_kb":     data.get("size", 0),
    }


def fetch_traffic_clones():
    """Fetch clone counts (requires push access + token)."""
    data = gh_get("/traffic/clones")
    if not data:
        return {}
    return {
        "clone_count":   data.get("count", 0),
        "clone_uniques": data.get("uniques", 0),
    }


def fetch_traffic_views():
    """Fetch page view counts (requires push access + token)."""
    data = gh_get("/traffic/views")
    if not data:
        return {}
    return {
        "view_count":   data.get("count", 0),
        "view_uniques": data.get("uniques", 0),
    }


def fetch_referrers():
    """Fetch top referral sources (requires push access + token)."""
    data = gh_get("/traffic/popular/referrers")
    if not data or not isinstance(data, list):
        return []
    refs = []
    for r in data[:10]:
        refs.append({
            "referrer": r.get("referrer", "unknown"),
            "count":    r.get("count", 0),
            "uniques":  r.get("uniques", 0),
        })
    return refs


def fetch_recent_issues(per_page=5):
    """Fetch recently opened issues."""
    data = gh_get("/issues?state=open&sort=created&direction=desc&per_page=%d" % per_page)
    if not data or not isinstance(data, list):
        return []
    issues = []
    for i in data:
        # Skip pull requests (GitHub API returns PRs in /issues too)
        if i.get("pull_request"):
            continue
        issues.append({
            "number":    i.get("number", 0),
            "title":     i.get("title", ""),
            "user":      i.get("user", {}).get("login", "unknown"),
            "created_at": i.get("created_at", ""),
        })
    return issues


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "last_stars": 0,
        "last_forks": 0,
        "last_open_issues": 0,
        "last_clone_count": 0,
        "last_view_count": 0,
        "known_issue_numbers": [],
        "known_referrers": [],
        "history": [],
        "cycles": 0,
        "last_run": None,
    }


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )


def load_signals():
    if SIGNALS_FILE.exists():
        try:
            return json.loads(SIGNALS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"signals": [], "total_ever": 0, "last_updated": None}


def save_signals(sig):
    SIGNALS_FILE.write_text(
        json.dumps(sig, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Signal detection
# ---------------------------------------------------------------------------

def detect_signals(state, repo_info, traffic, views, referrers, issues):
    """Compare current data to previous state. Return list of new signals."""
    now = datetime.now(timezone.utc).isoformat()
    signals = []

    # -- Stars --
    curr_stars = repo_info.get("stars", 0)
    prev_stars = state.get("last_stars", 0)
    if curr_stars > prev_stars:
        delta = curr_stars - prev_stars
        signals.append({
            "type": "new_star",
            "delta": delta,
            "total": curr_stars,
            "message": "+%d star%s (total: %d)" % (delta, "s" if delta != 1 else "", curr_stars),
            "priority": "high",
            "ts": now,
        })
        print("  SIGNAL: +%d star%s (now %d)" % (delta, "s" if delta != 1 else "", curr_stars))

    # -- Forks --
    curr_forks = repo_info.get("forks", 0)
    prev_forks = state.get("last_forks", 0)
    if curr_forks > prev_forks:
        delta = curr_forks - prev_forks
        signals.append({
            "type": "new_fork",
            "delta": delta,
            "total": curr_forks,
            "message": "+%d fork%s (total: %d)" % (delta, "s" if delta != 1 else "", curr_forks),
            "priority": "high",
            "ts": now,
        })
        print("  SIGNAL: +%d fork%s (now %d)" % (delta, "s" if delta != 1 else "", curr_forks))

    # -- Issues --
    curr_open = repo_info.get("open_issues", 0)
    prev_open = state.get("last_open_issues", 0)
    known_nums = set(state.get("known_issue_numbers", []))
    new_issues = []
    for iss in issues:
        num = iss.get("number", 0)
        if num and num not in known_nums:
            new_issues.append(iss)
            known_nums.add(num)
    if new_issues:
        signals.append({
            "type": "new_issue",
            "count": len(new_issues),
            "issues": new_issues,
            "message": "%d new issue%s opened" % (len(new_issues), "s" if len(new_issues) != 1 else ""),
            "priority": "medium",
            "ts": now,
        })
        for iss in new_issues:
            print("  SIGNAL: new issue #%d -- %s (by %s)" % (
                iss.get("number", 0), iss.get("title", "?"), iss.get("user", "?")))
    state["known_issue_numbers"] = list(known_nums)[-100:]

    # -- Traffic spike (clones) --
    curr_clones = traffic.get("clone_count", 0)
    prev_clones = state.get("last_clone_count", 0)
    if curr_clones > prev_clones and prev_clones > 0:
        ratio = curr_clones / max(prev_clones, 1)
        if ratio >= 1.5:
            signals.append({
                "type": "traffic_spike",
                "metric": "clones",
                "previous": prev_clones,
                "current": curr_clones,
                "message": "Clone spike: %d -> %d (%.1fx)" % (prev_clones, curr_clones, ratio),
                "priority": "medium",
                "ts": now,
            })
            print("  SIGNAL: clone spike %d -> %d (%.1fx)" % (prev_clones, curr_clones, ratio))

    # -- Traffic spike (views) --
    curr_views = views.get("view_count", 0)
    prev_views = state.get("last_view_count", 0)
    if curr_views > prev_views and prev_views > 0:
        ratio = curr_views / max(prev_views, 1)
        if ratio >= 1.5:
            signals.append({
                "type": "traffic_spike",
                "metric": "views",
                "previous": prev_views,
                "current": curr_views,
                "message": "View spike: %d -> %d (%.1fx)" % (prev_views, curr_views, ratio),
                "priority": "medium",
                "ts": now,
            })
            print("  SIGNAL: view spike %d -> %d (%.1fx)" % (prev_views, curr_views, ratio))

    # -- New referrers --
    known_refs = set(state.get("known_referrers", []))
    new_refs = []
    for ref in referrers:
        name = ref.get("referrer", "")
        if name and name not in known_refs:
            new_refs.append(ref)
            known_refs.add(name)
    if new_refs:
        signals.append({
            "type": "new_referrer",
            "referrers": new_refs,
            "message": "%d new referrer%s: %s" % (
                len(new_refs),
                "s" if len(new_refs) != 1 else "",
                ", ".join(r.get("referrer", "?") for r in new_refs),
            ),
            "priority": "low",
            "ts": now,
        })
        for ref in new_refs:
            print("  SIGNAL: new referrer -- %s (%d visits)" % (
                ref.get("referrer", "?"), ref.get("count", 0)))
    state["known_referrers"] = list(known_refs)[-50:]

    # -- Update state counts --
    state["last_stars"]       = curr_stars
    state["last_forks"]       = curr_forks
    state["last_open_issues"] = curr_open
    if curr_clones > 0:
        state["last_clone_count"] = curr_clones
    if curr_views > 0:
        state["last_view_count"] = curr_views

    return signals


def build_task_factory_entries(signals):
    """Convert signals into task entries that TASK_FACTORY can consume."""
    tasks = []
    for sig in signals:
        stype = sig.get("type", "")

        if stype == "new_issue":
            for iss in sig.get("issues", []):
                tasks.append({
                    "type": "TRIAGE",
                    "priority": 2,
                    "title": "Triage issue #%d: %s" % (iss.get("number", 0), iss.get("title", "")),
                    "engine": "ISSUE_SYNC",
                    "command": "python mycelium/ISSUE_SYNC.py",
                    "expected_output": "Issue #%d labeled and assigned" % iss.get("number", 0),
                    "autonomous": True,
                    "source": "INBOUND_LISTENER",
                })

        elif stype == "new_star":
            tasks.append({
                "type": "CONTENT",
                "priority": 3,
                "title": "Social proof: %s" % sig.get("message", "new stars"),
                "engine": "SIGNAL_CHAIN",
                "command": "python mycelium/SIGNAL_CHAIN.py",
                "expected_output": "Social post queued celebrating star milestone",
                "autonomous": True,
                "source": "INBOUND_LISTENER",
            })

        elif stype == "new_fork":
            tasks.append({
                "type": "OUTREACH",
                "priority": 2,
                "title": "Fork outreach: %s" % sig.get("message", "new forks"),
                "engine": "SIGNAL_CHAIN",
                "command": "python mycelium/SIGNAL_CHAIN.py",
                "expected_output": "Outreach action queued for new fork",
                "autonomous": True,
                "source": "INBOUND_LISTENER",
            })

        elif stype == "traffic_spike":
            tasks.append({
                "type": "CONTENT",
                "priority": 3,
                "title": "Amplify traffic spike: %s" % sig.get("message", "spike"),
                "engine": "SIGNAL_BOOST",
                "command": "python mycelium/SIGNAL_BOOST.py",
                "expected_output": "Content amplification triggered",
                "autonomous": True,
                "source": "INBOUND_LISTENER",
            })

        elif stype == "new_referrer":
            for ref in sig.get("referrers", []):
                tasks.append({
                    "type": "GROW",
                    "priority": 4,
                    "title": "Optimize for referrer: %s (%d visits)" % (
                        ref.get("referrer", "?"), ref.get("count", 0)),
                    "engine": "CONTENT_HARVESTER",
                    "command": "python mycelium/CONTENT_HARVESTER.py",
                    "expected_output": "SEO/content action for new referral source",
                    "autonomous": True,
                    "source": "INBOUND_LISTENER",
                })

    return tasks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    print("INBOUND_LISTENER -- GitHub Activity Sensor")
    print("=" * 50)

    state = load_state()
    state["cycles"] = state.get("cycles", 0) + 1
    now = datetime.now(timezone.utc).isoformat()

    auth_mode = "authenticated" if GITHUB_TOKEN else "unauthenticated (60 req/hr)"
    print("  Mode: %s" % auth_mode)

    # --- Fetch all data ---
    print("\n  [1/4] Fetching repo info...")
    repo_info = fetch_repo_info()
    if not repo_info:
        print("  ABORT: Could not reach GitHub API")
        state["last_run"] = now
        state["last_error"] = "API unreachable"
        save_state(state)
        return state

    print("    Stars: %d | Forks: %d | Issues: %d | Watchers: %d" % (
        repo_info.get("stars", 0),
        repo_info.get("forks", 0),
        repo_info.get("open_issues", 0),
        repo_info.get("watchers", 0),
    ))

    print("\n  [2/4] Fetching traffic + referrers...")
    traffic   = fetch_traffic_clones()
    views     = fetch_traffic_views()
    referrers = fetch_referrers()
    if traffic:
        print("    Clones: %d (%d unique)" % (
            traffic.get("clone_count", 0), traffic.get("clone_uniques", 0)))
    if views:
        print("    Views: %d (%d unique)" % (
            views.get("view_count", 0), views.get("view_uniques", 0)))
    if referrers:
        print("    Referrers: %s" % ", ".join(
            r.get("referrer", "?") for r in referrers[:5]))
    if not traffic and not views:
        print("    (Traffic data requires GITHUB_TOKEN with push access)")

    print("\n  [3/4] Fetching recent issues...")
    issues = fetch_recent_issues(per_page=10)
    print("    Open issues fetched: %d" % len(issues))

    # --- Detect signals ---
    print("\n  [4/4] Detecting new signals...")
    signals = detect_signals(state, repo_info, traffic, views, referrers, issues)

    # --- Build task entries ---
    task_entries = build_task_factory_entries(signals)

    # --- Save signals file ---
    sig_store = load_signals()
    sig_store["signals"].extend(signals)
    sig_store["signals"] = sig_store["signals"][-200:]  # bounded history
    sig_store["total_ever"] = sig_store.get("total_ever", 0) + len(signals)
    sig_store["last_updated"] = now
    sig_store["pending_tasks"] = task_entries
    sig_store["snapshot"] = {
        "stars":       repo_info.get("stars", 0),
        "forks":       repo_info.get("forks", 0),
        "open_issues": repo_info.get("open_issues", 0),
        "watchers":    repo_info.get("watchers", 0),
        "clone_count": traffic.get("clone_count", 0),
        "view_count":  views.get("view_count", 0),
        "referrers":   referrers,
        "fetched_at":  now,
    }
    save_signals(sig_store)

    # --- Update state ---
    state["last_run"]   = now
    state["last_error"] = None
    state["last_snapshot"] = sig_store.get("snapshot", {})
    state["history"].append({
        "ts": now,
        "signals": len(signals),
        "tasks":   len(task_entries),
        "stars":   repo_info.get("stars", 0),
        "forks":   repo_info.get("forks", 0),
    })
    state["history"] = state["history"][-100:]  # keep last 100 cycles
    save_state(state)

    # --- Summary ---
    print("\n  === INBOUND LISTENER SUMMARY ===")
    print("  Cycle:           %d" % state.get("cycles", 0))
    print("  Signals found:   %d" % len(signals))
    print("  Tasks generated: %d" % len(task_entries))
    print("  Total signals:   %d (all time)" % sig_store.get("total_ever", 0))
    if signals:
        for s in signals:
            print("    [%s] %s" % (s.get("type", "?"), s.get("message", "")))
    else:
        print("  (No new activity since last run)")
    print("  Listening never stops. Every signal becomes an action.")

    return state


if __name__ == "__main__":
    run()
