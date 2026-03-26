#!/usr/bin/env python3
"""
GRAND_CONDUCTOR.py — The Brain of All SolarPunk Dimensions
===========================================================
Reads every state file. Understands every dimension.
Decides what needs to happen this cycle. In what order. With what priority.

The 12 dimensions of SolarPunk:
  1. REVENUE      — Products, grants, affiliates, bounties
  2. LABOR        — Workers, tasks, verification, payment
  3. CRISIS       — Routing, allocation, proof, amplification
  4. PRINT        — 3D printing, prosthetics, OctoEverywhere
  5. SWARM        — Agents, A2A, distributed forge, queries
  6. KNOWLEDGE    — Harvest, synthesize, learn, remember
  7. PRESENCE     — Overflow tracking, auto-announce, proof
  8. SELF         — Problem solving, self-building, healing
  9. MARKET       — Prediction intelligence, Unusual Whales, SAM.gov
  10. COMMUNITY   — Onboarding, mutual aid, relationships
  11. PUBLIC_GOODS — RPGF, Octant, Gitcoin, retroactive proof
  12. INFRA       — AI routing, cost optimization, stability

Each cycle: reads all state → scores each dimension → outputs CYCLE_PLAN
The CYCLE_PLAN tells GRAND_UNIFIED_LOOP exactly what to run and in what order.

Writes: data/cycle_plan.json, data/dimension_health.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)


# ── Data loader ───────────────────────────────────────────────────────────────
def load_json(filename: str, default=None):
    """Safely load a JSON file from the data directory."""
    f = DATA / filename
    if not f.exists():
        return default if default is not None else {}
    try:
        return json.loads(f.read_text())
    except Exception:
        return default if default is not None else {}


def load_json_list(filename: str) -> list:
    result = load_json(filename, [])
    return result if isinstance(result, list) else []


# ── Earth phase ───────────────────────────────────────────────────────────────
def get_earth_phase() -> str:
    """Read bioregional clock for current earth phase."""
    clock = load_json("earth_clock.json")
    phase = clock.get("current_phase", "")
    hour = datetime.now(timezone.utc).hour
    if phase:
        return phase.upper().replace(" ", "_")
    if 6 <= hour < 12:
        return "MORNING_BUILD"
    elif 12 <= hour < 18:
        return "SOLAR_PEAK"
    elif 18 <= hour < 22:
        return "EVENING_FLOW"
    else:
        return "DEEP_CYCLE"


# ── Dimension scorers ─────────────────────────────────────────────────────────
def score_revenue(pool: dict, first_dollar: dict) -> dict:
    first_happened = first_dollar.get("happened", False) or first_dollar.get("first_dollar_earned", False)
    total_routed   = pool.get("total_routed_usd", 0)
    flywheel       = load_json("flywheel_state.json")
    revenue        = float(flywheel.get("current_balance", total_routed))

    if not first_happened:
        score    = 5
        critical = True
        priority = 1
        note     = "CRITICAL: First dollar not yet earned"
    else:
        score    = min(100, int(revenue / 10))
        critical = revenue < 10
        priority = 1 if critical else 3
        note     = f"${revenue:.2f} total revenue routed"

    return {
        "score":    score,
        "critical": critical,
        "note":     note,
        "engines":  ["FIRST_DOLLAR", "GUMROAD_ENGINE", "REVENUE_ARCHITECT",
                     "CIRCULATION_ENGINE", "EASY_MONEY_FINDER"],
        "priority": priority,
    }


def score_labor(pool: dict) -> dict:
    labor_bal  = pool.get("pools", {}).get("labor", {}).get("balance_usd", 0)
    reg        = load_json("worker_registry.json")
    total_w    = reg.get("total", 0)
    pay_log    = load_json("payment_log.json")
    paid_count = len(pay_log.get("payments", []))
    critical   = labor_bal < 50

    return {
        "score":    min(100, int(labor_bal / 5)),
        "critical": critical,
        "note":     f"Labor pool ${labor_bal:.2f} | {total_w} workers | {paid_count} paid",
        "engines":  ["LABOR_MARKETPLACE", "WORKER_ONBOARDING", "TASK_VERIFIER",
                     "DIGNITY_PAY", "TELEGRAM_WORKER_BOT", "RENTAHUMAN_BRIDGE"],
        "priority": 1 if critical else 2,
    }


def score_crisis(pool: dict) -> dict:
    crisis_bal   = pool.get("pools", {}).get("crisis", {}).get("balance_usd", 0)
    allocation   = load_json("crisis_allocation.json")
    hum_pool     = allocation.get("humanitarian_pool_usd", 0)
    allocs       = allocation.get("allocations", [])
    total_routed = sum(a.get("amount_usd", 0) for a in allocs)
    score        = min(100, 50 + int(total_routed * 2)) if total_routed > 0 else 50

    return {
        "score":    score,
        "critical": False,  # crisis engine always runs
        "note":     f"Crisis pool ${crisis_bal:.2f} | ${hum_pool:.4f} in humanitarian pool",
        "engines":  ["CRISIS_ROUTER", "PROOF_OF_IMPACT", "RETROACTIVE_PROOF"],
        "priority": 2,  # always high priority
    }


def score_print() -> dict:
    print_state = load_json("print_relay_state.json")
    dispatched  = print_state.get("total_parts_dispatched", 0)
    connected   = print_state.get("printers_connected", 0)
    score       = min(100, connected * 25 + dispatched * 5)

    return {
        "score":    score,
        "critical": False,
        "note":     f"{connected} printers | {dispatched} parts dispatched",
        "engines":  ["PRINT_RELAY_ENGINE"],
        "priority": 4,
    }


def score_swarm() -> dict:
    swarm_state = load_json("swarm_state.json")
    agents      = swarm_state.get("active_agents", 0)
    queries     = swarm_state.get("total_queries", 0)
    peers       = load_json("a2a_peers.json")
    peer_count  = len(peers) if isinstance(peers, list) else peers.get("total", 0)
    score       = min(100, agents * 10 + peer_count * 2)

    return {
        "score":    score,
        "critical": False,
        "note":     f"{agents} agents | {peer_count} A2A peers | {queries} queries",
        "engines":  ["SWARM_ORACLE", "SWARM_QUERY", "SWARM_AMPLIFIER",
                     "AGENT_NEXUS", "DISTRIBUTED_FORGE"],
        "priority": 3,
    }


def score_knowledge() -> dict:
    knowledge    = load_json("knowledge_graph.json")
    nodes        = knowledge.get("nodes", 0) if isinstance(knowledge, dict) else 0
    bank         = DATA / "knowledge_bank.txt"
    bank_size    = bank.stat().st_size if bank.exists() else 0
    lessons      = load_json_list("lessons.json")
    score        = min(100, len(lessons) * 2 + int(bank_size / 1000))

    return {
        "score":    score,
        "critical": False,
        "note":     f"{len(lessons)} lessons | {nodes} knowledge nodes | {bank_size} bytes banked",
        "engines":  ["KNOWLEDGE_SYNTHESIZER", "X_KNOWLEDGE_HARVESTER"],
        "priority": 3,
    }


def score_presence() -> dict:
    overflow     = load_json("overflow_events.json")
    events       = overflow.get("overflow_events", [])
    cross        = load_json("cross_post_log.json")
    total_posted = cross.get("total_posted", 0)
    score        = min(100, len(events) * 5 + total_posted * 2)

    return {
        "score":    score,
        "critical": False,
        "note":     f"{len(events)} overflow events | {total_posted} posts sent",
        "engines":  ["AUTO_ANNOUNCE", "FEDIVERSE_PUBLISHER", "PLANETARY_OVERFLOW"],
        "priority": 3,
    }


def score_self() -> dict:
    prob_log     = load_json("problem_log.json")
    fixed        = sum(e.get("fixed", 0) for e in prob_log.get("log", []))
    healer       = load_json("auto_healer_report.json")
    healed       = healer.get("total_healed", 0)
    engines_f    = sorted(Path("mycelium").glob("*.py")) if Path("mycelium").exists() else []
    engine_count = len(engines_f)
    score        = min(100, 20 + fixed * 5 + healed * 3 + int(engine_count / 3))

    return {
        "score":    score,
        "critical": False,
        "note":     f"{engine_count} engines | {fixed} problems fixed | {healed} self-heals",
        "engines":  ["PROBLEM_SOLVER_PRIME", "AI_ROUTER", "ENGINE_SANITIZER",
                     "AUTO_HEALER", "LOOP_CONDUCTOR"],
        "priority": 2,
    }


def score_market() -> dict:
    market_intel = load_json("market_intelligence.json")
    signals      = market_intel.get("signals_processed", 0)
    grants       = load_json("grants_found.json")
    grant_count  = len(grants) if isinstance(grants, list) else grants.get("total", 0)
    score        = min(100, signals * 2 + grant_count * 5)

    return {
        "score":    score,
        "critical": False,
        "note":     f"{signals} market signals | {grant_count} grants found",
        "engines":  ["UNUSUAL_WHALES_MCP", "PREDICTION_INTELLIGENCE",
                     "FREE_INFRA_SCANNER", "SAMGOV_HARVESTER"],
        "priority": 3,
    }


def score_community() -> dict:
    mutual_aid   = load_json("mutual_aid_summary.json")
    abundance    = mutual_aid.get("abundance_score", 0)
    members      = mutual_aid.get("active_givers", 0)
    reg          = load_json("worker_registry.json")
    workers      = reg.get("total", 0)
    score        = min(100, int(abundance) + workers * 5 + members * 3)

    return {
        "score":    score,
        "critical": False,
        "note":     f"Abundance score: {abundance} | {members} active | {workers} workers",
        "engines":  ["WORKER_ONBOARDING", "RENTAHUMAN_BRIDGE"],
        "priority": 4,
    }


def score_public_goods() -> dict:
    proof_ledger  = load_json("proof_ledger.json")
    proofs        = len(proof_ledger) if isinstance(proof_ledger, list) else proof_ledger.get("total", 0)
    grant_tracker = load_json("grant_submission_tracker.json")
    submitted     = grant_tracker.get("total_submitted", 0)
    score         = min(100, proofs * 3 + submitted * 10)

    return {
        "score":    score,
        "critical": False,
        "note":     f"{proofs} proofs | {submitted} grant apps submitted",
        "engines":  ["PUBLIC_GOODS_NETWORK", "RETROACTIVE_PROOF",
                     "GRANT_HUNTER", "GRANT_AUTO_SUBMITTER"],
        "priority": 4,
    }


def score_infra(pool: dict) -> dict:
    infra_bal     = pool.get("pools", {}).get("infrastructure", {}).get("balance_usd", 0)
    sanitizer     = load_json("sanitizer_report.json")
    errors_fixed  = sanitizer.get("total_fixed", 0)
    ai_router     = load_json("ai_router_state.json") if (DATA / "ai_router_state.json").exists() else {}
    cost_saved    = ai_router.get("total_saved_usd", 0)
    score         = min(100, int(infra_bal * 2) + errors_fixed * 2 + int(cost_saved * 5))

    return {
        "score":    score,
        "critical": infra_bal < 1,
        "note":     f"Infra pool ${infra_bal:.2f} | {errors_fixed} errors fixed | ${cost_saved:.2f} AI costs saved",
        "engines":  ["AI_ROUTER", "ENGINE_SANITIZER", "FREE_INFRA_SCANNER"],
        "priority": 2,
    }


# ── Master scorer ─────────────────────────────────────────────────────────────
def score_all_dimensions() -> dict:
    pool        = load_json("pool_state.json")
    first_dol   = load_json("first_dollar_state.json")
    if not first_dol:
        first_dol = load_json("first_sale_state.json")

    scores = {
        "revenue":      score_revenue(pool, first_dol),
        "labor":        score_labor(pool),
        "crisis":       score_crisis(pool),
        "print":        score_print(),
        "swarm":        score_swarm(),
        "knowledge":    score_knowledge(),
        "presence":     score_presence(),
        "self":         score_self(),
        "market":       score_market(),
        "community":    score_community(),
        "public_goods": score_public_goods(),
        "infra":        score_infra(pool),
    }
    return scores


# ── Cycle plan builder ────────────────────────────────────────────────────────
def build_cycle_plan(scores: dict) -> dict:
    critical    = [d for d, s in scores.items() if s.get("critical")]
    high_prio   = [d for d, s in scores.items() if s.get("priority") == 2 and not s.get("critical")]
    normal      = [d for d, s in scores.items() if s.get("priority") == 3]
    low_prio    = [d for d, s in scores.items() if s.get("priority") == 4]

    # Flatten engines for each priority tier
    def _engines(dims):
        result = []
        seen   = set()
        for d in dims:
            for e in scores[d].get("engines", []):
                if e not in seen:
                    result.append(e)
                    seen.add(e)
        return result

    critical_engines   = _engines(critical)
    high_prio_engines  = _engines(high_prio)
    normal_engines     = _engines(normal)
    low_prio_engines   = _engines(low_prio)

    # Always-run engines
    always = ["POOL_MANAGER", "CRISIS_ROUTER", "AUTO_ANNOUNCE"]
    sequence = (
        critical_engines
        + [e for e in always if e not in critical_engines]
        + [e for e in high_prio_engines if e not in critical_engines and e not in always]
        + [e for e in normal_engines   if e not in critical_engines + high_prio_engines + always]
        + [e for e in low_prio_engines if e not in critical_engines + high_prio_engines + normal_engines + always]
    )
    # Deduplicate while preserving order
    seen    = set()
    seq_deduped = []
    for e in sequence:
        if e not in seen:
            seq_deduped.append(e)
            seen.add(e)

    overall_health = int(sum(s.get("score", 0) for s in scores.values()) / len(scores))

    # Next cycle focus
    if critical:
        focus = f"{', '.join(critical)} — CRITICAL: needs immediate attention"
    elif high_prio:
        score_vals = {d: scores[d].get("score", 0) for d in high_prio}
        weakest    = min(score_vals, key=score_vals.get)
        focus      = f"{scores[weakest]['note']}"
    else:
        focus = "all dimensions healthy — optimize and amplify"

    return {
        "cycle_at":              datetime.now(timezone.utc).isoformat(),
        "earth_phase":           get_earth_phase(),
        "critical_dimensions":   critical,
        "high_priority":         high_prio,
        "normal":                normal,
        "low_priority":          low_prio,
        "recommended_sequence":  seq_deduped,
        "skip_this_cycle":       [],
        "dimension_scores":      {d: {"score": s.get("score"), "note": s.get("note"), "priority": s.get("priority")} for d, s in scores.items()},
        "overall_health":        overall_health,
        "next_cycle_focus":      focus,
    }


# ── Entry point ───────────────────────────────────────────────────────────────
def run():
    print("🧠 GRAND_CONDUCTOR: Reading all 12 dimensions...")

    scores     = score_all_dimensions()
    cycle_plan = build_cycle_plan(scores)

    # Save cycle plan
    (DATA / "cycle_plan.json").write_text(json.dumps(cycle_plan, indent=2))

    # Save dimension health (full detail)
    dimension_health = {
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "overall_health": cycle_plan["overall_health"],
        "earth_phase":    cycle_plan["earth_phase"],
        "dimensions":     scores,
        "critical_count": len(cycle_plan["critical_dimensions"]),
        "summary": {d: s.get("score", 0) for d, s in scores.items()},
    }
    (DATA / "dimension_health.json").write_text(json.dumps(dimension_health, indent=2))

    # Print report
    print(f"\n  🌐 GRAND CYCLE PLAN — {cycle_plan['earth_phase']}")
    print(f"  Overall health: {cycle_plan['overall_health']}/100")
    print(f"\n  Dimension scores:")
    for dim, score in sorted(scores.items(), key=lambda x: x[1].get("score", 0)):
        s   = score.get("score", 0)
        emoji = "🟢" if s >= 70 else "🟡" if s >= 30 else "🔴"
        crit  = " ⚠️  CRITICAL" if score.get("critical") else ""
        print(f"    {emoji} {dim:15s}: {s:3d}/100{crit}")
        print(f"         {score.get('note', '')}")

    if cycle_plan["critical_dimensions"]:
        print(f"\n  🔴 CRITICAL: {', '.join(cycle_plan['critical_dimensions'])}")
    print(f"\n  Next focus: {cycle_plan['next_cycle_focus']}")
    print(f"\n  Sequence ({len(cycle_plan['recommended_sequence'])} engines):")
    for i, eng in enumerate(cycle_plan["recommended_sequence"][:15], 1):
        print(f"    {i:2d}. {eng}")
    if len(cycle_plan["recommended_sequence"]) > 15:
        print(f"    ... + {len(cycle_plan['recommended_sequence']) - 15} more")

    return cycle_plan


if __name__ == "__main__":
    run()
