# Lightweight Cron Job Scheduler

Run Python functions on a schedule without external deps.

```python
import time, threading
from datetime import datetime

class CronJob:
    def __init__(self, name, fn, interval_seconds=60):
        self.name = name
        self.fn = fn
        self.interval = interval_seconds
        self.running = False
        self.run_count = 0

    def start(self):
        self.running = True
        def loop():
            while self.running:
                try:
                    self.fn()
                    self.run_count += 1
                    print('[%s] %s ran (count: %d)' % (datetime.now().isoformat(), self.name, self.run_count))
                except Exception as e:
                    print('[%s] %s error: %s' % (datetime.now().isoformat(), self.name, e))
                time.sleep(self.interval)
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        return t

    def stop(self):
        self.running = False

if __name__ == '__main__':
    def heartbeat():
        print('pulse')
    job = CronJob('heartbeat', heartbeat, interval_seconds=5)
    t = job.start()
    time.sleep(16)  # Run for 16 seconds
    job.stop()
    print('Stopped after %d runs' % job.run_count)
```