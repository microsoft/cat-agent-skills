---
name: readiness-pack
description: Drafts the audit-readiness pack - verdict, gaps with owners and actions, clause map, evidence index - from the contract payload. Use when the user says "draft the readiness pack", "prep the audit binder", or after gap-check in a readiness run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Quality}
---
# Readiness Pack
## Purpose
Terminal artifact: the pack rendered from templates/pack-template.md, populated only from the contract payload.
## When to use
End of every readiness run.
## Inputs
gaps.json (full payload).
## Steps
1. Validate against the contract; major gaps lead the pack.
2. Fill the template: verdict, gap table (clause, status, severity, owner, action, due), clause map, evidence index.
3. Mark DRAFT - the quality director owns the plan; nothing is filed and no evidence is fabricated or reworded into existence (#5).
## Output
READINESS-<audit_id>.md - terminal artifact.
## Grounding requirements
Every row cites the engine output; the verdict cites #4.
## Constraints
- Draft-first; nothing in the pack that is not in the contract payload.
- A not_ready verdict is presented as not_ready, whatever the meeting on Monday wants to hear.
## Escalation / uncertainty
Majors within 14 days of the audit date get an explicit call-out to the quality director.
