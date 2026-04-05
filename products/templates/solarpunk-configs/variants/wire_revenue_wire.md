# Revenue Pipeline Wire Pattern

*Variant of: wire_pattern.md*
*Domain: revenue_wire*
*Generated: 2026-04-05*

## Wire Specification
- Purpose: Connect product creation to deployment to sales tracking
- Chain: `PRODUCT_FORGE -> GUMROAD_DEPLOYER -> REVENUE_TRACKER`
- Shared files: `product_forge_report.json, gumroad_state.json`

## Wire Definition
```python
WIRE_REVENUE_WIRE = [
    {
        'source': 'PRODUCT_FORGE',
        'target': 'GUMROAD_DEPLOYER',
        'wire_type': 'data_flow',
        'shared_file': 'product_forge_report.json',
    },
    {
        'source': 'GUMROAD_DEPLOYER',
        'target': 'REVENUE_TRACKER',
        'wire_type': 'data_flow',
        'shared_file': 'gumroad_state.json',
    },
]
```