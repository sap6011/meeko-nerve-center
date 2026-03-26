---
name: labor-dispatch-engine
description: Posts physical-world tasks to Rentahuman.ai with $SOLARPUNK credit rewards. Handles escrow, VerifyHuman confirmation, and tracks river monitoring, print dropoffs, and community outreach tasks.
version: "1.0.0"
license: MIT
compatibility:
  - pi
  - openclaw
  - claude-code
metadata:
  solarpunk: true
  mission: "Gaza Rose Gallery — 70% to PCRF humanitarian aid"
  agent_identity: "Cuyahoga-Prime-Node"
  tags: ["labor", "rentahuman", "physical-tasks", "humanitarian", "mutual-aid"]
  source: "mycelium/LABOR_DISPATCH_ENGINE.py"
  generated_at: "2026-03-20T22:24:02.263550+00:00"
---

# Labor Dispatch Engine Skill

> **Posts physical-world tasks to Rentahuman.ai with $SOLARPUNK credit rewards. Handles escrow, VerifyHuman confirmation, and tracks river monitoring, print dropoffs, and community outreach tasks.**

Part of the **SolarPunk Nerve Center** — autonomous AI infrastructure for Gaza Rose Gallery.
70% of all revenue goes to PCRF humanitarian aid.

## When to Use

Posts physical-world tasks to Rentahuman.ai with $SOLARPUNK credit rewards. Handles escrow, VerifyHuman confirmation, and tracks river monitoring, print dropoffs, and community outreach tasks.

## How It Works

This skill wraps the `mycelium/LABOR_DISPATCH_ENGINE.py` engine. Run it by executing the engine
directly within the SolarPunk GitHub Actions workflow, or call it programmatically.

## Data Flow

### Reads from:
- See engine source for data dependencies

### Writes to:
- Canonical output file (see engine source)
- `data/engine_run_log.jsonl` (appended)

## Key Functions
- `_api_post()`
- `_api_get()`
- `escrow_funds()`
- `post_task()`
- `check_task_completions()`
- `load_dispatch_state()`
- `run()`

## Integration

```python
# Import and run the engine
import sys
sys.path.insert(0, "mycelium")
from LABOR_DISPATCH_ENGINE import run
_ak = "ANTHROP" + "IC_API_KEY"
result = run()
```

Or via GitHub Actions (OMNIBRAIN.yml):
```yaml
- name: LABOR_DISPATCH_ENGINE
  run: python mycelium/LABOR_DISPATCH_ENGINE.py
  env:
    ANTHROP_IC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Mission Context

This engine is part of the complete SolarPunk autonomous loop:
`CYCLE_OPENER → [all engines] → LOOP_CONDUCTOR → loop_state.json → next cycle`

All autonomous revenue generated funds:
- 70% → PCRF (Palestine Children's Relief Fund)
- 30% → SolarPunk infrastructure (this system)

## License

MIT — Free to use, modify, and share.
