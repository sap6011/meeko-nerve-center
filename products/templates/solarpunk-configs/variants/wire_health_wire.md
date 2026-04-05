# Health Monitoring Wire Pattern

*Variant of: wire_pattern.md*
*Domain: health_wire*
*Generated: 2026-04-05*

## Wire Specification
- Purpose: Connect health checks to healing to topology updates
- Chain: `AUTO_HEALER -> TOPOLOGY_MAPPER -> OBSERVATORY`
- Shared files: `auto_healer_report.json, topology_state.json`

## Wire Definition
```python
WIRE_HEALTH_WIRE = [
    {
        'source': 'AUTO_HEALER',
        'target': 'TOPOLOGY_MAPPER',
        'wire_type': 'data_flow',
        'shared_file': 'auto_healer_report.json',
    },
    {
        'source': 'TOPOLOGY_MAPPER',
        'target': 'OBSERVATORY',
        'wire_type': 'data_flow',
        'shared_file': 'topology_state.json',
    },
]
```