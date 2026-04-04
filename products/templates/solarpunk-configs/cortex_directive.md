# Cortex Directive Configuration

The central command structure for the nerve center.

```json
{
  "directive": "maximize_revenue_and_reach",
  "priority_engines": [
    "PRODUCT_FORGE",
    "GUMROAD_DEPLOYER",
    "DEVTO_PUBLISHER"
  ],
  "constraints": {
    "max_api_calls_per_hour": 100,
    "max_git_commits_per_cycle": 5,
    "require_dry_run_first": true
  },
  "flags": {
    "enable_auto_publish": false,
    "enable_auto_deploy": false,
    "enable_revenue_tracking": true
  },
  "version": "2026-04-04"
}
```