---
name: bom-impact
description: Traces the change across the BOM with where-used and rolls up form/fit/function impact, interface violations, document updates and inventory disposition - deterministically. Use when the user says "what does this change affect", "run where-used", "impact analysis", or after ecr-ingest in a change run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Engineering}
---
# BOM Impact
## Purpose
Deterministic impact: where_used traces every parent; bom_impact classifies impact (#1), applies the interface rule (#2), the document rule (#3) and inventory disposition (#4).
## When to use
After ecr-ingest in every change run.
## Inputs
ecr.json + bom.json + docs.json + inventory.json.
## Steps
1. Validate against the contract.
2. Run scripts/where_used.py --ecr ecr.json --bom bom.json --out traced.json
3. Run scripts/bom_impact.py --traced traced.json --docs docs.json --inventory inventory.json --out impact.json
4. Quote the rollup verbatim. An INTERFACE VIOLATION escalation is never softened - a "cheaper tolerance" on a mated feature is a function change, whatever the ECR calls it.
## Output
impact.json - the {impact} hop.
## Grounding requirements
Every affected item cites its BOM link; every document row cites the register and rule #3.
## Constraints
- All tracing and classification happens in the engines; the model never re-classes an impact.
## Escalation / uncertainty
Incomplete trace (#5), obsolete referencing documents (#3): engine escalates; the ECN stays blocked.
