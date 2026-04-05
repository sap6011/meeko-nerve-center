#!/usr/bin/env python3
"""
CREDENTIAL_SENSOR.py -- Auto-detect and activate infrastructure bridges
========================================================================
Scans environment variables and config files for newly added credentials.
When a new credential is detected:
  1. Reports which engines are now unblocked
  2. Generates a quick-start checklist
  3. Updates the resource allocator state

This is the "plug it in and it lights up" engine.
Add an API key -> this engine detects it -> reports what just came online.

Reads: data/resource_allocator_plan.json, data/credential_sensor_state.json
Writes: data/credential_sensor_state.json, data/credential_sensor_report.json
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)


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


# Credential -> what it unlocks
CREDENTIAL_MAP = {
    "GITHUB_TOKEN": {
        "name": "GitHub Personal Access Token",
        "engines": ["GITHUB_POSTER", "GITHUB_RELEASES_PUBLISHER", "ANALYTICS_ENGINE",
                     "REPO_SPIDER", "FORK_SCANNER", "SIGNAL_BOOST", "EVENT_RELAY"],
        "setup_steps": [
            "Token detected. The following engines will activate on next OMNIBUS run:",
            "  - GITHUB_POSTER: auto-post to GitHub Discussions",
            "  - GITHUB_RELEASES_PUBLISHER: create releases for products",
            "  - ANALYTICS_ENGINE: track repo traffic and stars",
            "  - REPO_SPIDER: scan for forks and derivatives",
            "  - FORK_SCANNER: detect who's using your code",
            "  - SIGNAL_BOOST: create permanent public records via Issues",
            "  - EVENT_RELAY: auto-create PRs for changes",
        ],
    },
    "GROQ_API_KEY": {
        "name": "Groq API Key",
        "engines": ["CORTEX", "CONTENT_AUTOPILOT", "PDF_GENERATOR",
                     "PASSIVE_INCOME_ARCHITECT", "ETSY_SEO_ENGINE",
                     "BIG_BRAIN_ORACLE", "HEALTH_BOOSTER"],
        "setup_steps": [
            "Groq API detected. AI-powered engines coming online:",
            "  - CORTEX: real AI reasoning instead of rule-based",
            "  - CONTENT_AUTOPILOT: AI-generated articles (not templates)",
            "  - PDF_GENERATOR: generate PDF products",
            "  - PASSIVE_INCOME_ARCHITECT: AI-scored income ideas",
            "  - BIG_BRAIN_ORACLE: AI analysis of system state",
        ],
    },
    "DEVTO_API_KEY": {
        "name": "Dev.to API Key",
        "engines": ["DEV_TO_PUBLISHER", "CONTENT_AUTOPILOT"],
        "setup_steps": [
            "Dev.to API detected. Content pipeline activated:",
            "  - DEV_TO_PUBLISHER: auto-publish article drafts",
            "  - CONTENT_AUTOPILOT: articles go live automatically",
            "  Note: articles publish as draft by default (published: false)",
        ],
    },
    "BLUESKY_HANDLE": {
        "name": "Bluesky Handle",
        "engines": ["BLUESKY_ENGINE"],
        "setup_steps": [
            "Bluesky handle detected. Also need BLUESKY_APP_PASSWORD.",
        ],
    },
    "BLUESKY_APP_PASSWORD": {
        "name": "Bluesky App Password",
        "engines": ["BLUESKY_ENGINE", "SOCIAL_PROMOTER", "AMPLIFY_ENGINE"],
        "setup_steps": [
            "Bluesky credentials complete. Social engines activated:",
            "  - BLUESKY_ENGINE: auto-post to Bluesky",
            "  - SOCIAL_PROMOTER: promote products on social",
            "  - AMPLIFY_ENGINE: amplify content across platforms",
        ],
    },
    "MASTODON_TOKEN": {
        "name": "Mastodon Access Token",
        "engines": ["MASTODON_ENGINE"],
        "setup_steps": [
            "Mastodon token detected.",
            "  - MASTODON_ENGINE: auto-post to Mastodon instance",
            "  Also set MASTODON_INSTANCE if not mastodon.social",
        ],
    },
    "NOTION_TOKEN": {
        "name": "Notion Integration Token",
        "engines": ["NOTION_NERVE_CENTER"],
        "setup_steps": [
            "Notion token detected.",
            "  - NOTION_NERVE_CENTER: live dashboard sync activated",
            "  Also set NOTION_DATABASE_ID for target database",
        ],
    },
    "KOFI_TOKEN": {
        "name": "Ko-fi API Token",
        "engines": ["QUICK_REVENUE", "NANOSHOP_ENGINE"],
        "setup_steps": [
            "Ko-fi token detected. Storefront engines activated:",
            "  - QUICK_REVENUE: direct product listings",
            "  - NANOSHOP_ENGINE: embeddable purchase widgets",
        ],
    },
    "OPENROUTER_API_KEY": {
        "name": "OpenRouter API Key",
        "engines": ["CORTEX", "CONTENT_AUTOPILOT", "BIG_BRAIN_ORACLE"],
        "setup_steps": [
            "OpenRouter API detected. AI fallback chain strengthened.",
            "  Priority: Groq -> OpenRouter -> Ollama -> rule-based",
        ],
    },
    "HF_TOKEN": {
        "name": "Hugging Face Token",
        "engines": ["AI_CLIENT"],
        "setup_steps": [
            "Hugging Face token detected. AI fallback chain extended.",
        ],
    },
}


def scan_credentials():
    """Scan for all known credentials."""
    found = {}
    missing = {}

    for env_var, info in CREDENTIAL_MAP.items():
        value = os.environ.get(env_var, "")
        if value:
            found[env_var] = {
                "name": info["name"],
                "engines_count": len(info["engines"]),
                "engines": info["engines"],
            }
        else:
            missing[env_var] = {
                "name": info["name"],
                "engines_count": len(info["engines"]),
                "engines": info["engines"],
            }

    return found, missing


def detect_new_credentials(found, state):
    """Detect credentials added since last run."""
    previously_found = set(state.get("known_credentials", []))
    currently_found = set(found.keys())
    new = currently_found - previously_found
    return new


def run():
    print("CREDENTIAL SENSOR -- Infrastructure Bridge Detector")
    print("=" * 60)

    state = load_json(DATA / "credential_sensor_state.json")
    if not state:
        state = {"known_credentials": [], "last_run": None, "activations": []}

    # Scan
    print("\n  [1/3] Scanning environment for credentials...")
    found, missing = scan_credentials()
    print("    Found:   %d credentials" % len(found))
    print("    Missing: %d credentials" % len(missing))

    # Detect new
    print("\n  [2/3] Detecting new credentials since last run...")
    new_creds = detect_new_credentials(found, state)
    if new_creds:
        print("    NEW CREDENTIALS DETECTED: %d" % len(new_creds))
        for cred in new_creds:
            info = CREDENTIAL_MAP[cred]
            print("\n    >>> %s (%s) <<<" % (cred, info["name"]))
            for step in info["setup_steps"]:
                print("    %s" % step)
            state.setdefault("activations", []).append({
                "credential": cred,
                "name": info["name"],
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "engines_unlocked": info["engines"],
            })
    else:
        print("    No new credentials since last run")

    # Report blocked engines
    print("\n  [3/3] Engines blocked by missing credentials...")
    total_blocked = 0
    for env_var, info in sorted(missing.items(), key=lambda x: -x[1]["engines_count"]):
        print("    %s (%s) -> %d engines blocked" % (
            env_var, info["name"], info["engines_count"]))
        total_blocked += info["engines_count"]

    # Summary of what's working
    total_active = sum(v["engines_count"] for v in found.values())

    # Save state
    state["known_credentials"] = list(found.keys())
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["found_count"] = len(found)
    state["missing_count"] = len(missing)
    save_json(DATA / "credential_sensor_state.json", state)

    # Save report
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "found": {k: v["name"] for k, v in found.items()},
        "missing": {k: v["name"] for k, v in missing.items()},
        "new_this_run": list(new_creds),
        "engines_active": total_active,
        "engines_blocked": total_blocked,
    }
    save_json(DATA / "credential_sensor_report.json", report)

    print("\n  === CREDENTIAL SENSOR SUMMARY ===")
    print("  Credentials found:    %d" % len(found))
    print("  Credentials missing:  %d" % len(missing))
    print("  New this run:         %d" % len(new_creds))
    print("  Engines active:       %d (via credentials)" % total_active)
    print("  Engines blocked:      %d (waiting for keys)" % total_blocked)
    print("\n  Plug in a key. Watch the engines light up.")


if __name__ == "__main__":
    run()
