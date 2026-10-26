---
name: provenance-check
description: Checks usage rights, geography and expiry for every retrieved study against the declared use - the explicit Govern step - with the deterministic provenance_check engine. Use on "can we use this externally", "is this stat cleared for the board deck", after trend-compare.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Insights & Category}
---
# Provenance Check (Govern)
## Purpose
The compliance determination IS the work: license scope x geography x expiry gates every citation for the DECLARED use (#4.1/#4.2). A restricted or expired study is unusable however strong the stat.
## When to use
After trend-compare, before any brief is drafted.
## Inputs
compared.json + config/rights-register.json.
## Steps
1. Run scripts/provenance_check.py --compared compared.json --rights rights-register.json --out governed.json
2. Quote the record verbatim; excluded studies are named with their restriction so the reader knows what was left out and why.
## Output
governed.json - the {provenance_record} hop.
## Grounding requirements
Every entry cites the rights register row.
## Constraints
- The engine decides; the model never launders a restricted stat by paraphrase - a reworded number is still the licensed number.
- Approving new rights is the licensing team's work, not this plugin's.
## Escalation / uncertainty
Missing register rows -> unusable until registered; escalate to research ops.
