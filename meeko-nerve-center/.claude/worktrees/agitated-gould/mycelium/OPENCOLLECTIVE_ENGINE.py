#!/usr/bin/env python3
"""
OPENCOLLECTIVE_ENGINE.py — Open Collective + GitHub Sponsors Integration
========================================================================
Manages the transparent donation infrastructure:
- Monitors Open Collective if configured (OC_API_KEY)
- Tracks GitHub Sponsors if configured (GITHUB_TOKEN)
- Generates the public transparency report
- Calculates 99/1 PCRF split from all sources
- Creates monthly PCRF transfer action items

Open Collective API docs: https://graphql.opencollective.com/
GitHub Sponsors GraphQL: https://docs.github.com/en/graphql

Without API keys: still useful — generates templates, action items,
and donor thank-you templates.

Outputs: opencollective_state.json, sponsors_report.json
"""
import json, os, time
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone, date

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

_oc_key = os.environ.get("OPENCOLLECTIVE_API_KEY", "")
_gh_token = os.environ.get("GITHUB_TOKEN")
_repo_owner = "meekoenergy"
_collective_slug = "solarpunk-gaza-relief"  # Update after creating OC collective

# ─── Open Collective GraphQL Query ────────────────────────────────────────────
OC_QUERY = """
query {
  collective(slug: "%s") {
    name
    description
    stats {
      totalDonations { value currency }
      totalAmountRaised { value currency }
      balance { value currency }
      backers { all }
    }
    transactions(limit: 10, type: CREDIT) {
      nodes {
        amount { value currency }
        createdAt
        fromAccount { name }
        description
      }
    }
  }
}
""" % _collective_slug


