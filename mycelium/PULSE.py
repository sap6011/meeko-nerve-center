#!/usr/bin/env python3
"""
PULSE.py -- SolarPunk System Vital Signs Monitor
=================================================
Real-time ASCII dashboard showing the ENTIRE SolarPunk nervous
system's vital signs in one shot. Pure Python, zero external
dependencies. Reads every state file across trading, autonomic,
nerve-loop, and portfolio subsystems and renders a single
consolidated view.

Run:
    python mycelium/PULSE.py

Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MYCELIUM = ROOT / "mycelium"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(name):
    """Load a JSON file from data/, returning {} on any error."""
    try:
        return json.loads((DATA / name).read_text(encoding="utf-8", errors="replace"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _ts_ago(ts_str):
    """Return a human-readable 'X min ago' string from an ISO timestamp."""
    if not ts_str:
        return "unknown"
    try:
        then = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - then
        mins = int(delta.total_seconds() / 60)
        if mins < 1:
            return "just now"
        if mins < 60:
            return f"{mins} min ago"
        hours = mins // 60
        if hours < 24:
            return f"{hours}h {mins % 60}m ago"
        days = hours // 24
        return f"{days}d {hours % 24}h ago"
    except Exception:
        return "unknown"


def _fmt_usd(val):
    """Format a number as USD string."""
    try:
        v = float(val)
        if v >= 1000:
            return f"${v:,.2f}"
        return f"${v:.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def _count_engines():
    """Count .py files in mycelium/ directory."""
    try:
        return len([f for f in MYCELIUM.iterdir() if f.suffix == ".py" and f.name != "__init__.py"])
    except OSError:
        return 0


def _bar(pct, width=20):
    """Render an ASCII progress bar like [========>           ] 40%"""
    pct = max(0, min(100, pct))
    filled = int(width * pct / 100)
    bar_str = "=" * filled
    if filled < width:
        bar_str += ">"
        bar_str += " " * (width - filled - 1)
    else:
        bar_str = "=" * width
    return f"[{bar_str}] {pct:.0f}%"


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def _collect():
    """Read all state files and compute aggregate metrics."""

    turbo       = _load("turbo_trader_state.json")
    alpaca      = _load("alpaca_trader_state.json")
    ledger      = _load("trade_ledger.json")
    compound    = _load("compound_tracker.json")
    nerve       = _load("nerve_loop_state.json")
    autonomic   = _load("autonomic_state.json")
    cost        = _load("ai_cost_tracker.json")
    flywheel    = _load("flywheel_state.json")
    growth      = _load("growth_tracker.json")
    cross       = _load("cross_pollinator_state.json")

    # -- Engine count -------------------------------------------------------
    engine_count = _count_engines()

    # -- Kalshi / TURBO_TRADER ----------------------------------------------
    kalshi_fw = flywheel.get("kalshi_trading", {})
    turbo_fw  = flywheel.get("turbo_trading", {})

    kalshi_cash    = float(turbo.get("balance", turbo.get("last_known_balance", 0)))
    kalshi_pending = float(kalshi_fw.get("pending_payout", 0))
    kalshi_total   = kalshi_cash + kalshi_pending

    trades_list  = ledger.get("trades", [])
    total_trades = len(trades_list)
    success_trades = sum(1 for t in trades_list if t.get("success"))
    win_rate = round(success_trades / total_trades * 100, 1) if total_trades else 0

    # Position and trade frequency from compound snapshots
    snapshots = compound.get("snapshots", [])
    latest_snap = snapshots[-1] if snapshots else {}
    positions_open = int(latest_snap.get("positions_open", kalshi_fw.get("positions_open", 0)))
    daily_trades   = int(latest_snap.get("daily_trades", 0))
    weekly_trades  = int(latest_snap.get("weekly_trades", 0))
    # Remaining trades are longer-horizon (monthly+)
    monthly_trades = max(0, success_trades - daily_trades - weekly_trades)

    compound_cycles = int(compound.get("compound_cycles", 0))
    peak_balance    = float(compound.get("peak_balance", 0))
    initial_balance = float(compound.get("initial_balance", 0))
    growth_pct      = round((peak_balance / initial_balance - 1) * 100, 0) if initial_balance > 0 else 0

    kalshi_status = turbo.get("status", "unknown").upper().replace("_", " ")
    kalshi_ts     = turbo.get("timestamp", "")

    # -- Alpaca -------------------------------------------------------------
    alpaca_portfolio = float(alpaca.get("portfolio_value", 0))
    alpaca_cash      = float(alpaca.get("cash", 0))
    alpaca_positions = int(alpaca.get("positions_count", 0))
    alpaca_market    = alpaca.get("market_open", False)
    alpaca_next_open = alpaca.get("next_open", "")
    alpaca_opps      = int(alpaca.get("opportunities_found", 0))
    alpaca_status_raw = alpaca.get("status", "unknown")
    alpaca_ts        = alpaca.get("timestamp", "")

    # Build opportunity list
    top_opps = alpaca.get("top_opportunities", [])
    opp_symbols = []
    for opp in top_opps[:4]:
        sym = opp.get("symbol", "?")
        chg = opp.get("daily_change_pct", 0)
        if chg != 0:
            opp_symbols.append(f"{sym} {chg:+.1f}%")
        else:
            opp_symbols.append(sym)

    # Market status string
    if alpaca_market:
        market_str = "OPEN"
    else:
        next_str = ""
        if alpaca_next_open:
            try:
                nxt = datetime.fromisoformat(alpaca_next_open)
                next_str = f" (opens {nxt.strftime('%I:%M %p')} ET)"
            except Exception:
                next_str = ""
        market_str = f"CLOSED{next_str}"

    # -- Autonomic nerve ----------------------------------------------------
    ollama_online = autonomic.get("ollama_available", False)
    ai_method     = autonomic.get("decision_method", "unknown")
    heartbeat     = autonomic.get("heartbeat_interval", 60)
    auto_status   = autonomic.get("status", "unknown").upper()

    # -- Self-funding -------------------------------------------------------
    trading_profit = float(cost.get("total_trading_profit", 0))
    ai_cost        = float(cost.get("total_cost_usd", 0))
    net_profit     = float(cost.get("profit_minus_ai_cost", trading_profit - ai_cost))
    self_sustaining = cost.get("self_sustaining", net_profit >= 0)

    # Provider summary
    providers = cost.get("providers", {})
    provider_names = list(providers.keys())

    # -- Portfolio total ----------------------------------------------------
    growth_latest = {}
    growth_entries = growth.get("entries", [])
    if growth_entries:
        growth_latest = growth_entries[-1]
    elif growth.get("latest"):
        growth_latest = growth.get("latest", {})

    sol_amount   = float(growth_latest.get("total_portfolio_sol", growth.get("latest", {}).get("total_portfolio_sol", 0)))
    sol_price    = float(growth_latest.get("sol_price", growth.get("latest", {}).get("sol_price", 0)))
    sol_usd      = float(growth_latest.get("crypto_usd", growth_latest.get("total_usd", 0)))
    if sol_usd == 0 and sol_amount > 0 and sol_price > 0:
        sol_usd = sol_amount * sol_price

    portfolio_total = kalshi_total + alpaca_portfolio + sol_usd

    # -- Nerve loop ---------------------------------------------------------
    nerve_status = nerve.get("status", "unknown")
    nerve_ts     = nerve.get("timestamp", "")
    nerve_phases = nerve.get("phases", {})
    phases_total = len(nerve_phases)
    # If overall status is "complete", all phases ran (some may have 0 sub-engines)
    if nerve_status == "complete":
        phases_complete = phases_total
    else:
        phases_complete = 0
        for phase_data in nerve_phases.values():
            results = phase_data.get("results", [])
            if results:
                phases_complete += 1

    nerve_elapsed = nerve.get("elapsed_seconds", 0)

    # -- Cross-pollinator (optional) ----------------------------------------
    cross_status = cross.get("status", "")
    cross_synergies = len(cross.get("synergies", []))

    # -- Flywheel / Gaza aid ------------------------------------------------
    total_to_gaza = float(flywheel.get("total_to_gaza", 0))

    # -- Build state dict ---------------------------------------------------
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "pulse-v1",
        "engine_count": engine_count,
        "kalshi": {
            "cash": kalshi_cash,
            "pending": kalshi_pending,
            "total": kalshi_total,
            "positions_open": positions_open,
            "daily_trades": daily_trades,
            "weekly_trades": weekly_trades,
            "monthly_trades": monthly_trades,
            "total_trades": total_trades,
            "successful_trades": success_trades,
            "win_rate": win_rate,
            "compound_cycles": compound_cycles,
            "peak_balance": peak_balance,
            "growth_pct": growth_pct,
            "status": kalshi_status,
            "last_update": kalshi_ts,
        },
        "alpaca": {
            "portfolio_value": alpaca_portfolio,
            "cash": alpaca_cash,
            "positions_count": alpaca_positions,
            "market_open": alpaca_market,
            "market_str": market_str,
            "opportunities": alpaca_opps,
            "opp_symbols": opp_symbols,
            "status": alpaca_status_raw,
            "last_update": alpaca_ts,
        },
        "autonomic": {
            "ollama_online": ollama_online,
            "ai_method": ai_method,
            "heartbeat_interval": heartbeat,
            "status": auto_status,
        },
        "self_funding": {
            "trading_profit": trading_profit,
            "ai_cost": ai_cost,
            "net_profit": net_profit,
            "self_sustaining": self_sustaining,
            "providers": provider_names,
        },
        "portfolio": {
            "kalshi_total": kalshi_total,
            "alpaca_total": alpaca_portfolio,
            "sol_amount": sol_amount,
            "sol_usd": sol_usd,
            "sol_price": sol_price,
            "total_usd": portfolio_total,
        },
        "nerve_loop": {
            "status": nerve_status,
            "last_run": nerve_ts,
            "phases_complete": phases_complete,
            "phases_total": phases_total,
            "elapsed_seconds": nerve_elapsed,
        },
        "aid": {
            "total_to_gaza": total_to_gaza,
        },
    }

    return state


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _render(state):
    """Render the ASCII dashboard string from collected state."""

    lines = []
    W = 64  # dashboard width

    def sep(char="="):
        lines.append(char * W)

    def blank():
        lines.append("")

    def heading(text):
        pad = (W - len(text) - 4) // 2
        lines.append(" " * max(pad, 0) + "  " + text)

    def section(title):
        lines.append(f"  {title}")
        lines.append("  " + "-" * (W - 4))

    def field(label, value, indent=4):
        prefix = " " * indent
        label_w = 17
        lines.append(f"{prefix}{label:<{label_w}}{value}")

    # -- Header -------------------------------------------------------------
    k = state["kalshi"]
    a = state["alpaca"]
    eng = state["engine_count"]
    platforms = 0
    if k.get("total_trades", 0) > 0 or k.get("status") != "UNKNOWN":
        platforms += 1
    if a.get("status") not in ("unknown", ""):
        platforms += 1

    sep("=")
    heading(f"SOLARPUNK PULSE -- System Vital Signs")
    heading(f"{eng}+ engines | {platforms} trading platforms | 1 autonomous AI")
    sep("=")
    blank()

    # -- Trading Platforms --------------------------------------------------
    section("TRADING PLATFORMS")
    blank()

    # Kalshi
    lines.append("    KALSHI (TURBO_TRADER)")
    field("Balance:",
          f"{_fmt_usd(k['cash'])} cash + {_fmt_usd(k['pending'])} pending = {_fmt_usd(k['total'])} total")
    field("Positions:",
          f"{k['positions_open']} open ({k['daily_trades']} daily, {k['weekly_trades']} weekly, {k['monthly_trades']} monthly)")
    field("Trades:",
          f"{k['total_trades']} total | {k['successful_trades']} successful | {k['win_rate']}% win rate")
    field("Compound:",
          f"{k['compound_cycles']} cycles | Peak: {_fmt_usd(k['peak_balance'])} | Growth: {k['growth_pct']:,.0f}%")
    field("Status:",
          f"{k['status']} | Last: {_ts_ago(k['last_update'])}")

    # Win-rate bar
    field("Win Rate:", _bar(k['win_rate']))
    blank()

    # Alpaca
    lines.append("    ALPACA (stocks/ETFs/crypto)")
    if a["portfolio_value"] > 0:
        field("Portfolio:", _fmt_usd(a["portfolio_value"]))
    else:
        field("Portfolio:", f"{_fmt_usd(0)} (awaiting deposit)")
    field("Positions:", f"{a['positions_count']} open")
    field("Market:", a["market_str"])

    opp_str = f"{a['opportunities']} queued"
    if a["opp_symbols"]:
        opp_str += " (" + ", ".join(a["opp_symbols"]) + ")"
    field("Opportunities:", opp_str)

    conn_status = "CONNECTED" if a["status"] not in ("unknown", "") else "DISCONNECTED"
    field("Status:", f"{conn_status} | Last: {_ts_ago(a['last_update'])}")
    blank()

    # -- Autonomic Nerve ----------------------------------------------------
    au = state["autonomic"]
    section("AUTONOMIC NERVE")
    blank()

    ollama_str = "ONLINE" if au["ollama_online"] else "OFFLINE"
    # Extract model name from ai_method like "ai:llama3.2:latest"
    model_parts = au["ai_method"].split(":")
    model_name = ":".join(model_parts[1:]) if len(model_parts) > 1 else au["ai_method"]
    if model_name:
        ollama_str += f" ({model_name})"

    field("Ollama:", ollama_str)
    field("AI Method:", au["ai_method"])
    field("Heartbeat:", f"{au['heartbeat_interval']}s interval")
    field("Status:", au["status"])
    blank()

    # -- Self-Funding -------------------------------------------------------
    sf = state["self_funding"]
    section("SELF-FUNDING")
    blank()

    # Build cost string
    cost_str = _fmt_usd(sf["ai_cost"])
    if sf["ai_cost"] == 0:
        prov_labels = []
        for p in sf["providers"]:
            if "ollama" in p.lower():
                prov_labels.append("Ollama FREE")
            elif "groq" in p.lower():
                prov_labels.append("Groq FREE")
            else:
                prov_labels.append(p)
        if prov_labels:
            cost_str += " (" + " + ".join(prov_labels) + ")"
        else:
            cost_str += " (local models)"

    field("Trading Profit:", _fmt_usd(sf["trading_profit"]))
    field("AI Token Cost:", cost_str)
    field("Net Profit:", _fmt_usd(sf["net_profit"]))
    field("Self-Sustaining:", "YES" if sf["self_sustaining"] else "NO")
    blank()

    # -- Portfolio Total ----------------------------------------------------
    p = state["portfolio"]
    section("PORTFOLIO TOTAL")
    blank()

    field("Kalshi:", _fmt_usd(p["kalshi_total"]))
    field("Alpaca:", _fmt_usd(p["alpaca_total"]))
    field("SOL:", f"{p['sol_amount']:.4f} (~{_fmt_usd(p['sol_usd'])})")
    field("TOTAL:", f"~{_fmt_usd(p['total_usd'])}")
    blank()

    # -- Nerve Loop ---------------------------------------------------------
    nl = state["nerve_loop"]
    section("NERVE_LOOP")
    blank()

    field("Status:", nl["status"])
    field("Last Run:", nl["last_run"] if nl["last_run"] else "never")
    field("Phases:", f"{nl['phases_complete']}/{nl['phases_total']} complete")
    field("Engines:", str(eng))

    if nl["phases_total"] > 0:
        phase_pct = nl["phases_complete"] / nl["phases_total"] * 100
        field("Progress:", _bar(phase_pct))

    if nl["elapsed_seconds"]:
        field("Cycle Time:", f"{nl['elapsed_seconds']:.1f}s")
    blank()

    # -- Aid routing --------------------------------------------------------
    aid = state.get("aid", {})
    if aid.get("total_to_gaza", 0) > 0:
        section("MUTUAL AID")
        blank()
        field("Gaza Aid:", _fmt_usd(aid["total_to_gaza"]))
        blank()

    # -- Footer -------------------------------------------------------------
    sep("=")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    heading(f"Snapshot: {now_str}")
    heading("Ethics: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)")
    sep("=")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Save snapshot
# ---------------------------------------------------------------------------

def _save_snapshot(state):
    """Save pulse state to data/pulse_state.json."""
    try:
        out_path = DATA / "pulse_state.json"
        out_path.write_text(
            json.dumps(state, indent=2, default=str),
            encoding="utf-8"
        )
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run():
    """
    Run the SolarPunk PULSE dashboard.

    1. Reads all state files across the nervous system.
    2. Calculates aggregate metrics (portfolio, win rates, self-funding).
    3. Prints a full ASCII dashboard to the terminal.
    4. Saves a snapshot to data/pulse_state.json.
    5. Returns the state dict for programmatic use.
    """
    state = _collect()
    dashboard = _render(state)
    print(dashboard)
    _save_snapshot(state)

    # Broadcast to synaptic bus -- every engine sees this INSTANTLY
    try:
        from SYNAPTIC_BUS import emit_batch
        portfolio = state.get("portfolio", {})

        # Read nervous system health for dashboard enrichment
        try:
            _h = json.loads((DATA / "homeostasis_state.json").read_text(encoding="utf-8"))
        except Exception:
            _h = {}
        try:
            _c = json.loads((DATA / "neural_cortex_state.json").read_text(encoding="utf-8"))
        except Exception:
            _c = {}

        emit_batch("PULSE", {
            "total_usd": portfolio.get("total_usd", 0),
            "kalshi_total": portfolio.get("kalshi_total", 0),
            "alpaca_total": portfolio.get("alpaca_total", 0),
            "sol_usd": portfolio.get("sol_usd", 0),
            "engine_count": state.get("engine_count", 0),
            "self_sustaining": state.get("self_funding", {}).get("self_sustaining", False),
            "status": "active",
            "equilibrium": _h.get("equilibrium", 0),
            "homeostasis_trend": _h.get("trend", "unknown"),
            "brain_confidence": _c.get("decision_confidence", 0),
            "brain_risk_posture": _c.get("strategy", {}).get("risk_posture", "moderate"),
        }, silent=True)
    except Exception:
        pass  # Bus not available -- degrade gracefully

    return state


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run()
