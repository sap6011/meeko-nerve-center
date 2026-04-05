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