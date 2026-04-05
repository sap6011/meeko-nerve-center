# Aggregator Engine Template

*Variant of: engine_template.md*
*Domain: aggregator_engine*
*Generated: 2026-04-05*

## Engine Specification
- Purpose: Combine data from multiple engines into a summary
- Reads: `data/*_report.json`
- Writes: `data/aggregated_summary.json`
- Schedule: After each OMNIBUS cycle

## Template
```python
# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / 'data'
DATA.mkdir(exist_ok=True)

INPUT = DATA / '*_report.json'
OUTPUT = DATA / 'aggregated_summary.json'

def run():
    print('[AGGREGATOR_ENGINE] Combine data from multiple engines into a summary')
    # Implementation here
    print('[AGGREGATOR_ENGINE] Complete.')

if __name__ == '__main__':
    run()
```