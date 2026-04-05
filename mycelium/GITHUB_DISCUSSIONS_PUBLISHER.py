# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
GITHUB_DISCUSSIONS_PUBLISHER.py -- Creates GitHub Discussions for the SolarPunk organism
========================================================================================
Generates three kinds of Discussion posts:
  1. Product launches  -- from data/product_registry.json
  2. Weekly system reports -- from data/chimera_evolution_report.json
  3. Crisis updates    -- from data/crisis_signals.json

Uses the GitHub GraphQL API (urllib only) to create Discussions.
If GITHUB_TOKEN is missing, runs DRY_RUN mode: generates the markdown,
saves to data/discussion_drafts.json, prints what it would post.

Tracks posted discussions in data/discussions_publisher_state.json
to avoid duplicates (keyed by content hash).

Every post includes a PCRF (Palestinian Children's Relief Fund) note.
"""
import os
import json
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA  = Path("data"); DATA.mkdir(exist_ok=True)
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = "meekotharaccoon-cell"
REPO  = "meeko-nerve-center"
GRAPHQL_URL = "https://api.github.com/graphql"
SHOP_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
KOFI_URL = "https://ko-fi.com/meekotharaccoon"
REPO_URL = "https://github.com/%s/%s" % (OWNER, REPO)

# Category suggestions -- the actual category ID must be fetched at runtime
CATEGORY_PRODUCT  = "Announcements"
CATEGORY_REPORT   = "General"
CATEGORY_CRISIS   = "Announcements"

STATE_FILE  = DATA / "discussions_publisher_state.json"
DRAFTS_FILE = DATA / "discussion_drafts.json"

PCRF_NOTE = (
    "\n\n---\n\n"
    "**15% of every dollar SolarPunk earns goes to "
    "[PCRF](https://www.pcrf.net/) (Palestinian Children's Relief Fund, "
    "EIN 93-1057665) -- automatically, before any payout.**\n\n"
    "Free Palestine.\n"
)


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"cycles": 0, "posted_hashes": [], "posted": [], "dry_runs": 0}


def save_state(state):
    state["posted_hashes"] = state.get("posted_hashes", [])[-500:]
    state["posted"] = state.get("posted", [])[-200:]
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_drafts():
    if DRAFTS_FILE.exists():
        try:
            return json.loads(DRAFTS_FILE.read_text())
        except Exception:
            pass
    return {"drafts": []}


def save_drafts(drafts):
    drafts["drafts"] = drafts.get("drafts", [])[-100:]
    DRAFTS_FILE.write_text(json.dumps(drafts, indent=2))


def content_hash(title, body):
    raw = "%s::%s" % (title.strip(), body.strip()[:500])
    return hashlib.md5(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# GitHub GraphQL helpers
# ---------------------------------------------------------------------------

def graphql(query, variables=None):
    """Execute a GraphQL query against the GitHub API. Returns (data, error)."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    data_bytes = json.dumps(payload).encode()
    req = urllib.request.Request(GRAPHQL_URL, data=data_bytes, method="POST", headers={
        "Authorization": "Bearer %s" % TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "SolarPunk-Discussions/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
        if resp.get("errors"):
            msg = resp.get("errors", [{}])[0].get("message", "unknown graphql error")
            return None, msg
        return resp.get("data"), None
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()[:200]
        except Exception:
            pass
        return None, "HTTP %s: %s" % (e.code, body)
    except Exception as e:
        return None, str(e)[:200]


def fetch_repo_id():
    """Fetch the repository node ID needed for creating discussions."""
    q = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        id
        discussionCategories(first: 25) {
          nodes { id name }
        }
      }
    }
    """
    data, err = graphql(q, {"owner": OWNER, "name": REPO})
    if err or not data:
        return None, {}, err or "no data"
    repo = data.get("repository", {})
    repo_id = repo.get("id", "")
    cats = {}
    for node in repo.get("discussionCategories", {}).get("nodes", []):
        cats[node.get("name", "")] = node.get("id", "")
    return repo_id, cats, None


def create_discussion(repo_id, category_id, title, body):
    """Create a discussion via GraphQL mutation. Returns (url, error)."""
    mutation = """
    mutation($repoId: ID!, $catId: ID!, $title: String!, $body: String!) {
      createDiscussion(input: {
        repositoryId: $repoId,
        categoryId: $catId,
        title: $title,
        body: $body
      }) {
        discussion { url }
      }
    }
    """
    data, err = graphql(mutation, {
        "repoId": repo_id,
        "catId": category_id,
        "title": title,
        "body": body,
    })
    if err or not data:
        return "", err or "no data returned"
    url = data.get("createDiscussion", {}).get("discussion", {}).get("url", "")
    return url, None


# ---------------------------------------------------------------------------
# Discussion generators
# ---------------------------------------------------------------------------

def build_product_discussions():
    """Build discussion posts for products that haven't been announced yet."""
    registry_path = DATA / "product_registry.json"
    if not registry_path.exists():
        return []
    try:
        registry = json.loads(registry_path.read_text())
    except Exception:
        return []

    products = registry.get("products", {})
    discussions = []
    for pid, product in products.items():
        if not product.get("content_ready"):
            continue
        title_text = product.get("title", pid)
        price = product.get("price", 0)
        ptype = product.get("type", "guide")
        word_count = product.get("word_count", 0)
        sections = product.get("sections", 0)
        download_url = product.get("download_url", "")
        gumroad_url = product.get("gumroad_url", "")
        kofi_url_product = product.get("kofi_url", "")

        title = "New Product: %s" % title_text

        body_parts = [
            "# %s" % title_text,
            "",
            "A new digital product from the SolarPunk autonomous system.",
            "",
            "## Details",
            "",
            "| Field | Value |",
            "|-------|-------|",
            "| **Price** | $%.2f |" % price,
            "| **Type** | %s |" % ptype,
            "| **Words** | %s |" % ("{:,}".format(word_count) if word_count else "N/A"),
            "| **Sections** | %s |" % (sections or "N/A"),
            "",
        ]

        if download_url:
            body_parts.append("**Download:** [%s](%s)" % (title_text, download_url))
            body_parts.append("")
        if gumroad_url:
            body_parts.append("**Buy on Gumroad:** [%s](%s)" % (title_text, gumroad_url))
            body_parts.append("")
        if kofi_url_product:
            body_parts.append("**Buy on Ko-fi:** [%s](%s)" % (title_text, kofi_url_product))
            body_parts.append("")

        # Bundle info
        components = product.get("components", [])
        if components:
            body_parts.append("## Bundle Contents")
            body_parts.append("")
            for comp in components:
                body_parts.append("- %s" % comp.replace("_", " ").title())
            individual_total = product.get("individual_total", 0)
            savings_pct = product.get("savings_pct", 0)
            if individual_total and savings_pct:
                body_parts.append("")
                body_parts.append(
                    "**Save %d%%** -- individual total $%.2f, bundle price $%.2f"
                    % (savings_pct, individual_total, price)
                )
            body_parts.append("")

        body_parts.extend([
            "## Links",
            "",
            "- [SolarPunk Store](%s/store.html)" % SHOP_URL,
            "- [Ko-fi](%s)" % KOFI_URL,
            "- [Source Code](%s)" % REPO_URL,
            "",
            "*Built autonomously by the SolarPunk organism.*",
            PCRF_NOTE,
        ])

        body = "\n".join(body_parts)
        discussions.append({
            "title": title,
            "body": body,
            "category": CATEGORY_PRODUCT,
            "source": "product",
            "source_id": pid,
        })

    return discussions


def build_system_report():
    """Build a weekly system status discussion from chimera_evolution_report."""
    report_path = DATA / "chimera_evolution_report.json"
    if not report_path.exists():
        return []
    try:
        report = json.loads(report_path.read_text())
    except Exception:
        return []

    ts = report.get("timestamp", "unknown")
    generation = report.get("generation", "?")
    composite = report.get("composite_score", 0)
    ethics = report.get("ethics_lock", "99% mutual aid / 1% node fuel")

    scores = report.get("scores", {})
    wiring = scores.get("wiring", 0)
    hunger = scores.get("hunger_reduction", 0)
    bridge = scores.get("bridge_rate", 0)
    health = scores.get("health", 0)
    mutation = scores.get("mutation", 0)

    stats = report.get("post_scan_stats", report.get("pre_scan_stats", {}))
    total_engines = stats.get("total_engines", 0)
    zs_engines = stats.get("zero_secrets_engines", 0)
    total_wires = stats.get("total_wires_discovered", 0)
    zs_chains = stats.get("zero_secret_chains", 0)
    hungry = stats.get("hungry_inputs", 0)
    connected_files = stats.get("connected_data_files", 0)

    bridges_built = report.get("bridges_built", 0)
    mutations_total = report.get("mutations_total", 0)
    best_ever = report.get("best_ever_score", 0)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = "System Report: Generation %s -- Score %s/100 (%s)" % (
        generation, composite, date_str
    )

    body_parts = [
        "# SolarPunk System Report",
        "",
        "**Generation:** %s | **Composite Score:** %s/100 | **Best Ever:** %s/100" % (
            generation, composite, best_ever
        ),
        "",
        "**Ethics Lock:** %s" % ethics,
        "",
        "## Evolution Scores",
        "",
        "| Metric | Score |",
        "|--------|-------|",
        "| Wiring | %s |" % wiring,
        "| Hunger Reduction | %s |" % hunger,
        "| Bridge Rate | %s |" % bridge,
        "| Health | %s |" % health,
        "| Mutation | %s |" % mutation,
        "",
        "## Infrastructure",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        "| Total Engines | %s |" % total_engines,
        "| Zero-Secret Engines | %s |" % zs_engines,
        "| Total Wires | %s |" % "{:,}".format(total_wires),
        "| Zero-Secret Chains | %s |" % "{:,}".format(zs_chains),
        "| Hungry Inputs | %s |" % hungry,
        "| Connected Data Files | %s |" % connected_files,
        "",
        "## This Cycle",
        "",
        "- **Bridges built:** %s" % bridges_built,
        "- **Mutations:** %s" % mutations_total,
        "",
        "## What is SolarPunk?",
        "",
        "SolarPunk is an autonomous digital organism -- self-building, self-funding, "
        "with Palestinian solidarity hardcoded into its DNA. %s engines. "
        "%s wires. Running without human intervention." % (
            total_engines, "{:,}".format(total_wires)
        ),
        "",
        "- [Live System](%s)" % SHOP_URL,
        "- [Ko-fi](%s)" % KOFI_URL,
        "- [Source](%s)" % REPO_URL,
        "",
        "*This report was generated autonomously by the SolarPunk organism.*",
        PCRF_NOTE,
    ]

    body = "\n".join(body_parts)
    return [{
        "title": title,
        "body": body,
        "category": CATEGORY_REPORT,
        "source": "system_report",
        "source_id": "gen-%s-%s" % (generation, date_str),
    }]


def build_crisis_discussions():
    """Build discussion posts for active crisis signals."""
    crisis_path = DATA / "crisis_signals.json"
    if not crisis_path.exists():
        return []
    try:
        crisis_data = json.loads(crisis_path.read_text())
    except Exception:
        return []

    signals = crisis_data.get("signals", [])
    if not signals:
        return []

    total = crisis_data.get("total", 0)
    by_urgency = crisis_data.get("by_urgency", {})

    discussions = []
    for signal in signals:
        sig_type = signal.get("type", "unknown")
        urgency = signal.get("urgency", "medium")
        summary = signal.get("summary", signal.get("description", "Crisis signal detected"))
        source = signal.get("source", "")
        sig_ts = signal.get("timestamp", signal.get("detected_at", ""))
        sig_id = signal.get("id", hashlib.md5(summary.encode()).hexdigest()[:12])

        urgency_label = {
            "critical": "CRITICAL",
            "high": "HIGH",
            "medium": "MEDIUM",
            "low": "LOW",
        }.get(urgency, urgency.upper())

        title = "[%s] Crisis Signal: %s" % (urgency_label, sig_type.replace("_", " ").title())

        body_parts = [
            "# Crisis Signal: %s" % sig_type.replace("_", " ").title(),
            "",
            "**Urgency:** %s" % urgency_label,
            "**Type:** %s" % sig_type,
            "",
        ]
        if sig_ts:
            body_parts.append("**Detected:** %s" % sig_ts)
            body_parts.append("")
        if source:
            body_parts.append("**Source:** %s" % source)
            body_parts.append("")

        body_parts.extend([
            "## Summary",
            "",
            summary,
            "",
            "## Context",
            "",
            "- **Total active signals:** %s" % total,
        ])

        for level, count in by_urgency.items():
            body_parts.append("- **%s:** %s" % (level.title(), count))

        body_parts.extend([
            "",
            "## How to Help",
            "",
            "- [Ko-fi](%s) -- direct support" % KOFI_URL,
            "- [Source Code](%s) -- fork, contribute, amplify" % REPO_URL,
            "",
            "*This crisis update was generated autonomously by the SolarPunk organism.*",
            PCRF_NOTE,
        ])

        body = "\n".join(body_parts)
        discussions.append({
            "title": title,
            "body": body,
            "category": CATEGORY_CRISIS,
            "source": "crisis",
            "source_id": "crisis-%s" % sig_id,
        })

    return discussions


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def run():
    ts = datetime.now(timezone.utc).isoformat()
    state = load_state()
    state["cycles"] = state.get("cycles", 0) + 1
    posted_hashes = set(state.get("posted_hashes", []))

    dry_run = not TOKEN
    mode = "DRY_RUN" if dry_run else "LIVE"
    print("GITHUB_DISCUSSIONS_PUBLISHER cycle %s [%s]" % (state.get("cycles", 1), mode))

    if dry_run:
        print("  No GITHUB_TOKEN -- generating drafts only")

    # Collect all discussions to post
    all_discussions = []
    all_discussions.extend(build_product_discussions())
    all_discussions.extend(build_system_report())
    all_discussions.extend(build_crisis_discussions())

    if not all_discussions:
        print("  No discussions to generate")
        save_state(state)
        return state

    print("  Candidates: %s discussions" % len(all_discussions))

    # Filter out already-posted
    new_discussions = []
    for disc in all_discussions:
        h = content_hash(disc.get("title", ""), disc.get("body", ""))
        if h not in posted_hashes:
            disc["_hash"] = h
            new_discussions.append(disc)

    if not new_discussions:
        print("  All discussions already posted -- nothing to do")
        save_state(state)
        return state

    print("  New: %s discussions" % len(new_discussions))

    # Fetch repo info if live
    repo_id = ""
    categories = {}
    if not dry_run:
        repo_id, categories, err = fetch_repo_id()
        if err:
            print("  Could not fetch repo info: %s" % err)
            print("  Falling back to DRY_RUN mode")
            dry_run = True
        else:
            print("  Repo ID: %s" % repo_id[:20])
            print("  Categories: %s" % ", ".join(categories.keys()))

    # Process each discussion
    drafts = load_drafts()
    posted_count = 0
    draft_count = 0

    for disc in new_discussions:
        title = disc.get("title", "Untitled")
        body = disc.get("body", "")
        category_name = disc.get("category", CATEGORY_REPORT)
        h = disc.get("_hash", content_hash(title, body))
        source = disc.get("source", "unknown")
        source_id = disc.get("source_id", "")

        if dry_run:
            # Save as draft
            draft_entry = {
                "title": title,
                "body": body,
                "category": category_name,
                "source": source,
                "source_id": source_id,
                "generated_at": ts,
                "hash": h,
            }
            drafts.setdefault("drafts", []).append(draft_entry)
            draft_count += 1
            print("  DRAFT: %s" % title[:70])
        else:
            # Post via GraphQL
            cat_id = categories.get(category_name, "")
            if not cat_id:
                # Fall back to first available category
                if categories:
                    fallback_name = list(categories.keys())[0]
                    cat_id = categories.get(fallback_name, "")
                    print("  Category '%s' not found, using '%s'" % (category_name, fallback_name))
                else:
                    print("  SKIP: no discussion categories available")
                    continue

            url, err = create_discussion(repo_id, cat_id, title, body)
            if err:
                print("  FAIL: %s -- %s" % (title[:50], err[:80]))
                # Save as draft on failure
                draft_entry = {
                    "title": title,
                    "body": body,
                    "category": category_name,
                    "source": source,
                    "source_id": source_id,
                    "generated_at": ts,
                    "hash": h,
                    "error": err[:200],
                }
                drafts.setdefault("drafts", []).append(draft_entry)
                draft_count += 1
                continue

            posted_hashes.add(h)
            state.setdefault("posted", []).append({
                "title": title,
                "url": url,
                "category": category_name,
                "source": source,
                "source_id": source_id,
                "posted_at": ts,
                "hash": h,
            })
            posted_count += 1
            print("  POSTED: %s -> %s" % (title[:50], url))

    # Save everything
    state["posted_hashes"] = list(posted_hashes)
    state["last_run"] = ts
    state["last_mode"] = mode

    if dry_run:
        state["dry_runs"] = state.get("dry_runs", 0) + 1
        save_drafts(drafts)
        print("  Saved %s drafts to %s" % (draft_count, DRAFTS_FILE))
    else:
        state["total_posted"] = len(state.get("posted", []))

    save_state(state)
    print("  Done: %s posted, %s drafted" % (posted_count, draft_count))
    return state


if __name__ == "__main__":
    run()
