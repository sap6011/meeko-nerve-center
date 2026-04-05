# Engine Bridge Pattern

Connect two engines via shared JSON state files.

```python
# Bridge: ENGINE_A -> shared_state.json -> ENGINE_B

import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path(__file__).resolve().parent.parent / 'data'

class Bridge:
    def __init__(self, source_engine, dest_engine, state_file):
        self.source = source_engine
        self.dest = dest_engine
        self.state_path = DATA / state_file

    def emit(self, payload):
        state = {
            'source': self.source,
            'dest': self.dest,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'payload': payload,
            'consumed': False,
        }
        self.state_path.write_text(
            json.dumps(state, indent=2), encoding='utf-8'
        )

    def consume(self):
        if not self.state_path.exists():
            return None
        state = json.loads(self.state_path.read_text(encoding='utf-8'))
        if state.get('consumed'):
            return None
        state['consumed'] = True
        self.state_path.write_text(
            json.dumps(state, indent=2), encoding='utf-8'
        )
        return state['payload']

# Usage:
# producer: Bridge('SCRAPER', 'ANALYZER', 'scraper_bridge.json').emit({'urls': [...]})
# consumer: data = Bridge('SCRAPER', 'ANALYZER', 'scraper_bridge.json').consume()
```