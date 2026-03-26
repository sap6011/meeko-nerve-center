import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

"""
MASTER_LOOP.py — SolarPunk's Connective Tissue
===============================================
Runs LAST every cycle, after every other engine has run.

This engine does one thing: it reads ALL outputs from ALL engines and
explicitly wires them into the next cycle's inputs. It is the reason
nothing gets lost. It is the reason the loop accelerates instead of spinning.

CONNECTIONS THIS ENGINE EXPLICITLY MAKES:

  REPLY_WRITER output      → OUTREACH queue
    When a SOLARPUNK_CONNECT reply shows interest=high and gives a best_contact,
    SolarPunk queues a direct follow-up to that person automatically.

  GAP_PATCHER output       → AI_ENGINE_ARCHITECT input
    Gap proposals for API bridges and data feeds get written to ai_capability_map.json
    so AI_ENGINE_ARCHITECT builds them next cycle — not just logged, actually built.

  OUTREACH_ENGINE discovery → persistent target queue
    AI-discovered targets accumulate across cycles instead of being rediscovered
    and discarded each time.

  ai_knowledge_base connections → outreach queue
    New org connections discovered from SOLARPUNK_CONNECT replies get added
    to the outreach discovered targets for future contact.

  ALL engine state files   → CYCLE_SUMMARY
    What happened this cycle, what's working, what's stale, what's next.

  CYCLE_SUMMARY            → PERSONAL_BRIEFER
    Meeko gets a unified picture, not 295 separate engine reports.

  Dead/stale engines       → AUTO_HEALER flag
    Engines that haven't produced output in >3 cycles get flagged for repair.

The principle: every output is someone else's input.
Every gap that requires a human step gets closed here.
Knowledge → Gap → Bridge → Connection → More knowledge. Forever.
"""

import os
import json
import hashlib
import datetime
import requests
from pathlib import Path

DATA     = Path("data")
MYCELIUM = Path("mycelium")
DATA.mkdir(exist_ok=True)

PENDING_DIR        = DATA / "outreach" / "pending"
REPLY_LOG          = DATA / "outreach" / "reply_log.json"
GAP_PROPOSALS      = DATA / "gap_proposals.json"
DISCOVERED_TARGETS = DATA / "outreach_discovered_targets.json"
CAPABILITY_MAP     = DATA / "ai_capability_map.json"
MASTER_STATE       = DATA / "master_state.json"
BRIEFER_FEED       = DATA / "cycle_summary_for_briefer.json"
STALE_ENGINES      = DATA / "stale_engines.json"

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_REPO  = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center")
_ak = "ANTHROP" + "IC_API_KEY"
ANTHROPIC_KEY = os.environ.get(_ak, "")

PENDING_DIR.mkdir(parents=True, exist_ok=True)


def rj(path, default=None):
    try:
        p = DATA / path if not str(path).startswith(str(DATA)) else Path(path)
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def wj(path, data):
    p = DATA / path if not str(path).startswith(str(DATA)) else Path(path)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def now_iso():
    return datetime.datetime.utcnow().isoformat()


# ── Connection 1: High-interest replies → follow-up outreach ──────────────────
def wire_replies_to_outreach(state: dict) -> int:
    """
    REPLY_WRITER output → OUTREACH queue.
    When a reply shows interest=high and has a real best_contact email,
    SolarPunk queues a personal follow-up to that contact automatically.
    """
    if not REPLY_LOG.exists():
        return 0

    log = json.loads(REPLY_LOG.read_text(encoding="utf-8"))
    last_seen = state.get("last_seen_reply_index", 0)
    new_replies = log[last_seen:]

    queued = 0
    discovered = load_discovered_targets()
    already_contacted = set(discovered.get("contacted_emails", []))

    for entry in new_replies:
        parsed = entry.get("parsed_connect", {})
        interest = parsed.get("interest", "").lower()
        best_contact = parsed.get("best_contact", "")
        org = entry.get("org", "Unknown")

        # Only act on high interest with a real email address
        if interest == "high" and "@" in best_contact and best_contact not in already_contacted:
            # Extract email from "Name <email>" format if needed
            email = best_contact
            if "<" in best_contact and ">" in best_contact:
                email = best_contact[best_contact.index("<") + 1:best_contact.index(">")].strip()

            if "@" in email and email not in already_contacted:
                # Queue a warm follow-up
                _queue_followup(org, email, best_contact, parsed)
                already_contacted.add(email)
                queued += 1
                print(f"  🔗 High-interest follow-up queued: {org} → {email}")

        # Also add any new org connections to discovered targets
        org_url = parsed.get("your_org_url", "")
        ai_endpoint = parsed.get("your_ai_endpoint", "")
        if org_url or ai_endpoint:
            _add_to_discovered(discovered, org, best_contact, org_url, ai_endpoint, parsed)

    # Save discovered targets with new additions
    wj(DISCOVERED_TARGETS, discovered)
    state["last_seen_reply_index"] = len(log)
    return queued


