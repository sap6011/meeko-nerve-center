# SolarPunk Engine Template

Boilerplate for creating a new engine in the nerve center.

```python
# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / 'data'
DATA.mkdir(exist_ok=True)

STATE_FILE = DATA / 'ENGINE_NAME_state.json'

def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception:
        return {}

def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8'
    )

def run():
    print('[ENGINE_NAME] Starting...')
    state = load_json(STATE_FILE)
    # -- your logic here --
    state['last_run'] = datetime.now(timezone.utc).isoformat()
    save_json(STATE_FILE, state)
    print('[ENGINE_NAME] Complete.')

if __name__ == '__main__':
    run()
```