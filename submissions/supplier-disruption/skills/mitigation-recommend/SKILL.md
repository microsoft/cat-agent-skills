---
name: mitigation-recommend
description: Chooses the mitigation (expedite, substitute or reschedule) for a mapped shortage and computes the escalation tier and owner-notification list, deterministically. Use when the user says "what do we do about it", "should we expedite or substitute", "recommend a mitigation", "who do we escalate to", "who do we notify", or after shortage-impact-map completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Supply Chain
---

# Mitigation Recommend

## Purpose
Deterministically choose the mitigation — **expedite**, **substitute** or **reschedule** — from the
impact summary and the supply position (substitutes, alternate suppliers, lead time, single-source
flag, supplier history), set the urgency, build the cumulative owner-notification list, and raise the
governance escalations — then finalize the recommended next-best action.

## When to use
- After shortage-impact-map, in every run.
- "Should we expedite or substitute, and who do we escalate to?".

## Inputs
- The contract payload with `impact_summary{}` (worst_severity, first_impact_date, total qty at risk)
  and `supply{}` (substitutes, alternates, single_source) and `history.chronic_pattern`
  (contract `mfg.supplier-disruption.v1`).

## Steps
1. Validate the payload against the contract.
2. Run `scripts/mitigation_recommend.py --impact impact-map.json --out disruption-packet.json`.
3. Do not restate or recompute the mitigation choice or the escalations in prose; quote the engine
   output verbatim.
4. Emit the `{mitigation, notifications}` contract payload and the finalized `next_best_action`.

## Output
Contract `mfg.supplier-disruption.v1` with a populated `mitigation{}` (option, urgency, actions,
substitute_part/alternate_supplier, confidence, source=engine:mitigation_recommend), a
`notifications[]` owner list, and appended `escalations[]` plus the finalized `next_best_action` —
the `{mitigation}` hop.

## Grounding requirements
The mitigation choice cites `references/mitigation-escalation-rules.md` #1; the urgency cites #2; each
escalation cites #3; each notification cites #4.

## Constraints
- All mitigation/escalation logic happens in the engine. The model must never choose the mitigation or
  escalate itself.
- Draft-first: the plugin drafts the mitigation and notifications; it never expedites, substitutes,
  reschedules or emails on its own. A buyer/planner confirms.
- Never suppress a customer-order (late_shipment) escalation or a chronic-supplier escalation because
  of time pressure.

## Escalation / uncertainty
- A line-down or late-shipment impact, a single-source critical part, a chronic supplier pattern, or
  low confidence: the engine adds to `escalations[]`; surface them so the decision and the sign-offs
  are visible (mitigation-escalation-rules.md #3).
