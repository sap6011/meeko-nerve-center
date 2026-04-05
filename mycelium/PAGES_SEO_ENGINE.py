# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
PAGES_SEO_ENGINE -- GitHub Pages SEO injector

Scans docs/*.html, injects/updates:
  - meta description, OG tags, Twitter cards
  - canonical link, JSON-LD Organization schema
  - sitemap.xml, robots.txt

Writes: data/seo_engine_state.json
"""
import os
import re
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs")
STATE = DATA / "seo_engine_state.json"

BASE_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"

ORG_JSONLD = json.dumps({
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "SolarPunk",
    "url": BASE_URL,
    "description": "Autonomous digital organism routing revenue to Palestinian relief.",
    "foundingDate": "2025",
    "sameAs": [
        "https://github.com/meekotharaccoon-cell/meeko-nerve-center"
    ]
}, indent=2)

# ── helpers ──────────────────────────────────────────────────

def _extract_title(html):
    """Pull <title>...</title> text."""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        raw = m.group(1).strip()
        # strip HTML entities / tags inside title
        raw = re.sub(r"<[^>]+>", "", raw)
        raw = raw.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        raw = raw.replace("&#8212;", " -- ").replace("&mdash;", " -- ")
        raw = raw.replace("&#x27;", "'").replace("&quot;", '"')
        return raw
    return ""


def _extract_body_text(html, limit=220):
    """Pull first visible text from <body> for auto-description."""
    # remove script/style blocks
    cleaned = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html,
                     flags=re.IGNORECASE | re.DOTALL)
    # grab body
    body_m = re.search(r"<body[^>]*>(.*)", cleaned,
                       re.IGNORECASE | re.DOTALL)
    if not body_m:
        return ""
    body = body_m.group(1)
    # strip all tags
    text = re.sub(r"<[^>]+>", " ", body)
    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "..."
    return text


def _make_description(title, html):
    """Build a meta description from title + body text."""
    if title:
        body = _extract_body_text(html, 180)
        if body:
            desc = "%s -- %s" % (title, body)
        else:
            desc = title
    else:
        desc = _extract_body_text(html, 220)
    if not desc:
        desc = "SolarPunk Nerve Center -- autonomous digital organism."
    # cap at 160 chars for SEO
    if len(desc) > 160:
        desc = desc[:157].rsplit(" ", 1)[0] + "..."
    # sanitize for attribute value
    desc = desc.replace('"', "&quot;").replace("\n", " ")
    return desc


def _page_url(filename):
    if filename == "index.html":
        return BASE_URL + "/"
    return "%s/%s" % (BASE_URL, filename)


# ── tag injection ────────────────────────────────────────────

def _upsert_meta(html, attr_name, attr_val, content):
    """Insert or update a <meta ...> tag in <head>."""
    safe_content = content.replace('"', "&quot;")
    tag = '<meta %s="%s" content="%s">' % (attr_name, attr_val, safe_content)

    # Build patterns that handle both quote styles.
    # Use [^"]* for double-quoted content, [^']* for single-quoted,
    # so apostrophes inside double-quoted attrs don't break the match.
    esc_name = re.escape(attr_name)
    esc_val = re.escape(attr_val)

    # attr="val" content="..." (double-quoted content)
    pat_dq = re.compile(
        r'<meta\s+%s\s*=\s*["\']%s["\']\s+content\s*=\s*"[^"]*"\s*/?>'
        % (esc_name, esc_val),
        re.IGNORECASE
    )
    # attr="val" content='...' (single-quoted content)
    pat_sq = re.compile(
        r"<meta\s+%s\s*=\s*[\"']%s[\"']\s+content\s*=\s*'[^']*'\s*/?>"
        % (esc_name, esc_val),
        re.IGNORECASE
    )
    # reversed: content="..." attr="val"
    pat_rev_dq = re.compile(
        r'<meta\s+content\s*=\s*"[^"]*"\s+%s\s*=\s*["\']%s["\']\s*/?>'
        % (esc_name, esc_val),
        re.IGNORECASE
    )
    pat_rev_sq = re.compile(
        r"<meta\s+content\s*=\s*'[^']*'\s+%s\s*=\s*[\"']%s[\"']\s*/?>"
        % (esc_name, esc_val),
        re.IGNORECASE
    )

    for pat in (pat_dq, pat_sq, pat_rev_dq, pat_rev_sq):
        if pat.search(html):
            return pat.sub(tag, html)

    # inject right after last <meta ...> in <head>, or after <head> / first tag
    insert_after = None
    for m in re.finditer(r"<meta\s[^>]*>", html, re.IGNORECASE):
        insert_after = m
    if insert_after:
        pos = insert_after.end()
        return html[:pos] + "\n" + tag + html[pos:]

    # fallback: after <head> tag
    head_m = re.search(r"<head[^>]*>", html, re.IGNORECASE)
    if head_m:
        pos = head_m.end()
        return html[:pos] + "\n" + tag + html[pos:]

    return html


