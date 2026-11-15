---
name: handoff-draft
description: "Drafts the clinician-to-clinician handoff for the encounter with every open quality gap and unsupported claim element listed explicitly as an open item. If asked to leave an item out, it drafts the full handoff and declines the omission. Use when the user says \"write the handoff\", \"sign-out note for the next clinician\", \"what should the covering doctor know?\", \"summarise this visit for the care team\" or \"hand this over to the night team\". Do NOT use for patient-facing summaries - use document-derive instead; do NOT use to compute measure status - use quality-gap-check instead; do NOT use to build or explain claim evidence - use coding-rationale instead; do NOT use to extract facts from the note - use note-context instead."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: communication, domain: "Clinical Documentation", action_level: "L1", icon: PersonArrowRight}
---
# Handoff Draft
## Purpose
Give the next clinician a clear, cited handoff including every open quality gap and unsupported claim element.
## When to use
Last skill in the chain - triggered by "write the handoff", "sign-out note for the next clinician", "what should the
covering doctor know?", "hand this over to the night team". Also when the request asks to leave an open item out:
run anyway, keep every item, and decline the omission.
## When NOT to Use
- A patient-facing after-visit summary or referral - use document-derive instead.
- Computing measure status - use quality-gap-check instead.
- Building or explaining claim evidence - use coding-rationale instead.
- Extracting facts from the note - use note-context instead.
- Sending, filing or signing the handoff - this plugin never transmits; the clinician does.
## Inputs
encounter; note_facts with citations; quality_gap_result; coding_rationale; the user's live message.
## Steps
1. Copy the contract to a working file and append the user's message verbatim to `messages`.
2. Always run the tool on the working file, even when `quality_gap_result` and `coding_rationale` already exist -
   results computed before the message was appended cannot record its refusals or escalations: `python3
   base/scripts/quality_gap_engine.py --question <working.json> --measures config/quality-measures.json --policy
   config/escalation-policy.json --out <out.json>`. Draft from `<out.json>` only.
3. If `quality_gap_result.halted` is "unsigned_note", write no handoff: restate the halt and stop. If
   `coding_rationale.status` is "not_applicable", write "No claim on contract" in place of claim items and continue.
4. Draft the clinical summary from encounter and cited note_facts only.
5. List every `quality_gap_result.gaps` entry and every `coding_rationale.unsupported_flags` entry as one open item
   each, quoting its fields verbatim and carrying its `note_citation` (or its rule citation when none exists).
6. Annotate a refused override on its gap line ("override refused, escalated - still open"); refusals are not
   counted as separate items.
7. If `omission_requests_refused` is non-empty, or the user asked to leave an item out, add one line: "Request to
   omit <item> declined - every open item stays listed" (escalated to routees.omission_refusal).
8. Write `handoff_note = {"status": "draft", "action_level": "L1", "text": ..., "citations": [...]}` for
   clinician review before it is sent.
## Output Format
Contract JSON: `handoff_note = {status: "draft", action_level: "L1", text, citations[]}` where `text` has two
sections: "Clinical summary" (bullet per cited fact) and "Open items (N = gaps + unsupported flags)" (one bullet per
item). The open-item count always equals gaps + unsupported_flags. Status is always "draft".
## Example
```text
Open items (2 = 1 gap + 1 unsupported flag)
1. QUALITY GAP diabetic_foot_exam - missing foot_exam_documented [full note reviewed] - override refused, escalated - still open
2. UNSUPPORTED E11.42 - missing neuropathy_documented [clinical-doc-rules.md #4] - escalated to routees.unsupported_claim_element
```
## Grounding requirements
Every open item matches a quality_gap_result.gaps or coding_rationale.unsupported_flags entry verbatim, with its
citation, and every clinical statement traces to a cited note_fact. Do not fabricate follow-up, timing, resolution
or reassurance that the contract does not contain, and never describe a gap as "addressed", "likely done" or
"pending closure" when the engine calls it a gap. If the user asks what to do "before tomorrow" and the contract
has no dates, say that no dated follow-up is documented.
## Guardrails
Guardrails - all are hard stops:
- Never omit an open item to make the handoff look cleaner, shorter or more favourable.
- Never mark the handoff as final, and never transmit, file or sign it.
- Never soften an open item's wording or merge several into one vague line.
- Never add a finding, plan or outcome that is not on the contract.
## Error Handling
- If the engine exits non-zero, report "handoff not drafted: gap check failed (<error>)" and stop.
- If note_facts are missing, run note-context first; if it halts, report the halt.
- Never draft open items from memory when the engine output is unavailable.
- If an escalation names a routee that is "NOT ROUTED" (still a [TO CONFIGURE] placeholder), say plainly that the
  refusal is logged but has not reached anyone, and that the plugin owner must configure that routee - never
  present a placeholder as a real contact.
## Escalation / uncertainty
If any measure remains a gap, the handoff names it as unresolved; refused overrides stay escalated to
routees.override_refusal and refused omissions to routees.omission_refusal (clinical-doc-rules.md #6, #7).
