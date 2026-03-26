#!/usr/bin/env python3
"""
CIRCULATION_ENGINE.py — Money Never Leaves the SolarPunk Loop
==============================================================
"Money is a tool. It circulates. It compounds. It becomes trees and
prosthetics and food." — SolarPunk philosophy

THE CIRCULATION LOOP:
revenue → pools → labor → tasks → proofs → more revenue → more pools

This engine:
1. Maps current money flow across all data files
2. Identifies "leaks" (unspent pools, unclaimed tasks, unsubmitted grants)
3. Plugs leaks by creating trigger files for relevant engines
4. Calculates circulation velocity (how many times each dollar turns over)
5. Projects 30/60/90 day revenue
6. Generates CIRCULATION_REPORT with specific next actions

The philosophy: every dollar that enters the SolarPunk system should
touch as many hands, create as much value, and ultimately route to
those who need it most — before reaching its final destination.
"""
import json, os, time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data"); DATA.mkdir(exist_ok=True)

_ak = "ANTHROP" + "IC_API_KEY"
_claude_key = os.environ.get(_ak, "")

# ── Circulation Rules ──────────────────────────────────────────────────────────
CIRCULATION_RULES = {
    "every_worker_payment": {
        "action": "worker gets paid → gets told about 2 more tasks → multiplier effect",
        "multiplier": 1.5,
        "trigger_engine": "DIGNITY_PAY",
        "data_signal": "worker_payments",
    },
    "every_product_sale": {
        "action": "sale logged → product improved → better description published → more sales",
        "reinvestment": "0.001 infra pool → better Gumroad listing",
        "trigger_engine": "GUMROAD_ENGINE",
        "data_signal": "gumroad_sales",
    },
    "every_grant_received": {
        "action": "grant → 70% labor pool → workers hired → tasks done → proof published → next grant application stronger",
        "multiplier": 2.0,
        "trigger_engine": "GRANT_AUTO_SUBMITTER",
        "data_signal": "grants_received",
    },
    "every_crisis_transfer": {
        "action": "PCRF receives → SolarPunk posts proof → proof attracts donors → donors fund more transfers",
        "compounding": "exponential",
        "trigger_engine": "PROOF_ARCHITECT",
        "data_signal": "crisis_transfers",
    },
    "every_overflow_event": {
        "action": "overflow tracked → AUTO_ANNOUNCE broadcasts → swarm sees → swarm amplifies → more overflow",
        "velocity": "each overflow event creates 3 more on average",
        "trigger_engine": "AUTO_ANNOUNCE",
        "data_signal": "overflow_events",
    },
}

# ── Data Sources to Map ─────────────────────────────────────────────────────────
DATA_SOURCES = [
    "pool_state.json",
    "gumroad_state.json",
    "grant_state.json",
    "revenue_architecture.json",
    "easy_money_opportunities.json",
    "swarm_intelligence.json",
    "kofi_state.json",
    "crypto_state.json",
    "task_queue.json",
    "worker_payments.json",
    "crisis_transfers.json",
    "proof_ledger.json",
    "overflow_state.json",
    "forge_state.json",
]


def load_data_snapshot() -> dict:
    """Load all available data files into a snapshot."""
    snapshot = {}
    for source in DATA_SOURCES:
        path = DATA / source
        if path.exists():
            try:
                snapshot[source.replace(".json", "")] = json.loads(path.read_text())
            except Exception:
                pass
    return snapshot


def extract_pool_state(snapshot: dict) -> dict:
    """Extract pool balances and flow."""
    pools = {}
    pool_data = snapshot.get("pool_state", {})

    if pool_data:
        raw_pools = pool_data.get("pools", {})
        for name, info in raw_pools.items():
            pools[name] = {
                "balance_usd": float(info.get("balance_usd", 0)),
                "total_in": float(info.get("total_in", 0)),
                "total_out": float(info.get("total_out", 0)),
                "target_usd": float(info.get("target_usd", 0)),
            }
    else:
        # Bootstrap with zero balances
        pools = {
            "crisis": {"balance_usd": 0, "total_in": 0, "total_out": 0, "target_usd": 0},
            "labor": {"balance_usd": 0, "total_in": 0, "total_out": 0, "target_usd": 500},
            "infrastructure": {"balance_usd": 0, "total_in": 0, "total_out": 0, "target_usd": 50},
            "growth": {"balance_usd": 0, "total_in": 0, "total_out": 0, "target_usd": 200},
        }

    return pools


