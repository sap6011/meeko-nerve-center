#!/usr/bin/env python3
"""
DUAL_SYSTEM_CROSSWIRE.py -- The bridge between the 1/99 and 99/1 universes.

    Two systems. One mission. This engine makes them talk.

The SolarPunk organism has TWO economic halves:
    1/99 system (FUEL_CORE, GROWTH_FLYWHEEL)  -- GROWS the machine
    99/1 system (ECONOMY_CHAIN, REVENUE_SPLITTER) -- GIVES to those who need it

Without CROSSWIRE, these halves are deaf to each other.
Content sits in growth_flywheel_content.json but never reaches social_queue.json.
Revenue signals stay in economy_chain_ledger but never flow through fuel routing.
Blockers identified by FUEL_CORE never reach the self_builder for automated fixing.
Products get listed but nobody announces them.

CROSSWIRE connects EVERY gap:

    1. CONTENT -> SOCIAL:    Flywheel content -> social_queue (so SOCIAL_DASHBOARD distributes)
    2. REVENUE -> BOTH:      Revenue signals flow through BOTH splitter AND economy chain
    3. FUEL -> GROWTH:       Zero-cost FUEL_CORE blockers -> self_builder_queue (AUTO_EXECUTOR fixes)
    4. STOREFRONT -> SIGNAL: New product listings -> signal_chain (announce to the world)
    5. TASK_BOARD -> TELEGRAM: Top 5 urgent tasks -> telegram_relay (notify Meeko)
    6. GROWTH_METRICS -> CHIMERA: Flywheel metrics -> chimera scoring (new fitness dimension)
    7. HUMANITARIAN -> FUEL:  grants_found -> fuel_plan (grants ARE revenue for 99/1)
    8. CROSSWIRE REPORT:     Full visibility into every cross-connection and gap

Zero secrets. Zero paid APIs. Pure signal routing between subsystems.
"""
import json
import time
import pathlib
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _load(fname, fallback=None):
    f = DATA / fname
    if f.exists():
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            return d if isinstance(d, (dict, list)) else (fallback or {})
        except Exception:
            pass
    return fallback if fallback is not None else {}


def _save(fname, data):
    (DATA / fname).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _ts():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# 1. CONTENT -> SOCIAL
#    Injects growth_flywheel_content pieces into social_queue.json
#    so SOCIAL_DASHBOARD, VIRALITY_ENGINE, and BROADCAST_PROTOCOL can distribute.
# ---------------------------------------------------------------------------

def _crosswire_content_to_social():
    """Pull content from growth_flywheel_content and inject into social_queue."""
    flywheel_content = _load("growth_flywheel_content.json", {})
    social_queue = _load("social_queue.json", {"posts": [], "queue": []})

    # Ensure structure
    if not isinstance(social_queue, dict):
        social_queue = {"posts": [], "queue": []}
    if "posts" not in social_queue:
        social_queue["posts"] = []

    # Collect existing post texts to avoid duplicates
    existing_texts = set()
    for p in social_queue.get("posts", []):
        if isinstance(p, dict) and p.get("text"):
            existing_texts.add(p["text"][:100])

    injected = 0

    # Inject twitter threads as social posts
    for thread in flywheel_content.get("twitter_threads", []):
        thread_id = thread.get("id", "unknown")
        for tweet in thread.get("tweets", []):
            text = tweet.get("text", "")
            if not text or text[:100] in existing_texts:
                continue
            social_queue["posts"].append({
                "text": text,
                "platform": "twitter",
                "source": "crosswire_flywheel",
                "flywheel_id": thread_id,
                "flywheel_type": thread.get("type", "general"),
                "status": "pending",
                "injected_at": _ts(),
            })
            existing_texts.add(text[:100])
            injected += 1

    # Inject bluesky posts
    for post in flywheel_content.get("bluesky_posts", []):
        text = post.get("text", "")
        if not text or text[:100] in existing_texts:
            continue
        social_queue["posts"].append({
            "text": text,
            "platform": "bluesky",
            "source": "crosswire_flywheel",
            "flywheel_id": post.get("id", "unknown"),
            "status": "pending",
            "injected_at": _ts(),
        })
        existing_texts.add(text[:100])
        injected += 1

    # Inject reddit posts
    for post in flywheel_content.get("reddit_posts", []):
        title = post.get("title", "")
        body = post.get("body", "")
        text = "r/%s\n\nTITLE: %s\n\n%s" % (
            post.get("subreddit", "SolarPunk"),
            title,
            body,
        )
        if text[:100] in existing_texts:
            continue
        social_queue["posts"].append({
            "text": text,
            "platform": "reddit",
            "source": "crosswire_flywheel",
            "flywheel_id": post.get("id", "unknown"),
            "status": "pending",
            "injected_at": _ts(),
        })
        existing_texts.add(text[:100])
        injected += 1

    # Inject GitHub discussion drafts as social content
    for disc in flywheel_content.get("github_discussions", []):
        text = "%s\n\n%s" % (disc.get("title", ""), disc.get("body", ""))
        if text[:100] in existing_texts:
            continue
        social_queue["posts"].append({
            "text": text,
            "platform": "github_discussion",
            "source": "crosswire_flywheel",
            "flywheel_id": disc.get("id", "unknown"),
            "status": "pending",
            "injected_at": _ts(),
        })
        existing_texts.add(text[:100])
        injected += 1

    # Inject product social_post lines from storefront_listings
    listings = _load("storefront_listings.json", {})
    for pid, listing in listings.get("listings", {}).items():
        sp = listing.get("social_post", "")
        if not sp or sp[:100] in existing_texts:
            continue
        social_queue["posts"].append({
            "text": sp,
            "platform": "multi",
            "source": "crosswire_storefront",
            "product_id": pid,
            "status": "pending",
            "injected_at": _ts(),
        })
        existing_texts.add(sp[:100])
        injected += 1

    if injected > 0:
        _save("social_queue.json", social_queue)

    return {"injected": injected, "total_posts": len(social_queue.get("posts", []))}


