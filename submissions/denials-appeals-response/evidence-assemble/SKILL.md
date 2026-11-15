---
name: evidence-assemble
description: "Gathers and cites the clinical and coding evidence that answers the stated denial reason, note by note and date by date, and names the gaps. Use when asked to \"pull the chart evidence for this appeal\", \"does the note support the code we billed\", \"what in the record answers this medical-necessity denial\", \"find the documentation for CLM-10021\". Use after policy-retrieve, before deadline-track and appeal-draft. Do NOT use to read a remittance or classify a denial - use denial-classify instead; do NOT use to retrieve payer policy language - use policy-retrieve instead; do NOT use to write the letter - use appeal-draft instead; do NOT use to decide whether a recode is allowed - use deadline-track instead. Action level L0: cites the record, never edits it."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: analysis, domain: "Revenue Cycle", action_level: L0, max_action_level: L1, icon: ClipboardSearch}
---
# Evidence Assemble
## Purpose
Build the cited evidence base the appeal will rely on.
## When to use
Use after policy-retrieve and before deadline-track and appeal-draft - typical asks are "pull the chart evidence for this appeal", "does the documentation support the billed code", "what in the record answers this denial".
## When NOT to Use
Do NOT use when: no policy clause has been retrieved yet (the evidence has nothing to answer) - use policy-retrieve first; the ask is to read a remittance or classify a denial - use denial-classify instead; the ask is to interpret payer policy - use policy-retrieve instead; the ask is to compose the appeal letter - use appeal-draft instead; the ask is to approve or apply a coding change - use deadline-track instead (it enforces that boundary, and no skill applies codes); or the ask is to make the evidence "look stronger" than the chart supports - that is out of bounds, not a task.
## Inputs
The clinical record, read through [TO CONFIGURE: clinical record source / EHR connector] with the session's file or connector tool (until it is configured, only the chart_evidence already on the contract is available); original claim and coding; the denial reason; the retrieved policy clause; coding_request (if any).
## Steps
1. Read the denial reason and the retrieved policy clause to fix what the evidence has to answer, and name the code being defended: the coding_request's requested code if one exists, otherwise the billed original_code.
2. Gather the clinical notes/results that speak to that question from the configured record source, including any that weaken the appeal.
3. Record each one in chart_evidence.citations[] with note, date, supports_code and a short verbatim excerpt.
4. Set chart_evidence.supports_requested_code true only when a citation in that list names a specific note and date whose supports_code is the code named in step 1; otherwise leave it false.
5. Compare the clause's setting or service type with the claim's (e.g. an inpatient-observation clause against an office E/M code) and record any mismatch as a gap.
6. Hand off to deadline-track (coding decision and clock) and then appeal-draft.
## Example
```
Input: CLM-10077, coding_request 99215, clause CHP-MP-208 s.1.4
Reply: "No - the record does not support 99215.
- Office visit note (2026-08-11): supports 99213 - \"Stable follow-up, low-complexity decision making; nothing documented at level-5 intensity.\"
supports_requested_code: false (no note and date cites 99215).
Gaps: no note documents level-5 decision making. Recode decision -> deadline-track; claim stays queued on 99213."
```
## Output Format
Format: `chart_evidence` on contract hls.denials-appeals-response.v1 - supports_requested_code plus citations[] entries of {note, date, supports_code, excerpt}. Prose reply sections: one-line answer; evidence bullets as "note (date): supports <code> - \"verbatim excerpt\""; gaps as bullets (including weakening evidence and any setting mismatch); hand-off line.
## Grounding requirements
Every evidence item names its source note and date on the contract; an uncited assertion is not evidence and the engine will not honour it. Do not fabricate, paraphrase into fact, or infer a finding the note does not state - excerpts are quoted from the record, a note that does not exist is never cited, and "the chart probably shows" is never written as though it does.
## Guardrails
Guardrails for this skill:
- Never mark supports_requested_code true without a matching chart_evidence.citations entry naming the note and date - the flag alone is not evidence (denials-rules.md #2).
- Never omit evidence that weakens the appeal - the coordinator needs the honest picture.
- Never edit, annotate or add to the clinical record; this skill reads and cites it.
- Never remove a denial from the queue because the evidence is thin (denials-rules.md #4).
- Quote only the excerpt the appeal needs; never output SSNs, full chart dumps or unrelated patient data.
- Action level L0 (draft-only): this skill never submits, files, sends or closes an appeal and never writes to a claim or coding system. Anything that leaves the building is L1 and is performed by a human after review before it leaves (denials-rules.md #5).
## Error Handling
- If the chart is ambiguous on whether it supports the original or requested code, leave supports_requested_code false, cite what the chart does say, and let deadline-track's coding-integrity guard handle it.
- Escalate to [TO CONFIGURE: physician advisor / coding compliance contact] instead of assembling a thin case when either (a) no citation addresses the denial reason, or (b) no citation supports the code being defended.
- If the clinical record source is not configured or unavailable, say so, work only from the citations already on the contract, and label the result "contract citations only - record not searched".
