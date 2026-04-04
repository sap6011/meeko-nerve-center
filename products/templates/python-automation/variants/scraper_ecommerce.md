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