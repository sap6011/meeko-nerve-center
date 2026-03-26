---
name: revenue-flywheel
description: Tracks Gaza Rose Gallery revenue streams (Gumroad, Ko-fi, PayPal). Use when you need the current revenue balance, per-stream totals, or want to trigger a revenue reconciliation cycle.
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
  tags: ["revenue", "gumroad", "kofi", "fundraising", "financial"]
  source: "mycelium/REVENUE_FLYWHEEL.py"
  generated_at: "2026-03-20T22:24:02.258640+00:00"
---

# Revenue Flywheel Skill

> **Tracks Gaza Rose Gallery revenue streams (Gumroad, Ko-fi, PayPal). Use when you need the current revenue balance, per-stream totals, or want to trigger a revenue reconciliation cycle.**

Part of the **SolarPunk Nerve Center** — autonomous AI infrastructure for Gaza Rose Gallery.
70% of all revenue goes to PCRF humanitarian aid.

## When to Use

Tracks Gaza Rose Gallery revenue streams (Gumroad, Ko-fi, PayPal). Use when you need the current revenue balance, per-stream totals, or want to trigger a revenue reconciliation cycle.

## How It Works

This skill wraps the `mycelium/REVENUE_FLYWHEEL.py` engine. Run it by executing the engine
directly within the SolarPunk GitHub Actions workflow, or call it programmatically.

## Data Flow

### Reads from:
- `data/kofi_state.json`
- `data/first_sale_state.json`
- `data/revenue_audit.json`
- `data/gumroad_state.json`

### Writes to:
- Canonical output file (see engine source)
- `data/engine_run_log.jsonl` (appended)

## Key Functions
- `load()`
- `advise()`
- `run()`

## Integration

```python
# Import and run the engine
import sys
sys.path.insert(0, "mycelium")
from REVENUE_FLYWHEEL import run
_ak = "ANTHROP" + "IC_API_KEY"
result = run()
```

Or via GitHub Actions (OMNIBRAIN.yml):
```yaml
- name: REVENUE_FLYWHEEL
  run: python mycelium/REVENUE_FLYWHEEL.py
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
