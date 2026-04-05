# Automated Release Drafter

Auto-draft releases from merged PRs.

```yaml
name: Release Drafter
on:
  push:
    branches: [main]
  pull_request:
    types: [opened, reopened, synchronize]

permissions:
  contents: read
  pull-requests: write

jobs:
  update_release_draft:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: release-drafter/release-drafter@v6
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Create `.github/release-drafter.yml`:
```yaml
name-template: 'v$RESOLVED_VERSION'
tag-template: 'v$RESOLVED_VERSION'
categories:
  - title: 'Features'
    labels: ['enhancement']
  - title: 'Bug Fixes'
    labels: ['bug']
change-template: '- $TITLE @$AUTHOR (#$NUMBER)'
template: |
  ## Changes
  $CHANGES
```