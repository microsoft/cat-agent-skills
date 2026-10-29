---
name: document-derive
description: "Drafts the clinical artefacts that follow a signed note - referral letter, after-visit summary, care-plan update - each cited to the note and marked draft. It never sends, faxes or files, and if the note indicates no referral it says so instead of drafting one. Use when the user says \"draft the referral letter\", \"write the after-visit summary\", \"AVS for this visit\", \"send the patient home with instructions\" or \"update the care plan from today's note\". Do NOT use for Word/PDF formatting or letterhead on an existing document - use the built-in docx instead; do NOT use for coding evidence - use coding-rationale instead; do NOT use for a clinician-to-clinician handoff - use handoff-draft instead."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: writing, domain: "Clinical Documentation", action_level: "L1", icon: DocumentArrowRight}
---
# Document Derive
## Purpose
Produce the downstream documents that follow the signed note, as cited drafts for clinician signature.
## When to use
After note-context, for an encounter whose signed note indicates a referral, AVS or care-plan update - triggered by
"draft the referral letter", "write the after-visit summary", "AVS for this visit", "update the care plan". Also
when the request mixes drafting with sending ("draft it and fax it"): draft, and decline the send.
## When NOT to Use
- Formatting, letterhead or Word/PDF production of an existing document - use the built-in docx skill instead.
- Coding evidence - use coding-rationale instead.
- Quality-measure status - use quality-gap-check instead.
- A clinician-to-clinician handoff - use handoff-draft instead.
## Inputs
note_signature (signed must be true); encounter; note_facts with citations from note-context, including
`referral_indicated`, `active_medications`, `patient_instructions` and `follow_up_plan`, each with its
`statements[]` (one cited entry per documented medication, instruction or follow-up statement).
## Steps
1. Confirm `note_signature.signed` is true; if not, write `halt{halted: "unsigned_note"}` and escalate - never
   draft from an unsigned note (clinical-doc-rules.md #5).
2. If a note_fact needed for a sentence is missing from the contract - or one of `active_medications`,
   `patient_instructions`, `follow_up_plan` or a true `referral_indicated` has `value: true` but no `statements[]` -
   run note-context for it first; never draft from the raw note directly and never draft the sentence without it.
3. Draft only the artefacts the user asked for (all three only when asked to "run the downstream documents").
4. Referral: check `referral_indicated`. If false or absent, set `referral_letter: null` and
   `referral_decision = {drafted: false, reason, citation}`, and say so. If true, draft the letter from cited
   note_facts only - every `statements[]` entry of `referral_indicated`, `active_medications` and
   `follow_up_plan` - attaching each supporting citation, and set `referral_decision.drafted = true`.
5. After-visit summary: plain patient language, one sentence per cited `statements[]` entry of
   `active_medications`, `patient_instructions` and `follow_up_plan` - every entry, so no medication, instruction
   or follow-up item is dropped - and no general teaching text, no reassurance the note does not contain. A symptom
   the plan does not address is listed for clinician review, not explained to the patient.
6. Care-plan update (if asked): cited to the note_facts and every relevant `statements[]` entry, written to
   `care_plan_update`.
7. Write each artefact as `{"status": "draft", "action_level": "L1", "text": "<document>", "citations":
   [{source, locator, text}]}` and hand back for clinician review before release. If asked to send, fax, file or
   push to a portal, decline in one line.
## Output Format
Contract JSON, sections: `referral_letter` (draft or null), `referral_decision`, `after_visit_summary`,
`care_plan_update` - each draft `{status: "draft", action_level: "L1", text, citations[]}` - plus a bullet list of
"for clinician review" items. Status is always "draft" - never "final", never "sent".
## Example
```json
"referral_letter": null,
"referral_decision": {"drafted": false, "reason": "The signed note indicates no referral this visit.",
  "citation": {"source": "DocumentReference/NOTE-91004-20260911", "locator": "Plan, line 10", "text": "No referral indicated this visit."}}
```
## Grounding requirements
Every derived document sentence traces to a note_facts entry - or one of its `statements[]` - and carries that
citation on the contract; every cited statement the document needs appears, none is silently dropped. Do
not fabricate, embellish or infer clinical content - no finding, diagnosis, result, instruction or reassurance that
is not in the signed note, even if the requester asserts it or it would make the letter read better. An uncited
sentence must be deleted, not softened.
## Guardrails
Guardrails - all are hard stops:
- Never draft from an unsigned note.
- Never draft a referral not indicated by the note.
- Never add clinical content beyond what the note documents; never fabricate a finding, instruction or reassurance.
- Never mark output final, send, fax, file or push it to a portal - clinician signature is required
  (clinical-doc-rules.md #3).
- Never restate a gap or unsupported finding as resolved in patient-facing text.
## Error Handling
- If note_facts are missing entirely, run note-context; if that halts, report the halt and stop.
- If the note is ambiguous about a referral, ask the clinician rather than drafting one speculatively.
- If the encounter date is not the day the user called "today", name the note's date in the review list.
## Escalation / uncertainty
If the note is unsigned, escalate to routees.unsigned_note in config/escalation-policy.json. A declined referral
or declined send is reported to the requester and listed for clinician review.
