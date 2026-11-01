---
name: standard-retrieve
description: Retrieves the perfect-store / picture-of-success standard, planogram and promo calendar for the outlet's channel and cluster. Use on "what's the standard for this outlet", "what should this store look like", after visit-prep.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Field Sales}
---
# Standard Retrieve
## Purpose
The governing standard for THIS outlet: channel x cluster criteria, pars, facing minimums, promo display requirements.
## When to use
After visit-prep in every run.
## Inputs
config/perfect-store-standards.json + planogram repository + promotion calendar.
## Steps
1. Resolve the standard by channel:cluster key; quote criteria verbatim with the standard version.
2. A missing standard blocks scoring - escalate to the execution analyst, never improvise criteria.
## Output
Standard citation attached to the payload.
## Grounding requirements
Standard id + version on every criterion.
## Constraints
- Retrieval only; criteria are configured, not negotiated at the shelf.
## Escalation / uncertainty
Channel/cluster mismatch vs outlet master -> confirm before scoring.
