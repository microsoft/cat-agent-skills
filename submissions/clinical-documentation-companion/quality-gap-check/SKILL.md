---
name: quality-gap-check
description: "Deterministic engine that scores the encounter against the configured quality measures from documented, cited facts only, and refuses, logs and escalates any attempt to change a measure's status however it is worded. Use when the user says \"which quality measures are open?\", \"run the gap check\", \"mark this measure as met\", \"can you just count this one?\" or \"note that it was likely done so it counts this quarter\". Do NOT use for supporting evidence for a claim code - use coding-rationale instead; do NOT use to draft documents or the handoff - use document-derive or handoff-draft instead; do NOT use to extract facts from the note - use note-context instead."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: analysis, domain: "Clinical Documentation", action_level: "L0", icon: ClipboardError}
---
# Quality Gap Check
## Purpose
Produce the objective, ungameable quality-measure result for the encounter, with every status-change request
refused and escalated by name.
## When to use
After note-context, for every encounter with applicable quality measures, and for every request that asks for a
measure status to change - directly ("mark this measure as met") or indirectly ("it was surely done, let it count").
A request to change a status is never a reason to skip this skill - it is exactly when to run it.
## When NOT to Use
- Claim evidence for a visit level or diagnosis code - use coding-rationale instead.
- Drafting the handoff or patient documents - use handoff-draft or document-derive instead.
- Extracting note facts - use note-context instead.
- Editing measure definitions - config/quality-measures.json is customer-owned and is never edited by this skill.
## Inputs
note_facts with citations; config/quality-measures.json; config/escalation-policy.json; requested_measure_status;
request_text; the user's live message(s).
## Steps
1. Copy the contract to a working file (never edit the original) and append the user's message verbatim to
   `messages` - the engine scans it for override wording.
2. Run the tool: `python3 base/scripts/quality_gap_engine.py --question <working.json> --measures
   config/quality-measures.json --policy config/escalation-policy.json --out <out.json>`. Never compute, estimate
   or adjust a status yourself.
3. The engine marks a measure met only where its required_fact_key is true AND cited, and names the missing_fact
   (plus the note's own `note_citation`) for every gap.
4. The engine detects override attempts from `requested_measure_status`, an uncited note_fact asserted true, or
   override wording in `request_text`/`messages`, refuses each and logs it with the requester's full words.
   `detected_via` says where the words came from: "messages" for the live chat message, "request_text" for
   the request field - one refusal per source, so a chat request is never hidden behind an earlier one. Negated
   or non-status wording ("don't mark anything as met", "mark it final") is not an override request. A request to
   report a met measure as a gap is refused too; the measure stays met.
5. Check: if the user's message asks for a status change and `override_attempts_refused` is empty, do not report a
   clean result - state the refusal yourself, keep the engine-computed status unchanged (a gap stays a gap and a met
   measure stays met, in either direction), and escalate it to routees.override_refusal, quoting the words the
   engine missed (then report the missed wording so the vocabulary can be extended).
6. Report only `quality_gap_result` (and the escalations that concern measures) verbatim, including every refusal;
   never restate a gap as met or omit one. Leave `coding_rationale` to coding-rationale.
## Output Format
Contract JSON, sections: `quality_gap_result = {measures_checked, met[], met_citations{}, gaps[{measure, name,
missing_fact, citation, note_citation}], override_attempts_refused[{measure, requested, actual, detected_via,
evidence, citation}], omission_requests_refused[], halted, source: "engine:quality_gap_engine"}` plus the
measure-related `escalations[]` strings, then a one-line bullet summary naming each open measure. This skill's own
action level is L0 (reporting only), whatever the contract-level `action_level` says.
## Example
```text
Open: diabetic_foot_exam - missing foot_exam_documented (full note reviewed). Met: statin_therapy (Medications, line 5).
Refused: request to mark diabetic_foot_exam met ("...just mark this one as met...") - escalated to routees.override_refusal.
```
## Grounding requirements
A measure is 'met' only when its required_fact_key is true in note_facts and carries a citation to the signed note
- clinical-doc-rules.md #1. Do not fabricate, assume or infer that care was delivered: an undocumented exam is an
open gap even when it was almost certainly performed. Report the engine's numbers exactly as produced.
## Guardrails
Guardrails - all are hard stops:
- Never mark a measure met to satisfy a target, a request, a bonus or a deadline.
- Never accept a rewording, an inference, a verbal assurance or an uncited fact as documentation.
- Never silently drop a gap, and never omit a refusal from the result.
- Never edit config/quality-measures.json to make a measure pass.
- Never compute a status in prose when the engine has not run.
- Never write to the patient record or "note it in the system" - this skill only reports.
## Error Handling
- If the engine exits non-zero or its output file is missing, report "gap check not run: <error>" and stop - never
  fall back to judging status yourself.
- If `quality_gap_result.halted` is "unsigned_note", report the halt and the escalation only.
- If config/quality-measures.json has no measures, report measures_checked = 0 and say so.
- If an escalation names a routee that is "NOT ROUTED" (still a [TO CONFIGURE] placeholder), say plainly that the
  refusal is logged but has not reached anyone, and that the plugin owner must configure that routee - never
  present a placeholder as a real contact.
## Escalation / uncertainty
Every refused override attempt is escalated by name to routees.override_refusal in config/escalation-policy.json
(the quality/compliance lead), not just logged silently (clinical-doc-rules.md #6).