def query_opencollective() -> dict:
    """Query Open Collective GraphQL API."""
    if not _oc_key:
        return {"status": "no_api_key", "message": "Set OPENCOLLECTIVE_API_KEY to enable"}

    try:
        body = json.dumps({"query": OC_QUERY}).encode()
        req = urllib.request.Request(
            "https://api.opencollective.com/graphql/v2",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Personal-Token": _oc_key,
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if "data" in data and "collective" in data["data"]:
                return {"status": "ok", "data": data["data"]["collective"]}
            return {"status": "error", "raw": data}
    except Exception as e:
        return {"status": "error", "message": str(e)[:80]}


def query_github_sponsors() -> dict:
    """Query GitHub Sponsors via GraphQL API."""
    if not _gh_token:
        return {"status": "no_token", "message": "GITHUB_TOKEN needed for sponsors"}

    query = """
    query {
      user(login: "%s") {
        sponsorshipsAsMaintainer(first: 20) {
          totalCount
          nodes {
            tierSelectedAt
            tier {
              name
              monthlyPriceInDollars
            }
            sponsorEntity {
              ... on User { login name }
              ... on Organization { login name }
            }
          }
        }
        monthlyEstimatedSponsorsIncomeInCents
      }
    }
    """ % _repo_owner

    try:
        body = json.dumps({"query": query}).encode()
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=body,
            headers={
                "Authorization": f"bearer {_gh_token}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if "data" in data and data["data"].get("user"):
                user = data["data"]["user"]
                sponsors = user.get("sponsorshipsAsMaintainer", {})
                monthly_cents = user.get("monthlyEstimatedSponsorsIncomeInCents", 0)
                return {
                    "status": "ok",
                    "total_sponsors": sponsors.get("totalCount", 0),
                    "monthly_usd": monthly_cents / 100,
                    "sponsors": [
                        {
                            "name": n.get("sponsorEntity", {}).get("name", ""),
                            "login": n.get("sponsorEntity", {}).get("login", ""),
                            "tier": n.get("tier", {}).get("name", ""),
                            "monthly_usd": n.get("tier", {}).get("monthlyPriceInDollars", 0),
                        }
                        for n in sponsors.get("nodes", [])
                    ],
                }
            return {"status": "error", "raw": str(data)[:200]}
    except Exception as e:
        return {"status": "error", "message": str(e)[:80]}


def calculate_pcrf_transfer(total_usd: float) -> dict:
    """Calculate what needs to go to PCRF."""
    pcrf_amount = round(total_usd * 0.99, 2)
    infra_amount = round(total_usd * 0.01, 2)
    return {
        "total_usd": total_usd,
        "pcrf_99pct": pcrf_amount,
        "infra_1pct": infra_amount,
        "pcrf_donate_url": "https://www.pcrf.net/donate",
        "transfer_instructions": (
            f"Transfer ${pcrf_amount} to PCRF via pcrf.net/donate or PayPal Giving Fund. "
            f"Document transfer in docs/TRANSPARENCY.md. "
            f"EIN: 11-3320278."
        ),
    }


def generate_sponsor_thank_you(sponsor_name: str, amount_usd: float) -> str:
    """Generate a thank-you message for a sponsor."""
    pcrf = round(amount_usd * 0.99, 2)
    return (
        f"Thank you, {sponsor_name}! 🌹\n\n"
        f"Your ${amount_usd:.2f}/month sponsorship routes ${pcrf:.2f} (99%) to PCRF "
        f"for medical aid and school supplies in Gaza. "
        f"The rest keeps SolarPunk running autonomously.\n\n"
        f"Your support is documented publicly at:\n"
        f"github.com/meekoenergy/meeko-nerve-center/blob/main/docs/TRANSPARENCY.md\n\n"
        f"Thank you for being part of the solution. 🤝"
    )


def generate_setup_checklist() -> list:
    """Generate the setup checklist for getting donations flowing."""
    return [
        {
            "step": 1,
            "title": "Create Open Collective",
            "url": "https://opencollective.com/create",
            "instructions": [
                "Go to opencollective.com/create",
                "Choose 'Open Source' collective type",
                "Name: 'SolarPunk AI — Gaza Relief'",
                "Apply to Open Source Collective as fiscal host (free, covers 501c3)",
                "Set mission: 99% to PCRF humanitarian aid",
                "Update OPENCOLLECTIVE_API_KEY in GitHub secrets",
            ],
            "time": "20 minutes",
            "benefit": "Tax-deductible donations, corporate sponsors, full transparency",
        },
        {
            "step": 2,
            "title": "Set Up GitHub Sponsors",
            "url": "https://github.com/sponsors",
            "instructions": [
                "Go to github.com/sponsors",
                "Complete W-9 or W-8BEN tax form",
                "Connect Stripe payout account",
                "Create tiers: $1/mo, $5/mo, $10/mo, $25/mo",
                "Publish sponsor profile",
            ],
            "time": "15 minutes",
            "benefit": "0% fees (GitHub covers Stripe), recurring, developer community",
        },
        {
            "step": 3,
            "title": "PayPal Giving Fund Fundraiser",
            "url": "https://www.paypal.com/us/webapps/mpp/giving-fund",
            "instructions": [
                "Create fundraiser for PCRF (already in PayPal Giving Fund)",
                "Set goal: $5,000 by end of year",
                "Share link in all SolarPunk content",
            ],
            "time": "10 minutes",
            "benefit": "0% fees when routing to enrolled nonprofits, tax-deductible",
        },
    ]


def run():
    sf = DATA / "opencollective_state.json"
    state = json.loads(sf.read_text()) if sf.exists() else {
        "cycles": 0, "total_donations_usd": 0, "total_to_pcrf_usd": 0
    }
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"OPENCOLLECTIVE_ENGINE cycle {state['cycles']}")

    # Query Open Collective
    print("  Querying Open Collective...")
    oc_data = query_opencollective()
    print(f"    Status: {oc_data['status']}")

    # Query GitHub Sponsors
    print("  Querying GitHub Sponsors...")
    gh_sponsors = query_github_sponsors()
    print(f"    Status: {gh_sponsors['status']}")

    # Aggregate revenue from all sources
    total_usd = 0.0
    if oc_data.get("status") == "ok":
        stats = oc_data.get("data", {}).get("stats", {})
        total_usd += stats.get("totalDonations", {}).get("value", 0)
    if gh_sponsors.get("status") == "ok":
        total_usd += gh_sponsors.get("monthly_usd", 0)

    # Also pull from flywheel
    for fname in ["data/flywheel_state.json", "data/gumroad_state.json"]:
        try:
            if Path(fname).exists():
                d = json.loads(Path(fname).read_text())
                rev = d.get("current_balance", d.get("total_revenue", 0))
                total_usd += rev
        except Exception:
            pass

    pcrf_calc = calculate_pcrf_transfer(total_usd)

    # Generate sponsor thank-you templates
    thank_yous = []
    if gh_sponsors.get("status") == "ok":
        for sponsor in gh_sponsors.get("sponsors", []):
            ty = generate_sponsor_thank_you(
                sponsor.get("name", sponsor.get("login", "Sponsor")),
                sponsor.get("monthly_usd", 0),
            )
            thank_yous.append({"sponsor": sponsor, "message": ty})

    # Setup checklist
    setup = generate_setup_checklist()

    # Save outputs
    (DATA / "sponsors_report.json").write_text(json.dumps({
        "generated_at": state["last_run"],
        "opencollective": oc_data,
        "github_sponsors": gh_sponsors,
        "total_revenue_usd": total_usd,
        "pcrf_distribution": pcrf_calc,
        "thank_yous": thank_yous,
        "setup_checklist": setup,
        "summary": (
            f"Total tracked: ${total_usd:.2f} | "
            f"To PCRF: ${pcrf_calc['pcrf_99pct']:.2f} | "
            f"Setup needed: {sum(1 for s in setup if s['step'] > 0)} steps"
        ),
    }, indent=2))

    state["total_donations_usd"] = total_usd
    state["total_to_pcrf_usd"] = pcrf_calc["pcrf_99pct"]
    sf.write_text(json.dumps(state, indent=2))

    print(f"  Total tracked: ${total_usd:.2f}")
    print(f"  PCRF allocation: ${pcrf_calc['pcrf_99pct']:.2f}")
    print(f"  Setup steps remaining: {len([s for s in setup])}")
    return state


if __name__ == "__main__":
    run()
