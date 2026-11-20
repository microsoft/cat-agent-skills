# JSON output schema

```json
{
  "title": "string",
  "status": "verified|indicative|incomplete",
  "currency": "EUR",
  "price_as_of": "YYYY-MM-DD",
  "executive_summary": ["string"],
  "assumptions": [
    {"name": "string", "value": "string", "source": "user|file|api|assumption"}
  ],
  "architecture": {
    "summary": "string",
    "components": [
      {"service": "string", "purpose": "string", "region": "string"}
    ]
  },
  "line_items": [
    {
      "service": "string",
      "region": "string",
      "sku_or_meter": "string",
      "quantity": 0,
      "unit": "string",
      "unit_price": 0,
      "monthly_cost": 0,
      "annual_cost": 0,
      "price_type": "string",
      "source": "string",
      "status": "verified|derived|assumption|open"
    }
  ],
  "totals": {"monthly": 0, "annual": 0, "one_time": 0},
  "scenarios": [],
  "finops_recommendations": [],
  "risks": [],
  "exclusions": [],
  "open_questions": []
}
```

Enter only available and reliable values. Do not fake missing numbers with zero; instead mark the line as `open` and add it to `open_questions`.
