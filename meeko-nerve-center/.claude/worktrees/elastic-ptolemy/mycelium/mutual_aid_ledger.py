#!/usr/bin/env python3
"""
mutual_aid_ledger.py — Ward 8 Neighborhood Resource Ledger
===========================================================
Tracks neighborly reciprocity with no money, no tokens, no bank.
Just a record of who gave what, who received what, and the running
balance of community abundance.

Categories:
  tools        — borrowed/lent physical tools
  labor        — volunteer hours offered/completed
  energy       — solar surplus kWh contributed to mesh
  materials    — plastic, wood, compost, seeds, etc.
  skills       — offered expertise (plumbing, coding, welding, etc.)
  space        — yard, garage, kitchen access offered

Anyone can add a contribution. The ledger is public and tamper-evident
(append-only with timestamps). No central authority. No tokens.
The "wealth" is the visible record of who shows up.

Reads:  data/mutual_aid_ledger.json   (running ledger)
Writes: data/mutual_aid_ledger.json   (updated with any new contributions)
        data/mutual_aid_summary.json  (OMNIBRAIN/dashboard reads this)
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA        = Path("data")
LEDGER_FILE = DATA / "mutual_aid_ledger.json"
SUMMARY_FILE= DATA / "mutual_aid_summary.json"

VALID_CATEGORIES = {"tools", "labor", "energy", "materials", "skills", "space", "food", "knowledge"}
VALID_DIRECTIONS = {"offer", "receive", "complete"}


def load_ledger():
    if LEDGER_FILE.exists():
        try:
            return json.loads(LEDGER_FILE.read_text())
        except Exception:
            pass
    return {
        "created": datetime.now(timezone.utc).isoformat(),
        "community": "Ward 8, Cuyahoga Falls",
        "entries": [],
        "members": {},
        "total_contributions": 0,
    }


def record_contribution(ledger, entry):
    """
    Add a contribution to the ledger.
    entry = {
        "member": "name or alias",
        "category": "tools|labor|energy|materials|skills|space|food|knowledge",
        "direction": "offer|receive|complete",
        "description": "what was given/received",
        "quantity": 1,
        "unit": "hours|kg|kWh|item|sq_ft|etc",
        "note": "optional context",
        "for_whom": "recipient name or 'community'"
    }
    """
    ts  = datetime.now(timezone.utc).isoformat()
    cat = entry.get("category", "").lower()
    if cat not in VALID_CATEGORIES:
        return False, f"Unknown category '{cat}'. Valid: {VALID_CATEGORIES}"

    record = {
        "id":          len(ledger["entries"]) + 1,
        "timestamp":   ts,
        "member":      entry.get("member", "anonymous"),
        "category":    cat,
        "direction":   entry.get("direction", "offer"),
        "description": entry.get("description", ""),
        "quantity":    entry.get("quantity", 1),
        "unit":        entry.get("unit", "unit"),
        "note":        entry.get("note", ""),
        "for_whom":    entry.get("for_whom", "community"),
    }
    ledger["entries"].append(record)
    ledger["total_contributions"] += 1

    # Track per-member stats
    member = record["member"]
    if member not in ledger["members"]:
        ledger["members"][member] = {
            "first_seen": ts, "total_gives": 0, "total_receives": 0,
            "categories": {}, "reputation_score": 0
        }
    m = ledger["members"][member]
    if record["direction"] == "offer":
        m["total_gives"] += 1
    elif record["direction"] == "receive":
        m["total_receives"] += 1
    m["categories"][cat] = m["categories"].get(cat, 0) + 1
    # Simple reputation: contributions - (0.5 × receipts), floor 0
    m["reputation_score"] = round(
        max(0, m["total_gives"] - 0.5 * m["total_receives"]), 1
    )
    return True, record


def compute_summary(ledger):
    entries  = ledger.get("entries", [])
    members  = ledger.get("members", {})
    now      = datetime.now(timezone.utc)

    # Category breakdown
    by_cat = {}
    for e in entries:
        cat = e.get("category", "unknown")
        if cat not in by_cat:
            by_cat[cat] = {"offers": 0, "receives": 0, "completes": 0}
        d = e.get("direction", "offer")
        if d in by_cat[cat]:
            by_cat[cat][d] += 1

    # Energy surplus (kWh contributed)
    energy_kwh = sum(
        e.get("quantity", 0) for e in entries
        if e.get("category") == "energy" and e.get("direction") == "offer"
        and e.get("unit", "").lower() in ("kwh", "kw", "kilowatt-hour")
    )

    # Labor hours
    labor_hours = sum(
        e.get("quantity", 0) for e in entries
        if e.get("category") == "labor" and e.get("direction") in ("offer", "complete")
        and e.get("unit", "").lower() in ("hours", "hour", "hrs", "hr")
    )

    # Top contributors (by reputation score)
    top = sorted(members.items(), key=lambda x: x[1].get("reputation_score", 0), reverse=True)[:5]

    # Recent entries (last 7 days)
    recent = []
    for e in entries[-20:]:
        try:
            ts = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
            if (now - ts).days <= 7:
                recent.append(e)
        except Exception:
            pass

    # Abundance score 0-100 (more contributions + diversity = higher score)
    active_cats   = len([c for c, v in by_cat.items() if v["offers"] > 0])
    active_members = len([m for m, v in members.items() if v["total_gives"] > 0])
    total_gives   = sum(v["total_gives"] for v in members.values())
    abundance_score = min(100, (active_cats * 10) + (active_members * 5) + min(total_gives, 30))

    return {
        "timestamp": now.isoformat(),
        "community": ledger.get("community", ""),
        "total_entries": len(entries),
        "total_members": len(members),
        "active_givers": active_members,
        "abundance_score": abundance_score,
        "by_category": by_cat,
        "energy_surplus_kwh": round(energy_kwh, 2),
        "labor_hours_contributed": round(labor_hours, 1),
        "top_contributors": [{"member": k, "score": v["reputation_score"], "gives": v["total_gives"]}
                             for k, v in top],
        "recent_7d": len(recent),
        "open_offers": [e for e in entries if e.get("direction") == "offer"][-10:],
        "shareable_one_liner": (
            f"Ward 8 Mutual Aid: {active_members} neighbors active | "
            f"{labor_hours:.0f} hours shared | {energy_kwh:.1f} kWh surplus | "
            f"Abundance score {abundance_score}/100"
        ),
    }


def seed_example_entries(ledger):
    """Seed with example entries so the ledger isn't empty on first run."""
    if ledger.get("entries"):
        return  # already has data

    examples = [
        {"member": "Ward8Neighbor_A", "category": "tools", "direction": "offer",
         "description": "Cordless drill + bits available for borrowing",
         "quantity": 1, "unit": "item", "for_whom": "community",
         "note": "Text to arrange pickup. Returns within 48 hours please."},
        {"member": "Ward8Neighbor_B", "category": "skills", "direction": "offer",
         "description": "Electrician — can help with solar panel wiring",
         "quantity": 4, "unit": "hours", "for_whom": "community",
         "note": "Weekends only. Free for Sovereign Cell project."},
        {"member": "Ward8Neighbor_C", "category": "space", "direction": "offer",
         "description": "Backyard available for community build days",
         "quantity": 400, "unit": "sq_ft", "for_whom": "community",
         "note": "Merriman Valley area. Has outdoor power outlet."},
        {"member": "Ward8Neighbor_D", "category": "materials", "direction": "offer",
         "description": "HDPE plastic waste (milk jugs, containers) for Precious Plastic",
         "quantity": 15, "unit": "kg", "for_whom": "Alchemist",
         "note": "Sorted and cleaned. Ready to shred."},
        {"member": "SolarPunk_AI", "category": "knowledge", "direction": "offer",
         "description": "Automated grant narrative generation, compliance monitoring, social posting",
         "quantity": 2, "unit": "hours/day", "for_whom": "community",
         "note": "OMNIBRAIN runs twice daily. All outputs open source."},
    ]
    for e in examples:
        record_contribution(ledger, e)
    print("  Seeded with 5 example entries to show neighbors what's possible")


def main():
    DATA.mkdir(exist_ok=True)
    print("mutual_aid_ledger — Ward 8 Neighborhood Resource Ledger...")

    ledger = load_ledger()
    seed_example_entries(ledger)

    summary = compute_summary(ledger)

    LEDGER_FILE.write_text(json.dumps(ledger, indent=2))
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2))

    print(f"\n  Members: {summary['total_members']} | Entries: {summary['total_entries']}")
    print(f"  Abundance Score: {summary['abundance_score']}/100")
    print(f"  Labor hours: {summary['labor_hours_contributed']} | Energy surplus: {summary['energy_surplus_kwh']} kWh")
    print(f"  Open offers: {len(summary['open_offers'])}")
    print(f"\n  {summary['shareable_one_liner']}")

    if summary["open_offers"]:
        print("\n  Current open offers:")
        for o in summary["open_offers"][:3]:
            print(f"    [{o['category']}] {o['description'][:60]} — {o['member']}")


if __name__ == "__main__":
    main()
