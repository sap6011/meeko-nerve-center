# JSON Output Enforcer Prompt

Force the model to output valid JSON every time.

```
You must respond ONLY with valid JSON. No markdown, no explanation, no preamble.

Output Schema:
{
  "status": "success" | "error",
  "data": {
    "result": "<your analysis>",
    "confidence": 0.0-1.0,
    "reasoning": "<brief explanation>"
  },
  "metadata": {
    "model": "<model name>",
    "timestamp": "<ISO 8601>"
  }
}

Rules:
- All string values must be properly escaped
- Numbers must not be quoted
- No trailing commas
- No comments in the JSON
- If you cannot answer, set status to error and explain in data.result
```