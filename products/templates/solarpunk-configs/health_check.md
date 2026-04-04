# Engine Health Check Pattern

Standard health verification for any engine.

```python
import json, importlib, sys
from pathlib import Path
from datetime import datetime, timezone

def check_engine_health(engine_path):
    results = {
        'engine': engine_path.stem,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'checks': {},
    }
    # 1. File exists
    results['checks']['exists'] = engine_path.exists()

    # 2. Syntax valid
    try:
        compile(engine_path.read_text(encoding='utf-8'), str(engine_path), 'exec')
        results['checks']['syntax'] = True
    except SyntaxError as e:
        results['checks']['syntax'] = str(e)

    # 3. Has run() function
    text = engine_path.read_text(encoding='utf-8')
    results['checks']['has_run'] = 'def run(' in text

    # 4. Has main guard
    results['checks']['has_main'] = "__name__" in text and "__main__" in text

    # Overall
    checks = results['checks']
    results['healthy'] = all(
        v is True for v in checks.values()
    )
    return results
```