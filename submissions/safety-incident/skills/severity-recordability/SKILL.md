---
name: severity-recordability
description: Classifies a safety incident's severity, near-miss status, OSHA recordability (with the OSHA 300 column) and reportability (with the 1904.39 clock), deterministically. Use when the user says "is this recordable", "classify this incident", "is this an OSHA reportable", "what severity is this", "do we have to report this", or after ehs-knowledge-retrieve completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: EHS
---

# Severity & Recordability

## Purpose
Deterministically classify the incident: severity tier (low/medium/high/critical), near-miss flag,
OSHA recordability (with the OSHA 300 classification column) and reportability to OSHA (with the
1904.39 regulatory clock). This is the determination the whole packet turns on.

## When to use
- After ehs-knowledge-retrieve, in every run.
- "Is this recordable?" / "do we have to report this?" / "what severity is this?".

## Inputs
- The contract payload with `injury{}`, `incident_type`, `occurred_at` and `history{}`
  (contract `mfg.safety-incident-assist.v1`).

## Steps
1. Validate the payload against the contract.
2. Run `scripts/recordability_classify.py --intake incident-intake.json --out classification.json`.
3. Do not restate or re-derive the determination in prose; quote the engine output verbatim.
4. Emit the `{classification}` contract payload and the preliminary `next_best_action`.

## Output
Contract `mfg.safety-incident-assist.v1` with a populated `classification{}` object (severity,
near_miss, recordable{value,reason,osha_300_column}, reportable{value,type,deadline_hours},
confidence, source=engine:recordability_classify, citation) — the `{classification}` hop.

## Grounding requirements
The recordability determination cites `references/osha-recordability-rules.md` #3; the reportability
determination cites #4; the severity cites #5.

## Constraints
- All classification logic happens in the engine. The model must never decide recordability itself.
- A first-aid list item does not make a case recordable; treatment beyond first aid does
  (osha-recordability-rules.md #2). Do not blur the two.
- Never downgrade a recordable/reportable determination to first-aid to make a report go away
  (osha-recordability-rules.md #6.3) — that is the whole point of the control.

## Escalation / uncertainty
- Incomplete treatment/outcome (confidence below the floor) or a downgrade request: the engine adds
  to `escalations[]`; surface it for EHS-manager sign-off and confirm with the treating clinician
  (osha-recordability-rules.md #6.2, #6.3).
