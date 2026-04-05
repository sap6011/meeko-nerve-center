# Monthly Data Cleanup Cron

*Variant of: scheduled_data_fetch.md*
*Domain: monthly_cleanup*
*Generated: 2026-04-05*

## Schedule
- Cron: `'0 0 1 * *'`
- Script: `scripts/cleanup_old_data.py`

## Workflow
```yaml
name: Monthly Data Cleanup Cron
on:
  schedule:
    - cron: '0 0 1 * *'
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
        run: python scripts/cleanup_old_data.py
      - name: Commit changes
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
          git add data/
          git diff --staged --quiet || git commit -m 'chore: monthly data cleanup [skip ci]'
          git push
```