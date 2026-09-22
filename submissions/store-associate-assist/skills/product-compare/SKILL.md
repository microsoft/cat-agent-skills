---
name: product-compare
description: Builds a side-by-side product comparison from the PIM extract with the deterministic product_compare engine. Use when the associate asks "what's the difference between these two", "which should I recommend", or names two SKUs.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Store Operations}
---
# Product Compare
## Purpose
Attribute-level comparison from the PIM extract only (#3.1) - differences stated, missing shown as missing.
## When to use
Whenever the question carries two SKUs.
## Inputs
resolved.json + config/pim-extract.json.
## Steps
1. Run scripts/product_compare.py --resolved resolved.json --pim pim-extract.json --out compared.json
2. Present the table verbatim; the recommendation narrative may explain fit-to-need but never invents an attribute.
## Output
compared.json - the {product_comparison} hop.
## Grounding requirements
Every attribute cites the PIM extract.
## Constraints
- No specs from memory or the internet; PIM only (#3.1).
## Escalation / uncertainty
SKU missing from PIM: shown as missing + escalation to the PIM steward.
