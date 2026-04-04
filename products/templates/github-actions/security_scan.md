# Security Dependency Scan

Scan dependencies for known vulnerabilities on every PR.

```yaml
name: Security Scan
on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 8 * * 1'  # Monday 8am

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install and audit
        run: |
          pip install pip-audit safety
          pip-audit --strict || true
          safety check --full-report || true
      - name: Check for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified
```