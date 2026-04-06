#!/usr/bin/env python3
"""
OSMOSIS_ROUTER.py — Help Flows Toward Information Voids (Molecular Pattern)
=============================================================================
NATURE'S BLUEPRINT: Osmosis.

Water doesn't need a pump. It flows naturally from HIGH concentration
to LOW concentration through a membrane. No energy required.
The gradient IS the force.

SolarPunk applies osmosis to information distribution:

  HELP FLOWS TOWARD INFORMATION VOIDS.

  If a region has HIGH signal volume (Gaza, Sudan) — that's the
  "high concentration" side. Lots of data, lots of coverage.

  If a region has LOW signal volume (Tigray, Rohingya, Haiti) —
  that's the "low concentration" side. Information void. Under-covered.

  Osmosis Router identifies the VOIDS and PUSHES resources there:
    1. Measure signal density per region
    2. Identify under-covered crises (low signals despite known conflict)
    3. Route amplification energy toward the voids
    4. Generate "attention debt" scores — how much the world owes in coverage

  The membrane is SolarPunk itself. The gradient is suffering.
  The flow is automatic.

  "Water doesn't ask where to go. It flows where it's needed." — SolarPunk

Reads: data/crisis_signals.json, data/quorum_state.json,
       data/bioluminescence.json
Writes: data/osmosis_routing.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

OSMOSIS_FILE = DATA / "osmosis_routing.json"
CRISIS_FILE = DATA / "crisis_signals.json"
QUORUM_FILE = DATA / "quorum_state.json"
BIO_FILE = DATA / "bioluminescence.json"

# Known conflict zones with expected minimum signal volume
# If signals are below expected, that's an information void
EXPECTED_SIGNALS = {
    "gaza": {"min_expected": 8, "known_crisis": True, "conflict_type": "bombardment/siege"},
    "palestine": {"min_expected": 5, "known_crisis": True, "conflict_type": "occupation"},
    "sudan": {"min_expected": 6, "known_crisis": True, "conflict_type": "civil war"},
    "darfur": {"min_expected": 4, "known_crisis": True, "conflict_type": "genocide"},
    "congo": {"min_expected": 3, "known_crisis": True, "conflict_type": "armed conflict"},
    "drc": {"min_expected": 3, "known_crisis": True, "conflict_type": "armed conflict"},
    "yemen": {"min_expected": 4, "known_crisis": True, "conflict_type": "civil war/famine"},
    "myanmar": {"min_expected": 3, "known_crisis": True, "conflict_type": "military coup"},
    "uyghur": {"min_expected": 2, "known_crisis": True, "conflict_type": "cultural genocide"},
    "xinjiang": {"min_expected": 2, "known_crisis": True, "conflict_type": "detention camps"},
    "tigray": {"min_expected": 2, "known_crisis": True, "conflict_type": "civil war"},
    "ethiopia": {"min_expected": 3, "known_crisis": True, "conflict_type": "civil conflict"},
    "syria": {"min_expected": 3, "known_crisis": True, "conflict_type": "civil war"},
    "ukraine": {"min_expected": 5, "known_crisis": True, "conflict_type": "invasion"},
    "haiti": {"min_expected": 2, "known_crisis": True, "conflict_type": "gang violence/collapse"},
    "somalia": {"min_expected": 3, "known_crisis": True, "conflict_type": "al-Shabaab/famine"},
    "rohingya": {"min_expected": 2, "known_crisis": True, "conflict_type": "genocide/displacement"},
    "afghanistan": {"min_expected": 3, "known_crisis": True, "conflict_type": "Taliban/women's rights"},
    "west bank": {"min_expected": 4, "known_crisis": True, "conflict_type": "settler violence/occupation"},
}


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def count_signals_by_region(signals):
    counts = {}
    for s in signals:
        text = (s.get("title", "") + " " + json.dumps(s.get("countries", []))).lower()
        for region in EXPECTED_SIGNALS:
            if region in text:
                counts[region] = counts.get(region, 0) + 1
    return counts


def calculate_attention_debt(signal_counts):
    """Calculate 'attention debt' — how much coverage each crisis SHOULD have vs DOES have."""
    debts = []

    for region, expected in EXPECTED_SIGNALS.items():
        actual = signal_counts.get(region, 0)
        min_exp = expected["min_expected"]

        if actual < min_exp:
            deficit = min_exp - actual
            debt_ratio = deficit / max(min_exp, 1)  # 0.0 to 1.0

            debts.append({
                "region": region,
                "conflict_type": expected["conflict_type"],
                "expected_signals": min_exp,
                "actual_signals": actual,
                "deficit": deficit,
                "debt_ratio": round(debt_ratio, 2),
                "attention_debt": round(debt_ratio * 100),  # 0-100 score
                "verdict": "CRITICAL VOID" if debt_ratio >= 0.8 else
                          "SIGNIFICANT VOID" if debt_ratio >= 0.5 else
                          "MODERATE VOID" if debt_ratio >= 0.3 else "MINOR VOID",
            })

    debts.sort(key=lambda x: -x["debt_ratio"])
    return debts


def generate_routing_directives(debts, signal_counts):
    """Generate routing directives — push amplification energy toward voids."""
    directives = []

    for debt in debts:
        if debt["debt_ratio"] < 0.3:
            continue  # Minor voids don't need active routing

        region = debt["region"]
        severity = debt["verdict"]

        directive = {
            "region": region,
            "severity": severity,
            "attention_debt": debt["attention_debt"],
            "conflict_type": debt["conflict_type"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actions": [],
        }

        if debt["debt_ratio"] >= 0.8:
            # CRITICAL VOID — maximum routing
            directive["actions"] = [
                {
                    "type": "AMPLIFY",
                    "message": f"UNDER-COVERED CRISIS: {region.title()} ({debt['conflict_type']}). "
                               f"Only {debt['actual_signals']} signals detected vs {debt['expected_signals']} expected. "
                               f"This crisis needs MORE coverage. Share. Amplify. Don't let them be forgotten.",
                    "priority": "HIGH",
                },
                {
                    "type": "SEARCH",
                    "note": f"Actively search for more data about {region}",
                    "targets": ["wikipedia", "reddit", "gdelt"],
                },
                {
                    "type": "RESOURCE_KIT",
                    "note": f"Ensure survival kits are prepared for {region}-relevant crisis type",
                },
            ]
        elif debt["debt_ratio"] >= 0.5:
            directive["actions"] = [
                {
                    "type": "AMPLIFY",
                    "message": f"Under-covered: {region.title()} ({debt['conflict_type']}). "
                               f"Signal deficit: {debt['deficit']} below baseline.",
                    "priority": "MEDIUM",
                },
            ]
        else:
            directive["actions"] = [
                {"type": "MONITOR", "note": f"Watch {region} for further signal drops"},
            ]

        directives.append(directive)

    return directives


def calculate_coverage_equity():
    """How equitably is the world's attention distributed across crises?"""
    crisis = load_json(CRISIS_FILE)
    signals = crisis.get("signals", [])
    counts = count_signals_by_region(signals)

    total = sum(counts.values()) if counts else 1
    region_shares = {}
    for region in EXPECTED_SIGNALS:
        share = counts.get(region, 0) / max(total, 1)
        region_shares[region] = round(share * 100, 1)

    # Gini coefficient of attention (0 = perfectly equal, 1 = all attention on one crisis)
    shares = sorted(region_shares.values())
    n = len(shares)
    if n == 0 or sum(shares) == 0:
        gini = 0
    else:
        cum_shares = [sum(shares[:i+1]) for i in range(n)]
        gini = round(1 - (2 * sum(cum_shares)) / (n * sum(shares)) + 1/n, 3)

    return {
        "region_shares": region_shares,
        "gini_coefficient": gini,
        "interpretation": "highly unequal" if gini > 0.5 else "moderately unequal" if gini > 0.3 else "relatively equal",
        "most_covered": max(region_shares, key=region_shares.get) if region_shares else "none",
        "least_covered": min(region_shares, key=region_shares.get) if region_shares else "none",
    }


