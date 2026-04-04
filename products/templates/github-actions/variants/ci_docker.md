# Docker Build and Test Pipeline

*Variant of: ci_python_test.md*
*Domain: docker*
*Generated: 2026-04-04*

## Configuration
- Runner: `ubuntu-latest`
- Setup: `docker/setup-buildx-action@v3`

## Workflow
```yaml
name: Docker Build and Test Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup
        uses: docker/setup-buildx-action@v3
      - name: Install
        run: docker build -t app:test .
      - name: Test
        run: docker run --rm app:test pytest
      - name: Lint
        run: hadolint Dockerfile
```