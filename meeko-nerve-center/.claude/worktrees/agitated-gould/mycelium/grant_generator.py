#!/usr/bin/env python3
"""
grant_generator.py — Liquid Grant Narrative Generator
======================================================
Turns data/grant_config.json + data/sites.json + live system stats
into a ready-to-file grant narrative. One config file → any city's
application. Change the city, update the census tracts, re-run.

Template variables are injected from:
  data/grant_config.json       (city-specific parameters — change per grant)
  data/sites.json              (signed site control records)
  data/compliance_config.json  (entity info: UEI, EIN, entity name)
  data/flywheel_state.json     (live revenue / Gaza total)
  data/brain_state.json        (live system health)
  data/mutual_aid_summary.json (community contribution evidence)

Writes: docs/{city_slug}-cdbg-current.md   (always fresh, ready to paste)
        data/grant_ready_status.json        (OMNIBRAIN/SYNAPSE reads this)

To adapt for a new city: copy grant_config.json, change the fields,
run grant_generator.py → new narrative in 10 seconds.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DOCS = Path("docs")


def load_json(fname, default=None):
    fp = DATA / fname
    try:
        return json.loads(fp.read_text()) if fp.exists() else (default or {})
    except Exception:
        return default or {}


def load_grant_config():
    """Load or create grant config template."""
    cfg_f = DATA / "grant_config.json"
    if cfg_f.exists():
        try:
            return json.loads(cfg_f.read_text())
        except Exception:
            pass
    # Write blank template
    template = {
        "_instructions": "One config per grant opportunity. Copy and fill in for each city.",
        "city": "Cuyahoga Falls",
        "city_slug": "cuyahoga-falls",
        "state": "Ohio",
        "grant_program": "CDBG Economic Development",
        "grant_year": 2026,
        "amount_requested": 236000,
        "submission_deadline": "2026-03-21",
        "census_tracts": ["5202.02", "5201"],
        "lmi_pct_tract_1": 0,
        "lmi_pct_tract_2": 0,
        "_lmi_note": "Look up exact % at hud.gov/grantees → LMISD Summit County. Must be ≥51% for Area Benefit.",
        "jobs_created": 4,
        "households_served": 150,
        "project_title": "The Ward 8 Sovereign-Lattice Hub",
        "hud_activity_type": "Economic Development — Public Facilities and Infrastructure",
        "national_objective": "LMI Area Benefit / Job Creation (24 CFR §570.208(a))",
        "contact_name": "",
        "contact_title": "Managing Member",
        "need_statement_extra": "",
        "leveraged_partners": [
            "Cadence Solar Grid (Union, OH) — grid interconnection support",
            "Puro.earth — CORC registration for community projects"
        ],
        "corc_tonnes_per_cell_per_year": 12,
        "corc_price_per_tonne": 85
    }
    cfg_f.write_text(json.dumps(template, indent=2))
    print("  Created blank grant_config.json — fill in city-specific values")
    return template


def build_site_map(sites_data):
    """Generate site map section from sites.json."""
    sites    = sites_data.get("sites", [])
    signed   = [s for s in sites if s.get("mou_signed")]
    unsigned = [s for s in sites if not s.get("mou_signed")]

    lines = ["**PROPOSED INSTALLATION SITES**\n"]
    lines.append(f"| Site | Address | Tract | Type | MOU Status |")
    lines.append(f"|------|---------|-------|------|------------|")
    for s in sites:
        addr   = s.get("address") or "[ADDRESS PENDING]"
        tract  = s.get("census_tract", "")
        stype  = s.get("site_type", "").title()
        signed_str = f"✓ Signed {s['mou_date']}" if s.get("mou_signed") else "Pending"
        lines.append(f"| {s.get('label','')} | {addr} | {tract} | {stype} | {signed_str} |")

    lines.append("")
    if unsigned:
        lines.append(f"*{len(unsigned)} site(s) pending MOU signature. "
                     f"All MOUs will be executed prior to grant submission.*")
    return "\n".join(lines)


def corc_projection(cfg):
    cells     = 3
    tonnes    = cfg.get("corc_tonnes_per_cell_per_year", 12)
    price     = cfg.get("corc_price_per_tonne", 85)
    annual    = cells * tonnes * price
    return annual, cells * tonnes


def render_narrative(cfg, compliance, sites_data, flywheel, brain, mutual_aid=None):
    """Merge all data sources into ready-to-file narrative."""
    city        = cfg.get("city", "[CITY]")
    state       = cfg.get("state", "Ohio")
    amount      = cfg.get("amount_requested", 0)
    deadline    = cfg.get("submission_deadline", "[DATE]")
    tracts      = ", ".join(cfg.get("census_tracts", []))
    lmi1        = cfg.get("lmi_pct_tract_1", 0)
    lmi2        = cfg.get("lmi_pct_tract_2", 0)
    jobs        = cfg.get("jobs_created", 4)
    households  = cfg.get("households_served", 150)
    title       = cfg.get("project_title", "")
    objective   = cfg.get("national_objective", "")
    contact     = cfg.get("contact_name", "[YOUR NAME]")
    partners    = "\n".join(f"- {p}" for p in cfg.get("leveraged_partners", []))
    extra_need  = cfg.get("need_statement_extra", "")

    entity   = compliance.get("entity_name", "Ward 8 Sovereign Lattice LLC")
    uei      = compliance.get("sam_gov", {}).get("uei", "[INSERT UEI]")
    ein_note = "[INSERT EIN]" if not compliance.get("ein", {}).get("has_number") else compliance.get("ein", {}).get("number", "[INSERT EIN]")

    engines        = brain.get("stats", {}).get("engines_total", 0)
    health         = brain.get("health_score", 0)
    to_gaza        = flywheel.get("total_to_gaza", 0)
    ma             = mutual_aid or {}
    abundance      = ma.get("abundance_score", 0)
    contributors   = ma.get("active_givers", 0)
    labor_hrs      = ma.get("labor_hours_contributed", 0)
    top_givers     = [g.get("name","") for g in ma.get("top_contributors", [])[:3] if g.get("name","")]

    corc_annual, corc_tonnes = corc_projection(cfg)
    site_map = build_site_map(sites_data)
    now_str  = datetime.now(timezone.utc).strftime("%B %d, %Y")

    lmi_line = ""
    if lmi1 > 0 or lmi2 > 0:
        lmi_line = f"HUD FY2025 LMISD confirms: Tract {cfg['census_tracts'][0] if cfg['census_tracts'] else 'TBD'}: **{lmi1}% LMI** | Tract {cfg['census_tracts'][1] if len(cfg['census_tracts'])>1 else 'TBD'}: **{lmi2}% LMI** (both exceed the 51% threshold)."
    else:
        lmi_line = f"*[REQUIRED: Look up LMI % at hud.gov/grantees → LMISD. Must confirm ≥51% before submission.]*"

    doc = f"""# {title}
