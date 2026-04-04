# Rust CI/CD Test Pipeline

*Variant of: ci_python_test.md*
*Domain: rust*
*Generated: 2026-04-04*

## Configuration
- Runner: `ubuntu-latest`
- Setup: `dtolnay/rust-toolchain@stable`

## Workflow
```yaml
name: Rust CI/CD Test Pipeline
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
        uses: dtolnay/rust-toolchain@stable
      - name: Install
        run: cargo build
      - name: Test
        run: cargo test --verbose
      - name: Lint
        run: cargo clippy -- -D warnings
```