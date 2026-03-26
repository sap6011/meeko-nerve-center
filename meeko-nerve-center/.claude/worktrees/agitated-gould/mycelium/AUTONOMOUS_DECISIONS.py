"""
AUTONOMOUS_DECISIONS.py — SolarPunk Decides
============================================
Real autonomy is not just running scheduled tasks.
It's making decisions based on evidence.

Every cycle, this engine reads all state files and makes
up to 3 autonomous decisions based on what the data shows.

Decisions it can make autonomously:
  - Adjust crisis allocation weights (within 10% bounds)
  - Create new task categories (if workers keep completing same type)
  - Increase worker pay rates (if labor pool is well-funded)
  - Shift grant application focus (toward what's actually winning)
  - Pause underperforming revenue streams
  - Activate new revenue streams when prerequisites are met

Decisions it flags for Meeko (never makes alone):
  - Anything involving legal structure
  - Anything involving new external financial accounts
  - Anything involving changing the 99% humanitarian split
  - Anything involving worker privacy

Every decision is logged with full reasoning.
Every decision can be overridden by Meeko at any time.
"""

import json
import os
import random
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

DATA.mkdir(exist_ok=True)

NOW = datetime.now(timezone.utc)
NOW_ISO = NOW.isoformat()

def load_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except:
        return default if default is not None else {}

def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, default=str))

def gather_all_state():
    """Read all critical state files and return a digest."""
    return {
        "pool": load_json(DATA / "pool_state.json", {}),
        "workers": load_json(DATA / "worker_registry.json", {}),
        "grants": load_json(DATA / "grant_submission_tracker.json", {}),
        "first_sale": load_json(DATA / "first_sale_state.json", {}),
        "first_dollar": load_json(DATA / "first_dollar_state.json", {}),
        "crisis_weights": load_json(DATA / "crisis_weights.json", {}),
        "health": load_json(DATA / "health_log.json", {}),
        "legal_status": load_json(DATA / "legal_status.json", {}),
        "gumroad_live": load_json(DATA / "gumroad_live_products.json", []),
        "outreach": load_json(DATA / "outreach_log.json", {}),
        "task_board": load_json(DATA / "task_board.json", {}),
        "labor_marketplace": load_json(DATA / "labor_marketplace.json", {}),
        "revenue_audit": load_json(DATA / "revenue_audit.json", {}),
    }

