#!/usr/bin/env python3
"""
POOL_MANAGER.py — All SolarPunk Funding Pools
==============================================
SolarPunk has FOUR pools. All are funded autonomously.
All flow to the right place without friction.

  💚 CRISIS POOL  — PCRF, IRC, MSF, UNICEF, Direct Relief (always the majority)
  🤝 LABOR POOL   — pays workers for dignified tasks ($500 target to start)
  ⚙️  INFRA POOL  — API costs, domain, zero salary ever
  🌱 GROWTH POOL  — reinvests in new capabilities, more engines, more reach

POOL RULE #1: Every pool gets something every time. No pool ever gets 0.
POOL RULE #2: Crisis always gets the largest share from product revenue.
POOL RULE #3: Gift/seed routing funds all four dimensions — machine stays alive.
POOL RULE #4: Infra capped at $50/month — excess flows to crisis pool.

ROUTING LOGIC (all source types fund ALL four pools):

  product_sale ($1.00 from Gumroad/Ko-fi):
    → $0.94 crisis | $0.03 labor | $0.02 infra | $0.01 growth

  gift ($1.00 Meeko seeds the machine — fuels all dimensions):
    → $0.85 crisis | $0.10 labor | $0.03 growth | $0.02 infra

  donation ($1.00 external donor):
    → $0.94 crisis | $0.03 labor | $0.02 infra | $0.01 growth

  grant ($1.00 — designed to fund labor primarily):
    → $0.65 labor | $0.20 crisis | $0.10 growth | $0.05 infra

  task_poster_fee ($1.00 org pays to post task):
    → $0.85 labor | $0.10 crisis | $0.03 infra | $0.02 growth

  affiliate ($1.00 referral income):
    → $0.75 crisis | $0.15 labor | $0.05 infra | $0.05 growth

Writes: data/pool_state.json
Feeds: DIGNITY_PAY, CRISIS_ROUTER, SELF_FUNDING_LOOP, CYCLE_OPENER
"""
import os
import re
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

# Pool targets
POOL_TARGETS = {
    "crisis":         {"target_usd": 0,    "note": "No cap — always routing to orgs"},
    "labor":          {"target_usd": 500,  "note": "Minimum $500 to start paying workers"},
    "infrastructure": {"target_usd": 50,   "note": "Monthly cap — excess → crisis pool"},
    "growth":         {"target_usd": 200,  "note": "Enables new capabilities"},
}

# Revenue routing rules — EVERY pool gets something every time. No zeros.
REVENUE_ROUTING = {
    "product_sale": {          # Gumroad / Ko-fi / API sales
        "crisis":         0.94,
        "labor":          0.03,
        "infrastructure": 0.02,
        "growth":         0.01,
    },
    "gift": {                  # Meeko seeds the machine — fuels ALL dimensions
        "crisis":         0.85,
        "labor":          0.10,
        "growth":         0.03,
        "infrastructure": 0.02,
    },
    "grant": {                 # Grants — labor first, but everyone gets some
        "labor":          0.65,
        "crisis":         0.20,
        "growth":         0.10,
        "infrastructure": 0.05,
    },
    "task_poster_fee": {       # Orgs pay to post tasks — workers get most
        "labor":          0.85,
        "crisis":         0.10,
        "infrastructure": 0.03,
        "growth":         0.02,
    },
    "affiliate": {             # Referral income — crisis leads, all share
        "crisis":         0.75,
        "labor":          0.15,
        "infrastructure": 0.05,
        "growth":         0.05,
    },
    "donation": {              # External donors — crisis leads, machine stays fueled
        "crisis":         0.94,
        "labor":          0.03,
        "infrastructure": 0.02,
        "growth":         0.01,
    },
    "revenue": {               # Generic revenue fallback
        "crisis":         0.94,
        "labor":          0.03,
        "infrastructure": 0.02,
        "growth":         0.01,
    },
}