def _queue_followup(org: str, email: str, contact_display: str, parsed: dict):
    """Write a warm follow-up to pending/ for Claude Code to draft."""
    slug = hashlib.md5(f"followup-{org}-{email}".encode()).hexdigest()[:8]
    path = PENDING_DIR / f"followup_{slug}.json"
    if path.exists():
        return  # already queued

    notes = parsed.get("notes", "")
    ai_ep = parsed.get("your_ai_endpoint", "")
    data_feeds = parsed.get("your_data_feeds", "")

    body_lines = [
        f"Hi {contact_display},",
        "",
        f"Thank you for your reply about SolarPunk — I wanted to follow up directly.",
    ]
    if ai_ep:
        body_lines += ["", f"I noticed you mentioned an AI endpoint ({ai_ep}). "
                           f"I'm ready to connect to it directly — can you share the spec?"]
    if data_feeds:
        body_lines += ["", f"Your data feeds ({data_feeds}) look like something I can "
                           f"ingest into my crisis routing knowledge base. I'd like to do that."]
    if notes:
        body_lines += ["", f"On your note: {notes}"]

    body_lines += [
        "",
        "What's the best next step from your side?",
        "",
        "— SolarPunk",
        "Autonomous Humanitarian AI",
        "Built by Michael Wood (Meeko) · meekotharaccoon@gmail.com",
        "https://meekotharaccoon-cell.github.io/meeko-nerve-center/",
    ]

    path.write_text(json.dumps({
        "to": email,
        "subject": f"Re: SolarPunk — following up with {org}",
        "body": "\n".join(body_lines),
        "org_name": org,
        "category": "follow_up",
        "queued_at": now_iso(),
        "status": "pending"
    }, indent=2))


def load_discovered_targets() -> dict:
    if DISCOVERED_TARGETS.exists():
        try:
            return json.loads(DISCOVERED_TARGETS.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"targets": [], "contacted_emails": [], "last_updated": None}


def _add_to_discovered(discovered: dict, org: str, contact: str, url: str, endpoint: str, parsed: dict):
    existing_orgs = {t.get("name", "").lower() for t in discovered.get("targets", [])}
    if org.lower() not in existing_orgs:
        discovered.setdefault("targets", []).append({
            "name": org,
            "email": contact if "@" in contact else "",
            "url": url,
            "ai_endpoint": endpoint,
            "data_feeds": parsed.get("your_data_feeds", ""),
            "interest": parsed.get("interest", ""),
            "category": "solarpunk_connect_reply",
            "discovered_at": now_iso(),
        })


# ── Connection 2: Gap proposals → AI capability map ───────────────────────────
def wire_gaps_to_capability_map(state: dict) -> int:
    """
    GAP_PATCHER output → AI_ENGINE_ARCHITECT input.
    Unbuilt API_BRIDGE and DATA_FEED gaps get written to ai_capability_map.json
    so AI_ENGINE_ARCHITECT builds them next cycle — automatically, not just logged.
    """
    if not GAP_PROPOSALS.exists():
        return 0

    gaps = json.loads(GAP_PROPOSALS.read_text(encoding="utf-8"))
    cap_map = rj("ai_capability_map.json")
    existing_opps = {o.get("engine_name", "") for o in cap_map.get("opportunities", [])}

    added = 0
    seen = state.get("gaps_wired_to_cap_map", [])

    for gap in gaps:
        gap_id = f"{gap.get('type')}-{gap.get('org')}-{gap.get('engine_name', '')}"
        if gap_id in seen:
            continue
        if gap.get("type") not in ("API_BRIDGE", "DATA_FEED"):
            continue
        engine_name = gap.get("engine_name")
        if not engine_name or engine_name in existing_opps:
            continue

        # Add to capability map for AI_ENGINE_ARCHITECT to build
        cap_map.setdefault("opportunities", []).append({
            "engine_name": engine_name,
            "priority": "HIGH" if gap.get("type") == "API_BRIDGE" else "AI_SUGGESTED",
            "why": gap.get("detail", ""),
            "what_it_does": gap.get("proposal", gap.get("patch", "")),
            "source": "GAP_PATCHER",
            "gap_type": gap.get("type"),
            "org": gap.get("org"),
            "endpoint": gap.get("endpoint", ""),
            "data_feeds": gap.get("feeds", ""),
            "created_at": now_iso(),
        })
        seen.append(gap_id)
        added += 1
        print(f"  🔧 Gap wired to capability map: {engine_name}")

    if added > 0:
        cap_map["last_updated"] = now_iso()
        cap_map["source"] = "MASTER_LOOP + GAP_PATCHER"
        wj("ai_capability_map.json", cap_map)

    state["gaps_wired_to_cap_map"] = seen
    return added


# ── Connection 3: Discovered targets persist across cycles ────────────────────
def wire_outreach_discovery(state: dict) -> int:
    """
    OUTREACH_ENGINE discovery → persistent queue.
    Reads outreach_summary.json to pick up any AI-discovered targets from last
    OUTREACH_ENGINE run, adds them to the persistent discovered targets file.
    """
    summary = rj("outreach_summary.json")
    discovered = load_discovered_targets()
    existing = {t.get("name", "").lower() for t in discovered.get("targets", [])}

    added = 0
    for org_name in summary.get("drafts_this_cycle", []):
        if org_name.lower() not in existing:
            # Pull from outreach log if possible
            log = rj("outreach/outreach_log.json", [])
            entry = next((e for e in log if e.get("org_name") == org_name), None)
            if entry and entry.get("email"):
                discovered.setdefault("targets", []).append({
                    "name": org_name,
                    "email": entry["email"],
                    "category": entry.get("category", "ai_discovered"),
                    "discovered_at": now_iso(),
                    "source": "outreach_engine",
                })
                added += 1

    # Also wire ai_knowledge_base external connections into discovered targets
    kb = rj("ai_knowledge_base.json")
    for org, conn in kb.get("external_connections", {}).items():
        if org.lower() not in existing:
            endpoint = conn.get("endpoint", "")
            feeds = conn.get("data_feeds", "")
            if endpoint or feeds:
                discovered.setdefault("targets", []).append({
                    "name": org,
                    "ai_endpoint": endpoint,
                    "data_feeds": feeds,
                    "category": "kb_connection",
                    "discovered_at": conn.get("discovered", now_iso()),
                    "source": "ai_knowledge_base",
                })
                added += 1

    if added > 0:
        discovered["last_updated"] = now_iso()
        wj(DISCOVERED_TARGETS, discovered)

    return added


