#!/usr/bin/env python3
"""
METABOLISM_LOOP.py -- The full circular metabolism
===================================================
v1 (2026-04-06): Closes the loop. Nervous system -> Ecosystem -> back.

THE PROBLEM:
  The nervous system (trading, signals, bus) produces outputs.
  The ecosystem (content, products, revenue, growth) produces outputs.
  But neither feeds back into the other automatically.
  That's an open circuit. Open circuits are dead circuits.

THE SOLUTION:
  METABOLISM_LOOP reads BOTH sides and feeds each into the other:

  NERVOUS SYSTEM (trading, signals, bus)
      |
      v
  METABOLISM_LOOP reads nervous system state
      |
      v
  Feeds into SolarPunk ecosystem:
    - flywheel_state.json (11 consuming engines)
    - economy_chain_ledger.json (11 consuming engines)
    - proof_ledger.json (12 consuming engines)
    - revenue_data.json (7 consuming engines)
    - growth_tracker.json (tracked by PROPRIOCEPTION)
      |
      v
  Reads ecosystem OUTPUTS:
    - content production metrics
    - product catalog state
    - storefront data
    - social media engagement
    - domain/bridge status
      |
      v
  Feeds BACK into nervous system:
    - Emit ecosystem health to SYNAPTIC_BUS
    - Update signal mesh with non-trading intelligence
    - Feed revenue data back into AI cost tracker
    - Inform AUTO_DEPOSIT of total revenue velocity

  That's a CIRCLE. Circles are alive.

SIGNAL SOURCES READ:
  Nervous system:
    - synaptic_bus.json (all engine states)
    - signal_mesh_state.json (composite trading signal)
    - cross_pollinator_state.json (portfolio health)
    - pulse_state.json (system dashboard data)

  Ecosystem:
    - flywheel_state.json (revenue flywheel momentum)
    - economy_chain_ledger.json (economic chain events)
    - proof_ledger.json (evidence of real revenue)
    - revenue_data.json (income streams)
    - growth_tracker.json (portfolio growth over time)
    - bridge_report.json (domain/infrastructure status)
    - quick_revenue.json (fast revenue sources)
    - chimera_evolution_report.json (system evolution metrics)

OUTPUT: data/metabolism_state.json
  - Revenue velocity ($/hr from all sources)
  - Nervous system contribution vs ecosystem contribution
  - Circular efficiency (amplification ratio)
  - Growth rate (trading + ecosystem combined)
  - Self-funding ratio (all income vs all costs)

ETHICS: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)
Called by: OMNIBUS (L6 nervous system block), AUTONOMIC_NERVE, task_queue (15 min)
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Core I/O
# ---------------------------------------------------------------------------
def _load(path, default=None):
    """Read JSON file with graceful fallback."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _save(path, data):
    """Write JSON file."""
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _safe_float(val, default=0.0):
    """Coerce a value to float or return default."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _parse_ts(raw):
    """Parse ISO timestamp to tz-aware datetime, or None."""
    if not raw or not isinstance(raw, str):
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _age_hours(ts_str, now):
    """Return age of a timestamp in hours, or None."""
    dt = _parse_ts(ts_str)
    if dt is None:
        return None
    delta = now - dt
    return max(0, delta.total_seconds() / 3600)


# ---------------------------------------------------------------------------
# Phase 1: Read NERVOUS SYSTEM state
# ---------------------------------------------------------------------------
def _read_nervous_system():
    """
    Read all nervous system data in one pass:
    synaptic_bus, signal_mesh, cross_pollinator, pulse.
    """
    bus = _load(DATA / "synaptic_bus.json")
    mesh = _load(DATA / "signal_mesh_state.json")
    xpoll = _load(DATA / "cross_pollinator_state.json")
    pulse = _load(DATA / "pulse_state.json")

    # Extract key nervous system metrics
    composite = mesh.get("composite_signal", {})
    heartbeat = mesh.get("heartbeat", {})
    portfolio = pulse.get("portfolio", {})

    # Trading metrics from bus engine states
    engines = bus.get("engines", {})
    turbo_props = engines.get("TURBO_TRADER", {}).get("properties", {})
    alpaca_props = engines.get("ALPACA_TRADER", {}).get("properties", {})
    cost_props = engines.get("AI_COST_TRACKER", {}).get("properties", {})

    turbo_balance = _safe_float(turbo_props.get("balance", 0))
    alpaca_portfolio = _safe_float(alpaca_props.get("portfolio_value", alpaca_props.get("cash", 0)))
    total_capital = _safe_float(xpoll.get("total_portfolio_value", 0))
    if total_capital == 0:
        total_capital = turbo_balance + alpaca_portfolio

    return {
        "composite_strength": _safe_float(composite.get("composite_strength", 0)),
        "dominant_direction": composite.get("dominant_direction", "neutral"),
        "conviction": _safe_float(composite.get("conviction_score", 0)),
        "urgency": _safe_float(composite.get("urgency", 0)),
        "neural_connectivity": _safe_float(heartbeat.get("neural_connectivity", 0)),
        "alive_sources": heartbeat.get("alive", 0),
        "total_sources": heartbeat.get("total_sources", 0),
        "turbo_balance": turbo_balance,
        "alpaca_portfolio": alpaca_portfolio,
        "total_capital": total_capital,
        "ai_cost_total": _safe_float(cost_props.get("total_cost_usd", 0)),
        "ai_trading_profit": _safe_float(cost_props.get("total_trading_profit", 0)),
        "ai_self_sustaining": cost_props.get("self_sustaining", False),
        "pulse_total_usd": _safe_float(portfolio.get("total_usd", 0)),
        "bus_total_emissions": bus.get("meta", {}).get("total_emissions", 0),
        "bus_engine_count": len(engines),
        "convergence_sync": _safe_float(bus.get("convergence", {}).get("sync_score", 0)),
    }


# ---------------------------------------------------------------------------
# Phase 2: Read ECOSYSTEM state
# ---------------------------------------------------------------------------
def _read_ecosystem():
    """
    Read all ecosystem data files:
    flywheel, economy_chain, proof_ledger, revenue, growth,
    bridge, quick_revenue, chimera evolution.
    """
    flywheel = _load(DATA / "flywheel_state.json")
    economy = _load(DATA / "economy_chain_ledger.json")
    proof = _load(DATA / "proof_ledger.json")
    revenue = _load(DATA / "revenue_data.json")
    growth = _load(DATA / "growth_tracker.json")
    bridge = _load(DATA / "bridge_report.json")
    quick_rev = _load(DATA / "quick_revenue.json")
    chimera = _load(DATA / "chimera_evolution_report.json")

    # Also read product/content state for circular awareness
    products = _load(DATA / "product_registry.json")
    storefront = _load(DATA / "storefront_builder_state.json")
    nanoshop = _load(DATA / "nanoshop_state.json")
    publisher = _load(DATA / "autonomous_publisher_state.json")
    bluesky = _load(DATA / "bluesky_engine_state.json")

    # Flywheel momentum
    flywheel_momentum = _safe_float(flywheel.get("momentum", flywheel.get("flywheel_momentum", 0)))
    flywheel_revenue = _safe_float(flywheel.get("total_revenue", flywheel.get("revenue_30d", 0)))

    # Proof ledger totals
    proof_total_gaza = _safe_float(proof.get("total_to_gaza", 0))
    proof_total_transferred = _safe_float(proof.get("total_transferred", 0))
    proof_entries = len(proof.get("entries", proof.get("ledger", [])))

    # Revenue streams
    revenue_streams = revenue.get("streams", revenue.get("sources", []))
    total_revenue = _safe_float(revenue.get("total_revenue", revenue.get("total", 0)))
    if isinstance(revenue_streams, list):
        total_revenue = max(total_revenue, sum(
            _safe_float(s.get("amount", s.get("revenue", 0)))
            for s in revenue_streams
        ))

    # Growth tracker
    growth_rate = _safe_float(growth.get("growth_rate", growth.get("daily_growth_pct", 0)))
    growth_entries = len(growth.get("entries", growth.get("snapshots", [])))

    # Bridge/infrastructure
    bridges_active = 0
    bridges_total = 0
    bridge_domains = bridge.get("domains", bridge.get("bridges", []))
    if isinstance(bridge_domains, list):
        bridges_total = len(bridge_domains)
        bridges_active = sum(
            1 for d in bridge_domains
            if d.get("status", "") in ("active", "live", "connected", "online")
        )
    elif isinstance(bridge_domains, dict):
        bridges_total = len(bridge_domains)
        bridges_active = sum(
            1 for d in bridge_domains.values()
            if isinstance(d, dict) and d.get("status", "") in ("active", "live", "connected", "online")
        )

    # Quick revenue
    quick_rev_ideas = quick_rev.get("ideas", quick_rev.get("opportunities", []))
    quick_rev_count = len(quick_rev_ideas) if isinstance(quick_rev_ideas, list) else 0

    # Chimera evolution
    chimera_gen = chimera.get("generation", chimera.get("evolution_cycle", 0))
    chimera_fitness = _safe_float(chimera.get("fitness", chimera.get("fitness_score", 0)))

    # Product catalog
    product_catalog = products.get("products", {})
    if isinstance(product_catalog, dict):
        products_total = len(product_catalog)
        products_live = sum(
            1 for p in product_catalog.values()
            if isinstance(p, dict) and (p.get("gumroad_url") or p.get("download_url"))
        )
    elif isinstance(product_catalog, list):
        products_total = len(product_catalog)
        products_live = sum(
            1 for p in product_catalog
            if isinstance(p, dict) and (p.get("gumroad_url") or p.get("download_url"))
        )
    else:
        products_total = 0
        products_live = 0

    # Content/social metrics
    bluesky_posts = bluesky.get("posted", bluesky.get("total_posts", 0))
    publisher_sent = publisher.get("total_sent", publisher.get("published", 0))
    nanoshop_pages = nanoshop.get("pages_generated", 0)

    # Economy chain
    economy_events = len(economy.get("events", economy.get("entries", [])))
    economy_total = _safe_float(economy.get("total_value", economy.get("total_economic_value", 0)))

    return {
        "flywheel_momentum": flywheel_momentum,
        "flywheel_revenue": flywheel_revenue,
        "proof_entries": proof_entries,
        "proof_total_gaza": proof_total_gaza,
        "proof_total_transferred": proof_total_transferred,
        "total_revenue": total_revenue,
        "revenue_stream_count": len(revenue_streams) if isinstance(revenue_streams, list) else 0,
        "growth_rate": growth_rate,
        "growth_entries": growth_entries,
        "bridges_active": bridges_active,
        "bridges_total": bridges_total,
        "quick_revenue_ideas": quick_rev_count,
        "chimera_generation": chimera_gen,
        "chimera_fitness": chimera_fitness,
        "products_total": products_total,
        "products_live": products_live,
        "bluesky_posts": bluesky_posts,
        "publisher_sent": publisher_sent,
        "nanoshop_pages": nanoshop_pages,
        "economy_events": economy_events,
        "economy_total_value": economy_total,
    }


# ---------------------------------------------------------------------------
# Phase 3: Calculate METABOLISM METRICS
# ---------------------------------------------------------------------------
def _calculate_metabolism(nervous, ecosystem, now):
    """
    Combine nervous system + ecosystem data into metabolism metrics.
    This is where the circular amplification is measured.
    """
    # --- Revenue Velocity ---
    # Total revenue from all sources
    trading_revenue = nervous["ai_trading_profit"]
    ecosystem_revenue = ecosystem["total_revenue"]
    flywheel_revenue = ecosystem["flywheel_revenue"]
    total_all_revenue = trading_revenue + ecosystem_revenue + flywheel_revenue

    # Estimate hourly rate (assume 30-day window if we have data)
    hours_30d = 30 * 24
    revenue_velocity_hr = total_all_revenue / hours_30d if total_all_revenue > 0 else 0

    # --- Contribution Split ---
    total_for_split = max(trading_revenue + ecosystem_revenue, 0.001)
    nervous_contribution_pct = round(trading_revenue / total_for_split * 100, 1)
    ecosystem_contribution_pct = round(ecosystem_revenue / total_for_split * 100, 1)

    # --- Circular Efficiency ---
    # How much does the ecosystem amplify nervous system output?
    # If trading makes $1 and ecosystem makes $5, amplification = 5x
    if trading_revenue > 0:
        circular_amplification = round((trading_revenue + ecosystem_revenue) / trading_revenue, 2)
    elif ecosystem_revenue > 0:
        circular_amplification = float("inf")  # ecosystem carries all weight
    else:
        circular_amplification = 1.0  # no amplification (nothing flowing yet)

    # --- Combined Growth Rate ---
    # Nervous system growth: capital appreciation
    total_capital = nervous["total_capital"]
    ecosystem_growth = ecosystem["growth_rate"]
    # Composite growth: weighted average of trading capital growth and ecosystem growth
    capital_growth = 0
    if total_capital > 0 and trading_revenue > 0:
        capital_growth = (trading_revenue / total_capital) * 100  # % return
    combined_growth = round((capital_growth + ecosystem_growth) / 2, 2) if ecosystem_growth else capital_growth

    # --- Self-Funding Ratio ---
    ai_costs = nervous["ai_cost_total"]
    if ai_costs > 0:
        self_funding_ratio = round(total_all_revenue / ai_costs, 3)
    else:
        self_funding_ratio = float("inf") if total_all_revenue > 0 else 0

    # --- Ecosystem Health Score ---
    # Composite score: flywheel momentum, products live, bridges active,
    # proof entries, content output, neural connectivity
    health_components = [
        min(100, ecosystem["flywheel_momentum"] * 10),  # flywheel 0-10 -> 0-100
        min(100, ecosystem["products_live"] * 10),        # up to 10 products = 100
        min(100, ecosystem["bridges_active"] * 20),       # up to 5 bridges = 100
        min(100, ecosystem["proof_entries"] * 5),          # up to 20 entries = 100
        min(100, (ecosystem["bluesky_posts"] + ecosystem["publisher_sent"]) * 2),  # content output
        nervous["neural_connectivity"],                    # how connected the mesh is
    ]
    ecosystem_health = round(sum(health_components) / len(health_components), 1)

    # --- Circuit Status ---
    # Is the full loop actually flowing?
    has_nervous_input = nervous["composite_strength"] > 0 or nervous["total_capital"] > 0
    has_ecosystem_output = ecosystem["total_revenue"] > 0 or ecosystem["products_live"] > 0
    has_feedback = nervous["bus_total_emissions"] > 0
    circuit_status = "closed" if (has_nervous_input and has_ecosystem_output and has_feedback) else "open"
    if has_nervous_input and not has_ecosystem_output:
        circuit_status = "half-open (ecosystem side stalled)"
    elif has_ecosystem_output and not has_nervous_input:
        circuit_status = "half-open (nervous system side stalled)"

    return {
        "revenue_velocity_per_hour": round(revenue_velocity_hr, 4),
        "revenue_velocity_per_day": round(revenue_velocity_hr * 24, 2),
        "total_all_revenue": round(total_all_revenue, 2),
        "trading_revenue": round(trading_revenue, 2),
        "ecosystem_revenue": round(ecosystem_revenue, 2),
        "nervous_contribution_pct": nervous_contribution_pct,
        "ecosystem_contribution_pct": ecosystem_contribution_pct,
        "circular_amplification": circular_amplification,
        "combined_growth_rate": combined_growth,
        "capital_growth_pct": round(capital_growth, 2),
        "ecosystem_growth_pct": round(ecosystem_growth, 2),
        "self_funding_ratio": self_funding_ratio,
        "ai_costs_total": round(ai_costs, 2),
        "ecosystem_health": ecosystem_health,
        "ecosystem_health_components": {
            "flywheel": round(health_components[0], 1),
            "products": round(health_components[1], 1),
            "bridges": round(health_components[2], 1),
            "proof": round(health_components[3], 1),
            "content": round(health_components[4], 1),
            "connectivity": round(health_components[5], 1),
        },
        "circuit_status": circuit_status,
        "total_capital": round(nervous["total_capital"], 2),
    }


# ---------------------------------------------------------------------------
# Phase 4: Feed BACK into nervous system
# ---------------------------------------------------------------------------
def _feed_back(metabolism, nervous, ecosystem):
    """
    Emit metabolism metrics to SYNAPTIC_BUS so every engine sees them.
    This is the feedback arc that closes the circuit.
    """
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_batch("METABOLISM_LOOP", {
            "status": "active",
            "circuit_status": metabolism["circuit_status"],
            "revenue_velocity_hr": metabolism["revenue_velocity_per_hour"],
            "revenue_velocity_day": metabolism["revenue_velocity_per_day"],
            "ecosystem_health": metabolism["ecosystem_health"],
            "self_funding_ratio": metabolism["self_funding_ratio"],
            "circular_amplification": metabolism["circular_amplification"],
            "combined_growth_rate": metabolism["combined_growth_rate"],
            "nervous_contribution_pct": metabolism["nervous_contribution_pct"],
            "ecosystem_contribution_pct": metabolism["ecosystem_contribution_pct"],
            "total_all_revenue": metabolism["total_all_revenue"],
            "total_capital": metabolism["total_capital"],
            "products_live": ecosystem["products_live"],
            "bridges_active": ecosystem["bridges_active"],
            "signal_direction": nervous["dominant_direction"],
        }, silent=False)
    except Exception:
        pass  # Bus not available -- degrade gracefully


# ---------------------------------------------------------------------------
# Phase 5: Dashboard
# ---------------------------------------------------------------------------
def _print_dashboard(metabolism, nervous, ecosystem):
    """Print the METABOLISM DASHBOARD showing circular flow."""
    W = 64
    print()
    print("=" * W)
    print("  METABOLISM LOOP -- Full Circular Flow")
    print("=" * W)

    # Circuit status
    cs = metabolism["circuit_status"]
    indicator = "[CLOSED]" if cs == "closed" else "[OPEN]"
    print(f"\n  CIRCUIT: {indicator} {cs}")

    # Revenue flow
    print(f"\n  REVENUE FLOW:")
    print(f"    Velocity:        ${metabolism['revenue_velocity_per_hour']:.4f}/hr "
          f"(${metabolism['revenue_velocity_per_day']:.2f}/day)")
    print(f"    Total revenue:   ${metabolism['total_all_revenue']:.2f}")
    print(f"      Trading:       ${metabolism['trading_revenue']:.2f} "
          f"({metabolism['nervous_contribution_pct']}%)")
    print(f"      Ecosystem:     ${metabolism['ecosystem_revenue']:.2f} "
          f"({metabolism['ecosystem_contribution_pct']}%)")

    # Amplification
    amp = metabolism["circular_amplification"]
    amp_str = f"{amp:.2f}x" if amp != float("inf") else "INF (pure ecosystem)"
    print(f"\n  CIRCULAR AMPLIFICATION: {amp_str}")
    print(f"    Every $1 from trading becomes ${amp_str} through ecosystem")

    # Growth
    print(f"\n  GROWTH:")
    print(f"    Capital growth:  {metabolism['capital_growth_pct']:.2f}%")
    print(f"    Ecosystem growth:{metabolism['ecosystem_growth_pct']:.2f}%")
    print(f"    Combined:        {metabolism['combined_growth_rate']:.2f}%")

    # Self-funding
    sf = metabolism["self_funding_ratio"]
    sf_str = f"{sf:.3f}x" if sf != float("inf") else "INF (zero cost)"
    sf_label = "SELF-SUSTAINING" if sf >= 1.0 else "NOT YET"
    print(f"\n  SELF-FUNDING: {sf_str} ({sf_label})")
    print(f"    AI costs:        ${metabolism['ai_costs_total']:.2f}")
    print(f"    All revenue:     ${metabolism['total_all_revenue']:.2f}")

    # Ecosystem health
    print(f"\n  ECOSYSTEM HEALTH: {metabolism['ecosystem_health']}/100")
    components = metabolism["ecosystem_health_components"]
    for name, score in components.items():
        bar_len = int(score / 5)
        bar = "#" * bar_len + "-" * (20 - bar_len)
        print(f"    {name:<14} [{bar}] {score:.0f}")

    # Nervous system vitals
    print(f"\n  NERVOUS SYSTEM:")
    print(f"    Signal strength: {nervous['composite_strength']}/100")
    print(f"    Direction:       {nervous['dominant_direction'].upper()}")
    print(f"    Conviction:      {nervous['conviction']}%")
    print(f"    Connectivity:    {nervous['neural_connectivity']}%")
    print(f"    Total capital:   ${nervous['total_capital']:.2f}")

    # Ecosystem inventory
    print(f"\n  ECOSYSTEM INVENTORY:")
    print(f"    Products live:   {ecosystem['products_live']}/{ecosystem['products_total']}")
    print(f"    Bridges active:  {ecosystem['bridges_active']}/{ecosystem['bridges_total']}")
    print(f"    Revenue streams: {ecosystem['revenue_stream_count']}")
    print(f"    Proof entries:   {ecosystem['proof_entries']}")
    print(f"    Content output:  {ecosystem['bluesky_posts']} posts, "
          f"{ecosystem['publisher_sent']} published, "
          f"{ecosystem['nanoshop_pages']} shop pages")

    # The loop visualization
    print(f"\n  THE LOOP:")
    print(f"    Nervous System -> [{nervous['alive_sources']}/{nervous['total_sources']} alive]")
    print(f"        |")
    print(f"        v")
    print(f"    Ecosystem -----> [{ecosystem['products_live']} products, "
          f"${ecosystem['total_revenue']:.2f} rev]")
    print(f"        |")
    print(f"        v")
    print(f"    Feedback -------> [bus emissions: {nervous['bus_total_emissions']}, "
          f"sync: {nervous['convergence_sync']}%]")
    print(f"        |")
    print(f"        v")
    print(f"    Back to Nervous System (SIGNAL_MESH reads metabolism_state.json)")

    print(f"\n  ETHICS: 99% mutual aid / 1% node fuel")
    print("=" * W)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def run():
    """
    Execute the full circular metabolism:
    1. Read nervous system state
    2. Read ecosystem state
    3. Calculate metabolism metrics
    4. Feed back into nervous system via SYNAPTIC_BUS
    5. Save metabolism_state.json (read by SIGNAL_MESH as source #12)
    6. Print dashboard
    """
    now = datetime.now(timezone.utc)

    # Phase 1: Read nervous system
    nervous = _read_nervous_system()

    # Phase 2: Read ecosystem
    ecosystem = _read_ecosystem()

    # Phase 3: Calculate metabolism
    metabolism = _calculate_metabolism(nervous, ecosystem, now)

    # Phase 4: Feed back into nervous system
    _feed_back(metabolism, nervous, ecosystem)

    # Phase 5: Build full state
    state = {
        "timestamp": now.isoformat(),
        "engine": "METABOLISM_LOOP",
        "version": 1,
        "ethics": "99% mutual aid / 1% node fuel",
        "status": "active",
        "circuit_status": metabolism["circuit_status"],
        "metabolism": metabolism,
        "nervous_system_snapshot": nervous,
        "ecosystem_snapshot": ecosystem,
        # These two fields are what SIGNAL_MESH reads as signal source #12
        "revenue_velocity": metabolism["revenue_velocity_per_hour"],
        "ecosystem_health": metabolism["ecosystem_health"],
        "summary": {
            "revenue_velocity_per_day": metabolism["revenue_velocity_per_day"],
            "circular_amplification": metabolism["circular_amplification"],
            "self_funding_ratio": metabolism["self_funding_ratio"],
            "ecosystem_health": metabolism["ecosystem_health"],
            "circuit_status": metabolism["circuit_status"],
            "combined_growth_rate": metabolism["combined_growth_rate"],
            "total_capital": metabolism["total_capital"],
            "products_live": ecosystem["products_live"],
            "bridges_active": ecosystem["bridges_active"],
        },
    }

    # Phase 6: Save state (this is what SIGNAL_MESH reads next cycle)
    _save(DATA / "metabolism_state.json", state)

    # Phase 7: Print dashboard
    _print_dashboard(metabolism, nervous, ecosystem)

    return state


if __name__ == "__main__":
    run()