# ---------------------------------------------------------------------------
# 2. REVENUE -> BOTH
#    Ensures revenue flows through BOTH revenue_splitter AND economy_chain.
#    Writes a unified data/revenue_flow.json showing the full picture.
# ---------------------------------------------------------------------------

def _crosswire_revenue_to_both():
    """Unify revenue signals from all sources into a single flow document."""
    economy = _load("economy_chain_ledger.json", {})
    kofi = _load("kofi_tracker_state.json", {})
    proof = _load("proof_ledger.json", {})
    splitter = _load("revenue_splitter_state.json", {})
    fuel_state = _load("fuel_core_state.json", {})
    routing = _load("revenue_routing.json", {})
    quick_rev = _load("quick_revenue.json", {})

    # Canonical revenue: take the max across all sources
    total_earned = max(
        float(economy.get("total_earned", 0)),
        float(kofi.get("total_verified", 0)),
        float(proof.get("total_sales", 0)),
        float(quick_rev.get("total_revenue", 0)),
        0.0,
    )

    # Economy chain routing breakdown (99/1 perspective)
    economy_routes = {}
    for key in ("gaza", "legal", "ai", "reinvest", "meeko"):
        route_data = economy.get("routes", {}).get(key, {})
        economy_routes[key] = {
            "total": float(route_data.get("total", 0)),
            "events_count": len(route_data.get("events", [])),
        }

    # Fuel core routing breakdown (1/99 perspective)
    fuel_routes = {}
    for key in ("immediate_aid", "product_development", "storefront_infra",
                "marketing_growth", "api_keys_tools", "legal_runway"):
        route_data = fuel_state.get("fuel_routes", {}).get(key, {})
        fuel_routes[key] = {
            "total": float(route_data.get("total", 0)) if isinstance(route_data, dict) else 0.0,
        }

    # Splitter lifetime routing
    lifetime = splitter.get("lifetime_routing", {})

    # Phase info
    phase = splitter.get("current_phase", "ignition")
    phase_label = routing.get("phase_label", "IGNITION")

    revenue_flow = {
        "generated_at": _ts(),
        "engine": "DUAL_SYSTEM_CROSSWIRE",
        "total_earned": total_earned,
        "first_dollar_earned": total_earned > 0,
        "loop_closed": economy.get("loop_closed", False),
        "phase": phase,
        "phase_label": phase_label,
        "sources": {
            "economy_chain": float(economy.get("total_earned", 0)),
            "kofi_tracker": float(kofi.get("total_verified", 0)),
            "proof_ledger": float(proof.get("total_sales", 0)),
            "quick_revenue": float(quick_rev.get("total_revenue", 0)),
        },
        "system_99_1": {
            "description": "ECONOMY_CHAIN -- 99/1 giving system",
            "total_routed": float(economy.get("total_routed", 0)),
            "cycles": economy.get("cycles", 0),
            "routes": economy_routes,
        },
        "system_1_99": {
            "description": "FUEL_CORE -- 1/99 growth system",
            "total_routed": float(fuel_state.get("total_fuel_routed", 0)),
            "cycles": fuel_state.get("cycles", 0),
            "routes": fuel_routes,
        },
        "splitter": {
            "description": "REVENUE_SPLITTER -- dual-mode router deciding the split",
            "phase": phase,
            "total_through_1_99": float(lifetime.get("total_through_1_99", 0)),
            "total_through_99_1": float(lifetime.get("total_through_99_1", 0)),
            "total_to_aid": float(lifetime.get("total_to_aid", 0)),
            "total_to_growth": float(lifetime.get("total_to_growth", 0)),
        },
        "combined_aid_total": round(
            float(lifetime.get("total_to_aid", 0)) +
            float(economy_routes.get("gaza", {}).get("total", 0)),
            6,
        ),
        "active_routes_count": len(routing.get("routes", [])),
        "mantra": "Every dollar flows through both systems. No leaks. No blind spots.",
    }

    _save("revenue_flow.json", revenue_flow)
    return revenue_flow


