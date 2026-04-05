# Social Media Profile Scraper

*Variant of: web_scraper_requests.md*
*Domain: social_media*
*Generated: 2026-04-05*

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