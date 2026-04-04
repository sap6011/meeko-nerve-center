# Batch File Renamer

Rename files in bulk using patterns and regex.

```python
import re, os
from pathlib import Path

def batch_rename(directory, pattern, replacement, dry_run=True):
    """Rename files matching regex pattern."""
    renamed = []
    for f in Path(directory).iterdir():
        if f.is_file():
            new_name = re.sub(pattern, replacement, f.name)
            if new_name != f.name:
                new_path = f.parent / new_name
                if dry_run:
                    renamed.append(('%s -> %s' % (f.name, new_name)))
                else:
                    f.rename(new_path)
                    renamed.append(('%s -> %s' % (f.name, new_name)))
    return renamed

if __name__ == '__main__':
    # Example: remove 'copy_' prefix from files
    results = batch_rename('.', r'^copy_', '', dry_run=True)
    for r in results:
        print('  ' + r)
    print('Total: %d files (dry run)' % len(results))
```