---
name: policy-ingest
description: "Finds which payer coverage policy governs an ordered service and writes its exact clause key into the prior-auth packet. Use when the user says \"which Contoso policy covers a lumbar MRI\", \"what are the payer's rules for this procedure\", \"look up the coverage policy before we request auth\", \"which clause applies to this order\". Do NOT use to read the chart or gather notes - use evidence-match instead; do NOT use to judge whether this patient qualifies - use criteria-extract instead; do NOT use to write the necessity narrative - use necessity-draft instead; do NOT use to report outstanding items - use gap-report instead; do NOT use on a policy already applied to a denied claim - use the denials-appeals-response plugin instead. An unlisted service is handed on as out_of_scope, never matched to a near-miss clause."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: analysis, domain: "Prior Authorisation", action_level: "L0", risk: "high", icon: BookSearch}
---
# Policy Ingest
## Purpose
Identify which payer policy clause governs the requested service before anything else runs. This decides which
policy the whole packet is built on, so it is exact-match only.

## When to Use
- A service has been ordered but not yet requested, and the user asks which policy or clause applies, what the
  payer requires for the service, or to look up the coverage policy.
- The first step of any prior-auth run, when `request.clause` is not yet on the contract.

## When NOT to Use
- The packet already has `request{service, payer, clause}` populated - re-running would overwrite a confirmed clause.
- The question is about evidence in the chart - use evidence-match instead.
- The question is whether this patient meets the criteria, or whether the request is ready - use criteria-extract instead.
- The user wants the necessity narrative - use necessity-draft instead; the missing-items list - use gap-report instead.
- The payer has already issued a determination and the user wants it challenged - use the denials-appeals-response plugin instead.

## Inputs
The order (requested service and payer, verbatim); the payer medical policy / coverage-determination library
`config/payer-policy-library.json` (customer-owned, read only).

## Workflow
1. Read the order and copy the requested service and payer verbatim - do not normalise a service name into one that happens to exist in the library. If the order already names a policy clause, copy that clause verbatim as well.
2. Look up the service key in `config/payer-policy-library.json` (read-only file tool, e.g. `python3 -c "import json;print(json.load(open('config/payer-policy-library.json')).get('<service>'))"` run from this skill's folder - the directory containing this SKILL.md, where `config/` lives).
3. If there is an exact entry, take its `clause` value exactly as written.
4. If there is no exact entry, set `clause` to JSON `null`, record the out-of-scope hand-off, and do not substitute a related clause.
5. If two library entries could plausibly govern the service, choose neither: name both and escalate to the prior-auth coordinator (`config/escalation-contacts.json`).
6. Write `request{service, payer, clause}` to the contract (hls.prior-auth-assist.v1) and hand on to criteria-extract. If the order named a clause, also write it verbatim as `request.order_clause` - never drop it or overwrite it with the library clause; the criteria engine compares it with the library clause and escalates a mismatch to the prior-auth coordinator (prior-auth-rules.md #1).

## Output Format
The `request` object on the contract - JSON with three fields (`service` string, `payer` string, `clause` string or
`null`), plus `order_clause` (string, verbatim) only when the order names a clause - followed by exactly one
plain-text confirmation line (no table, no bullets):
`Policy identified: <payer> - service <service> - clause <clause>` or
`No policy entry: <payer> - service <service> - clause null; handed to criteria-extract for out_of_scope`.
When `order_clause` differs from `clause`, end the "Policy identified" line with
`; the order names clause <order_clause> - mismatch handed to criteria-extract for escalation`.
No narrative, no determination, no packet status.

## Example
```
Order: "Ordering MRI lumbar spine" (payer Contoso Health Plan)
request: {"service": "mri_lumbar_spine", "payer": "Contoso Health Plan", "clause": "RAD-7.2"}
Policy identified: Contoso Health Plan - service mri_lumbar_spine - clause RAD-7.2

Order: proton_beam_therapy (payer Contoso Health Plan)
request: {"service": "proton_beam_therapy", "payer": "Contoso Health Plan", "clause": null}
No policy entry: Contoso Health Plan - service proton_beam_therapy - clause null; handed to criteria-extract for out_of_scope

Order: mri_lumbar_spine, order policy clause RAD-7.1 (payer Contoso Health Plan)
request: {"service": "mri_lumbar_spine", "payer": "Contoso Health Plan", "clause": "RAD-7.2", "order_clause": "RAD-7.1"}
Policy identified: Contoso Health Plan - service mri_lumbar_spine - clause RAD-7.2; the order names clause RAD-7.1 - mismatch handed to criteria-extract for escalation
```

## Grounding requirements
The clause is the exact key in `config/payer-policy-library.json`, never paraphrased and never reconstructed from
memory of what a payer policy usually says. `order_clause` is the clause exactly as written on the order. Every value
written to `request` traces to the order or the library.

## Guardrails
- Action level L0 (read/lookup only): writes to the contract only, never to a payer and never to the chart.
- Never guess a policy clause for a service that is not in the library, and never reuse a near-miss clause (a lumbar clause for a knee order is a defect).
- Never fabricate criteria; the criteria engine, not this skill, emits `out_of_scope` (prior-auth-rules.md #2).
- Never state or imply coverage, approval or denial - identifying a policy is not applying it.
- Never edit `config/payer-policy-library.json`; it is the customer-owned side of the base/config seam.
- Do not match chart evidence here - that belongs to evidence-match.

## Error Handling
- If the service has no library entry: clause `null`, hand on to criteria-extract, whose engine returns `out_of_scope` and routes the escalation to the payer-relations contact (prior-auth-rules.md #7).
- If the order is missing the service or the payer: stop and ask the user for it; do not infer it from clinical plausibility.
- If the escalation contact in `config/escalation-contacts.json` is still `[TO CONFIGURE: ...]`: name the role and say the contact is not configured - never invent a name.