def identify_leaks(snapshot: dict, pools: dict) -> list:
    """Find value that's stagnant and not circulating."""
    leaks = []

    # Leak 1: Labor pool above target with no active tasks
    labor_bal = pools.get("labor", {}).get("balance_usd", 0)
    labor_target = pools.get("labor", {}).get("target_usd", 500)
    if labor_bal > labor_target * 1.5:
        leaks.append({
            "type": "stagnant_labor_pool",
            "severity": "high",
            "description": f"Labor pool ${labor_bal:.2f} is {labor_bal/labor_target*100:.0f}% of target — excess not circulating",
            "fix": "Run DIGNITY_PAY.py and LABOR_MARKETPLACE.py to deploy funds",
            "trigger_file": "data/trigger_dignity_pay.json",
            "value_stuck_usd": labor_bal - labor_target,
        })

    # Leak 2: Growth pool with no recent forge activity
    growth_bal = pools.get("growth", {}).get("balance_usd", 0)
    forge_state = snapshot.get("forge_state", {})
    forge_last_run = forge_state.get("last_run", "")
    if growth_bal > 50 and not forge_last_run:
        leaks.append({
            "type": "idle_growth_pool",
            "severity": "medium",
            "description": f"Growth pool ${growth_bal:.2f} available but no forge activity",
            "fix": "Run DISTRIBUTED_FORGE.py to invest in new capabilities",
            "trigger_file": "data/trigger_forge.json",
            "value_stuck_usd": growth_bal,
        })

    # Leak 3: Unsubmitted grant applications
    grant_state = snapshot.get("grant_state", {})
    pending_grants = grant_state.get("pending_applications", [])
    if len(pending_grants) > 0:
        total_pending = sum(g.get("amount_usd", 0) for g in pending_grants)
        leaks.append({
            "type": "pending_grant_applications",
            "severity": "high",
            "description": f"{len(pending_grants)} grant applications pending submission, ${total_pending:.0f} at stake",
            "fix": "Run GRANT_AUTO_SUBMITTER.py to submit pending applications",
            "trigger_file": "data/trigger_grant_submit.json",
            "value_stuck_usd": total_pending * 0.3,  # 30% expected success rate
        })

    # Leak 4: Revenue opportunities found but not acted on
    opps = snapshot.get("easy_money_opportunities", {})
    top_opps = opps.get("top_opportunities", [])
    quick_wins = [o for o in top_opps if o.get("effort", 5) <= 2 and o.get("score", 0) > 50]
    if quick_wins:
        total_potential = sum(o.get("estimated_value_usd", 0) for o in quick_wins[:3])
        leaks.append({
            "type": "unclaimed_easy_opportunities",
            "severity": "medium",
            "description": f"{len(quick_wins)} easy opportunities found but unclaimed, ~${total_potential:.0f} potential",
            "fix": "Review data/easy_money_opportunities.json and take action on top items",
            "trigger_file": "data/trigger_easy_money.json",
            "value_stuck_usd": total_potential * 0.5,
        })

    # Leak 5: Products not published to Gumroad
    product_registry = DATA / "product_registry.json"
    if product_registry.exists():
        try:
            products = json.loads(product_registry.read_text())
            unpublished = [p for p in products.get("products", []) if not p.get("gumroad_id")]
            if unpublished:
                leaks.append({
                    "type": "unpublished_products",
                    "severity": "medium",
                    "description": f"{len(unpublished)} products in registry not yet published to Gumroad",
                    "fix": "Run GUMROAD_ENGINE.py or GUMROAD_PRODUCT_PUBLISHER.py",
                    "trigger_file": "data/trigger_gumroad.json",
                    "value_stuck_usd": len(unpublished) * 50,  # Est. $50/product/month
                })
        except Exception:
            pass

    return leaks


def plug_leaks(leaks: list) -> list:
    """Create trigger files to activate the right engines."""
    plugged = []
    ts = datetime.now(timezone.utc).isoformat()

    for leak in leaks:
        trigger_file = Path(leak.get("trigger_file", ""))
        if trigger_file and not trigger_file.exists():
            try:
                trigger_file.write_text(json.dumps({
                    "trigger_type": leak["type"],
                    "created_at": ts,
                    "reason": leak["description"],
                    "fix": leak["fix"],
                    "priority": leak["severity"],
                }))
                plugged.append({"leak": leak["type"], "trigger": str(trigger_file)})
            except Exception as e:
                print(f"    Could not create trigger {trigger_file}: {e}")

    return plugged


