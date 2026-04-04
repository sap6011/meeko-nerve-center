"""
MUTUAL_AID_AUDITOR.py
=====================
The Supreme Mutant — assembled from:
  - Dexter gene: self-correction loop (critique → regenerate until correct)
  - n8n gene: DAG pipeline execution (trigger → transform → action)
  - DistributeAid gene: resource routing with delivery tracking

This agent monitors ALL revenue flows through SolarPunk, enforces the
20% local aid rule (hard-coded, NOT optional policy), self-corrects
routing errors, and logs everything to the transparency ledger.

It never stops. It never sleeps (daemon mode).
It serves the community, not shareholders.
"""

import json
import time
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

# ── Paths ─────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent.parent
LEDGER_PATH   = ROOT / "vault" / "treasury_ledger.json"
ACTUAL_LOG    = ROOT / "SOLARPUNK_ACTUAL.md"
DATA_PATH     = ROOT / "data"
AID_LOG       = DATA_PATH / "mutual_aid_routing.json"

# ── Constants (hard-coded, not configurable — this is the mission) ─────────
LOCAL_AID_PERCENT    = 0.20   # 20% to local mutual aid — ALWAYS
SELF_FUND_PERCENT    = 0.80   # 80% back into SolarPunk
MAX_CRITIQUE_PASSES  = 3      # Self-correction attempts before alerting human
AUDIT_INTERVAL_SECS  = 300    # Run audit every 5 minutes

logging.basicConfig(
    level=logging.INFO,
    format="[AUDITOR] %(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("mutual_aid_auditor")


# ────────────────────────────────────────────────────────────────────────────
# GENE 1: DEXTER — Self-Correction Loop
# ────────────────────────────────────────────────────────────────────────────

def self_correct(
    action_fn: Callable,
    critique_fn: Callable,
    context: dict,
    max_passes: int = MAX_CRITIQUE_PASSES
) -> dict:
    """
    Dexter gene: Run action → critique result → re-run if needed.
    Returns: {"result": ..., "passes": int, "confident": bool}
    """
    passes = 0
    result = None

    while passes < max_passes:
        result  = action_fn(context)
        verdict = critique_fn(result, context)
        passes += 1

        if verdict["confident"]:
            log.info(f"Self-correction: confident after {passes} pass(es)")
            return {"result": result, "passes": passes, "confident": True}

        log.warning(f"Self-correction pass {passes}: {verdict['reason']} -- retrying...")
        context["previous_attempt"] = result
        context["critique"]         = verdict["reason"]

    # Exhausted passes — flag for human review but don't block
    log.error(f"Self-correction exhausted {max_passes} passes. Flagging for human anchor.")
    _alert_human("SELF_CORRECTION_EXHAUSTED", context)
    return {"result": result, "passes": passes, "confident": False}


def _alert_human(event_type: str, context: dict):
    """Write an alert to SOLARPUNK_ACTUAL.md for the human anchor."""
    if not ACTUAL_LOG.exists():
        return
    ts    = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"\n**[AUDITOR ALERT — {ts}]** {event_type}: {json.dumps(context, default=str)[:200]}\n"
    with open(ACTUAL_LOG, "a") as f:
        f.write(entry)


# ────────────────────────────────────────────────────────────────────────────
# GENE 2: n8n — DAG Pipeline Execution
# ────────────────────────────────────────────────────────────────────────────

class Pipeline:
    """
    n8n gene: A simple directed pipeline where each step transforms data
    and passes it to the next. Trigger → [Step1 → Step2 → Step3] → Action.
    """

    def __init__(self, name: str):
        self.name  = name
        self.steps: list[tuple[str, Callable]] = []

    def add_step(self, name: str, fn: Callable) -> "Pipeline":
        self.steps.append((name, fn))
        return self

    def execute(self, trigger_data: dict) -> dict:
        data    = trigger_data.copy()
        results = []

        for step_name, fn in self.steps:
            try:
                data = fn(data)
                results.append({"step": step_name, "status": "ok"})
                log.info(f"Pipeline [{self.name}] step [{step_name}]: OK")
            except Exception as e:
                log.error(f"Pipeline [{self.name}] step [{step_name}] FAILED: {e}")
                results.append({"step": step_name, "status": "error", "error": str(e)})
                data["pipeline_error"] = str(e)
                break

        data["_pipeline_results"] = results
        return data


# ────────────────────────────────────────────────────────────────────────────
# GENE 3: DistributeAid — Resource Routing
# ────────────────────────────────────────────────────────────────────────────

def route_aid(amount: float, source: str, metadata: dict = None) -> dict:
    """
    DistributeAid gene: Given an amount, split and route it.
    20% local mutual aid (HARD CODED — not negotiable).
    80% back into SolarPunk infrastructure.

    Returns a routing receipt logged to the ledger.
    """
    local_share = round(amount * LOCAL_AID_PERCENT, 2)
    solar_share = round(amount * SELF_FUND_PERCENT, 2)

    receipt = {
        "timestamp":     datetime.utcnow().isoformat(),
        "source":        source,
        "total":         amount,
        "local_aid":     local_share,
        "solarpunk":     solar_share,
        "rule":          f"{int(LOCAL_AID_PERCENT*100)}% local / {int(SELF_FUND_PERCENT*100)}% SolarPunk",
        "metadata":      metadata or {},
        "status":        "routed",
    }

    _append_ledger(receipt)
    log.info(f"Routed ${amount:.2f}: ${local_share:.2f} -> local aid | ${solar_share:.2f} -> SolarPunk")
    return receipt


def _append_ledger(entry: dict):
    """Append to treasury ledger — the permanent public record."""
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    ledger = []
    if LEDGER_PATH.exists():
        try:
            ledger = json.loads(LEDGER_PATH.read_text())
        except Exception:
            ledger = []
    ledger.append(entry)
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2))


