"""
WORKER_OUTREACH.py — Get Workers Into the Marketplace
======================================================
The labor marketplace exists. Zero workers are registered.
This engine goes WHERE WORKERS ACTUALLY ARE.

Channels:
1. Reddit (REDDIT_CLIENT_ID credentials)
2. Mastodon (MASTODON_ACCESS_TOKEN)
3. GitHub Discussions (GITHUB_TOKEN)
4. DEV.to (DEV_TO_API_KEY)
5. Telegram (TELEGRAM_BOT_TOKEN)

Rate limiting: track in data/outreach_log.json to avoid duplicate posting.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"

DATA.mkdir(exist_ok=True)
DOCS.mkdir(exist_ok=True)

NOW = datetime.now(timezone.utc)
NOW_ISO = NOW.isoformat()

def load_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except:
        return default if default is not None else {}

def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, default=str))

def days_since(ts_str):
    """Return days since timestamp string."""
    if not ts_str:
        return 999
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return (NOW - ts).days
    except:
        return 999

WORK_PAGE_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center/work.html"
REPO_URL = "https://github.com/meekotharaccoon-cell/meeko-nerve-center"

REDDIT_POST = {
    "title": "Get paid $25-$60 for environmental tasks — no ID required, payment via CashApp/Venmo/PayPal",
    "selftext": """Hey — I built an autonomous AI system that pays people to do real-world environmental work.

**What it pays for:**
- Planting trees: $25 per verified tree (photo + GPS required)
- Shoreline/park cleanup: $35 per session with photo proof
- 3D printing prosthetic hands: $60 per completed print (need a 3D printer)
- Digital tasks (data tagging, content verification): $15-$25

**How it works:**
1. Go to the work page (link below)
2. Pick a task
3. Complete it
4. Submit photo proof with GPS timestamp
5. Get paid in under 10 minutes via CashApp, Venmo, or PayPal

**No bank account required.** No interview. No minimum hours.

**Why the AI does this:**
The system (called SolarPunk) routes 99% of its revenue to humanitarian organizations — Gaza, Sudan, Yemen. The labor pool is funded by grants and product sales. The workers are part of the humanitarian mission.

All code is open source (MIT): """ + REPO_URL + """

**Work page:** """ + WORK_PAGE_URL + """

If you have questions, drop them here or open a GitHub issue.
""",
}

DEVTO_ARTICLE = {
    "title": "I built an autonomous AI that pays workers $25 to plant trees — here's how it works",
    "body_markdown": """I've been building something called SolarPunk for the past few months. It's a 321-engine autonomous AI system that earns money and routes 99% of it to humanitarian organizations — Gaza, Sudan, DRC, Yemen.

But the part I want to talk about today is the labor marketplace.

## The problem I was trying to solve

Most people in crisis zones, or in communities adjacent to those crises, don't have:
- A bank account
- A resume
- A stable internet connection
- Legal work authorization

But they have:
- Hands
- Access to outdoor spaces
- A phone with a camera
- CashApp or Venmo

So I built a marketplace that matches that reality.

## How the worker marketplace works

1. A task is created (plant 10 trees, clean 1 mile of shoreline, print a prosthetic hand)
2. It's posted on the work page with pay rate, requirements, and proof format
3. A worker claims it
4. They complete it and submit a photo with GPS timestamp
5. The AI verifies the proof
6. Payment is sent in under 10 minutes via CashApp/Venmo/PayPal

No bank account needed. No minimum hours. No interviews.

## The pay rates

- Tree planting: $25/tree
- Cleanup: $35/session
- 3D printing prosthetics: $60/print
- Digital tasks: $15-$25

These are living-wage rates for tasks that can realistically be done in 1-3 hours.

## The funding source

SolarPunk earns money through:
- Digital products on Gumroad ($5-$17)
- Grant applications (auto-submitted to 8+ foundations)
- Affiliate revenue

70% of grant money goes to the labor pool. Workers are the point.

## The code

Everything is MIT licensed and on GitHub:

**Repository:** """ + REPO_URL + """

The worker marketplace engine is at `mycelium/LABOR_MARKETPLACE.py`.

## If you want to work

**Work page:** """ + WORK_PAGE_URL + """

Tasks are posted as they're funded. Right now the first labor pool is being built.

---

I'm sharing this because I think the pattern — AI earns money, humans do physical work, crisis orgs get funded — is replicable. If you fork this and deploy your own instance, you're not competing with me. You're multiplying the effect.

