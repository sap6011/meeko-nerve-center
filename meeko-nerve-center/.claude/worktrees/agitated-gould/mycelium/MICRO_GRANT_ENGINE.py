#!/usr/bin/env python3
"""
MICRO_GRANT_ENGINE.py — Small Money, Big Impact
================================================
$25 can plant a tree.
$50 can buy tools for a repair cafe.
$100 can fund a week of a community project.

Micro-grants are how growth pool overflow finds its way into the world.
No application. No committee. No waiting.

Eligibility:
  - Completed 5+ tasks on the labor marketplace
  - OR contributed code to the Distributed Forge
  - OR referred 3+ workers who completed tasks

Grant tiers:
  $25  — Tier 1: 5+ tasks, auto-approved
  $50  — Tier 2: 10+ tasks OR code contribution, auto-approved
  $100 — Tier 3: 20+ tasks OR community role, auto-approved

What grants fund (worker chooses):
  - Tools for physical tasks (seeds, equipment, protective gear)
  - Skills development (course fees, certification)
  - Community project seed funding (repair cafe, community garden)
  - Personal stability (rent gap, food, medicine) — no questions asked

Payment via same DIGNITY_PAY channels (CashApp, PayPal, Venmo, USDC, SolarPunk Credit)
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

GRANT_TIERS = {
    "tier1": {"amount_usd": 25,  "min_score": 50,  "min_tasks": 5},
    "tier2": {"amount_usd": 50,  "min_score": 100, "min_tasks": 10},
    "tier3": {"amount_usd": 100, "min_score": 200, "min_tasks": 20},
}


def load_json(path: Path, fallback=None):
    if fallback is None:
        fallback = {}
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return fallback


def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2))


def score_worker(worker: dict) -> int:
    """Score a worker: tasks*10 + code*25 + referrals*15."""
    tasks = worker.get("tasks_completed", 0)
    code = worker.get("code_contributions", 0)
    referrals = worker.get("referrals", 0)
    return tasks * 10 + code * 25 + referrals * 15


def assign_tier(worker: dict) -> str | None:
    """Return grant tier for worker, or None if not eligible."""
    score = score_worker(worker)
    tasks = worker.get("tasks_completed", 0)
    code = worker.get("code_contributions", 0)

    # Tier 3: 20+ tasks OR community role
    if tasks >= 20 or score >= 200 or worker.get("community_role"):
        return "tier3"
    # Tier 2: 10+ tasks OR code contribution
    if tasks >= 10 or code >= 1 or score >= 100:
        return "tier2"
    # Tier 1: 5+ tasks
    if tasks >= 5 or score >= 50:
        return "tier1"
    return None


def append_overflow_html(grant: dict):
    """Add a public entry to docs/overflow.html for the grant (anonymous unless opted in)."""
    overflow_html = DOCS / "overflow.html"

    # Build the entry
    show_name = grant.get("worker_display_name") if grant.get("public_opted_in") else "Anonymous contributor"
    tier = grant.get("tier", "tier1")
    amount = grant.get("grant_usd", 25)
    ts = grant.get("created_at", "")[:10]

    entry_html = f"""  <div class="grant-entry">
    <span class="grant-tier">{tier.upper()}</span>
    <span class="grant-name">{show_name}</span>
    <span class="grant-amount">${amount}</span>
    <span class="grant-date">{ts}</span>
  </div>\n"""

    # Create or append to overflow.html
    if overflow_html.exists():
        content = overflow_html.read_text()
        # Insert before closing </div> of grant-list if present
        if '<div class="grant-list">' in content:
            content = content.replace("</div>\n</body>", entry_html + "</div>\n</body>")
            overflow_html.write_text(content)
            return
    else:
        # Create minimal overflow page
        content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>SolarPunk — Overflow & Micro-Grants</title>
  <style>
    body {{ background:#080f0b; color:#c8f0d8; font-family:'Courier New',monospace; padding:24px; }}
    h1 {{ color:#00ff88; letter-spacing:3px; }}
    .grant-list {{ margin-top:24px; }}
    .grant-entry {{ display:flex; gap:16px; padding:8px 0; border-bottom:1px solid #1a3322; font-size:13px; }}
    .grant-tier {{ color:#44ffcc; min-width:60px; }}
    .grant-name {{ color:#c8f0d8; flex:1; }}
    .grant-amount {{ color:#00ff88; font-weight:bold; min-width:50px; }}
    .grant-date {{ color:#6a9a7a; font-size:11px; }}
    .philosophy {{ color:#6a9a7a; font-size:12px; margin-top:32px; font-style:italic; }}
  </style>
</head>
<body>
  <h1>Overflow &amp; Micro-Grants</h1>
  <p style="color:#6a9a7a;font-size:12px;">Growth pool overflow finds its way into the world. No application. No committee. No waiting.</p>
  <div class="grant-list">
{entry_html}  </div>
  <p class="philosophy">The faucet is always open. Connected means covered. Overflow finds its way.</p>
</body>
</html>"""
        overflow_html.write_text(content)
        return

    # Fallback: just append text
    overflow_html.write_text(overflow_html.read_text() + entry_html)


