# Translation API Client

*Variant of: api_client_rest.md*
*Domain: translation_api*
*Generated: 2026-04-05*

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