# OMNIBUS Configuration Template

How to add engines to the OMNIBUS orchestrator.

```json
{
  "omnibus_version": 30,
  "engine_groups": {
    "revenue": {
      "engines": [
        "PRODUCT_FORGE",
        "GUMROAD_DEPLOYER",
        "AFFILIATE_MAXIMIZER"
      ],
      "run_order": "sequential",
      "fail_mode": "continue"
    },
    "content": {
      "engines": [
        "ARTICLE_WRITER",
        "DEVTO_PUBLISHER",
        "TWEET_WRITER"
      ],
      "run_order": "sequential",
      "fail_mode": "continue"
    },
    "infrastructure": {
      "engines": [
        "AUTO_HEALER",
        "TOPOLOGY_MAPPER",
        "SELF_WIRING_ENGINE"
      ],
      "run_order": "parallel",
      "fail_mode": "log_and_continue"
    }
  },
  "schedule": "*/30 * * * *",
  "notifications": true
}
```