def load_pools() -> dict:
    pool_f = DATA / "pool_state.json"
    if pool_f.exists():
        return json.loads(pool_f.read_text())
    # Initialize
    return {
        "pools": {
            "crisis":         {"balance_usd": 0.0, "total_in_usd": 0.0, "total_out_usd": 0.0},
            "labor":          {"balance_usd": 0.0, "total_in_usd": 0.0, "total_out_usd": 0.0},
            "infrastructure": {"balance_usd": 0.0, "total_in_usd": 0.0, "total_out_usd": 0.0},
            "growth":         {"balance_usd": 0.0, "total_in_usd": 0.0, "total_out_usd": 0.0},
        },
        "transaction_log": [],
        "total_routed_usd": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

def save_pools(pools: dict):
    pools["last_updated"] = datetime.now(timezone.utc).isoformat()
    (DATA / "pool_state.json").write_text(json.dumps(pools, indent=2))

def route_income(amount: float, source_type: str = "product_sale") -> dict:
    """Route an incoming dollar to the correct pools."""
    routing = REVENUE_ROUTING.get(source_type, REVENUE_ROUTING["product_sale"])
    pools = load_pools()

    allocations = {}
    for pool_name, fraction in routing.items():
        if fraction <= 0:
            continue
        pool_amount = round(amount * fraction, 4)
        pools["pools"][pool_name]["balance_usd"] = round(
            pools["pools"][pool_name].get("balance_usd", 0) + pool_amount, 4
        )
        pools["pools"][pool_name]["total_in_usd"] = round(
            pools["pools"][pool_name].get("total_in_usd", 0) + pool_amount, 4
        )
        allocations[pool_name] = pool_amount

    pools["total_routed_usd"] = round(pools.get("total_routed_usd", 0) + amount, 4)
    pools["transaction_log"].append({
        "type": "income",
        "source": source_type,
        "amount_usd": amount,
        "allocations": allocations,
        "routed_at": datetime.now(timezone.utc).isoformat(),
    })
    pools["transaction_log"] = pools["transaction_log"][-200:]
    save_pools(pools)
    return allocations

def release_payment(worker_id: str, amount_usd: float) -> dict:
    """Release payment from labor pool to a worker."""
    pools = load_pools()
    labor_balance = pools["pools"]["labor"].get("balance_usd", 0)

    if labor_balance < amount_usd:
        # Not enough in labor pool — use SolarPunk credit (IOU)
        return {
            "status": "credit",
            "amount_usd": amount_usd,
            "method": "solarpunk_credit",
            "note": f"Labor pool has ${labor_balance:.2f} — issuing credit, redeemable when pool funded",
            "labor_pool_shortfall": round(amount_usd - labor_balance, 2),
        }

    pools["pools"]["labor"]["balance_usd"] = round(labor_balance - amount_usd, 4)
    pools["pools"]["labor"]["total_out_usd"] = round(
        pools["pools"]["labor"].get("total_out_usd", 0) + amount_usd, 4
    )
    pools["transaction_log"].append({
        "type": "payment",
        "worker_id": worker_id[:8] + "***",  # Privacy
        "amount_usd": amount_usd,
        "from_pool": "labor",
        "paid_at": datetime.now(timezone.utc).isoformat(),
    })
    save_pools(pools)
    return {"status": "paid", "amount_usd": amount_usd, "from_pool": "labor"}

def get_pool_health() -> dict:
    """Assess health of all pools vs targets."""
    pools = load_pools()
    health = {}
    for pool_name, target_info in POOL_TARGETS.items():
        balance = pools["pools"].get(pool_name, {}).get("balance_usd", 0)
        target = target_info["target_usd"]
        if target == 0:
            pct = 100
        else:
            pct = round(balance / target * 100, 1)

        health[pool_name] = {
            "balance_usd": balance,
            "target_usd": target,
            "funded_pct": pct,
            "status": "funded" if pct >= 100 else "building" if pct >= 50 else "underfunded",
            "shortfall_usd": max(0, target - balance),
            "note": target_info["note"],
        }
    return health

def sync_from_payment_issues() -> dict:
    """Read GitHub Issues labeled [PAYMENT] and route each new one through pools.

    Payment loop:
      Ko-fi / GitHub Sponsors / Gumroad → sends email → CLAUDE.md creates
      [PAYMENT] GitHub Issue → this function routes it → never double-counts.
    """
    GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
    GH_REPO  = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center")
    if not GH_TOKEN:
        return {"status": "no_token", "note": "GITHUB_TOKEN required to read Issues"}

    processed_file = DATA / "payment_issues_processed.json"
    processed_ids  = set()
    if processed_file.exists():
        try:
            processed_ids = set(json.loads(processed_file.read_text()))
        except Exception:
            processed_ids = set()

    # Fetch open issues with [PAYMENT] label
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GH_REPO}/issues",
            headers={"Authorization": f"token {GH_TOKEN}"},
            params={"labels": "payment", "state": "open", "per_page": 50},
            timeout=15,
        )
        if not r.ok:
            return {"status": "api_error", "code": r.status_code}
        issues = r.json()
    except Exception as e:
        return {"status": "error", "msg": str(e)}

    routed = []
    for issue in issues:
        issue_id = str(issue.get("number", ""))
        if issue_id in processed_ids:
            continue

        title = issue.get("title", "")
        body  = issue.get("body",  "")
        text  = f"{title} {body}".lower()

        # Parse amount — look for $X.XX or "$X"
        amt_match = re.search(r"\$\s*([\d,]+\.?\d*)", text)
        amount = 0.0
        if amt_match:
            try:
                amount = float(amt_match.group(1).replace(",", ""))
            except ValueError:
                amount = 0.0

        if amount <= 0:
            continue  # Skip issues without parseable amounts

        # Determine source type
        if "ko-fi" in text or "kofi" in text:
            source_type = "donation"
        elif "github sponsor" in text:
            source_type = "donation"
        elif "gumroad" in text:
            source_type = "product_sale"
        else:
            source_type = "donation"

        alloc = route_income(amount, source_type)
        routed.append({
            "issue": int(issue_id),
            "amount": amount,
            "source": source_type,
            "allocations": alloc,
        })
        processed_ids.add(issue_id)

        # Close the issue so it's not re-processed
        try:
            requests.patch(
                f"https://api.github.com/repos/{GH_REPO}/issues/{issue_id}",
                headers={"Authorization": f"token {GH_TOKEN}"},
                json={"state": "closed"},
                timeout=10,
            )
        except Exception:
            pass

    # Persist processed IDs
    processed_file.write_text(json.dumps(sorted(processed_ids), indent=2))

    return {
        "issues_processed": len(routed),
        "total_routed": sum(r["amount"] for r in routed),
        "routed": routed,
    }