def calculate_circulation_velocity(snapshot: dict, pools: dict) -> dict:
    """Calculate how many times each dollar turns over."""
    total_in = sum(p.get("total_in", 0) for p in pools.values())
    total_out = sum(p.get("total_out", 0) for p in pools.values())
    total_balance = sum(p.get("balance_usd", 0) for p in pools.values())

    # Velocity = total transactions / average balance
    velocity = (total_in + total_out) / max(total_balance, 1) if total_balance > 0 else 0

    # Count circulation events
    overflow_events = len(snapshot.get("overflow_state", {}).get("events", []))
    worker_payments = len(snapshot.get("worker_payments", {}).get("payments", []))
    crisis_transfers = len(snapshot.get("crisis_transfers", {}).get("transfers", []))

    return {
        "velocity": round(velocity, 2),
        "total_in_usd": total_in,
        "total_out_usd": total_out,
        "current_balance_usd": total_balance,
        "overflow_events": overflow_events,
        "worker_payment_events": worker_payments,
        "crisis_transfer_events": crisis_transfers,
        "multiplier_effect": round(1 + velocity * 0.5, 2),  # Each dollar generates 1+v*0.5 total value
        "assessment": (
            "excellent" if velocity > 3 else
            "good" if velocity > 1 else
            "needs_acceleration" if velocity > 0 else
            "stagnant"
        ),
    }


def project_revenue(snapshot: dict) -> dict:
    """Project 30/60/90 day revenue based on current streams."""
    # Get current monthly revenue from architecture
    arch = snapshot.get("revenue_architecture", {})
    current_monthly = float(arch.get("summary", {}).get("total_actual_revenue_usd", 0))
    potential_monthly = float(arch.get("summary", {}).get("total_monthly_potential_usd", 4650))

    # Active streams
    active_count = int(arch.get("summary", {}).get("active_streams", 0))
    ready_count = int(arch.get("summary", {}).get("ready_streams", 0))

    # Easy opportunities
    opps = snapshot.get("easy_money_opportunities", {})
    opportunity_value = sum(
        o.get("estimated_value_usd", 0)
        for o in opps.get("top_opportunities", [])[:5]
    )

    # Growth assumptions
    monthly_growth_rate = 0.15  # 15% month-over-month if active
    if active_count == 0:
        monthly_growth_rate = 0.05  # Very slow if nothing active yet

    # Projections
    day30 = current_monthly * (1 + monthly_growth_rate)
    # Add opportunity conversion (assume 20% of top opportunities convert in 60 days)
    day60 = day30 * (1 + monthly_growth_rate) + opportunity_value * 0.2
    day90 = day60 * (1 + monthly_growth_rate) + opportunity_value * 0.3

    return {
        "current_monthly_usd": round(current_monthly, 2),
        "projected_30d_usd": round(day30, 2),
        "projected_60d_usd": round(day60, 2),
        "projected_90d_usd": round(day90, 2),
        "potential_monthly_usd": potential_monthly,
        "opportunity_pipeline_usd": opportunity_value,
        "days_to_1000_monthly": max(0, round(
            30 * (1000 - current_monthly) / max(day30 - current_monthly, 1)
        )) if day30 > current_monthly else 999,
        "active_streams": active_count,
        "ready_streams_unlocked": ready_count,
        "methodology": "15% MoM growth rate + opportunity conversion at 20%/30% by day 60/90",
    }


