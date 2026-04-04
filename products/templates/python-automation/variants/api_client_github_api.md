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