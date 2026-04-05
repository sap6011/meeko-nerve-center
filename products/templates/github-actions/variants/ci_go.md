# Go CI/CD Test Pipeline

*Variant of: ci_python_test.md*
*Domain: go*
*Generated: 2026-04-05*

## Configuration
- Runner: `ubuntu-latest`
- Setup: `actions/setup-go@v5 with go-version: '1.22'`

## Workflow
```yaml
name: Go CI/CD Test Pipeline
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
        uses: actions/setup-go@v5 with go-version: '1.22'
      - name: Install
        run: go mod download
      - name: Test
        run: go test ./... -v -race
      - name: Lint
        run: go vet ./...
```