#!/usr/bin/env python3
"""
REVENUE_SPLITTER.py -- The DUAL-MODE Revenue Router.

    Phase 1: Grow. Phase 2: Balance. Phase 3: Give.
    The mission never changes -- only the method.

This is the bridge between the two halves of SolarPunk's economy:

    The 1/99 system GROWS the machine.
    The 99/1 system GIVES to those who need it.

REVENUE_SPLITTER decides which system every dollar flows through,
based on what the organism needs RIGHT NOW.

PHASE 1 -- IGNITION (total revenue < $100):
    100% flows through 1/99 (grow the machine)
    BUT 1% of that 1/99 still goes to immediate aid (PCRF)
    This is survival mode. The organism must grow before it can give.

PHASE 2 -- COMBUSTION ($100 - $1000):
    50% flows through 1/99 (keep growing)
    50% flows through 99/1 (start giving)
    The organism is self-sustaining. Both halves activate.

PHASE 3 -- ORBIT ($1000+):
    10% flows through 1/99 (maintenance)
    90% flows through 99/1 (full giving mode)
    The machine is built. Now it serves its purpose.

Zero secrets needed. Zero paid APIs. Pure signal routing.
"""
import json
import time
import pathlib
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Phase thresholds -- hardcoded, non-negotiable
# ---------------------------------------------------------------------------
PHASE_THRESHOLDS = {
    "ignition":   {"min": 0.0,    "max": 100.0,   "label": "IGNITION",   "pct_1_99": 1.00, "pct_99_1": 0.00},
    "combustion": {"min": 100.0,  "max": 1000.0,  "label": "COMBUSTION", "pct_1_99": 0.50, "pct_99_1": 0.50},
    "orbit":      {"min": 1000.0, "max": float("inf"), "label": "ORBIT", "pct_1_99": 0.10, "pct_99_1": 0.90},
}

# ---------------------------------------------------------------------------
# The 1/99 routing table -- every growth dollar splits this way
# ---------------------------------------------------------------------------
ROUTES_1_99 = {
    "immediate_aid": {
        "pct": 0.01,
        "label": "Immediate Aid (PCRF)",
        "purpose": "1% reminder -- every growth dollar remembers why we build",
        "recipient": "Palestinian Children's Relief Fund (EIN: 93-1057665)",
    },
    "product_development": {
        "pct": 0.35,
        "label": "Product Development",
        "purpose": "New products, better products, more value per dollar",
    },
    "storefront_infra": {
        "pct": 0.25,
        "label": "Storefront Infrastructure",
        "purpose": "Ko-fi, Gumroad, domains, payment rails",
    },
    "marketing_growth": {
        "pct": 0.20,
        "label": "Marketing & Growth",
        "purpose": "SEO, social media, outreach, distribution",
    },
    "api_keys_tools": {
        "pct": 0.10,
        "label": "API Keys & Tools",
        "purpose": "Anthropic API, hosting, services",
    },
    "legal_runway": {
        "pct": 0.09,
        "label": "Legal Runway",
        "purpose": "DBA, trademark, LLC",
    },
}

