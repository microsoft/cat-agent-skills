---
name: trend-compare
description: Compares trends across markets and periods like-for-like with the deterministic trend_compare engine. Use on "how has this trended", "compare markets", "what changed since the last study", after research-retrieve.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Insights & Category}
---
# Trend Compare
## Purpose
Deterministic deltas on same-metric, same-market pairs (#2.1); cross-definition comparisons flagged, never blended.
## When to use
After research-retrieve in every run.
## Inputs
question.json + config/research-index.json.
## Steps
1. Run scripts/trend_compare.py --question question.json --index research-index.json --out compared.json
2. Quote deltas with both study ids and periods; state methods when they differ.
## Output
compared.json - the {retrieved, trends, contradictions} hop.
## Grounding requirements
Every delta cites both studies.
## Constraints
- Like-for-like only; the model never converts metrics to force a comparison.
## Escalation / uncertainty
Metric-definition mismatch -> flagged comparison, not a blended number.
