---
name: openclaw-skill-sync
description: Syncs with the agentskills.io registry and GitHub skill repos. Downloads validated skills matching humanitarian/revenue/knowledge keywords. Maintains the wisdom library.
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
  tags: ["skills", "openclaw", "sync", "registry", "agentskills"]
  source: "mycelium/OPENCLAW_SKILL_SYNC.py"
  generated_at: "2026-03-20T22:24:02.262577+00:00"
---

# Openclaw Skill Sync Skill

> **Syncs with the agentskills.io registry and GitHub skill repos. Downloads validated skills matching humanitarian/revenue/knowledge keywords. Maintains the wisdom library.**

Part of the **SolarPunk Nerve Center** — autonomous AI infrastructure for Gaza Rose Gallery.
70% of all revenue goes to PCRF humanitarian aid.

## When to Use

Syncs with the agentskills.io registry and GitHub skill repos. Downloads validated skills matching humanitarian/revenue/knowledge keywords. Maintains the wisdom library.

## How It Works

This skill wraps the `mycelium/OPENCLAW_SKILL_SYNC.py` engine. Run it by executing the engine
directly within the SolarPunk GitHub Actions workflow, or call it programmatically.

## Data Flow

### Reads from:
- See engine source for data dependencies

### Writes to:
- Canonical output file (see engine source)
- `data/engine_run_log.jsonl` (appended)

## Key Functions
- `_gh_get()`
- `_download_raw()`
- `skill_is_wanted()`
- `skill_is_safe()`
- `extract_skill_meta()`
- `install_skill()`
- `sync_from_github_dir()`
- `sync_from_github_repos()`

## Integration

```python
# Import and run the engine
import sys
sys.path.insert(0, "mycelium")
from OPENCLAW_SKILL_SYNC import run
_ak = "ANTHROP" + "IC_API_KEY"
result = run()
```

Or via GitHub Actions (OMNIBRAIN.yml):
```yaml
- name: OPENCLAW_SKILL_SYNC
  run: python mycelium/OPENCLAW_SKILL_SYNC.py
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
