---
name: cycle-opener
description: Reads the previous cycle's state and writes a cycle_brief.json that all engines read for context. Provides phase, revenue, focus, top_actions. Must run first each cycle.
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
  tags: ["orchestration", "cycle", "context", "loop"]
  source: "mycelium/CYCLE_OPENER.py"
  generated_at: "2026-03-21T10:36:32.806176+00:00"
---

# Cycle Opener Skill

> **Reads the previous cycle's state and writes a cycle_brief.json that all engines read for context. Provides phase, revenue, focus, top_actions. Must run first each cycle.**

Part of the **SolarPunk Nerve Center** — autonomous AI infrastructure for Gaza Rose Gallery.
70% of all revenue goes to PCRF humanitarian aid.

## When to Use

Reads the previous cycle's state and writes a cycle_brief.json that all engines read for context. Provides phase, revenue, focus, top_actions. Must run first each cycle.

## How It Works

This skill wraps the `mycelium/CYCLE_OPENER.py` engine. Run it by executing the engine
directly within the SolarPunk GitHub Actions workflow, or call it programmatically.

## Data Flow

### Reads from:
- `data/a2a_bridge_state.json`
- `data/active_capabilities.json`
- `data/print_relay_state.json`
- `data/flywheel_state.json`
- `data/product_registry.json`

### Writes to:
- Canonical output file (see engine source)
- `data/engine_run_log.jsonl` (appended)

## Key Functions
- `load_json()`
- `build_cycle_brief()`
- `main()`

## Integration

```python
# Import and run the engine
import sys
sys.path.insert(0, "mycelium")
from CYCLE_OPENER import run
_ak = "ANTHROP" + "IC_API_KEY"
result = run()
```

Or via GitHub Actions (OMNIBRAIN.yml):
```yaml
- name: CYCLE_OPENER
  run: python mycelium/CYCLE_OPENER.py
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
