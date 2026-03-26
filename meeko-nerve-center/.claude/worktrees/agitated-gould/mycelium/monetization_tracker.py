#!/usr/bin/env python3
"""
monetization_tracker.py — Revenue Signal Engine
================================================
First link in the missing connections chain (connections.json):
  monetization_tracker → signal_tracker → cross_poster → meeko_brain

Tracks every revenue stream by source, amount, and trend.
Calculates which products/platforms are generating money.
Feeds signal_tracker.py so it knows what content drives revenue.

Reads:  data/flywheel_state.json
        data/gumroad_listings.json
        data/etsy_seo_output.json
        data/brave_bridge_report.json  (Etsy pricing intel)
Writes: data/monetization_tracker.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")


def load_json(fname, default=None):
    fp = DATA / fname
    try:
        return json.loads(fp.read_text()) if fp.exists() else (default or {})
    except Exception:
        return default or {}


def analyze_streams(flywheel):
    """Break down revenue by stream with trend signals."""
    streams    = flywheel.get("streams", {})
    history    = flywheel.get("history", [])
    total_earn = flywheel.get("total_earned_meeko", 0) + flywheel.get("total_to_gaza", 0)
    balance    = flywheel.get("current_balance", 0)
    to_gaza    = flywheel.get("total_to_gaza", 0)
    total_sales= flywheel.get("total_sales", 0)

    # Calculate per-stream signals
    stream_signals = []
    for name, val in streams.items():
        amount = val if isinstance(val, (int, float)) else (val.get("amount", 0) if isinstance(val, dict) else 0)
        stream_signals.append({
            "stream": name,
            "amount": amount,
            "share_pct": round(amount / total_earn * 100, 1) if total_earn > 0 else 0,
            "status": "active" if amount > 0 else "dormant",
        })
    stream_signals.sort(key=lambda x: x["amount"], reverse=True)

    # Trend from history (last 5 cycles)
    recent = history[-5:] if history else []
    trend = "flat"
    if len(recent) >= 2:
        if recent[-1].get("amount", 0) > recent[-2].get("amount", 0):
            trend = "up"
        elif recent[-1].get("amount", 0) < recent[-2].get("amount", 0):
            trend = "down"

    return {
        "total_revenue": total_earn,
        "current_balance": balance,
        "total_to_gaza": to_gaza,
        "total_sales": total_sales,
        "streams": stream_signals,
        "active_streams": sum(1 for s in stream_signals if s["status"] == "active"),
        "revenue_trend": trend,
        "loop_efficiency": round(flywheel.get("auto_loop_sales", 0) / max(total_sales, 1) * 100, 1),
    }


def analyze_products(gumroad, etsy_output):
    """Check product listing health."""
    gumroad_listings = gumroad.get("listings", []) if isinstance(gumroad, dict) else []
    etsy_listings    = etsy_output.get("listings", []) if isinstance(etsy_output, dict) else []

    products = []
    for g in gumroad_listings:
        products.append({
            "platform": "gumroad",
            "name": g.get("name", g.get("title", "?")),
            "status": g.get("status", "unknown"),
            "price": g.get("price_cents", 0) / 100,
        })
    for e in etsy_listings[:3]:
        products.append({
            "platform": "etsy",
            "name": e.get("title", "?"),
            "status": "ready" if e.get("description") else "needs_description",
            "source": e.get("source", "template"),
        })

    return {
        "total_products": len(products),
        "gumroad_count": len(gumroad_listings),
        "etsy_count": len(etsy_listings),
        "products": products[:10],
        "listing_health": "good" if len(products) >= 5 else "needs_more_listings",
    }


def pricing_intel(brave):
    """Extract competitor pricing from BRAVE_BRIDGE web intel."""
    intel = brave.get("intelligence", {}) if isinstance(brave, dict) else {}
    etsy  = brave.get("etsy_pricing", {}) if isinstance(brave, dict) else {}
    price_range = etsy.get("price_range", {}) if isinstance(etsy, dict) else {}
    return {
        "competitor_avg_price": price_range.get("avg"),
        "competitor_min_price": price_range.get("min"),
        "competitor_max_price": price_range.get("max"),
        "our_price": 1.00,
        "price_positioning": "undercut" if (price_range.get("min") or 0) > 1.00 else "competitive",
        "web_priority": intel.get("priority_action", ""),
    }


def generate_signals(revenue_analysis, product_analysis, pricing):
    """Generate actionable signals for signal_tracker."""
    signals = []
    if revenue_analysis["total_revenue"] == 0:
        signals.append({"signal": "zero_revenue", "urgency": "critical",
                        "action": "First sale needed — share shop URL manually"})
    if revenue_analysis["active_streams"] == 0:
        signals.append({"signal": "no_active_streams", "urgency": "high",
                        "action": "Enable payment processing in docs/index.html"})
    if product_analysis["listing_health"] == "needs_more_listings":
        signals.append({"signal": "thin_catalog", "urgency": "medium",
                        "action": "Add more Gumroad products — data/gumroad_listings.json has templates"})
    if pricing["price_positioning"] == "undercut":
        signals.append({"signal": "price_advantage", "urgency": "info",
                        "action": f"Our $1 undercuts competitor avg ${pricing['competitor_avg_price']} — lead with price in copy"})
    if revenue_analysis["revenue_trend"] == "up":
        signals.append({"signal": "revenue_rising", "urgency": "info",
                        "action": "Revenue trending up — increase posting frequency"})
    return signals


def main():
    DATA.mkdir(exist_ok=True)
    print("monetization_tracker — Revenue Signal Engine...")
    ts = datetime.now(timezone.utc).isoformat()

    flywheel    = load_json("flywheel_state.json")
    gumroad     = load_json("gumroad_listings.json")
    etsy_output = load_json("etsy_seo_output.json")
    brave       = load_json("brave_bridge_report.json")

    revenue_analysis = analyze_streams(flywheel)
    product_analysis = analyze_products(gumroad, etsy_output)
    pricing          = pricing_intel(brave)
    signals          = generate_signals(revenue_analysis, product_analysis, pricing)

    report = {
        "timestamp": ts,
        "revenue": revenue_analysis,
        "products": product_analysis,
        "pricing": pricing,
        "signals": signals,
        "signal_count": len(signals),
        "critical_signals": [s for s in signals if s["urgency"] == "critical"],
        "feeds_into": "signal_tracker.py",
    }
    (DATA / "monetization_tracker.json").write_text(json.dumps(report, indent=2))

    print(f"  Revenue: ${revenue_analysis['total_revenue']:.2f} | "
          f"Streams: {revenue_analysis['active_streams']} active | "
          f"Products: {product_analysis['total_products']}")
    print(f"  Signals: {len(signals)} ({len(report['critical_signals'])} critical)")
    for s in signals[:3]:
        icon = {"critical": "🔴", "high": "🟡", "medium": "🔵", "info": "⚪"}.get(s["urgency"], "•")
        print(f"  {icon} [{s['urgency']}] {s['action']}")


if __name__ == "__main__":
    main()