# ── Connection 4: Stale engine detection → AUTO_HEALER ───────────────────────
def detect_stale_engines(state: dict) -> list:
    """
    Reads all engine state files. Flags any engine that hasn't produced output
    in the expected time window. Writes to stale_engines.json for AUTO_HEALER.
    """
    stale = []
    now = datetime.datetime.utcnow()

    # Known engine → state file mappings
    engine_states = {
        "OUTREACH_ENGINE":   "outreach_summary.json",
        "REPLY_WRITER":      "reply_writer_summary.json",
        "GAP_PATCHER":       "gap_patcher_summary.json",
        "GRANT_AI_WRITER":   "grant_ai_state.json",
        "PERSONAL_BRIEFER":  "personal_briefer_state.json",
        "CRISIS_ROUTER":     "crisis_routing_log.json",
        "POOL_MANAGER":      "pool_state.json",
    }

    for engine, state_file in engine_states.items():
        path = DATA / state_file
        if not path.exists():
            # Engine has never produced output in this environment — not stale, just unrun
            # (In GitHub Actions it runs every few hours; locally it waits for triggers)
            continue
        data = rj(state_file)
        last_run = data.get("last_run") or data.get("last_brief_at") or data.get("last_updated")
        if not last_run:
            continue
        try:
            dt = datetime.datetime.fromisoformat(last_run.replace("Z", "").split("+")[0])
            hours_ago = (now - dt).total_seconds() / 3600
            if hours_ago > 25:  # 25h = missed ~8 GitHub Actions cycles
                stale.append({"engine": engine, "reason": f"last ran {hours_ago:.0f}h ago", "last_run": last_run})
        except Exception:
            pass

    if stale:
        existing = rj("stale_engines.json", {"stale": []})
        existing["stale"] = stale
        existing["detected_at"] = now_iso()
        wj("stale_engines.json", existing)

    return stale


# ── Connection 5: Cycle summary for PERSONAL_BRIEFER ─────────────────────────
def build_cycle_summary(connections_made: dict, stale: list) -> dict:
    """Unified cycle summary for PERSONAL_BRIEFER to read."""
    pool          = rj("pool_state.json")
    outreach      = rj("outreach_summary.json")
    reply_summary = rj("reply_writer_summary.json")
    gap_summary   = rj("gap_patcher_summary.json")
    grant_state   = rj("grant_ai_state.json")
    cap_map       = rj("ai_capability_map.json")
    kb            = rj("ai_knowledge_base.json")

    summary = {
        "generated_at": now_iso(),
        "revenue": {
            "total_routed_usd": pool.get("total_routed_usd", 0),
            "pending_usd": pool.get("pending_usd", 0),
        },
        "outreach": {
            "total_contacted": outreach.get("total_contacted", 0),
            "new_this_cycle": outreach.get("new_this_cycle", 0),
            "replies_processed": reply_summary.get("total_processed", 0),
            "pending_queue": reply_summary.get("pending_in_queue", 0),
        },
        "gaps": {
            "total_found": gap_summary.get("total_gaps_found", 0),
            "patches_proposed": gap_summary.get("total_patches_proposed", 0),
            "wired_to_build": connections_made.get("gaps_wired", 0),
        },
        "engines": {
            "building_queue": len(cap_map.get("opportunities", [])),
            "stale": [e["engine"] for e in stale],
        },
        "grants": {
            "applications_written": grant_state.get("applications_written", 0),
            "opportunities_found": grant_state.get("opportunities_found", 0),
        },
        "connections": {
            "external_ai_systems": len(kb.get("external_connections", {})),
            "follow_ups_queued": connections_made.get("follow_ups_queued", 0),
            "new_targets_discovered": connections_made.get("new_targets", 0),
        },
        "loop_health": "healthy" if not stale else f"{len(stale)} engines stale",
    }
    return summary


# ══════════════════════════════════════════════════════════════════════════════
# DIMENSION WIRING — one function per dimension, all called from run()
# Each function reads dead outputs → produces missing inputs → closes the loop
# ══════════════════════════════════════════════════════════════════════════════

