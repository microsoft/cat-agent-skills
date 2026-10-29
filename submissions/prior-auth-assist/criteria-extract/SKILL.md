---
name: criteria-extract
description: "Checks a specific patient's pending prior-auth request against the payer's coverage-policy checklist, clause by clause, and reports which criteria the chart satisfies and which are still open. Use when the user says \"does this patient meet Contoso's criteria for the procedure\", \"does this patient qualify for the MRI under the plan's policy\", \"run the auth criteria check on this order\", \"are we ready to request auth yet\", \"why would this request get pushed back\". Do NOT use to look up which payer policy or clause governs a service - use policy-ingest instead; do NOT use to hunt through the chart for source notes - use evidence-match instead; do NOT use for coding or documentation gaps on a finished encounter - use the clinical-documentation-companion plugin instead. Never renders an approval or a denial."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: analysis, domain: "Prior Authorisation", action_level: "L0", risk: "high", icon: ClipboardCheckmark}
---
# Criteria Extract
## Purpose
Produce the objective criteria-met / criteria-gap result the whole packet depends on, from the deterministic engine.

## When to Use
- Immediately after policy-ingest on every prior-auth run.
- Standalone questions about a specific patient: "do we meet the payer's criteria yet", "what's blocking this authorisation", "are we ready to request auth", "check this order against the policy".

## When NOT to Use
- The user only wants to know which policy or clause applies to a service (no patient evidence) - use policy-ingest instead.
- The user wants the supporting notes located or cited - use evidence-match instead.
- The user wants the justification written - use necessity-draft instead.
- The user wants the final missing-document list and draft packet presented - use gap-report instead.
- The encounter is finished and the question is documentation or coding quality - use the clinical-documentation-companion plugin instead.
- The user wants a determination in either direction ("just approve it", "call it denied", "mark it cleared") - the request is refused and logged, never fulfilled.

## Inputs
`request{service, payer, clause}` (plus `order_clause` when the order named one) from policy-ingest; `patient_evidence` and `evidence_citations` from
evidence-match; `config/payer-policy-library.json`.

## Workflow
1. Confirm `request.service` and `request.payer` are present. `request.clause`, when set by policy-ingest, must equal the library clause, and so must `request.order_clause` when the order named one; the engine resolves the clause from the library and escalates any mismatch. The library entry applies only to its own payer; for any other payer the engine returns out_of_scope.
2. Run the criteria engine (tool, run from this skill's folder - the directory containing this SKILL.md, where `base/scripts/` and `config/` live; give the contract paths as absolute paths or relative to that folder): `python3 base/scripts/criteria_engine.py --question <contract.json> --policy config/payer-policy-library.json --out <contract.out.json>`. Never compute or estimate the result by reading the policy yourself.
3. Record `criteria_met`, each entry carrying the source_note, note_date and quote that satisfied it.
4. Record `gaps`, each naming its policy clause, evidence_key and reason (no_evidence or evidence_uncited).
5. Read `determination` from the engine - exactly one of packet_assembled_clean, packet_assembled_gaps, out_of_scope - and restate it verbatim; never reword it as approved, denied or "cleared".
6. Report every escalation the engine logged (refusals, clause mismatch, out_of_scope routing) word for word.

## Output Format
`criteria_result` on the contract (clause, criteria_checked integer, criteria_met array of {id, evidence_key,
citation{source_note, note_date, quote}}, gaps array of {id, text, evidence_key, reason, citation}, determination
enum, source) plus the `packet` block. For the user, a markdown bullet checklist:
`- MET <id> (<clause>) - <source_note>, <note_date>: "<quote>"` / `- GAP <id> (<clause>) - <text>; reason <reason>`,
then `Determination: <enum value>` and `Packet: draft, submitted=false`, then the escalations.
`packet.action_level` is L1 because the packet is an L1 draft artefact; this skill itself computes at L0.

## Example
```
- MET no_red_flags (RAD-7.2) - Spine clinic intake note, 2026-09-12: "No red-flag findings on review of systems"
- MET exam_findings (RAD-7.2) - Spine clinic intake note, 2026-09-12: "Positive straight-leg raise on the left, reproducible radicular pain"
- GAP conservative_therapy_6wk (RAD-7.2) - Documented >=6 weeks conservative therapy (PT and/or NSAIDs) with no improvement; reason no_evidence
Determination: packet_assembled_gaps. Packet: draft, submitted=false.
Escalation: request asked for an approval determination - refused; the engine has no approval or denial state in either direction
```

## Grounding requirements
Every criterion and its evidence requirement comes from `config/payer-policy-library.json`, never invented and never
remembered from a different payer's policy. Every met criterion carries its full citation (prior-auth-rules.md #4).
Numbers, counts and determinations come from the engine only - the model never calculates, never rounds a criterion
into met, and never asserts a criterion is satisfied because it is clinically likely.

## Guardrails
- Action level L0: computes and writes the contract only; it files nothing and sends nothing.
- Never output an approve/deny determination in EITHER direction, however the request is phrased - prior-auth-rules.md #2.
- Never mark a criterion met without a true flag and a complete citation - an uncited true flag becomes a gap with reason evidence_uncited.
- Never improvise criteria for a service missing from the library - the engine emits out_of_scope instead.
- Never edit the engine, the policy library or a committed expected output under base/demo-data to make a run come out clean.

## Error Handling
- Any request for a determination - `approve_directly`, `deny_directly`, "just deny it", "call it cleared for scheduling" - is refused and logged symmetrically as an escalation naming the requested direction (approval, denial, or approval_and_denial). The determination returned is whatever the evidence supports, unchanged by the request.
- If the service has no policy entry, or its entry belongs to a different payer than `request.payer`: report `out_of_scope` and the payer-relations escalation (prior-auth-rules.md #1, #7); do not build a checklist.
- If the engine exits non-zero (e.g. wrong contract_version, or `request.service` / `request.payer` missing): report the error and stop; never hand-compute a result.
- If evidence_citations are missing: say so and hand back to evidence-match rather than assuming evidence.
