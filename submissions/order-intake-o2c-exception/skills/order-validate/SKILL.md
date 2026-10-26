---
name: order-validate
description: Validates the order against customer, pricing, product and credit masters deterministically with the order_validate engine. Use on "is this order clean", "validate before entry", after line-normalize.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Commerce}
---
# Order Validate
## Purpose
Deterministic validation: alias identity (#1.1), UOM/qty sanity (#2.1), price tolerance (#3.1), credit (#4.1).
## When to use
After line-normalize in every run.
## Inputs
order.json + config/masters.json + config/o2c-config.json.
## Steps
1. Run scripts/order_validate.py --order order.json --masters masters.json --config o2c-config.json --out validated.json
2. Quote issues verbatim. 500 EA from a cases-of-24 customer is confirmed, never keyed - the classic rekeying disaster is exactly this line (#2.1).
## Output
validated.json - the {validation} hop.
## Grounding requirements
Every issue cites the master it checked against.
## Constraints
- Validation is engine-only; "regular customer, just key it" changes nothing; the truck schedule is not a validation input.
## Escalation / uncertainty
Any issue holds the order at the configured action level (#5.1).