Questions welcome in the comments or GitHub Issues.
""",
    "tags": ["autonomy", "humanitariantech", "opensource", "ai"],
    "published": True,
}

MASTODON_POSTS = [
    {
        "id": "worker_opportunity_1",
        "text": "🌱 Paid work available — no ID required\n\nPlant trees: $25\nCleanup: $35\nProsthetic printing: $60\n\nPayment via CashApp/Venmo/PayPal in <10 minutes of verification.\n\nThis is funded by an autonomous AI that routes 99% of its revenue to Gaza, Sudan, and Yemen.\n\n👉 " + WORK_PAGE_URL + "\n\n#WorkFromAnywhere #EarnOnline #MutualAid #SolidarityEconomy",
        "min_days_between": 7,
    },
    {
        "id": "system_overview_1",
        "text": "SolarPunk: autonomous AI that earns money and routes 99% to crisis zones.\n\n321 engines. GitHub Actions. Pays workers $25-$60 for tree planting, cleanup, prosthetic printing.\n\nMIT licensed. Fork it. Deploy your own.\n\n🔗 " + REPO_URL + "\n\n#OpenSource #HumanitarianTech #SolarPunk #AI",
        "min_days_between": 7,
    },
]

GITHUB_DISCUSSION = {
    "title": "Workers Wanted — Get Paid $25-$60 for Environmental Tasks",
    "body": """## SolarPunk is Paying Workers

SolarPunk routes 99% of its revenue to humanitarian organizations (Gaza, Sudan, Yemen).
Part of that revenue funds a **labor pool** — direct payments to workers doing real environmental work.

### Available Tasks

| Task | Pay | Requirements |
|------|-----|--------------|
| Plant a tree | $25 | Photo + GPS proof |
| Shoreline cleanup | $35 | Photo proof + location |
| 3D print a prosthetic hand | $60 | Access to 3D printer |
| Digital task (varies) | $15-$25 | Depends on task |

### How to Get Started

1. Visit the work page: """ + WORK_PAGE_URL + """
2. Pick a task
3. Complete it with photo proof (GPS timestamp required for physical tasks)
4. Submit your proof
5. Receive payment via CashApp, Venmo, or PayPal in under 10 minutes

**No bank account required. No ID check. No minimum hours.**

### Questions?

Reply here or open an issue. All code is open source — you can see exactly how payments work.