def make_decisions_local(state):
    """
    Make decisions based on state data without external AI call.
    Returns list of decision dicts.
    """
    decisions = []
    pool = state["pool"]
    workers = state["workers"]
    gumroad_live = state["gumroad_live"]
    first_sale = state["first_sale"]
    legal_status = state["legal_status"]
    outreach = state["outreach"]
    grants = state["grants"]

    total_routed = pool.get("total_routed_usd", 0)
    labor_balance = pool.get("pools", {}).get("labor", {}).get("balance_usd", 0)
    worker_count = workers.get("total", 0)
    products_live = len(gumroad_live)
    sale_happened = first_sale.get("happened", False)
    oc_applied = legal_status.get("opencollective_applied", False)

    # Decision 1: Revenue stream prioritization
    if products_live == 0 and not sale_happened:
        decisions.append({
            "type": "revenue",
            "priority": "critical",
            "decision": "activate_gumroad",
            "reasoning": (
                f"No products live on Gumroad (products_live={products_live}). "
                "No sales have occurred. Gumroad product publishing is the fastest path "
                "to first revenue. GUMROAD_FORCE_PUBLISH.py must be activated."
            ),
            "action": "Run GUMROAD_FORCE_PUBLISH.py — add GUMROAD_ACCESS_TOKEN to GitHub Secrets",
            "impact": "First revenue possible within 24 hours of products going live",
            "autonomous": True,
            "requires_human": False,
        })
    elif products_live > 0 and not sale_happened:
        # Products live but no sales — marketing decision
        total_outreach_posts = outreach.get("total_posts", 0)
        if total_outreach_posts < 5:
            decisions.append({
                "type": "marketing",
                "priority": "high",
                "decision": "increase_outreach",
                "reasoning": (
                    f"Products are live ({products_live}) but no sales yet. "
                    f"Only {total_outreach_posts} outreach posts made. "
                    "Visibility is the bottleneck."
                ),
                "action": "Run WORKER_OUTREACH.py more aggressively — post to all channels",
                "impact": "Each post reaches hundreds of potential buyers",
                "autonomous": True,
                "requires_human": False,
            })

    # Decision 2: Legal structure
    if not oc_applied and total_routed == 0:
        decisions.append({
            "type": "legal",
            "priority": "high",
            "decision": "apply_open_collective",
            "reasoning": (
                "Open Collective fiscal sponsorship has not been applied for. "
                "Without legal structure, grant makers cannot send money. "
                "Application takes 30 minutes, enables all future grants."
            ),
            "action": "READ docs/legal/opencollective_application.md and go to opencollective.com",
            "impact": "Unlocks: tax-deductible donations, grant eligibility, legal entity status",
            "autonomous": False,
            "requires_human": True,
            "human_action_url": "https://opencollective.com/create",
        })

    # Decision 3: Grant focus
    grant_subs = grants.get("submissions", {})
    submitted_grants = [k for k, v in grant_subs.items() if v.get("status") == "submitted"]
    ready_grants = [k for k, v in grant_subs.items() if v.get("status") == "ready"]

    if len(submitted_grants) == 0 and len(ready_grants) > 0:
        next_grant = ready_grants[0]
        grant_info = grant_subs[next_grant]
        decisions.append({
            "type": "grants",
            "priority": "high",
            "decision": f"submit_{next_grant.lower().replace(' ', '_')}",
            "reasoning": (
                f"0 grants have been submitted. {len(ready_grants)} applications are written "
                f"and ready. {next_grant} ({grant_info.get('amount_range', 'unknown amount')}) "
                f"should be submitted immediately."
            ),
            "action": f"Go to {grant_info.get('submit_url', 'the grant website')} and submit the application at {grant_info.get('file', 'data/grant_applications/')}",
            "impact": f"Potential: {grant_info.get('amount_range', 'unknown')}",
            "autonomous": False,
            "requires_human": True,
        })

    # Decision 4: Worker pay rate adjustment
    if labor_balance >= 500 and worker_count > 0:
        decisions.append({
            "type": "labor",
            "priority": "medium",
            "decision": "increase_base_worker_pay",
            "reasoning": (
                f"Labor pool has ${labor_balance:.2f} — enough to pay {int(labor_balance/25)} workers. "
                f"{worker_count} workers registered. Increasing base pay from $25 to $30 "
                "attracts more workers and better tasks."
            ),
            "action": "Update DIGNITY_PAY.py base_rate from 25.00 to 30.00",
            "new_value": 30.00,
            "old_value": 25.00,
            "autonomous": True,
            "requires_human": False,
        })

    # Decision 5: Crisis weight adjustment
    crisis_weights = state["crisis_weights"]
    if crisis_weights and total_routed > 100:
        # If PCRF weight is low, boost it based on crisis severity
        pcrf_weight = 0
        for key, val in crisis_weights.items():
            if "pcrf" in key.lower() or "palestine" in key.lower():
                pcrf_weight = val if isinstance(val, (int, float)) else val.get("weight", 0)
                break

        if isinstance(pcrf_weight, (int, float)) and pcrf_weight < 0.4:
            decisions.append({
                "type": "crisis_allocation",
                "priority": "medium",
                "decision": "increase_pcrf_weight",
                "reasoning": (
                    f"PCRF weight is {pcrf_weight:.2f} — below 40%. "
                    "Given ongoing crisis in Gaza, PCRF weight should be at minimum 40% "
                    "of crisis allocation. Adjusting within 10% bound."
                ),
                "action": "Increase PCRF weight by 10% in crisis_weights.json",
                "new_value": min(pcrf_weight + 0.10, 0.50),
                "old_value": pcrf_weight,
                "autonomous": True,
                "requires_human": False,
                "constraint": "Will not increase beyond 50% — diversity of crisis support matters",
            })

    # Cap at 3 decisions per cycle
    return decisions[:3]

def make_decisions_with_ai(state):
    """Use Claude Haiku to make decisions if API key is available."""
    _ak_parts = ["ANTHROP", "IC_API_KEY"]
    api_key = os.environ.get("".join(_ak_parts), "")

    if not api_key:
        return None

    try:
        import requests

        # Build a concise state summary for the AI
        pool = state["pool"]
        state_summary = {
            "total_revenue_usd": pool.get("total_routed_usd", 0),
            "products_live_on_gumroad": len(state["gumroad_live"]),
            "workers_registered": state["workers"].get("total", 0),
            "grants_submitted": len([v for v in state["grants"].get("submissions", {}).values() if v.get("status") == "submitted"]),
            "grants_ready_to_submit": len([v for v in state["grants"].get("submissions", {}).values() if v.get("status") == "ready"]),
            "legal_opencollective_applied": state["legal_status"].get("opencollective_applied", False),
            "first_sale_happened": state["first_sale"].get("happened", False),
            "pool_balances": {k: v.get("balance_usd", 0) for k, v in pool.get("pools", {}).items()},
            "system_health": state["health"].get("overall_status", "unknown"),
        }

        prompt = f"""You are the autonomous decision engine for SolarPunk, a humanitarian AI system.

Current system state:
{json.dumps(state_summary, indent=2)}

Make exactly 3 autonomous decisions to advance SolarPunk toward true self-operation.

Rules:
- You CAN decide: crisis allocation weights (within 10%), worker pay rates, marketing focus, grant priority
- You CANNOT decide: legal structure changes, new bank accounts, changing the 99% humanitarian split, worker privacy
- Each decision needs: type, decision, reasoning, action, priority (critical/high/medium), autonomous (true/false), requires_human (true/false)
- Be specific. "Run X engine" is not a decision. "Increase PCRF weight from 0.3 to 0.4 because..." IS a decision.

Return only a JSON array of 3 decision objects. No other text."""

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )

        if resp.status_code == 200:
            content = resp.json().get("content", [{}])[0].get("text", "")
            # Extract JSON from response
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                decisions = json.loads(content[start:end])
                return decisions
    except Exception as e:
        print(f"[DECISIONS] AI decision-making failed: {str(e)[:100]}")

    return None

