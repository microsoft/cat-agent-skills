---
name: readiness-check
description: Tests store readiness against the campaign pack deterministically - applicability, completeness, fixture conflicts and price integrity - with the readiness_check engine. Use when the user asks "are we ready", "any gaps for launch", "check the pack against my store".
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Store Operations}
---
# Readiness Check
## Purpose
Deterministic readiness: applicability (#1.1), completeness (#2.1), fixture conflicts (#4.1), price conflicts (#3.1/#3.2).
## When to use
After store-map in every run.
## Inputs
pack.json + store.json + shelf-prices.json.
## Steps
1. Validate against the contract.
2. Run scripts/readiness_check.py --pack pack.json --store store.json --prices shelf-prices.json --out checked.json
3. Quote statuses and the completeness % verbatim. A PRICE CONFLICT (promo >= shelf) blocks the shelf change - it is the top mispricing pattern, never "probably a typo, proceed".
## Output
checked.json - the {readiness} hop.
## Grounding requirements
Every item cites the pack line; price conflicts cite the price file rows.
## Constraints
- All tests in the engine; a conflict is never reclassified as missing to make the store look fixable.
## Escalation / uncertainty
Fixture and price conflicts escalate to HQ; the store cannot resolve them locally (#4.1).
