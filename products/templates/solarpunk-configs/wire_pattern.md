# Engine Wire Pattern (Topology)

Define typed connections between engines in the mesh.

```python
# Wire definition for TOPOLOGY_MAPPER

WIRE_DEFINITIONS = [
    {
        'source': 'PRODUCT_FORGE',
        'target': 'GUMROAD_DEPLOYER',
        'wire_type': 'data_flow',
        'shared_file': 'product_forge_report.json',
        'description': 'New products trigger deployment',
    },
    {
        'source': 'ARTICLE_WRITER',
        'target': 'DEVTO_PUBLISHER',
        'wire_type': 'data_flow',
        'shared_file': 'article_drafts.json',
        'description': 'Written articles get published',
    },
    {
        'source': 'AUTO_HEALER',
        'target': 'TOPOLOGY_MAPPER',
        'wire_type': 'health_check',
        'shared_file': 'auto_healer_report.json',
        'description': 'Health status feeds topology view',
    },
]

# Wire types: data_flow, health_check, trigger, feedback_loop
# Each wire is bidirectional-aware but flows in one direction.
```