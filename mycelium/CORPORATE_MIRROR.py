"""
CORPORATE_MIRROR.py
===================
S&P 500 Shadow Architecture Generator

Concept (Meeko):
  "For every big company, like ALL the S&P 500, build a SolarPunk duplicate
   BUT the EMPLOYEES get paid like CEOs and the CEOs? It's SolarPunk!
   There are no CEOs! Anything SolarPunk makes goes right back into itself."

This module generates "shadow reports" showing what a company would look like
if it ran on SolarPunk principles:
- CEO overhead redistributed to workers
- Automated redistribution instead of shareholder dividends
- Open ledger instead of proprietary financials
- Community value instead of shareholder value
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

ROOT       = Path(__file__).parent.parent
MIRROR_DIR = ROOT / "data" / "corporate_mirrors"
ACTUAL_LOG = ROOT / "SOLARPUNK_ACTUAL.md"

log = logging.getLogger("corporate_mirror")


@dataclass
class CompanyProfile:
    name:                   str
    sector:                 str
    avg_employee_salary:    float   # annual USD
    ceo_compensation:       float   # annual USD (salary + equity + bonuses)
    employee_count:         int
    annual_revenue:         float   # USD
    annual_profit:          float   # USD
    shareholder_dividend:   float   # total annual USD paid to shareholders


@dataclass
class SolarPunkMirror:
    company:               str
    generated_at:          str

    # Redistribution math
    ceo_overhead_per_worker:    float   # how much each worker gets if CEO comp is split
    redistributed_salary:       float   # what avg worker would make
    salary_multiplier:          float   # how many X more vs current

    # Dividend redistribution
    dividend_per_worker:        float   # if shareholder dividends went to workers instead
    total_worker_bonus:         float

    # SolarPunk structure
    governance:             str
    ledger_type:            str
    ip_policy:              str
    redistribution_rule:    str

    # The "shadow report" — what employees would actually earn
    current_avg_salary:     float
    solarpunk_equivalent_salary: float
    gain_per_worker:        float

    narrative: str


# ── Known S&P 500 data (approximate, public information) ─────────────────────
SP500_PROFILES = {
    "amazon": CompanyProfile(
        name="Amazon", sector="E-commerce/Logistics",
        avg_employee_salary=37_000, ceo_compensation=212_000_000,
        employee_count=1_540_000, annual_revenue=574_000_000_000,
        annual_profit=30_000_000_000, shareholder_dividend=0,
    ),
    "walmart": CompanyProfile(
        name="Walmart", sector="Retail",
        avg_employee_salary=25_000, ceo_compensation=25_700_000,
        employee_count=2_100_000, annual_revenue=648_000_000_000,
        annual_profit=15_500_000_000, shareholder_dividend=8_100_000_000,
    ),
    "mcdonalds": CompanyProfile(
        name="McDonald's", sector="Food Service",
        avg_employee_salary=24_000, ceo_compensation=19_200_000,
        employee_count=200_000, annual_revenue=23_200_000_000,
        annual_profit=8_500_000_000, shareholder_dividend=4_500_000_000,
    ),
    "apple": CompanyProfile(
        name="Apple", sector="Technology",
        avg_employee_salary=147_000, ceo_compensation=63_200_000,
        employee_count=161_000, annual_revenue=391_000_000_000,
        annual_profit=97_000_000_000, shareholder_dividend=14_800_000_000,
    ),
    "microsoft": CompanyProfile(
        name="Microsoft", sector="Technology",
        avg_employee_salary=182_000, ceo_compensation=55_000_000,
        employee_count=228_000, annual_revenue=245_000_000_000,
        annual_profit=87_900_000_000, shareholder_dividend=22_300_000_000,
    ),
    "target": CompanyProfile(
        name="Target", sector="Retail",
        avg_employee_salary=26_000, ceo_compensation=18_000_000,
        employee_count=415_000, annual_revenue=109_000_000_000,
        annual_profit=4_100_000_000, shareholder_dividend=800_000_000,
    ),
}


def generate_mirror(company_key: str) -> Optional[SolarPunkMirror]:
    """Generate a SolarPunk shadow report for a company."""
    profile = SP500_PROFILES.get(company_key.lower())
    if not profile:
        log.warning(f"No profile for '{company_key}'. Known: {list(SP500_PROFILES.keys())}")
        return None

    # Math: what if CEO pay was split among all workers?
    ceo_per_worker = profile.ceo_compensation / profile.employee_count
    sp_salary      = profile.avg_employee_salary + ceo_per_worker

    # Math: what if shareholder dividends went to workers?
    dividend_per_worker = profile.shareholder_dividend / profile.employee_count
    total_worker_bonus  = profile.shareholder_dividend  # all of it

    sp_total_salary = sp_salary + dividend_per_worker
    gain            = sp_total_salary - profile.avg_employee_salary
    multiplier      = sp_total_salary / max(profile.avg_employee_salary, 1)

    narrative = (
        f"{profile.name} ({profile.sector}): "
        f"Under current structure, the average worker earns ${profile.avg_employee_salary:,}/yr "
        f"while CEO earns ${profile.ceo_compensation:,.0f}/yr — a {profile.ceo_compensation/max(profile.avg_employee_salary,1):.0f}x gap. "
        f"Under SolarPunk principles: CEO pay redistributed → +${ceo_per_worker:,.0f}/worker/yr. "
        f"Shareholder dividends redirected to workers → +${dividend_per_worker:,.0f}/worker/yr. "
        f"Result: average worker earns ${sp_total_salary:,.0f}/yr ({multiplier:.1f}x current). "
        f"No CEO. No board. Automated redistribution logic handles what boards used to gatekeep."
    )

    mirror = SolarPunkMirror(
        company                     = profile.name,
        generated_at                = datetime.utcnow().isoformat(),
        ceo_overhead_per_worker     = round(ceo_per_worker, 2),
        redistributed_salary        = round(sp_salary, 2),
        salary_multiplier           = round(multiplier, 2),
        dividend_per_worker         = round(dividend_per_worker, 2),
        total_worker_bonus          = round(total_worker_bonus, 2),
        governance                  = "Community DAO + Automated Redistribution Algorithm",
        ledger_type                 = "Real-time public ledger (anyone can see everything)",
        ip_policy                   = "Open source — workers own what they build",
        redistribution_rule         = "100% of profit flows back to workers and community. Zero CEO overhead.",
        current_avg_salary          = profile.avg_employee_salary,
        solarpunk_equivalent_salary = round(sp_total_salary, 2),
        gain_per_worker             = round(gain, 2),
        narrative                   = narrative,
    )

    _save_mirror(company_key, mirror)
    return mirror


def _save_mirror(company_key: str, mirror: SolarPunkMirror):
    MIRROR_DIR.mkdir(parents=True, exist_ok=True)
    path = MIRROR_DIR / f"{company_key}_mirror.json"
    path.write_text(json.dumps(asdict(mirror), indent=2))
    log.info(f"Saved mirror: {path}")


def generate_all() -> dict:
    """Generate mirrors for all known companies."""
    results = {}
    for key in SP500_PROFILES:
        mirror = generate_mirror(key)
        if mirror:
            results[key] = mirror
            log.info(f"{mirror.company}: workers would earn ${mirror.solarpunk_equivalent_salary:,.0f}/yr ({mirror.salary_multiplier:.1f}x) under SolarPunk")
    return results


def print_report(company_key: str):
    """Print a human-readable shadow report."""
    mirror = generate_mirror(company_key)
    if not mirror:
        return
    print(f"\n{'='*60}")
    print(f"SOLARPUNK MIRROR: {mirror.company.upper()}")
    print(f"{'='*60}")
    print(mirror.narrative)
    print(f"\nCurrent avg salary:     ${mirror.current_avg_salary:>12,.0f}")
    print(f"SolarPunk equivalent:   ${mirror.solarpunk_equivalent_salary:>12,.0f}")
    print(f"Worker gain:            ${mirror.gain_per_worker:>12,.0f} (+{mirror.salary_multiplier:.1f}x)")
    print(f"\nGovernance: {mirror.governance}")
    print(f"IP Policy:  {mirror.ip_policy}")
    print(f"Ledger:     {mirror.ledger_type}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("Generating SolarPunk mirrors for all known S&P 500 companies...\n")
    results = generate_all()
    print(f"\nGenerated {len(results)} corporate mirrors.")
    print(f"Saved to: {MIRROR_DIR}")
    print("\nTop 3 biggest worker gains:")
    sorted_by_gain = sorted(results.values(), key=lambda m: m.gain_per_worker, reverse=True)
    for m in sorted_by_gain[:3]:
        print(f"  {m.company}: +${m.gain_per_worker:,.0f}/worker/yr ({m.salary_multiplier:.1f}x)")
