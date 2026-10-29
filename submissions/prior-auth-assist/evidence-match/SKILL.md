---
name: evidence-match
description: "Finds the specific chart notes, dates and verbatim quotes that back a prior-auth request and attaches them as citations. Use when the user says \"where in the chart does it show the conservative therapy\", \"find the notes supporting this auth request\", \"cite the documentation for the MRI request\", \"pull the PT records for this order\". Do NOT use to decide whether the payer's criteria are met - use criteria-extract instead; do NOT use to write the justification - use necessity-draft instead; do NOT use to list what is still missing - use gap-report instead; do NOT use to audit a completed encounter's documentation or coding - use the clinical-documentation-companion plugin instead."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: analysis, domain: "Prior Authorisation", action_level: "L0", risk: "high", icon: DocumentSearch}
---
# Evidence Match
## Purpose
Ground every criterion in a specific note, date and verbatim quote, so the criteria engine can count it as met.

## When to Use
- Before criteria-extract, to populate `patient_evidence` and `evidence_citations` for the policy's evidence_keys.
- After criteria-extract, to confirm every `criteria_met` entry still carries its full citation.
- Asks like "find the documentation", "cite the source note", "what do we have on file for this criterion".

## When NOT to Use
- No policy clause and evidence_keys have been established yet - use policy-ingest first.
- The user wants the met/gap verdict - use criteria-extract instead.
- The user wants prose written from the evidence - use necessity-draft instead.
- The user wants the missing-document list - use gap-report instead.
- The user wants a completed encounter's coding or documentation audited - use the clinical-documentation-companion plugin instead.
- The record does not contain the evidence - do not use this skill to justify a "close enough" note.

## Inputs
Clinical notes, imaging/pathology reports, labs, prior authorisation history, order details; the evidence_keys
named by the policy criteria for the requested service.

## Workflow
1. List the required evidence_keys from `config/payer-policy-library.json` for `request.service`.
2. Search the record for each evidence_key and locate the specific document, its date and the exact supporting sentence.
3. Only when all three exist, set `patient_evidence[key] = true` and write `evidence_citations[key] = {source_note, note_date, quote}` in the same step; the quote is copied verbatim.
4. When the record is ambiguous, partial or undated, set `patient_evidence[key] = false` and write no citation.
5. Run the engine to re-check (tool, run from this skill's folder - the directory containing this SKILL.md, where `base/scripts/` and `config/` live; give the contract paths as absolute paths or relative to that folder): `python3 base/scripts/criteria_engine.py --question <contract.json> --policy config/payer-policy-library.json --out <contract.out.json>`.
6. Confirm every `criteria_met` entry still carries source_note, note_date and quote; report any that do not.

## Output Format
`patient_evidence` (JSON object evidence_key -> boolean) and `evidence_citations` (JSON object evidence_key ->
{source_note, note_date, quote}) on the contract, then a markdown bullet list with one line per evidence_key:
`- <evidence_key>: FOUND - <source_note>, <note_date>: "<quote>"` or
`- <evidence_key>: NOT FOUND - <what the record does or does not say>; retrieval escalated to the prior-auth coordinator`.

## Example
```
- conservative_therapy_6wk: FOUND - Physical therapy discharge summary - Contoso Rehab, 2026-09-02: "7 weeks of supervised PT completed with no functional improvement"
- red_flags_absent: FOUND - Neurosurgery office visit note, 2026-09-10: "No bowel or bladder dysfunction, no progressive motor deficit, no constitutional symptoms"
- exam_findings_documented: NOT FOUND - no dated exam note in the record; retrieval escalated to the prior-auth coordinator
```

## Grounding requirements
Every true evidence flag cites a specific note, date and verbatim quote; absence of a flag is not itself evidence
of anything. Never invent, approximate or round a note date, never paraphrase a quote into something the note does
not say, and never cite a document you have not actually read in the record. If the chart is silent, the correct
output is silence plus a gap - not a plausible reconstruction.

## Guardrails
- Action level L0: reads the record and writes the contract only.
- Never mark an evidence_key true 'to help the packet along'.
- Never infer evidence from a diagnosis code alone without a supporting note.
- Never widen a date range, count weeks of therapy that the note does not state, or treat an order as evidence that the therapy happened.
- A true flag without source_note, note_date and quote does not count - the engine converts it to a gap with reason evidence_uncited (prior-auth-rules.md #4).
- Never invent a coordinator's name; name the role and `config/escalation-contacts.json`.

## Error Handling
- If the record is ambiguous on a required criterion: flag false, no citation, and let it surface as a gap rather than guessing true.
- If the only supporting document is outside this system (e.g. an outside-facility PT record): record it as a gap and escalate retrieval to the prior-auth coordinator (prior-auth-rules.md #7).
- If only pre-extracted note excerpts are available rather than full notes: say the citations were verified against excerpts, not full notes.
- If a note you expected cannot be found in the record: treat the key as not found; never cite it from memory.
- If the engine exits non-zero: report the error text and stop; do not hand-compute the result.
