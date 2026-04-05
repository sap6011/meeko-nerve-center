# CSV File Processor Pipeline

Batch process CSV files with filtering, transformation, and output.

```python
import csv, json
from pathlib import Path

def process_csv(input_path, output_path, transform_fn=None, filter_fn=None):
    """Process a CSV: filter rows, transform columns, write output."""
    rows = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if filter_fn and not filter_fn(row):
                continue
            if transform_fn:
                row = transform_fn(row)
            rows.append(row)

    if not rows:
        print('No rows matched filters.')
        return 0

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)

# Example: keep rows where 'status' == 'active', uppercase names
def my_filter(row):
    return row.get('status') == 'active'

def my_transform(row):
    row['name'] = row.get('name', '').upper()
    return row

if __name__ == '__main__':
    count = process_csv('input.csv', 'output.csv', my_transform, my_filter)
    print('Processed %d rows' % count)
```