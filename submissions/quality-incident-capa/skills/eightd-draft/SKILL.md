---
name: eightd-draft
description: Drafts the 8D / CAPA report from the contract payload, cited to the clause and rules, with open blockers leading. Use when the user says "draft the 8D", "write the CAPA report", or after closure-check in a CAPA run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Quality}
---
# 8D Draft
## Purpose
Terminal artifact: the 8D / CAPA report rendered from templates/eightd-template.md, populated only from the contract payload.
## When to use
End of every CAPA run.
## Inputs
capa.json (full contract payload).
## Steps
1. Validate against the contract; open escalations and closure blockers lead the document.
2. Fill the template: D1-D8 mapped from the payload (D3=containment, D4=root cause chain, D5/D6=CA, D7=PA, D8=closure status with blockers).
3. Mark DRAFT - pending quality-manager approval; nothing is filed or closed by this plugin.
## Output
8D-<capa_id>.md - terminal artifact.
## Grounding requirements
Root cause cites method + evidence; actions cite the library and rule sections; standard citations to ISO 9001 10.2 / IATF 16949 via references.
## Constraints
- Nothing in the report that is not in the contract payload; draft-first, no QMS write-back.
- Scope: starts at NCR handoff, tracks to closure readiness - execution of actions is human work.
## Escalation / uncertainty
Unresolved #3.4 rejection or closure blockers render as a leading "Open items" block.
