---
name: parts-readiness
description: Checks whether a work order's parts are ready — storeroom stock, shortages, and part supersession — and computes a READY/PARTIAL/BLOCKED status, deterministically. Use when the user says "are the parts in stock", "check parts readiness", "can we schedule this", "is that part still current", or after similar-work-rank completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Maintenance
---

# Parts Readiness

## Purpose
Deterministically assemble the required parts for the work order, check each against storeroom stock
and the supersession table, and compute an overall readiness status (READY, READY_WITH_SUBSTITUTION,
PARTIAL, BLOCKED), escalating shortages and redirecting procurement for superseded parts.

## When to use
- After similar-work-rank, in every run.
- "Are the parts in stock?" / "can we schedule this?" / "is that part still current?".

## Inputs
- The contract payload with `required_parts[]`, `parts_catalog[]`, `superseding_fix{}` and
  `asset_criticality` (contract `mfg.work-order-assist.v1`, the `{similar_work}` hop).

## Steps
1. Validate the payload against the contract.
2. Run `scripts/parts_readiness.py --similar similar-work.json --out work-order-packet.json`.
3. Do not restate or recompute any stock number in prose; quote the engine output verbatim.
4. Emit the `{parts_readiness}` contract payload and the finalized `next_best_action`.

## Output
Contract `mfg.work-order-assist.v1` with a populated `parts_readiness{}` object (status, per-part
lines with line_status and effective_part, blockers, confidence, source=engine:parts_readiness,
citation) — the `{parts_readiness}` hop.

## Grounding requirements
Every line cites its parts-catalog row; a supersession redirect cites
`references/parts-readiness-rules.md` #2; a critical-part block cites #3.

## Constraints
- All readiness math happens in the engine. The model must never set a status itself.
- Never re-order a superseded part; redirect to its current replacement (parts-readiness-rules.md #2).
- Do not draft the write-up here — that is work-order-writeup's job.

## Escalation / uncertainty
- A critical part out of stock (BLOCKED), a class-A asset shortage, or a superseded SOP part: the
  engine adds to `escalations[]`; surface the blockers so no un-executable job is scheduled
  (parts-readiness-rules.md #3).