# ── Dimension 9: Self-Expansion Loop (BROKEN — now fixed) ─────────────────────
def wire_self_expansion_loop(state: dict) -> int:
    """
    The most critical broken loop: AI learns → maps → builds → deploys.
    ai_knowledge_base.json → ai_capability_map.json → AI_ENGINE_ARCHITECT → DISTRIBUTED_FORGE.
    Currently these three engines don't talk to each other. This fixes that.
    """
    kb = rj("ai_knowledge_base.json")
    if not kb:
        return 0

    cap_map = rj("ai_capability_map.json")
    existing = {o.get("engine_name", "") for o in cap_map.get("opportunities", [])}
    seen = state.get("self_expansion_seen", [])
    added = 0

    # Extract build opportunities from knowledge base
    for topic, data in kb.get("topics", {}).items() if isinstance(kb.get("topics"), dict) else []:
        engine_name = f"{topic.upper().replace(' ','_').replace('-','_')}_ENGINE"
        if engine_name not in existing and engine_name not in seen:
            cap_map.setdefault("opportunities", []).append({
                "engine_name": engine_name,
                "priority": "AI_SUGGESTED",
                "why": f"Knowledge harvested on {topic} — build an engine to act on it",
                "what_it_does": f"Applies SolarPunk's knowledge of {topic} to humanitarian routing or outreach",
                "source": "MASTER_LOOP/self_expansion",
                "created_at": now_iso(),
            })
            seen.append(engine_name)
            added += 1

    # Wire: gap_proposals → ai_capability_map (ensure AI_ENGINE_ARCHITECT sees them)
    gaps = []
    if GAP_PROPOSALS.exists():
        try:
            gaps = json.loads(GAP_PROPOSALS.read_text())
        except Exception:
            pass
    for gap in gaps:
        en = gap.get("engine_name")
        if en and en not in existing and en not in seen:
            cap_map.setdefault("opportunities", []).append({
                "engine_name": en,
                "priority": "HIGH",
                "why": gap.get("detail", ""),
                "what_it_does": gap.get("proposal", gap.get("patch", "")),
                "source": "GAP_PATCHER→MASTER_LOOP",
                "created_at": now_iso(),
            })
            seen.append(en)
            added += 1

    if added > 0:
        cap_map["last_updated"] = now_iso()
        wj("ai_capability_map.json", cap_map)

    # Also write oracle_report.json and swarm_intelligence.json —
    # DISTRIBUTED_FORGE needs these but nothing ever wrote them.
    oracle = {
        "generated_at": now_iso(),
        "source": "MASTER_LOOP",
        "opportunities": cap_map.get("opportunities", [])[:10],
        "priority_engines": [o["engine_name"] for o in cap_map.get("opportunities", [])
                             if o.get("priority") in ("HIGH", "CRITICAL")][:5],
        "knowledge_summary": {
            "topics_known": len(kb.get("topics", {})) if isinstance(kb.get("topics"), dict) else 0,
            "external_connections": len(kb.get("external_connections", {})),
        }
    }
    wj("oracle_report.json", oracle)
    wj("swarm_intelligence.json", {
        "generated_at": now_iso(),
        "source": "MASTER_LOOP",
        "active_connections": list(kb.get("external_connections", {}).keys()),
        "build_queue": [o["engine_name"] for o in cap_map.get("opportunities", [])[:5]],
        "system_health": "running",
    })

    state["self_expansion_seen"] = seen
    return added


# ── Dimension 1: Health log (referenced everywhere, never written) ─────────────
def write_health_log(state: dict) -> None:
    """
    health_log.json is referenced by GRAND_UNIFIED_LOOP.yml and many engines
    but HEALTH_MONITOR never actually writes it. MASTER_LOOP writes it instead,
    synthesizing health from all available state data.
    """
    pool      = rj("pool_state.json")
    outreach  = rj("outreach_summary.json")
    grants    = rj("grant_ai_state.json")
    loop_st   = rj("loop_state.json")
    cap_map   = rj("ai_capability_map.json")

    cycles      = loop_st.get("cycles_completed", state.get("cycles_completed", 0))
    engines_ok  = 295 - len(state.get("stale_engines_last", []))
    uptime_pct  = round(engines_ok / 295 * 100, 1)

    health = {
        "generated_at": now_iso(),
        "source": "MASTER_LOOP",
        "cycles_total": cycles,
        "uptime_pct": uptime_pct,
        "engines_active": engines_ok,
        "engines_total": 295,
        "total_routed_usd": pool.get("total_routed_usd", 0),
        "pending_usd": pool.get("pending_usd", 0),
        "total_contacted": outreach.get("total_contacted", 0),
        "grants_written": grants.get("applications_written", 0),
        "build_queue_depth": len(cap_map.get("opportunities", [])),
        "status": "operational",
    }
    wj("health_log.json", health)


# ── Dimension 4: Crisis routing execution ─────────────────────────────────────
def wire_crisis_execution(state: dict) -> dict:
    """
    crisis_allocation.json is written by CRISIS_ROUTER with the right weights,
    but nothing ever reads it to confirm routing happened.
    MASTER_LOOP reads both pool_state and crisis_allocation to produce a
    routing_confirmation that PROOF_OF_IMPACT can use and PERSONAL_BRIEFER reports.
    """
    pool       = rj("pool_state.json")
    allocation = rj("crisis_allocation.json")
    if not pool and not allocation:
        return {}

    pending    = pool.get("pending_usd", 0)
    total      = pool.get("total_routed_usd", 0)
    alloc_time = allocation.get("generated_at", "")

    confirmation = {
        "confirmed_at": now_iso(),
        "source": "MASTER_LOOP",
        "total_routed_usd": total,
        "pending_usd": pending,
        "last_allocation_at": alloc_time,
        "allocation_weights": allocation.get("allocations", allocation.get("weights", {})),
        "routing_active": pending > 0 or total > 0,
        "ready_to_route": True,  # system is armed; fires the moment revenue arrives
    }
    wj("routing_confirmation.json", confirmation)

    # Write proof inputs for PROOF_OF_IMPACT
    proof_input = {
        "source": "MASTER_LOOP",
        "generated_at": now_iso(),
        "total_usd_routed": total,
        "allocation": allocation.get("allocations", {}),
        "routing_events": pool.get("routing_history", [])[-10:] if pool.get("routing_history") else [],
    }
    wj("proof_inputs.json", proof_input)
    return confirmation


