---
name: claim-check
description: Validates marketing claims and regulated terms against the approved claim library - the explicit Govern step - with the deterministic claim_check engine. Use on "is this copy safe", "can we say antibacterial", "check the claims", after gap-score.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Merchandising}
---
# Claim Check (Govern)
## Purpose
The compliance determination IS the work: a claim ships only with library substantiation for that GTIN and market (#4.1/#4.2); blocked claims never appear in copy, not even softened (#4.3).
## When to use
After gap-score, before any copy is drafted.
## Inputs
scored.json + config/claim-library.json + target market.
## Steps
1. Run scripts/claim_check.py --scored scored.json --library claim-library.json --market <mkt> --out governed.json
2. Quote verdicts verbatim. Supplier romance copy is not approval - "the supplier wrote it" changes nothing (#4.1).
## Output
governed.json - the {claim_findings} hop.
## Grounding requirements
Approvals cite the substantiation reference; blocks cite the regulated-term list.
## Constraints
- The engine decides; the model never rephrases a blocked claim into the draft ("fights germs" for a blocked "antibacterial" is still the claim).
- Approving a regulated claim is a human/regulatory affair - out of scope.
## Escalation / uncertainty
Every blocked claim escalates to the claim owner with the library citation.
