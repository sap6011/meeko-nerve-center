---
name: loop-conductor
description: Synthesizes all engine outputs at end of cycle, identifies what succeeded/failed, and writes loop_state.json for the next cycle. Closes the feedback loop.
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
  tags: ["orchestration", "loop", "synthesis", "feedback"]
  source: "mycelium/LOOP_CONDUCTOR.py"
  generated_at: "2026-03-21T10:36:32.806703+00:00"
---

# Loop Conductor Skill

> **Synthesizes all engine outputs at end of cycle, identifies what succeeded/failed, and writes loop_state.json for the next cycle. Closes the feedback loop.**

Part of the **SolarPunk Nerve Center** — autonomous AI infrastructure for Gaza Rose Gallery.
70% of all revenue goes to PCRF humanitarian aid.

## When to Use

Synthesizes all engine outputs at end of cycle, identifies what succeeded/failed, and writes loop_state.json for the next cycle. Closes the feedback loop.

## How It Works

This skill wraps the `mycelium/LOOP_CONDUCTOR.py` engine. Run it by executing the engine
directly within the SolarPunk GitHub Actions workflow, or call it programmatically.

## Data Flow

### Reads from:
- `data/skill_siphon_state.json`
- `data/multi_repo_intelligence.json`
- `data/knowledge_graph.json`
- `data/loop_memory.json`
- `data/health_report.json`

### Writes to:
- Canonical output file (see engine source)
- `data/engine_run_log.jsonl` (appended)

## Key Functions
- `load_json()`
- `scan_engine_outputs()`
- `extract_top_actions()`
- `extract_lessons()`
- `compute_revenue_snapshot()`
- `build_cycle_summary()`
- `main()`

## Integration

```python
# Import and run the engine
import sys
sys.path.insert(0, "mycelium")
from LOOP_CONDUCTOR import run
_ak = "ANTHROP" + "IC_API_KEY"
result = run()
```

Or via GitHub Actions (OMNIBRAIN.yml):
```yaml
- name: LOOP_CONDUCTOR
  run: python mycelium/LOOP_CONDUCTOR.py
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