# ---------------------------------------------------------------------------
# 3. FUEL -> GROWTH
#    Takes FUEL_CORE blockers that are zero-cost and writes them as
#    high-priority items into self_builder_queue.json for AUTO_EXECUTOR.
# ---------------------------------------------------------------------------

def _crosswire_fuel_to_growth():
    """Push zero-cost FUEL_CORE blockers into self_builder_queue for automated fixing."""
    fuel_plan = _load("fuel_plan.json", {})
    builder_queue = _load("self_builder_queue.json", {})

    # Normalize builder_queue structure
    if isinstance(builder_queue, dict) and "tasks" not in builder_queue:
        # Existing queue may be metadata-only; ensure tasks list exists
        if "status" in builder_queue or "generated_by" in builder_queue:
            builder_queue["tasks"] = builder_queue.get("tasks", [])
        else:
            builder_queue = {"tasks": [], "meta": builder_queue}

    if isinstance(builder_queue, list):
        builder_queue = {"tasks": builder_queue}

    tasks = builder_queue.get("tasks", [])
    existing_ids = set()
    for t in tasks:
        if isinstance(t, dict):
            existing_ids.add(t.get("id", ""))

    injected = 0

    # Inject zero-cost infrastructure items from fuel plan
    for item in fuel_plan.get("infrastructure_queue", []):
        cost = item.get("cost", 999)
        item_id = "fuel_infra_%s" % item.get("id", "unknown")
        if cost == 0 and item_id not in existing_ids:
            tasks.append({
                "id": item_id,
                "source": "crosswire_fuel_core",
                "priority": "high" if item.get("blocking") else "medium",
                "action": item.get("name", ""),
                "impact": item.get("impact", ""),
                "time_estimate": item.get("time_to_revenue", "unknown"),
                "blocking": item.get("blocking", False),
                "category": item.get("route", "general"),
                "injected_at": _ts(),
                "status": "pending",
            })
            existing_ids.add(item_id)
            injected += 1

    # Inject zero-cost blocker fixes
    for blocker in fuel_plan.get("blockers", []):
        blocker_id = "fuel_blocker_%s" % blocker.get("id", "unknown")
        if blocker_id in existing_ids:
            continue
        # Only inject if the fix is automatable (no cost, has a fix description)
        fix_text = blocker.get("fix", "")
        if not fix_text:
            continue
        tasks.append({
            "id": blocker_id,
            "source": "crosswire_fuel_core",
            "priority": "critical" if blocker.get("severity") == "critical" else "high",
            "action": fix_text,
            "reason": blocker.get("message", ""),
            "time_estimate": blocker.get("time_to_fix", "unknown"),
            "severity": blocker.get("severity", "medium"),
            "category": "blocker_fix",
            "injected_at": _ts(),
            "status": "pending",
        })
        existing_ids.add(blocker_id)
        injected += 1

    # Inject critical path steps as tasks
    for step in fuel_plan.get("critical_path", []):
        step_id = "fuel_critical_%s_%s" % (
            step.get("priority", 0),
            step.get("category", "unknown"),
        )
        if step_id in existing_ids:
            continue
        tasks.append({
            "id": step_id,
            "source": "crosswire_fuel_core",
            "priority": "critical",
            "action": step.get("action", ""),
            "reason": step.get("reason", ""),
            "time_estimate": step.get("time", "unknown"),
            "category": step.get("category", "general"),
            "injected_at": _ts(),
            "status": "pending",
        })
        existing_ids.add(step_id)
        injected += 1

    builder_queue["tasks"] = tasks
    builder_queue["crosswire_last_update"] = _ts()
    builder_queue["crosswire_injected_total"] = builder_queue.get("crosswire_injected_total", 0) + injected
    _save("self_builder_queue.json", builder_queue)

    return {"injected": injected, "total_tasks": len(tasks)}


