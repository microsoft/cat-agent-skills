---
name: policy-retrieve
description: "Pulls the governing payer policy clause, contract term and coding guidance for a denial reason and attaches them as citations, or reports that none was found. Use when asked \"what policy does this denial cite\", \"find the Contoso medical policy for CO-50\", \"which contract term applies here\", \"what does the payer's policy actually say\". Use after denial-classify, on every denial. Do NOT use to search the patient's chart - use evidence-assemble instead; do NOT use to write the appeal letter - use appeal-draft instead; do NOT use to compute deadlines - use deadline-track instead. Never quotes policy from memory. Action level L0: retrieves and cites only, never submits or negotiates anything."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: research, domain: "Revenue Cycle", action_level: L0, max_action_level: L1, icon: BookSearch}
---
# Policy Retrieve
## Purpose
Ground the appeal in the specific payer policy or contract clause the denial cites.
## When to use
Use immediately after denial-classify, for every denial - typical asks are "what policy does this denial cite", "find the clause behind CARC CO-50", "which contract term covers this service".
## When NOT to Use
Do NOT use when: denial.reason_code is not yet populated - use denial-classify first; the ask is for clinical evidence from the record rather than payer policy - use evidence-assemble instead; the ask is to draft or reword the appeal letter - use appeal-draft instead; the ask is about the appeal window, queue order or coding decision - use deadline-track instead.
## Inputs
denial.reason_code (CARC) and denial.remark_codes (RARC); denial.original_code and service setting; the payer policy and contract-term library at [TO CONFIGURE: payer policy and contract-term library location or connector], read with the session's file or connector tool; any policy_citations already on the contract.
## Steps
1. Look up the policy clause and contract term that govern the denial's reason_code in the configured library. If the library is unavailable, skip to Error Handling - never substitute remembered text or web results.
2. Confirm the clause actually addresses that reason_code; discard near-matches. Also compare the clause's setting or service type with the claim's (e.g. an inpatient-observation section against an office E/M code) and escalate a mismatch.
3. Note any coding guidance in the clause relevant to the claim, quoting it with its section.
4. Append each clause to policy_citations[] with clause_id, source, section, retrieved_on and applies_to_reason_code; label medical-policy clauses and contract terms separately. Hand off to evidence-assemble.
## Example
```
Input: CLM-10077, CARC CO-97, library not configured
Reply: "Contract term: none found - no contract-term library is configured, so none was retrieved and none is composed.
Carried on the contract (medical policy, not a contract term; not re-verified today):
| clause_id | source | section | applies_to |
| CHP-MP-208 s.1.4 | Contoso Health Plan Medical Policy MP-208 | 1.4 Evaluation and management level substantiation | CO-97 |
Escalated to [TO CONFIGURE: payer-relations contact] for the governing contract term."
```
## Output Format
Format: `policy_citations[]` on contract hls.denials-appeals-response.v1, one object per clause with clause_id, source, section, retrieved_on and applies_to_reason_code; the engine echoes these clause_ids into deadline_result.policy_basis and provenance.citations. Prose reply sections: answer line; citations as a markdown table (clause_id, source, section, applies_to, kind: medical policy | contract term, status: retrieved today | carried, not re-verified); quoted clause wording only when read from the library; escalations as bullets.
## Grounding requirements
The clause cited is the specific policy/contract section, read from the library at retrieval time, never a general summary and never recalled from memory. Do not fabricate a clause_id, section number, policy title or effective date; if the library returns nothing for the reason_code, or is unavailable, report that no clause was found rather than composing plausible policy language.
## Guardrails
Guardrails for this skill:
- Never cite a clause that does not match the stated reason_code.
- Never paraphrase a clause into policy_citations without its clause_id and source.
- Never characterise the payer's obligation beyond what the clause says, and never present a medical-policy clause as a contract term.
- Never quote or paraphrase clause wording that was not read from the library in this run.
- Include only the identifiers the lookup needs; never output SSNs or unrelated patient data.
- Action level L0 (draft-only): this skill never submits, files, sends or closes an appeal and never writes to a claim or coding system. Anything that leaves the building is L1 and is performed by a human after review before it leaves (denials-rules.md #5).
## Error Handling
- If the library is unavailable or not configured: report "no clause found", list any policy_citations already on the contract as "carried, not re-verified" (identifiers only, no wording), add nothing new to policy_citations[], and escalate to [TO CONFIGURE: payer-relations contact].
- If no clause matches the reason_code, escalate rather than citing the nearest approximate clause.
- If the clause found contradicts the denial as classified, or its setting does not fit the claim, escalate to [TO CONFIGURE: payer-relations contact] before the appeal is drafted.
