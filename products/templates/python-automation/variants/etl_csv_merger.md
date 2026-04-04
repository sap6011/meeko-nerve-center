# Multi-CSV Merger ETL Pipeline

*Variant of: data_pipeline_etl.md*
*Domain: csv_merger*
*Generated: 2026-04-04*

## Pipeline
- Source: N/A (local CSV files)
- Fields: All columns from source CSVs, unified schema

## Setup
```python
import json, csv, glob
from pathlib import Path
from datetime import datetime, timezone
```

## Pipeline Code
```python
class CsvMergerPipeline:
    def __init__(self):
        self.data = []
        self.errors = 0

    def extract(self, source):
        # Domain-specific extraction
        return self

    def transform(self, record):
        # Domain-specific transformation
        return record

    def load(self, dest):
        # Domain-specific loading
        return len(self.data)
```

## Notes
Merges CSVs with different schemas. Fills missing columns with null.