def _upsert_link_canonical(html, url):
    """Insert or update <link rel="canonical">."""
    tag = '<link rel="canonical" href="%s">' % url
    pat = re.compile(
        r'<link\s+rel\s*=\s*["\']canonical["\']\s+href\s*=\s*["\'][^"\']*["\']\s*/?>',
        re.IGNORECASE
    )
    if pat.search(html):
        return pat.sub(tag, html)

    # inject before </head>
    head_close = re.search(r"</head>", html, re.IGNORECASE)
    if head_close:
        pos = head_close.start()
        return html[:pos] + tag + "\n" + html[pos:]
    return html


def _upsert_jsonld(html, jsonld_str):
    """Insert or update JSON-LD Organization block."""
    marker = '"@type": "Organization"'
    # replace existing Organization JSON-LD script block
    pat = re.compile(
        r'<script\s+type\s*=\s*["\']application/ld\+json["\'][^>]*>\s*\{[^}]*"@type"\s*:\s*"Organization"[^<]*</script>',
        re.IGNORECASE | re.DOTALL
    )
    new_block = '<script type="application/ld+json">\n%s\n</script>' % jsonld_str

    if pat.search(html):
        return pat.sub(new_block, html)

    # inject before </head>
    head_close = re.search(r"</head>", html, re.IGNORECASE)
    if head_close:
        pos = head_close.start()
        return html[:pos] + new_block + "\n" + html[pos:]
    return html


# ── main processing ──────────────────────────────────────────

def process_page(filepath):
    """Inject SEO tags into one HTML file.  Returns page info dict."""
    html = filepath.read_text(encoding="utf-8", errors="replace")
    filename = filepath.name
    title = _extract_title(html)
    desc = _make_description(title, html)
    url = _page_url(filename)
    og_title = title if title else "SolarPunk Nerve Center"

    # meta description
    html = _upsert_meta(html, "name", "description", desc)

    # Open Graph
    html = _upsert_meta(html, "property", "og:title", og_title)
    html = _upsert_meta(html, "property", "og:description", desc)
    html = _upsert_meta(html, "property", "og:url", url)
    html = _upsert_meta(html, "property", "og:type", "website")

    # Twitter Card
    html = _upsert_meta(html, "name", "twitter:card", "summary")
    html = _upsert_meta(html, "name", "twitter:title", og_title)
    html = _upsert_meta(html, "name", "twitter:description", desc)

    # Canonical
    html = _upsert_link_canonical(html, url)

    # JSON-LD (only on index page to avoid duplication across all pages)
    if filename == "index.html":
        html = _upsert_jsonld(html, ORG_JSONLD)

    filepath.write_text(html, encoding="utf-8")

    stat = filepath.stat()
    return {
        "file": filename,
        "title": title,
        "description": desc,
        "url": url,
        "lastmod": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc
                                          ).strftime("%Y-%m-%d"),
    }


def generate_sitemap(pages):
    """Write docs/sitemap.xml from page info list."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    # sort: index first, then alphabetical
    def sort_key(p):
        name = p.get("file", "")
        if name == "index.html":
            return ("0", name)
        return ("1", name)

    for p in sorted(pages, key=sort_key):
        prio = "1.0" if p.get("file") == "index.html" else "0.7"
        lines.append("  <url>")
        lines.append("    <loc>%s</loc>" % p.get("url", ""))
        lines.append("    <lastmod>%s</lastmod>" % p.get("lastmod", ""))
        lines.append("    <changefreq>weekly</changefreq>")
        lines.append("    <priority>%s</priority>" % prio)
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")

    sitemap_path = DOCS / "sitemap.xml"
    sitemap_path.write_text("\n".join(lines), encoding="utf-8")
    print("  sitemap.xml written (%d URLs)" % len(pages))


def generate_robots():
    """Write docs/robots.txt allowing all crawlers."""
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "Sitemap: %s/sitemap.xml\n" % BASE_URL
    )
    robots_path = DOCS / "robots.txt"
    robots_path.write_text(content, encoding="utf-8")
    print("  robots.txt written")


def run():
    print("PAGES_SEO_ENGINE starting...")

    if not DOCS.is_dir():
        print("  SKIP: docs/ directory not found")
        return

    html_files = sorted(DOCS.glob("*.html"))
    if not html_files:
        print("  SKIP: no HTML files in docs/")
        return

    print("  found %d HTML files" % len(html_files))

    pages = []
    errors = []
    for fp in html_files:
        try:
            info = process_page(fp)
            pages.append(info)
            print("  OK  %s" % fp.name)
        except Exception as exc:
            errors.append({"file": fp.name, "error": str(exc)})
            print("  ERR %s: %s" % (fp.name, exc))

    generate_sitemap(pages)
    generate_robots()

    state = {
        "engine": "PAGES_SEO_ENGINE",
        "last_run": datetime.now(timezone.utc).isoformat(),
        "pages_processed": len(pages),
        "errors": len(errors),
        "base_url": BASE_URL,
        "pages": [{"file": p.get("file", ""), "url": p.get("url", "")}
                  for p in pages],
        "error_details": errors,
    }
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print("PAGES_SEO_ENGINE done -- %d pages, %d errors" % (
        len(pages), len(errors)))


if __name__ == "__main__":
    run()
