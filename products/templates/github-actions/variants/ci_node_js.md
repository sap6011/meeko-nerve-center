# Node.js CI/CD Test Pipeline

*Variant of: ci_python_test.md*
*Domain: node_js*
*Generated: 2026-04-04*

## Configuration
- Runner: `ubuntu-latest`
- Setup: `actions/setup-node@v4 with node-version: ['18', '20', '22']`

## Workflow
```yaml
name: Node.js CI/CD Test Pipeline
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
        uses: actions/setup-node@v4 with node-version: ['18', '20', '22']
      - name: Install
        run: npm ci
      - name: Test
        run: npm test
      - name: Lint
        run: npx eslint .
```