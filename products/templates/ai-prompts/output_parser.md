# Structured Output Parser Prompt

Extract structured data from unstructured text.

```
Extract the following fields from the text below.
Return ONLY a JSON object with these fields:

Required fields:
  "name": string,
  "date": string (ISO 8601),
  "amount": number,
  "category": string (one of: income, expense, transfer),
  "notes": string (empty string if not found)

Rules:
- If a field cannot be determined, use null
- Dates should be normalized to YYYY-MM-DD format
- Amounts should be numeric (no currency symbols)
- Category must be one of the specified values

Text to parse:
[INSERT TEXT HERE]
```