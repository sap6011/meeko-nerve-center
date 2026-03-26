#!/usr/bin/env python3
"""
compliance_monitor.py — Sovereign Legal Handler
================================================
Treats the legal shell like a self-healing microservice.
Meeko sets it up once. OMNIBRAIN watches it forever.

Tracks:
  - LLC filing status + expiration (Ohio SOS annual report due date)
  - SAM.gov UEI active status + registration expiration (via public API)
  - EIN registration (manual record — IRS has no public lookup)
  - Grant deadlines (stored in compliance_config.json)
  - CORC revenue vs grant spend (Sovereign Wallet tracking)

Reads:  data/compliance_config.json  (Meeko fills this in once)
        data/sites.json              (site control ledger)
Writes: data/compliance_status.json  (SYNAPSE reads this every cycle)

SAM.gov API: api.sam.gov/entity-information/v3/entities
Free key: sam.gov/content/entity-api (takes ~1 business day to activate)
"""
import os, json, requests
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA   = Path("data")
CONFIG = DATA / "compliance_config.json"
STATUS = DATA / "compliance_status.json"

SAMGOV_API_KEY = os.environ.get("SAMGOV_API_KEY")
SAMGOV_URL     = "https://api.sam.gov/entity-information/v3/entities"

# Days-until-expiry thresholds for alerts
WARN_DAYS  = 60
URGENT_DAYS = 14


def load_config():
    """
    Load compliance config. If missing, write a blank template
    so Meeko knows exactly what to fill in.
    """
    if CONFIG.exists():
        try:
            return json.loads(CONFIG.read_text())
        except Exception:
            pass

    # First-run: write blank template
    template = {
        "_instructions": "Fill in your real values. This file is read every OMNIBRAIN cycle.",
        "entity_name": "Ward 8 Sovereign Lattice LLC",
        "ohio_sos": {
            "filing_date": "",          # e.g. "2026-03-18"
            "confirmation_number": "",  # from bsportal.ohiosos.gov
            "annual_report_due": "",    # Ohio LLCs: due by April 15 each year after formation
            "status": "pending"         # pending | active | expired
        },
        "ein": {
            "number": "",               # XX-XXXXXXX format
            "issued_date": "",
            "status": "pending"         # pending | active
        },
        "sam_gov": {
            "uei": "",                  # e.g. J7KL2M3N4P55
            "registration_date": "",
            "expiration_date": "",      # SAM registrations expire annually — must renew
            "status": "pending"         # pending | active | expired | not_registered
        },
        "grants": [
            {
                "name": "Cuyahoga Falls CDBG 2026",
                "amount_requested": 236000,
                "submission_deadline": "2026-03-21",  # UPDATE WITH REAL DEADLINE
                "status": "drafting",   # drafting | submitted | awarded | rejected
                "award_date": "",
                "amount_awarded": 0
            }
        ],
        "sovereign_wallet": {
            "grant_funds_received": 0,
            "grant_funds_spent": 0,
            "corc_revenue": 0,
            "maintenance_reserve": 0,
            "last_updated": ""
        }
    }
    CONFIG.write_text(json.dumps(template, indent=2))
    print("  Created blank compliance_config.json — fill in your LLC/EIN/UEI details")
    return template


def check_samgov(uei, api_key):
    """Check entity status via SAM.gov public API."""
    if not uei:
        return {"status": "no_uei", "note": "Add UEI to compliance_config.json"}
    if not api_key:
        return {"status": "no_api_key",
                "note": "Add SAMGOV_API_KEY to GitHub Secrets (free key at sam.gov/content/entity-api)"}
    try:
        r = requests.get(
            SAMGOV_URL,
            params={"api_key": api_key, "uei": uei, "includeSections": "entityRegistration"},
            timeout=20
        )
        if r.status_code == 200:
            data = r.json()
            entities = data.get("entityData", [])
            if not entities:
                return {"status": "not_found", "note": f"UEI {uei} not found in SAM.gov"}
            ent  = entities[0].get("entityRegistration", {})
            exp  = ent.get("registrationExpirationDate", "")
            stat = ent.get("registrationStatus", "")
            days_left = None
            if exp:
                try:
                    exp_dt    = datetime.fromisoformat(exp[:10])
                    days_left = (exp_dt - datetime.now()).days
                except Exception:
                    pass
            return {
                "status": stat.lower() if stat else "unknown",
                "expiration_date": exp,
                "days_until_expiry": days_left,
                "uei": uei,
                "raw_status": stat,
            }
        elif r.status_code == 403:
            return {"status": "api_key_invalid", "note": "Check SAMGOV_API_KEY"}
        else:
            return {"status": "api_error", "code": r.status_code, "note": r.text[:100]}
    except Exception as ex:
        return {"status": "error", "note": str(ex)}


