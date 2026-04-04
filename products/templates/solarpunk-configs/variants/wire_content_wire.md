# Content Pipeline Wire Pattern

*Variant of: wire_pattern.md*
*Domain: content_wire*
*Generated: 2026-04-04*

## Wire Specification
- Purpose: Connect writing to publishing to amplification
- Chain: `ARTICLE_WRITER -> DEVTO_PUBLISHER -> AMPLIFY_ENGINE`
- Shared files: `article_drafts.json, devto_state.json`

## Wire Definition
```python
WIRE_CONTENT_WIRE = [
    {
        'source': 'ARTICLE_WRITER',
        'target': 'DEVTO_PUBLISHER',
        'wire_type': 'data_flow',
        'shared_file': 'article_drafts.json',
    },
    {
        'source': 'DEVTO_PUBLISHER',
        'target': 'AMPLIFY_ENGINE',
        'wire_type': 'data_flow',
        'shared_file': 'devto_state.json',
    },
]
```