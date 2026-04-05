# Engine State Machine Pattern

Track engine lifecycle through defined states.

```python
import json
from pathlib import Path
from datetime import datetime, timezone

STATES = ['idle', 'running', 'success', 'error', 'cooldown']
TRANSITIONS = {
    'idle': ['running'],
    'running': ['success', 'error'],
    'success': ['idle', 'cooldown'],
    'error': ['idle'],
    'cooldown': ['idle'],
}

class EngineState:
    def __init__(self, engine_name, state_dir):
        self.name = engine_name
        self.path = Path(state_dir) / ('%s_lifecycle.json' % engine_name.lower())
        self.state = 'idle'
        self.history = []

    def transition(self, new_state):
        if new_state not in TRANSITIONS.get(self.state, []):
            raise ValueError(
                'Invalid transition: %s -> %s' % (self.state, new_state)
            )
        self.history.append({
            'from': self.state,
            'to': new_state,
            'at': datetime.now(timezone.utc).isoformat(),
        })
        self.state = new_state
        self._save()

    def _save(self):
        data = {
            'engine': self.name,
            'current_state': self.state,
            'history': self.history[-20:],
        }
        self.path.write_text(json.dumps(data, indent=2), encoding='utf-8')
```