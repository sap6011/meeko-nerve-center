---
name: archive-brain
description: Mines saves/, docs/, and knowledge_ingest/ for wisdom and lessons. Reads governance documents (MANIFESTO, CONSTITUTION, AGENCY_MEMORY) and merges insights into the active brain loop.
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
  tags: ["archive", "knowledge", "governance", "lessons", "history"]
  source: "mycelium/ARCHIVE_BRAIN.py"
  generated_at: "2026-03-21T10:36:32.810215+00:00"
---

# Archive Brain Skill

> **Mines saves/, docs/, and knowledge_ingest/ for wisdom and lessons. Reads governance documents (MANIFESTO, CONSTITUTION, AGENCY_MEMORY) and merges insights into the active brain loop.**

Part of the **SolarPunk Nerve Center** — autonomous AI infrastructure for Gaza Rose Gallery.
70% of all revenue goes to PCRF humanitarian aid.

## When to Use

Mines saves/, docs/, and knowledge_ingest/ for wisdom and lessons. Reads governance documents (MANIFESTO, CONSTITUTION, AGENCY_MEMORY) and merges insights into the active brain loop.

## How It Works

This skill wraps the `mycelium/ARCHIVE_BRAIN.py` engine. Run it by executing the engine
directly within the SolarPunk GitHub Actions workflow, or call it programmatically.

## Data Flow

### Reads from:
- `data/archive_intelligence.json`
- `data/consolidated_knowledge.json`
- `data/lessons.json`

### Writes to:
- Canonical output file (see engine source)
- `data/engine_run_log.jsonl` (appended)

## Key Functions
- `load_json()`
- `load_text()`
- `extract_from_last_good_state()`
- `extract_from_guides()`
- `extract_from_docs_knowledge()`
- `build_archive_lessons()`
- `merge_to_consolidated()`
- `main()`

## Integration

```python
# Import and run the engine
import sys
sys.path.insert(0, "mycelium")
from ARCHIVE_BRAIN import run
_ak = "ANTHROP" + "IC_API_KEY"
result = run()
```

Or via GitHub Actions (OMNIBRAIN.yml):
```yaml
- name: ARCHIVE_BRAIN
  run: python mycelium/ARCHIVE_BRAIN.py
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
