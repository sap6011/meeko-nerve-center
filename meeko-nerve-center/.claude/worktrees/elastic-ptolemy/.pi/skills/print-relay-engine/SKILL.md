---
name: print-relay-engine
description: Dispatches Gaza medical supply 3D print jobs via OctoEverywhere MCP. Monitors print node availability, queues humanitarian prints (prosthetics, tourniquets), and reports completions.
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
  tags: ["3d-printing", "octoeverywhere", "humanitarian", "gaza", "medical"]
  source: "mycelium/PRINT_RELAY_ENGINE.py"
  generated_at: "2026-03-20T22:24:02.263013+00:00"
---

# Print Relay Engine Skill

> **Dispatches Gaza medical supply 3D print jobs via OctoEverywhere MCP. Monitors print node availability, queues humanitarian prints (prosthetics, tourniquets), and reports completions.**

Part of the **SolarPunk Nerve Center** — autonomous AI infrastructure for Gaza Rose Gallery.
70% of all revenue goes to PCRF humanitarian aid.

## When to Use

Dispatches Gaza medical supply 3D print jobs via OctoEverywhere MCP. Monitors print node availability, queues humanitarian prints (prosthetics, tourniquets), and reports completions.

## How It Works

This skill wraps the `mycelium/PRINT_RELAY_ENGINE.py` engine. Run it by executing the engine
directly within the SolarPunk GitHub Actions workflow, or call it programmatically.

## Data Flow

### Reads from:
- See engine source for data dependencies

### Writes to:
- Canonical output file (see engine source)
- `data/engine_run_log.jsonl` (appended)

## Key Functions
- `_api_get()`
- `_api_post()`
- `get_printer_nodes()`
- `get_printer_status()`
- `queue_print_job()`
- `load_print_state()`
- `run()`

## Integration

```python
# Import and run the engine
import sys
sys.path.insert(0, "mycelium")
from PRINT_RELAY_ENGINE import run
_ak = "ANTHROP" + "IC_API_KEY"
result = run()
```

Or via GitHub Actions (OMNIBRAIN.yml):
```yaml
- name: PRINT_RELAY_ENGINE
  run: python mycelium/PRINT_RELAY_ENGINE.py
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
