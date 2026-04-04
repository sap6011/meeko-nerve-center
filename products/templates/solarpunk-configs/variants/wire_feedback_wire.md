# Feedback Loop Wire Pattern

*Variant of: wire_pattern.md*
*Domain: feedback_wire*
*Generated: 2026-04-04*

## Wire Specification
- Purpose: Connect analytics to optimization to re-evaluation
- Chain: `ANALYTICS_ENGINE -> VALUE_ROUTER -> CORTEX`
- Shared files: `analytics_state.json, value_router_state.json`

## Wire Definition
```python
WIRE_FEEDBACK_WIRE = [
    {
        'source': 'ANALYTICS_ENGINE',
        'target': 'VALUE_ROUTER',
        'wire_type': 'data_flow',
        'shared_file': 'analytics_state.json',
    },
    {
        'source': 'VALUE_ROUTER',
        'target': 'CORTEX',
        'wire_type': 'data_flow',
        'shared_file': 'value_router_state.json',
    },
]
```