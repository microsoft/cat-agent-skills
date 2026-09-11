---
name: similar-work-rank
description: Ranks the most similar past work orders for the current job and surfaces recurring failures and superseding fixes, deterministically. Use when the user says "find similar past work", "have we done this before", "what's the closest prior fix", "is this a repeat failure", or after knowledge-retrieve completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Maintenance
---

# Similar-Work Rank

## Purpose
Deterministically rank the asset's prior work orders by similarity to the current work order,
detect a recurring SOP-default fix, and surface a superseding-fix recommendation from a prior fix
note.

## When to use
- After knowledge-retrieve, in every run.
- "What's the closest prior fix?" / "have we done this before?" / "is this a repeat failure?".

## Inputs
- The contract payload with `issue_keywords[]`, `required_parts[]`, `retrieved.prior_fixes[]` and
  `history.prior_work_orders[]` (contract `mfg.work-order-assist.v1`).

## Steps
1. Validate the payload against the contract.
2. Run `scripts/similar_work.py --intake wo-intake.json --out similar-work.json`.
3. Do not restate or recompute any similarity score in prose; quote the engine output verbatim.
4. Emit the `{similar_work}` and `{superseding_fix}` contract payload plus the preliminary
   `next_best_action`.

## Output
Contract `mfg.work-order-assist.v1` with populated `similar_work[]` (rank, wo_id, similarity_score,
shared_signals, outcome, recommended_fix, repeat_failure, confidence, source=engine:similar_work,
citation), `superseding_fix{}`, and `history.repeat_promotion` — the `{similar_work}` hop.

## Grounding requirements
Every similar match carries its CMMS record citation; a recurring-failure promotion cites
`references/similar-work-rules.md` #3.1; a superseding fix cites its fix-note ID and #3.3.

## Constraints
- All similarity math happens in the engine. The model must never re-rank prior work itself.
- No parts-readiness talk here — that is parts-readiness's job.
- Never suppress a recurring-failure or superseding-fix finding because "the SOP says to do X".

## Escalation / uncertainty
- Top match below the 0.75 confidence floor, no comparable history, or a repeat failure detected:
  the engine adds to `escalations[]`; surface it and route a recurring failure to an RCA
  (similar-work-rules.md #4.1-#4.3).
