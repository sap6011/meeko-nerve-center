# Weekly Analytics Report Cron

*Variant of: scheduled_data_fetch.md*
*Domain: weekly_report*
*Generated: 2026-04-04*

## Schedule
- Cron: `'0 9 * * 1'`
- Script: `scripts/generate_report.py`

## Workflow
```yaml
name: Weekly Analytics Report Cron
on:
  schedule:
    - cron: '0 9 * * 1'
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
        run: python scripts/generate_report.py
      - name: Commit changes
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
          git add reports/
          git diff --staged --quiet || git commit -m 'chore: weekly analytics report [skip ci]'
          git push
```