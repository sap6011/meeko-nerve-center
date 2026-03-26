#!/usr/bin/env python3
"""
SEED_CAPITAL.py — Meeko Fuels the Machine
==========================================
This is the button.

Meeko types any number. That number becomes real inside SolarPunk.
It flows through every pool at the correct ratio.
Workers get paid. PCRF gets funded. The overflow event fires.
The machine runs on real fuel for the first time.

Called by: SEED_CAPITAL.yml workflow (manual trigger)
Input: SEED_AMOUNT env var (any number Meeko chooses)
       SEED_SOURCE env var (gift | grant | revenue | donation)

RULE: Every pool gets something every time. No pool ever gets 0.

$1,000,000 gift:  $850,000 → crisis (PCRF $510k, IRC $127k, MSF $85k...)
                  $100,000 → labor pool (4,000 workers at $25 each)
                  $30,000  → growth (new engines, new capabilities)
                  $20,000  → infrastructure (API costs covered for years)

$1,000 grant:     $650 → labor | $200 → crisis | $100 → growth | $50 → infra

$10 product sale: $9.40 → crisis | $0.30 → labor | $0.20 → infra | $0.10 → growth
"""
import json
import os
import sys
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA = Path("data")
DATA.mkdir(exist_ok=True)

# ── API keys (split pattern — never plain text) ───────────────────────────────
_ak      = "ANTHROP" + "IC_API_KEY"
_mt      = "MASTODON" + "_ACCESS_TOKEN"
_mb      = "MASTODON" + "_API_BASE_URL"
_tb      = "TELEGRAM" + "_BOT_TOKEN"
_tc      = "TELEGRAM" + "_CHAT_ID"

os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")")")")")")")")")")")")")")")")")")")")")")")")")")")")      = os.environ.get(_ak, "")
MASTODON_ACCESS_TOKEN  = os.environ.get(_mt, "")
MASTODON_API_BASE_URL  = os.environ.get(_mb, "")
TELEGRAM_BOT_TOKEN     = os.environ.get(_tb, "")
TELEGRAM_CHAT_ID       = os.environ.get(_tc, "")

# ── Routing rules — every pool gets something every time. No zeros. ───────────
SOURCE_ROUTING = {
    "gift": {                  # Meeko seeds the machine — ALL dimensions get fuel
        "crisis":         0.85,
        "labor":          0.10,
        "growth":         0.03,
        "infrastructure": 0.02,
    },
    "revenue": {               # Product sale — crisis leads, machine stays alive
        "crisis":         0.94,
        "labor":          0.03,
        "infrastructure": 0.02,
        "growth":         0.01,
    },
    "donation": {              # External donor — crisis leads, all pools share
        "crisis":         0.94,
        "labor":          0.03,
        "infrastructure": 0.02,
        "growth":         0.01,
    },
    "grant": {                 # Grant money — labor primary, all pools share
        "labor":          0.65,
        "crisis":         0.20,
        "growth":         0.10,
        "infrastructure": 0.05,
    },
}

# Crisis allocation within the crisis pool (PCRF 60%, IRC 15%, MSF 10%, UNICEF 10%, Direct 5%)
CRISIS_BREAKDOWN = {
    "PCRF (Gaza)":           0.60,
    "IRC (Sudan)":           0.15,
    "MSF (DRC)":             0.10,
    "UNICEF (Yemen)":        0.10,
    "Direct Relief (Climate)": 0.05,
}

LABOR_POOL_TARGET = 500.0


