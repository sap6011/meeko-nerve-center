---
name: knowledge-miner
description: >
  Deep knowledge synthesis from 13,713+ harvested files, 857 processed guides,
  and live web sources. Use when you need to extract insights from large knowledge
  bases, synthesize research from multiple sources, mine academic papers, or
  build a knowledge graph connecting concepts. Covers arXiv, Semantic Scholar,
  HackerNews, DEV.to, Wikipedia, and the SolarPunk internal knowledge base.
version: 1.0.0
license: MIT
---

# Knowledge Miner Skill

> Mine 13k+ files + live web → synthesize → feed all engines.

## Knowledge Sources

### Internal (already indexed)
- `data/consolidated_knowledge.json` — unified brain
- `data/knowledge_map.json` — knowledge graph
- `data/knowledge_graph.json` — nodes + edges
- `mycelium/MYCELIUM_KNOWLEDGE_BASE.json` — SolarPunk doctrine
- `knowledge_ingest/processed/` — 857 processed guides
- `data/harvested_knowledge/` — 13,713+ raw files
- `saves/last_good_state.json` — 145KB system snapshot

### Live (zero auth required)
- arXiv API: `https://export.arxiv.org/api/query?search_query=`
- Semantic Scholar: `https://api.semanticscholar.org/graph/v1/paper/search`
- OpenAlex: `https://api.openalex.org/works?search=`
- Wikipedia: `https://en.wikipedia.org/api/rest_v1/page/summary/`
- HackerNews: `https://hacker-news.firebaseio.com/v0/topstories.json`
- DEV.to: `https://dev.to/api/articles?tag=`

## Engines

```python
# Full knowledge synthesis pipeline
python mycelium/KNOWLEDGE_SYNTHESIZER.py   # Synthesizes all sources → knowledge_map.json
python mycelium/KNOWLEDGE_MINER.py         # Live web mining → harvested_knowledge/
python mycelium/ARCHIVE_BRAIN.py           # Processes saves/ + docs/ governance
python mycelium/ORPHAN_CONNECTOR.py        # Connects isolated data islands
python mycelium/REPO_LIBRARIAN.py          # Indexes full repo → repo_index.json
python mycelium/KNOWLEDGE_BRIDGE.py        # Bridges internal and external knowledge
python mycelium/KNOWLEDGE_CHAIN.py         # Chains knowledge for downstream engines
```

## Knowledge Graph Structure

```json
{
  "nodes": [
    {"id": "Mission", "type": "concept", "weight": 100},
    {"id": "PCRF", "type": "organization", "weight": 90},
    {"id": "Gaza_Rose_Gallery", "type": "product", "weight": 85},
    {"id": "NEURON_A", "type": "engine", "weight": 80}
  ],
  "edges": [
    {"from": "Gaza_Rose_Gallery", "to": "PCRF", "rel": "donates_70pct"},
    {"from": "NEURON_A", "to": "SYNAPSE", "rel": "reports_to"},
    {"from": "SYNAPSE", "to": "SYNTHESIS_FACTORY", "rel": "seeds"}
  ]
}
```

## Priority Knowledge Files

| File | Content | Priority |
|------|---------|----------|
| `COMPLETE_AUTONOMY_GUIDE.md` | Full system setup | CRITICAL |
| `AI_TO_AI_HANDOFF_GUIDE.md` | AI-to-AI protocols | HIGH |
| `SHOP_SETUP.md` | Gaza Rose Gallery setup | HIGH |
| `MYCELIUM_KNOWLEDGE_BASE.json` | SolarPunk doctrine | CRITICAL |
| `MANIFESTO.md` | Mission + values | HIGH |
| `CONVENTIONS.md` | Code conventions | MEDIUM |

## Integration
Knowledge output feeds:
- `CYCLE_OPENER.py` — injects knowledge_map into cycle_brief
- `SYNAPSE.py` — uses knowledge for brain synthesis
- `NEURON_A/B.py` — knowledge-informed state analysis
- `GRANT_WRITER.py` — knowledge for grant writing context
- `INVESTOR_RADAR.py` — knowledge for pitch generation
