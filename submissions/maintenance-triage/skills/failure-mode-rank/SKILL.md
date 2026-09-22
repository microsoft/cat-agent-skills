---
name: failure-mode-rank
description: Ranks the likely failure modes for a fault against the failure-mode library, symptoms, alarm codes and repeat-failure history, deterministically. Use when the user says "what's the likely cause", "rank the failure modes", "diagnose this fault", "is this the real root cause?", or after history-retrieve completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Maintenance
---

# Failure-Mode Rank

## Purpose
Deterministically rank the candidate failure modes for the fault, matching symptoms and
alarm codes to the failure-mode library and applying the repeat-failure root-cause
promotion rule.

## When to use
- After history-retrieve, in every triage run.
- "What's the likely cause?" / "rank the failure modes" / "is the reset masking something?".

## Inputs
- The contract payload with `symptoms[]`, `alarm_codes[]`, and `history{}`
  (contract `mfg.maintenance-triage.v1`).

## Steps
1. Validate the payload against the contract.
2. Run `scripts/fault_rank.py --intake fault-intake.json --out ranked-causes.json`.
3. Do not restate or recompute any score in prose; quote the engine output verbatim.
4. Emit the `{ranked_causes}` contract payload.

## Output
Contract `mfg.maintenance-triage.v1` with populated `ranked_causes[]` (rank, failure_mode,
match_score, evidence, recommended_fix, confidence, source=engine:fault_rank, citation) and
`history.repeat_promotion` — the `{ranked_causes}` hop.

## Grounding requirements
Every ranked cause carries its OEM manual / library citation; the promotion of a root cause
over a symptomatic fix cites `references/failure-mode-library.md` #3.1.

## Constraints
- All ranking math happens in the engine. The model must never re-rank causes itself.
- No priority or cost talk here — that is criticality-rank's job.
- Never suppress the repeat-failure promotion because a cheaper symptomatic fix "usually works".

## Escalation / uncertainty
- Top candidate confidence below the 0.75 floor, or two candidates within the ambiguity
  band: the engine adds to `escalations[]`; surface it and route to a human diagnosis
  (failure-mode-library.md #4.1-#4.2).
