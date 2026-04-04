# Stale Issue Auto-Closer

Close issues and PRs that have been inactive.

```yaml
name: Close Stale Issues
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  stale:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/stale@v9
        with:
          stale-issue-message: 'This issue has been inactive for 30 days. Closing soon.'
          stale-pr-message: 'This PR has been inactive for 14 days. Please update.'
          days-before-issue-stale: 30
          days-before-pr-stale: 14
          days-before-issue-close: 7
          days-before-pr-close: 7
          stale-issue-label: 'stale'
          stale-pr-label: 'stale'
```