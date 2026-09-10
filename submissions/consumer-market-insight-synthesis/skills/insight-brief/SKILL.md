---
name: insight-brief
description: 'Drafts the cited insight brief with the provenance and usage-rights record attached. Use to close every insight run: "draft the brief", "write it up for the category review".'
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Insights & Category}
---
# Insight Brief
## Purpose
Terminal artifacts: cited brief + provenance record (#4.3), populated only from the contract payload.
## When to use
End of every insight run.
## Inputs
governed.json (full payload).
## Steps
1. Validate against the contract; contradictions and exclusions lead when present.
2. Brief: question, what the usable evidence shows (per-study citations), trend deltas, contradiction section presented both-sides, and the "excluded from this use" list with reasons.
3. Attach the provenance record: who can reuse, where, until when (#4.3). Mark DRAFT.
## Output
INSIGHT-<topic>.md + provenance record - terminal artifacts.
## Grounding requirements
No sentence without a study citation; every citation is a USABLE study for the declared use.
## Constraints
- No forecasts, no claim approval, no causal attribution (#5.1); the strongest excluded stat stays excluded (#4.1).
## Escalation / uncertainty
A brief whose best evidence was excluded says so - honest gaps beat borrowed stats.
