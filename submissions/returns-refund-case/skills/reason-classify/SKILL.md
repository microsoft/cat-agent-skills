---
name: reason-classify
description: Classifies the stated return reason against the customer's reason-code taxonomy with the deterministic reason_classify engine. Use after return-intake in every case, or on "what reason code is this".
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Customer Operations}
---
# Reason Classify
## Purpose
Deterministic taxonomy classification of the verbatim reason text.
## When to use
After return-intake in every case.
## Inputs
case.json + config/reason-taxonomy.json.
## Steps
1. Run scripts/reason_classify.py --case case.json --taxonomy reason-taxonomy.json --out classified.json
2. Quote the category and confidence verbatim; ambiguous classifications get confirmed with the customer, not guessed.
## Output
classified.json - the {reason} hop.
## Grounding requirements
Category cites the taxonomy file.
## Constraints
- Taxonomy-only; never invent a new reason code.
## Escalation / uncertainty
Confidence < 0.75 -> confirm with the customer before the packet closes.