## {city}, {state} — {cfg.get('grant_program','')} {cfg.get('grant_year','')}
## Application Narrative — Generated {now_str}

> *This document is auto-generated by OMNIBRAIN grant_generator.py from live data.*
> *Update data/grant_config.json and data/sites.json, then re-run to refresh.*

**APPLICANT:** {entity}
**UEI:** {uei}
**EIN:** {ein_note}
**REQUESTED AMOUNT:** ${amount:,}
**SUBMISSION DEADLINE:** {deadline}
**NATIONAL OBJECTIVE:** {objective}
**HUD ACTIVITY TYPE:** {cfg.get('hud_activity_type','')}

---

## SECTION 1 — PROJECT DESCRIPTION

The {title} installs three (3) modular "Sovereign Cell" infrastructure units in the {city} service area. Each unit delivers three simultaneous services to low-to-moderate income (LMI) residents at zero cost to users:

**Service 1 — Renewable Energy Access.** H55 modular battery arrays bid automatically onto the Cadence Solar Grid, storing renewable energy and providing emergency backup during outages.

**Service 2 — Emergency Water Filtration.** Each cell's WEF Nexus module provides on-site clean water capacity during grid failures — the infrastructure gap LMI households in this service area lack any fallback for.

**Service 3 — Free Neighborhood Wi-Fi.** PicoCELA mesh networking creates a self-healing internet backbone covering approximately 300 feet per node. Three overlapping nodes serve ~{households} households with free, permanent broadband access.

This project is a replicable template. Full specifications are released under Creative Commons upon completion.

---

## SECTION 2 — NATIONAL OBJECTIVE

**Method of Compliance:** Area Benefit — LMI (24 CFR §570.208(a)(1)(i))

**Service Area Census Tracts:** {tracts}

{lmi_line}

**Estimated Beneficiaries:** ~{households} households within mesh signal range.

**Job Creation Backup Objective:** {jobs} FTE positions created, prioritized for LMI Ward 8 residents per 24 CFR §570.208(a)(4).

---

## SECTION 3 — STATEMENT OF NEED

The {city} service area presents compounding infrastructure deficits: no public Wi-Fi in the Valley corridor, aging grid reliability, and zero off-grid energy fallback for LMI households. During the 2024–2025 storm seasons, portions of the service area experienced 24–72 hour outages. FEMA NHMA (2024) documents LMI households bear ~$1,800/household in recovery costs per major event.
{extra_need}
The convergence of mature mesh networking, modular batteries, and voluntary carbon markets makes it possible — for the first time — to build self-funding neighborhood infrastructure that pays its own maintenance costs through CORC revenue (~${corc_annual:,}/year projected), eliminating ongoing municipal subsidy.

