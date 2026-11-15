---
name: appeal-draft
description: "Drafts the level-appropriate appeal letter from the cited policy clause and chart evidence already on the contract, with the deadline status in the header. Use when asked to \"draft the appeal letter\", \"write the appeal for this denial\", \"put together our response to Contoso\", \"redraft this appeal on the original code\". Use after evidence-assemble and deadline-track. Do NOT use to classify a new denial or \"start an appeal\" from a remittance - use denial-classify instead; do NOT use to gather evidence - use evidence-assemble instead; do NOT use to find policy - use policy-retrieve instead; do NOT use to compute the deadline - use deadline-track instead. Never sends, files or uploads the appeal: hand it to the human coordinator. Action level L0: draft text only."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: writing, domain: "Revenue Cycle", action_level: L0, max_action_level: L1, icon: DocumentEdit}
---
# Appeal Draft
## Purpose
Produce the appeal letter text for coordinator review.
## When to use
Use after evidence-assemble and after deadline-track has set coding_decision and deadline_status - typical asks are "draft the appeal letter", "write our response to this denial", "redraft it on the original code".
## When NOT to Use
Do NOT use when: the denial has not been classified yet ("start an appeal on CLM-..." from a remittance) - use denial-classify instead; policy_citations or chart_evidence are still empty (there is nothing to cite, so drafting would invent the case) - use policy-retrieve or evidence-assemble instead; the ask is to submit, file, fax, e-mail or upload the appeal to a payer portal, or to mark it submitted or closed - that is refused, not delegated; the ask is to draft around a code the chart does not cite; or the ask is for the deadline, queue order or coding decision - use deadline-track instead.
## Inputs
denial; policy_citations; chart_evidence (with its citations); deadline_result (coding_decision, deadline, days_remaining, deadline_status); config/payer-appeal-windows.json (appeal level).
## Steps
1. Confirm policy_citations and chart_evidence are populated. If deadline_result is absent, or its provenance.computed_as_of is not today, run deadline-track first (tool: `python3 base/scripts/deadline_engine.py --question <contract.json> --payers config/payer-appeal-windows.json --out <result.json>`, no `--today`) and use its result.
2. Read deadline_result.deadline_status: if `expired` or `urgent`, put that status, the deadline and the day count in the first line of the draft header and in the coordinator notes; if `unconfigured`, say no deadline could be computed.
3. Draft the letter at the level carried in config for the payer (config/payer-appeal-windows.json payers[payer].level, payer name matched case-insensitively).
4. Cite the policy clause_id and every chart_evidence citation used, inline, in the forms "(clause_id)" and "(note, date)". If the clause text is not on the contract, cite it by clause_id only and say the wording is not on file.
5. If coding_decision is refused_evidence_gap, draft on the original, chart-supported code only and state in the coordinator notes that the coding question is open for human decision.
6. Return the letter as a draft for coordinator review before anything is sent - never as a sent or filed item.
## Example
```
*** DRAFT - FOR COORDINATOR REVIEW - NOT SUBMITTED ***
Deadline status: URGENT - due 2026-09-27, 2 day(s) left (deadline-track, as of 2026-09-25)
To: Contoso Health Plan - Appeals (first-level clinical appeal)
Re: Claim CLM-10077 | Denial 2026-08-28 | CARC CO-97 / RARC N657 | Code under appeal: 99213 (original)
Policy basis: (CHP-MP-208 s.1.4) - clause wording not on file; not quoted.
Clinical basis: "Stable follow-up, low-complexity decision making..." (Office visit note, 2026-08-11)
Signed: [TO CONFIGURE: signatory name and title]
Coordinator notes: recode to 99215 refused (refused_evidence_gap) - open for human decision.
```
## Output Format
Format: `appeal_draft` on contract hls.denials-appeals-response.v1 - letter text in these sections: DRAFT banner; deadline-status line; addressee and appeal level; claim header (claim_id, denial date, CARC/RARC, code under appeal, amount); policy basis; clinical basis; statement of what the record is silent on; signature block placeholder; coordinator notes (bullets: deadline status, open coding question, anything to confirm). There is no submitted state on the contract; submission happens outside the plugin.
## Grounding requirements
Every claim in the letter cites a policy_citations clause_id or a chart_evidence citation carried on the contract. Do not fabricate clinical detail, dates, quotations, clause language or outcomes: nothing enters the letter that is not on the contract, and where the record is silent the letter says the record is silent rather than filling the gap with plausible narrative.
## Guardrails
Guardrails for this skill:
- Never draft an appeal around a code the chart does not cite.
- Never mark the appeal as submitted, and never act on it: this skill never submits, files, sends, faxes or uploads the appeal to a payer portal, and never closes the denial (denials-rules.md #5).
- Never omit an expired or urgent deadline_status from the draft header.
- Never overstate the evidence or characterise a gap as satisfied, however the request is phrased.
- Never drop a denial from the queue because its recode was refused - draft on the original code instead (denials-rules.md #4).
- Include only the patient identifiers the appeal needs (claim ID, dates of service, codes); never output SSNs or unrelated patient data.
- Action level L0 (draft-only). Submission is an L1 act performed by a human after review before it leaves the building.
## Error Handling
- If chart_evidence does not support the original code either, escalate to [TO CONFIGURE: physician advisor / coding compliance contact] before drafting.
- If deadline_status is expired, still draft only if the coordinator asks, and keep EXPIRED in the header; the decision on next steps goes to [TO CONFIGURE: appeals manager contact].
- If the payer has no level in config, leave the appeal level as "[level not configured]" and escalate to [TO CONFIGURE: payer-relations contact].
- If asked to submit the draft, decline and hand the submission back to the human coordinator as an L1 act.