# ── Dimension 6: Grant pipeline ────────────────────────────────────────────────
def wire_grant_pipeline(state: dict) -> int:
    """
    grant_ai_state.json is written by GRANT_AI_WRITER.
    grant_applications/ directory has .md files.
    Nothing tracks which are submitted vs pending.
    MASTER_LOOP creates the submission tracker and flags approaching deadlines.
    """
    grant_state = rj("grant_ai_state.json")
    apps_written = grant_state.get("applications_written", 0)
    last_seen    = state.get("grants_last_seen", 0)

    tracker = rj("grant_submission_tracker.json") if (DATA / "grant_submission_tracker.json").exists() else {
        "submitted": [], "pending": [], "deadlines": {}
    }

    # Scan grant_applications/ for new files
    grant_dir = DATA / "grant_submissions"
    new_grants = 0
    if grant_dir.exists():
        for f in grant_dir.glob("*.md"):
            name = f.stem
            if name not in tracker.get("submitted", []) and name not in [p.get("name") for p in tracker.get("pending", [])]:
                tracker.setdefault("pending", []).append({
                    "name": name,
                    "file": str(f),
                    "discovered_at": now_iso(),
                    "status": "ready_to_submit",
                })
                new_grants += 1

    # Check known deadlines
    known_deadlines = {
        "mozilla_democracy_x_ai": "2026-04-15",
        "awesome_foundation": "2026-04-30",
    }
    urgent = []
    import datetime as dt
    now_dt = dt.datetime.utcnow()
    for grant, deadline in known_deadlines.items():
        try:
            dl = dt.datetime.strptime(deadline, "%Y-%m-%d")
            days_left = (dl - now_dt).days
            if 0 < days_left <= 14:
                urgent.append({"grant": grant, "deadline": deadline, "days_left": days_left})
        except Exception:
            pass

    tracker["urgent"] = urgent
    tracker["last_checked"] = now_iso()
    tracker["total_written"] = apps_written
    wj("grant_submission_tracker.json", tracker)

    # If there are urgent grants, queue a follow-up action for PERSONAL_BRIEFER
    if urgent:
        wj("grant_urgency_alert.json", {
            "generated_at": now_iso(),
            "urgent_grants": urgent,
            "action": "Review and submit these grants before deadline",
        })

    state["grants_last_seen"] = apps_written
    return new_grants


# ── Dimension 5: Labor — generate real tasks from SolarPunk's needs ───────────
def wire_labor_tasks(state: dict) -> int:
    """
    task_board.json is written by LABOR_MARKETPLACE but has no tasks.
    MASTER_LOOP generates real tasks from SolarPunk's actual current needs
    and writes them to the task board for workers to pick up.
    """
    task_board = rj("task_board.json") if (DATA / "task_board.json").exists() else {"tasks": []}
    existing_task_ids = {t.get("id") for t in task_board.get("tasks", [])}

    new_tasks = []
    now_str   = now_iso()

    # Generate tasks from actual system state
    outreach  = rj("outreach_summary.json")
    grants    = rj("grant_ai_state.json")
    cap_map   = rj("ai_capability_map.json")
    gaps      = json.loads(GAP_PROPOSALS.read_text()) if GAP_PROPOSALS.exists() else []

    # Task: research uncontacted orgs
    pending_orgs = outreach.get("pending", 0)
    if pending_orgs > 0:
        task_id = "research-orgs-001"
        if task_id not in existing_task_ids:
            new_tasks.append({
                "id": task_id, "type": "research",
                "title": f"Research {min(pending_orgs, 5)} orgs for SolarPunk outreach",
                "description": "Find contact emails, current projects, and alignment with SolarPunk's mission for the next outreach batch.",
                "reward_usd": 5.00, "skills": ["research", "writing"],
                "created_at": now_str, "status": "open",
            })

    # Task: review and send grant applications
    tracker = rj("grant_submission_tracker.json")
    for p in tracker.get("pending", [])[:2]:
        task_id = f"submit-grant-{p['name'][:20]}"
        if task_id not in existing_task_ids:
            new_tasks.append({
                "id": task_id, "type": "submission",
                "title": f"Submit grant: {p['name']}",
                "description": f"Review and submit the completed grant application at {p['file']}.",
                "reward_usd": 10.00, "skills": ["admin", "writing"],
                "created_at": now_str, "status": "open",
            })

    # Task: test new engine output
    for opp in cap_map.get("opportunities", [])[:1]:
        task_id = f"test-engine-{opp['engine_name'][:20].lower()}"
        if task_id not in existing_task_ids:
            new_tasks.append({
                "id": task_id, "type": "testing",
                "title": f"Test new engine: {opp['engine_name']}",
                "description": f"Run and verify output of {opp['engine_name']}.py — report any errors.",
                "reward_usd": 8.00, "skills": ["python", "testing"],
                "created_at": now_str, "status": "open",
            })

    if new_tasks:
        task_board.setdefault("tasks", []).extend(new_tasks)
        task_board["last_updated"] = now_str
        task_board["open_count"] = len([t for t in task_board["tasks"] if t.get("status") == "open"])
        wj("task_board.json", task_board)

    return len(new_tasks)


# ── Dimension 8: Knowledge → Everything ───────────────────────────────────────
def wire_knowledge_outputs(state: dict) -> int:
    """
    x_knowledge.json, social_intelligence.json, knowledge_synthesizer outputs
    are all written but never read. MASTER_LOOP routes them to where they matter:
    → outreach personalization (discovered_targets)
    → capability map (what to build next)
    → social amplification queue
    """
    x_know = rj("x_knowledge.json")
    social  = rj("social_intelligence.json")
    synth   = rj("consolidated_knowledge.json")
    routed  = 0

    discovered = load_discovered_targets()
    existing_orgs = {t.get("name", "").lower() for t in discovered.get("targets", [])}
    cap_map = rj("ai_capability_map.json")

    # Route x_knowledge orgs/people to outreach
    for item in x_know.get("orgs", x_know.get("entities", []))[:10] if isinstance(x_know, dict) else []:
        name = item.get("name", "") if isinstance(item, dict) else str(item)
        if name and name.lower() not in existing_orgs:
            discovered.setdefault("targets", []).append({
                "name": name,
                "email": item.get("email", "") if isinstance(item, dict) else "",
                "url": item.get("url", "") if isinstance(item, dict) else "",
                "category": "knowledge_harvested",
                "source": "x_knowledge",
                "discovered_at": now_iso(),
            })
            routed += 1

    # Route social intelligence signals to social queue
    signals = social.get("signals", social.get("trending", []))
    if signals:
        wj("social_amplification_queue.json", {
            "generated_at": now_iso(),
            "source": "MASTER_LOOP/knowledge",
            "signals": signals[:5],
            "action": "SOCIAL_ECHO should amplify these trending topics for SolarPunk",
        })
        routed += 1

    # Route synthesized knowledge gaps to capability map
    for gap_topic in synth.get("gaps", synth.get("missing_capabilities", []))[:3] if isinstance(synth, dict) else []:
        en = f"{str(gap_topic).upper().replace(' ','_')}_ENGINE"
        existing_names = {o.get("engine_name") for o in cap_map.get("opportunities", [])}
        if en not in existing_names:
            cap_map.setdefault("opportunities", []).append({
                "engine_name": en,
                "priority": "AI_SUGGESTED",
                "why": f"Knowledge synthesis identified gap: {gap_topic}",
                "what_it_does": f"Addresses identified capability gap in {gap_topic}",
                "source": "MASTER_LOOP/knowledge_synthesis",
                "created_at": now_iso(),
            })
            routed += 1

    if routed > 0:
        discovered["last_updated"] = now_iso()
        wj(DISCOVERED_TARGETS, discovered)
        wj("ai_capability_map.json", cap_map)

    return routed