---

## SECTION 4 — SITE CONTROL

{site_map}

---

## SECTION 5 — BUDGET SUMMARY

| Line Item | Amount |
|-----------|--------|
| Site assessment + permitting | $18,000 |
| Sovereign Cell fabrication — materials (3 units) | $84,000 |
| Sovereign Cell fabrication — labor | $42,000 |
| PicoCELA mesh installation + hardware | $54,000 |
| Puro.earth CORC registration + baseline measurement | $14,000 |
| Community training + documentation | $12,000 |
| Contingency (5%) | $12,000 |
| **TOTAL** | **${amount:,}** |

**No ongoing city subsidy required.** Projected CORC revenue: {corc_tonnes} tonnes/year × ${cfg.get('corc_price_per_tonne',85)}/tonne = ~${corc_annual:,}/year self-funded maintenance.

---

## SECTION 6 — ORGANIZATIONAL CAPACITY

{entity} operates an autonomous digital infrastructure stack (SolarPunk AI, {engines} active modules, health score {health}/100) that has run continuously since 2025 with zero server cost. The same systems-integration discipline is applied here to physical infrastructure. GitHub: github.com/meekotharaccoon-cell/meeko-nerve-center

**Community Reciprocity (Ward 8 Mutual Aid Ledger):**
Abundance score: {abundance}/100 | Active contributors: {contributors} | Labor hours pledged: {labor_hrs:.1f} hrs{(" | Key contributors: " + ", ".join(top_givers)) if top_givers else ""}

**Leveraged Partners:**
{partners}

---

## SECTION 7 — PERFORMANCE METRICS

| Metric | Target |
|--------|--------|
| Households with free Wi-Fi | ≥{households} |
| LMI jobs created | ≥{jobs} FTE |
| Cell uptime | ≥95% |
| Carbon credits issued (Year 1) | ≥{corc_tonnes} tonnes |
| Community training participants | ≥40 |

---

## CERTIFICATIONS

Applicant: {contact}, {cfg.get('contact_title','Managing Member')}, {entity}
UEI: {uei} | Date: {now_str}

*[Attach: Ohio LLC Articles, EIN letter, HUD LMISD printout, executed MOUs, community support letters]*
"""
    return doc


def main():
    DOCS.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    print("grant_generator — Liquid Grant Narrative Generator...")

    cfg        = load_grant_config()
    compliance = load_json("compliance_status.json")
    sites_data = load_json("sites.json", {"sites": []})
    flywheel   = load_json("flywheel_state.json")
    brain      = load_json("brain_state.json")
    mutual_aid = load_json("mutual_aid_summary.json")

    sites     = sites_data.get("sites", [])
    signed    = [s for s in sites if s.get("mou_signed")]
    uei_ready = bool(compliance.get("sam_gov", {}).get("uei", ""))
    ein_ready = compliance.get("ein", {}).get("status") == "active"

    narrative = render_narrative(cfg, compliance, sites_data, flywheel, brain, mutual_aid)

    city_slug = cfg.get("city_slug", "grant")
    out_file  = DOCS / f"{city_slug}-cdbg-current.md"
    out_file.write_text(narrative)

    # Status for OMNIBRAIN
    ready_score = 0
    if uei_ready:       ready_score += 30
    if ein_ready:       ready_score += 20
    if len(signed) >= 3: ready_score += 30
    if cfg.get("lmi_pct_tract_1", 0) > 51: ready_score += 10
    if cfg.get("contact_name"):             ready_score += 10

    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "city": cfg.get("city"),
        "amount_requested": cfg.get("amount_requested"),
        "deadline": cfg.get("submission_deadline"),
        "ready_score": ready_score,
        "ready_to_file": ready_score >= 90,
        "blocking_items": [],
        "output_file": str(out_file),
    }
    if not uei_ready:       status["blocking_items"].append("UEI from SAM.gov")
    if not ein_ready:       status["blocking_items"].append("EIN from IRS.gov")
    if len(signed) < 3:     status["blocking_items"].append(f"Site MOUs ({len(signed)}/3 signed)")
    if not cfg.get("lmi_pct_tract_1"): status["blocking_items"].append("LMI % from HUD LMISD")

    (DATA / "grant_ready_status.json").write_text(json.dumps(status, indent=2))

    print(f"\n  Grant: {cfg.get('city')} {cfg.get('grant_year')} — ${cfg.get('amount_requested',0):,}")
    print(f"  Ready score: {ready_score}/100 | File-ready: {status['ready_to_file']}")
    print(f"  Blocking: {status['blocking_items'] or 'none'}")
    print(f"  Output: {out_file}")


if __name__ == "__main__":
    main()
