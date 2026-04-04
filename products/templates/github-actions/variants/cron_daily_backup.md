# Daily JSON Backup Cron

*Variant of: scheduled_data_fetch.md*
*Domain: daily_backup*
*Generated: 2026-04-04*

## Schedule
- Cron: `'0 2 * * *'`
- Script: `scripts/backup_data.py`

## Workflow
```yaml
name: Daily JSON Backup Cron
on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch: {}

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Run script
        run: python scripts/backup_data.py
      - name: Commit changes
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
          git add backups/
          git diff --staged --quiet || git commit -m 'chore: daily data backup [skip ci]'
          git push
```