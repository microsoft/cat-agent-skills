---
name: work-order-writeup
description: Drafts the technician notes or planner summary for a work order from the assembled contract payload, with every determination cited to the SOP, manual, history and parts data. Use when the user says "draft the technician notes", "write up the work order", "give me the planner summary", "what's the next best action", or after parts-readiness completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Maintenance
---

# Work-Order Write-up

## Purpose
Produce the human-readable artifact: a work-order write-up rendered from
`templates/work-order-writeup-template.md`, populated only from the contract payload — the assembled
context, the most similar past work, the parts readiness, the recommended next-best action, and any
open escalations. Audience is either the technician (field notes) or the planner (summary).

## When to use
- After parts-readiness, to close the loop.
- "Draft the technician notes" / "give me the planner summary" / "what's the next best action?".

## Inputs
- `work-order-packet.json` (contract `mfg.work-order-assist.v1`, the `{parts_readiness}` hop with
  `similar_work[]`, `parts_readiness{}`, `superseding_fix{}`, `next_best_action`, `escalations[]`).

## Steps
1. Validate input against the contract.
2. Fill `templates/work-order-writeup-template.md`: asset & work-order identification, issue
   summary, the applicable SOP, the top similar past work with citations, the parts-readiness table,
   the recommended next-best action, an "Open escalations" block, and the contract payload appendix.
3. Render to the requested format (markdown; DOCX/PDF via the platform document component).
4. Choose the audience voice: concise field notes for a technician, or a summary with cost/priority
   framing for a planner.
5. Mark the write-up DRAFT — pending planner/supervisor review.

## Output
`WO-<work_order_id>-writeup.md` (or .docx) — the terminal artifact of the contract flow.

## Grounding requirements
Every similar match traces to `engine:similar_work`; the readiness traces to
`engine:parts_readiness`; the SOP/manual and standards cite the reference files.

## Constraints
- Draft-first: no CMMS/EAM write-back, no scheduling, and no stock commitment in v1. The write-up is
  a recommendation, not an executed action.
- Nothing appears in the write-up that is not present in the contract payload.
- Scope ends at the draft; auto-scheduling and inventory commitment are out of scope (Wave 3).

## Escalation / uncertainty
- If `escalations[]` is non-empty, the write-up must surface them in a visible "Open escalations"
  block above the recommended action — especially a recurring-failure, a superseded SOP part, or a
  BLOCKED parts status.
