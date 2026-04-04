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