import json
import os
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

ANALYTICS_FILE = os.path.join("analytics", "revenue_data.json")


def _load_analytics() -> Dict[str, Any]:
    """Load revenue analytics if available."""
    if not os.path.exists(ANALYTICS_FILE):
        return {}

    try:
        with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def estimate_revenue(cycle_index: int) -> float:
    """Estimate AI-generated revenue available for humanitarian aid.

    Priority:
    1. Use recent 30-day revenue from analytics if available.
    2. Otherwise fall back to a simple exponential growth model.
    """
    data = _load_analytics()
    daily = data.get("daily_revenue") or []
    if daily:
        # Use the most recent 30 days if we have them
        last_30 = daily[-30:] if len(daily) > 30 else daily
        avg_daily = sum(d.get("total", 0.0) for d in last_30) / max(
            1, len(last_30)
        )
        # Assume a small growth factor per humanitarian cycle
        growth_factor = 1.08 ** max(0, cycle_index)
        return round(avg_daily * 30 * growth_factor, 2)

    # Fallback: synthetic model similar to original humanitarian_orchestrator
    base = 1000.0
    growth = 1.20 ** max(0, cycle_index)
    return round(base * growth, 2)


def run():
    """Main entry point with data I/O wiring."""
    revenue_data = json.loads((DATA / "revenue_data.json").read_text()) if (DATA / "revenue_data.json").exists() else {}
    results = {}
    for i in range(3):
        est = estimate_revenue(i)
        results[f"cycle_{i+1}"] = est
        print(f"Cycle {i+1}: estimated revenue = ${est:,.2f}")
    (DATA / "legacy_sifted_humanitarian_revenue_state.json").write_text(json.dumps({"last_run": datetime.now().isoformat(), "status": "ok", "estimates": results}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    run()