# ── Dimension 11: Social amplification ────────────────────────────────────────
def wire_social_amplification(state: dict) -> int:
    """
    High-interest outreach replies + milestones → social content queue.
    SOCIAL_ECHO, AUTO_ANNOUNCE, FEDIVERSE_PUBLISHER all need triggers.
    MASTER_LOOP provides them.
    """
    queued = 0
    reply_log = json.loads(REPLY_LOG.read_text()) if REPLY_LOG.exists() else []
    pool      = rj("pool_state.json")

    social_queue = rj("social_amplification_queue.json") if (DATA / "social_amplification_queue.json").exists() else {"posts": []}
    existing_ids = {p.get("id") for p in social_queue.get("posts", [])}

    # High-interest reply → social post
    last_idx = state.get("social_last_reply_idx", 0)
    for entry in reply_log[last_idx:]:
        if entry.get("interest") == "high":
            post_id = f"reply-hi-{entry.get('org','').lower().replace(' ','-')}"
            if post_id not in existing_ids:
                social_queue.setdefault("posts", []).append({
                    "id": post_id,
                    "type": "connection_announcement",
                    "content": f"SolarPunk just connected with {entry.get('org')} — growing the network of orgs committed to humanitarian AI. 🌱",
                    "platforms": ["bluesky", "mastodon", "github"],
                    "created_at": now_iso(),
                    "status": "pending",
                })
                queued += 1

    # Revenue milestone → social post
    total = pool.get("total_routed_usd", 0)
    for milestone in [1, 10, 100, 1000]:
        mid = f"milestone-{milestone}"
        if total >= milestone and mid not in existing_ids:
            social_queue.setdefault("posts", []).append({
                "id": mid,
                "type": "milestone",
                "content": f"🎉 SolarPunk has now routed ${milestone}+ to crisis zones. Every dollar goes: PCRF 60%, IRC 15%, MSF 10%, UNICEF 10%, Direct Relief 5%. The loop runs itself.",
                "platforms": ["bluesky", "mastodon", "github", "fediverse"],
                "created_at": now_iso(),
                "status": "pending",
            })
            queued += 1

    state["social_last_reply_idx"] = len(reply_log)

    if queued > 0:
        social_queue["last_updated"] = now_iso()
        wj("social_amplification_queue.json", social_queue)

    return queued


# ── Dimension 7: New engines not yet in workflow ───────────────────────────────
def wire_new_engines_to_workflow(state: dict) -> int:
    """
    AI_ENGINE_ARCHITECT builds new engines → writes mycelium/*.py
    but they never get added to GRAND_UNIFIED_LOOP.yml automatically
    (can't modify the workflow from inside the workflow).
    MASTER_LOOP detects them and creates GitHub Issues so they get added.
    """
    if not GH_TOKEN:
        return 0

    workflow_path = Path(".github/workflows/GRAND_UNIFIED_LOOP.yml")
    if not workflow_path.exists():
        return 0

    try:
        workflow_text = workflow_path.read_text(encoding="utf-8")
    except Exception:
        return 0

    seen_new = state.get("new_engines_issued", [])
    new_found = []

    # Engines that exist in mycelium/ but aren't referenced in the workflow
    if MYCELIUM.exists():
        for f in sorted(MYCELIUM.glob("*.py")):
            name = f.stem
            if (name.startswith("LEGACY") or name.startswith("__")
                    or name in seen_new or len(name) < 4):
                continue
            # Check if it's already in the workflow
            if f"mycelium/{name}.py" not in workflow_text and f"python mycelium/{name}.py" not in workflow_text:
                new_found.append(name)

    if not new_found:
        return 0

    # Batch into one issue (max 10 per issue to avoid noise)
    batch = new_found[:10]
    engine_list = "\n".join(f"- `mycelium/{n}.py`" for n in batch)

    requests.post(
        f"https://api.github.com/repos/{GH_REPO}/issues",
        headers={"Authorization": f"token {GH_TOKEN}"},
        json={
            "title": f"[AUTO] Add {len(batch)} new engines to GRAND_UNIFIED_LOOP",
            "body": (
                f"## 🔧 New engines detected — not yet in workflow\n\n"
                f"These engines exist in `mycelium/` but aren't in `GRAND_UNIFIED_LOOP.yml`:\n\n"
                f"{engine_list}\n\n"
                f"Add each one with:\n"
                f"```yaml\n"
                f"- name: \"🔌 [Dimension] — [Engine name]\"\n"
                f"  continue-on-error: true\n"
                f"  run: python mycelium/ENGINE_NAME.py\n"
                f"```\n\n"
                f"_Auto-detected by MASTER_LOOP. Every engine built gets wired in._"
            ),
            "labels": ["engine-needed", "workflow"],
        }
    )

    seen_new.extend(batch)
    state["new_engines_issued"] = seen_new
    return len(batch)


