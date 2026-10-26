---
name: scorecard-roll
description: Rolls up the OTIF / defect / dispute scorecard by quarter with trend flags, deterministically, with the scorecard_roll engine. Use on "how are they performing", "roll the scorecard", after record-pull.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Merchandising & Supply}
---
# Scorecard Roll
## Purpose
Deterministic scorecard: computed OTIF (#1.1), consecutive-decline trend flags (#1.2).
## When to use
After record-pull in every review.
## Inputs
vendor.json + records.json.
## Steps
1. Run scripts/scorecard_roll.py --vendor vendor.json --records records.json --out scored.json
2. Quote quarters and flags verbatim. A trend flag stands even when the latest quarter "isn't that bad" - three consecutive declines is the signal (#1.2).
## Output
scored.json - the {scorecard} hop.
## Grounding requirements
Every quarter cites its receipt extract.
## Constraints
- Computation is engine-only; the vendor's deck never substitutes (#1.1); hospitality is not a metric (#4.1).
## Escalation / uncertainty
Trend flags escalate into the review agenda automatically.
