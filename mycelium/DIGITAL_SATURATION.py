#!/usr/bin/env python3
"""
DIGITAL_SATURATION -- Every digital task IS code. Stop preparing. Start executing.

Philosophy: Every channel that CAN be reached by code WILL be reached by code.
Measures and maximizes digital presence across every available channel.

Writes:
  - data/digital_saturation_state.json  (full state with per-channel scores)
  - data/saturation_gaps.json           (what's missing, what to generate next)
  - docs/saturation.html                (dashboard with per-channel bar charts)
"""
import json
import time
import re
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

BASE_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
REPO_URL = "https://github.com/meekotharaccoon-cell/meeko-nerve-center"

# ── targets ─────────────────────────────────────────────────────
TARGETS = {
    "github_pages":      100,   # HTML pages
    "github_discussions": 10,   # discussion posts
    "github_releases":     5,   # releases
    "rss_feed":           20,   # RSS entries
    "email_templates":    20,   # email templates
    "social_queue":       50,   # social posts
    "product_listings":    1,   # ratio: listed / total (100%)
    "sitemap_urls":        1,   # ratio: indexed / total (100%)
}

# ── helpers ─────────────────────────────────────────────────────

def _load_json(path, default=None):
    """Load JSON file safely with UTF-8 encoding."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _count_html_pages():
    """Count all .html files under docs/."""
    return list(DOCS.rglob("*.html"))


def _count_products():
    """Count products in product_registry.json."""
    reg = _load_json(DATA / "product_registry.json")
    products = reg.get("products", {})
    total = len(products)
    listed = sum(1 for p in products.values()
                 if p.get("kofi_url") or p.get("gumroad_url") or p.get("download_url"))
    return total, listed


def _count_discussions():
    """Count discussion drafts."""
    # Check discussions_publisher_state for posted count
    pub_state = _load_json(DATA / "discussions_publisher_state.json")
    posted = len(pub_state.get("posted", []))
    # Check discussion_drafts for total drafted
    drafts = _load_json(DATA / "discussion_drafts.json")
    draft_list = drafts.get("drafts", [])
    # Also check growth_flywheel_content for github_discussions
    flywheel = _load_json(DATA / "growth_flywheel_content.json")
    gh_discussions = flywheel.get("github_discussions", [])
    return posted, len(draft_list) + len(gh_discussions)


def _count_releases():
    """Count GitHub releases."""
    state = _load_json(DATA / "release_deployer_state.json")
    deployed = state.get("deployed", {})
    return len(deployed), state.get("total_assets_uploaded", 0)


def _count_rss_entries():
    """Count <item> elements in feed.xml."""
    feed_path = DOCS / "feed.xml"
    if not feed_path.exists():
        return 0
    content = feed_path.read_text(encoding="utf-8")
    return len(re.findall(r"<item>", content, re.IGNORECASE))


def _count_sitemap_urls():
    """Count <url> elements in sitemap.xml."""
    sitemap = DOCS / "sitemap.xml"
    if not sitemap.exists():
        return 0
    content = sitemap.read_text(encoding="utf-8")
    return len(re.findall(r"<url>", content, re.IGNORECASE))


def _count_email_templates():
    """Count templates in email_templates.json."""
    data = _load_json(DATA / "email_templates.json")
    return len(data.get("templates", []))


def _count_social_posts():
    """Count posts in social_queue.json."""
    data = _load_json(DATA / "social_queue.json")
    posts = data.get("posts", [])
    # Filter out separator/header lines that aren't real posts
    real = [p for p in posts if len(p.get("text", "")) > 20
            and not p["text"].startswith("===")
            and not p["text"].startswith("---")]
    return len(real), len(posts)


def _count_content_pieces():
    """Count all content artifacts ready to distribute."""
    pieces = 0
    # Content from growth_flywheel_content
    flywheel = _load_json(DATA / "growth_flywheel_content.json")
    for key in ("github_discussions", "twitter_threads", "reddit_posts",
                "linkedin_posts", "newsletter_content"):
        val = flywheel.get(key, [])
        if isinstance(val, list):
            pieces += len(val)
        elif isinstance(val, dict):
            pieces += len(val)
    # Article drafts
    articles = _load_json(DATA / "article_drafts.json")
    pieces += len(articles.get("articles", articles.get("drafts", [])))
    # Amplification posts
    amp = _load_json(DATA / "amplification_posts.json")
    pieces += len(amp.get("posts", []))
    # Virality posts
    vir = _load_json(DATA / "virality_posts.json")
    pieces += len(vir.get("posts", []))
    return pieces


def _count_kofi_ready():
    """Count Ko-fi ready listings."""
    data = _load_json(DATA / "kofi_ready_listings.json")
    listings = data.get("listings", {})
    return len(listings)


# ── cross-link density ──────────────────────────────────────────

def _scan_internal_links():
    """Scan all HTML pages for internal links. Return per-page link counts."""
    pages = _count_html_pages()
    link_map = {}
    all_filenames = set()
    for p in pages:
        rel = p.relative_to(DOCS).as_posix()
        all_filenames.add(rel)

    for p in pages:
        rel = p.relative_to(DOCS).as_posix()
        try:
            html = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            html = ""
        # Find href links to internal pages
        hrefs = re.findall(r'href=["\']([^"\'#]+)', html)
        internal = set()
        for h in hrefs:
            # Strip base URL prefix
            cleaned = h.replace(BASE_URL + "/", "").replace(BASE_URL, "")
            # Strip leading slash
            cleaned = cleaned.lstrip("/")
            # Skip external links and anchors
            if cleaned.startswith("http") or cleaned.startswith("mailto:"):
                continue
            # Normalize
            if cleaned and not cleaned.startswith("#"):
                internal.add(cleaned)
        link_map[rel] = {
            "internal_links": len(internal),
            "links": sorted(internal)[:10],  # sample
        }
    return link_map


# ── channel scoring ─────────────────────────────────────────────

def _score(count, target):
    """Compute saturation score 0-100."""
    if target <= 0:
        return 100
    return min(100, round((count / target) * 100))


def _ratio_score(numerator, denominator):
    """Score for ratio-based channels (listed/total)."""
    if denominator <= 0:
        return 100
    return min(100, round((numerator / denominator) * 100))


# ── gap generation ──────────────────────────────────────────────

TOPIC_SEEDS = [
    "autonomous-ai-architecture", "self-healing-systems", "bio-inspired-computing",
    "mutual-aid-technology", "zero-cost-infrastructure", "ethical-ai-design",
    "revenue-routing-patterns", "digital-organism-patterns", "mycelium-networks",
    "solarpunk-philosophy", "engine-composition", "fractal-replication",
    "immune-system-patterns", "knowledge-graph-design", "signal-chain-architecture",
    "swarm-intelligence", "digital-commons", "cooperative-ai", "resilient-systems",
    "post-capitalist-tech", "decentralized-automation", "proof-of-work-transparency",
    "ai-for-humanitarian-aid", "open-source-revenue", "template-economy",
    "growth-flywheel-mechanics", "content-saturation-strategy", "seo-for-autonomous-systems",
    "github-pages-at-scale", "community-driven-ai", "digital-sovereignty",
    "ai-product-generation", "autonomous-deployment", "self-writing-code",
    "crisis-response-automation", "knowledge-distillation", "resource-allocation-ai",
    "narrative-generation", "proof-ledger-design", "observatory-patterns",
]

DISCUSSION_SEEDS = [
    "What should the SolarPunk system build next?",
    "How do you verify an AI system is truly autonomous?",
    "Best practices for routing AI revenue to mutual aid",
    "Zero-cost infrastructure: what's possible in 2026?",
    "Should autonomous systems have ethics hardcoded?",
    "Open source AI: competition or cooperation?",
    "The role of transparency in AI trust",
    "Scaling digital products without paid APIs",
    "Community feedback: which product helped most?",
    "Future of bio-inspired software architecture",
    "How SolarPunk self-heals: immune system patterns",
    "Discussion: mycelium network as software metaphor",
]

SOCIAL_TEMPLATES = [
    "SolarPunk: {n} engines running autonomously. $0 infrastructure. 99% to mutual aid. {url}",
    "Built by AI, funded by community, routed to Gaza. {n} products ready. {url}/store.html",
    "The system that writes itself. {n} engines. Every dollar to PCRF, IRC, MSF. {url}",
    "AI doesn't care about Palestine. I do. So I hardcoded it. {url}/proof.html",
    "Zero APIs. Zero secrets. {n} engines. Full source code. {url}",
    "What happens when an AI runs a business for mutual aid? {n} products. $0 cost. {url}",
    "Every 6 hours this system wakes up and builds something. {n} engines and counting. {url}",
    "Digital products built by autonomous AI. $1 each. 99% to humanitarian relief. {url}/store.html",
    "Open source autonomous system: {n} engines, 11 products, 0 paid dependencies. {url}",
    "The architecture of solidarity: how code routes money to people who need it. {url}/proof.html",
]


def _generate_page_topics(current_count, target):
    """Generate topic slugs for missing pages."""
    needed = max(0, target - current_count)
    if needed == 0:
        return []
    topics = []
    for seed in TOPIC_SEEDS:
        if len(topics) >= needed:
            break
        slug = seed
        # Check if page already exists
        if not (DOCS / f"{slug}.html").exists() and not (DOCS / slug / "index.html").exists():
            topics.append({
                "slug": slug,
                "title": slug.replace("-", " ").title(),
                "target_file": f"docs/{slug}.html",
                "priority": "medium",
            })
    return topics


def _generate_discussion_topics(current_count, target):
    """Generate discussion topics to fill gaps."""
    needed = max(0, target - current_count)
    if needed == 0:
        return []
    return [{"title": t, "category": "General", "status": "draft"}
            for t in DISCUSSION_SEEDS[:needed]]


def _generate_social_posts(current_count, target):
    """Generate social post variants to fill gaps."""
    needed = max(0, target - current_count)
    if needed == 0:
        return []
    posts = []
    for tmpl in SOCIAL_TEMPLATES[:needed]:
        posts.append({
            "text": tmpl.format(n="300+", url=BASE_URL),
            "status": "generated",
            "source": "DIGITAL_SATURATION",
        })
    return posts


def _generate_rss_topics(current_count, target):
    """Suggest RSS feed items to add."""
    needed = max(0, target - current_count)
    if needed == 0:
        return []
    suggestions = [
        "Weekly system health update",
        "New engine spotlight: DIGITAL_SATURATION",
        "Community milestone: first discussion reply",
        "Architecture deep dive: signal chains",
        "How the immune system protects SolarPunk",
        "Product update: bundles now available",
        "Transparency report: where the money goes",
        "Open source milestone: full source published",
        "Engine count milestone: 300+",
        "New landing pages deployed",
    ]
    return [{"title": s, "status": "suggested"} for s in suggestions[:needed]]


# ── HTML dashboard ──────────────────────────────────────────────

def _build_dashboard(channels, composite_score, total_artifacts, link_density, gaps):
    """Build saturation.html dashboard."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    bars_html = ""
    for ch in channels:
        name = ch["name"]
        score = ch["score"]
        count = ch["count"]
        target = ch["target"]
        # Color gradient: red < 30, orange < 60, yellow < 80, green >= 80
        if score >= 80:
            color = "#22c55e"
        elif score >= 60:
            color = "#eab308"
        elif score >= 30:
            color = "#f97316"
        else:
            color = "#ef4444"
        bars_html += f"""
    <div style="margin-bottom:18px;">
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
        <span style="font-weight:600;color:#e2e8f0;">{name}</span>
        <span style="color:#94a3b8;">{count}/{target} &mdash; {score}%</span>
      </div>
      <div style="background:#1e293b;border-radius:8px;height:28px;overflow:hidden;">
        <div style="width:{score}%;height:100%;background:{color};border-radius:8px;transition:width 0.5s;"></div>
      </div>
    </div>"""

    # Under-linked pages
    under_linked = sorted(
        [(k, v["internal_links"]) for k, v in link_density.items() if v["internal_links"] < 5],
        key=lambda x: x[1]
    )[:20]
    links_rows = ""
    for page, count in under_linked:
        links_rows += f"<tr><td style='padding:6px 12px;color:#e2e8f0;'>{page}</td><td style='padding:6px 12px;color:#f97316;text-align:center;'>{count}</td></tr>\n"

    # Gap summary
    gap_items = ""
    for g in gaps:
        gap_items += f"<li style='margin-bottom:6px;'><strong>{g['channel']}</strong>: {g['action']} ({g['needed']} needed)</li>\n"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Digital Saturation Dashboard -- SolarPunk</title>
  <meta name="description" content="SolarPunk digital presence saturation score: {composite_score}/100 across all channels.">
  <meta property="og:title" content="Digital Saturation -- SolarPunk">
  <meta property="og:description" content="Digital presence: {composite_score}/100. {total_artifacts} total artifacts across {len(channels)} channels.">
  <meta property="og:url" content="{BASE_URL}/saturation.html">
  <style>
    *{{margin:0;padding:0;box-sizing:border-box;}}
    body{{background:#0f172a;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;padding:24px;max-width:960px;margin:0 auto;}}
    h1{{font-size:2rem;margin-bottom:8px;color:#22c55e;}}
    h2{{font-size:1.4rem;margin:32px 0 16px;color:#38bdf8;}}
    .score-ring{{display:inline-flex;align-items:center;justify-content:center;width:140px;height:140px;border-radius:50%;border:6px solid {("#22c55e" if composite_score >= 80 else "#eab308" if composite_score >= 60 else "#f97316" if composite_score >= 30 else "#ef4444")};margin:20px auto;font-size:3rem;font-weight:700;color:#fff;}}
    .meta{{color:#94a3b8;margin-bottom:24px;font-size:0.9rem;}}
    table{{width:100%;border-collapse:collapse;margin:12px 0;}}
    th{{text-align:left;padding:8px 12px;background:#1e293b;color:#38bdf8;font-weight:600;}}
    tr:nth-child(even){{background:#1e293b44;}}
    a{{color:#38bdf8;text-decoration:none;}}
    a:hover{{text-decoration:underline;}}
    .nav{{margin-top:32px;padding-top:16px;border-top:1px solid #334155;}}
    .nav a{{margin-right:16px;}}
    .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin:20px 0;}}
    .stat{{background:#1e293b;padding:16px;border-radius:12px;text-align:center;}}
    .stat .val{{font-size:2rem;font-weight:700;color:#22c55e;}}
    .stat .lbl{{color:#94a3b8;font-size:0.85rem;margin-top:4px;}}
  </style>
</head>
<body>
  <h1>Digital Saturation</h1>
  <p class="meta">Every channel that CAN be reached by code WILL be reached by code. Updated {now}.</p>

  <div style="text-align:center;">
    <div class="score-ring">{composite_score}</div>
    <div style="color:#94a3b8;font-size:1.1rem;">Composite Score / 100</div>
  </div>

  <div class="stats">
    <div class="stat"><div class="val">{total_artifacts}</div><div class="lbl">Total Artifacts</div></div>
    <div class="stat"><div class="val">{len(channels)}</div><div class="lbl">Channels Measured</div></div>
    <div class="stat"><div class="val">{sum(1 for c in channels if c['score'] >= 100)}</div><div class="lbl">Channels at 100%</div></div>
    <div class="stat"><div class="val">{min(channels, key=lambda c: c['score'])['score']}%</div><div class="lbl">Lowest Channel</div></div>
  </div>

  <h2>Channel Saturation</h2>
  {bars_html}

  <h2>Gaps to Fill</h2>
  <ul style="list-style:none;padding:0;">
    {gap_items if gap_items else '<li style="color:#94a3b8;">All channels at target. Full saturation.</li>'}
  </ul>

  <h2>Cross-Link Density (Under-linked Pages)</h2>
  <p class="meta">Target: every page links to at least 5 other internal pages.</p>
  <table>
    <tr><th>Page</th><th style="text-align:center;">Internal Links</th></tr>
    {links_rows if links_rows else '<tr><td colspan="2" style="padding:12px;color:#94a3b8;">All pages meet link target.</td></tr>'}
  </table>

  <div class="nav">
    <a href="index.html">Home</a>
    <a href="dashboard.html">Dashboard</a>
    <a href="store.html">Store</a>
    <a href="status.html">Status</a>
    <a href="proof.html">Proof</a>
    <a href="evolution.html">Evolution</a>
  </div>

  <p style="margin-top:24px;color:#475569;font-size:0.8rem;">
    Generated by DIGITAL_SATURATION engine. Source:
    <a href="{REPO_URL}">{REPO_URL}</a>
  </p>
</body>
</html>"""
    return html


# ── main ────────────────────────────────────────────────────────

def run():
    t0 = time.time()
    now = datetime.now(timezone.utc).isoformat()

    # ── 1. INVENTORY ────────────────────────────────────────────
    html_pages = _count_html_pages()
    html_count = len(html_pages)

    total_products, listed_products = _count_products()

    content_pieces = _count_content_pieces()

    email_count = _count_email_templates()

    kofi_ready = _count_kofi_ready()

    discussions_posted, discussions_drafted = _count_discussions()

    releases_deployed, releases_assets = _count_releases()

    rss_count = _count_rss_entries()

    sitemap_count = _count_sitemap_urls()

    social_real, social_total = _count_social_posts()

    # ── 2. CHANNEL ANALYSIS ─────────────────────────────────────
    channels = [
        {
            "id": "github_pages",
            "name": "GitHub Pages",
            "count": html_count,
            "target": TARGETS["github_pages"],
            "score": _score(html_count, TARGETS["github_pages"]),
        },
        {
            "id": "github_discussions",
            "name": "GitHub Discussions",
            "count": discussions_posted + discussions_drafted,
            "target": TARGETS["github_discussions"],
            "score": _score(discussions_posted + discussions_drafted,
                            TARGETS["github_discussions"]),
        },
        {
            "id": "github_releases",
            "name": "GitHub Releases",
            "count": releases_deployed,
            "target": TARGETS["github_releases"],
            "score": _score(releases_deployed, TARGETS["github_releases"]),
        },
        {
            "id": "rss_feed",
            "name": "RSS Feed",
            "count": rss_count,
            "target": TARGETS["rss_feed"],
            "score": _score(rss_count, TARGETS["rss_feed"]),
        },
        {
            "id": "email_templates",
            "name": "Email Templates",
            "count": email_count,
            "target": TARGETS["email_templates"],
            "score": _score(email_count, TARGETS["email_templates"]),
        },
        {
            "id": "social_queue",
            "name": "Social Queue",
            "count": social_real,
            "target": TARGETS["social_queue"],
            "score": _score(social_real, TARGETS["social_queue"]),
        },
        {
            "id": "product_listings",
            "name": "Product Listings",
            "count": listed_products,
            "target": total_products,
            "score": _ratio_score(listed_products, total_products),
        },
        {
            "id": "sitemap_urls",
            "name": "Sitemap Coverage",
            "count": sitemap_count,
            "target": html_count,
            "score": _ratio_score(sitemap_count, html_count),
        },
    ]

    # ── 3. GENERATE GAPS ────────────────────────────────────────
    gaps = []
    gap_details = {}

    # Pages
    if html_count < TARGETS["github_pages"]:
        needed = TARGETS["github_pages"] - html_count
        topics = _generate_page_topics(html_count, TARGETS["github_pages"])
        gaps.append({"channel": "GitHub Pages", "action": f"Generate {needed} more topic pages", "needed": needed})
        gap_details["pages_to_generate"] = topics

    # Discussions
    disc_total = discussions_posted + discussions_drafted
    if disc_total < TARGETS["github_discussions"]:
        needed = TARGETS["github_discussions"] - disc_total
        topics = _generate_discussion_topics(disc_total, TARGETS["github_discussions"])
        gaps.append({"channel": "GitHub Discussions", "action": f"Draft {needed} more discussion topics", "needed": needed})
        gap_details["discussions_to_draft"] = topics

    # Releases
    if releases_deployed < TARGETS["github_releases"]:
        needed = TARGETS["github_releases"] - releases_deployed
        gaps.append({"channel": "GitHub Releases", "action": f"Deploy {needed} more releases", "needed": needed})
        gap_details["releases_needed"] = needed

    # RSS
    if rss_count < TARGETS["rss_feed"]:
        needed = TARGETS["rss_feed"] - rss_count
        rss_topics = _generate_rss_topics(rss_count, TARGETS["rss_feed"])
        gaps.append({"channel": "RSS Feed", "action": f"Add {needed} more feed items", "needed": needed})
        gap_details["rss_items_to_add"] = rss_topics

    # Email
    if email_count < TARGETS["email_templates"]:
        needed = TARGETS["email_templates"] - email_count
        gaps.append({"channel": "Email Templates", "action": f"Generate {needed} more email templates", "needed": needed})
        gap_details["emails_needed"] = needed

    # Social
    if social_real < TARGETS["social_queue"]:
        needed = TARGETS["social_queue"] - social_real
        new_posts = _generate_social_posts(social_real, TARGETS["social_queue"])
        gaps.append({"channel": "Social Queue", "action": f"Generate {needed} more real posts", "needed": needed})
        gap_details["social_posts_to_generate"] = new_posts

    # Product listings coverage
    unlisted = total_products - listed_products
    if unlisted > 0:
        gaps.append({"channel": "Product Listings", "action": f"List {unlisted} unlisted products on Ko-fi/Gumroad", "needed": unlisted})
        gap_details["products_to_list"] = unlisted

    # Sitemap coverage
    sitemap_diff = html_count - sitemap_count
    if sitemap_diff > 0:
        gaps.append({"channel": "Sitemap Coverage", "action": f"Add {sitemap_diff} missing URLs to sitemap", "needed": sitemap_diff})
        gap_details["sitemap_urls_missing"] = sitemap_diff

    # ── 4. CROSS-LINK DENSITY ───────────────────────────────────
    link_density = _scan_internal_links()
    under_linked = {k: v for k, v in link_density.items() if v["internal_links"] < 5}
    avg_links = round(sum(v["internal_links"] for v in link_density.values()) / max(len(link_density), 1), 1)

    # ── 5. COMPOSITE SCORE ──────────────────────────────────────
    if channels:
        composite_score = round(sum(c["score"] for c in channels) / len(channels))
    else:
        composite_score = 0

    total_artifacts = (html_count + total_products + content_pieces +
                       email_count + social_total + rss_count +
                       discussions_drafted + kofi_ready)

    # Sort channels by score ascending (worst first) for gap identification
    sorted_channels = sorted(channels, key=lambda c: c["score"])
    top_gap = sorted_channels[0] if sorted_channels else {"name": "none", "score": 100}

    # ── 6. WRITE STATE FILES ────────────────────────────────────

    # data/digital_saturation_state.json
    state = {
        "engine": "DIGITAL_SATURATION",
        "philosophy": "Every channel that CAN be reached by code WILL be reached by code.",
        "timestamp": now,
        "composite_score": composite_score,
        "total_artifacts": total_artifacts,
        "total_channels": len(channels),
        "channels_at_100": sum(1 for c in channels if c["score"] >= 100),
        "top_gap": {"channel": top_gap["name"], "score": top_gap["score"]},
        "inventory": {
            "html_pages": html_count,
            "products_total": total_products,
            "products_listed": listed_products,
            "content_pieces": content_pieces,
            "email_templates": email_count,
            "kofi_ready": kofi_ready,
            "discussions_posted": discussions_posted,
            "discussions_drafted": discussions_drafted,
            "releases_deployed": releases_deployed,
            "rss_entries": rss_count,
            "sitemap_urls": sitemap_count,
            "social_posts_real": social_real,
            "social_posts_total": social_total,
        },
        "channels": channels,
        "cross_link_density": {
            "average_internal_links": avg_links,
            "under_linked_count": len(under_linked),
            "target_links_per_page": 5,
        },
        "elapsed_sec": round(time.time() - t0, 2),
    }
    (DATA / "digital_saturation_state.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8")

    # data/saturation_gaps.json
    gap_state = {
        "engine": "DIGITAL_SATURATION",
        "timestamp": now,
        "composite_score": composite_score,
        "gaps": gaps,
        "gap_details": gap_details,
        "under_linked_pages": [
            {"page": k, "links": v["internal_links"]}
            for k, v in sorted(under_linked.items(), key=lambda x: x[1]["internal_links"])
        ][:30],
        "next_actions": [g["action"] for g in gaps[:5]],
    }
    (DATA / "saturation_gaps.json").write_text(
        json.dumps(gap_state, indent=2), encoding="utf-8")

    # docs/saturation.html
    dashboard_html = _build_dashboard(channels, composite_score, total_artifacts,
                                       link_density, gaps)
    (DOCS / "saturation.html").write_text(dashboard_html, encoding="utf-8")

    # ── REPORT ──────────────────────────────────────────────────
    print(f"DIGITAL SATURATION: {composite_score}/100. "
          f"{len(channels)} channels. {total_artifacts} total artifacts. "
          f"Top gap: {top_gap['name']} at {top_gap['score']}%")
    print(f"  Pages: {html_count}/{TARGETS['github_pages']} | "
          f"Discussions: {discussions_posted + discussions_drafted}/{TARGETS['github_discussions']} | "
          f"Releases: {releases_deployed}/{TARGETS['github_releases']} | "
          f"RSS: {rss_count}/{TARGETS['rss_feed']}")
    print(f"  Email: {email_count}/{TARGETS['email_templates']} | "
          f"Social: {social_real}/{TARGETS['social_queue']} | "
          f"Products listed: {listed_products}/{total_products} | "
          f"Sitemap: {sitemap_count}/{html_count}")
    print(f"  Cross-links avg: {avg_links}/page | Under-linked: {len(under_linked)} pages")
    print(f"  Wrote: data/digital_saturation_state.json, data/saturation_gaps.json, docs/saturation.html")
    print(f"  Elapsed: {round(time.time() - t0, 2)}s")


if __name__ == "__main__":
    run()