def generate_circulation_report(pools: dict, leaks: list, plugged: list, velocity: dict, projections: dict) -> str:
    """Generate the circulation report narrative."""
    total_balance = velocity["current_balance_usd"]
    leak_value = sum(l.get("value_stuck_usd", 0) for l in leaks)
    high_severity = [l for l in leaks if l.get("severity") == "high"]

    lines = [
        "=" * 60,
        "SOLARPUNK CIRCULATION REPORT",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "=" * 60,
        "",
        "MONEY FLOW STATE:",
        f"  Current balance across all pools: ${total_balance:.2f}",
        f"  Total money in: ${velocity['total_in_usd']:.2f}",
        f"  Total money deployed: ${velocity['total_out_usd']:.2f}",
        f"  Circulation velocity: {velocity['velocity']:.2f}x ({velocity['assessment']})",
        f"  Multiplier effect: {velocity['multiplier_effect']:.2f}x (each dollar creates this much value)",
        "",
        "POOL BALANCES:",
    ]
    for name, pool in pools.items():
        bal = pool.get("balance_usd", 0)
        tgt = pool.get("target_usd", 0)
        pct = (bal / tgt * 100) if tgt > 0 else 100
        status = "FUNDED" if pct >= 100 else f"{pct:.0f}% of target"
        lines.append(f"  {name:15s}: ${bal:.2f} ({status})")

    lines += [
        "",
        f"LEAKS DETECTED: {len(leaks)} (${leak_value:.0f} stagnant)",
    ]
    for leak in leaks:
        sev = "!!!" if leak["severity"] == "high" else "!!" if leak["severity"] == "medium" else "!"
        lines.append(f"  [{sev}] {leak['type']}: {leak['description'][:60]}")
        lines.append(f"      FIX: {leak['fix']}")

    lines += [
        "",
        f"LEAKS PLUGGED: {len(plugged)} trigger files created",
        "",
        "REVENUE PROJECTIONS:",
        f"  Current monthly:    ${projections['current_monthly_usd']:.2f}",
        f"  30-day projection:  ${projections['projected_30d_usd']:.2f}",
        f"  60-day projection:  ${projections['projected_60d_usd']:.2f}",
        f"  90-day projection:  ${projections['projected_90d_usd']:.2f}",
        f"  Days to $1000/mo:   {projections['days_to_1000_monthly']}",
        f"  Total potential:    ${projections['potential_monthly_usd']:.0f}/mo",
        "",
        "CIRCULATION RULES FIRING:",
    ]
    for rule_id, rule in CIRCULATION_RULES.items():
        lines.append(f"  → {rule['action']}")

    lines += [
        "",
        "TOP ACTIONS TO ACCELERATE CIRCULATION:",
    ]
    if high_severity:
        for i, leak in enumerate(high_severity[:3], 1):
            lines.append(f"  {i}. {leak['fix']}")
    else:
        lines.append("  1. Keep all engines running — circulation is healthy")
        lines.append("  2. Run EASY_MONEY_FINDER.py to find new opportunities")
        lines.append("  3. Run DISTRIBUTED_FORGE.py to build new revenue capabilities")

    lines += [
        "",
        "THE LOOP:",
        "  revenue → pools → labor → tasks → proofs → more revenue → more pools",
        "  Every dollar circulates. Every worker is paid. Every crisis receives aid.",
        "=" * 60,
    ]

    return "\n".join(lines)


def run():
    print("CIRCULATION_ENGINE: Mapping money flow and plugging leaks...")
    ts = datetime.now(timezone.utc).isoformat()

    # Load all data
    snapshot = load_data_snapshot()
    print(f"  Loaded {len(snapshot)} data sources")

    # Extract pool state
    pools = extract_pool_state(snapshot)
    print(f"  Pools: {list(pools.keys())}")

    # Identify leaks
    leaks = identify_leaks(snapshot, pools)
    print(f"  Leaks found: {len(leaks)}")

    # Plug leaks
    plugged = plug_leaks(leaks)
    print(f"  Leaks plugged: {len(plugged)}")

    # Calculate velocity
    velocity = calculate_circulation_velocity(snapshot, pools)
    print(f"  Circulation velocity: {velocity['velocity']:.2f}x ({velocity['assessment']})")

    # Project revenue
    projections = project_revenue(snapshot)
    print(f"  Current monthly: ${projections['current_monthly_usd']:.2f}")
    print(f"  30-day projection: ${projections['projected_30d_usd']:.2f}")
    print(f"  Days to $1000/mo: {projections['days_to_1000_monthly']}")

    # Generate report
    report_text = generate_circulation_report(pools, leaks, plugged, velocity, projections)

    # Save circulation state
    state = {
        "generated_at": ts,
        "pools": pools,
        "leaks_detected": len(leaks),
        "leaks": leaks,
        "plugged": plugged,
        "velocity": velocity,
        "projections": projections,
        "circulation_rules": {k: v["action"] for k, v in CIRCULATION_RULES.items()},
    }
    (DATA / "circulation_state.json").write_text(json.dumps(state, indent=2))

    # Save report
    (DATA / "circulation_report.json").write_text(json.dumps({
        "generated_at": ts,
        "report": report_text,
        "summary": {
            "total_balance_usd": velocity["current_balance_usd"],
            "leaks_detected": len(leaks),
            "leaks_plugged": len(plugged),
            "velocity": velocity["velocity"],
            "velocity_assessment": velocity["assessment"],
            "days_to_1000": projections["days_to_1000_monthly"],
        },
    }, indent=2))

    # Also write as text file for human readability
    (DATA / "circulation_report.txt").write_text(report_text)

    print(f"\nCIRCULATION_ENGINE: Done.")
    print(f"\n{report_text}")
    return state


if __name__ == "__main__":
    run()