def main():
    print("OSMOSIS_ROUTER — Help flows toward information voids (molecular pattern)...")
    print("  'Water doesn't ask where to go. It flows where it's needed.'")

    crisis = load_json(CRISIS_FILE)
    signals = crisis.get("signals", [])
    counts = count_signals_by_region(signals)

    print(f"\n  Signal distribution across {len(EXPECTED_SIGNALS)} conflict zones:")
    for region in sorted(counts, key=counts.get, reverse=True):
        exp = EXPECTED_SIGNALS.get(region, {}).get("min_expected", "?")
        status = "OK" if counts[region] >= exp else "VOID"
        print(f"    {region}: {counts[region]} signals (expected >= {exp}) [{status}]")

    # Calculate attention debt
    print("\n  Calculating attention debt...")
    debts = calculate_attention_debt(counts)

    voids = [d for d in debts if d["debt_ratio"] >= 0.3]
    if voids:
        print(f"\n  INFORMATION VOIDS DETECTED: {len(voids)}")
        for d in voids[:10]:
            print(f"    [{d['verdict']}] {d['region']}: "
                  f"debt={d['attention_debt']}% | "
                  f"actual={d['actual_signals']}/{d['expected_signals']} | "
                  f"{d['conflict_type']}")

    # Generate routing directives
    directives = generate_routing_directives(debts, counts)

    # Coverage equity
    equity = calculate_coverage_equity()
    print(f"\n  Coverage equity (Gini): {equity['gini_coefficient']} ({equity['interpretation']})")
    print(f"  Most covered: {equity['most_covered']} | Least covered: {equity['least_covered']}")

    # Save
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "pattern": "osmosis",
        "philosophy": "Help flows from high concentration to low. The gradient is suffering.",
        "signal_counts": counts,
        "attention_debts": debts,
        "information_voids": voids,
        "routing_directives": directives,
        "coverage_equity": equity,
        "stats": {
            "regions_monitored": len(EXPECTED_SIGNALS),
            "voids_detected": len(voids),
            "critical_voids": len([d for d in debts if d.get("verdict") == "CRITICAL VOID"]),
            "directives_generated": len(directives),
        },
    }
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    output["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    OSMOSIS_FILE.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"\n  {len(directives)} routing directives generated")
    print("OSMOSIS_ROUTER done.")


if __name__ == "__main__":
    main()
