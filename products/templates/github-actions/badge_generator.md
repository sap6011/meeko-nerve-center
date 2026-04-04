# Dynamic Badge Generator

Generate and update repo badges from code metrics.

```yaml
name: Update Badges
on:
  push:
    branches: [main]

jobs:
  badges:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Count engines
        id: count
        run: |
          COUNT=$(ls mycelium/*.py | wc -l)
          echo "engine_count=$COUNT" >> $GITHUB_OUTPUT
      - name: Create badge
        uses: schneegans/dynamic-badges-action@v1.7.0
        with:
          auth: ${{ secrets.GIST_TOKEN }}
          gistID: YOUR_GIST_ID
          filename: engines.json
          label: engines
          message: ${{ steps.count.outputs.engine_count }}
          color: brightgreen
```