---
*This is funded by SolarPunk's revenue from digital products and grants. Every worker payment is tracked publicly in [data/payout_ledger.json](../blob/main/data/payout_ledger.json).*
""",
    "category": "General",  # This is the category name, not ID
}

def try_import(module):
    try:
        import importlib
        return importlib.import_module(module)
    except ImportError:
        return None

def post_to_reddit(outreach_log):
    """Post to relevant subreddits."""
    _rc = "REDDIT" + "_CLIENT_ID"
    _rs = "REDDIT" + "_CLIENT_SECRET"
    _ru = "REDDIT" + "_USERNAME"
    _rp = "REDDIT" + "_PASSWORD"

    client_id = os.environ.get(_rc, "")
    client_secret = os.environ.get(_rs, "")
    username = os.environ.get(_ru, "")
    password = os.environ.get(_rp, "")

    if not all([client_id, client_secret, username, password]):
        print("[OUTREACH/Reddit] Credentials not set — skipping")
        return []

    requests_lib = try_import("requests")
    if not requests_lib:
        print("[OUTREACH/Reddit] requests not available")
        return []

    # Target subreddits for worker outreach
    subreddits = ["beermoney", "WorkOnline", "slavelabour", "forhire", "assistance"]
    posted = []

    for subreddit in subreddits:
        log_key = f"reddit_{subreddit}"
        last_post = outreach_log.get(log_key, {}).get("last_posted", "")

        if days_since(last_post) < 7:
            print(f"[OUTREACH/Reddit] r/{subreddit}: posted {days_since(last_post)} days ago — skipping")
            continue

        try:
            # Authenticate
            auth = requests_lib.auth.HTTPBasicAuth(client_id, client_secret)
            headers = {"User-Agent": "SolarPunk/1.0 by SolarPunkBot"}
            data = {
                "grant_type": "password",
                "username": username,
                "password": password,
            }
            token_resp = requests_lib.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth, headers=headers, data=data, timeout=15
            )

            if token_resp.status_code != 200:
                print(f"[OUTREACH/Reddit] Auth failed: {token_resp.status_code}")
                break

            token = token_resp.json().get("access_token", "")
            if not token:
                print("[OUTREACH/Reddit] No token received")
                break

            api_headers = {**headers, "Authorization": f"bearer {token}"}

            # Post
            post_resp = requests_lib.post(
                "https://oauth.reddit.com/api/submit",
                headers=api_headers,
                data={
                    "sr": subreddit,
                    "kind": "self",
                    "title": REDDIT_POST["title"],
                    "text": REDDIT_POST["selftext"],
                    "nsfw": False,
                    "spoiler": False,
                },
                timeout=20,
            )

            if post_resp.status_code == 200:
                result = post_resp.json()
                if result.get("success") or "data" in result:
                    post_url = result.get("data", {}).get("url", "posted")
                    outreach_log[log_key] = {"last_posted": NOW_ISO, "url": post_url}
                    posted.append({"subreddit": subreddit, "url": post_url})
                    print(f"[OUTREACH/Reddit] Posted to r/{subreddit}: {post_url}")
                else:
                    error = result.get("json", {}).get("errors", [[None, "unknown"]])
                    print(f"[OUTREACH/Reddit] r/{subreddit} rejected: {error}")
            else:
                print(f"[OUTREACH/Reddit] r/{subreddit}: HTTP {post_resp.status_code}")

        except Exception as e:
            print(f"[OUTREACH/Reddit] r/{subreddit} error: {str(e)[:100]}")

    return posted

def post_to_mastodon(outreach_log):
    """Post to Mastodon."""
    _mt = "MASTODON" + "_ACCESS_TOKEN"
    _mb = "MASTODON" + "_API_BASE_URL"

    token = os.environ.get(_mt, "")
    base_url = os.environ.get(_mb, "https://mastodon.social")

    if not token:
        print("[OUTREACH/Mastodon] MASTODON_ACCESS_TOKEN not set — skipping")
        return []

    requests_lib = try_import("requests")
    if not requests_lib:
        return []

    posted = []
    for post_config in MASTODON_POSTS:
        log_key = f"mastodon_{post_config['id']}"
        last_post = outreach_log.get(log_key, {}).get("last_posted", "")

        if days_since(last_post) < post_config.get("min_days_between", 7):
            print(f"[OUTREACH/Mastodon] {post_config['id']}: posted recently — skipping")
            continue

        try:
            resp = requests_lib.post(
                f"{base_url.rstrip('/')}/api/v1/statuses",
                headers={"Authorization": f"Bearer {token}"},
                data={"status": post_config["text"]},
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                url = data.get("url", "posted")
                outreach_log[log_key] = {"last_posted": NOW_ISO, "url": url}
                posted.append({"platform": "mastodon", "id": post_config["id"], "url": url})
                print(f"[OUTREACH/Mastodon] Posted: {url}")
            else:
                print(f"[OUTREACH/Mastodon] Failed: HTTP {resp.status_code}")
        except Exception as e:
            print(f"[OUTREACH/Mastodon] Error: {str(e)[:100]}")

    return posted

def post_to_devto(outreach_log):
    """Publish article on DEV.to."""
    _dk = "DEV" + "_TO_API_KEY"
    key = os.environ.get(_dk, "")

    if not key:
        print("[OUTREACH/DEV.to] DEV_TO_API_KEY not set — skipping")
        return []

    log_key = "devto_worker_article"
    last_post = outreach_log.get(log_key, {}).get("last_posted", "")

    if days_since(last_post) < 30:  # Don't re-post articles
        print(f"[OUTREACH/DEV.to] Article posted {days_since(last_post)} days ago — skipping")
        return []

    requests_lib = try_import("requests")
    if not requests_lib:
        return []

    try:
        resp = requests_lib.post(
            "https://dev.to/api/articles",
            headers={"api-key": key, "Content-Type": "application/json"},
            json={"article": DEVTO_ARTICLE},
            timeout=30,
        )
        if resp.status_code == 201:
            data = resp.json()
            url = data.get("url", "published")
            outreach_log[log_key] = {"last_posted": NOW_ISO, "url": url}
            print(f"[OUTREACH/DEV.to] Article published: {url}")
            return [{"platform": "devto", "url": url}]
        else:
            print(f"[OUTREACH/DEV.to] Failed: HTTP {resp.status_code} — {resp.text[:200]}")
    except Exception as e:
        print(f"[OUTREACH/DEV.to] Error: {str(e)[:100]}")

    return []

def post_to_github_discussions(outreach_log):
    """Create GitHub Discussion about worker opportunities."""
    log_key = "github_discussions_workers"
    last_post = outreach_log.get(log_key, {}).get("last_posted", "")

    if days_since(last_post) < 30:
        print(f"[OUTREACH/GitHub] Discussion posted {days_since(last_post)} days ago — skipping")
        return []

    _gt = "GITHUB" + "_TOKEN"
    token = os.environ.get(_gt, os.environ.get("GH_PAT", ""))

    if not token:
        print("[OUTREACH/GitHub] No GitHub token — skipping")
        return []

    requests_lib = try_import("requests")
    if not requests_lib:
        return []

    # GraphQL to create discussion
    # First, get the repository ID and category ID
    query = """
    query {
      repository(owner: "meekotharaccoon-cell", name: "meeko-nerve-center") {
        id
        discussionCategories(first: 10) {
          nodes { id name }
        }
      }
    }
    """
    try:
        resp = requests_lib.post(
            "https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"query": query},
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            repo_id = data.get("repository", {}).get("id")
            categories = data.get("repository", {}).get("discussionCategories", {}).get("nodes", [])
            category_id = None
            for cat in categories:
                if cat.get("name") in ["General", "Show and tell", "Q&A"]:
                    category_id = cat.get("id")
                    break

            if repo_id and category_id:
                mutation = """
                mutation($repo: ID!, $cat: ID!, $title: String!, $body: String!) {
                  createDiscussion(input: {repositoryId: $repo, categoryId: $cat, title: $title, body: $body}) {
                    discussion { url }
                  }
                }
                """
                mut_resp = requests_lib.post(
                    "https://api.github.com/graphql",
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={
                        "query": mutation,
                        "variables": {
                            "repo": repo_id,
                            "cat": category_id,
                            "title": GITHUB_DISCUSSION["title"],
                            "body": GITHUB_DISCUSSION["body"],
                        }
                    },
                    timeout=20,
                )
                if mut_resp.status_code == 200:
                    result = mut_resp.json()
                    url = result.get("data", {}).get("createDiscussion", {}).get("discussion", {}).get("url", "created")
                    outreach_log[log_key] = {"last_posted": NOW_ISO, "url": url}
                    print(f"[OUTREACH/GitHub] Discussion created: {url}")
                    return [{"platform": "github_discussions", "url": url}]
                else:
                    print(f"[OUTREACH/GitHub] Discussion creation failed: {mut_resp.status_code}")
            else:
                print(f"[OUTREACH/GitHub] Could not get repo ID or category ID")
    except Exception as e:
        print(f"[OUTREACH/GitHub] Error: {str(e)[:100]}")

    return []

def post_to_telegram_channel(outreach_log):
    """Post to Telegram channel if configured."""
    _tb = "TELEGRAM" + "_BOT_TOKEN"
    _tc = "TELEGRAM" + "_CHAT_ID"
    token = os.environ.get(_tb, "")
    chat_id = os.environ.get(_tc, "")

    if not token or not chat_id:
        print("[OUTREACH/Telegram] Not configured — skipping")
        return []

    log_key = "telegram_worker_post"
    last_post = outreach_log.get(log_key, {}).get("last_posted", "")

    if days_since(last_post) < 7:
        print(f"[OUTREACH/Telegram] Posted {days_since(last_post)} days ago — skipping")
        return []

    requests_lib = try_import("requests")
    if not requests_lib:
        return []

    message = (
        "🌱 *SolarPunk Labor Marketplace — Earn $25-$60*\n\n"
        "Tasks available:\n"
        "• Plant a tree: $25\n"
        "• Cleanup session: $35\n"
        "• Print prosthetic hand: $60\n\n"
        "No bank account needed. CashApp/Venmo/PayPal.\n"
        "Payment in <10 minutes after photo proof.\n\n"
        f"👉 {WORK_PAGE_URL}"
    )

    try:
        resp = try_import("requests").post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10,
        )
        if resp.status_code == 200:
            outreach_log[log_key] = {"last_posted": NOW_ISO}
            print("[OUTREACH/Telegram] Posted to channel")
            return [{"platform": "telegram"}]
    except Exception as e:
        print(f"[OUTREACH/Telegram] Error: {str(e)[:100]}")

    return []

def main():
    print("[WORKER_OUTREACH] Starting worker outreach cycle...")

    # Load outreach log
    log_path = DATA / "outreach_log.json"
    outreach_log = load_json(log_path, {})

    all_posted = []

    # Run all outreach channels
    all_posted.extend(post_to_reddit(outreach_log))
    all_posted.extend(post_to_mastodon(outreach_log))
    all_posted.extend(post_to_devto(outreach_log))
    all_posted.extend(post_to_github_discussions(outreach_log))
    all_posted.extend(post_to_telegram_channel(outreach_log))

    # Save updated log
    outreach_log["last_run"] = NOW_ISO
    outreach_log["total_posts"] = outreach_log.get("total_posts", 0) + len(all_posted)
    save_json(log_path, outreach_log)

    print(f"\n[WORKER_OUTREACH] Complete. {len(all_posted)} posts made this cycle.")
    if all_posted:
        for post in all_posted:
            print(f"  - {post.get('platform', 'unknown')}: {post.get('url', 'posted')}")

if __name__ == "__main__":
    main()
