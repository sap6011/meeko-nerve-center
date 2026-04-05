# Weather API Client

*Variant of: api_client_rest.md*
*Domain: weather_api*
*Generated: 2026-04-05*

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