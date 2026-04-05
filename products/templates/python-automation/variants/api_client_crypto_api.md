# Cryptocurrency Price API Client

*Variant of: api_client_rest.md*
*Domain: crypto_api*
*Generated: 2026-04-05*

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