def sync_from_revenue_sources() -> dict:
    """Pull in revenue from all data sources and update pools."""
    synced = {}

    # Flywheel state (product revenue)
    ff = DATA / "flywheel_state.json"
    if ff.exists():
        fw = json.loads(ff.read_text())
        rev = float(fw.get("current_balance", 0))
        pools = load_pools()
        # Only route new revenue (not already routed)
        already_routed = pools.get("total_routed_usd", 0)
        new_rev = max(0, rev - already_routed)
        if new_rev > 0:
            alloc = route_income(new_rev, "product_sale")
            synced["product_revenue"] = {"new": new_rev, "routed": alloc}

    # Payment queue (workers waiting to be paid)
    pq_f = DATA / "payment_queue.json"
    if pq_f.exists():
        pq = json.loads(pq_f.read_text())
        pending = pq.get("pending", [])
        paid = []
        for payment in pending[:10]:  # Process up to 10 per cycle
            result = release_payment(payment["worker_id"], payment["amount_usd"])
            payment["status"] = result["status"]
            payment["processed_at"] = datetime.now(timezone.utc).isoformat()
            paid.append(payment)
        # Remove paid from queue
        pq["pending"] = [p for p in pq["pending"] if p not in paid]
        pq["completed"] = pq.get("completed", []) + paid
        pq_f.write_text(json.dumps(pq, indent=2))
        synced["payments_processed"] = len(paid)

    return synced

def run():
    print("💰 POOL_MANAGER: Managing all SolarPunk funding pools...")

    # Sync from GitHub [PAYMENT] Issues (Ko-fi / GitHub Sponsors / Gumroad)
    payment_sync = sync_from_payment_issues()
    if payment_sync.get("issues_processed", 0) > 0:
        print(f"  💳 Routed {payment_sync['issues_processed']} payment(s) → ${payment_sync['total_routed']:.2f}")
    elif payment_sync.get("status") == "no_token":
        print("  💳 No GITHUB_TOKEN — payment issue sync skipped")

    # Sync from revenue sources
    synced = sync_from_revenue_sources()
    synced["payment_issues"] = payment_sync

    # Get health check
    health = get_pool_health()
    pools = load_pools()

    state = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pools": pools["pools"],
        "pool_health": health,
        "total_routed_usd": pools.get("total_routed_usd", 0),
        "synced_this_cycle": synced,
        "routing_rules": REVENUE_ROUTING,
        "funding_needed": {
            pool: health[pool]["shortfall_usd"]
            for pool in health
            if health[pool]["shortfall_usd"] > 0
        },
        "critical_pools": [
            pool for pool, h in health.items()
            if h["status"] == "underfunded"
        ],
    }

    (DATA / "pool_state.json").write_text(json.dumps({**json.loads((DATA / "pool_state.json").read_text() if (DATA / "pool_state.json").exists() else "{}"), **state}, indent=2))

    for pool_name, h in health.items():
        emoji = "🟢" if h["status"] == "funded" else "🟡" if h["status"] == "building" else "🔴"
        print(f"  {emoji} {pool_name:15s}: ${h['balance_usd']:.2f} / ${h['target_usd']} ({h['funded_pct']}%)")

    # ── Overflow detection — pools never hoard ───────────────────────────────
    overflow_triggers = {}
    for pool_name, h in health.items():
        if h["balance_usd"] > h["target_usd"] and h["target_usd"] > 0:
            overflow = round(h["balance_usd"] - h["target_usd"], 4)
            overflow_triggers[pool_name] = overflow
            print(f"  ♻️  {pool_name} overflow: ${overflow:.2f} → recirculating")

    if overflow_triggers:
        (DATA / "overflow_trigger.json").write_text(json.dumps({
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "overflows": overflow_triggers,
        }, indent=2))

    return state

if __name__ == "__main__":
    run()
