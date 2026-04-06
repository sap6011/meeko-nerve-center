# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
EVENT_RELAY.py -- Event-driven trigger system for local machine
================================================================
Monitors system state files and triggers actions based on changes.
Checks git status, product creation, article drafts, and cortex
directives to decide what actions to take.

DRY_RUN mode (default True) shows what WOULD happen without acting.

Triggers:
  - New products -> git add + commit + push
  - Ready articles + DEVTO_API_KEY -> mark for DEV_TO_PUBLISHER
  - Uncommitted changes in products/ or data/ -> report them

Output:
  data/event_relay_report.json
  data/event_relay_state.json
"""
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# -- paths ----------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

REPORT_FILE = DATA / "event_relay_report.json"
STATE_FILE = DATA / "event_relay_state.json"

# Source files to monitor
CORTEX_FILE = DATA / "cortex_directive.json"
PRODUCT_FORGE_FILE = DATA / "product_forge_report.json"
ARTICLE_DRAFTS_FILE = DATA / "article_drafts.json"

# Default: dry run mode -- set to False to execute actions
DRY_RUN = True


def load_json(path):
    """Load JSON from path, return empty dict on failure."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_json(path, data):
    """Write data as JSON to path."""
    Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def git_run(args, cwd=None):
    """Run a git command and return (returncode, stdout, stderr)."""
    cmd = ["git"] + args
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or str(BASE),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except FileNotFoundError:
        return -1, "", "git not found"


def check_git_status():
    """Check for uncommitted changes in products/ and data/."""
    changes = {"products": [], "data": [], "other": []}

    code, stdout, _ = git_run(["status", "--porcelain"])
    if code != 0:
        return changes

    for line in stdout.splitlines():
        if not line.strip():
            continue
        # Status is first 2 chars, then space, then path
        status_marker = line[:2].strip()
        file_path = line[3:].strip()

        if file_path.startswith("products/"):
            changes["products"].append({
                "status": status_marker,
                "file": file_path,
            })
        elif file_path.startswith("data/"):
            changes["data"].append({
                "status": status_marker,
                "file": file_path,
            })
        else:
            changes["other"].append({
                "status": status_marker,
                "file": file_path,
            })

    return changes


def check_new_products():
    """Check if product_forge_report.json indicates new products."""
    report = load_json(PRODUCT_FORGE_FILE)
    if not report:
        return {"found": False, "detail": "No product forge report found"}

    total = report.get("total_files", 0)
    if total > 0:
        return {
            "found": True,
            "total_files": total,
            "domains": list(report.get("domains", {}).keys()),
            "detail": "Found %d product files across %d domains" % (
                total, len(report.get("domains", {}))
            ),
        }
    return {"found": False, "detail": "Product forge report exists but has 0 files"}


def check_article_drafts():
    """Check if article_drafts.json has ready articles."""
    drafts = load_json(ARTICLE_DRAFTS_FILE)
    if not drafts:
        return {"found": False, "ready_count": 0, "detail": "No article drafts found"}

    # Handle both list and dict formats
    articles = []
    if isinstance(drafts, list):
        articles = drafts
    elif isinstance(drafts, dict):
        articles = drafts.get("articles", drafts.get("drafts", []))

    ready = [a for a in articles if a.get("status") in ("ready", "draft_complete", "approved")]
    return {
        "found": len(ready) > 0,
        "ready_count": len(ready),
        "total_count": len(articles),
        "detail": "%d of %d articles are ready" % (len(ready), len(articles)),
    }


def check_cortex_directive():
    """Read the current cortex directive."""
    directive = load_json(CORTEX_FILE)
    if not directive:
        return {"found": False, "detail": "No cortex directive found"}

    return {
        "found": True,
        "directive": directive.get("directive", "unknown"),
        "priority_engines": directive.get("priority_engines", []),
        "flags": directive.get("flags", {}),
        "detail": "Directive: %s" % directive.get("directive", "unknown"),
    }


def action_stage_and_commit_products(git_changes, dry_run=True):
    """Stage new product files and commit them."""
    product_files = [c["file"] for c in git_changes.get("products", [])]
    if not product_files:
        return {"action": "commit_products", "skipped": True, "reason": "No product files to commit"}

    if dry_run:
        return {
            "action": "commit_products",
            "dry_run": True,
            "would_stage": product_files,
            "would_commit_message": "feat: add %d new product templates" % len(product_files),
        }

    # Stage product files
    for f in product_files:
        code, _, err = git_run(["add", f])
        if code != 0:
            return {
                "action": "commit_products",
                "error": "Failed to stage %s: %s" % (f, err),
            }

    # Commit
    msg = "feat: add %d new product templates" % len(product_files)
    code, stdout, err = git_run(["commit", "-m", msg])
    if code != 0:
        return {"action": "commit_products", "error": "Commit failed: %s" % err}

    # Push
    code, stdout, err = git_run(["push", "origin", "HEAD"])
    push_result = "success" if code == 0 else "failed: %s" % err

    return {
        "action": "commit_products",
        "staged": product_files,
        "commit_message": msg,
        "push": push_result,
    }