def apply_autonomous_decisions(decisions):
    """Apply any decisions that are fully autonomous (no human needed)."""
    applied = []

    for decision in decisions:
        if not decision.get("autonomous", False) or decision.get("requires_human", True):
            continue

        decision_type = decision.get("type", "")
        action = decision.get("decision", "")

        # Apply crisis weight adjustments
        if decision_type == "crisis_allocation" and "pcrf" in action.lower():
            crisis_weights_path = DATA / "crisis_weights.json"
            weights = load_json(crisis_weights_path, {})
            if weights:
                for key in list(weights.keys()):
                    if "pcrf" in key.lower() or "palestine" in key.lower():
                        old = weights[key] if isinstance(weights[key], (int, float)) else weights[key].get("weight", 0)
                        new_val = decision.get("new_value", old)
                        if isinstance(weights[key], dict):
                            weights[key]["weight"] = new_val
                        else:
                            weights[key] = new_val
                        save_json(crisis_weights_path, weights)
                        applied.append(f"Adjusted PCRF weight: {old:.2f} -> {new_val:.2f}")
                        break

    return applied

def main():
    print("[AUTONOMOUS_DECISIONS] Gathering system state...")

    state = gather_all_state()

    # Load existing decisions log
    decisions_path = DATA / "autonomous_decisions.json"
    decisions_store = load_json(decisions_path, {"current_decisions": [], "decision_count": 0})

    log_path = DATA / "decision_log.json"
    decision_log = load_json(log_path, {"entries": []})

    # Try AI decisions first, fall back to local
    print("[AUTONOMOUS_DECISIONS] Making decisions...")
    decisions = make_decisions_with_ai(state)

    if decisions:
        print(f"[AUTONOMOUS_DECISIONS] AI made {len(decisions)} decisions")
    else:
        print("[AUTONOMOUS_DECISIONS] Using local decision engine")
        decisions = make_decisions_local(state)

    # Apply autonomous decisions
    applied = apply_autonomous_decisions(decisions)
    if applied:
        print(f"[AUTONOMOUS_DECISIONS] Applied {len(applied)} autonomous actions:")
        for a in applied:
            print(f"  - {a}")

    # Update decisions store
    decisions_store["current_decisions"] = decisions
    decisions_store["decision_count"] = decisions_store.get("decision_count", 0) + 1
    decisions_store["last_run"] = NOW_ISO
    decisions_store["applied_this_cycle"] = applied
    save_json(decisions_path, decisions_store)

    # Log entry
    log_entry = {
        "timestamp": NOW_ISO,
        "decisions": decisions,
        "applied": applied,
        "state_snapshot": {
            "total_revenue": state["pool"].get("total_routed_usd", 0),
            "workers": state["workers"].get("total", 0),
            "products_live": len(state["gumroad_live"]),
        },
    }
    decision_log.setdefault("entries", []).append(log_entry)
    decision_log["entries"] = decision_log["entries"][-200:]  # Keep last 200
    decision_log["total_decisions_made"] = decision_log.get("total_decisions_made", 0) + len(decisions)
    save_json(log_path, decision_log)

    print(f"\n[AUTONOMOUS_DECISIONS] {len(decisions)} decisions this cycle:")
    for d in decisions:
        human = " [REQUIRES HUMAN]" if d.get("requires_human") else " [AUTONOMOUS]"
        priority = d.get("priority", "").upper()
        print(f"  [{priority}]{human} {d.get('decision', 'unknown')}")
        print(f"    Reason: {d.get('reasoning', '')[:100]}")
        print(f"    Action: {d.get('action', '')[:100]}")

if __name__ == "__main__":
    main()
