---
name: claim-match
description: Matches each claim to its governing promotion or trade term deterministically with the claim_match engine. Use on "does this deduction match anything we signed", after term-retrieve.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Revenue Growth Management}
---
# Claim Match
## Purpose
Deterministic matching on customer + period + type against SIGNED terms (#1.1). Unmatched = unsupported, never assumed valid.
## When to use
After term-retrieve in every case.
## Inputs
deduction.json + trade-terms.json.
## Steps
1. Run scripts/claim_match.py --deduction deduction.json --terms trade-terms.json --out matched.json
2. Quote matches and misses verbatim; an unmatched claim is a recovery candidate, not a write-off line.
## Output
matched.json - the {matches} hop.
## Grounding requirements
Matches cite the signed agreement; misses cite the absence.
## Constraints
- Matching is engine-only; "they always deduct this" is not a match.
## Escalation / uncertainty
Unmatched claims escalate to the trade manager with the miss stated.
