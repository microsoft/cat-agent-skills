---
name: line-normalize
description: Normalises extracted order lines - whitespace, casing, UOM tokens, qty formats - without changing meaning, preparing them for validation. Use after order-ingest.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Commerce}
---
# Line Normalize
## Purpose
Make lines machine-comparable (CS-24 -> CS24, "5 hundred" -> 500) while preserving the customer's intent verbatim in a raw field.
## When to use
After order-ingest in every run.
## Inputs
order.json.
## Steps
1. Normalise tokens; keep raw_value alongside every normalised field.
2. Never resolve an alias to a product or "fix" a price - normalisation is formatting, not judgment.
## Output
order.json with normalised lines.
## Grounding requirements
raw_value preserved per field.
## Constraints
- Formatting only; ambiguity survives normalisation for the validator to catch.
## Escalation / uncertainty
Token it cannot normalise deterministically -> left raw + flagged.