def action_mark_articles_for_publisher(article_info, dry_run=True):
    """Mark ready articles for DEV_TO_PUBLISHER if API key is set."""
    has_key = bool(os.environ.get("DEVTO_API_KEY"))
    ready_count = article_info.get("ready_count", 0)

    if not article_info.get("found") or ready_count == 0:
        return {
            "action": "mark_for_publisher",
            "skipped": True,
            "reason": "No ready articles",
        }

    if not has_key:
        return {
            "action": "mark_for_publisher",
            "skipped": True,
            "reason": "DEVTO_API_KEY not set in environment",
            "ready_articles": ready_count,
        }

    if dry_run:
        return {
            "action": "mark_for_publisher",
            "dry_run": True,
            "would_mark": ready_count,
            "detail": "Would mark %d articles for DEV_TO_PUBLISHER" % ready_count,
        }

    # Actually mark articles for publishing
    drafts = load_json(ARTICLE_DRAFTS_FILE)
    articles = []
    if isinstance(drafts, list):
        articles = drafts
    elif isinstance(drafts, dict):
        articles = drafts.get("articles", drafts.get("drafts", []))

    marked = 0
    for article in articles:
        if article.get("status") in ("ready", "draft_complete", "approved"):
            article["queued_for"] = "DEV_TO_PUBLISHER"
            article["queued_at"] = datetime.now(timezone.utc).isoformat()
            marked += 1

    if isinstance(drafts, list):
        save_json(ARTICLE_DRAFTS_FILE, articles)
    else:
        key = "articles" if "articles" in drafts else "drafts"
        drafts[key] = articles
        save_json(ARTICLE_DRAFTS_FILE, drafts)

    return {
        "action": "mark_for_publisher",
        "marked_count": marked,
        "detail": "Marked %d articles for DEV_TO_PUBLISHER" % marked,
    }


def run():
    """Execute the event relay cycle."""
    print("[EVENT_RELAY] Starting event relay cycle...")
    mode_label = "DRY RUN" if DRY_RUN else "LIVE"
    print("[EVENT_RELAY] Mode: %s" % mode_label)
    print("=" * 60)

    report = {
        "engine": "EVENT_RELAY",
        "mode": mode_label,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "checks": {},
        "actions": [],
        "summary": {},
    }

    # -- 1. Check cortex directive --
    print("\n[1] Checking cortex directive...")
    cortex = check_cortex_directive()
    report["checks"]["cortex_directive"] = cortex
    print("    %s" % cortex["detail"])

    # -- 2. Check for new products --
    print("\n[2] Checking for new products...")
    products = check_new_products()
    report["checks"]["new_products"] = products
    print("    %s" % products["detail"])

    # -- 3. Check for article drafts --
    print("\n[3] Checking article drafts...")
    articles = check_article_drafts()
    report["checks"]["article_drafts"] = articles
    print("    %s" % articles["detail"])

    # -- 4. Check git status --
    print("\n[4] Checking git status...")
    git_changes = check_git_status()
    product_count = len(git_changes["products"])
    data_count = len(git_changes["data"])
    other_count = len(git_changes["other"])
    print("    Uncommitted: %d products, %d data, %d other" % (
        product_count, data_count, other_count
    ))
    report["checks"]["git_status"] = {
        "products_changed": product_count,
        "data_changed": data_count,
        "other_changed": other_count,
        "details": git_changes,
    }

    # -- 5. Execute actions based on checks --
    print("\n" + "-" * 60)
    print("[Actions]")

    # Action: commit products if new
    if product_count > 0:
        print("\n  -> Staging and committing %d product files..." % product_count)
        result = action_stage_and_commit_products(git_changes, dry_run=DRY_RUN)
        report["actions"].append(result)
        if result.get("dry_run"):
            print("     [DRY RUN] Would stage %d files" % len(result.get("would_stage", [])))
        elif result.get("error"):
            print("     [ERROR] %s" % result["error"])
        else:
            print("     [DONE] Committed and pushed")
    else:
        print("\n  -> No product files to commit")

    # Action: mark articles for publisher
    if articles.get("found"):
        print("\n  -> Checking article publish readiness...")
        result = action_mark_articles_for_publisher(articles, dry_run=DRY_RUN)
        report["actions"].append(result)
        if result.get("skipped"):
            print("     [SKIP] %s" % result["reason"])
        elif result.get("dry_run"):
            print("     [DRY RUN] %s" % result["detail"])
        else:
            print("     [DONE] %s" % result.get("detail", ""))
    else:
        print("\n  -> No articles ready for publishing")

    # -- Summary --
    report["summary"] = {
        "total_checks": len(report["checks"]),
        "total_actions": len(report["actions"]),
        "actions_executed": sum(
            1 for a in report["actions"]
            if not a.get("skipped") and not a.get("dry_run")
        ),
        "actions_dry_run": sum(
            1 for a in report["actions"] if a.get("dry_run")
        ),
        "actions_skipped": sum(
            1 for a in report["actions"] if a.get("skipped")
        ),
    }
    report["completed_at"] = datetime.now(timezone.utc).isoformat()

    # Save report
    save_json(REPORT_FILE, report)

    # Save state
    state = load_json(STATE_FILE)
    state["last_run"] = report["completed_at"]
    state["last_mode"] = mode_label
    state["run_count"] = state.get("run_count", 0) + 1
    state["last_summary"] = report["summary"]
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    save_json(STATE_FILE, state)

    print("\n" + "=" * 60)
    print("[EVENT_RELAY] Complete! (%s)" % mode_label)
    print("  Checks:   %d" % report["summary"]["total_checks"])
    print("  Actions:  %d (executed: %d, dry_run: %d, skipped: %d)" % (
        report["summary"]["total_actions"],
        report["summary"]["actions_executed"],
        report["summary"]["actions_dry_run"],
        report["summary"]["actions_skipped"],
    ))
    print("  Report:   %s" % REPORT_FILE)


if __name__ == "__main__":
    run()
