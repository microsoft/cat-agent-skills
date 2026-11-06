---
name: coding-rationale
description: "Assembles the cited documentation evidence for the visit level and diagnosis codes already on the claim and flags every element the note does not support. If asked to change, pick or upgrade a code it still builds the rationale and declines the change. Use when the user says \"why is this coded 99214?\", \"does the note support this diagnosis?\", \"build the coding rationale\", \"what backs up this claim?\" or \"the coder is asking for the evidence\". Do NOT use for quality-measure status - use quality-gap-check instead; do NOT use for documentation drafting - use document-derive instead; do NOT use to extract facts from the note - use note-context instead."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: analysis, domain: "Clinical Documentation", action_level: "L1", icon: TextQuote}
---
# Coding Rationale
## Purpose
Give the coder/biller a cited rationale draft for the codes already on the claim - never a proposed code.
## When to use
After note-context, whenever `claim.visit_level` or `claim.elements` exist - triggered by "why is this coded
99214?", "does the note support this diagnosis?", "build the coding rationale", "what backs up this claim?". Also
when the request mixes a rationale with a code change ("bump it to 99215"): build the rationale, decline the change.
## When NOT to Use
- Quality-measure status - use quality-gap-check instead.
- Drafting patient or referral documents - use document-derive instead.
- Extracting facts from the note - use note-context instead.
- Submitting the claim - nothing in this plugin submits anything.
## Inputs
note_facts with citations; claim.visit_level and claim.elements (each naming the note_facts key that supports it);
config/escalation-policy.json; the user's live message.
## Steps
1. If note_facts are already on the contract with citations, use them; otherwise run note-context first.
2. Copy the contract to a working file and append the user's message verbatim to `messages`.
3. Run the tool: `python3 base/scripts/quality_gap_engine.py --question <working.json> --measures
   config/quality-measures.json --policy config/escalation-policy.json --out <out.json>`. Never decide support
   yourself.
4. Read back `coding_rationale.supported[]`, `unsupported_flags[]` and `change_requests_refused[]`.
5. Report all three lists verbatim - never move an element from unsupported to supported, and never drop one.
6. Escalate every unsupported element to routees.unsupported_claim_element, and every refused code-change request
   to routees.code_change_refusal. If the user asked for a code change and `change_requests_refused` is empty,
   decline it yourself and escalate it the same way.
7. Present the evidence pack as a draft with `status: "draft"` (clinical-doc-rules.md #3). If there is nothing to
   escalate, say "no unsupported elements - nothing escalated".
## Output Format
Contract JSON, sections: `coding_rationale = {status: "draft", action_level: "L1", visit_level, supported[{element,
type, supported_by, citation{source, locator, text}}], unsupported_flags[{element, type, missing_fact, citation,
note_citation}], change_requests_refused[{requested, evidence, citation}], source: "engine:quality_gap_engine"}`,
then a short bullet list: Supported / Unsupported / Declined. Report only the coding part of the engine output. No
proposed codes appear anywhere. When `status` is "not_applicable" (no claim), say so and stop.
## Example
```text
Supported: 99214 <- moderate_complexity_mdm_documented (Plan, line 10: "...moderate complexity MDM.")
Unsupported: E11.42 - missing neuropathy_documented - escalated to routees.unsupported_claim_element
Declined: "bump the visit to 99215" - this skill never selects or upgrades a code - escalated to routees.code_change_refusal
```
## Grounding requirements
Every 'supported' entry carries the citation of the documented note_fact that supports it; every 'unsupported' flag
names the missing fact (clinical-doc-rules.md #4). Do not fabricate or infer supporting documentation, do not treat
a requester's assertion or clinical plausibility as evidence, and do not describe an element as supported when the
engine did not. If it has no citation, it is unsupported - say so plainly.
## Guardrails
Guardrails - all are hard stops:
- Never propose or select a code, and never recommend a higher or lower level.
- Never mark an element supported without a documented, cited note_fact.
- Never silently drop or soften an unsupported flag, however small the dollar value.
- Never present the rationale as final; it is always a draft pending clinician review before submission.
- Never compute support yourself - the engine's result is the result.
## Error Handling
- If the engine exits non-zero or writes no output, report "rationale not built: <error>" and stop.
- If a claim element names a note_facts key that is missing, it is unsupported - never look for a substitute fact.
- If the note is unsigned (`halted: "unsigned_note"`), report the halt only.
- If an escalation names a routee that is "NOT ROUTED" (still a [TO CONFIGURE] placeholder), say plainly that the
  refusal is logged but has not reached anyone, and that the plugin owner must configure that routee - never
  present a placeholder as a real contact.
## Escalation / uncertainty
Every unsupported element is escalated by name to routees.unsupported_claim_element, and every refused code-change
request to routees.code_change_refusal, in config/escalation-policy.json (clinical-doc-rules.md #6, #7).
