# Hourly Health Check Cron

*Variant of: scheduled_data_fetch.md*
*Domain: hourly_health*
*Generated: 2026-04-05*

## Schedule
- Cron: `'0 * * * *'`
- Script: `scripts/health_check.py`

## Workflow
```yaml
name: Hourly Health Check Cron
on:
  schedule:
    - cron: '0 * * * *'
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
        run: python scripts/health_check.py
      - name: Commit changes
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
          git add data/health/
          git diff --staged --quiet || git commit -m 'chore: update health metrics [skip ci]'
          git push
```