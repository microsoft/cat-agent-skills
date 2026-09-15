---
name: avl-compare
description: Compares the candidate against the approved vendor list and category requirements and produces the banded recommendation, using the deterministic avl_match engine. Use when the user says "how do they compare to our current vendors", "check the AVL", "should we qualify them", or after risk-score in a run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Supply Chain}
---
# AVL Compare
## Purpose
Deterministic AVL comparison (incumbents, regional diversity, dual-source position) and the #5 recommendation banding with named conditions.
## When to use
After risk-score in every run.
## Inputs
scored.json + approved vendor list export.
## Steps
1. Validate against the contract.
2. Run scripts/avl_match.py --scored scored.json --avl avl.json --out compared.json
3. Quote the outcome and conditions verbatim; conditions are engine-derived from the escalations, never invented or dropped.
## Output
compared.json - the {avl, recommendation} hop.
## Grounding requirements
AVL facts cite the vendor-list export; the outcome cites rule #5.
## Constraints
- The model never upgrades an outcome; a do_not_qualify stands unless the commodity council overrides in writing (#5).
## Escalation / uncertainty
Concentration (#3.1) and PPAP (#4.1) conditions are mandatory when flagged.
