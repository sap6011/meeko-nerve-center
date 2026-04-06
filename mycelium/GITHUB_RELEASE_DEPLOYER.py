# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
GITHUB_RELEASE_DEPLOYER.py -- packages products as .zip and deploys via GitHub Releases
========================================================================================
Reads every .md product from products/ and cross-references data/product_registry.json
for metadata (titles, prices). For each product it:

  1. Creates a .zip containing the .md file + a README with purchase / donation info
  2. Uploads the .zip as a GitHub Release asset
  3. Tracks deployed releases in data/release_deployer_state.json
  4. Skips products that were already released (idempotent)

If GITHUB_TOKEN is missing, runs in DRY_RUN mode -- prepares everything locally
but does not call the API. Prints exactly what it WOULD do.

Download URL format:
  https://github.com/meekotharaccoon-cell/meeko-nerve-center/releases/download/{tag}/{slug}.zip

stdlib only. No pip installs. No secrets required for dry-run.
"""
import os
import json
import zipfile
import tempfile
import urllib.request
import urllib.error
import hashlib
from pathlib import Path
from datetime import datetime, timezone

DATA  = Path("data"); DATA.mkdir(exist_ok=True)
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = "meekotharaccoon-cell"
REPO  = "meeko-nerve-center"
API   = "https://api.github.com"

KOFI_URL  = "https://ko-fi.com/meekotharaccoon"
PCRF_NOTE = (
    "15%% of all revenue goes to Palestinian Children's Relief Fund "
    "(PCRF, EIN: 93-1057665)"
)

STATE_FILE   = DATA / "release_deployer_state.json"
REGISTRY_FILE = DATA / "product_registry.json"
PRODUCTS_DIR  = Path("products")


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "deployed": {},
        "runs": 0,
        "last_run": None,
        "dry_runs": 0,
        "total_zips_created": 0,
        "total_assets_uploaded": 0,
    }


def save_state(state):
    state["deployed"] = dict(
        list(state.get("deployed", {}).items())[-500:]
    )
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Product discovery
# ---------------------------------------------------------------------------

def discover_products():
    """Walk products/ recursively for all .md files."""
    found = []
    if not PRODUCTS_DIR.exists():
        print("  WARN: products/ directory not found")
        return found
    for md in sorted(PRODUCTS_DIR.rglob("*.md")):
        rel = md.relative_to(PRODUCTS_DIR)
        slug = str(rel).replace("\\", "/").replace("/", "--").replace(".md", "")
        found.append({"path": md, "slug": slug, "rel": str(rel)})
    print("  Discovered %d product files in products/" % len(found))
    return found


def load_registry():
    """Load product_registry.json for metadata enrichment."""
    if not REGISTRY_FILE.exists():
        print("  WARN: product_registry.json not found -- using defaults")
        return {}
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        return data.get("products", {})
    except Exception as exc:
        print("  WARN: Failed to parse product_registry.json: %s" % str(exc)[:80])
        return {}


def match_registry(slug, rel_path, registry):
    """Try to match a discovered product to a registry entry."""
    # Direct slug match
    if slug in registry:
        return registry.get(slug)
    # Try matching by file_path
    for _pid, meta in registry.items():
        fp = meta.get("file_path", "")
        # Normalise separators for comparison
        fp_norm = fp.replace("\\", "/")
        target = ("products/" + rel_path).replace("\\", "/")
        if fp_norm == target:
            return meta
    # Try stem-based fuzzy match
    stem = Path(rel_path).stem
    for pid, meta in registry.items():
        if pid == stem or stem in pid or pid in stem:
            return meta
    return None


# ---------------------------------------------------------------------------
# ZIP packaging
# ---------------------------------------------------------------------------

def build_readme_txt(title, price, slug):
    """Build the README.txt that goes inside each .zip."""
    lines = []
    lines.append("=" * 60)
    lines.append(title)
    lines.append("=" * 60)
    lines.append("")
    lines.append("Thank you for downloading this SolarPunk digital product!")
    lines.append("")
    if price:
        lines.append("Suggested price: $%.2f" % price)
        lines.append("")
    lines.append("------------------------------------------------------------")
    lines.append("SUPPORT & PURCHASE")
    lines.append("------------------------------------------------------------")
    lines.append("Ko-fi: %s" % KOFI_URL)
    lines.append("")
    lines.append(PCRF_NOTE)
    lines.append("")
    lines.append("------------------------------------------------------------")
    lines.append("ABOUT")
    lines.append("------------------------------------------------------------")
    lines.append("Built by the SolarPunk autonomous AI system.")
    lines.append("300+ engines. Zero cloud bills. Fighting tyranny with code.")
    lines.append("")
    lines.append("GitHub: https://github.com/%s/%s" % (OWNER, REPO))
    lines.append("Ko-fi:  %s" % KOFI_URL)
    lines.append("")
    lines.append("Every purchase helps fund:")
    lines.append("  - Palestinian Children's Relief Fund (PCRF)")
    lines.append("  - Open-source autonomous infrastructure")
    lines.append("  - Mutual aid networks")
    lines.append("")
    lines.append("Peace. Code. Solidarity.")
    lines.append("")
    return "\n".join(lines)


def create_zip(product_path, slug, title, price, tmp_dir):
    """Create a .zip containing the .md and a README.txt."""
    zip_name = "%s.zip" % slug
    zip_path = Path(tmp_dir) / zip_name

    readme_content = build_readme_txt(title, price, slug)
    md_content = product_path.read_bytes()

    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
        # Add the product markdown
        zf.writestr(product_path.name, md_content)
        # Add the README
        zf.writestr("README.txt", readme_content.encode("utf-8"))

    size = zip_path.stat().st_size
    md5 = hashlib.md5(zip_path.read_bytes()).hexdigest()[:12]
    print("    ZIP: %s (%s bytes, md5=%s)" % (zip_name, "{:,}".format(size), md5))
    return zip_path, zip_name, size


# ---------------------------------------------------------------------------
# GitHub API (urllib only)
# ---------------------------------------------------------------------------

def gh(method, path, body=None, upload_url=None, content_type="application/json"):
    """Call GitHub API. Returns (data, error_string)."""
    url = upload_url or ("%s%s" % (API, path))
    if body and not upload_url:
        data = json.dumps(body).encode("utf-8")
    else:
        data = body
    headers = {
        "Authorization": "Bearer %s" % TOKEN,
        "Accept": "application/vnd.github+json",
        "Content-Type": content_type,
        "User-Agent": "SolarPunk-ReleaseDeployer/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as exc:
        return None, "HTTP %d: %s" % (exc.code, exc.read().decode()[:200])
    except Exception as exc:
        return None, str(exc)[:120]


def get_or_create_release(tag):
    """Find existing release by tag, or create a new one."""
    # Check existing releases
    releases, err = gh("GET", "/repos/%s/%s/releases" % (OWNER, REPO))
    if releases:
        for r in releases:
            if r.get("tag_name") == tag:
                print("  Found existing release: %s" % r.get("html_url", tag))
                return r, None

    # Create new release
    body_text = (
        "SolarPunk Digital Products -- packaged as .zip with README.\n\n"
        "%s\n\n"
        "Ko-fi: %s\n"
        "GitHub: https://github.com/%s/%s\n\n"
        "Built autonomously by 300+ AI engines."
    ) % (PCRF_NOTE, KOFI_URL, OWNER, REPO)

    release, err = gh("POST", "/repos/%s/%s/releases" % (OWNER, REPO), {
        "tag_name": tag,
        "name": "SolarPunk Products -- %s" % tag,
        "body": body_text,
        "draft": False,
        "prerelease": False,
    })
    if release:
        print("  Created release: %s" % release.get("html_url", tag))
    return release, err


def upload_asset(release, zip_path, zip_name):
    """Upload a .zip file as a release asset."""
    upload_url = release.get("upload_url", "").replace("{?name,label}", "")
    if not upload_url:
        return None, "No upload_url in release"
    full_url = "%s?name=%s" % (upload_url, zip_name)
    content = zip_path.read_bytes()
    return gh(
        "POST", None, body=content,
        upload_url=full_url,
        content_type="application/zip",
    )


def get_existing_asset_names(release):
    """Return set of asset filenames already on this release."""
    names = set()
    for asset in release.get("assets", []):
        names.add(asset.get("name", ""))
    return names


# ---------------------------------------------------------------------------
# Main run
# ---------------------------------------------------------------------------

def run():
    ts = datetime.now(timezone.utc).isoformat()
    dry_run = not TOKEN
    mode = "DRY_RUN" if dry_run else "LIVE"

    print("")
    print("GITHUB_RELEASE_DEPLOYER -- %s [%s]" % (ts, mode))
    print("=" * 60)

    if dry_run:
        print("  No GITHUB_TOKEN found -- running in DRY_RUN mode")
        print("  Will prepare .zips and show what WOULD be deployed")

    state = load_state()
    state["runs"] = state.get("runs", 0) + 1
    state["last_run"] = ts
    deployed = state.get("deployed", {})

    # Discover products
    products = discover_products()
    if not products:
        print("  No product files found -- nothing to do")
        save_state(state)
        return state

    # Load registry for metadata
    registry = load_registry()

    # Determine release tag
    version = datetime.now(timezone.utc).strftime("%Y%m%d")
    tag = "products-%s" % version
    print("  Release tag: %s" % tag)

    # In live mode, get or create the release
    release = None
    existing_assets = set()
    if not dry_run:
        release, err = get_or_create_release(tag)
        if not release:
            print("  ERROR: Could not get/create release: %s" % err)
            print("  Falling back to DRY_RUN for this cycle")
            dry_run = True
        else:
            existing_assets = get_existing_asset_names(release)

    # Process each product
    created = 0
    uploaded = 0
    skipped = 0
    errors = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        for prod in products:
            slug = prod.get("slug", "unknown")
            md_path = prod.get("path")
            rel = prod.get("rel", slug)

            # Skip if already deployed with this tag
            deploy_key = "%s@%s" % (slug, tag)
            if deploy_key in deployed:
                print("  SKIP (already deployed): %s" % slug)
                skipped += 1
                continue

            # Get metadata from registry
            meta = match_registry(slug, rel, registry)
            title = "SolarPunk Product"
            price = None
            if meta:
                title = meta.get("title", title)
                price = meta.get("price")

            print("  Processing: %s" % slug)
            print("    Title: %s | Price: %s" % (
                title,
                "$%.2f" % price if price else "free/unset",
            ))

            # Create .zip
            try:
                zip_path, zip_name, zip_size = create_zip(
                    md_path, slug, title, price, tmp_dir
                )
                created += 1
                state["total_zips_created"] = state.get("total_zips_created", 0) + 1
            except Exception as exc:
                print("    ERROR creating zip: %s" % str(exc)[:100])
                errors.append({"slug": slug, "error": str(exc)[:100]})
                continue

            # Upload or dry-run
            if dry_run:
                print("    DRY_RUN: Would upload %s (%s bytes) to release %s" % (
                    zip_name, "{:,}".format(zip_size), tag
                ))
                download_url = (
                    "https://github.com/%s/%s/releases/download/%s/%s"
                    % (OWNER, REPO, tag, zip_name)
                )
                print("    DRY_RUN: Download URL would be: %s" % download_url)
                state["dry_runs"] = state.get("dry_runs", 0) + 1
            else:
                # Check if asset already exists on release
                if zip_name in existing_assets:
                    print("    SKIP (asset exists on release): %s" % zip_name)
                    download_url = (
                        "https://github.com/%s/%s/releases/download/%s/%s"
                        % (OWNER, REPO, tag, zip_name)
                    )
                    deployed[deploy_key] = {
                        "slug": slug,
                        "tag": tag,
                        "url": download_url,
                        "title": title,
                        "ts": ts,
                        "note": "asset_existed",
                    }
                    skipped += 1
                    continue

                print("    Uploading %s to release..." % zip_name)
                asset, err = upload_asset(release, zip_path, zip_name)
                if asset:
                    download_url = asset.get("browser_download_url", "")
                    print("    UPLOADED: %s" % download_url)
                    uploaded += 1
                    state["total_assets_uploaded"] = (
                        state.get("total_assets_uploaded", 0) + 1
                    )
                    deployed[deploy_key] = {
                        "slug": slug,
                        "tag": tag,
                        "url": download_url,
                        "title": title,
                        "size": zip_size,
                        "ts": ts,
                    }
                else:
                    print("    UPLOAD FAILED: %s" % err)
                    errors.append({"slug": slug, "error": err})

    # Summary
    state["deployed"] = deployed
    print("")
    print("-" * 60)
    print("SUMMARY")
    print("  Products found:  %d" % len(products))
    print("  ZIPs created:    %d" % created)
    print("  Assets uploaded: %d" % uploaded)
    print("  Skipped:         %d" % skipped)
    print("  Errors:          %d" % len(errors))
    print("  Mode:            %s" % mode)
    if errors:
        for e in errors:
            print("  ERR: %s -- %s" % (e.get("slug", "?"), e.get("error", "?")))
    print("-" * 60)

    save_state(state)
    print("  State saved to %s" % str(STATE_FILE))

    return {
        "status": "dry_run" if dry_run else "deployed",
        "tag": tag,
        "created": created,
        "uploaded": uploaded,
        "skipped": skipped,
        "errors": len(errors),
        "ts": ts,
    }


if __name__ == "__main__":
    run()
