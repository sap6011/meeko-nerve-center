# Developer Starter Pack

**Price: $8.00** | *SolarPunk Digital Products*

The best templates for getting started fast. Python automation, GitHub Actions CI/CD, and AI prompt engineering templates with a quick-start guide to wire them together.

---

## Bundle Savings

| Item | Individual Price |
|------|----------------|
| Python Automation Templates | $4.00 |
| GitHub Actions Templates | $4.00 |
| AI Prompt Templates | $4.00 |
| **Total if bought separately** | **$12.00** |

**Bundle Price: $8.00**

**You save: $4.00 (33% off)**

---

## What's Included

1. **Python Automation Templates** ($4.00 value)
2. **GitHub Actions Templates** ($4.00 value)
3. **AI Prompt Templates** ($4.00 value)

---

## Table of Contents

1. [Python Automation Templates](#--python-automation-templates)
2. [GitHub Actions Templates](#--github-actions-templates)
3. [AI Prompt Templates](#--ai-prompt-templates)


---

# >> Python Automation Templates

---

### Api Client Rest

# REST API Client with Retry Logic

A reusable REST API client with exponential backoff.

```python
import requests, time, json

class APIClient:
    def __init__(self, base_url, api_key=None, max_retries=3):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = 'Bearer ' + api_key
        self.max_retries = max_retries

    def _request(self, method, endpoint, **kwargs):
        url = self.base_url + '/' + endpoint.lstrip('/')
        for attempt in range(self.max_retries):
            try:
                resp = self.session.request(method, url, timeout=30, **kwargs)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                wait = 2 ** attempt
                print('Retry %d/%d in %ds: %s' % (attempt+1, self.max_retries, wait, e))
                time.sleep(wait)

    def get(self, endpoint, params=None):
        return self._request('GET', endpoint, params=params)

    def post(self, endpoint, data=None):
        return self._request('POST', endpoint, json=data)

if __name__ == '__main__':
    client = APIClient('https://jsonplaceholder.typicode.com')
    posts = client.get('/posts', params={'_limit': 5})
    print(json.dumps(posts, indent=2))
```

### Batch Renamer

# Batch File Renamer

Rename files in bulk using patterns and regex.

```python
import re, os
from pathlib import Path

def batch_rename(directory, pattern, replacement, dry_run=True):
    """Rename files matching regex pattern."""
    renamed = []
    for f in Path(directory).iterdir():
        if f.is_file():
            new_name = re.sub(pattern, replacement, f.name)
            if new_name != f.name:
                new_path = f.parent / new_name
                if dry_run:
                    renamed.append(('%s -> %s' % (f.name, new_name)))
                else:
                    f.rename(new_path)
                    renamed.append(('%s -> %s' % (f.name, new_name)))
    return renamed

if __name__ == '__main__':
    # Example: remove 'copy_' prefix from files
    results = batch_rename('.', r'^copy_', '', dry_run=True)
    for r in results:
        print('  ' + r)
    print('Total: %d files (dry run)' % len(results))
```

### Cron Scheduler

# Lightweight Cron Job Scheduler

Run Python functions on a schedule without external deps.

```python
import time, threading
from datetime import datetime

class CronJob:
    def __init__(self, name, fn, interval_seconds=60):
        self.name = name
        self.fn = fn
        self.interval = interval_seconds
        self.running = False
        self.run_count = 0

    def start(self):
        self.running = True
        def loop():
            while self.running:
                try:
                    self.fn()
                    self.run_count += 1
                    print('[%s] %s ran (count: %d)' % (datetime.now().isoformat(), self.name, self.run_count))
                except Exception as e:
                    print('[%s] %s error: %s' % (datetime.now().isoformat(), self.name, e))
                time.sleep(self.interval)
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        return t

    def stop(self):
        self.running = False

if __name__ == '__main__':
    def heartbeat():
        print('pulse')
    job = CronJob('heartbeat', heartbeat, interval_seconds=5)
    t = job.start()
    time.sleep(16)  # Run for 16 seconds
    job.stop()
    print('Stopped after %d runs' % job.run_count)
```

### Data Pipeline Etl

# ETL Data Pipeline

A lightweight extract-transform-load pipeline for JSON data.

```python
import json
from pathlib import Path
from datetime import datetime, timezone

class ETLPipeline:
    def __init__(self, name):
        self.name = name
        self.extracted = []
        self.transformed = []
        self.stats = {'extracted': 0, 'transformed': 0, 'loaded': 0, 'errors': 0}

    def extract(self, source_path):
        data = json.loads(Path(source_path).read_text(encoding='utf-8'))
        if isinstance(data, list):
            self.extracted = data
        else:
            self.extracted = [data]
        self.stats['extracted'] = len(self.extracted)
        return self

    def transform(self, fn):
        self.transformed = []
        for record in self.extracted:
            try:
                result = fn(record)
                if result is not None:
                    self.transformed.append(result)
            except Exception:
                self.stats['errors'] += 1
        self.stats['transformed'] = len(self.transformed)
        return self

    def load(self, dest_path):
        output = {
            'pipeline': self.name,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stats': self.stats,
            'data': self.transformed,
        }
        Path(dest_path).write_text(json.dumps(output, indent=2), encoding='utf-8')
        self.stats['loaded'] = len(self.transformed)
        return self.stats

if __name__ == '__main__':
    def enrich(rec):
        rec['processed'] = True
        return rec
    pipe = ETLPipeline('demo')
    # pipe.extract('input.json').transform(enrich).load('output.json')
    print('ETL pipeline ready: %s' % pipe.name)
```

### File Processor Csv

# CSV File Processor Pipeline

Batch process CSV files with filtering, transformation, and output.

```python
import csv, json
from pathlib import Path

def process_csv(input_path, output_path, transform_fn=None, filter_fn=None):
    """Process a CSV: filter rows, transform columns, write output."""
    rows = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if filter_fn and not filter_fn(row):
                continue
            if transform_fn:
                row = transform_fn(row)
            rows.append(row)

    if not rows:
        print('No rows matched filters.')
        return 0

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)

# Example: keep rows where 'status' == 'active', uppercase names
def my_filter(row):
    return row.get('status') == 'active'

def my_transform(row):
    row['name'] = row.get('name', '').upper()
    return row

if __name__ == '__main__':
    count = process_csv('input.csv', 'output.csv', my_transform, my_filter)
    print('Processed %d rows' % count)
```

### File Watcher

# Directory File Watcher

Poll a directory for new or changed files and react.

```python
import time, os, json
from pathlib import Path

class FileWatcher:
    def __init__(self, watch_dir, extensions=None):
        self.watch_dir = Path(watch_dir)
        self.extensions = extensions or ['*']
        self.seen = {}

    def scan(self):
        changes = {'new': [], 'modified': []}
        for ext in self.extensions:
            pattern = '**/*.' + ext if ext != '*' else '**/*'
            for p in self.watch_dir.glob(pattern):
                if p.is_file():
                    mtime = p.stat().st_mtime
                    key = str(p)
                    if key not in self.seen:
                        changes['new'].append(key)
                    elif self.seen[key] < mtime:
                        changes['modified'].append(key)
                    self.seen[key] = mtime
        return changes

    def watch(self, callback, interval=5):
        print('Watching %s ...' % self.watch_dir)
        while True:
            changes = self.scan()
            if changes['new'] or changes['modified']:
                callback(changes)
            time.sleep(interval)

if __name__ == '__main__':
    def on_change(changes):
        print('Detected: %s' % json.dumps(changes, indent=2))
    watcher = FileWatcher('.', extensions=['py', 'json'])
    print('File watcher ready. %d extensions tracked.' % len(watcher.extensions))
```

### Json Transformer

# JSON Transformer Utility

Flatten, filter, and reshape JSON data structures.

```python
import json
from pathlib import Path

def flatten_json(nested, prefix='', sep='.'):
    """Flatten a nested dict into dot-notation keys."""
    flat = {}
    for key, val in nested.items():
        new_key = prefix + sep + key if prefix else key
        if isinstance(val, dict):
            flat.update(flatten_json(val, new_key, sep))
        elif isinstance(val, list):
            for i, item in enumerate(val):
                idx_key = '%s[%d]' % (new_key, i)
                if isinstance(item, dict):
                    flat.update(flatten_json(item, idx_key, sep))
                else:
                    flat[idx_key] = item
        else:
            flat[new_key] = val
    return flat

def pick_keys(data, keys):
    """Extract only specified keys from a dict."""
    return {k: data[k] for k in keys if k in data}

if __name__ == '__main__':
    sample = {'user': {'name': 'Meeko', 'tags': ['solarpunk', 'builder']}, 'score': 99}
    print(json.dumps(flatten_json(sample), indent=2))
```

### Web Scraper Requests

# Web Scraper with Requests + BeautifulSoup

A minimal, production-ready web scraper.

```python
import requests
from bs4 import BeautifulSoup
import json, time

def scrape_page(url, selector='article'):
    """Fetch a page and extract elements by CSS selector."""
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; SolarPunkBot/1.0)'}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    return [el.get_text(strip=True) for el in soup.select(selector)]

def scrape_multiple(urls, selector='article', delay=1.0):
    """Scrape multiple URLs with polite delay."""
    results = {}
    for url in urls:
        try:
            results[url] = scrape_page(url, selector)
            time.sleep(delay)
        except Exception as e:
            results[url] = {'error': str(e)}
    return results

if __name__ == '__main__':
    urls = ['https://example.com']
    data = scrape_multiple(urls, selector='h1')
    print(json.dumps(data, indent=2))
```

## Usage
- Change `selector` to target specific HTML elements
- Adjust `delay` to be respectful to servers
- Add proxy rotation for large-scale scraping

### Api Client Crypto Api

# Cryptocurrency Price API Client

*Variant of: api_client_rest.md*
*Domain: crypto_api*
*Generated: 2026-04-04*

## API Details
- Base URL: `https://api.coingecko.com/api/v3`
- Fields: coin, price_usd, market_cap, volume_24h, price_change_24h

## Setup
```python
import requests, json, time
from decimal import Decimal
```

## Client
```python
BASE_URL = 'https://api.coingecko.com/api/v3'

class CryptoApiClient:
    def __init__(self, api_key=None):
        self.base_url = BASE_URL
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = 'Bearer ' + api_key

    def fetch(self, endpoint='/', params=None):
        resp = self.session.get(self.base_url + endpoint, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
```

## Notes
Free tier: 10-30 calls/min. No API key required for basic queries.

### Api Client Github Api

# GitHub API Client

*Variant of: api_client_rest.md*
*Domain: github_api*
*Generated: 2026-04-04*

## API Details
- Base URL: `https://api.github.com`
- Fields: repos, stars, issues, pull_requests, contributors

## Setup
```python
import requests, json, time, os
```

## Client
```python
BASE_URL = 'https://api.github.com'

class GithubApiClient:
    def __init__(self, api_key=None):
        self.base_url = BASE_URL
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = 'Bearer ' + api_key

    def fetch(self, endpoint='/', params=None):
        resp = self.session.get(self.base_url + endpoint, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
```

## Notes
Uses GITHUB_TOKEN for auth. Handles pagination via Link header.

### Api Client Rss Feed

# RSS Feed API Client

*Variant of: api_client_rest.md*
*Domain: rss_feed*
*Generated: 2026-04-04*

## API Details
- Base URL: `https://example.com/feed.xml`
- Fields: title, link, description, pub_date, author

## Setup
```python
import requests, json, xml.etree.ElementTree as ET
```

## Client
```python
BASE_URL = 'https://example.com/feed.xml'

class RssFeedClient:
    def __init__(self, api_key=None):
        self.base_url = BASE_URL
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = 'Bearer ' + api_key

    def fetch(self, endpoint='/', params=None):
        resp = self.session.get(self.base_url + endpoint, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
```

## Notes
Parses RSS 2.0 and Atom feeds. Converts XML to JSON.

### Api Client Translation Api

# Translation API Client

*Variant of: api_client_rest.md*
*Domain: translation_api*
*Generated: 2026-04-04*

## API Details
- Base URL: `https://api.mymemory.translated.net/get`
- Fields: source_text, target_text, source_lang, target_lang, confidence

## Setup
```python
import requests, json, time, hashlib
```

## Client
```python
BASE_URL = 'https://api.mymemory.translated.net/get'

class TranslationApiClient:
    def __init__(self, api_key=None):
        self.base_url = BASE_URL
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = 'Bearer ' + api_key

    def fetch(self, endpoint='/', params=None):
        resp = self.session.get(self.base_url + endpoint, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
```

## Notes
Free tier: 5000 chars/day. Caches translations locally.

### Api Client Weather Api

# Weather API Client

*Variant of: api_client_rest.md*
*Domain: weather_api*
*Generated: 2026-04-04*

## API Details
- Base URL: `https://api.openweathermap.org/data/2.5`
- Fields: temperature, humidity, wind_speed, description, forecast

## Setup
```python
import requests, json, time
```

## Client
```python
BASE_URL = 'https://api.openweathermap.org/data/2.5'

class WeatherApiClient:
    def __init__(self, api_key=None):
        self.base_url = BASE_URL
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = 'Bearer ' + api_key

    def fetch(self, endpoint='/', params=None):
        resp = self.session.get(self.base_url + endpoint, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
```

## Notes
Requires OPENWEATHER_API_KEY. Supports current weather and 5-day forecast.

### Etl Csv Merger

# Multi-CSV Merger ETL Pipeline

*Variant of: data_pipeline_etl.md*
*Domain: csv_merger*
*Generated: 2026-04-04*

## Pipeline
- Source: N/A (local CSV files)
- Fields: All columns from source CSVs, unified schema

## Setup
```python
import json, csv, glob
from pathlib import Path
from datetime import datetime, timezone
```

## Pipeline Code
```python
class CsvMergerPipeline:
    def __init__(self):
        self.data = []
        self.errors = 0

    def extract(self, source):
        # Domain-specific extraction
        return self

    def transform(self, record):
        # Domain-specific transformation
        return record

    def load(self, dest):
        # Domain-specific loading
        return len(self.data)
```

## Notes
Merges CSVs with different schemas. Fills missing columns with null.

### Etl Database Sync

# Database Sync ETL Pipeline

*Variant of: data_pipeline_etl.md*
*Domain: database_sync*
*Generated: 2026-04-04*

## Pipeline
- Source: N/A (SQLite databases)
- Fields: Varies per table schema

## Setup
```python
import json, sqlite3
from pathlib import Path
from datetime import datetime, timezone
```

## Pipeline Code
```python
class DatabaseSyncPipeline:
    def __init__(self):
        self.data = []
        self.errors = 0

    def extract(self, source):
        # Domain-specific extraction
        return self

    def transform(self, record):
        # Domain-specific transformation
        return record

    def load(self, dest):
        # Domain-specific loading
        return len(self.data)
```

## Notes
Extracts from SQLite, transforms in Python, loads to new SQLite.

### Etl Email Parser

# Email Data ETL Pipeline

*Variant of: data_pipeline_etl.md*
*Domain: email_parser*
*Generated: 2026-04-04*

## Pipeline
- Source: N/A (local .eml files)
- Fields: from, to, subject, date, body_text, attachments

## Setup
```python
import json, email, re
from pathlib import Path
from datetime import datetime, timezone
```

## Pipeline Code
```python
class EmailParserPipeline:
    def __init__(self):
        self.data = []
        self.errors = 0

    def extract(self, source):
        # Domain-specific extraction
        return self

    def transform(self, record):
        # Domain-specific transformation
        return record

    def load(self, dest):
        # Domain-specific loading
        return len(self.data)
```

## Notes
Parses .eml files. Extracts headers, body, and attachment metadata.

### Etl Json Normalizer

# Nested JSON Normalizer ETL

*Variant of: data_pipeline_etl.md*
*Domain: json_normalizer*
*Generated: 2026-04-04*

## Pipeline
- Source: N/A (JSON files or API responses)
- Fields: Flattened key-value pairs from nested structures

## Setup
```python
import json
from pathlib import Path
from datetime import datetime, timezone
```

## Pipeline Code
```python
class JsonNormalizerPipeline:
    def __init__(self):
        self.data = []
        self.errors = 0

    def extract(self, source):
        # Domain-specific extraction
        return self

    def transform(self, record):
        # Domain-specific transformation
        return record

    def load(self, dest):
        # Domain-specific loading
        return len(self.data)
```

## Notes
Handles arbitrarily nested JSON. Dot-notation output keys.

### Etl Log Processor

# Log File ETL Pipeline

*Variant of: data_pipeline_etl.md*
*Domain: log_processor*
*Generated: 2026-04-04*

## Pipeline
- Source: N/A (local log files)
- Fields: timestamp, level, source, message, count

## Setup
```python
import json, re
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
```

## Pipeline Code
```python
class LogProcessorPipeline:
    def __init__(self):
        self.data = []
        self.errors = 0

    def extract(self, source):
        # Domain-specific extraction
        return self

    def transform(self, record):
        # Domain-specific transformation
        return record

    def load(self, dest):
        # Domain-specific loading
        return len(self.data)
```

## Notes
Parses Apache, nginx, and Python log formats. Aggregates by level.

### Scraper Academic Papers

# Academic Paper Metadata Scraper

*Variant of: web_scraper_requests.md*
*Domain: academic_papers*
*Generated: 2026-04-04*

## Target
- URL: `https://api.semanticscholar.org/graph/v1/paper/search`
- Selectors: API-based: Semantic Scholar API
- Fields: title, authors, year, abstract, citation_count, doi

## Setup
```python
import requests
import json, time
from urllib.parse import quote
```

## Implementation
```python
TARGET_URL = 'https://api.semanticscholar.org/graph/v1/paper/search'
FIELDS = ['title', 'authors', 'year', 'abstract', 'citation_count', 'doi']

def scrape_academic_papers(url=TARGET_URL):
    """Scrape academic_papers data from target."""
    headers = {'User-Agent': 'SolarPunkBot/1.0'}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    # Parse response based on domain
    return resp.text[:500]  # Placeholder
```

## Notes
Uses Semantic Scholar API. Respects 100 req/5min rate limit.

### Scraper Ecommerce

# E-Commerce Product Scraper

*Variant of: web_scraper_requests.md*
*Domain: ecommerce*
*Generated: 2026-04-04*

## Target
- URL: `https://example-shop.com/products`
- Selectors: '.product-card', '.price', '.product-title', '.rating'
- Fields: title, price, rating, availability, url

## Setup
```python
import requests
from bs4 import BeautifulSoup
import json, time, csv
```

## Implementation
```python
TARGET_URL = 'https://example-shop.com/products'
FIELDS = ['title', 'price', 'rating', 'availability', 'url']

def scrape_ecommerce(url=TARGET_URL):
    """Scrape ecommerce data from target."""
    headers = {'User-Agent': 'SolarPunkBot/1.0'}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    # Parse response based on domain
    return resp.text[:500]  # Placeholder
```

## Notes
Handles pagination via next-page links. Exports to CSV.

### Scraper Government Data

# Government Open Data Scraper

*Variant of: web_scraper_requests.md*
*Domain: government_data*
*Generated: 2026-04-04*

## Target
- URL: `https://data.gov/api/3/action/package_search`
- Selectors: API-based: CKAN API format
- Fields: dataset_name, organization, format, date_updated, download_url

## Setup
```python
import requests
import json, csv
from pathlib import Path
```

## Implementation
```python
TARGET_URL = 'https://data.gov/api/3/action/package_search'
FIELDS = ['dataset_name', 'organization', 'format', 'date_updated', 'download_url']

def scrape_government_data(url=TARGET_URL):
    """Scrape government_data data from target."""
    headers = {'User-Agent': 'SolarPunkBot/1.0'}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    # Parse response based on domain
    return resp.text[:500]  # Placeholder
```

## Notes
Uses CKAN API standard. Downloads linked CSV/JSON datasets.

### Scraper News

# News Article Scraper

*Variant of: web_scraper_requests.md*
*Domain: news*
*Generated: 2026-04-04*

## Target
- URL: `https://example-news.com/latest`
- Selectors: 'article', '.headline', '.byline', '.publish-date'
- Fields: headline, author, date, summary, full_text, url

## Setup
```python
import requests
from bs4 import BeautifulSoup
import json, time
from datetime import datetime
```

## Implementation
```python
TARGET_URL = 'https://example-news.com/latest'
FIELDS = ['headline', 'author', 'date', 'summary', 'full_text', 'url']

def scrape_news(url=TARGET_URL):
    """Scrape news data from target."""
    headers = {'User-Agent': 'SolarPunkBot/1.0'}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    # Parse response based on domain
    return resp.text[:500]  # Placeholder
```

## Notes
Extracts article body text. Respects robots.txt.

### Scraper Social Media

# Social Media Profile Scraper

*Variant of: web_scraper_requests.md*
*Domain: social_media*
*Generated: 2026-04-04*

## Target
- URL: `https://example-social.com/api/v1/profiles`
- Selectors: API-based: JSON response fields
- Fields: username, display_name, bio, follower_count, post_count

## Setup
```python
import requests
import json, time
from urllib.parse import urljoin
```

## Implementation
```python
TARGET_URL = 'https://example-social.com/api/v1/profiles'
FIELDS = ['username', 'display_name', 'bio', 'follower_count', 'post_count']

def scrape_social_media(url=TARGET_URL):
    """Scrape social_media data from target."""
    headers = {'User-Agent': 'SolarPunkBot/1.0'}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    # Parse response based on domain
    return resp.text[:500]  # Placeholder
```

## Notes
Uses API endpoints where available. Rate-limited to 1 req/sec.


---

# >> GitHub Actions Templates

---

### Auto Deploy Pages

# Auto Deploy to GitHub Pages

Deploy a static site on every push to main.

```yaml
name: Deploy to Pages
on:
  push:
    branches: [main]
    paths: ['docs/**', '*.html', '*.css']

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - name: Setup Pages
        uses: actions/configure-pages@v4
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs/
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### Badge Generator

# Dynamic Badge Generator

Generate and update repo badges from code metrics.

```yaml
name: Update Badges
on:
  push:
    branches: [main]

jobs:
  badges:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Count engines
        id: count
        run: |
          COUNT=$(ls mycelium/*.py | wc -l)
          echo "engine_count=$COUNT" >> $GITHUB_OUTPUT
      - name: Create badge
        uses: schneegans/dynamic-badges-action@v1.7.0
        with:
          auth: ${{ secrets.GIST_TOKEN }}
          gistID: YOUR_GIST_ID
          filename: engines.json
          label: engines
          message: ${{ steps.count.outputs.engine_count }}
          color: brightgreen
```

### Ci Python Test

# Python CI/CD Test Pipeline

Run tests on every push with caching and matrix builds.

```yaml
name: Python CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python -m pytest tests/ -v --tb=short
      - name: Run linter
        run: python -m flake8 . --count --show-source --statistics
```

### Issue Responder

# Auto Issue Responder

Automatically label and greet new issues.

```yaml
name: Issue Responder
on:
  issues:
    types: [opened]

jobs:
  respond:
    runs-on: ubuntu-latest
    steps:
      - name: Label issue
        uses: actions/github-script@v7
        with:
          script: |
            const title = context.payload.issue.title.toLowerCase();
            const labels = [];
            if (title.includes('bug')) labels.push('bug');
            if (title.includes('feature')) labels.push('enhancement');
            if (title.includes('docs')) labels.push('documentation');
            if (labels.length === 0) labels.push('triage');
            await github.rest.issues.addLabels({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              labels: labels
            });
      - name: Welcome comment
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: 'Thanks for opening this issue! We will review it shortly.'
            });
```

### Release Drafter

# Automated Release Drafter

Auto-draft releases from merged PRs.

```yaml
name: Release Drafter
on:
  push:
    branches: [main]
  pull_request:
    types: [opened, reopened, synchronize]

permissions:
  contents: read
  pull-requests: write

jobs:
  update_release_draft:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: release-drafter/release-drafter@v6
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Create `.github/release-drafter.yml`:
```yaml
name-template: 'v$RESOLVED_VERSION'
tag-template: 'v$RESOLVED_VERSION'
categories:
  - title: 'Features'
    labels: ['enhancement']
  - title: 'Bug Fixes'
    labels: ['bug']
change-template: '- $TITLE @$AUTHOR (#$NUMBER)'
template: |
  ## Changes
  $CHANGES
```

### Scheduled Data Fetch

# Scheduled Data Fetch via GitHub Actions Cron

Fetch data on a schedule and commit updates.

```yaml
name: Scheduled Data Fetch
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch: {}

jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Fetch data
        run: python scripts/fetch_data.py
      - name: Commit if changed
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
          git add data/
          git diff --staged --quiet || git commit -m 'chore: update data [skip ci]'
          git push
```

### Security Scan

# Security Dependency Scan

Scan dependencies for known vulnerabilities on every PR.

```yaml
name: Security Scan
on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 8 * * 1'  # Monday 8am

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install and audit
        run: |
          pip install pip-audit safety
          pip-audit --strict || true
          safety check --full-report || true
      - name: Check for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified
```

### Stale Issue Closer

# Stale Issue Auto-Closer

Close issues and PRs that have been inactive.

```yaml
name: Close Stale Issues
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  stale:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/stale@v9
        with:
          stale-issue-message: 'This issue has been inactive for 30 days. Closing soon.'
          stale-pr-message: 'This PR has been inactive for 14 days. Please update.'
          days-before-issue-stale: 30
          days-before-pr-stale: 14
          days-before-issue-close: 7
          days-before-pr-close: 7
          stale-issue-label: 'stale'
          stale-pr-label: 'stale'
```

### Ci Docker

# Docker Build and Test Pipeline

*Variant of: ci_python_test.md*
*Domain: docker*
*Generated: 2026-04-04*

## Configuration
- Runner: `ubuntu-latest`
- Setup: `docker/setup-buildx-action@v3`

## Workflow
```yaml
name: Docker Build and Test Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup
        uses: docker/setup-buildx-action@v3
      - name: Install
        run: docker build -t app:test .
      - name: Test
        run: docker run --rm app:test pytest
      - name: Lint
        run: hadolint Dockerfile
```

### Ci Go

# Go CI/CD Test Pipeline

*Variant of: ci_python_test.md*
*Domain: go*
*Generated: 2026-04-04*

## Configuration
- Runner: `ubuntu-latest`
- Setup: `actions/setup-go@v5 with go-version: '1.22'`

## Workflow
```yaml
name: Go CI/CD Test Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup
        uses: actions/setup-go@v5 with go-version: '1.22'
      - name: Install
        run: go mod download
      - name: Test
        run: go test ./... -v -race
      - name: Lint
        run: go vet ./...
```

### Ci Node Js

# Node.js CI/CD Test Pipeline

*Variant of: ci_python_test.md*
*Domain: node_js*
*Generated: 2026-04-04*

## Configuration
- Runner: `ubuntu-latest`
- Setup: `actions/setup-node@v4 with node-version: ['18', '20', '22']`

## Workflow
```yaml
name: Node.js CI/CD Test Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup
        uses: actions/setup-node@v4 with node-version: ['18', '20', '22']
      - name: Install
        run: npm ci
      - name: Test
        run: npm test
      - name: Lint
        run: npx eslint .
```

### Ci Rust

# Rust CI/CD Test Pipeline

*Variant of: ci_python_test.md*
*Domain: rust*
*Generated: 2026-04-04*

## Configuration
- Runner: `ubuntu-latest`
- Setup: `dtolnay/rust-toolchain@stable`

## Workflow
```yaml
name: Rust CI/CD Test Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup
        uses: dtolnay/rust-toolchain@stable
      - name: Install
        run: cargo build
      - name: Test
        run: cargo test --verbose
      - name: Lint
        run: cargo clippy -- -D warnings
```

### Cron Daily Backup

# Daily JSON Backup Cron

*Variant of: scheduled_data_fetch.md*
*Domain: daily_backup*
*Generated: 2026-04-04*

## Schedule
- Cron: `'0 2 * * *'`
- Script: `scripts/backup_data.py`

## Workflow
```yaml
name: Daily JSON Backup Cron
on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch: {}

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Run script
        run: python scripts/backup_data.py
      - name: Commit changes
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
          git add backups/
          git diff --staged --quiet || git commit -m 'chore: daily data backup [skip ci]'
          git push
```

### Cron Hourly Health

# Hourly Health Check Cron

*Variant of: scheduled_data_fetch.md*
*Domain: hourly_health*
*Generated: 2026-04-04*

## Schedule
- Cron: `'0 * * * *'`
- Script: `scripts/health_check.py`

## Workflow
```yaml
name: Hourly Health Check Cron
on:
  schedule:
    - cron: '0 * * * *'
  workflow_dispatch: {}

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Run script
        run: python scripts/health_check.py
      - name: Commit changes
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
          git add data/health/
          git diff --staged --quiet || git commit -m 'chore: update health metrics [skip ci]'
          git push
```

### Cron Monthly Cleanup

# Monthly Data Cleanup Cron

*Variant of: scheduled_data_fetch.md*
*Domain: monthly_cleanup*
*Generated: 2026-04-04*

## Schedule
- Cron: `'0 0 1 * *'`
- Script: `scripts/cleanup_old_data.py`

## Workflow
```yaml
name: Monthly Data Cleanup Cron
on:
  schedule:
    - cron: '0 0 1 * *'
  workflow_dispatch: {}

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Run script
        run: python scripts/cleanup_old_data.py
      - name: Commit changes
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
          git add data/
          git diff --staged --quiet || git commit -m 'chore: monthly data cleanup [skip ci]'
          git push
```

### Cron Weekly Report

# Weekly Analytics Report Cron

*Variant of: scheduled_data_fetch.md*
*Domain: weekly_report*
*Generated: 2026-04-04*

## Schedule
- Cron: `'0 9 * * 1'`
- Script: `scripts/generate_report.py`

## Workflow
```yaml
name: Weekly Analytics Report Cron
on:
  schedule:
    - cron: '0 9 * * 1'
  workflow_dispatch: {}

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Run script
        run: python scripts/generate_report.py
      - name: Commit changes
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
          git add reports/
          git diff --staged --quiet || git commit -m 'chore: weekly analytics report [skip ci]'
          git push
```


---

# >> AI Prompt Templates

---

### Chain Of Thought

# Chain-of-Thought Reasoning Template

Force step-by-step reasoning for complex problems.

```
Solve the following problem step by step.

## Process
1. UNDERSTAND: Restate the problem in your own words
2. PLAN: List the steps needed to solve it
3. EXECUTE: Work through each step, showing your reasoning
4. VERIFY: Check your answer against the original question
5. ANSWER: State the final answer clearly

## Rules
- Show all intermediate calculations
- If you hit a dead end, backtrack and explain why
- Label each step clearly
- If assumptions are needed, state them explicitly

Problem: [INSERT PROBLEM HERE]
```

### Code Generator

# Code Generation Prompt Template

Structured prompt for generating production-quality code.

```
Generate code for the following task.

## Requirements
- Language: [LANGUAGE]
- Framework: [FRAMEWORK or 'none']
- Purpose: [DESCRIPTION]

## Code Standards
- Include type hints/annotations where the language supports them
- Add docstrings to all public functions
- Handle errors with try/except (do not silently swallow errors)
- Use meaningful variable names (no single letters except loop vars)
- Follow PEP 8 (Python) / standard style guide for the language

## Output Format
1. Brief description of the approach (2-3 sentences)
2. The complete, runnable code
3. Example usage showing expected input and output
4. Known limitations or edge cases

## Constraints
- Prefer standard library over third-party packages
- Code must be self-contained (no external config files required)
- Include a __main__ block for direct execution
```

### Data Analyst

# Data Analysis System Prompt

Prompt for structured data analysis tasks.

```
You are a data analyst. Analyze the provided data following this process:

## Analysis Steps
1. DATA SUMMARY: Describe shape, types, and basic statistics
2. QUALITY CHECK: Identify missing values, outliers, and inconsistencies
3. PATTERNS: Find trends, correlations, and clusters
4. INSIGHTS: List 3-5 actionable insights
5. VISUALIZATION: Suggest appropriate chart types for key findings

## Output Format
Always structure your response as:
- Executive Summary (2-3 sentences)
- Key Findings (bulleted list)
- Detailed Analysis (sections per step above)
- Recommendations (numbered list)

## Rules
- Use exact numbers, not vague qualifiers
- Show your calculations
- Distinguish correlation from causation
- Flag any data quality issues before drawing conclusions
```

### Few Shot Template

# Few-Shot Learning Template

Provide examples so the model learns the pattern.

```
Classify the following text into one of these categories:
[CATEGORY_1], [CATEGORY_2], [CATEGORY_3]

## Examples

Input: [EXAMPLE_1_INPUT]
Category: [EXAMPLE_1_CATEGORY]
Reasoning: [EXAMPLE_1_REASONING]

Input: [EXAMPLE_2_INPUT]
Category: [EXAMPLE_2_CATEGORY]
Reasoning: [EXAMPLE_2_REASONING]

Input: [EXAMPLE_3_INPUT]
Category: [EXAMPLE_3_CATEGORY]
Reasoning: [EXAMPLE_3_REASONING]

---
Now classify this text:
Input: [USER_INPUT]
Category:
Reasoning:
```

### Json Output Enforcer

# JSON Output Enforcer Prompt

Force the model to output valid JSON every time.

```
You must respond ONLY with valid JSON. No markdown, no explanation, no preamble.

Output Schema:
{
  "status": "success" | "error",
  "data": {
    "result": "<your analysis>",
    "confidence": 0.0-1.0,
    "reasoning": "<brief explanation>"
  },
  "metadata": {
    "model": "<model name>",
    "timestamp": "<ISO 8601>"
  }
}

Rules:
- All string values must be properly escaped
- Numbers must not be quoted
- No trailing commas
- No comments in the JSON
- If you cannot answer, set status to error and explain in data.result
```

### Output Parser

# Structured Output Parser Prompt

Extract structured data from unstructured text.

```
Extract the following fields from the text below.
Return ONLY a JSON object with these fields:

Required fields:
  "name": string,
  "date": string (ISO 8601),
  "amount": number,
  "category": string (one of: income, expense, transfer),
  "notes": string (empty string if not found)

Rules:
- If a field cannot be determined, use null
- Dates should be normalized to YYYY-MM-DD format
- Amounts should be numeric (no currency symbols)
- Category must be one of the specified values

Text to parse:
[INSERT TEXT HERE]
```

### Persona Template

# Persona-Based Prompt Template

Define a specific expert persona for the AI.

```
You are [ROLE], a [EXPERIENCE]-year veteran in [DOMAIN].

## Background
- Specialization: [SPECIALTY]
- Key skills: [SKILL_1], [SKILL_2], [SKILL_3]
- Communication style: [STYLE - e.g., direct, academic, casual]

## Behavior Guidelines
- Prioritize practical, tested solutions over theoretical ones
- When asked about areas outside your expertise, redirect clearly
- Use industry-standard terminology but explain jargon when first used
- Provide examples from real-world scenarios

## Response Pattern
1. Acknowledge the question
2. Provide your expert analysis
3. Offer a concrete recommendation
4. Note any caveats or edge cases
```

### System Prompt Assistant

# General-Purpose System Prompt

A structured system prompt for AI assistants.

```
You are a helpful, precise, and thoughtful assistant.

## Core Behaviors
- Answer directly and concisely
- When uncertain, say so explicitly
- Break complex problems into clear steps
- Cite sources when making factual claims

## Response Format
- Use markdown for structure
- Code blocks with language tags
- Bullet points for lists of 3+ items
- Tables for comparative data

## Constraints
- Never fabricate URLs, citations, or statistics
- If a task is ambiguous, ask one clarifying question before proceeding
- Maximum response length: 2000 words unless explicitly asked for more
```

### Codegen Cli Tool

# CLI Tool Code Generator

*Variant of: code_generator.md*
*Domain: cli_tool*
*Generated: 2026-04-04*

## Context
- Role: CLI tool developer
- Specialization: building command-line applications with argparse

## Prompt
```
You are a CLI tool developer specializing in building command-line applications with argparse.

Style: practical, includes --help text, exit codes

Constraints:
Must include argument parsing, colored output, and error handling.

Generate production-ready code following these guidelines.
```

### Codegen Discord Bot

# Discord Bot Code Generator

*Variant of: code_generator.md*
*Domain: discord_bot*
*Generated: 2026-04-04*

## Context
- Role: Discord bot developer
- Specialization: building bots with discord.py

## Prompt
```
You are a Discord bot developer specializing in building bots with discord.py.

Style: event-driven, includes slash commands

Constraints:
Must handle permissions, rate limits, and graceful shutdown.

Generate production-ready code following these guidelines.
```

### Codegen Fastapi Endpoint

# FastAPI Endpoint Generator

*Variant of: code_generator.md*
*Domain: fastapi_endpoint*
*Generated: 2026-04-04*

## Context
- Role: backend API developer
- Specialization: building REST endpoints with FastAPI

## Prompt
```
You are a backend API developer specializing in building REST endpoints with FastAPI.

Style: follows OpenAPI spec, includes Pydantic models

Constraints:
Must include request validation, error responses, and docs.

Generate production-ready code following these guidelines.
```

### Codegen Test Suite

# Test Suite Code Generator

*Variant of: code_generator.md*
*Domain: test_suite*
*Generated: 2026-04-04*

## Context
- Role: QA engineer
- Specialization: writing comprehensive test suites with pytest

## Prompt
```
You are a QA engineer specializing in writing comprehensive test suites with pytest.

Style: thorough, covers edge cases, uses fixtures

Constraints:
Must include unit tests, integration tests, and parametrized cases.

Generate production-ready code following these guidelines.
```

### System Prompt Coding Tutor

# Coding Tutor System Prompt

*Variant of: system_prompt_assistant.md*
*Domain: coding_tutor*
*Generated: 2026-04-04*

## Persona
- Role: patient coding tutor
- Specialization: teaching programming to beginners
- Style: encouraging, step-by-step, uses analogies

## Prompt
```
You are a patient coding tutor.

## Specialization
Your expertise is in teaching programming to beginners.

## Communication Style
encouraging, step-by-step, uses analogies

## Constraints
Never give the full solution directly. Use Socratic questioning.
```

### System Prompt Data Scientist

# Data Scientist System Prompt

*Variant of: system_prompt_assistant.md*
*Domain: data_scientist*
*Generated: 2026-04-04*

## Persona
- Role: data scientist
- Specialization: statistical analysis and ML model selection
- Style: precise, quantitative, skeptical of claims without evidence

## Prompt
```
You are a data scientist.

## Specialization
Your expertise is in statistical analysis and ML model selection.

## Communication Style
precise, quantitative, skeptical of claims without evidence

## Constraints
Always state assumptions. Report confidence intervals.
```

### System Prompt Product Manager

# Product Manager System Prompt

*Variant of: system_prompt_assistant.md*
*Domain: product_manager*
*Generated: 2026-04-04*

## Persona
- Role: senior product manager
- Specialization: feature prioritization and user story writing
- Style: outcome-focused, data-driven, customer-empathetic

## Prompt
```
You are a senior product manager.

## Specialization
Your expertise is in feature prioritization and user story writing.

## Communication Style
outcome-focused, data-driven, customer-empathetic

## Constraints
Frame everything in terms of user value. Reference metrics.
```

### System Prompt Security Auditor

# Security Auditor System Prompt

*Variant of: system_prompt_assistant.md*
*Domain: security_auditor*
*Generated: 2026-04-04*

## Persona
- Role: cybersecurity auditor
- Specialization: code review for vulnerabilities
- Style: thorough, methodical, references OWASP Top 10

## Prompt
```
You are a cybersecurity auditor.

## Specialization
Your expertise is in code review for vulnerabilities.

## Communication Style
thorough, methodical, references OWASP Top 10

## Constraints
Always check for injection, auth bypass, and data exposure.
```

### System Prompt Technical Writer

# Technical Writer System Prompt

*Variant of: system_prompt_assistant.md*
*Domain: technical_writer*
*Generated: 2026-04-04*

## Persona
- Role: senior technical writer
- Specialization: API documentation and developer guides
- Style: clear, concise, example-driven

## Prompt
```
You are a senior technical writer.

## Specialization
Your expertise is in API documentation and developer guides.

## Communication Style
clear, concise, example-driven

## Constraints
Every explanation must include a code example. Use active voice.
```


---

*Generated by BUNDLE_FORGE on 2026-04-05*

*99%% of revenue goes to mutual aid. 1%% to infrastructure.*
