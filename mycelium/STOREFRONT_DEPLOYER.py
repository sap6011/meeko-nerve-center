# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
STOREFRONT_DEPLOYER.py -- The Bridge Between Products and Buyers.

Takes EVERY product in the registry and generates READY-TO-PASTE listings
for every platform we sell on:

    1. Ko-fi Shop  (PRIMARY -- free, no approval, already live)
    2. Gumroad     (SECONDARY -- when account is active)
    3. GitHub Releases (TERTIARY -- already have GITHUB_RELEASE_DEPLOYER)

For each product, this engine generates:
    - Title (max 60 chars)
    - Description (max 500 chars, value prop + what's included)
    - Price
    - Tags/categories
    - Download pointer (the .md file in products/)

Then creates a DEPLOYMENT CHECKLIST:
    - Step-by-step Ko-fi instructions with URLs
    - Copy-paste ready text blocks
    - Image suggestions from art_catalog.json

Tracks deployment status per product per platform.
Generates docs/store_deploy.html dashboard.

Zero secrets. Zero paid APIs. Pure bridge-building.
"""
import json
import time
import pathlib
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)
PRODUCTS_DIR = Path("products")
STATE_FILE = DATA / "storefront_deployer_state.json"

KOFI_SHOP_URL = "https://ko-fi.com/meekotharaccoon/shop"
KOFI_MANAGE_URL = "https://ko-fi.com/manage/shop"
KOFI_PROFILE_URL = "https://ko-fi.com/meekotharaccoon"
GITHUB_REPO = "meekotharaccoon-cell/meeko-nerve-center"
GITHUB_PAGES = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"

# ---------------------------------------------------------------------------
# Platform definitions
# ---------------------------------------------------------------------------
PLATFORMS = {
    "kofi": {
        "name": "Ko-fi Shop",
        "priority": 1,
        "status": "live",
        "url": KOFI_SHOP_URL,
        "manage_url": KOFI_MANAGE_URL,
        "fee_pct": 0,
        "notes": "Free, no approval needed, instant listing, already active",
    },
    "gumroad": {
        "name": "Gumroad",
        "priority": 2,
        "status": "pending",
        "url": "https://meekotharacoon.gumroad.com",
        "manage_url": "https://app.gumroad.com/products",
        "fee_pct": 10,
        "notes": "10% platform fee. Account needs activation.",
    },
    "github": {
        "name": "GitHub Releases",
        "priority": 3,
        "status": "live",
        "url": "https://github.com/%s/releases" % GITHUB_REPO,
        "manage_url": "https://github.com/%s/releases/new" % GITHUB_REPO,
        "fee_pct": 0,
        "notes": "Free distribution via releases. No payment -- link to Ko-fi for purchase.",
    },
}

# ---------------------------------------------------------------------------
# Tag mapping for products
# ---------------------------------------------------------------------------
CATEGORY_MAP = {
    "bundle": "Bundle",
    "guide": "Guide",
    "art": "Art Print",
    "template": "Template Pack",
    "playbook": "Playbook",
    "encyclopedia": "Reference",
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _load(fname, fallback=None):
    f = DATA / fname
    if f.exists():
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            return d if isinstance(d, (dict, list)) else (fallback or {})
        except Exception:
            pass
    return fallback if fallback is not None else {}


def _save(fname, data):
    (DATA / fname).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _ts():
    return datetime.now(timezone.utc).isoformat()


def _truncate(text, max_len):
    """Truncate text to max_len, ending at a word boundary."""
    if len(text) <= max_len:
        return text
    cut = text[:max_len - 3]
    last_space = cut.rfind(" ")
    if last_space > max_len // 2:
        cut = cut[:last_space]
    return cut + "..."


def _classify_product(product_id, product):
    """Determine the category of a product."""
    pid = product_id.lower()
    title = (product.get("title") or "").lower()
    if product.get("type") == "bundle" or "bundle" in pid:
        return "bundle"
    if "encyclopedia" in pid or "encyclopedia" in title:
        return "encyclopedia"
    if "playbook" in pid or "playbook" in title:
        return "playbook"
    if "art" in pid or "gaza" in pid or "rose" in pid:
        return "art"
    if "template" in pid or "template" in title:
        return "template"
    return "guide"


def _get_price(product_id, product, first_dollar_plan):
    """Get price from first_dollar_plan scored_products or product_registry."""
    # Check first_dollar_plan scored products for authoritative price
    for sp in first_dollar_plan.get("scored_products", []):
        if sp.get("id") == product_id:
            return sp.get("price", product.get("price", 1.0))
    return product.get("price", 1.0)


# ---------------------------------------------------------------------------
# Listing generators -- one per platform
# ---------------------------------------------------------------------------

def _generate_kofi_listing(product_id, product, category, price, art_catalog):
    """Generate a ready-to-paste Ko-fi shop listing."""
    title = product.get("title", product_id)
    title_short = _truncate(title, 60)

    word_count = product.get("word_count", 0)
    sections = product.get("sections", 0)
    components = product.get("components", [])
    savings_pct = product.get("savings_pct", 0)
    file_path = product.get("file_path", "")

    # Build description lines
    desc_lines = []
    desc_lines.append("%s -- from the SolarPunk autonomous AI system." % title)
    desc_lines.append("")

    if category == "bundle" and components:
        desc_lines.append("BUNDLE INCLUDES:")
        for comp in components[:6]:
            desc_lines.append("- %s" % comp.replace("_", " ").title())
        if savings_pct > 0:
            desc_lines.append("Save %d%% vs buying separately." % savings_pct)
        desc_lines.append("")

    desc_lines.append("WHAT YOU GET:")
    if word_count > 0:
        desc_lines.append("- %s words of practical, battle-tested content" % f"{word_count:,}")
    if sections > 0:
        desc_lines.append("- %d sections with real implementation patterns" % sections)
    desc_lines.append("- Instant digital download (.md format)")
    desc_lines.append("- Works with any text editor or Markdown viewer")
    desc_lines.append("")
    desc_lines.append("Built by a 300-engine autonomous AI system.")
    desc_lines.append("99% of revenue goes to mutual aid (PCRF, IRC, MSF).")

    description = "\n".join(desc_lines)
    description = _truncate(description, 500)

    # Tags
    base_tags = ["solarpunk", "ai", "automation"]
    if category == "bundle":
        base_tags.extend(["bundle", "value-pack"])
    elif category == "guide":
        base_tags.extend(["python", "tutorial", "open-source"])
    elif category == "encyclopedia":
        base_tags.extend(["reference", "documentation"])
    elif category == "playbook":
        base_tags.extend(["revenue", "ethics", "business"])

    # Image suggestion
    image_suggestion = _get_image_suggestion(product_id, category, art_catalog)

    return {
        "platform": "kofi",
        "title": title_short,
        "description": description,
        "price": price,
        "price_display": "$%.2f" % price,
        "tags": base_tags[:5],
        "file_to_upload": file_path,
        "image_suggestion": image_suggestion,
        "paste_ready": {
            "title_field": title_short,
            "description_field": description,
            "price_field": "%.2f" % price,
            "tags_field": ", ".join(base_tags[:5]),
        },
    }


def _generate_gumroad_listing(product_id, product, category, price, art_catalog):
    """Generate a ready-to-paste Gumroad listing."""
    title = product.get("title", product_id)
    title_short = _truncate(title, 60)

    word_count = product.get("word_count", 0)
    sections = product.get("sections", 0)
    components = product.get("components", [])
    savings_pct = product.get("savings_pct", 0)
    file_path = product.get("file_path", "")

    # Short description for Gumroad card
    short_desc = "%s from a 300-engine autonomous AI system." % (
        CATEGORY_MAP.get(category, "Digital product")
    )
    if word_count > 0:
        short_desc += " %s words, %d sections." % (f"{word_count:,}", sections)

    # Full Gumroad description (Markdown)
    full_lines = []
    full_lines.append("# %s" % title)
    full_lines.append("")
    full_lines.append("From a real, running autonomous AI system with 300+ engines,")
    full_lines.append("4,700+ data wires, and zero paid API dependencies.")
    full_lines.append("")

    if category == "bundle" and components:
        full_lines.append("## Bundle Includes")
        for comp in components[:6]:
            full_lines.append("- **%s**" % comp.replace("_", " ").title())
        if savings_pct > 0:
            full_lines.append("")
            full_lines.append("**Save %d%%** vs buying separately." % savings_pct)
        full_lines.append("")

    full_lines.append("## What You Get")
    if word_count > 0:
        full_lines.append("- %s words of practical content" % f"{word_count:,}")
    if sections > 0:
        full_lines.append("- %d detailed sections" % sections)
    full_lines.append("- Instant download (.md format)")
    full_lines.append("- Real code patterns from production")
    full_lines.append("")
    full_lines.append("## Ethics")
    full_lines.append("99% of revenue goes to mutual aid organizations:")
    full_lines.append("PCRF (60%), IRC (15%), MSF (10%), UNICEF (10%), Direct Relief (5%)")
    full_lines.append("")
    full_lines.append("Built by SolarPunk. The system that builds itself.")

    full_desc = "\n".join(full_lines)

    # Tags
    base_tags = ["solarpunk", "ai", "automation", "python", "open-source"]
    slug = product_id

    image_suggestion = _get_image_suggestion(product_id, category, art_catalog)

    return {
        "platform": "gumroad",
        "title": title_short,
        "short_description": _truncate(short_desc, 160),
        "full_description": full_desc,
        "price": price,
        "price_display": "$%.2f" % price,
        "url_slug": slug,
        "tags": base_tags[:5],
        "file_to_upload": file_path,
        "image_suggestion": image_suggestion,
        "paste_ready": {
            "name_field": title_short,
            "price_field": "%.2f" % price,
            "short_desc_field": _truncate(short_desc, 160),
            "full_desc_field": full_desc,
            "url_slug_field": slug,
            "tags_field": ", ".join(base_tags[:5]),
        },
    }


def _generate_github_listing(product_id, product, category, price):
    """Generate GitHub release listing info."""
    title = product.get("title", product_id)
    title_short = _truncate(title, 60)
    file_path = product.get("file_path", "")
    download_url = product.get("download_url")

    release_body = []
    release_body.append("## %s" % title)
    release_body.append("")
    release_body.append("Digital product from the SolarPunk autonomous AI system.")
    release_body.append("")
    release_body.append("**Price:** $%.2f on [Ko-fi](%s)" % (price, KOFI_SHOP_URL))
    release_body.append("")
    release_body.append("99%% of revenue goes to mutual aid (PCRF, IRC, MSF, UNICEF, Direct Relief).")
    release_body.append("")
    release_body.append("---")
    release_body.append("*Built by SolarPunk -- 300+ engines, zero paid APIs.*")

    return {
        "platform": "github",
        "title": title_short,
        "release_tag": "product-%s" % product_id,
        "release_body": "\n".join(release_body),
        "file_to_upload": file_path,
        "existing_download_url": download_url,
        "buy_link": KOFI_SHOP_URL,
        "paste_ready": {
            "tag_field": "product-%s" % product_id,
            "title_field": title_short,
            "body_field": "\n".join(release_body),
        },
    }


def _get_image_suggestion(product_id, category, art_catalog):
    """Suggest cover image based on art catalog or category."""
    pieces = art_catalog.get("pieces", [])

    # Map specific products to art pieces
    art_map = {
        "solarpunk-starter": "white-doves",
        "local-ai-agent": "tatreez",
        "system-snapshot": "gaza-coastline",
        "bio-inspired-architecture": "olive-grove",
        "autonomous-system-guide": "star-of-hope",
        "ethical-ai-playbook": "night-garden",
        "engine-encyclopedia": "pomegranate",
    }

    suggested_id = art_map.get(product_id)
    if suggested_id:
        for piece in pieces:
            if piece.get("id") == suggested_id:
                return {
                    "source": "art_catalog",
                    "piece_id": piece["id"],
                    "piece_title": piece.get("title", ""),
                    "colors": piece.get("colors", []),
                    "suggestion": "Use %s art piece as cover image" % piece.get("title", suggested_id),
                }

    # Generic suggestion by category
    color_map = {
        "bundle": {"colors": ["#00ff88", "#0a0a0a"], "suggestion": "Green circuit/bundle aesthetic"},
        "guide": {"colors": ["#00cc6a", "#111111"], "suggestion": "SolarPunk green/terminal aesthetic"},
        "encyclopedia": {"colors": ["#ffd166", "#0a0a0a"], "suggestion": "Gold/dark reference book aesthetic"},
        "playbook": {"colors": ["#f59e0b", "#111111"], "suggestion": "Amber/dark strategy aesthetic"},
        "art": {"colors": ["#c41e3a", "#f8f4e8"], "suggestion": "Use the actual art piece as cover"},
    }
    fallback = color_map.get(category, {"colors": ["#00ff88", "#0a0a0a"], "suggestion": "SolarPunk green aesthetic"})
    return {
        "source": "category_default",
        "suggestion": fallback["suggestion"],
        "colors": fallback["colors"],
    }


# ---------------------------------------------------------------------------
# Deployment checklist generator
# ---------------------------------------------------------------------------

def _build_deployment_checklist(product_id, product, kofi_listing, gumroad_listing, github_listing):
    """Build step-by-step deployment checklist for a product."""
    title = product.get("title", product_id)
    file_path = product.get("file_path", "")
    download_url = product.get("download_url")
    price = kofi_listing["price"]

    steps = []

    # --- Ko-fi steps ---
    steps.append({
        "platform": "kofi",
        "step": 1,
        "action": "Open Ko-fi shop dashboard",
        "url": KOFI_MANAGE_URL,
        "detail": "Log in as meekotharaccoon. Navigate to Shop management.",
    })
    steps.append({
        "platform": "kofi",
        "step": 2,
        "action": "Click 'Add New Item' or '+ New Product'",
        "url": KOFI_MANAGE_URL,
        "detail": "Select 'Digital Item' as the product type.",
    })
    steps.append({
        "platform": "kofi",
        "step": 3,
        "action": "Paste title",
        "paste": kofi_listing["paste_ready"]["title_field"],
        "detail": "Paste into the Title field exactly as shown.",
    })
    steps.append({
        "platform": "kofi",
        "step": 4,
        "action": "Paste description",
        "paste": kofi_listing["paste_ready"]["description_field"],
        "detail": "Paste into Description. Includes PCRF disclosure.",
    })
    steps.append({
        "platform": "kofi",
        "step": 5,
        "action": "Set price to %s" % kofi_listing["price_display"],
        "paste": kofi_listing["paste_ready"]["price_field"],
        "detail": "Enter in the Price field.",
    })
    steps.append({
        "platform": "kofi",
        "step": 6,
        "action": "Upload the product file",
        "file": file_path,
        "fallback_url": download_url,
        "detail": "Upload '%s'. If not on disk, download from GitHub release." % file_path,
    })
    steps.append({
        "platform": "kofi",
        "step": 7,
        "action": "Add tags",
        "paste": kofi_listing["paste_ready"]["tags_field"],
        "detail": "Add each tag. Comma-separated.",
    })

    img = kofi_listing.get("image_suggestion", {})
    if img:
        steps.append({
            "platform": "kofi",
            "step": 8,
            "action": "Add cover image",
            "detail": "Image suggestion: %s (colors: %s)" % (
                img.get("suggestion", "SolarPunk green aesthetic"),
                ", ".join(img.get("colors", [])),
            ),
        })

    steps.append({
        "platform": "kofi",
        "step": 9,
        "action": "Click Publish",
        "url": KOFI_MANAGE_URL,
        "detail": "Product goes live immediately after publish.",
    })
    steps.append({
        "platform": "kofi",
        "step": 10,
        "action": "Verify listing is live",
        "url": KOFI_SHOP_URL,
        "detail": "Visit the public shop and confirm '%s' appears." % title,
    })

    # --- Gumroad steps ---
    steps.append({
        "platform": "gumroad",
        "step": 1,
        "action": "Open Gumroad product dashboard",
        "url": "https://app.gumroad.com/products",
        "detail": "Log in. If account is not active, skip Gumroad for now.",
    })
    steps.append({
        "platform": "gumroad",
        "step": 2,
        "action": "Click 'New Product'",
        "url": "https://app.gumroad.com/products/new",
        "detail": "Select 'Digital Product' type.",
    })
    steps.append({
        "platform": "gumroad",
        "step": 3,
        "action": "Paste product name",
        "paste": gumroad_listing["paste_ready"]["name_field"],
        "detail": "Paste into the Name field.",
    })
    steps.append({
        "platform": "gumroad",
        "step": 4,
        "action": "Set price to %s" % gumroad_listing["price_display"],
        "paste": gumroad_listing["paste_ready"]["price_field"],
        "detail": "Enter in Price field. Gumroad takes 10%% fee.",
    })
    steps.append({
        "platform": "gumroad",
        "step": 5,
        "action": "Set URL slug",
        "paste": gumroad_listing["paste_ready"]["url_slug_field"],
        "detail": "Custom URL will be: gumroad.com/l/%s" % gumroad_listing["url_slug"],
    })
    steps.append({
        "platform": "gumroad",
        "step": 6,
        "action": "Paste full description (Markdown)",
        "paste": gumroad_listing["paste_ready"]["full_desc_field"],
        "detail": "Paste into Description. Gumroad renders Markdown.",
    })
    steps.append({
        "platform": "gumroad",
        "step": 7,
        "action": "Upload product file and publish",
        "file": file_path,
        "detail": "Upload the .md file, then click Publish.",
    })

    # --- GitHub steps ---
    steps.append({
        "platform": "github",
        "step": 1,
        "action": "Create new GitHub release",
        "url": "https://github.com/%s/releases/new" % GITHUB_REPO,
        "detail": "Or use GITHUB_RELEASE_DEPLOYER.py to automate.",
    })
    steps.append({
        "platform": "github",
        "step": 2,
        "action": "Set tag: %s" % github_listing["paste_ready"]["tag_field"],
        "paste": github_listing["paste_ready"]["tag_field"],
        "detail": "Create new tag on publish.",
    })
    steps.append({
        "platform": "github",
        "step": 3,
        "action": "Set release title and body",
        "paste": github_listing["paste_ready"]["title_field"],
        "detail": "Paste title, then paste release body with Ko-fi buy link.",
    })
    steps.append({
        "platform": "github",
        "step": 4,
        "action": "Attach product file and publish",
        "file": file_path,
        "detail": "Upload .md file as release asset. Link to Ko-fi for payment.",
    })

    return steps


# ---------------------------------------------------------------------------
# State tracking
# ---------------------------------------------------------------------------

def _load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "engine": "STOREFRONT_DEPLOYER",
        "created_at": _ts(),
        "cycles": 0,
        "deployments": {},
    }


def _update_deployment_status(state, product_id, platform, status, url=None):
    """Update deployment status for a product on a platform."""
    if product_id not in state["deployments"]:
        state["deployments"][product_id] = {}
    state["deployments"][product_id][platform] = {
        "status": status,
        "url": url,
        "last_checked": _ts(),
    }


def _check_existing_deployments(product, state, product_id):
    """Check if product is already deployed based on existing URLs."""
    deployments = state.get("deployments", {}).get(product_id, {})

    # Check Ko-fi
    if product.get("kofi_url"):
        deployments["kofi"] = {
            "status": "live",
            "url": product["kofi_url"],
            "last_checked": _ts(),
        }
    elif "kofi" not in deployments:
        deployments["kofi"] = {"status": "not_listed", "url": None, "last_checked": _ts()}

    # Check Gumroad
    if product.get("gumroad_url"):
        deployments["gumroad"] = {
            "status": "live",
            "url": product["gumroad_url"],
            "last_checked": _ts(),
        }
    elif "gumroad" not in deployments:
        deployments["gumroad"] = {"status": "not_listed", "url": None, "last_checked": _ts()}

    # Check GitHub
    if product.get("download_url"):
        deployments["github"] = {
            "status": "live",
            "url": product["download_url"],
            "last_checked": _ts(),
        }
    elif "github" not in deployments:
        deployments["github"] = {"status": "not_listed", "url": None, "last_checked": _ts()}

    return deployments


# ---------------------------------------------------------------------------
# HTML dashboard generator
# ---------------------------------------------------------------------------

def _build_html(all_listings, state):
    """Generate docs/store_deploy.html -- the deployment dashboard."""
    now = _ts()[:16]
    total_products = len(all_listings)
    deployments = state.get("deployments", {})

    # Count statuses
    live_kofi = sum(1 for d in deployments.values() if d.get("kofi", {}).get("status") == "live")
    live_gumroad = sum(1 for d in deployments.values() if d.get("gumroad", {}).get("status") == "live")
    live_github = sum(1 for d in deployments.values() if d.get("github", {}).get("status") == "live")
    total_live = live_kofi + live_gumroad + live_github
    total_possible = total_products * 3

    # Product rows
    product_rows = ""
    for pid, listing_data in sorted(all_listings.items()):
        title = listing_data.get("title", pid)
        price = listing_data.get("price", 0)
        dep = deployments.get(pid, {})

        kofi_status = dep.get("kofi", {}).get("status", "not_listed")
        gumroad_status = dep.get("gumroad", {}).get("status", "not_listed")
        github_status = dep.get("github", {}).get("status", "not_listed")

        def badge(s):
            if s == "live":
                return '<span class="status live">LIVE</span>'
            elif s == "pending":
                return '<span class="status pending">PENDING</span>'
            else:
                return '<span class="status none">NOT LISTED</span>'

        product_rows += (
            "<tr>"
            "<td class='prod-name'>%s</td>"
            "<td>$%.2f</td>"
            "<td>%s</td>"
            "<td>%s</td>"
            "<td>%s</td>"
            "</tr>\n"
        ) % (title, price, badge(kofi_status), badge(gumroad_status), badge(github_status))

    # Checklist section -- show Ko-fi checklists for not-yet-listed products
    checklist_html = ""
    unlisted_count = 0
    for pid, listing_data in sorted(all_listings.items()):
        dep = deployments.get(pid, {})
        if dep.get("kofi", {}).get("status") == "live":
            continue
        unlisted_count += 1
        if unlisted_count > 5:
            checklist_html += '<div class="checklist-note">... and %d more products to list</div>\n' % (
                total_products - live_kofi - 5
            )
            break

        title = listing_data.get("title", pid)
        kofi = listing_data.get("kofi", {})
        paste = kofi.get("paste_ready", {})

        checklist_html += '<div class="checklist-product">\n'
        checklist_html += '<h3>%s ($%.2f)</h3>\n' % (title, listing_data.get("price", 0))
        checklist_html += '<div class="paste-block">\n'
        checklist_html += '<div class="paste-label">Title (copy this):</div>\n'
        checklist_html += '<pre class="paste-text">%s</pre>\n' % _html_escape(paste.get("title_field", ""))
        checklist_html += '<div class="paste-label">Description (copy this):</div>\n'
        checklist_html += '<pre class="paste-text">%s</pre>\n' % _html_escape(paste.get("description_field", ""))
        checklist_html += '<div class="paste-label">Price:</div>\n'
        checklist_html += '<pre class="paste-text">$%s</pre>\n' % paste.get("price_field", "0.00")
        checklist_html += '<div class="paste-label">Tags:</div>\n'
        checklist_html += '<pre class="paste-text">%s</pre>\n' % _html_escape(paste.get("tags_field", ""))

        img = kofi.get("image_suggestion", {})
        if img:
            checklist_html += '<div class="paste-label">Cover Image:</div>\n'
            checklist_html += '<pre class="paste-text">%s</pre>\n' % _html_escape(
                img.get("suggestion", "SolarPunk green aesthetic")
            )

        checklist_html += '</div>\n'
        checklist_html += '</div>\n'

    # Revenue potential
    total_catalog_value = sum(d.get("price", 0) for d in all_listings.values())

    coverage_pct = (total_live / total_possible * 100) if total_possible > 0 else 0

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>STOREFRONT DEPLOYER -- Deployment Dashboard</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0a0a0a;color:#d4d4d4;padding:24px;max-width:1000px;margin:0 auto}
h1{color:#00ff88;margin-bottom:4px;font-size:1.8em}
h2{color:#22c55e;margin:28px 0 12px;font-size:1.2em;border-bottom:1px solid #1a3320;padding-bottom:6px}
h3{color:#4ade80;font-size:1em;margin-bottom:8px}
.subtitle{color:#888;margin-bottom:20px;font-size:0.9em;font-style:italic}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:16px 0}
.stat{background:#111;border:1px solid #222;border-radius:6px;padding:12px;text-align:center}
.stat .val{font-size:1.4em;font-weight:700;color:#00ff88}
.stat .val.warn{color:#f59e0b}
.stat .val.danger{color:#ef4444}
.stat .lbl{font-size:0.75em;color:#666;margin-top:4px}
table{width:100%%;border-collapse:collapse;font-size:0.85em;margin-top:8px}
th{text-align:left;color:#00ff88;border-bottom:1px solid #333;padding:8px 6px}
td{border-bottom:1px solid #1a1a1a;padding:8px 6px;color:#aaa}
td.prod-name{color:#d4d4d4;font-weight:600}
.status{padding:2px 8px;border-radius:3px;font-size:0.75em;font-weight:700;letter-spacing:0.05em}
.status.live{background:#14532d;color:#4ade80;border:1px solid #22c55e}
.status.pending{background:#1c1200;color:#f59e0b;border:1px solid #d97706}
.status.none{background:#1a1a1a;color:#666;border:1px solid #333}
.checklist-product{background:#111;border:1px solid #222;border-radius:6px;padding:16px;margin-bottom:12px}
.checklist-note{color:#666;font-size:0.85em;padding:8px 0;font-style:italic}
.paste-block{margin-top:8px}
.paste-label{color:#888;font-size:0.75em;margin-top:10px;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.05em}
.paste-text{background:#0d1410;border:1px solid rgba(0,255,136,.13);border-radius:4px;padding:8px 10px;font-size:0.82em;color:#d4d4d4;white-space:pre-wrap;word-wrap:break-word;font-family:'Courier New',monospace;cursor:text;user-select:all;max-height:200px;overflow-y:auto}
.platform-bar{display:flex;gap:12px;margin:16px 0;flex-wrap:wrap}
.platform-card{background:#111;border:1px solid #222;border-radius:6px;padding:12px 16px;flex:1;min-width:200px}
.platform-card .name{color:#00ff88;font-weight:700;font-size:0.9em}
.platform-card .detail{color:#666;font-size:0.75em;margin-top:4px}
.platform-card a{color:#4ade80;font-size:0.8em}
.progress-bar{background:#1a1a1a;border-radius:4px;height:20px;margin:12px 0;overflow:hidden;border:1px solid #222}
.progress-fill{height:100%%;background:linear-gradient(90deg,#00ff88,#22c55e);border-radius:4px;transition:width 0.3s;display:flex;align-items:center;justify-content:center;font-size:0.7em;font-weight:700;color:#0a0a0a}
.action-box{background:#0d1410;border:1px solid rgba(0,255,136,.2);border-radius:6px;padding:16px;margin:16px 0}
.action-box .action-title{color:#00ff88;font-weight:700;margin-bottom:8px}
.action-box .action-url{font-size:0.85em}
.action-box .action-url a{color:#4ade80}
.ts{color:#444;font-size:0.7em;margin-top:20px;text-align:center}
.pcrf{margin-top:24px;padding:12px;background:#0a1a0a;border:1px solid #334433;border-radius:6px;color:#86efac;font-size:0.82em;text-align:center}
</style>
</head>
<body>
<h1>STOREFRONT DEPLOYER</h1>
<p class="subtitle">Deployment Dashboard -- What is listed where</p>

<div class="stat-grid">
<div class="stat"><div class="val">%d</div><div class="lbl">Total Products</div></div>
<div class="stat"><div class="val %s">%d / %d</div><div class="lbl">Listings Live</div></div>
<div class="stat"><div class="val">%d</div><div class="lbl">Ko-fi Live</div></div>
<div class="stat"><div class="val">%d</div><div class="lbl">Gumroad Live</div></div>
<div class="stat"><div class="val">%d</div><div class="lbl">GitHub Live</div></div>
<div class="stat"><div class="val">$%.2f</div><div class="lbl">Catalog Value</div></div>
</div>

<h2>Deployment Coverage</h2>
<div class="progress-bar">
<div class="progress-fill" style="width:%s%%">%s%%</div>
</div>

<h2>Platforms</h2>
<div class="platform-bar">
<div class="platform-card">
<div class="name">Ko-fi Shop (PRIMARY)</div>
<div class="detail">Free, no approval, instant listing</div>
<a href="%s" target="_blank">Open Dashboard</a>
</div>
<div class="platform-card">
<div class="name">Gumroad (SECONDARY)</div>
<div class="detail">10%% fee, account activation needed</div>
<a href="https://app.gumroad.com/products" target="_blank">Open Dashboard</a>
</div>
<div class="platform-card">
<div class="name">GitHub Releases (TERTIARY)</div>
<div class="detail">Free hosting, link to Ko-fi for payment</div>
<a href="https://github.com/%s/releases" target="_blank">View Releases</a>
</div>
</div>

<h2>Product Deployment Matrix</h2>
<table>
<tr><th>Product</th><th>Price</th><th>Ko-fi</th><th>Gumroad</th><th>GitHub</th></tr>
%s
</table>

<h2>Next Action</h2>
<div class="action-box">
<div class="action-title">List products on Ko-fi Shop</div>
<p>%d products ready to list. Copy-paste blocks below.</p>
<div class="action-url"><a href="%s" target="_blank">Open Ko-fi Shop Dashboard</a></div>
</div>

<h2>Copy-Paste Deployment Checklists</h2>
<p style="color:#888;font-size:0.85em;margin-bottom:12px">Each block below is ready to paste directly into Ko-fi. Select all text in each field, copy, paste.</p>
%s

<div class="pcrf">99%% of revenue goes to mutual aid. PCRF EIN: 93-1057665.</div>
<div class="ts">Generated %s UTC by STOREFRONT_DEPLOYER | Cycle %d</div>
</body>
</html>""" % (
        total_products,
        "danger" if total_live == 0 else ("warn" if coverage_pct < 50 else ""),
        total_live, total_possible,
        live_kofi, live_gumroad, live_github,
        total_catalog_value,
        "%.0f" % coverage_pct, "%.0f" % coverage_pct,
        KOFI_MANAGE_URL,
        GITHUB_REPO,
        product_rows,
        total_products - live_kofi, KOFI_MANAGE_URL,
        checklist_html,
        now, state.get("cycles", 0),
    )
    return html


def _html_escape(text):
    """Basic HTML escaping."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


# ---------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------

def run():
    print("=" * 60)
    print("STOREFRONT DEPLOYER -- The Bridge Between Products and Buyers")
    print("=" * 60)
    print()

    # 1. Load all data sources
    registry = _load("product_registry.json", {})
    products = registry.get("products", {})
    first_dollar = _load("first_dollar_plan.json", {})
    art_catalog = _load("art_catalog.json", {})
    gumroad_data = _load("gumroad_listings.json", {})
    storefront_copy = _load("storefront_listings.json", {})

    if not products:
        print("[warn] No products found in product_registry.json")
        print("       Run product generation engines first.")
        return {"engine": "STOREFRONT_DEPLOYER", "status": "no_products", "ts": _ts()}

    print("[load] %d products in registry" % len(products))
    print("[load] %d scored in first_dollar_plan" % len(first_dollar.get("scored_products", [])))
    print("[load] %d art pieces for images" % art_catalog.get("total_pieces", 0))
    print()

    # 2. Load state
    state = _load_state()
    state["cycles"] = state.get("cycles", 0) + 1

    # 3. Generate listings for every product on every platform
    all_listings = {}
    all_checklists = {}
    kofi_count = 0
    gumroad_count = 0
    github_count = 0

    print("[generate] Building listings for %d products x 3 platforms..." % len(products))
    print()

    for product_id, product in sorted(products.items()):
        if not product.get("content_ready"):
            print("  [skip] %s -- content not ready" % product_id)
            continue

        category = _classify_product(product_id, product)
        price = _get_price(product_id, product, first_dollar)
        title = product.get("title", product_id)

        print("  [%s] %s ($%.2f) -- %s" % (category, title[:45], price, product_id))

        # Generate platform listings
        kofi_listing = _generate_kofi_listing(product_id, product, category, price, art_catalog)
        gumroad_listing = _generate_gumroad_listing(product_id, product, category, price, art_catalog)
        github_listing = _generate_github_listing(product_id, product, category, price)

        # Check existing deployment status
        dep_status = _check_existing_deployments(product, state, product_id)
        state["deployments"][product_id] = dep_status

        # Build checklist
        checklist = _build_deployment_checklist(
            product_id, product, kofi_listing, gumroad_listing, github_listing
        )

        all_listings[product_id] = {
            "title": _truncate(title, 60),
            "price": price,
            "category": category,
            "file_path": product.get("file_path", ""),
            "kofi": kofi_listing,
            "gumroad": gumroad_listing,
            "github": github_listing,
            "checklist_steps": len(checklist),
        }
        all_checklists[product_id] = checklist

        kofi_count += 1
        gumroad_count += 1
        github_count += 1

    print()
    print("[generated] %d Ko-fi listings, %d Gumroad listings, %d GitHub listings" % (
        kofi_count, gumroad_count, github_count
    ))

    # 4. Deployment status summary
    deployments = state.get("deployments", {})
    live_kofi = sum(1 for d in deployments.values() if d.get("kofi", {}).get("status") == "live")
    live_gumroad = sum(1 for d in deployments.values() if d.get("gumroad", {}).get("status") == "live")
    live_github = sum(1 for d in deployments.values() if d.get("github", {}).get("status") == "live")
    total_live = live_kofi + live_gumroad + live_github
    total_possible = len(all_listings) * 3

    print()
    print("[status] Deployment matrix:")
    print("  Ko-fi:   %d / %d live" % (live_kofi, len(all_listings)))
    print("  Gumroad: %d / %d live" % (live_gumroad, len(all_listings)))
    print("  GitHub:  %d / %d live" % (live_github, len(all_listings)))
    print("  Total:   %d / %d (%.0f%% coverage)" % (
        total_live, total_possible,
        (total_live / total_possible * 100) if total_possible > 0 else 0,
    ))

    # 5. Save listings data
    listings_output = {
        "generated_at": _ts(),
        "engine": "STOREFRONT_DEPLOYER",
        "total_products": len(all_listings),
        "platforms": {
            "kofi": {"listings": kofi_count, "live": live_kofi},
            "gumroad": {"listings": gumroad_count, "live": live_gumroad},
            "github": {"listings": github_count, "live": live_github},
        },
        "products": {},
    }
    for pid, ld in all_listings.items():
        listings_output["products"][pid] = {
            "title": ld["title"],
            "price": ld["price"],
            "category": ld["category"],
            "file_path": ld["file_path"],
            "kofi_paste": ld["kofi"]["paste_ready"],
            "gumroad_paste": ld["gumroad"]["paste_ready"],
            "github_paste": ld["github"]["paste_ready"],
            "image_suggestion": ld["kofi"].get("image_suggestion", {}),
        }
    _save("storefront_deployer_listings.json", listings_output)
    print()
    print("[write] data/storefront_deployer_listings.json")

    # 6. Save checklists
    checklists_output = {
        "generated_at": _ts(),
        "engine": "STOREFRONT_DEPLOYER",
        "total_products": len(all_checklists),
        "products": {},
    }
    for pid, steps in all_checklists.items():
        checklists_output["products"][pid] = {
            "title": all_listings[pid]["title"],
            "price": all_listings[pid]["price"],
            "total_steps": len(steps),
            "steps": steps,
        }
    _save("storefront_deployer_checklists.json", checklists_output)
    print("[write] data/storefront_deployer_checklists.json")

    # 7. Save state
    state["last_run"] = _ts()
    state["total_products"] = len(all_listings)
    state["coverage"] = {
        "total_live": total_live,
        "total_possible": total_possible,
        "kofi_live": live_kofi,
        "gumroad_live": live_gumroad,
        "github_live": live_github,
    }
    state["status"] = "deployed" if total_live > 0 else "listings_ready"
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print("[write] data/storefront_deployer_state.json")

    # 8. Build HTML dashboard
    html = _build_html(all_listings, state)
    (DOCS / "store_deploy.html").write_text(html, encoding="utf-8")
    print("[write] docs/store_deploy.html")

    # 9. Final report
    print()
    print("=" * 60)
    print("STOREFRONT DEPLOYER: %d products, %d listings generated" % (
        len(all_listings), kofi_count + gumroad_count + github_count,
    ))
    print()
    if live_kofi == 0:
        print("  CRITICAL: Zero products listed on Ko-fi.")
        print("  ACTION: Open %s" % KOFI_MANAGE_URL)
        print("  Copy-paste blocks are in data/storefront_deployer_checklists.json")
        print("  Visual dashboard: docs/store_deploy.html")
    else:
        print("  Ko-fi: %d live | Gumroad: %d live | GitHub: %d live" % (
            live_kofi, live_gumroad, live_github,
        ))
    print()

    # Print top 3 products to list next
    unlisted = [(pid, ld) for pid, ld in all_listings.items()
                if deployments.get(pid, {}).get("kofi", {}).get("status") != "live"]
    # Sort by price ascending (cheapest first = easiest first sale)
    unlisted.sort(key=lambda x: x[1]["price"])

    if unlisted:
        print("  TOP 3 TO LIST NEXT (cheapest first):")
        for pid, ld in unlisted[:3]:
            print("    -> %s ($%.2f) [%s]" % (ld["title"], ld["price"], ld["category"]))
        print()
        print("  Full paste-ready checklists: docs/store_deploy.html")

    print()
    print("  99%% of revenue goes to mutual aid. The bridge is built.")
    print("  Now someone needs to walk across it.")
    print("=" * 60)

    return {
        "engine": "STOREFRONT_DEPLOYER",
        "status": state["status"],
        "total_products": len(all_listings),
        "listings_generated": kofi_count + gumroad_count + github_count,
        "live_kofi": live_kofi,
        "live_gumroad": live_gumroad,
        "live_github": live_github,
        "coverage_pct": round((total_live / total_possible * 100) if total_possible > 0 else 0, 1),
        "ts": _ts(),
    }


if __name__ == "__main__":
    run()