def run():
    print("🌱 MICRO_GRANT_ENGINE: Small money, big impact — processing grants...")

    now = datetime.now(timezone.utc).isoformat()

    # ── Load data ────────────────────────────────────────────────────────────
    micro_grants = load_json(DATA / "micro_grants.json", {"grants": []})
    worker_reg = load_json(DATA / "worker_registry.json", {"workers": []})
    workers = worker_reg.get("workers", [])

    pending_grants = [g for g in micro_grants.get("grants", []) if g.get("status") != "queued"]
    new_grant_log = []
    payment_entries = []

    # ── Score workers and assign grant tiers ────────────────────────────────
    already_granted = {g.get("worker_id") for g in micro_grants.get("grants", [])}

    for worker in workers:
        worker_id = worker.get("worker_id", "unknown")
        if worker_id in already_granted:
            continue  # Already received a grant this cycle

        tier = assign_tier(worker)
        if not tier:
            continue

        grant_usd = GRANT_TIERS[tier]["amount_usd"]
        score = score_worker(worker)

        grant = {
            "grant_id": f"grant_{worker_id[:8]}_{now[:10].replace('-', '')}",
            "worker_id": worker_id,
            "tier": tier,
            "grant_usd": grant_usd,
            "score": score,
            "tasks_completed": worker.get("tasks_completed", 0),
            "code_contributions": worker.get("code_contributions", 0),
            "referrals": worker.get("referrals", 0),
            "auto_approved": True,
            "created_at": now,
            "status": "queued",
            "public_opted_in": worker.get("public_profile", False),
            "worker_display_name": worker.get("display_name", ""),
        }

        new_grant_log.append(grant)

        # Add to payment queue for DIGNITY_PAY
        payment_entries.append({
            "worker_id": worker_id,
            "amount_usd": grant_usd,
            "reason": f"micro_grant_{tier}",
            "grant_id": grant["grant_id"],
            "queued_at": now,
            "status": "pending",
        })

        # Public HTML entry
        append_overflow_html(grant)

        print(f"  🌱 {tier.upper()} grant: ${grant_usd} → worker {worker_id[:8]}*** (score: {score})")

    # ── Persist grant log ────────────────────────────────────────────────────
    grant_log_file = DATA / "micro_grant_log.json"
    existing_log = load_json(grant_log_file, {"grants": [], "total_granted_usd": 0.0})
    existing_log.setdefault("grants", []).extend(new_grant_log)
    existing_log["total_granted_usd"] = round(
        existing_log.get("total_granted_usd", 0) + sum(g["grant_usd"] for g in new_grant_log), 4
    )
    existing_log["last_updated"] = now
    save_json(grant_log_file, existing_log)

    # ── Update micro_grants.json ─────────────────────────────────────────────
    micro_grants.setdefault("grants", []).extend(new_grant_log)
    micro_grants["last_updated"] = now
    save_json(DATA / "micro_grants.json", micro_grants)

    # ── Update payment queue ─────────────────────────────────────────────────
    if payment_entries:
        pq_file = DATA / "payment_queue.json"
        pq = load_json(pq_file, {"pending": [], "completed": []})
        pq.setdefault("pending", []).extend(payment_entries)
        save_json(pq_file, pq)
        print(f"  💸 {len(payment_entries)} payment entries added to queue for DIGNITY_PAY")

    total_granted = sum(g["grant_usd"] for g in new_grant_log)
    print(f"  ✅ {len(new_grant_log)} grants processed | ${total_granted:.2f} total")
    print(f"  💬 $25 can plant a tree. Overflow finds its way.")

    return {
        "generated_at": now,
        "grants_processed": len(new_grant_log),
        "total_granted_usd": total_granted,
        "payment_entries_queued": len(payment_entries),
    }


if __name__ == "__main__":
    run()
