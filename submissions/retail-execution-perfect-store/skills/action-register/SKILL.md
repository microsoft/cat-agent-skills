---
name: action-register
description: Ranks gaps by revenue at stake with the gap_rank engine and builds the action register and suggested order for the rep to confirm. Use on "what do I fix first", "rank the gaps", "build my order", after gap-score.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Field Sales}
---
# Action Register
## Purpose
Deterministic value ranking (#2.1) with the promo multiplier (#2.2) and the par-based suggested order (#4.1).
## When to use
After gap-score in every run.
## Inputs
scored.json + scan extract + config/perfect-store-standards.json.
## Steps
1. Run scripts/gap_rank.py --scored scored.json --scan scan.json --standards perfect-store-standards.json --out ranked.json
2. Quote the ranking verbatim - two fails on hero SKUs outrank five on tail; a promo-week empty display is the most expensive kind of empty (#2.2). Say it with the numbers.
3. The suggested order is at par quantities; the REP confirms and places it - never transmitted by the plugin (#4.1).
## Output
ranked.json - the {ranked_gaps, suggested_order} hop.
## Grounding requirements
Every gap cites its scan line and standard criterion.
## Constraints
- Ranking is engine-only; a high compliance % never waves off a high-value gap.
## Escalation / uncertainty
Missing scan data degrades to criterion order with an explicit note (#5).
