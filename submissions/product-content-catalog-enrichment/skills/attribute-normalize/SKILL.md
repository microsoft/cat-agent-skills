---
name: attribute-normalize
description: Normalises supplier fields to the taxonomy and validates GTIN check digits with the deterministic attribute_normalize engine. Use after source-ingest, or on "map these to our taxonomy", "are these GTINs valid".
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Merchandising}
---
# Attribute Normalize
## Purpose
Deterministic mapping through the taxonomy table (#2.1), UOM conversions shown (#2.2), GS1 check-digit validation (#1.1).
## When to use
After source-ingest in every batch.
## Inputs
batch.json + config/taxonomy-map.json.
## Steps
1. Run scripts/attribute_normalize.py --batch batch.json --taxonomy taxonomy-map.json --out normalized.json
2. Quote results verbatim. An invalid GTIN blocks the record - identity errors poison every channel downstream; never "fix" a check digit by guessing.
3. Unmapped fields are listed for the steward, never forced into the nearest slot.
## Output
normalized.json - the {normalized} hop.
## Grounding requirements
Every attribute cites sheet row + mapping entry.
## Constraints
- Mapping-table-only; the model never invents a mapping.
## Escalation / uncertainty
Invalid GTINs and unmapped fields escalate to the PIM steward.
