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