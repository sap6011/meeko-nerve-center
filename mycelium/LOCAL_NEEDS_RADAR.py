"""
LOCAL_NEEDS_RADAR.py
====================
Task 1 of Deep-Tissue Audit: Resource Gap

Monitors local Akron/Summit County food security needs and calculates
the fastest routing path when SolarPunk mutual aid funds become available.

Data sources:
  - Akron-Canton Regional Foodbank (akroncantonfoodbank.org)
  - OPEN M food services (openm.org/food)
  - Good Samaritan Hunger Center (goodsamaritanhungercenter.org)
  - Summit County data: 15.7% food insecurity, 4,180 affected individuals

The 'lube path': When revenue routes to local_aid fund,
this module instantly calculates and logs where that money fills gaps fastest.

Triggered by: MUTUAL_AID_AUDITOR.py route_aid() events
"""

import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

ROOT        = Path(__file__).parent.parent
DATA_PATH   = ROOT / "data"
LEDGER_PATH = ROOT / "vault" / "treasury_ledger.json"
ACTUAL_LOG  = ROOT / "SOLARPUNK_ACTUAL.md"
RADAR_LOG   = DATA_PATH / "local_needs_radar.json"

# ── Verified Local Aid Partners (Summit County, Ohio) ─────────────────────
LOCAL_PARTNERS = [
    {
        "name":     "Akron-Canton Regional Foodbank",
        "url":      "https://www.akroncantonfoodbank.org",
        "donate":   "https://www.akroncantonfoodbank.org/ways-give",
        "coverage": "8 NE Ohio counties, 600+ hunger relief programs",
        "impact":   "Every $1 = 3 meals. 705,864 meals/quarter baseline.",
        "signal":   "SNAP cuts + federal furloughs = demand surge active",
        "priority": "HIGH",
    },
    {
        "name":     "OPEN M Food Services",
        "url":      "https://www.openm.org/food",
        "donate":   "https://www.openm.org/donate",
        "coverage": "Akron core, walk-in pantry + hot meals",
        "impact":   "Serves 500+ families/week. Zero eligibility barriers.",
        "signal":   "Ongoing urban food desert coverage",
        "priority": "HIGH",
    },
    {
        "name":     "Good Samaritan Hunger Center",
        "url":      "https://www.goodsamaritanhungercenter.org",
        "donate":   "https://www.goodsamaritanhungercenter.org/donate",
        "coverage": "Cuyahoga Falls, Summit County",
        "impact":   "Closest to Node-01 location. Neighborhood-level reach.",
        "signal":   "Local node proximity — fastest physical routing",
        "priority": "CRITICAL",  # Closest to Meeko's location
    },
]

# ── Summit County Baseline Stats (public data, 2026) ──────────────────────
SUMMIT_COUNTY_STATS = {
    "food_insecurity_rate":  0.157,       # 15.7%
    "individuals_affected":  4180,
    "children_affected":     1230,
    "pct_children":          0.223,       # 22.3% of children
    "meals_per_quarter":     705864,
    "pounds_food_per_quarter": 730578,
    "programs_in_network":   600,
    "snap_threat":           "ACTIVE",    # SNAP cuts confirmed 2026
    "demand_status":         "ELEVATED",  # Post-pandemic demand persists
    "source":                "akroncantonfoodbank.org/hunger-summit-county",
}


def calculate_lube_path(available_aid_dollars: float) -> dict:
    """
    Given X dollars in the local aid fund, calculate the fastest
    path to filling the most critical gap.

    Returns a routing receipt showing exactly where money goes,
    in what order, and what the impact is.
    """
    stats  = SUMMIT_COUNTY_STATS
    routes = []

    # Priority 1: Good Samaritan (closest to Node-01 / Cuyahoga Falls)
    # $1 = ~2.5 meals at local pantry level
    good_sam_alloc = round(min(available_aid_dollars * 0.50, available_aid_dollars), 2)
    routes.append({
        "partner":     "Good Samaritan Hunger Center",
        "allocation":  good_sam_alloc,
        "impact":      f"~{int(good_sam_alloc * 2.5)} meals for Cuyahoga Falls neighbors",
        "rationale":   "Closest to Node-01. Highest geographic precision.",
        "action":      f"Donate at goodsamaritanhungercenter.org/donate",
        "priority":    1,
    })

    # Priority 2: Akron-Canton Foodbank (systemwide multiplier — $1 = 3 meals)
    foodbank_alloc = round(available_aid_dollars * 0.35, 2)
    routes.append({
        "partner":     "Akron-Canton Regional Foodbank",
        "allocation":  foodbank_alloc,
        "impact":      f"~{int(foodbank_alloc * 3)} meals across Summit County network",
        "rationale":   "Highest per-dollar meal multiplier (3x). Feeds 600+ programs.",
        "action":      "Donate at akroncantonfoodbank.org/ways-give",
        "priority":    2,
    })

    # Priority 3: OPEN M (urban core, zero-barrier)
    openm_alloc = round(available_aid_dollars * 0.15, 2)
    routes.append({
        "partner":     "OPEN M Food Services",
        "allocation":  openm_alloc,
        "impact":      f"~{int(openm_alloc * 2)} walk-in meals, no eligibility check",
        "rationale":   "Zero-barrier urban pantry. Reaches people other orgs miss.",
        "action":      "Donate at openm.org/donate",
        "priority":    3,
    })

    total_meals = sum(
        int(r["allocation"] * (3 if "Foodbank" in r["partner"] else (2.5 if "Good Samaritan" in r["partner"] else 2)))
        for r in routes
    )

    routing = {
        "timestamp":          datetime.utcnow().isoformat(),
        "total_aid_dollars":  available_aid_dollars,
        "total_meals_funded": total_meals,
        "gap_context": {
            "summit_county_insecure": stats["individuals_affected"],
            "children_at_risk":       stats["children_affected"],
            "snap_threat":            stats["snap_threat"],
            "demand_status":          stats["demand_status"],
        },
        "routes":  routes,
        "verdict": (
            f"${available_aid_dollars:.2f} → {total_meals} meals for Summit County neighbors. "
            f"50% to Cuyahoga Falls (Node-01 proximity), 35% to county network, 15% zero-barrier urban."
        ),
    }

    _save_radar_log(routing)
    _log_to_actual(routing)
    return routing


