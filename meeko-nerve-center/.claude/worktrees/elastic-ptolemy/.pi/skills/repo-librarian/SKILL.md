---
name: repo-librarian
description: Indexes the entire repository: all engines, data files, workflows, docs, and scripts. Identifies gaps (unread data, orphan engines, stale files). Use for repo health audits.
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
  tags: ["index", "audit", "repository", "health", "gaps"]
  source: "mycelium/REPO_LIBRARIAN.py"
  generated_at: "2026-03-20T22:24:02.264925+00:00"
---

# Repo Librarian Skill

> **Indexes the entire repository: all engines, data files, workflows, docs, and scripts. Identifies gaps (unread data, orphan engines, stale files). Use for repo health audits.**

Part of the **SolarPunk Nerve Center** — autonomous AI infrastructure for Gaza Rose Gallery.
70% of all revenue goes to PCRF humanitarian aid.

## When to Use

Indexes the entire repository: all engines, data files, workflows, docs, and scripts. Identifies gaps (unread data, orphan engines, stale files). Use for repo health audits.

## How It Works

This skill wraps the `mycelium/REPO_LIBRARIAN.py` engine. Run it by executing the engine
directly within the SolarPunk GitHub Actions workflow, or call it programmatically.

## Data Flow

### Reads from:
- `data/lessons.json`
- `data/active_capabilities.json`
- `data/consolidated_knowledge.json`
- `data/capability_map.json`
- `data/knowledge_graph.json`

### Writes to:
- Canonical output file (see engine source)
- `data/engine_run_log.jsonl` (appended)

## Key Functions
- `load_json()`
- `age_days()`
- `index_engines()`
- `index_data_files()`
- `index_docs()`
- `index_workflows()`
- `index_knowledge()`
- `index_scripts()`

## Integration

```python
# Import and run the engine
import sys
sys.path.insert(0, "mycelium")
from REPO_LIBRARIAN import run
_ak = "ANTHROP" + "IC_API_KEY"
result = run()
```

Or via GitHub Actions (OMNIBRAIN.yml):
```yaml
- name: REPO_LIBRARIAN
  run: python mycelium/REPO_LIBRARIAN.py
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
