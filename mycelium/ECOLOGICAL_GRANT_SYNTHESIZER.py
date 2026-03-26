#!/usr/bin/env python3
"""
ECOLOGICAL_GRANT_SYNTHESIZER.py — Hybrid-3 Mutation
====================================================
Parents: RIVER_WATCH + FUND_SCOUT
Emergent behavior: Neither parent could do this alone.

RIVER_WATCH monitors the Cuyahoga River and Gorge Dam removal.
FUND_SCOUT discovers grant opportunities.
This hybrid COMBINES them: it searches for ecological/environmental grants
specifically matched to the river data SolarPunk is already collecting.

When RIVER_WATCH detects poor water quality or new EPA actions,
this engine automatically searches for environmental restoration grants
that match those specific conditions.

Zero secrets needed — uses Grants.gov API (free) + river data from disk.
"""
import json
import os
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# Environmental grant keywords mapped to river conditions
CONDITION_GRANT_MAP = {
    "low_flow": ["drought resilience", "water conservation", "stream restoration"],
    "high_flow": ["flood mitigation", "stormwater management", "green infrastructure"],
    "dam_removal": ["dam removal", "fish passage", "river restoration", "aquatic habitat"],
    "poor_quality": ["water quality improvement", "pollution remediation", "watershed protection"],
    "epa_action": ["environmental compliance", "clean water", "EPA enforcement"],
    "default": ["environmental restoration", "watershed", "Great Lakes", "Ohio river"]
}

GRANTS_GOV_API = "https://apply07.grants.gov/grantsws/rest/opportunities/search/"


def load_river_data():
    """Load the latest RIVER_WATCH results."""
    f = DATA / "river_watch.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text())
    except Exception:
        return None


def assess_conditions(river):
    """Determine current river conditions from data."""
    conditions = []

    if not river:
        return ["default"]

    # Check flow data
    flow = river.get("usgs_flow", {})
    if isinstance(flow, dict):
        val = flow.get("value")
        if val and isinstance(val, (int, float)):
            if val < 100:
                conditions.append("low_flow")
            elif val > 5000:
                conditions.append("high_flow")

    # Check for dam-related news
    fed_reg = river.get("federal_register", [])
    if isinstance(fed_reg, list) and len(fed_reg) > 0:
        conditions.append("dam_removal")

    # Check EPA actions
    epa_count = river.get("epa_count", 0)
    if epa_count and epa_count > 10:
        conditions.append("epa_action")

    # Check water quality
    wq = river.get("wq_count", 0)
    if wq == 0:
        conditions.append("poor_quality")  # No data = flag for investigation

    return conditions if conditions else ["default"]


def search_grants(keywords, max_results=5):
    """Search Grants.gov for matching environmental grants."""
    results = []

    for kw in keywords[:3]:  # Limit to 3 keyword searches
        try:
            payload = json.dumps({
                "keyword": kw,
                "oppStatuses": "forecasted|posted",
                "rows": max_results
            }).encode()

            req = urllib.request.Request(
                GRANTS_GOV_API,
                data=payload,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "SolarPunk-EcoGrant/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                opps = data.get("oppHits", [])
                for opp in opps:
                    results.append({
                        "title": opp.get("title", ""),
                        "number": opp.get("number", ""),
                        "agency": opp.get("agencyCode", ""),
                        "close_date": opp.get("closeDate", ""),
                        "keyword_match": kw,
                        "url": f"https://www.grants.gov/search-results-detail/{opp.get('id', '')}"
                    })
        except Exception as e:
            print(f"  Grant search error for '{kw}': {e}")

    # Deduplicate by grant number
    seen = set()
    unique = []
    for r in results:
        num = r.get("number", "")
        if num and num not in seen:
            seen.add(num)
            unique.append(r)

    return unique


def run():
    print("ECOLOGICAL GRANT SYNTHESIZER — Hybrid-3 Mutation")
    print("Parents: RIVER_WATCH + FUND_SCOUT")
    print("=" * 50)

    # Load river data
    river = load_river_data()
    if river:
        print(f"  River data loaded: {river.get('timestamp', 'unknown')}")
    else:
        print("  No river data yet — using default ecological keywords")

    # Assess conditions
    conditions = assess_conditions(river)
    print(f"  Conditions detected: {conditions}")

    # Build keyword list from conditions
    keywords = []
    for cond in conditions:
        keywords.extend(CONDITION_GRANT_MAP.get(cond, []))
    keywords = list(dict.fromkeys(keywords))[:6]  # Dedupe, limit to 6
    print(f"  Grant keywords: {keywords}")

    # Search grants
    grants = search_grants(keywords)
    print(f"  Grants found: {len(grants)}")

    for g in grants[:5]:
        print(f"    [{g['agency']}] {g['title'][:60]}...")
        print(f"      Matched: '{g['keyword_match']}' | Closes: {g['close_date']}")

    # Save results
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "river_conditions": conditions,
        "keywords_searched": keywords,
        "grants_found": len(grants),
        "grants": grants[:20],
        "parents": ["RIVER_WATCH", "FUND_SCOUT"],
        "mutation_type": "Hybrid-3"
    }

    out = DATA / "eco_grant_state.json"
    out.write_text(json.dumps(state, indent=2))
    print(f"\n  State saved: {out}")
    print(f"  This engine finds grants that MATCH the river's actual conditions.")
    print(f"  Neither RIVER_WATCH nor FUND_SCOUT could do this alone.")


if __name__ == "__main__":
    run()