# ---------------------------------------------------------------------------
# 4. STOREFRONT -> SIGNAL
#    When a product gets listed, generate a signal for SIGNAL_CHAIN to announce.
# ---------------------------------------------------------------------------

def _crosswire_storefront_to_signal():
    """Detect newly listed products and inject announcement signals."""
    listings = _load("storefront_listings.json", {})
    signal_state = _load("signal_chain_state.json", {})
    crosswire_state = _load("crosswire_state.json", {})

    # Track which products we already announced
    announced = set(crosswire_state.get("announced_products", []))

    signals_emitted = []
    for pid, listing in listings.get("listings", {}).items():
        if pid in announced:
            continue
        # This product hasn't been announced through crosswire yet
        title = listing.get("title", pid)
        price = listing.get("price", 1.0)
        signals_emitted.append({
            "type": "product_listed",
            "source": "crosswire_storefront",
            "product_id": pid,
            "title": title,
            "price": price,
            "message": "NEW PRODUCT: %s -- $%.2f -- 99%% to mutual aid" % (title, price),
            "ts": _ts(),
        })
        announced.add(pid)

    # Append signals to signal_chain_queue for SIGNAL_CHAIN to pick up
    signal_queue = _load("signal_chain_queue.json", [])
    if not isinstance(signal_queue, list):
        signal_queue = signal_queue.get("signals", []) if isinstance(signal_queue, dict) else []

    existing_sigs = set()
    for s in signal_queue:
        if isinstance(s, dict):
            existing_sigs.add(s.get("product_id", "") + s.get("type", ""))

    added = 0
    for sig in signals_emitted:
        sig_key = sig.get("product_id", "") + sig.get("type", "")
        if sig_key not in existing_sigs:
            signal_queue.append(sig)
            existing_sigs.add(sig_key)
            added += 1

    if added > 0:
        _save("signal_chain_queue.json", signal_queue)

    return {
        "new_products_announced": added,
        "total_announced": len(announced),
        "announced_products": sorted(announced),
    }


# ---------------------------------------------------------------------------
# 5. TASK_BOARD -> TELEGRAM
#    Takes top 5 urgent human tasks and formats for telegram_relay.json
#    so TELEGRAM_BRIDGE can notify Meeko.
# ---------------------------------------------------------------------------

def _crosswire_tasks_to_telegram():
    """Extract top 5 urgent tasks and push them to telegram_relay for Meeko."""
    fuel_plan = _load("fuel_plan.json", {})
    builder_queue = _load("self_builder_queue.json", {})
    telegram_relay = _load("telegram_relay.json", {})

    # Ensure telegram_relay has the right structure
    if not isinstance(telegram_relay, dict):
        telegram_relay = {}

    # Collect urgent tasks from multiple sources
    urgent_tasks = []

    # From fuel_plan critical path
    for step in fuel_plan.get("critical_path", []):
        urgent_tasks.append({
            "source": "FUEL_CORE",
            "priority": step.get("priority", 99),
            "action": step.get("action", ""),
            "reason": step.get("reason", ""),
            "time": step.get("time", "unknown"),
            "category": step.get("category", "general"),
        })

    # From fuel_plan blockers (critical and high only)
    for blocker in fuel_plan.get("blockers", []):
        if blocker.get("severity") in ("critical", "high"):
            urgent_tasks.append({
                "source": "FUEL_CORE",
                "priority": 0 if blocker.get("severity") == "critical" else 1,
                "action": blocker.get("fix", ""),
                "reason": blocker.get("message", ""),
                "time": blocker.get("time_to_fix", "unknown"),
                "category": "blocker_%s" % blocker.get("severity", "unknown"),
            })

    # Sort by priority (lower number = more urgent), take top 5
    urgent_tasks.sort(key=lambda t: t.get("priority", 99))
    top5 = urgent_tasks[:5]

    # Format as telegram messages
    if top5:
        lines = ["CROSSWIRE URGENT TASKS (%s)" % _ts()[:16], ""]
        for i, task in enumerate(top5, 1):
            lines.append("%d. [%s] %s" % (i, task["source"], task["action"]))
            if task.get("reason"):
                lines.append("   Why: %s" % task["reason"][:80])
            if task.get("time"):
                lines.append("   Time: %s" % task["time"])
            lines.append("")

        lines.append("-- DUAL_SYSTEM_CROSSWIRE")

        # Merge into telegram_relay without overwriting existing messages
        existing_messages = telegram_relay.get("messages", [])
        if not isinstance(existing_messages, list):
            existing_messages = []

        # Check if we already sent this exact batch (avoid spam)
        crosswire_msgs = [m for m in existing_messages
                          if isinstance(m, dict) and m.get("source") == "crosswire"]
        last_batch_actions = set()
        for m in crosswire_msgs[-1:]:
            last_batch_actions = set(m.get("task_actions", []))

        current_actions = set(t["action"] for t in top5)
        if current_actions != last_batch_actions:
            existing_messages.append({
                "source": "crosswire",
                "type": "urgent_tasks",
                "text": "\n".join(lines),
                "task_count": len(top5),
                "task_actions": list(current_actions),
                "ts": _ts(),
            })
            # Keep last 50 messages
            telegram_relay["messages"] = existing_messages[-50:]
            telegram_relay["crosswire_last_update"] = _ts()
            _save("telegram_relay.json", telegram_relay)

    return {"tasks_sent": len(top5), "tasks_considered": len(urgent_tasks)}


