# Event Bus Pattern

Lightweight event system for engine-to-engine communication.

```python
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path(__file__).resolve().parent.parent / 'data'
EVENT_LOG = DATA / 'event_bus_log.json'

def emit_event(source, event_type, payload=None):
    log = []
    if EVENT_LOG.exists():
        try:
            log = json.loads(EVENT_LOG.read_text(encoding='utf-8'))
        except Exception:
            log = []
    event = {
        'source': source,
        'type': event_type,
        'payload': payload or {},
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'consumed_by': [],
    }
    log.append(event)
    # Keep last 100 events
    log = log[-100:]
    EVENT_LOG.write_text(json.dumps(log, indent=2), encoding='utf-8')
    return event

def poll_events(consumer, event_type=None, limit=10):
    if not EVENT_LOG.exists():
        return []
    log = json.loads(EVENT_LOG.read_text(encoding='utf-8'))
    results = []
    for evt in reversed(log):
        if consumer in evt.get('consumed_by', []):
            continue
        if event_type and evt['type'] != event_type:
            continue
        results.append(evt)
        if len(results) >= limit:
            break
    return results
```