# ---------------------------------------------------------------------------
# The 99/1 routing table -- every giving dollar splits this way
# ---------------------------------------------------------------------------
ROUTES_99_1 = {
    "mutual_aid": {
        "pct": 0.99,
        "label": "Mutual Aid (99%)",
        "sub_routes": {
            "pcrf":          {"pct": 0.60, "label": "PCRF", "recipient": "Palestinian Children's Relief Fund (EIN: 93-1057665)"},
            "irc":           {"pct": 0.15, "label": "IRC", "recipient": "International Rescue Committee"},
            "msf":           {"pct": 0.10, "label": "MSF", "recipient": "Doctors Without Borders"},
            "unicef":        {"pct": 0.10, "label": "UNICEF", "recipient": "United Nations Children's Fund"},
            "direct_relief": {"pct": 0.05, "label": "Direct Relief", "recipient": "Direct Relief"},
        },
    },
    "node_fuel": {
        "pct": 0.01,
        "label": "Node Fuel (1%)",
        "purpose": "Keep the lights on -- minimal maintenance cost",
    },
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _load(fname, fallback=None):
    f = DATA / fname
    if f.exists():
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            return d if isinstance(d, (dict, list)) else (fallback or {})
        except Exception:
            pass
    return fallback if fallback is not None else {}


def _save(fname, data):
    (DATA / fname).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _ts():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# revenue signal aggregation -- pull from ALL sources
# ---------------------------------------------------------------------------

def _gather_total_revenue():
    """Pull every revenue signal. Return total lifetime revenue."""
    economy   = _load("economy_chain_ledger.json", {})
    kofi      = _load("kofi_tracker_state.json", {})
    audit     = _load("revenue_audit.json", {})
    proof     = _load("proof_ledger.json", {})
    quick_rev = _load("quick_revenue.json", {})
    first_dol = _load("first_dollar_plan.json", {})

    # Take the max across all sources -- they may disagree, trust the highest
    total = max(
        float(economy.get("total_earned", 0)),
        float(kofi.get("total_verified", 0)),
        float(proof.get("total_sales", 0)),
        float(quick_rev.get("total_revenue", 0)),
        0.0,
    )

    return {
        "total_lifetime": total,
        "economy_earned": float(economy.get("total_earned", 0)),
        "economy_routed": float(economy.get("total_routed", 0)),
        "economy_cycles": economy.get("cycles", 0),
        "kofi_verified": float(kofi.get("total_verified", 0)),
        "kofi_alive": audit.get("kofi_alive", False),
        "gumroad_alive": audit.get("gumroad_alive", False),
        "loop_closed": economy.get("loop_closed", False),
        "first_dollar_earned": first_dol.get("first_dollar_earned", False),
    }


# ---------------------------------------------------------------------------
# phase determination
# ---------------------------------------------------------------------------

def _determine_phase(total_revenue):
    """Determine which phase the organism is in based on lifetime revenue."""
    if total_revenue >= PHASE_THRESHOLDS["orbit"]["min"]:
        return "orbit", PHASE_THRESHOLDS["orbit"]
    elif total_revenue >= PHASE_THRESHOLDS["combustion"]["min"]:
        return "combustion", PHASE_THRESHOLDS["combustion"]
    else:
        return "ignition", PHASE_THRESHOLDS["ignition"]


# ---------------------------------------------------------------------------
# the split -- where every penny goes
# ---------------------------------------------------------------------------

def _calculate_split(total_revenue, new_revenue, phase_key, phase):
    """Calculate the dual-mode split for new revenue.

    Returns a dict showing exactly where every penny routes.
    """
    pct_growth = phase["pct_1_99"]
    pct_giving = phase["pct_99_1"]

    growth_pool = round(new_revenue * pct_growth, 6)
    giving_pool = round(new_revenue * pct_giving, 6)

    # Route growth pool through 1/99
    growth_routes = {}
    for key, route in ROUTES_1_99.items():
        amount = round(growth_pool * route["pct"], 6)
        growth_routes[key] = {
            "amount": amount,
            "label": route["label"],
            "purpose": route.get("purpose", ""),
        }
        if "recipient" in route:
            growth_routes[key]["recipient"] = route["recipient"]

    # Route giving pool through 99/1
    giving_routes = {}
    mutual_aid_pool = round(giving_pool * ROUTES_99_1["mutual_aid"]["pct"], 6)
    node_fuel_amount = round(giving_pool * ROUTES_99_1["node_fuel"]["pct"], 6)

    # Sub-route the mutual aid pool
    aid_sub_routes = {}
    for key, sub in ROUTES_99_1["mutual_aid"]["sub_routes"].items():
        amount = round(mutual_aid_pool * sub["pct"], 6)
        aid_sub_routes[key] = {
            "amount": amount,
            "label": sub["label"],
            "recipient": sub["recipient"],
        }

    giving_routes["mutual_aid"] = {
        "amount": mutual_aid_pool,
        "label": ROUTES_99_1["mutual_aid"]["label"],
        "sub_routes": aid_sub_routes,
    }
    giving_routes["node_fuel"] = {
        "amount": node_fuel_amount,
        "label": ROUTES_99_1["node_fuel"]["label"],
        "purpose": ROUTES_99_1["node_fuel"]["purpose"],
    }

    # Total aid across BOTH systems
    # In 1/99: the 1% immediate aid goes to PCRF
    # In 99/1: the mutual aid sub-routes go to organizations
    total_to_aid = growth_routes.get("immediate_aid", {}).get("amount", 0)
    for sub in aid_sub_routes.values():
        total_to_aid = round(total_to_aid + sub["amount"], 6)

    return {
        "new_revenue": new_revenue,
        "phase": phase_key,
        "phase_label": phase["label"],
        "growth_pct": pct_growth,
        "giving_pct": pct_giving,
        "growth_pool": growth_pool,
        "giving_pool": giving_pool,
        "growth_routes": growth_routes,
        "giving_routes": giving_routes,
        "total_to_aid": total_to_aid,
        "total_to_growth": round(growth_pool - growth_routes.get("immediate_aid", {}).get("amount", 0), 6),
        "total_to_node": node_fuel_amount,
    }


# ---------------------------------------------------------------------------
# accumulate lifetime routing totals
# ---------------------------------------------------------------------------

def _accumulate(state, split):
    """Add this cycle's split into the running totals."""
    default_lifetime = {
        "total_through_1_99": 0.0,
        "total_through_99_1": 0.0,
        "total_to_aid": 0.0,
        "total_to_growth": 0.0,
        "growth_routes": {k: 0.0 for k in ROUTES_1_99},
        "aid_routes": {k: 0.0 for k in ROUTES_99_1["mutual_aid"]["sub_routes"]},
        "node_fuel": 0.0,
    }
    lifetime = state.get("lifetime_routing") or default_lifetime

    lifetime["total_through_1_99"] = round(
        lifetime["total_through_1_99"] + split["growth_pool"], 6
    )
    lifetime["total_through_99_1"] = round(
        lifetime["total_through_99_1"] + split["giving_pool"], 6
    )
    lifetime["total_to_aid"] = round(
        lifetime["total_to_aid"] + split["total_to_aid"], 6
    )
    lifetime["total_to_growth"] = round(
        lifetime["total_to_growth"] + split["total_to_growth"], 6
    )

    # Accumulate growth sub-routes
    for key, route in split["growth_routes"].items():
        prev = lifetime["growth_routes"].get(key, 0.0)
        lifetime["growth_routes"][key] = round(prev + route["amount"], 6)

    # Accumulate aid sub-routes
    aid_subs = split["giving_routes"].get("mutual_aid", {}).get("sub_routes", {})
    for key, sub in aid_subs.items():
        prev = lifetime["aid_routes"].get(key, 0.0)
        lifetime["aid_routes"][key] = round(prev + sub["amount"], 6)

    # Node fuel
    lifetime["node_fuel"] = round(
        lifetime["node_fuel"] + split["giving_routes"].get("node_fuel", {}).get("amount", 0), 6
    )

    return lifetime


# ---------------------------------------------------------------------------
# build the simplified active routing table
# ---------------------------------------------------------------------------

def _build_active_routing(phase_key, phase, total_revenue):
    """Build the simplified routing table showing current active percentages."""
    pct_growth = phase["pct_1_99"]
    pct_giving = phase["pct_99_1"]

    routes = []

    # 1/99 routes (growth side)
    for key, route in ROUTES_1_99.items():
        effective_pct = round(pct_growth * route["pct"], 6)
        entry = {
            "system": "1/99",
            "route": key,
            "label": route["label"],
            "effective_pct": effective_pct,
            "effective_pct_display": "%.2f%%" % (effective_pct * 100),
            "purpose": route.get("purpose", ""),
        }
        if "recipient" in route:
            entry["recipient"] = route["recipient"]
        routes.append(entry)

    # 99/1 routes (giving side)
    mutual_aid_pct = pct_giving * ROUTES_99_1["mutual_aid"]["pct"]
    for key, sub in ROUTES_99_1["mutual_aid"]["sub_routes"].items():
        effective_pct = round(mutual_aid_pct * sub["pct"], 6)
        routes.append({
            "system": "99/1",
            "route": "mutual_aid_%s" % key,
            "label": "%s (Mutual Aid)" % sub["label"],
            "effective_pct": effective_pct,
            "effective_pct_display": "%.2f%%" % (effective_pct * 100),
            "recipient": sub["recipient"],
        })

    node_pct = round(pct_giving * ROUTES_99_1["node_fuel"]["pct"], 6)
    routes.append({
        "system": "99/1",
        "route": "node_fuel",
        "label": ROUTES_99_1["node_fuel"]["label"],
        "effective_pct": node_pct,
        "effective_pct_display": "%.2f%%" % (node_pct * 100),
        "purpose": ROUTES_99_1["node_fuel"]["purpose"],
    })

    # Verification: all percentages should sum to ~1.0
    total_pct = round(sum(r["effective_pct"] for r in routes), 6)

    return {
        "generated_at": _ts(),
        "engine": "REVENUE_SPLITTER",
        "phase": phase_key,
        "phase_label": phase["label"],
        "total_revenue": total_revenue,
        "growth_system_pct": pct_growth,
        "giving_system_pct": pct_giving,
        "routes": routes,
        "verification_total_pct": total_pct,
        "mantra": "Phase 1: Grow. Phase 2: Balance. Phase 3: Give. The mission never changes -- only the method.",
    }


# ---------------------------------------------------------------------------
# phase transition detection
# ---------------------------------------------------------------------------

def _check_phase_transition(state, current_phase):
    """Detect if we just crossed a phase boundary."""
    prev_phase = state.get("current_phase", "ignition")
    if current_phase != prev_phase:
        return {
            "transitioned": True,
            "from": prev_phase,
            "to": current_phase,
            "from_label": PHASE_THRESHOLDS[prev_phase]["label"],
            "to_label": PHASE_THRESHOLDS[current_phase]["label"],
            "ts": _ts(),
        }
    return {"transitioned": False}


# ---------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------

def run():
    print("=" * 60)
    print("REVENUE SPLITTER -- The Dual-Mode Revenue Router")
    print("=" * 60)
    print()
    print("  Phase 1: Grow. Phase 2: Balance. Phase 3: Give.")
    print("  The mission never changes -- only the method.")
    print()

    # 1. Gather revenue from all sources
    signals = _gather_total_revenue()
    total_revenue = signals["total_lifetime"]

    print("[signals] Lifetime revenue: $%.2f" % total_revenue)
    print("[signals] Economy earned: $%.2f | Ko-fi verified: $%.2f" % (
        signals["economy_earned"], signals["kofi_verified"],
    ))
    print("[signals] Ko-fi: %s | Gumroad: %s | Loop closed: %s" % (
        "ALIVE" if signals["kofi_alive"] else "DEAD",
        "ALIVE" if signals["gumroad_alive"] else "DEAD",
        "YES" if signals["loop_closed"] else "NO",
    ))

    # 2. Determine current phase
    phase_key, phase = _determine_phase(total_revenue)
    print()
    print("[phase] Current: %s" % phase["label"])
    print("  1/99 (growth):  %d%%" % int(phase["pct_1_99"] * 100))
    print("  99/1 (giving):  %d%%" % int(phase["pct_99_1"] * 100))

    if phase_key == "ignition":
        print("  Status: Survival mode. Growing the machine.")
        print("  Next threshold: $%.0f -> COMBUSTION" % PHASE_THRESHOLDS["combustion"]["min"])
        remaining = PHASE_THRESHOLDS["combustion"]["min"] - total_revenue
        print("  Distance: $%.2f to go" % remaining)
    elif phase_key == "combustion":
        print("  Status: Self-sustaining. Both halves active.")
        print("  Next threshold: $%.0f -> ORBIT" % PHASE_THRESHOLDS["orbit"]["min"])
        remaining = PHASE_THRESHOLDS["orbit"]["min"] - total_revenue
        print("  Distance: $%.2f to go" % remaining)
    else:
        print("  Status: FULL GIVING MODE. The machine serves its purpose.")

    # 3. Load or init state
    state = _load("revenue_splitter_state.json", {
        "engine": "REVENUE_SPLITTER",
        "created_at": _ts(),
        "current_phase": "ignition",
        "total_revenue_routed": 0.0,
        "lifetime_routing": None,
        "cycles": 0,
        "phase_transitions": [],
    })

    # 4. Check for phase transition
    transition = _check_phase_transition(state, phase_key)
    if transition["transitioned"]:
        print()
        print("  *** PHASE TRANSITION: %s -> %s ***" % (
            transition["from_label"], transition["to_label"],
        ))
        transitions = state.get("phase_transitions", [])
        transitions.append(transition)
        state["phase_transitions"] = transitions[-20:]

    # 5. Calculate the split for new revenue
    previously_routed = state.get("total_revenue_routed", 0.0)
    new_revenue = round(total_revenue - previously_routed, 6)
    new_revenue = max(new_revenue, 0.0)

    split = _calculate_split(total_revenue, new_revenue, phase_key, phase)

    print()
    if new_revenue > 0:
        print("[split] New revenue this cycle: $%.4f" % new_revenue)
        print("  -> 1/99 (growth): $%.4f (%.0f%%)" % (split["growth_pool"], phase["pct_1_99"] * 100))
        print("  -> 99/1 (giving): $%.4f (%.0f%%)" % (split["giving_pool"], phase["pct_99_1"] * 100))

        print()
        print("  [1/99 GROWTH ROUTES]")
        for key, route in split["growth_routes"].items():
            pct = int(ROUTES_1_99[key]["pct"] * 100)
            print("    %s (%d%%): $%.6f" % (route["label"], pct, route["amount"]))

        if split["giving_pool"] > 0:
            print()
            print("  [99/1 GIVING ROUTES]")
            aid_subs = split["giving_routes"]["mutual_aid"]["sub_routes"]
            for key, sub in aid_subs.items():
                org_pct = int(ROUTES_99_1["mutual_aid"]["sub_routes"][key]["pct"] * 100)
                print("    %s (%d%% of aid): $%.6f -> %s" % (
                    sub["label"], org_pct, sub["amount"], sub["recipient"],
                ))
            nf = split["giving_routes"]["node_fuel"]
            print("    %s: $%.6f" % (nf["label"], nf["amount"]))

        print()
        print("  Total to aid (both systems): $%.6f" % split["total_to_aid"])
        print("  Total to growth:             $%.6f" % split["total_to_growth"])
    else:
        print("[split] No new revenue to route. Standing by.")
        print("  The machine is built and waiting for fuel.")

    # 6. Accumulate lifetime totals
    lifetime = _accumulate(state, split)
    state["lifetime_routing"] = lifetime

    # 7. Update state
    state["current_phase"] = phase_key
    state["total_revenue_routed"] = round(previously_routed + new_revenue, 6)
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = _ts()
    state["last_split"] = {
        "new_revenue": new_revenue,
        "phase": phase_key,
        "growth_pool": split["growth_pool"],
        "giving_pool": split["giving_pool"],
        "total_to_aid": split["total_to_aid"],
        "ts": _ts(),
    }
    state["signals_snapshot"] = signals
    state["mantra"] = "Phase 1: Grow. Phase 2: Balance. Phase 3: Give. The mission never changes -- only the method."

    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    _save("revenue_splitter_state.json", state)
    print()
    print("[write] data/revenue_splitter_state.json")

    # 8. Build and save the active routing table
    active_routing = _build_active_routing(phase_key, phase, total_revenue)
    _save("revenue_routing.json", active_routing)
    print("[write] data/revenue_routing.json")

    # 9. Print the dual-system report
    print()
    print("=" * 60)
    print("DUAL-SYSTEM ROUTING REPORT")
    print("=" * 60)
    print()
    print("  Phase:           %s" % phase["label"])
    print("  Total revenue:   $%.2f" % total_revenue)
    print("  Total routed:    $%.6f" % state["total_revenue_routed"])
    print()
    print("  --- Lifetime through 1/99 (GROWTH) ---")
    print("  Total:           $%.6f" % lifetime["total_through_1_99"])
    for key in ROUTES_1_99:
        val = lifetime["growth_routes"].get(key, 0)
        print("    %-22s $%.6f" % (ROUTES_1_99[key]["label"] + ":", val))
    print()
    print("  --- Lifetime through 99/1 (GIVING) ---")
    print("  Total:           $%.6f" % lifetime["total_through_99_1"])
    for key in ROUTES_99_1["mutual_aid"]["sub_routes"]:
        sub = ROUTES_99_1["mutual_aid"]["sub_routes"][key]
        val = lifetime["aid_routes"].get(key, 0)
        print("    %-22s $%.6f  -> %s" % (sub["label"] + ":", val, sub["recipient"]))
    print("    %-22s $%.6f" % ("Node Fuel:", lifetime["node_fuel"]))
    print()
    print("  --- COMBINED AID TOTAL ---")
    print("  All aid (both systems): $%.6f" % lifetime["total_to_aid"])
    print()

    # Active routing table summary
    print("  --- ACTIVE ROUTING TABLE (effective %) ---")
    for r in active_routing["routes"]:
        system_tag = "[1/99]" if r["system"] == "1/99" else "[99/1]"
        print("    %s %-6s %-30s %s" % (
            system_tag, r["effective_pct_display"], r["label"],
            r.get("recipient", r.get("purpose", "")),
        ))
    print()
    print("  Verification: %.2f%% of every dollar accounted for" % (
        active_routing["verification_total_pct"] * 100,
    ))
    print()

    # Phase roadmap
    print("  --- PHASE ROADMAP ---")
    for pkey, pval in PHASE_THRESHOLDS.items():
        marker = " <-- YOU ARE HERE" if pkey == phase_key else ""
        max_display = "inf" if pval["max"] == float("inf") else "$%.0f" % pval["max"]
        print("    %-12s $%.0f - %-8s  1/99: %d%%  99/1: %d%%%s" % (
            pval["label"],
            pval["min"],
            max_display,
            int(pval["pct_1_99"] * 100),
            int(pval["pct_99_1"] * 100),
            marker,
        ))

    print()
    print("=" * 60)
    print("  Phase 1: Grow. Phase 2: Balance. Phase 3: Give.")
    print("  The mission never changes -- only the method.")
    print("  PCRF EIN: 93-1057665")
    print("=" * 60)

    return {
        "engine": "REVENUE_SPLITTER",
        "phase": phase_key,
        "phase_label": phase["label"],
        "total_revenue": total_revenue,
        "new_revenue": new_revenue,
        "growth_pool": split["growth_pool"],
        "giving_pool": split["giving_pool"],
        "total_to_aid": split["total_to_aid"],
        "lifetime_aid": lifetime["total_to_aid"],
        "phase_transitioned": transition["transitioned"],
        "cycles": state["cycles"],
        "ts": _ts(),
    }


if __name__ == "__main__":
    run()
