# Directory File Watcher

Poll a directory for new or changed files and react.

```python
import time, os, json
from pathlib import Path

class FileWatcher:
    def __init__(self, watch_dir, extensions=None):
        self.watch_dir = Path(watch_dir)
        self.extensions = extensions or ['*']
        self.seen = {}

    def scan(self):
        changes = {'new': [], 'modified': []}
        for ext in self.extensions:
            pattern = '**/*.' + ext if ext != '*' else '**/*'
            for p in self.watch_dir.glob(pattern):
                if p.is_file():
                    mtime = p.stat().st_mtime
                    key = str(p)
                    if key not in self.seen:
                        changes['new'].append(key)
                    elif self.seen[key] < mtime:
                        changes['modified'].append(key)
                    self.seen[key] = mtime
        return changes

    def watch(self, callback, interval=5):
        print('Watching %s ...' % self.watch_dir)
        while True:
            changes = self.scan()
            if changes['new'] or changes['modified']:
                callback(changes)
            time.sleep(interval)

if __name__ == '__main__':
    def on_change(changes):
        print('Detected: %s' % json.dumps(changes, indent=2))
    watcher = FileWatcher('.', extensions=['py', 'json'])
    print('File watcher ready. %d extensions tracked.' % len(watcher.extensions))
```