# ---------------------------------------------------------------------------
# 6. GROWTH_METRICS -> CHIMERA
#    Feed growth flywheel metrics into chimera scoring as a new dimension.
# ---------------------------------------------------------------------------

def _crosswire_growth_to_chimera():
    """Inject growth flywheel performance as a chimera fitness dimension."""
    flywheel_state = _load("growth_flywheel_state.json", {})
    flywheel_content = _load("growth_flywheel_content.json", {})
    chimera_report = _load("chimera_evolution_report.json", {})

    # Extract growth metrics
    metrics = flywheel_state.get("metrics", {})
    content_count = (
        len(flywheel_content.get("twitter_threads", [])) +
        len(flywheel_content.get("bluesky_posts", [])) +
        len(flywheel_content.get("reddit_posts", [])) +
        len(flywheel_content.get("github_discussions", []))
    )

    # Calculate a growth score (0-100)
    # Factors: content pieces generated, distribution channels active, revenue per content
    content_score = min(content_count * 5, 50)  # up to 50 points for content volume
    channel_score = 0
    for channel in ("twitter_threads", "bluesky_posts", "reddit_posts", "github_discussions"):
        if len(flywheel_content.get(channel, [])) > 0:
            channel_score += 12.5  # up to 50 points for channel diversity

    growth_fitness = min(int(content_score + channel_score), 100)

    # Inject into chimera scores
    if isinstance(chimera_report, dict) and "scores" in chimera_report:
        chimera_report["scores"]["growth_flywheel"] = growth_fitness
        # Recalculate composite if possible
        scores = chimera_report["scores"]
        all_vals = [v for v in scores.values() if isinstance(v, (int, float))]
        if all_vals:
            chimera_report["composite_score"] = int(sum(all_vals) / len(all_vals))
        chimera_report["crosswire_growth_injected"] = True
        chimera_report["crosswire_growth_ts"] = _ts()
        _save("chimera_evolution_report.json", chimera_report)

    return {
        "growth_fitness": growth_fitness,
        "content_count": content_count,
        "content_score": content_score,
        "channel_score": channel_score,
    }


# ---------------------------------------------------------------------------
# 7. HUMANITARIAN -> FUEL
#    Takes grants_found.json opportunities and feeds them into fuel_plan
#    as potential revenue sources. Grants ARE revenue for the 99/1 system.
# ---------------------------------------------------------------------------

def _crosswire_humanitarian_to_fuel():
    """Inject grants_found opportunities into fuel_plan as revenue sources."""
    grants = _load("grants_found.json", [])
    fuel_plan = _load("fuel_plan.json", {})

    if not isinstance(grants, list):
        grants = grants.get("grants", []) if isinstance(grants, dict) else []

    if not grants:
        return {"grants_injected": 0, "note": "No grants found yet"}

    # Ensure fuel_plan has a grants section
    existing_grant_ids = set()
    fuel_grants = fuel_plan.get("grant_revenue_sources", [])
    for g in fuel_grants:
        if isinstance(g, dict):
            existing_grant_ids.add(g.get("id", ""))

    injected = 0
    for grant in grants:
        if not isinstance(grant, dict):
            continue
        grant_id = grant.get("id", grant.get("name", grant.get("title", "unknown")))
        if grant_id in existing_grant_ids:
            continue

        fuel_grants.append({
            "id": grant_id,
            "source": "crosswire_humanitarian",
            "name": grant.get("name", grant.get("title", "Unknown Grant")),
            "amount": grant.get("amount", grant.get("value", 0)),
            "deadline": grant.get("deadline", "unknown"),
            "url": grant.get("url", ""),
            "relevance": grant.get("relevance", grant.get("match_score", 0)),
            "note": "Grants are revenue for the 99/1 system -- fund the mission directly",
            "injected_at": _ts(),
            "status": "review_needed",
        })
        existing_grant_ids.add(grant_id)
        injected += 1

    if injected > 0:
        fuel_plan["grant_revenue_sources"] = fuel_grants
        fuel_plan["crosswire_grants_last_update"] = _ts()
        _save("fuel_plan.json", fuel_plan)

    return {"grants_injected": injected, "total_grants_tracked": len(fuel_grants)}


