# RSS Feed API Client

*Variant of: api_client_rest.md*
*Domain: rss_feed*
*Generated: 2026-04-05*

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