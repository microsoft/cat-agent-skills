---
name: criticality-rank
description: Prioritizes the fault by asset criticality and downtime cost into a P1-P4 maintenance priority with a response target and cost estimate, deterministically. Use when the user says "how urgent is this", "what's the priority", "rank by criticality", "what will downtime cost", or after failure-mode-rank completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Maintenance
---

# Criticality Rank

## Purpose
Deterministically compute the maintenance priority (P1-P4), response target, and downtime
cost for the fault from the asset-criticality matrix, escalating for recurring failures.

## When to use
- After failure-mode-rank, in every triage run.
- "How urgent is this?" / "what's the priority?" / "what does downtime cost?".

## Inputs
- The contract payload with `ranked_causes[]`, `asset_criticality`,
  `downtime_cost_per_hr`, and `history.repeat_promotion`
  (contract `mfg.maintenance-triage.v1`, the `{ranked_causes}` hop).

## Steps
1. Validate the payload against the contract.
2. Run `scripts/criticality_score.py --ranked ranked-causes.json --out triaged.json`.
3. Do not restate or recompute any score in prose; quote the engine output verbatim.
4. Emit the `{priority}` contract payload and the `recommended_action`.

## Output
Contract `mfg.maintenance-triage.v1` with a populated `priority{}` object (level, score,
response_target, downtime_cost_estimate, factors, confidence,
source=engine:criticality_score, citation) — the `{priority}` hop.

## Grounding requirements
Every priority cites the matrix sections used and ISO 55000 risk-based prioritization
(`references/asset-criticality-matrix.md`, `references/rcm-iso55000-excerpts.md`).

## Constraints
- All scoring math happens in the engine. The model must never set a priority itself.
- Never downgrade a repeat-failure escalation to save a planned-outage slot.
- Do not draft the work order here — that is work-order-update's job.

## Escalation / uncertainty
- Missing downtime cost yields an estimated impact and an escalation; a P1 assignment or a
  repeat-failure escalation is surfaced to the shift supervisor and planner
  (asset-criticality-matrix.md #6).
