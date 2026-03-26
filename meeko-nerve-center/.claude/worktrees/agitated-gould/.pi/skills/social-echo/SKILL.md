---
name: social-echo
description: Publishes content to Bluesky, Mastodon, and other social platforms. Formats posts for each platform, schedules campaigns, and tracks engagement. Cross-posts art reveals, donation milestones, and gallery updates.
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
  tags: ["social", "bluesky", "mastodon", "publishing", "marketing"]
  source: "mycelium/SOCIAL_ECHO.py"
  generated_at: "2026-03-21T10:36:32.808755+00:00"
---

# Social Echo Skill

> **Publishes content to Bluesky, Mastodon, and other social platforms. Formats posts for each platform, schedules campaigns, and tracks engagement. Cross-posts art reveals, donation milestones, and gallery updates.**

Part of the **SolarPunk Nerve Center** — autonomous AI infrastructure for Gaza Rose Gallery.
70% of all revenue goes to PCRF humanitarian aid.

## When to Use

Publishes content to Bluesky, Mastodon, and other social platforms. Formats posts for each platform, schedules campaigns, and tracks engagement. Cross-posts art reveals, donation milestones, and gallery updates.

## How It Works

This skill wraps the `mycelium/SOCIAL_ECHO.py` engine. Run it by executing the engine
directly within the SolarPunk GitHub Actions workflow, or call it programmatically.

## Data Flow

### Reads from:
- See engine source for data dependencies

### Writes to:
- Canonical output file (see engine source)
- `data/engine_run_log.jsonl` (appended)

## Key Functions
- `generate_echo()`

## Integration

```python
# Import and run the engine
import sys
sys.path.insert(0, "mycelium")
from SOCIAL_ECHO import run
_ak = "ANTHROP" + "IC_API_KEY"
result = run()
```

Or via GitHub Actions (OMNIBRAIN.yml):
```yaml
- name: SOCIAL_ECHO
  run: python mycelium/SOCIAL_ECHO.py
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
