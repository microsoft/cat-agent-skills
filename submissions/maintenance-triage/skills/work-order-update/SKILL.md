---
name: work-order-update
description: Drafts the work-order update and recommended action from the triaged contract payload, with every determination cited to the manual, history and rules. Use when the user says "draft the work order", "write up the WO update", "what should we do", "recommend the fix", or after criticality-rank completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Maintenance
---

# Work-Order Update

## Purpose
Produce the human-readable artifact: a work-order update rendered from
`templates/work-order-update-template.md`, populated only from the contract payload — the
likely failure mode, the priority, the recommended action, and the open escalations.

## When to use
- After criticality-rank, to close the triage loop.
- "Draft the work order" / "what should we do?" / "recommend the fix".

## Inputs
- `triaged.json` (contract `mfg.maintenance-triage.v1`, the `{priority}` hop with
  `ranked_causes[]`, `priority{}`, `recommended_action`, `escalations[]`).

## Steps
1. Validate input against the contract.
2. Fill `templates/work-order-update-template.md`: asset identification, symptom summary,
   ranked likely failure modes with citations, priority + response target + downtime cost,
   the recommended action, an "Open escalations" block, and the contract payload as an appendix.
3. Render to the requested format (markdown; DOCX/PDF via the platform document generation
   component).
4. Mark the update DRAFT — pending planner/supervisor approval.

## Output
`WO-<asset_id>-update.md` (or .docx) — the terminal artifact of the contract flow.

## Grounding requirements
Every failure mode traces to `engine:fault_rank`; the priority traces to
`engine:criticality_score`; standards references cite `rcm-iso55000-excerpts.md`.

## Constraints
- Draft-first: no CMMS/EAM write-back and no work is dispatched in v1. The draft is a
  recommendation, not an executed action.
- Nothing appears in the work order that is not present in the contract payload.
- Scope ends at the WO draft; predictive maintenance and PM optimization are out of scope
  (Wave 3).

## Escalation / uncertainty
- If `escalations[]` is non-empty, the work order must surface them in a visible "Open
  escalations" block above the recommended action — especially a recurring-failure or P1
  escalation.
