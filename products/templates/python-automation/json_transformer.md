# JSON Transformer Utility

Flatten, filter, and reshape JSON data structures.

```python
import json
from pathlib import Path

def flatten_json(nested, prefix='', sep='.'):
    """Flatten a nested dict into dot-notation keys."""
    flat = {}
    for key, val in nested.items():
        new_key = prefix + sep + key if prefix else key
        if isinstance(val, dict):
            flat.update(flatten_json(val, new_key, sep))
        elif isinstance(val, list):
            for i, item in enumerate(val):
                idx_key = '%s[%d]' % (new_key, i)
                if isinstance(item, dict):
                    flat.update(flatten_json(item, idx_key, sep))
                else:
                    flat[idx_key] = item
        else:
            flat[new_key] = val
    return flat

def pick_keys(data, keys):
    """Extract only specified keys from a dict."""
    return {k: data[k] for k in keys if k in data}

if __name__ == '__main__':
    sample = {'user': {'name': 'Meeko', 'tags': ['solarpunk', 'builder']}, 'score': 99}
    print(json.dumps(flatten_json(sample), indent=2))
```