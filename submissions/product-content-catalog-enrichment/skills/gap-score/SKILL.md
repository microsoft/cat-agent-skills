---
name: gap-score
description: Scores per-SKU completeness against the channel's required fields with the deterministic completeness_score engine. Use on "how complete are these", "what's missing per SKU", after attribute-normalize.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Merchandising}
---
# Gap Score
## Purpose
Deterministic completeness per channel (#3.1): the gap report names the missing fields per SKU.
## When to use
After attribute-normalize in every batch.
## Inputs
normalized.json + config/taxonomy-map.json (required_by_channel).
## Steps
1. Run scripts/completeness_score.py --normalized normalized.json --taxonomy taxonomy-map.json --out scored.json
2. Quote percentages and missing-field lists verbatim - a SKU at 80% with the missing field named beats a soothing average.
## Output
scored.json - the {completeness} hop.
## Grounding requirements
Requirements cite the channel config.
## Constraints
- Required-fields-only arithmetic; the model never pads completeness with optional fields.
## Escalation / uncertainty
Batch average below the customer's floor -> steward escalation before drafting.
