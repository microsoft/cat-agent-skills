---
name: ecn-draft
description: Drafts the engineering change notice with the affected-item list, document updates, dispositions and open requirements from the contract payload. Use when the user says "draft the ECN", "write up the change", or after standards-check in a change run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Engineering}
---
# ECN Draft
## Purpose
Terminal artifact: ECN rendered from templates/ecn-template.md, populated only from the contract payload.
## When to use
End of every change run.
## Inputs
Payload with impact{} and standards_findings[].
## Steps
1. Validate against the contract; escalations (interface violations, blocked documents) lead the draft.
2. Fill the template: change summary, impact class, affected items, documents to update (obsolete revs flagged), inventory disposition, standards findings, open requirements.
3. Mark DRAFT - the change board approves; nothing is released or written back by this plugin.
## Output
ECN-<ecr_id>.md - terminal artifact.
## Grounding requirements
Everything cites its BOM link, register row, rule section or standard excerpt.
## Constraints
- Draft-first; a release_blocked=true payload is never drafted as releasable.
- Nothing in the ECN that is not in the contract payload.
## Escalation / uncertainty
Open requirements (stackup, stress sign-off) render as a checklist the change board must clear.