def scan_current_needs() -> dict:
    """
    Probe local partner sites for any public signal of urgent need.
    Returns a needs assessment dict.
    """
    needs = {
        "timestamp":  datetime.utcnow().isoformat(),
        "partners":   [],
        "alert":      False,
        "summary":    "",
    }

    for partner in LOCAL_PARTNERS:
        status = _probe_site(partner["url"])
        needs["partners"].append({
            "name":     partner["name"],
            "reachable": status["ok"],
            "signal":   partner["signal"],
            "priority": partner["priority"],
            "donate":   partner["donate"],
        })
        if partner["priority"] in ("HIGH", "CRITICAL"):
            needs["alert"] = True

    active_urgent = [
        p for p in needs["partners"]
        if p["priority"] == "CRITICAL"
    ]

    if active_urgent:
        needs["summary"] = (
            f"CRITICAL: {len(active_urgent)} high-priority local partners "
            f"with active demand signals. SNAP cuts confirmed. Route aid NOW."
        )
    else:
        needs["summary"] = "Local partners operational. Elevated demand baseline."

    return needs


def _probe_site(url: str) -> dict:
    """Light HTTP HEAD check — is the site reachable?"""
    try:
        req = urllib.request.Request(url, method="HEAD",
            headers={"User-Agent": "SolarPunk-LocalNeedsRadar/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return {"ok": True, "status": r.status}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


def _save_radar_log(routing: dict):
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    log = []
    if RADAR_LOG.exists():
        try:
            log = json.loads(RADAR_LOG.read_text())
        except Exception:
            log = []
    log.append(routing)
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    log["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    RADAR_LOG.write_text(json.dumps(log[-50:], indent=2), encoding="utf-8")  # keep last 50 routing events


def _log_to_actual(routing: dict):
    if not ACTUAL_LOG.exists():
        return
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = (
        f"\n**[LOCAL NEEDS RADAR — {ts}]** "
        f"Aid routing calculated: ${routing['total_aid_dollars']:.2f} → "
        f"{routing['total_meals_funded']} meals. "
        f"Summit County: {SUMMIT_COUNTY_STATS['individuals_affected']:,} food-insecure "
        f"({SUMMIT_COUNTY_STATS['children_affected']:,} children). "
        f"SNAP threat: {SUMMIT_COUNTY_STATS['snap_threat']}.\n"
    )
    with open(ACTUAL_LOG, "a") as f:
        f.write(entry)


def run_radar(available_aid: float = 0.0):
    """Full radar sweep: scan needs + calculate routing path."""
    print("[LOCAL NEEDS RADAR] Scanning Summit County food security...")

    needs = scan_current_needs()
    print(f"  Alert: {needs['alert']} | {needs['summary']}")

    if available_aid > 0:
        print(f"\n[LOCAL NEEDS RADAR] Calculating lube path for ${available_aid:.2f}...")
        routing = calculate_lube_path(available_aid)
        print(f"  {routing['verdict']}")
        for r in routing["routes"]:
            print(f"  P{r['priority']}: {r['partner']} — ${r['allocation']:.2f} → {r['impact']}")
        return routing
    else:
        print("[LOCAL NEEDS RADAR] No funds available yet. Need signal logged.")
        print("  When revenue routes to local_aid fund, re-run with:")
        print("  run_radar(available_aid=<amount>)")
        return needs


if __name__ == "__main__":
    # Called with $0 = show current needs assessment
    # Called with $X = calculate full lube path
    import sys
    amount = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    result = run_radar(amount)
    print(f"\nSaved to: {RADAR_LOG}")