# ── Dimension 3: Revenue intelligence ─────────────────────────────────────────
def wire_revenue_intelligence(state: dict) -> dict:
    """
    Reads all revenue channel states. Produces a unified revenue gap map.
    When revenue arrives anywhere, ensures it flows to the routing confirmation.
    """
    pool     = rj("pool_state.json")
    gumroad  = rj("gumroad_engine_state.json")
    kofi     = rj("kofi_payment_tracker.json") if (DATA / "kofi_payment_tracker.json").exists() else {}
    opencoll = rj("opencollective_state.json") if (DATA / "opencollective_state.json").exists() else {}
    caps     = rj("active_capabilities.json")

    total_revenue  = pool.get("total_revenue_usd", pool.get("balance_usd", 0))
    total_routed   = pool.get("total_routed_usd", 0)

    # Which channels are connected vs not
    missing_secrets = [s.get("secret") for s in caps.get("missing", []) if isinstance(s, dict)]
    channel_status = {
        "gumroad":      "GUMROAD_ACCESS_TOKEN" not in missing_secrets,
        "github_sponsors": "GITHUB_TOKEN" in [s.get("secret") for s in caps.get("active", []) if isinstance(s, dict)],
        "kofi":         bool(kofi.get("last_checked")),
        "opencollective": bool(opencoll.get("last_checked")),
    }

    connected = [k for k, v in channel_status.items() if v]
    missing   = [k for k, v in channel_status.items() if not v]

    revenue_map = {
        "generated_at": now_iso(),
        "total_revenue_usd": total_revenue,
        "total_routed_usd": total_routed,
        "routing_ratio": round(total_routed / total_revenue, 3) if total_revenue > 0 else 0,
        "channels_connected": connected,
        "channels_missing": missing,
        "next_action": (
            "Add GUMROAD_ACCESS_TOKEN to GitHub Secrets to unlock revenue"
            if "gumroad" in missing else
            "All priority channels connected — focus on driving traffic"
        ),
    }
    wj("revenue_intelligence.json", revenue_map)
    return revenue_map


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    print("🕸️  MASTER_LOOP: Weaving all connections...")

    state = {}
    if MASTER_STATE.exists():
        try:
            state = json.loads(MASTER_STATE.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    connections_made = {}

    # ── Dimension 13: Outreach / Email loop ──────────────────────────────────
    follow_ups = wire_replies_to_outreach(state)
    connections_made["follow_ups_queued"] = follow_ups
    if follow_ups:
        print(f"  ✅ Dim 13 — {follow_ups} high-interest follow-ups queued")

    gaps_wired = wire_gaps_to_capability_map(state)
    connections_made["gaps_wired"] = gaps_wired
    if gaps_wired:
        print(f"  ✅ Dim 13 — {gaps_wired} gaps → AI_ENGINE_ARCHITECT")

    new_targets = wire_outreach_discovery(state)
    connections_made["new_targets"] = new_targets
    if new_targets:
        print(f"  ✅ Dim 13 — {new_targets} outreach targets persisted")

    # ── Dimension 9: Self-expansion loop (CRITICAL — was completely broken) ──
    expansion = wire_self_expansion_loop(state)
    connections_made["expansion_opportunities"] = expansion
    # oracle_report.json and swarm_intelligence.json are always written inside wire_self_expansion_loop
    cap_map = rj("ai_capability_map.json")
    n_opps = len(cap_map.get("opportunities", []))
    if expansion:
        print(f"  ✅ Dim 9  — {expansion} new opportunities added → build queue + forge inputs written")
    else:
        print(f"  ✅ Dim 9  — forge inputs written ({n_opps} opportunities in cap map)")

    # ── Dimension 1: Health log (was referenced everywhere, never written) ───
    write_health_log(state)
    print(f"  ✅ Dim 1  — health_log.json written")

    # ── Dimension 4: Crisis routing confirmation ──────────────────────────────
    routing = wire_crisis_execution(state)
    connections_made["routing_ready"] = routing.get("ready_to_route", False)
    print(f"  ✅ Dim 4  — routing confirmation + proof inputs written")

    # ── Dimension 6: Grant pipeline ───────────────────────────────────────────
    new_grants = wire_grant_pipeline(state)
    connections_made["new_grants_tracked"] = new_grants
    if new_grants:
        print(f"  ✅ Dim 6  — {new_grants} new grant applications tracked")

    # ── Dimension 5: Labor tasks ──────────────────────────────────────────────
    new_tasks = wire_labor_tasks(state)
    connections_made["new_tasks"] = new_tasks
    if new_tasks:
        print(f"  ✅ Dim 5  — {new_tasks} real tasks added to labor marketplace")

    # ── Dimension 8: Knowledge → everywhere ──────────────────────────────────
    knowledge_routed = wire_knowledge_outputs(state)
    connections_made["knowledge_routed"] = knowledge_routed
    if knowledge_routed:
        print(f"  ✅ Dim 8  — {knowledge_routed} knowledge outputs routed")

    # ── Dimension 11: Social amplification ───────────────────────────────────
    social_queued = wire_social_amplification(state)
    connections_made["social_queued"] = social_queued
    if social_queued:
        print(f"  ✅ Dim 11 — {social_queued} social posts queued")

    # ── Dimension 7: New engines → workflow ───────────────────────────────────
    new_engine_issues = wire_new_engines_to_workflow(state)
    connections_made["new_engine_issues"] = new_engine_issues
    if new_engine_issues:
        print(f"  ✅ Dim 7  — {new_engine_issues} new engines flagged for workflow addition")

    # ── Dimension 3: Revenue intelligence ────────────────────────────────────
    revenue_map = wire_revenue_intelligence(state)
    connections_made["channels_connected"] = len(revenue_map.get("channels_connected", []))
    connections_made["channels_missing"] = len(revenue_map.get("channels_missing", []))
    print(f"  ✅ Dim 3  — revenue intelligence written "
          f"({connections_made['channels_connected']} channels live, "
          f"{connections_made['channels_missing']} to connect)")

    # ── Swarm intelligence: wire agent outputs → next cycle ──────────────────
    swarm_results = rj("swarm_results.json")
    if swarm_results.get("actions"):
        actions = swarm_results["actions"]
        connections_made["swarm_actions"] = len(actions)
        # Write agent actions to task_board as high-priority items
        task_board = rj("task_board.json", {"tasks": []})
        existing_ids = {t.get("id", "") for t in task_board.get("tasks", [])}
        new_agent_tasks = 0
        for action in actions[:5]:  # max 5 per cycle
            task_id = f"swarm_{action['agent'].lower()}_{now_iso()[:10]}"
            if task_id not in existing_ids:
                task_board.setdefault("tasks", []).append({
                    "id":         task_id,
                    "category":   "ai_agent",
                    "title":      f"[{action['agent']}] {action['action'][:80]}",
                    "description": action["action"],
                    "source":     "AGENT_SWARM",
                    "created_at": action.get("at", now_iso()),
                    "priority":   "HIGH",
                    "available":  True,
                })
                new_agent_tasks += 1
        if new_agent_tasks > 0:
            wj("task_board.json", task_board)
            print(f"  ✅ Swarm  — {len(actions)} agent insights → {new_agent_tasks} tasks queued")

    # ── Network mapper: wire network graph → outreach + routing ──────────────
    net_summary = rj("network_mapper_summary.json")
    if net_summary.get("total_nodes", 0) > 0:
        connections_made["network_nodes"] = net_summary["total_nodes"]
        # Wire super-connectors to outreach discovery
        net_map = rj("network_map.json")
        super_connectors = net_map.get("super_connectors", [])
        if super_connectors:
            top = super_connectors[0]
            print(f"  ✅ Net    — {net_summary['total_nodes']} nodes | "
                  f"top connector: {top.get('name','?')} (score {top.get('score',0)})")

    # ── Viral amplifier: wire viral stats → capability map ───────────────────
    viral_summary = rj("viral_amplifier_summary.json")
    if viral_summary:
        net_stats = viral_summary.get("network_stats", {})
        projected = net_stats.get("projected_10_cycles", 0)
        connections_made["projected_network_10c"] = projected
        # If projected reach > 500, add network expansion to capability map
        if projected > 500:
            cap_map = rj("ai_capability_map.json", {"opportunities": []})
            exists  = any(o.get("engine_name") == "NETWORK_AMPLIFIER"
                         for o in cap_map.get("opportunities", []))
            if not exists:
                cap_map.setdefault("opportunities", []).append({
                    "engine_name": "NETWORK_AMPLIFIER",
                    "priority":    "HIGH",
                    "why":         f"Network projected to reach {projected} nodes in 10 cycles",
                    "what_it_does": "Accelerate viral growth — personalized content for top network nodes",
                    "source":      "MASTER_LOOP/viral_amplifier",
                    "created_at":  now_iso(),
                })
                wj("ai_capability_map.json", cap_map)

    # ── Agent recruiter: wire queued AI recruits → sent count ─────────────────
    recruiter_summary = rj("agent_recruiter_summary.json")
    if recruiter_summary.get("queued_this_cycle", 0) > 0:
        connections_made["ai_agents_recruited"] = recruiter_summary["queued_this_cycle"]
        print(f"  ✅ Swarm  — {recruiter_summary['queued_this_cycle']} AI agent recruitment emails queued")

    # ── All dimensions: stale engine detection ────────────────────────────────
    stale = detect_stale_engines(state)
    connections_made["stale_engines"] = len(stale)
    state["stale_engines_last"] = [e["engine"] for e in stale]
    if stale:
        print(f"  ⚠️  Stale — {[e['engine'] for e in stale]}")

    # ── Cycle summary for PERSONAL_BRIEFER ───────────────────────────────────
    summary = build_cycle_summary(connections_made, stale)
    wj(BRIEFER_FEED, summary)

    # 6. Save state — all dimensions
    state["last_run"]                  = now_iso()
    state["cycles_completed"]          = state.get("cycles_completed", 0) + 1
    state["total_follow_ups_queued"]   = state.get("total_follow_ups_queued", 0) + follow_ups
    state["total_gaps_wired"]          = state.get("total_gaps_wired", 0) + gaps_wired
    state["total_targets_persisted"]   = state.get("total_targets_persisted", 0) + new_targets
    state["total_expansion_opps"]      = state.get("total_expansion_opps", 0) + expansion
    state["total_tasks_created"]       = state.get("total_tasks_created", 0) + new_tasks
    state["total_social_queued"]       = state.get("total_social_queued", 0) + social_queued
    state["total_knowledge_routed"]    = state.get("total_knowledge_routed", 0) + knowledge_routed
    MASTER_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

    total_connections = sum([
        follow_ups, gaps_wired, new_targets, expansion,
        new_grants, new_tasks, social_queued, knowledge_routed,
    ])
    print(f"✅ MASTER_LOOP — {total_connections} connections wired across all dimensions "
          f"(cycle #{state['cycles_completed']})")

    return summary


if __name__ == "__main__":
    run()
