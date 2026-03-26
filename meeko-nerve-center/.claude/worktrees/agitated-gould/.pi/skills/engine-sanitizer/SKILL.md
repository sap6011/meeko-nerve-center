---
name: engine-sanitizer
description: Scans all mycelium Python files for API key corruption patterns (recursive os.getenv() nesting) and fixes them in place. Critical for repos where AI-generated code can self-corrupt.
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
  tags: ["sanitizer", "security", "corruption", "fix", "automation"]
  source: "mycelium/ENGINE_SANITIZER.py"
  generated_at: "2026-03-21T10:36:32.809464+00:00"
---

# Engine Sanitizer Skill

> **Scans all mycelium Python files for API key corruption patterns (recursive os.getenv() nesting) and fixes them in place. Critical for repos where AI-generated code can self-corrupt.**

Part of the **SolarPunk Nerve Center** — autonomous AI infrastructure for Gaza Rose Gallery.
70% of all revenue goes to PCRF humanitarian aid.

## When to Use

Scans all mycelium Python files for API key corruption patterns (recursive os.getenv() nesting) and fixes them in place. Critical for repos where AI-generated code can self-corrupt.

## How It Works

This skill wraps the `mycelium/ENGINE_SANITIZER.py` engine. Run it by executing the engine
directly within the SolarPunk GitHub Actions workflow, or call it programmatically.

## Data Flow

### Reads from:
- `data/sanitizer_report.json`

### Writes to:
- Canonical output file (see engine source)
- `data/engine_run_log.jsonl` (appended)

## Key Functions
- `_fix_line()`
- `sanitize_file()`
- `main()`

## Integration

```python
# Import and run the engine
import sys
sys.path.insert(0, "mycelium")
from ENGINE_SANITIZER import run
_ak = "ANTHROP" + "IC_API_KEY"
result = run()
```

Or via GitHub Actions (OMNIBRAIN.yml):
```yaml
- name: ENGINE_SANITIZER
  run: python mycelium/ENGINE_SANITIZER.py
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