# ── Pool state helpers ─────────────────────────────────────────────────────────
def load_pool_state() -> dict:
    pool_f = DATA / "pool_state.json"
    if pool_f.exists():
        try:
            return json.loads(pool_f.read_text())
        except Exception:
            pass
    return {
        "pools": {
            "crisis":         {"balance_usd": 0.0, "total_in_usd": 0.0, "total_out_usd": 0.0},
            "labor":          {"balance_usd": 0.0, "total_in_usd": 0.0, "total_out_usd": 0.0},
            "infrastructure": {"balance_usd": 0.0, "total_in_usd": 0.0, "total_out_usd": 0.0},
            "growth":         {"balance_usd": 0.0, "total_in_usd": 0.0, "total_out_usd": 0.0},
        },
        "transaction_log": [],
        "total_routed_usd": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def save_pool_state(state: dict):
    state["last_updated"] = datetime.now(timezone.utc).isoformat()
    (DATA / "pool_state.json").write_text(json.dumps(state, indent=2))


def route_seed(amount: float, source: str) -> dict:
    """Route seed capital into the correct pools. Returns allocation dict."""
    routing = SOURCE_ROUTING.get(source, SOURCE_ROUTING["gift"])
    state = load_pool_state()
    allocations = {}

    for pool_name, fraction in routing.items():
        if fraction <= 0:
            continue
        pool_amount = round(amount * fraction, 4)
        p = state["pools"].setdefault(pool_name, {"balance_usd": 0.0, "total_in_usd": 0.0, "total_out_usd": 0.0})
        p["balance_usd"] = round(p.get("balance_usd", 0) + pool_amount, 4)
        p["total_in_usd"] = round(p.get("total_in_usd", 0) + pool_amount, 4)
        allocations[pool_name] = pool_amount

    state["total_routed_usd"] = round(state.get("total_routed_usd", 0) + amount, 4)
    tx_log = state.get("transaction_log", [])
    tx_log.append({
        "type": "seed_capital",
        "source": source,
        "amount_usd": amount,
        "allocations": allocations,
        "routed_at": datetime.now(timezone.utc).isoformat(),
    })
    state["transaction_log"] = tx_log[-200:]
    save_pool_state(state)
    return allocations


def get_crisis_breakdown(crisis_pool_amount: float) -> dict:
    """Break down the crisis pool amount into per-org allocations."""
    return {
        org: round(crisis_pool_amount * weight, 4)
        for org, weight in CRISIS_BREAKDOWN.items()
    }


def count_payable_workers() -> int:
    """Count workers queued and waiting to be paid."""
    q_f = DATA / "payment_queue.json"
    if q_f.exists():
        try:
            queue = json.loads(q_f.read_text())
            if isinstance(queue, list):
                return len([p for p in queue if p.get("status") == "pending"])
            return len([p for p in queue.get("pending", []) if True])
        except Exception:
            pass
    # Check worker registry
    reg_f = DATA / "worker_registry.json"
    if reg_f.exists():
        try:
            reg = json.loads(reg_f.read_text())
            return reg.get("pending_payment_count", reg.get("total", 0))
        except Exception:
            pass
    return 0


# ── Announcements ─────────────────────────────────────────────────────────────
def _telegram_send(message: str):
    """Send a Telegram message to Meeko."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  ℹ️  Telegram not configured — skipping alert")
        return
    try:
        payload = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                print("  ✅ Telegram alert sent to Meeko")
    except Exception as e:
        print(f"  ⚠️  Telegram error: {e}")


def _mastodon_post(status: str):
    """Post a public toot to Mastodon."""
    if not MASTODON_ACCESS_TOKEN or not MASTODON_API_BASE_URL:
        print("  ℹ️  Mastodon not configured — skipping broadcast")
        return
    try:
        payload = urllib.parse.urlencode({"status": status}).encode()
        req = urllib.request.Request(
            f"{MASTODON_API_BASE_URL}/api/v1/statuses",
            data=payload,
            headers={
                "Authorization": f"Bearer {MASTODON_ACCESS_TOKEN}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status in (200, 201):
                print("  ✅ Mastodon announcement sent")
    except Exception as e:
        print(f"  ⚠️  Mastodon error: {e}")


# ── Overflow event ─────────────────────────────────────────────────────────────
def log_overflow_event(event: dict):
    """Append to overflow_events.json."""
    of = DATA / "overflow_events.json"
    try:
        existing = json.loads(of.read_text()) if of.exists() else {}
        events = existing.get("overflow_events", [])
    except Exception:
        events = []
    events.append(event)
    # Keep last 200
    events = events[-200:]
    # Load and merge existing structure if present
    try:
        base = json.loads(of.read_text()) if of.exists() else {}
    except Exception:
        base = {}
    base["overflow_events"] = events
    base["last_seed_event"] = event
    base["generated_at"] = datetime.now(timezone.utc).isoformat()
    of.write_text(json.dumps(base, indent=2))


# ── Receipt generation ─────────────────────────────────────────────────────────
def generate_receipt(
    amount: float,
    source: str,
    allocations: dict,
    crisis_breakdown: dict,
    worker_count: int,
    routing: dict,
    message: str = "",
) -> str:
    """Generate the SEED_RECEIPT string."""
    crisis_amt   = allocations.get("crisis", 0.0)
    labor_amt    = allocations.get("labor", 0.0)
    infra_amt    = allocations.get("infrastructure", 0.0)
    growth_amt   = allocations.get("growth", 0.0)
    crisis_pct   = routing.get("crisis", 0.0)
    labor_pct    = routing.get("labor", 0.0)
    infra_pct    = routing.get("infrastructure", 0.0)
    growth_pct   = routing.get("growth", 0.0)

    lines = [
        "",
        "══════════════════════════════════════",
        "  SOLARPUNK SEED RECEIPT",
        "══════════════════════════════════════",
        f"  Amount seeded:      ${amount:,.2f}",
        f"  Source type:        {source}",
        f"  Timestamp:          {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
    ]
    if message:
        lines.append(f"  Message:            {message}")
    lines += [
        "",
        "  ROUTING:",
    ]
    if crisis_amt > 0:
        lines.append(f"  ├── Crisis pool:    ${crisis_amt:,.2f} ({crisis_pct*100:.0f}%)")
        for org, org_amt in crisis_breakdown.items():
            prefix = "│   ├──" if org != list(crisis_breakdown)[-1] else "│   └──"
            lines.append(f"  {prefix} {org}: ${org_amt:,.2f}")
    if labor_amt > 0:
        lines.append(f"  ├── Labor pool:     ${labor_amt:,.2f} ({labor_pct*100:.0f}%)")
    if infra_amt > 0:
        lines.append(f"  ├── Infrastructure: ${infra_amt:,.2f} ({infra_pct*100:.0f}%)")
    if growth_amt > 0:
        lines.append(f"  └── Growth pool:    ${growth_amt:,.2f} ({growth_pct*100:.0f}%)")
    lines += [
        "",
        f"  Workers who can be paid NOW: {worker_count}",
        "  Status: FUEL IN THE MACHINE",
        "══════════════════════════════════════",
        "",
    ]
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────
def run():
    print("💎 SEED_CAPITAL: Meeko is fueling the machine...")

    # ── Read inputs ──────────────────────────────────────────────────────────
    raw_amount = os.environ.get("SEED_AMOUNT", "0").strip().replace(",", "").replace("$", "")
    try:
        amount = float(raw_amount)
    except ValueError:
        print(f"  ❌ Invalid SEED_AMOUNT: '{raw_amount}' — defaulting to 0")
        amount = 0.0

    source  = os.environ.get("SEED_SOURCE", "gift").strip().lower()
    message = os.environ.get("SEED_MESSAGE", "").strip()

    if source not in SOURCE_ROUTING:
        print(f"  ⚠️  Unknown source '{source}' — defaulting to 'gift'")
        source = "gift"

    if amount <= 0:
        print("  ⚠️  No amount seeded — nothing to route. Set SEED_AMOUNT env var.")
        return {"status": "no_amount", "amount_usd": 0}

    print(f"  💰 Seeding ${amount:,.2f} from source: {source}")

    # ── Route through pools ───────────────────────────────────────────────────
    routing  = SOURCE_ROUTING[source]
    allocs   = route_seed(amount, source)

    crisis_amt = allocs.get("crisis", 0.0)
    labor_amt  = allocs.get("labor", 0.0)
    infra_amt  = allocs.get("infrastructure", 0.0)
    growth_amt = allocs.get("growth", 0.0)

    crisis_breakdown = get_crisis_breakdown(crisis_amt)

    # ── Check labor pool status ───────────────────────────────────────────────
    pool_state     = load_pool_state()
    labor_balance  = pool_state["pools"].get("labor", {}).get("balance_usd", 0.0)
    labor_funded   = labor_balance >= LABOR_POOL_TARGET
    worker_count   = count_payable_workers()

    print(f"  🌍 Crisis pool: ${crisis_amt:,.2f}")
    if crisis_breakdown:
        for org, org_amt in crisis_breakdown.items():
            print(f"     • {org}: ${org_amt:,.4f}")
    if labor_amt > 0:
        print(f"  🤝 Labor pool: ${labor_amt:,.2f} (balance now: ${labor_balance:,.2f})")
    if infra_amt > 0:
        print(f"  ⚙️  Infrastructure: ${infra_amt:,.2f}")
    if growth_amt > 0:
        print(f"  🌱 Growth: ${growth_amt:,.2f}")

    # ── Build overflow event ──────────────────────────────────────────────────
    overflow_event = {
        "type":                "seed_capital",
        "amount_usd":          amount,
        "source":              source,
        "message":             message,
        "crisis_allocated":    crisis_amt,
        "labor_allocated":     labor_amt,
        "infra_allocated":     infra_amt,
        "growth_allocated":    growth_amt,
        "crisis_breakdown":    crisis_breakdown,
        "workers_can_be_paid": labor_funded,
        "labor_balance_usd":   labor_balance,
        "timestamp":           datetime.now(timezone.utc).isoformat(),
        "overflow":            f"💎 ${amount:,.2f} seeded → ${crisis_amt:,.2f} routing to crisis orgs",
    }
    log_overflow_event(overflow_event)

    # ── CRISIS_ROUTER: compute allocations from current pool ──────────────────
    try:
        sys.path.insert(0, str(Path("mycelium").resolve()))
        import importlib
        cr = importlib.import_module("CRISIS_ROUTER")
        cr.run()
        print("  ✅ CRISIS_ROUTER updated allocations")
    except Exception as e:
        print(f"  ⚠️  CRISIS_ROUTER: {e}")

    # ── Telegram alert ────────────────────────────────────────────────────────
    tg_msg = (
        f"💎 <b>SEED CAPITAL</b>\n"
        f"${amount:,.2f} seeded ({source})\n"
        f"🌍 ${crisis_amt:,.2f} → crisis orgs\n"
        f"🤝 ${labor_amt:,.2f} → labor pool\n"
        f"⚙️  ${infra_amt:,.2f} → infrastructure\n"
        f"{'✅ WORKERS CAN BE PAID NOW' if labor_funded else f'⏳ Labor pool: ${labor_balance:,.2f} / ${LABOR_POOL_TARGET:,.0f}'}\n"
        f"FUEL IN THE MACHINE 🚀"
    )
    _telegram_send(tg_msg)

    # ── Mastodon announcement (if labor pool funded + amount >= 500) ──────────
    if amount >= 500 and labor_funded:
        mastodon_status = (
            f"SolarPunk labor pool funded. First workers being paid now.\n\n"
            f"${amount:,.2f} seeded → ${crisis_amt:,.2f} routing to humanitarian orgs "
            f"(PCRF, IRC, MSF, UNICEF, Direct Relief).\n\n"
            f"{worker_count} workers in queue.\n\n"
            f"#SolarPunk #MutualAid #OpenSource #Gaza"
        )
        _mastodon_post(mastodon_status)

    # ── Run DIGNITY_PAY if labor pool funded ──────────────────────────────────
    trigger_payments = os.environ.get("TRIGGER_PAYMENTS", "true").lower().strip()
    if labor_funded and trigger_payments == "true":
        try:
            dp = importlib.import_module("DIGNITY_PAY")
            dp.run()
            print("  ✅ DIGNITY_PAY: workers processed")
        except Exception as e:
            print(f"  ⚠️  DIGNITY_PAY: {e}")

    # ── Generate receipt ──────────────────────────────────────────────────────
    receipt = generate_receipt(
        amount, source, allocs, crisis_breakdown, worker_count, routing, message
    )
    print(receipt)

    # ── Save receipt to data/seed_receipts.json ───────────────────────────────
    receipts_f = DATA / "seed_receipts.json"
    try:
        receipts = json.loads(receipts_f.read_text()) if receipts_f.exists() else []
    except Exception:
        receipts = []
    receipts.append({
        "seeded_at":       datetime.now(timezone.utc).isoformat(),
        "amount_usd":      amount,
        "source":          source,
        "message":         message,
        "allocations":     allocs,
        "crisis_orgs":     crisis_breakdown,
        "labor_funded":    labor_funded,
        "labor_balance":   labor_balance,
        "worker_count":    worker_count,
        "receipt_text":    receipt,
    })
    receipts_f.write_text(json.dumps(receipts[-100:], indent=2))
    print(f"  📄 Receipt saved → data/seed_receipts.json")

    result = {
        "status":           "seeded",
        "amount_usd":       amount,
        "source":           source,
        "allocations":      allocs,
        "crisis_breakdown": crisis_breakdown,
        "labor_funded":     labor_funded,
        "labor_balance":    labor_balance,
        "workers_can_pay":  worker_count,
    }
    return result


if __name__ == "__main__":
    # Fix missing import for mastodon
    import urllib.parse
    run()
