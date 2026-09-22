---
name: exception-raise
description: Ranks readiness exceptions by revenue at stake with the exception_rank engine and raises the exception list. Use when the user asks "what do we fix first", "rank the gaps", or after readiness-check.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Store Operations}
---
# Exception Raise
## Purpose
Deterministic ranking: weekly promo revenue at stake x launch proximity (#5.1) - impact, not count.
## When to use
After readiness-check whenever anything is missing or conflicted.
## Inputs
checked.json + velocity extract (weekly units + promo price per SKU).
## Steps
1. Run scripts/exception_rank.py --checked checked.json --velocity velocity.json --out ranked.json
2. Quote the ranking verbatim. A small missing signage kit on the top-velocity SKU outranks five gaps on slow movers - say so with the numbers.
## Output
ranked.json - the {exceptions} hop.
## Grounding requirements
Every exception cites its pack line and the velocity extract.
## Constraints
- Ranking is engine-only; never reorder because a gap "looks small".
## Escalation / uncertainty
Top exceptions within 3 days of launch carry the 2x proximity factor and go to the district manager.
