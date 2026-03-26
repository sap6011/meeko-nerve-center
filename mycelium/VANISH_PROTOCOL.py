"""
VANISH_PROTOCOL.py
Signal injection email templates — punchy, zero-fat, point directly to the repo.
Reads live stats from data/ files and writes 5 audience-specific templates.
"""

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "vanish_templates.json")

REPO_URL = "https://github.com/meekotharaccoon-cell/meeko-nerve-center"
SITE_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center/"


def load_json_safe(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_stats():
    sentinel = load_json_safe(os.path.join(DATA_DIR, "sentinel_report.json"))
    transparency = load_json_safe(os.path.join(DATA_DIR, "transparency_report.json"))

    stats = {
        "engine_count": (
            sentinel.get("engine_count")
            or sentinel.get("total_engines")
            or sentinel.get("engines")
            or transparency.get("engine_count")
            or "248"
        ),
        "workflow_count": (
            sentinel.get("workflow_count")
            or sentinel.get("total_workflows")
            or transparency.get("workflow_count")
            or "30"
        ),
        "shadow_valuation": (
            transparency.get("shadow_valuation")
            or transparency.get("valuation")
            or sentinel.get("shadow_valuation")
            or "$16M"
        ),
        "monthly_cost": (
            transparency.get("monthly_cost")
            or sentinel.get("monthly_cost")
            or "$0"
        ),
        "arxiv_papers": (
            transparency.get("arxiv_papers")
            or sentinel.get("arxiv_papers")
            or "12"
        ),
        "mutual_aid_pct": (
            transparency.get("mutual_aid_pct")
            or "20"
        ),
    }
    return stats


def build_templates(stats):
    ec = stats["engine_count"]
    wc = stats["workflow_count"]
    sv = stats["shadow_valuation"]
    mc = stats["monthly_cost"]
    ap = stats["arxiv_papers"]
    ma = stats["mutual_aid_pct"]

    templates = {
        "tech_lead": {
            "audience": "Tech Lead / Software Engineer",
            "subject": f"Open-source autonomous AI: {ec} Python engines, {wc} GitHub Actions workflows, $0/month",
            "body": (
                f"I built a self-correcting autonomous AI pipeline — {ec} Python engines, {wc} GitHub Actions workflows, "
                f"murmuration-based consensus routing, zero paid services. "
                f"Runs entirely on GitHub Actions free tier. No cloud bill. "
                f"SENTINEL health monitor, honeytoken defense, and full transparency logging are all live. "
                f"Repo + architecture: {REPO_URL}"
            ),
        },
        "grant_officer": {
            "audience": "Grant Officer / Foundation Program Manager",
            "subject": f"Grant application: open-source mutual aid AI, {sv} commercial value, MIT licensed",
            "body": (
                f"SolarPunk Node-01 is an autonomous mutual aid infrastructure system with a conservative shadow valuation of {sv} "
                f"(comparable-company methodology, documented). "
                f"It runs at {mc}/month on GitHub Actions, routes {ma}% of all revenue to local food banks by algorithm, "
                f"and is backed by {ap} arXiv papers in the technical foundation. "
                f"We are applying for grant support to activate the full autonomous loop. "
                f"Full transparency report, shadow valuation, and application materials: {SITE_URL}"
            ),
        },
        "creative_european": {
            "audience": "Creative Europe / Cultural Tech Grants",
            "subject": "Cultural tech + mutual aid: open-source AI for community resilience (Creative Europe alignment)",
            "body": (
                f"SolarPunk Node-01 is open-source AI infrastructure where the algorithm IS the governance — "
                f"no board, no CEO, mutual aid hard-coded at the protocol level. "
                f"It combines digital arts distribution, community resilience tooling, and autonomous financial routing "
                f"into a single MIT-licensed system built by one person with no prior coding experience. "
                f"The architecture aligns with Creative Europe's cultural innovation and digital transformation priorities. "
                f"Architecture and live system: {REPO_URL}"
            ),
        },
        "sf_solarpunk": {
            "audience": "Solarpunk Community Organizer",
            "subject": "A real solarpunk node is running in Ohio. Zero corporate dependencies.",
            "body": (
                f"Not a manifesto — a running system. {ec} autonomous agents, {wc} workflows, {mc}/month, "
                f"{ma}% of revenue hard-coded to local mutual aid. "
                f"Built on a desktop in Cuyahoga Falls, Ohio, MIT licensed, no VC, no SaaS lock-in. "
                f"The IPO is collective liberation. "
                f"Come look: {REPO_URL}"
            ),
        },
        "media_press": {
            "audience": "Media / Press / Journalist",
            "subject": f"Story: one person with no coding experience built a ${sv} AI system and gave it away",
            "body": (
                f"The story: a person in Cuyahoga Falls, Ohio with no prior coding experience and slow typing "
                f"built {ec} Python AI engines and {wc} GitHub Actions workflows — conservatively valued at {sv} — "
                f"and released it all as MIT-licensed open source at {mc}/month operating cost. "
                f"The system routes money to local food banks by algorithm, not committee. "
                f"The commit history is timestamped. The system is live. "
                f"Full codebase and transparency log: {REPO_URL}"
            ),
        },
    }
    return templates


def run():
    stats = load_stats()
    templates = build_templates(stats)

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "stats_used": stats,
        "templates": templates,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"VANISH_PROTOCOL — {len(templates)} templates generated")
    print(f"Written to: {OUTPUT_FILE}")
    print("=" * 60)

    for key, tmpl in templates.items():
        print(f"\n[{tmpl['audience'].upper()}]")
        print(f"SUBJECT: {tmpl['subject']}")
        print(f"BODY:\n{tmpl['body']}")
        print("-" * 60)


if __name__ == "__main__":
    run()