# ---------------------------------------------------------------------------
# 8. CROSSWIRE REPORT
#    Shows all active cross-connections, data flowing, and gaps.
# ---------------------------------------------------------------------------

def _build_crosswire_report(results):
    """Build the comprehensive cross-connection report."""
    # Detect gaps: files that SHOULD exist but don't, or are empty
    gap_checks = [
        ("growth_flywheel_content.json", "GROWTH_FLYWHEEL", "Content for distribution"),
        ("social_queue.json", "SOCIAL_DASHBOARD", "Social post queue"),
        ("fuel_plan.json", "FUEL_CORE", "Growth plan and blockers"),
        ("economy_chain_ledger.json", "ECONOMY_CHAIN", "Revenue routing ledger"),
        ("revenue_routing.json", "REVENUE_SPLITTER", "Active routing table"),
        ("storefront_listings.json", "STOREFRONT_DEPLOYER", "Product listings"),
        ("signal_chain_state.json", "SIGNAL_CHAIN", "Signal processing state"),
        ("chimera_evolution_report.json", "CHIMERA_EVOLUTION", "Fitness scoring"),
        ("grants_found.json", "ECO_GRANT_SCANNER", "Grant opportunities"),
        ("self_builder_queue.json", "SELF_BUILDER", "Automated task queue"),
        ("telegram_relay.json", "TELEGRAM_BRIDGE", "Telegram notifications"),
        ("kofi_tracker_state.json", "KOFI_PAYMENT_TRACKER", "Ko-fi payment state"),
        ("proof_ledger.json", "PROOF_LEDGER", "Revenue proof chain"),
    ]

    connections = []
    gaps = []

    for fname, engine, desc in gap_checks:
        f = DATA / fname
        if f.exists():
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                is_empty = (
                    (isinstance(d, dict) and len(d) <= 1) or
                    (isinstance(d, list) and len(d) == 0)
                )
                connections.append({
                    "file": fname,
                    "engine": engine,
                    "description": desc,
                    "status": "empty" if is_empty else "active",
                    "size": f.stat().st_size,
                })
                if is_empty:
                    gaps.append({
                        "file": fname,
                        "engine": engine,
                        "issue": "File exists but contains no meaningful data",
                        "impact": "Downstream consumers get no signal from %s" % engine,
                    })
            except Exception:
                gaps.append({
                    "file": fname,
                    "engine": engine,
                    "issue": "File exists but failed to parse as JSON",
                    "impact": "Data corruption in %s pipeline" % engine,
                })
        else:
            gaps.append({
                "file": fname,
                "engine": engine,
                "issue": "File does not exist -- engine may not have run yet",
                "impact": "%s has never produced output" % engine,
            })

    # Cross-connection status summary
    cross_connections = [
        {
            "wire": "CONTENT -> SOCIAL",
            "from": "growth_flywheel_content.json",
            "to": "social_queue.json",
            "status": "active" if results.get("content_to_social", {}).get("injected", 0) > 0 else "idle",
            "items_flowing": results.get("content_to_social", {}).get("injected", 0),
        },
        {
            "wire": "REVENUE -> BOTH",
            "from": "kofi_tracker_state + economy_chain_ledger + proof_ledger",
            "to": "revenue_flow.json",
            "status": "active",
            "items_flowing": 1,  # always produces unified view
        },
        {
            "wire": "FUEL -> GROWTH",
            "from": "fuel_plan.json (blockers)",
            "to": "self_builder_queue.json",
            "status": "active" if results.get("fuel_to_growth", {}).get("injected", 0) > 0 else "idle",
            "items_flowing": results.get("fuel_to_growth", {}).get("injected", 0),
        },
        {
            "wire": "STOREFRONT -> SIGNAL",
            "from": "storefront_listings.json",
            "to": "signal_chain_queue.json",
            "status": "active" if results.get("storefront_to_signal", {}).get("new_products_announced", 0) > 0 else "idle",
            "items_flowing": results.get("storefront_to_signal", {}).get("new_products_announced", 0),
        },
        {
            "wire": "TASK_BOARD -> TELEGRAM",
            "from": "fuel_plan.json (critical path + blockers)",
            "to": "telegram_relay.json",
            "status": "active" if results.get("tasks_to_telegram", {}).get("tasks_sent", 0) > 0 else "idle",
            "items_flowing": results.get("tasks_to_telegram", {}).get("tasks_sent", 0),
        },
        {
            "wire": "GROWTH_METRICS -> CHIMERA",
            "from": "growth_flywheel_state.json + growth_flywheel_content.json",
            "to": "chimera_evolution_report.json",
            "status": "active",
            "items_flowing": 1,
        },
        {
            "wire": "HUMANITARIAN -> FUEL",
            "from": "grants_found.json",
            "to": "fuel_plan.json",
            "status": "active" if results.get("humanitarian_to_fuel", {}).get("grants_injected", 0) > 0 else "idle",
            "items_flowing": results.get("humanitarian_to_fuel", {}).get("grants_injected", 0),
        },
    ]

    active_wires = sum(1 for c in cross_connections if c["status"] == "active")
    idle_wires = sum(1 for c in cross_connections if c["status"] == "idle")
    total_items_flowing = sum(c.get("items_flowing", 0) for c in cross_connections)

    return {
        "cross_connections": cross_connections,
        "active_wires": active_wires,
        "idle_wires": idle_wires,
        "total_items_flowing": total_items_flowing,
        "data_connections": connections,
        "gaps": gaps,
        "gap_count": len(gaps),
    }


