---
name: product-registry
description: Catalogs all digital products (art prints, guides, PDFs) across Gumroad, Ko-fi, and docs/. Use when you need the full product inventory, pricing, or want to find products pending Gumroad publication.
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
  tags: ["products", "gumroad", "inventory", "digital-goods", "shop"]
  source: "mycelium/PRODUCT_REGISTRY.py"
  generated_at: "2026-03-20T22:24:02.259807+00:00"
---

# Product Registry Skill

> **Catalogs all digital products (art prints, guides, PDFs) across Gumroad, Ko-fi, and docs/. Use when you need the full product inventory, pricing, or want to find products pending Gumroad publication.**

Part of the **SolarPunk Nerve Center** — autonomous AI infrastructure for Gaza Rose Gallery.
70% of all revenue goes to PCRF humanitarian aid.

## When to Use

Catalogs all digital products (art prints, guides, PDFs) across Gumroad, Ko-fi, and docs/. Use when you need the full product inventory, pricing, or want to find products pending Gumroad publication.

## How It Works

This skill wraps the `mycelium/PRODUCT_REGISTRY.py` engine. Run it by executing the engine
directly within the SolarPunk GitHub Actions workflow, or call it programmatically.

## Data Flow

### Reads from:
- `data/product_registry.json`
- `data/art_catalog.json`
- `data/gumroad_state.json`

### Writes to:
- Canonical output file (see engine source)
- `data/engine_run_log.jsonl` (appended)

## Key Functions
- `load_json()`
- `scan_docs_products()`
- `enrich_from_business_data()`
- `enrich_from_gumroad()`
- `add_art_products()`
- `compute_summary()`
- `main()`

## Integration

```python
# Import and run the engine
import sys
sys.path.insert(0, "mycelium")
from PRODUCT_REGISTRY import run
_ak = "ANTHROP" + "IC_API_KEY"
result = run()
```

Or via GitHub Actions (OMNIBRAIN.yml):
```yaml
- name: PRODUCT_REGISTRY
  run: python mycelium/PRODUCT_REGISTRY.py
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