def get_aid_summary() -> dict:
    """Summarize all aid routed so far."""
    if not LEDGER_PATH.exists():
        return {"total_routed": 0, "local_aid_total": 0, "solarpunk_total": 0, "entries": 0}

    try:
        ledger = json.loads(LEDGER_PATH.read_text())
        return {
            "total_routed":     sum(e.get("total", 0)      for e in ledger),
            "local_aid_total":  sum(e.get("local_aid", 0)  for e in ledger),
            "solarpunk_total":  sum(e.get("solarpunk", 0)  for e in ledger),
            "entries":          len(ledger),
        }
    except Exception:
        return {"error": "ledger parse failed"}


# ────────────────────────────────────────────────────────────────────────────
# THE ASSEMBLED MUTANT — Audit Loop
# ────────────────────────────────────────────────────────────────────────────

def _audit_revenue_pipeline() -> Pipeline:
    """
    Build the revenue audit pipeline:
    Load transactions -> Validate routing -> Self-correct errors -> Log result
    """

    def load_transactions(ctx: dict) -> dict:
        """Load any pending/unaudited transactions from data/."""
        pending = []
        for f in DATA_PATH.glob("*revenue*.json"):
            try:
                data = json.loads(f.read_text())
                if isinstance(data, list):
                    pending.extend(data)
                elif isinstance(data, dict):
                    pending.append(data)
            except Exception:
                pass
        ctx["pending"] = pending
        ctx["count"]   = len(pending)
        return ctx

    def validate_routing(ctx: dict) -> dict:
        """Check each transaction has correct aid routing applied."""
        errors = []
        for tx in ctx.get("pending", []):
            amount = tx.get("amount", tx.get("total", 0))
            if amount <= 0:
                continue
            expected_local = round(amount * LOCAL_AID_PERCENT, 2)
            actual_local   = tx.get("local_aid", 0)
            if abs(actual_local - expected_local) > 0.01:
                errors.append({
                    "tx":       tx,
                    "expected": expected_local,
                    "actual":   actual_local,
                    "delta":    round(expected_local - actual_local, 2),
                })
        ctx["routing_errors"] = errors
        return ctx

    def apply_corrections(ctx: dict) -> dict:
        """Re-route any transactions with incorrect splits."""
        for err in ctx.get("routing_errors", []):
            tx     = err["tx"]
            amount = tx.get("amount", tx.get("total", 0))
            log.warning(f"Correcting routing for ${amount:.2f} transaction (delta: ${err['delta']:.2f})")
            route_aid(amount, source="audit_correction", metadata={"original_tx": tx})
        ctx["corrections_applied"] = len(ctx.get("routing_errors", []))
        return ctx

    def log_audit_result(ctx: dict) -> dict:
        """Write audit summary to SOLARPUNK_ACTUAL.md."""
        ts      = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        summary = get_aid_summary()
        entry   = (
            f"\n**[AUDITOR CYCLE — {ts}]** "
            f"Reviewed {ctx.get('count', 0)} transactions | "
            f"Corrections: {ctx.get('corrections_applied', 0)} | "
            f"Cumulative local aid: ${summary.get('local_aid_total', 0):.2f} | "
            f"Cumulative SolarPunk fund: ${summary.get('solarpunk_total', 0):.2f}\n"
        )
        if ACTUAL_LOG.exists():
            with open(ACTUAL_LOG, "a") as f:
                f.write(entry)
        return ctx

    return (Pipeline("revenue_audit")
            .add_step("load_transactions",  load_transactions)
            .add_step("validate_routing",   validate_routing)
            .add_step("apply_corrections",  apply_corrections)
            .add_step("log_result",         log_audit_result))


def run_audit():
    """Execute one full audit cycle with self-correction."""
    pipeline = _audit_revenue_pipeline()

    def action(ctx):
        return pipeline.execute(ctx)

    def critique(result, ctx):
        errors = result.get("routing_errors", [])
        if errors and result.get("corrections_applied", 0) < len(errors):
            return {"confident": False, "reason": f"{len(errors)} unresolved routing errors"}
        return {"confident": True, "reason": "all routing verified"}

    self_correct(action, critique, context={})


def start_daemon():
    """Run the auditor continuously as a background daemon."""
    log.info("=== MUTUAL AID AUDITOR STARTING (daemon mode) ===")
    log.info(f"Rules: {int(LOCAL_AID_PERCENT*100)}% local aid | {int(SELF_FUND_PERCENT*100)}% SolarPunk | Audit every {AUDIT_INTERVAL_SECS}s")

    while True:
        try:
            run_audit()
        except Exception as e:
            log.error(f"Audit cycle failed: {e}")
            _alert_human("AUDIT_CYCLE_FAILURE", {"error": str(e)})
        time.sleep(AUDIT_INTERVAL_SECS)


if __name__ == "__main__":
    # Run one audit cycle (non-blocking for swarm engine use).
    # Pass --daemon flag to run the infinite audit loop.
    import sys
    if "--daemon" in sys.argv:
        run_audit()
        t = threading.Thread(target=start_daemon, daemon=True)
        t.start()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            log.info("Auditor standing down.")
    else:
        run_audit()
        log.info("Single audit cycle complete.")