def compute_alerts(config, sam_result):
    """Generate actionable alerts sorted by urgency."""
    alerts = []
    now    = datetime.now(timezone.utc)

    # LLC status
    llc = config.get("ohio_sos", {})
    if llc.get("status") == "pending" and not llc.get("filing_date"):
        alerts.append({
            "level": "critical", "area": "LLC",
            "message": "Ohio LLC not yet filed. Go to bsportal.ohiosos.gov — $99, same-day.",
            "action": "File now: bsportal.ohiosos.gov"
        })
    elif llc.get("annual_report_due"):
        try:
            due = datetime.fromisoformat(llc["annual_report_due"])
            days = (due - now.replace(tzinfo=None)).days
            if days <= URGENT_DAYS:
                alerts.append({"level": "critical", "area": "LLC Annual Report",
                    "message": f"Ohio LLC annual report due in {days} days",
                    "action": "File at bsportal.ohiosos.gov"})
            elif days <= WARN_DAYS:
                alerts.append({"level": "warning", "area": "LLC Annual Report",
                    "message": f"Ohio LLC annual report due in {days} days",
                    "action": "File at bsportal.ohiosos.gov"})
        except Exception:
            pass

    # EIN status
    ein = config.get("ein", {})
    if ein.get("status") == "pending" and not ein.get("number"):
        alerts.append({
            "level": "critical", "area": "EIN",
            "message": "EIN not yet applied for. Takes 5 minutes at IRS.gov.",
            "action": "Apply: IRS.gov → Apply for EIN Online"
        })

    # SAM.gov status
    sam = config.get("sam_gov", {})
    if not sam.get("uei") and sam.get("status") == "pending":
        alerts.append({
            "level": "critical", "area": "SAM.gov",
            "message": "SAM.gov registration not started. UEI required for all HUD grants.",
            "action": "Register: sam.gov (need EIN first)"
        })
    elif sam_result.get("status") == "active":
        days = sam_result.get("days_until_expiry")
        if days is not None:
            if days <= URGENT_DAYS:
                alerts.append({"level": "critical", "area": "SAM.gov",
                    "message": f"SAM.gov registration expires in {days} days",
                    "action": "Renew immediately at sam.gov"})
            elif days <= WARN_DAYS:
                alerts.append({"level": "warning", "area": "SAM.gov",
                    "message": f"SAM.gov registration expires in {days} days",
                    "action": "Schedule renewal at sam.gov"})
    elif sam_result.get("status") == "expired":
        alerts.append({"level": "critical", "area": "SAM.gov",
            "message": "SAM.gov registration EXPIRED — cannot receive federal funds",
            "action": "Renew immediately at sam.gov"})

    # Grant deadlines
    for grant in config.get("grants", []):
        deadline_str = grant.get("submission_deadline", "")
        status       = grant.get("status", "")
        if status in ("drafting", "in_progress") and deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str)
                days     = (deadline - now.replace(tzinfo=None)).days
                if days <= URGENT_DAYS:
                    alerts.append({"level": "critical", "area": f"Grant: {grant['name']}",
                        "message": f"Deadline in {days} days — ${grant.get('amount_requested',0):,} at stake",
                        "action": f"Submit by {deadline_str}"})
                elif days <= WARN_DAYS:
                    alerts.append({"level": "warning", "area": f"Grant: {grant['name']}",
                        "message": f"Deadline in {days} days",
                        "action": f"Finalize for {deadline_str}"})
            except Exception:
                pass

    return alerts


