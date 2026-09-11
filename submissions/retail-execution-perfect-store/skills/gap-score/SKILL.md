---
name: gap-score
description: 'Scores perfect-store compliance deterministically from the visit audit answers with the visit_score engine - photos attach as evidence, never scored by vision. Use after the visit: "score the visit", "how compliant is the store".'
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Field Sales}
---
# Gap Score
## Purpose
Deterministic pass/fail per criterion (#1.1); compliance % is coverage, not value (#1.2).
## When to use
After the audit answers arrive.
## Inputs
visit.json (audit answers + photo refs) + config/perfect-store-standards.json.
## Steps
1. Run scripts/visit_score.py --visit visit.json --standards perfect-store-standards.json --out scored.json
2. Quote per-criterion results verbatim; photos are referenced as evidence only (#3.1) - the plugin never claims to have "seen" a shelf.
## Output
scored.json - the {compliance} hop.
## Grounding requirements
Every criterion cites the standard version and its audit answer.
## Constraints
- No partial credit unless the standard defines it; no vision scoring (Wave 3).
## Escalation / uncertainty
Missing standard blocks scoring (#5).
