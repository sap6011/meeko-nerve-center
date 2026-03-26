---
name: capability-broker
description: Checks which API secrets are set, determines which engines can run, and generates priority actions for unlocking new capabilities. Use when diagnosing why certain engines are inactive.
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
  tags: ["capabilities", "secrets", "api-keys", "diagnostics"]
  source: "mycelium/CAPABILITY_BROKER.py"
  generated_at: "2026-03-20T22:24:02.260357+00:00"
---

# Capability Broker Skill

> **Checks which API secrets are set, determines which engines can run, and generates priority actions for unlocking new capabilities. Use when diagnosing why certain engines are inactive.**

Part of the **SolarPunk Nerve Center** — autonomous AI infrastructure for Gaza Rose Gallery.
70% of all revenue goes to PCRF humanitarian aid.

## When to Use

Checks which API secrets are set, determines which engines can run, and generates priority actions for unlocking new capabilities. Use when diagnosing why certain engines are inactive.

## How It Works

This skill wraps the `mycelium/CAPABILITY_BROKER.py` engine. Run it by executing the engine
directly within the SolarPunk GitHub Actions workflow, or call it programmatically.

## Data Flow

### Reads from:
- `data/active_capabilities.json`
- `data/capability_map.json`
- `data/capability_brief.json`

### Writes to:
- Canonical output file (see engine source)
- `data/engine_run_log.jsonl` (appended)

## Key Functions
- `load_json()`
- `check_capabilities()`
- `build_active_engines()`
- `build_action_list()`
- `main()`

## Integration

```python
# Import and run the engine
import sys
sys.path.insert(0, "mycelium")
from CAPABILITY_BROKER import run
_ak = "ANTHROP" + "IC_API_KEY"
result = run()
```

Or via GitHub Actions (OMNIBRAIN.yml):
```yaml
- name: CAPABILITY_BROKER
  run: python mycelium/CAPABILITY_BROKER.py
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
