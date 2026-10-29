---
name: gap-report
description: "After the criteria check has run, lists every piece of evidence still missing from a prior-auth packet and presents the packet as a draft for review. Use when the user says \"what's still missing before we submit this auth\", \"what does the payer still need from us\", \"assemble the submission packet for review\", \"give me the outstanding items on this request\". Do NOT use to check whether the patient meets the payer's criteria or why a request would be pushed back - use criteria-extract instead; do NOT use to locate documents in the chart - use evidence-match instead; do NOT use for general Word reports or documents - use docx instead; do NOT use on a claim the payer already denied - use the denials-appeals-response plugin instead. Never submits, files or uploads anything."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: analysis, domain: "Prior Authorisation", action_level: "L1", risk: "high", icon: DocumentQuestionMark}
---
# Gap Report
## Purpose
Give the coordinator an explicit, actionable missing-evidence list and the draft packet, after criteria-extract has run.

## When to Use
- As the last skill in the chain on every run - including when gaps is empty, to confirm the all-clear explicitly.
- Standalone asks once a criteria_result exists: "what's outstanding", "what do we still owe the plan", "assemble the packet for review".

## When NOT to Use
- criteria-extract has not run (there is no criteria_result), or the user asks whether the patient meets the criteria or why the plan would push back - use criteria-extract instead.
- The user wants the evidence found rather than the gap named - use evidence-match instead.
- The user wants the justification written - use necessity-draft instead.
- The user wants a general Word report or document - use docx instead.
- The payer already denied the claim - use the denials-appeals-response plugin instead.
- The user wants the packet sent, filed or uploaded to a payer portal - that action does not exist in this package and the request is declined.

## Inputs
`criteria_result.gaps` (id, text, evidence_key, reason, clause citation); `criteria_result.criteria_met`;
`criteria_result.determination`; `necessity_narrative`; `packet`; `escalations`.

## Workflow
1. Read `criteria_result.gaps`, `criteria_result.determination` and `packet` from the contract produced by the engine (tool: `python3 base/scripts/criteria_engine.py --question <contract.json> --policy config/payer-policy-library.json --out <contract.out.json>`, run by criteria-extract).
2. For every entry in gaps, write one table row: criterion id, policy clause, evidence_key, reason, and the evidence needed, restated from the criterion `text` in the policy library.
3. If gaps is empty, state explicitly that all required criteria are evidenced and cited - never leave the all-clear implicit.
4. If determination is out_of_scope, report that no checklist could be assembled and carry the payer-relations escalation forward instead of an empty all-clear.
5. List met criteria with their citations, then every escalation word for word.
6. Present the packet block exactly as the engine wrote it - status draft, submitted false.

## Output Format
A markdown table, one row per gap:
`| # | Criterion | Clause | evidence_key | Reason | Evidence needed |`
or the line `All required criteria are evidenced and cited (<n> of <n>).`; then `Met:` bullets with citations;
then `Escalations:` bullets; then the `packet` JSON exactly as on the contract. The first line always states
`Not ready - <open_gaps> open gap(s)` or `No open gaps`; this is never an approval.

## Example
```
Not ready - 1 open gap. This is a draft for review, not an approval or denial.
| # | Criterion | Clause | evidence_key | Reason | Evidence needed |
| 1 | conservative_therapy_6wk | RAD-7.2 | conservative_therapy_6wk | no_evidence | Documented >=6 weeks conservative therapy (PT and/or NSAIDs) with no improvement, cited with note, date and quote |
Met: no_red_flags, exam_findings - Spine clinic intake note, 2026-09-12
packet: {"status": "draft", "submitted": false, "determination": "packet_assembled_gaps", "clause": "RAD-7.2", "criteria_met_count": 2, "open_gaps": 1}
```

## Grounding requirements
Every listed gap matches an entry in `criteria_result.gaps` verbatim - nothing is added or summarised out. The
"evidence needed" column restates the criterion text from the policy library; it never names an invented document,
deadline, payer instruction or readiness percentage. Counts (open_gaps, criteria_met_count) are read from the
engine, never recounted by the model.

## Guardrails
- Action level L1 (draft only): assembles a packet for human review; L2 submit/file/upload actions are not available in this package.
- Never omit a gap to make the packet look cleaner.
- Never soften a gap list into "basically ready" - the specific evidence_key and clause are always named.
- Never report a gap as resolved because someone says the document will arrive later.
- Never change packet.status from draft or packet.submitted from false (prior-auth-rules.md #5).
- Never present the packet as an approval, denial or clearance, whatever the determination value (prior-auth-rules.md #2).

## Error Handling
- If criteria_result is missing: stop and hand back to criteria-extract; do not build a gap list by reading the policy yourself.
- If determination is out_of_scope: report it as such with the payer-relations escalation (prior-auth-rules.md #7), not as an empty all-clear.
- If a remaining gap needs a document: route it to the prior-auth coordinator role in `config/escalation-contacts.json`; if that contact is still `[TO CONFIGURE: ...]`, say so rather than naming anyone.
- If the user asks to upload or submit: decline, and keep the packet as a draft.