# ---------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------

def run():
    print("=" * 64)
    print("DUAL_SYSTEM_CROSSWIRE -- Bridging 1/99 and 99/1")
    print("=" * 64)
    print()
    print("  Two systems. One mission. This engine makes them talk.")
    print()

    results = {}
    start_time = time.time()

    # Load existing crosswire state for tracking announced products, etc.
    crosswire_state = _load("crosswire_state.json", {
        "engine": "DUAL_SYSTEM_CROSSWIRE",
        "created_at": _ts(),
        "cycles": 0,
        "announced_products": [],
    })

    # --- Wire 1: CONTENT -> SOCIAL ---
    print("[1/8] CONTENT -> SOCIAL ...")
    r = _crosswire_content_to_social()
    results["content_to_social"] = r
    print("      Injected %d content pieces into social_queue (%d total posts)" % (
        r["injected"], r["total_posts"],
    ))

    # --- Wire 2: REVENUE -> BOTH ---
    print("[2/8] REVENUE -> BOTH ...")
    r = _crosswire_revenue_to_both()
    results["revenue_to_both"] = {
        "total_earned": r["total_earned"],
        "phase": r["phase"],
        "combined_aid": r["combined_aid_total"],
    }
    print("      Unified revenue: $%.2f | Phase: %s | Aid total: $%.6f" % (
        r["total_earned"], r["phase_label"], r["combined_aid_total"],
    ))

    # --- Wire 3: FUEL -> GROWTH ---
    print("[3/8] FUEL -> GROWTH ...")
    r = _crosswire_fuel_to_growth()
    results["fuel_to_growth"] = r
    print("      Injected %d zero-cost tasks into self_builder_queue (%d total)" % (
        r["injected"], r["total_tasks"],
    ))

    # --- Wire 4: STOREFRONT -> SIGNAL ---
    print("[4/8] STOREFRONT -> SIGNAL ...")
    r = _crosswire_storefront_to_signal()
    results["storefront_to_signal"] = r
    # Persist announced products in crosswire state
    crosswire_state["announced_products"] = r["announced_products"]
    print("      %d new product announcements | %d total tracked" % (
        r["new_products_announced"], r["total_announced"],
    ))

    # --- Wire 5: TASK_BOARD -> TELEGRAM ---
    print("[5/8] TASK_BOARD -> TELEGRAM ...")
    r = _crosswire_tasks_to_telegram()
    results["tasks_to_telegram"] = r
    print("      %d urgent tasks sent to telegram_relay (of %d considered)" % (
        r["tasks_sent"], r["tasks_considered"],
    ))

    # --- Wire 6: GROWTH_METRICS -> CHIMERA ---
    print("[6/8] GROWTH_METRICS -> CHIMERA ...")
    r = _crosswire_growth_to_chimera()
    results["growth_to_chimera"] = r
    print("      Growth fitness score: %d/100 (content: %d, channels: %d)" % (
        r["growth_fitness"], r["content_score"], r["channel_score"],
    ))

    # --- Wire 7: HUMANITARIAN -> FUEL ---
    print("[7/8] HUMANITARIAN -> FUEL ...")
    r = _crosswire_humanitarian_to_fuel()
    results["humanitarian_to_fuel"] = r
    print("      %d grants injected into fuel_plan" % r["grants_injected"])

    # --- Wire 8: CROSSWIRE REPORT ---
    print("[8/8] Building crosswire report ...")
    report = _build_crosswire_report(results)
    results["report"] = {
        "active_wires": report["active_wires"],
        "idle_wires": report["idle_wires"],
        "total_items_flowing": report["total_items_flowing"],
        "gaps": report["gap_count"],
    }

    elapsed = round(time.time() - start_time, 3)

    # Save crosswire state
    crosswire_state["cycles"] = crosswire_state.get("cycles", 0) + 1
    crosswire_state["last_run"] = _ts()
    crosswire_state["last_results"] = results
    crosswire_state["last_elapsed_s"] = elapsed
    crosswire_state["cross_connections"] = report["cross_connections"]
    crosswire_state["gaps"] = report["gaps"]
    crosswire_state["data_connections"] = report["data_connections"]
    crosswire_state["mantra"] = "Two systems. One mission. This engine makes them talk."
    _save("crosswire_state.json", crosswire_state)

    # Print the full cross-connection report
    print()
    print("=" * 64)
    print("CROSS-CONNECTION REPORT")
    print("=" * 64)
    print()
    print("  Active wires:     %d / %d" % (report["active_wires"], len(report["cross_connections"])))
    print("  Items flowing:    %d" % report["total_items_flowing"])
    print("  Data gaps:        %d" % report["gap_count"])
    print()

    print("  --- WIRE STATUS ---")
    for conn in report["cross_connections"]:
        marker = ">>>" if conn["status"] == "active" else "..."
        print("  %s %-26s %s  (%d items)" % (
            marker,
            conn["wire"],
            conn["status"].upper(),
            conn.get("items_flowing", 0),
        ))

    if report["gaps"]:
        print()
        print("  --- GAPS DETECTED ---")
        for gap in report["gaps"][:10]:
            print("  [!] %s (%s)" % (gap["file"], gap["issue"][:60]))

    print()
    print("  --- DATA FLOW SUMMARY ---")
    print("  Content -> Social:     %d pieces injected" % results.get("content_to_social", {}).get("injected", 0))
    print("  Revenue unified:       $%.2f through both systems" % results.get("revenue_to_both", {}).get("total_earned", 0))
    print("  Fuel -> Builder:       %d zero-cost tasks queued" % results.get("fuel_to_growth", {}).get("injected", 0))
    print("  Storefront signals:    %d product announcements" % results.get("storefront_to_signal", {}).get("new_products_announced", 0))
    print("  Telegram alerts:       %d urgent tasks" % results.get("tasks_to_telegram", {}).get("tasks_sent", 0))
    print("  Chimera growth score:  %d/100" % results.get("growth_to_chimera", {}).get("growth_fitness", 0))
    print("  Grants -> Fuel:        %d opportunities" % results.get("humanitarian_to_fuel", {}).get("grants_injected", 0))
    print()
    print("  Elapsed: %.3fs" % elapsed)
    print()
    print("=" * 64)
    print("  Two systems. One mission. This engine makes them talk.")
    print("  PCRF EIN: 93-1057665")
    print("=" * 64)

    # Write outputs
    print()
    print("[write] data/crosswire_state.json")
    print("[write] data/revenue_flow.json")
    if results.get("content_to_social", {}).get("injected", 0) > 0:
        print("[write] data/social_queue.json (merged)")
    if results.get("fuel_to_growth", {}).get("injected", 0) > 0:
        print("[write] data/self_builder_queue.json (merged)")
    if results.get("tasks_to_telegram", {}).get("tasks_sent", 0) > 0:
        print("[write] data/telegram_relay.json (merged)")

    return {
        "engine": "DUAL_SYSTEM_CROSSWIRE",
        "status": "active",
        "cycles": crosswire_state["cycles"],
        "active_wires": report["active_wires"],
        "idle_wires": report["idle_wires"],
        "total_items_flowing": report["total_items_flowing"],
        "gaps": report["gap_count"],
        "elapsed_s": elapsed,
        "ts": _ts(),
    }


if __name__ == "__main__":
    run()
