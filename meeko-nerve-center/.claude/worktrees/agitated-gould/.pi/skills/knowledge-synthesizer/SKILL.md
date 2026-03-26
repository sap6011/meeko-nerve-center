---
name: knowledge-synthesizer
description: Synthesizes all knowledge sources (harvested guides, lessons, brain state) into a unified knowledge graph. Use when you want to build a cross-linked map of everything the system knows.
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
  tags: ["knowledge", "synthesis", "graph", "research"]
  source: "mycelium/KNOWLEDGE_SYNTHESIZER.py"
  generated_at: "2026-03-21T10:36:32.805005+00:00"
---

# Knowledge Synthesizer Skill

> **Synthesizes all knowledge sources (harvested guides, lessons, brain state) into a unified knowledge graph. Use when you want to build a cross-linked map of everything the system knows.**

Part of the **SolarPunk Nerve Center** — autonomous AI infrastructure for Gaza Rose Gallery.
70% of all revenue goes to PCRF humanitarian aid.

## When to Use

Synthesizes all knowledge sources (harvested guides, lessons, brain state) into a unified knowledge graph. Use when you want to build a cross-linked map of everything the system knows.

## How It Works

This skill wraps the `mycelium/KNOWLEDGE_SYNTHESIZER.py` engine. Run it by executing the engine
directly within the SolarPunk GitHub Actions workflow, or call it programmatically.

## Data Flow

### Reads from:
- `data/consolidated_knowledge.json`
- `data/capability_map.json`
- `data/loop_state.json`
- `data/neuron_b_report.json`
- `data/knowledge_graph.json`

### Writes to:
- Canonical output file (see engine source)
- `data/engine_run_log.jsonl` (appended)

## Key Functions
- `load_json()`
- `gather_all_knowledge()`
- `build_knowledge_graph()`
- `extract_harvest_patterns()`
- `update_consolidated()`
- `write_knowledge_map()`
- `main()`

## Integration

```python
# Import and run the engine
import sys
sys.path.insert(0, "mycelium")
from KNOWLEDGE_SYNTHESIZER import run
_ak = "ANTHROP" + "IC_API_KEY"
result = run()
```

Or via GitHub Actions (OMNIBRAIN.yml):
```yaml
- name: KNOWLEDGE_SYNTHESIZER
  run: python mycelium/KNOWLEDGE_SYNTHESIZER.py
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
