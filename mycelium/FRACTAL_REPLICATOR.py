# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
FRACTAL_REPLICATOR.py -- Template variant multiplier
=====================================================
Takes one template and generates domain-specific variants.
A single web scraper template becomes 5 variants (ecommerce,
news, social media, government data, academic papers) -- each
with domain-specific imports, URLs, selectors, and patterns.

Reads: products/templates/ for existing templates
Writes: products/templates/{domain}/variants/*
        data/fractal_replicator_report.json
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# -- paths ----------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
PRODUCTS = BASE / "products" / "templates"
PRODUCTS.mkdir(parents=True, exist_ok=True)

REPORT_FILE = DATA / "fractal_replicator_report.json"
TRACKING_FILE = DATA / "fractal_replicator_tracking.json"


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


def file_hash(content):
    """Generate a short hash for dedup tracking."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]


# -- variant specifications -----------------------------------------------
# Each domain crossing defines how to specialize a template.

PYTHON_AUTOMATION_VARIANTS = {
    "web_scraper_requests.md": {
        "variant_key": "scraper",
        "domains": [
            {
                "name": "ecommerce",
                "title": "E-Commerce Product Scraper",
                "imports": "import requests\nfrom bs4 import BeautifulSoup\nimport json, time, csv",
                "target_url": "https://example-shop.com/products",
                "selectors": "'.product-card', '.price', '.product-title', '.rating'",
                "fields": "title, price, rating, availability, url",
                "notes": "Handles pagination via next-page links. Exports to CSV.",
            },
            {
                "name": "news",
                "title": "News Article Scraper",
                "imports": "import requests\nfrom bs4 import BeautifulSoup\nimport json, time\nfrom datetime import datetime",
                "target_url": "https://example-news.com/latest",
                "selectors": "'article', '.headline', '.byline', '.publish-date'",
                "fields": "headline, author, date, summary, full_text, url",
                "notes": "Extracts article body text. Respects robots.txt.",
            },
            {
                "name": "social_media",
                "title": "Social Media Profile Scraper",
                "imports": "import requests\nimport json, time\nfrom urllib.parse import urljoin",
                "target_url": "https://example-social.com/api/v1/profiles",
                "selectors": "API-based: JSON response fields",
                "fields": "username, display_name, bio, follower_count, post_count",
                "notes": "Uses API endpoints where available. Rate-limited to 1 req/sec.",
            },
            {
                "name": "government_data",
                "title": "Government Open Data Scraper",
                "imports": "import requests\nimport json, csv\nfrom pathlib import Path",
                "target_url": "https://data.gov/api/3/action/package_search",
                "selectors": "API-based: CKAN API format",
                "fields": "dataset_name, organization, format, date_updated, download_url",
                "notes": "Uses CKAN API standard. Downloads linked CSV/JSON datasets.",
            },
            {
                "name": "academic_papers",
                "title": "Academic Paper Metadata Scraper",
                "imports": "import requests\nimport json, time\nfrom urllib.parse import quote",
                "target_url": "https://api.semanticscholar.org/graph/v1/paper/search",
                "selectors": "API-based: Semantic Scholar API",
                "fields": "title, authors, year, abstract, citation_count, doi",
                "notes": "Uses Semantic Scholar API. Respects 100 req/5min rate limit.",
            },
        ],
    },
    "api_client_rest.md": {
        "variant_key": "api_client",
        "domains": [
            {
                "name": "weather_api",
                "title": "Weather API Client",
                "imports": "import requests, json, time",
                "target_url": "https://api.openweathermap.org/data/2.5",
                "selectors": "N/A",
                "fields": "temperature, humidity, wind_speed, description, forecast",
                "notes": "Requires OPENWEATHER_API_KEY. Supports current weather and 5-day forecast.",
            },
            {
                "name": "github_api",
                "title": "GitHub API Client",
                "imports": "import requests, json, time, os",
                "target_url": "https://api.github.com",
                "selectors": "N/A",
                "fields": "repos, stars, issues, pull_requests, contributors",
                "notes": "Uses GITHUB_TOKEN for auth. Handles pagination via Link header.",
            },
            {
                "name": "crypto_api",
                "title": "Cryptocurrency Price API Client",
                "imports": "import requests, json, time\nfrom decimal import Decimal",
                "target_url": "https://api.coingecko.com/api/v3",
                "selectors": "N/A",
                "fields": "coin, price_usd, market_cap, volume_24h, price_change_24h",
                "notes": "Free tier: 10-30 calls/min. No API key required for basic queries.",
            },
            {
                "name": "rss_feed",
                "title": "RSS Feed API Client",
                "imports": "import requests, json, xml.etree.ElementTree as ET",
                "target_url": "https://example.com/feed.xml",
                "selectors": "N/A",
                "fields": "title, link, description, pub_date, author",
                "notes": "Parses RSS 2.0 and Atom feeds. Converts XML to JSON.",
            },
            {
                "name": "translation_api",
                "title": "Translation API Client",
                "imports": "import requests, json, time, hashlib",
                "target_url": "https://api.mymemory.translated.net/get",
                "selectors": "N/A",
                "fields": "source_text, target_text, source_lang, target_lang, confidence",
                "notes": "Free tier: 5000 chars/day. Caches translations locally.",
            },
        ],
    },
    "data_pipeline_etl.md": {
        "variant_key": "etl",
        "domains": [
            {
                "name": "log_processor",
                "title": "Log File ETL Pipeline",
                "imports": "import json, re\nfrom pathlib import Path\nfrom datetime import datetime, timezone\nfrom collections import Counter",
                "target_url": "N/A (local log files)",
                "selectors": "regex patterns for log parsing",
                "fields": "timestamp, level, source, message, count",
                "notes": "Parses Apache, nginx, and Python log formats. Aggregates by level.",
            },
            {
                "name": "csv_merger",
                "title": "Multi-CSV Merger ETL Pipeline",
                "imports": "import json, csv, glob\nfrom pathlib import Path\nfrom datetime import datetime, timezone",
                "target_url": "N/A (local CSV files)",
                "selectors": "N/A",
                "fields": "All columns from source CSVs, unified schema",
                "notes": "Merges CSVs with different schemas. Fills missing columns with null.",
            },
            {
                "name": "json_normalizer",
                "title": "Nested JSON Normalizer ETL",
                "imports": "import json\nfrom pathlib import Path\nfrom datetime import datetime, timezone",
                "target_url": "N/A (JSON files or API responses)",
                "selectors": "N/A",
                "fields": "Flattened key-value pairs from nested structures",
                "notes": "Handles arbitrarily nested JSON. Dot-notation output keys.",
            },
            {
                "name": "database_sync",
                "title": "Database Sync ETL Pipeline",
                "imports": "import json, sqlite3\nfrom pathlib import Path\nfrom datetime import datetime, timezone",
                "target_url": "N/A (SQLite databases)",
                "selectors": "SQL queries",
                "fields": "Varies per table schema",
                "notes": "Extracts from SQLite, transforms in Python, loads to new SQLite.",
            },
            {
                "name": "email_parser",
                "title": "Email Data ETL Pipeline",
                "imports": "import json, email, re\nfrom pathlib import Path\nfrom datetime import datetime, timezone",
                "target_url": "N/A (local .eml files)",
                "selectors": "email header fields",
                "fields": "from, to, subject, date, body_text, attachments",
                "notes": "Parses .eml files. Extracts headers, body, and attachment metadata.",
            },
        ],
    },
}

GITHUB_ACTIONS_VARIANTS = {
    "ci_python_test.md": {
        "variant_key": "ci",
        "domains": [
            {
                "name": "node_js",
                "title": "Node.js CI/CD Test Pipeline",
                "runner": "ubuntu-latest",
                "setup": "actions/setup-node@v4 with node-version: ['18', '20', '22']",
                "install": "npm ci",
                "test_cmd": "npm test",
                "lint_cmd": "npx eslint .",
            },
            {
                "name": "rust",
                "title": "Rust CI/CD Test Pipeline",
                "runner": "ubuntu-latest",
                "setup": "dtolnay/rust-toolchain@stable",
                "install": "cargo build",
                "test_cmd": "cargo test --verbose",
                "lint_cmd": "cargo clippy -- -D warnings",
            },
            {
                "name": "go",
                "title": "Go CI/CD Test Pipeline",
                "runner": "ubuntu-latest",
                "setup": "actions/setup-go@v5 with go-version: '1.22'",
                "install": "go mod download",
                "test_cmd": "go test ./... -v -race",
                "lint_cmd": "go vet ./...",
            },
            {
                "name": "docker",
                "title": "Docker Build and Test Pipeline",
                "runner": "ubuntu-latest",
                "setup": "docker/setup-buildx-action@v3",
                "install": "docker build -t app:test .",
                "test_cmd": "docker run --rm app:test pytest",
                "lint_cmd": "hadolint Dockerfile",
            },
        ],
    },
    "scheduled_data_fetch.md": {
        "variant_key": "cron",
        "domains": [
            {
                "name": "hourly_health",
                "title": "Hourly Health Check Cron",
                "schedule": "'0 * * * *'",
                "script": "scripts/health_check.py",
                "commit_path": "data/health/",
                "commit_msg": "chore: update health metrics [skip ci]",
            },
            {
                "name": "daily_backup",
                "title": "Daily JSON Backup Cron",
                "schedule": "'0 2 * * *'",
                "script": "scripts/backup_data.py",
                "commit_path": "backups/",
                "commit_msg": "chore: daily data backup [skip ci]",
            },
            {
                "name": "weekly_report",
                "title": "Weekly Analytics Report Cron",
                "schedule": "'0 9 * * 1'",
                "script": "scripts/generate_report.py",
                "commit_path": "reports/",
                "commit_msg": "chore: weekly analytics report [skip ci]",
            },
            {
                "name": "monthly_cleanup",
                "title": "Monthly Data Cleanup Cron",
                "schedule": "'0 0 1 * *'",
                "script": "scripts/cleanup_old_data.py",
                "commit_path": "data/",
                "commit_msg": "chore: monthly data cleanup [skip ci]",
            },
        ],
    },
}

AI_PROMPTS_VARIANTS = {
    "system_prompt_assistant.md": {
        "variant_key": "system_prompt",
        "domains": [
            {
                "name": "coding_tutor",
                "title": "Coding Tutor System Prompt",
                "role": "patient coding tutor",
                "specialization": "teaching programming to beginners",
                "style": "encouraging, step-by-step, uses analogies",
                "constraints": "Never give the full solution directly. Use Socratic questioning.",
            },
            {
                "name": "security_auditor",
                "title": "Security Auditor System Prompt",
                "role": "cybersecurity auditor",
                "specialization": "code review for vulnerabilities",
                "style": "thorough, methodical, references OWASP Top 10",
                "constraints": "Always check for injection, auth bypass, and data exposure.",
            },
            {
                "name": "technical_writer",
                "title": "Technical Writer System Prompt",
                "role": "senior technical writer",
                "specialization": "API documentation and developer guides",
                "style": "clear, concise, example-driven",
                "constraints": "Every explanation must include a code example. Use active voice.",
            },
            {
                "name": "data_scientist",
                "title": "Data Scientist System Prompt",
                "role": "data scientist",
                "specialization": "statistical analysis and ML model selection",
                "style": "precise, quantitative, skeptical of claims without evidence",
                "constraints": "Always state assumptions. Report confidence intervals.",
            },
            {
                "name": "product_manager",
                "title": "Product Manager System Prompt",
                "role": "senior product manager",
                "specialization": "feature prioritization and user story writing",
                "style": "outcome-focused, data-driven, customer-empathetic",
                "constraints": "Frame everything in terms of user value. Reference metrics.",
            },
        ],
    },
    "code_generator.md": {
        "variant_key": "codegen",
        "domains": [
            {
                "name": "cli_tool",
                "title": "CLI Tool Code Generator",
                "role": "CLI tool developer",
                "specialization": "building command-line applications with argparse",
                "style": "practical, includes --help text, exit codes",
                "constraints": "Must include argument parsing, colored output, and error handling.",
            },
            {
                "name": "fastapi_endpoint",
                "title": "FastAPI Endpoint Generator",
                "role": "backend API developer",
                "specialization": "building REST endpoints with FastAPI",
                "style": "follows OpenAPI spec, includes Pydantic models",
                "constraints": "Must include request validation, error responses, and docs.",
            },
            {
                "name": "test_suite",
                "title": "Test Suite Code Generator",
                "role": "QA engineer",
                "specialization": "writing comprehensive test suites with pytest",
                "style": "thorough, covers edge cases, uses fixtures",
                "constraints": "Must include unit tests, integration tests, and parametrized cases.",
            },
            {
                "name": "discord_bot",
                "title": "Discord Bot Code Generator",
                "role": "Discord bot developer",
                "specialization": "building bots with discord.py",
                "style": "event-driven, includes slash commands",
                "constraints": "Must handle permissions, rate limits, and graceful shutdown.",
            },
        ],
    },
}

SOLARPUNK_CONFIGS_VARIANTS = {
    "engine_template.md": {
        "variant_key": "engine",
        "domains": [
            {
                "name": "monitor_engine",
                "title": "Monitor Engine Template",
                "purpose": "Watch a resource and alert on changes",
                "reads": "data/monitored_resource.json",
                "writes": "data/monitor_alerts.json",
                "schedule": "Every 5 minutes",
            },
            {
                "name": "transformer_engine",
                "title": "Data Transformer Engine Template",
                "purpose": "Transform data from one format to another",
                "reads": "data/raw_input.json",
                "writes": "data/transformed_output.json",
                "schedule": "On-demand",
            },
            {
                "name": "publisher_engine",
                "title": "Publisher Engine Template",
                "purpose": "Publish content to external platforms",
                "reads": "data/publish_queue.json",
                "writes": "data/publish_log.json",
                "schedule": "Every hour",
            },
            {
                "name": "aggregator_engine",
                "title": "Aggregator Engine Template",
                "purpose": "Combine data from multiple engines into a summary",
                "reads": "data/*_report.json",
                "writes": "data/aggregated_summary.json",
                "schedule": "After each OMNIBUS cycle",
            },
        ],
    },
    "wire_pattern.md": {
        "variant_key": "wire",
        "domains": [
            {
                "name": "revenue_wire",
                "title": "Revenue Pipeline Wire Pattern",
                "purpose": "Connect product creation to deployment to sales tracking",
                "chain": "PRODUCT_FORGE -> GUMROAD_DEPLOYER -> REVENUE_TRACKER",
                "shared_files": "product_forge_report.json, gumroad_state.json",
            },
            {
                "name": "content_wire",
                "title": "Content Pipeline Wire Pattern",
                "purpose": "Connect writing to publishing to amplification",
                "chain": "ARTICLE_WRITER -> DEVTO_PUBLISHER -> AMPLIFY_ENGINE",
                "shared_files": "article_drafts.json, devto_state.json",
            },
            {
                "name": "health_wire",
                "title": "Health Monitoring Wire Pattern",
                "purpose": "Connect health checks to healing to topology updates",
                "chain": "AUTO_HEALER -> TOPOLOGY_MAPPER -> OBSERVATORY",
                "shared_files": "auto_healer_report.json, topology_state.json",
            },
            {
                "name": "feedback_wire",
                "title": "Feedback Loop Wire Pattern",
                "purpose": "Connect analytics to optimization to re-evaluation",
                "chain": "ANALYTICS_ENGINE -> VALUE_ROUTER -> CORTEX",
                "shared_files": "analytics_state.json, value_router_state.json",
            },
        ],
    },
}


# Map top-level domain names to their variant specs
ALL_VARIANT_SPECS = {
    "python-automation": PYTHON_AUTOMATION_VARIANTS,
    "github-actions": GITHUB_ACTIONS_VARIANTS,
    "ai-prompts": AI_PROMPTS_VARIANTS,
    "solarpunk-configs": SOLARPUNK_CONFIGS_VARIANTS,
}


def generate_variant_content(source_template, domain, variant_spec):
    """Generate a domain-specific variant of a template."""
    lines = []
    lines.append("# %s" % domain["title"])
    lines.append("")
    lines.append("*Variant of: %s*" % source_template)
    lines.append("*Domain: %s*" % domain["name"])
    lines.append("*Generated: %s*" % datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    lines.append("")

    vk = variant_spec["variant_key"]

    # Different variant formats based on variant_key
    if vk == "scraper":
        lines.append("## Target")
        lines.append("- URL: `%s`" % domain.get("target_url", "N/A"))
        lines.append("- Selectors: %s" % domain.get("selectors", "N/A"))
        lines.append("- Fields: %s" % domain.get("fields", "N/A"))
        lines.append("")
        lines.append("## Setup")
        lines.append("```python")
        lines.append(domain.get("imports", "import requests"))
        lines.append("```")
        lines.append("")
        lines.append("## Implementation")
        lines.append("```python")
        lines.append("TARGET_URL = '%s'" % domain.get("target_url", ""))
        lines.append("FIELDS = %s" % repr(domain.get("fields", "").split(", ")))
        lines.append("")
        lines.append("def scrape_%s(url=TARGET_URL):" % domain["name"])
        lines.append('    """Scrape %s data from target."""' % domain["name"])
        lines.append("    headers = {'User-Agent': 'SolarPunkBot/1.0'}")
        lines.append("    resp = requests.get(url, headers=headers, timeout=15)")
        lines.append("    resp.raise_for_status()")
        lines.append("    # Parse response based on domain")
        lines.append("    return resp.text[:500]  # Placeholder")
        lines.append("```")
        lines.append("")
        lines.append("## Notes")
        lines.append(domain.get("notes", ""))

    elif vk == "api_client":
        lines.append("## API Details")
        lines.append("- Base URL: `%s`" % domain.get("target_url", "N/A"))
        lines.append("- Fields: %s" % domain.get("fields", "N/A"))
        lines.append("")
        lines.append("## Setup")
        lines.append("```python")
        lines.append(domain.get("imports", "import requests, json"))
        lines.append("```")
        lines.append("")
        lines.append("## Client")
        lines.append("```python")
        lines.append("BASE_URL = '%s'" % domain.get("target_url", ""))
        lines.append("")
        lines.append("class %sClient:" % domain["name"].replace("_", " ").title().replace(" ", ""))
        lines.append("    def __init__(self, api_key=None):")
        lines.append("        self.base_url = BASE_URL")
        lines.append("        self.session = requests.Session()")
        lines.append("        if api_key:")
        lines.append("            self.session.headers['Authorization'] = 'Bearer ' + api_key")
        lines.append("")
        lines.append("    def fetch(self, endpoint='/', params=None):")
        lines.append("        resp = self.session.get(self.base_url + endpoint, params=params, timeout=30)")
        lines.append("        resp.raise_for_status()")
        lines.append("        return resp.json()")
        lines.append("```")
        lines.append("")
        lines.append("## Notes")
        lines.append(domain.get("notes", ""))

    elif vk == "etl":
        lines.append("## Pipeline")
        lines.append("- Source: %s" % domain.get("target_url", "N/A"))
        lines.append("- Fields: %s" % domain.get("fields", "N/A"))
        lines.append("")
        lines.append("## Setup")
        lines.append("```python")
        lines.append(domain.get("imports", "import json"))
        lines.append("```")
        lines.append("")
        lines.append("## Pipeline Code")
        lines.append("```python")
        lines.append("class %sPipeline:" % domain["name"].replace("_", " ").title().replace(" ", ""))
        lines.append("    def __init__(self):")
        lines.append("        self.data = []")
        lines.append("        self.errors = 0")
        lines.append("")
        lines.append("    def extract(self, source):")
        lines.append("        # Domain-specific extraction")
        lines.append("        return self")
        lines.append("")
        lines.append("    def transform(self, record):")
        lines.append("        # Domain-specific transformation")
        lines.append("        return record")
        lines.append("")
        lines.append("    def load(self, dest):")
        lines.append("        # Domain-specific loading")
        lines.append("        return len(self.data)")
        lines.append("```")
        lines.append("")
        lines.append("## Notes")
        lines.append(domain.get("notes", ""))

    elif vk == "ci":
        lines.append("## Configuration")
        lines.append("- Runner: `%s`" % domain.get("runner", "ubuntu-latest"))
        lines.append("- Setup: `%s`" % domain.get("setup", "N/A"))
        lines.append("")
        lines.append("## Workflow")
        lines.append("```yaml")
        lines.append("name: %s" % domain["title"])
        lines.append("on:")
        lines.append("  push:")
        lines.append("    branches: [main]")
        lines.append("  pull_request:")
        lines.append("    branches: [main]")
        lines.append("")
        lines.append("jobs:")
        lines.append("  test:")
        lines.append("    runs-on: %s" % domain.get("runner", "ubuntu-latest"))
        lines.append("    steps:")
        lines.append("      - uses: actions/checkout@v4")
        lines.append("      - name: Setup")
        lines.append("        uses: %s" % domain.get("setup", "N/A"))
        lines.append("      - name: Install")
        lines.append("        run: %s" % domain.get("install", "echo install"))
        lines.append("      - name: Test")
        lines.append("        run: %s" % domain.get("test_cmd", "echo test"))
        lines.append("      - name: Lint")
        lines.append("        run: %s" % domain.get("lint_cmd", "echo lint"))
        lines.append("```")

    elif vk == "cron":
        lines.append("## Schedule")
        lines.append("- Cron: `%s`" % domain.get("schedule", "N/A"))
        lines.append("- Script: `%s`" % domain.get("script", "N/A"))
        lines.append("")
        lines.append("## Workflow")
        lines.append("```yaml")
        lines.append("name: %s" % domain["title"])
        lines.append("on:")
        lines.append("  schedule:")
        lines.append("    - cron: %s" % domain.get("schedule", "'0 * * * *'"))
        lines.append("  workflow_dispatch: {}")
        lines.append("")
        lines.append("jobs:")
        lines.append("  run:")
        lines.append("    runs-on: ubuntu-latest")
        lines.append("    steps:")
        lines.append("      - uses: actions/checkout@v4")
        lines.append("      - uses: actions/setup-python@v5")
        lines.append("        with:")
        lines.append("          python-version: '3.12'")
        lines.append("      - name: Run script")
        lines.append("        run: python %s" % domain.get("script", "scripts/run.py"))
        lines.append("      - name: Commit changes")
        lines.append("        run: |")
        lines.append("          git config user.name 'github-actions[bot]'")
        lines.append("          git config user.email '41898282+github-actions[bot]@users.noreply.github.com'")
        lines.append("          git add %s" % domain.get("commit_path", "data/"))
        lines.append("          git diff --staged --quiet || git commit -m '%s'" % domain.get("commit_msg", "chore: update"))
        lines.append("          git push")
        lines.append("```")

    elif vk == "system_prompt":
        lines.append("## Persona")
        lines.append("- Role: %s" % domain.get("role", "assistant"))
        lines.append("- Specialization: %s" % domain.get("specialization", "general"))
        lines.append("- Style: %s" % domain.get("style", "helpful"))
        lines.append("")
        lines.append("## Prompt")
        lines.append("```")
        lines.append("You are a %s." % domain.get("role", "helpful assistant"))
        lines.append("")
        lines.append("## Specialization")
        lines.append("Your expertise is in %s." % domain.get("specialization", "general topics"))
        lines.append("")
        lines.append("## Communication Style")
        lines.append("%s" % domain.get("style", "Be helpful and clear."))
        lines.append("")
        lines.append("## Constraints")
        lines.append("%s" % domain.get("constraints", "Answer accurately."))
        lines.append("```")

    elif vk == "codegen":
        lines.append("## Context")
        lines.append("- Role: %s" % domain.get("role", "developer"))
        lines.append("- Specialization: %s" % domain.get("specialization", "general"))
        lines.append("")
        lines.append("## Prompt")
        lines.append("```")
        lines.append("You are a %s specializing in %s." % (
            domain.get("role", "developer"),
            domain.get("specialization", "software development"),
        ))
        lines.append("")
        lines.append("Style: %s" % domain.get("style", "practical"))
        lines.append("")
        lines.append("Constraints:")
        lines.append("%s" % domain.get("constraints", "Write clean, tested code."))
        lines.append("")
        lines.append("Generate production-ready code following these guidelines.")
        lines.append("```")

    elif vk == "engine":
        lines.append("## Engine Specification")
        lines.append("- Purpose: %s" % domain.get("purpose", ""))
        lines.append("- Reads: `%s`" % domain.get("reads", ""))
        lines.append("- Writes: `%s`" % domain.get("writes", ""))
        lines.append("- Schedule: %s" % domain.get("schedule", "on-demand"))
        lines.append("")
        lines.append("## Template")
        lines.append("```python")
        lines.append("# NEURAL_LINK: The")
        lines.append("# Part of the Meeko SolarPunk Swarm.")
        lines.append("")
        lines.append("import json")
        lines.append("from pathlib import Path")
        lines.append("from datetime import datetime, timezone")
        lines.append("")
        lines.append("BASE = Path(__file__).resolve().parent.parent")
        lines.append("DATA = BASE / 'data'")
        lines.append("DATA.mkdir(exist_ok=True)")
        lines.append("")
        engine_upper = domain["name"].upper()
        lines.append("INPUT = DATA / '%s'" % domain.get("reads", "input.json").split("/")[-1])
        lines.append("OUTPUT = DATA / '%s'" % domain.get("writes", "output.json").split("/")[-1])
        lines.append("")
        lines.append("def run():")
        lines.append("    print('[%s] %s')" % (engine_upper, domain.get("purpose", "Running")))
        lines.append("    # Implementation here")
        lines.append("    print('[%s] Complete.')" % engine_upper)
        lines.append("")
        lines.append("if __name__ == '__main__':")
        lines.append("    run()")
        lines.append("```")

    elif vk == "wire":
        lines.append("## Wire Specification")
        lines.append("- Purpose: %s" % domain.get("purpose", ""))
        lines.append("- Chain: `%s`" % domain.get("chain", ""))
        lines.append("- Shared files: `%s`" % domain.get("shared_files", ""))
        lines.append("")
        lines.append("## Wire Definition")
        lines.append("```python")
        chain_parts = domain.get("chain", "A -> B").split(" -> ")
        lines.append("WIRE_%s = [" % domain["name"].upper())
        for i in range(len(chain_parts) - 1):
            lines.append("    {")
            lines.append("        'source': '%s'," % chain_parts[i].strip())
            lines.append("        'target': '%s'," % chain_parts[i + 1].strip())
            lines.append("        'wire_type': 'data_flow',")
            shared = domain.get("shared_files", "state.json").split(", ")
            sf = shared[i] if i < len(shared) else shared[-1]
            lines.append("        'shared_file': '%s'," % sf)
            lines.append("    },")
        lines.append("]")
        lines.append("```")

    else:
        lines.append("## Details")
        for k, v in domain.items():
            if k != "name" and k != "title":
                lines.append("- %s: %s" % (k, v))

    return "\n".join(lines)


def run():
    """Generate fractal variants of all templates."""
    print("[FRACTAL_REPLICATOR] Starting fractal replication...")
    print("=" * 60)

    tracking = load_json(TRACKING_FILE)
    if not isinstance(tracking, dict):
        tracking = {}
    generated_hashes = tracking.get("generated_hashes", [])

    report = {
        "engine": "FRACTAL_REPLICATOR",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "domains_processed": {},
        "total_variants": 0,
        "total_skipped": 0,
        "total_new": 0,
    }

    for domain_name, variant_specs in ALL_VARIANT_SPECS.items():
        domain_dir = PRODUCTS / domain_name
        variants_dir = domain_dir / "variants"
        variants_dir.mkdir(parents=True, exist_ok=True)

        domain_results = {"templates": {}, "new": 0, "skipped": 0}

        print("\n[Domain: %s]" % domain_name)

        for source_template, spec in variant_specs.items():
            template_results = []
            print("  Source: %s" % source_template)

            for domain in spec["domains"]:
                variant_filename = "%s_%s.md" % (
                    spec["variant_key"],
                    domain["name"],
                )
                variant_path = variants_dir / variant_filename

                content = generate_variant_content(source_template, domain, spec)
                content_hash = file_hash(content)

                # Dedup check
                if content_hash in generated_hashes:
                    print("    [skip] %s (already generated)" % variant_filename)
                    domain_results["skipped"] += 1
                    report["total_skipped"] += 1
                    template_results.append({
                        "filename": variant_filename,
                        "status": "skipped",
                        "reason": "duplicate",
                    })
                    continue

                variant_path.write_text(content, encoding="utf-8")
                generated_hashes.append(content_hash)
                domain_results["new"] += 1
                report["total_new"] += 1
                report["total_variants"] += 1
                print("    [+] %s" % variant_filename)
                template_results.append({
                    "filename": variant_filename,
                    "status": "created",
                    "size_bytes": variant_path.stat().st_size,
                })

            domain_results["templates"][source_template] = template_results

        report["domains_processed"][domain_name] = domain_results

    # Save tracking for dedup
    tracking["generated_hashes"] = generated_hashes
    tracking["last_run"] = datetime.now(timezone.utc).isoformat()
    save_json(TRACKING_FILE, tracking)

    # Save report
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    save_json(REPORT_FILE, report)

    print("\n" + "=" * 60)
    print("[FRACTAL_REPLICATOR] Complete!")
    print("  Total variants: %d" % report["total_variants"])
    print("  New:            %d" % report["total_new"])
    print("  Skipped:        %d" % report["total_skipped"])
    print("  Domains:        %d" % len(report["domains_processed"]))
    print("  Report:         %s" % REPORT_FILE)


if __name__ == "__main__":
    run()
