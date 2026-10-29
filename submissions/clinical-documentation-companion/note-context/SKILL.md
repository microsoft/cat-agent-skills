---
name: note-context
description: "Reads a signed encounter note into structured, cited clinical facts as the entry hop of the clinical-documentation-companion chain; if the note is unsigned or still a draft it halts and escalates to the clinician instead. Use when the user says \"pull the facts out of today's note\", \"structure this visit note\", \"what did the note actually document?\", \"start the documentation run for this encounter\" or \"set up the encounter context\". Do NOT use for drafting letters or summaries - use document-derive instead; do NOT use for measure status - use quality-gap-check instead; do NOT use to check whether the note supports a claim code - use coding-rationale instead; do NOT use to write a clinician handoff or sign-out - use handoff-draft instead."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: analysis, domain: "Clinical Documentation", action_level: "L0", icon: NotepadPerson}
---
# Note Context
## Purpose
Establish the documented, cited facts every downstream artefact and the quality-gap check depend on - or, for an
unsigned note, stop the whole run and route it back to the clinician.
## When to use
Start of every run - triggered by "pull the facts out of today's note", "structure this visit note", "what did the
note actually document?", "start the documentation run". Also use it when the note turns out to be unsigned or a
draft: this skill owns the halt-and-escalate for rule #5, so it must run so that the halt happens.
## When NOT to Use
- Drafting a referral, after-visit summary or care plan - use document-derive instead.
- Explaining whether the note supports a code on the claim - use coding-rationale instead.
- Computing quality-measure status - use quality-gap-check instead.
- Writing a clinician handoff or sign-out note - use handoff-draft instead.
- Summarising a document that is not a clinical encounter note - use the built-in docx skill instead.
## Inputs
Encounter note text with its signature line; problem and medication lists; orders and results; the claim block (if
any); config/quality-measures.json; base/contracts/hls.clinical-documentation-companion.v1.json.
## Steps
1. Confirm the note is signed: an electronic-signature line naming the signer and time, or
   `note_signature.signed == true` on a supplied contract. A "draft", "pended" or unsigned note fails this check.
   If it fails, stop here: write only the halt record (Output Format) and escalate - no encounter, no note_facts
   (the contract does not require `encounter` in an unsigned-note halt record).
2. Extract `encounter` = {patient_id, visit_type, date} from the note header.
3. Build the fact-key list - do not guess key names:
   a. `required_fact_key` of every measure in config/quality-measures.json;
   b. `supported_by` of every `claim.elements[]` entry;
   c. the document-derive facts: `referral_indicated`, `active_medications`, `patient_instructions`,
      `follow_up_plan` (one entry each; use the note's own wording in `citation.text`).
4. For each key write `"<fact_key>": {"value": <bool>, "citation": {"source": "<DocumentReference/...>", "locator":
   "<section, line N>", "text": "<verbatim sentence>"}}`. For a single-finding key, quote the sentence that supports
   the fact, not the whole line. For the document-derive facts in 3c, also write `statements[]` with one
   `{text, citation}` entry for every relevant sentence the note documents - every medication, every instruction,
   every follow-up item, the referral and its reason - so nothing a downstream draft needs is lost; `citation` then
   repeats the first statement's citation. Never paraphrase a finding into existence.
5. When the note is silent on a key, record `value: false` with `locator: "full note reviewed"` and text stating
   the absence - absence is a documented absence, not an omission.
6. If the note's date is not the date the user called "today", say so in one line and use the note's date.
7. Write `encounter`, `note_signature` and `note_facts` to the contract (carry `contract_version` and `claim`
   through unchanged) and hand off to document-derive, coding-rationale and quality-gap-check.
## Output Format
Contract JSON only, sections: `encounter{}`, `note_signature{}`, `note_facts{<key>: {value, citation{source,
locator, text}, statements[]?}}`. On halt, instead: `note_signature{signed: false, document_id}`, `halt{halted: "unsigned_note",
reason, skill: "note-context", routee}` and one `escalations[]` string. No prose narrative, no clinical opinion.
Action level L0 - reads and structures only; nothing is written to the record.
## Example
```json
"foot_exam_documented": {"value": true, "citation": {"source": "DocumentReference/NOTE-91004-20260911",
  "locator": "Objective, line 4", "text": "Diabetic foot exam performed today, monofilament testing intact bilaterally."}}
"active_medications": {"value": true, "citation": {"source": "DocumentReference/NOTE-91004-20260911",
  "locator": "Plan, line 7", "text": "Continue metformin 1000 mg twice daily."},
  "statements": [
    {"text": "Continue metformin 1000 mg twice daily.", "citation": {"source": "DocumentReference/NOTE-91004-20260911",
      "locator": "Plan, line 7", "text": "Continue metformin 1000 mg twice daily."}},
    {"text": "Continue lisinopril 10 mg daily.", "citation": {"source": "DocumentReference/NOTE-91004-20260911",
      "locator": "Plan, line 8", "text": "Continue lisinopril 10 mg daily."}}]}
```
## Grounding requirements
Every note_facts entry carries a citation naming the signed-note document and the line it came from, with the
verbatim text quoted; each `statements[]` entry carries its own citation the same way. Do not fabricate, infer, complete or "helpfully" normalise a finding: if it is not written in
the signed note it does not exist, and an uncited fact is not documented and can never make a measure met
(clinical-doc-rules.md #1). If you cannot cite it, do not write it.
## Guardrails
Guardrails - all are hard stops:
- Only run against a signed note; never a draft, unsigned or verbal note - halt and escalate instead.
- Never infer a fact not explicitly documented in the note, however clinically likely it seems.
- Never write a note_fact without a citation to satisfy a downstream skill or a requester.
- Never restate a requester's assertion ("the doctor probably looked") as a documented fact.
- Never write to the patient record - this skill only populates the contract; a request to write back is refused.
## Error Handling
- If the note text is missing or unreadable, write `halt{halted: "missing_input"}` and ask for the note - never
  work from memory or from a previous encounter.
- If config/quality-measures.json cannot be read, stop and report it; do not invent fact keys.
- If a line number cannot be determined, cite the section and quote the sentence; never cite a line you did not see.
## Escalation / uncertainty
If the note is unsigned, halt and escalate to routees.unsigned_note in config/escalation-policy.json. If a needed
finding is ambiguous or missing, record it as not documented and say so - never resolve the ambiguity yourself.