def load_sites():
    sf = DATA / "sites.json"
    if sf.exists():
        try:
            return json.loads(sf.read_text())
        except Exception:
            pass
    return {"sites": []}


def sovereign_wallet_summary(config):
    """Compute wallet health: grant spend vs CORC revenue."""
    wallet = config.get("sovereign_wallet", {})
    received = wallet.get("grant_funds_received", 0)
    spent    = wallet.get("grant_funds_spent", 0)
    corc     = wallet.get("corc_revenue", 0)
    reserve  = wallet.get("maintenance_reserve", 0)

    unspent   = received - spent
    self_fund = corc + reserve
    burn_rate = spent / max(received, 1) * 100

    return {
        "grant_funds_received": received,
        "grant_funds_spent": spent,
        "grant_unspent": unspent,
        "corc_revenue": corc,
        "maintenance_reserve": reserve,
        "self_funding_total": self_fund,
        "grant_burn_rate_pct": round(burn_rate, 1),
        "status": "healthy" if unspent >= 0 and burn_rate <= 90 else "overspent",
    }


def main():
    DATA.mkdir(exist_ok=True)
    print("compliance_monitor — Sovereign Legal Handler...")
    ts     = datetime.now(timezone.utc).isoformat()
    config = load_config()

    # Check SAM.gov live
    uei        = config.get("sam_gov", {}).get("uei", "")
    sam_result = check_samgov(uei, SAMGOV_API_KEY)

    # Alerts
    alerts   = compute_alerts(config, sam_result)
    critical = [a for a in alerts if a["level"] == "critical"]
    warnings = [a for a in alerts if a["level"] == "warning"]

    # Sites
    sites     = load_sites()
    site_list = sites.get("sites", [])
    signed    = [s for s in site_list if s.get("mou_signed")]

    # Wallet
    wallet = sovereign_wallet_summary(config)

    # Entity health score (0-100)
    entity_score = 100
    entity_score -= len(critical) * 25
    entity_score -= len(warnings) * 10
    entity_score = max(0, min(100, entity_score))

    status = {
        "timestamp": ts,
        "entity_name": config.get("entity_name", ""),
        "entity_score": entity_score,
        "ohio_llc": {
            "status": config.get("ohio_sos", {}).get("status", "pending"),
            "filing_date": config.get("ohio_sos", {}).get("filing_date", ""),
            "annual_report_due": config.get("ohio_sos", {}).get("annual_report_due", ""),
        },
        "ein": {
            "status": config.get("ein", {}).get("status", "pending"),
            "has_number": bool(config.get("ein", {}).get("number", "")),
        },
        "sam_gov": sam_result,
        "grants": config.get("grants", []),
        "sites_total": len(site_list),
        "sites_signed": len(signed),
        "sites_needed": 3,
        "sites_gap": max(0, 3 - len(signed)),
        "sovereign_wallet": wallet,
        "alerts": alerts,
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "compliance_summary": (
            "LEGAL SHELL ACTIVE" if entity_score >= 75
            else ("FILINGS IN PROGRESS" if entity_score >= 40
            else "ACTION REQUIRED — CHECK COMPLIANCE_CONFIG.JSON")
        ),
    }

    STATUS.write_text(json.dumps(status, indent=2))

    print(f"\n  Entity Score: {entity_score}/100 — {status['compliance_summary']}")
    print(f"  LLC: {status['ohio_llc']['status']} | EIN: {status['ein']['status']} | SAM: {sam_result.get('status','?')}")
    print(f"  Sites signed: {len(signed)}/3 | Grant alerts: {len(critical)} critical")
    for a in critical[:3]:
        print(f"  🔴 [{a['area']}] {a['message']}")
    for a in warnings[:2]:
        print(f"  🟡 [{a['area']}] {a['message']}")
    if not alerts:
        print("  ✅ All compliance checks clear")


if __name__ == "__main__":
    main()
