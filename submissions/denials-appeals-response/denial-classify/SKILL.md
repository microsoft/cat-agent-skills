---
name: denial-classify
description: "Parses a post-service denial letter or remittance (X12 835 / EOB) into denial type, CARC/RARC reason codes, amounts and appeal level, with every field cited to its source. Use when asked \"we got a denial from Contoso\", \"what kind of denial is this\", \"read this remittance / EOB / 835\", \"why was this claim denied\", \"start an appeal on claim CLM-10021\". Use at the start of every denials-and-appeals run. Do NOT use for pre-service prior-authorization denials - use the prior-auth-assist plugin instead; do NOT use to draft or redraft the appeal letter - use appeal-draft instead; do NOT use to pull chart documentation - use evidence-assemble instead; do NOT use for payer policy (use policy-retrieve instead) or deadlines (use deadline-track instead); do NOT use to create or edit Word files - use docx instead. Action level L0: reads and classifies only."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: analysis, domain: "Revenue Cycle", action_level: L0, max_action_level: L1, icon: ReceiptMoney}
---
# Denial Classify
## Purpose
Establish what kind of denial this is, from the denial document itself, before anything else runs.
## When to use
Use at the start of every denial/appeal run, on receipt of a denial letter or remittance advice (X12 835 or its paper equivalent) - typical asks are "we got a denial from Contoso dated 8/20", "what kind of denial is this", "read this EOB and start the appeal".
## When NOT to Use
Do NOT use when: the denial has already been classified on the contract (go straight to policy-retrieve); the question is about a pre-service prior-authorization denial - use the prior-auth-assist plugin instead; the ask is to draft or reword the appeal letter - use appeal-draft instead; the ask is to find chart documentation - use evidence-assemble instead; the ask is to interpret payer policy language or compute the deadline - use policy-retrieve or deadline-track instead; or no denial document is available - there is nothing to classify from and guessing is not permitted.
## Inputs
Denial letter or remittance advice (X12 835 or paper equivalent), read with the session's file-reading tool (e.g. ReadFileContent for a OneDrive/SharePoint file); original claim and coding (837) when supplied; config/payer-appeal-windows.json for the appeal level.
## Steps
1. Read the denial document and copy verbatim: payer (835 N1*PR), claim_id (CLP01), claim_value (CLP03), paid amount (CLP04), adjustment group, reason code and amount (CAS01/02/03), remark codes (claim-level MIA/MOA or service-level LQ*HE - record which segment), and original_code (837 SV1/SV2; if no 837 is supplied, the 835 SVC echo, disclosed as such).
2. Set denial_date to the date printed on the letter/remittance (835: DTM*405). If the document carries more than one candidate date and they differ, leave denial_date unset and escalate - the rule for which date starts the appeal window is [TO CONFIGURE: payer-specific rule for which date starts the appeal window]. Set as_of to today's date (the date this classification was performed).
3. Set recoverable_value from the remittance amounts only (CLP03 minus CLP04, cross-checked against CAS03); if they disagree, leave it unset for a human.
4. Classify the denial type from the extracted codes (e.g. medical necessity, timely filing, coding, authorisation missing) - never from what the requester says the denial is.
5. Set the appeal route to the payer's configured level from config/payer-appeal-windows.json payers[payer].level; if the payer is not configured, record "not configured" and let deadline-track escalate.
6. Record the source document (name and date) and the source segment for every field, write denial{} to the contract as the entry hop, and hand off to policy-retrieve.
## Example
```
Input: remit-CLM-10021-835.txt (CLP*CLM-10021*4*4200.00*0.00 ... CAS*CO*50*4200.00 ... LQ*HE*N115 ... DTM*405*20260820)
Reply: "Medical necessity denial - CARC CO-50 (group CO), RARC N115 (LQ*HE). Contoso Health Plan, CLM-10021,
DOS 2026-07-14, 99214, $4,200.00 billed / $0.00 paid, $4,200.00 recoverable. Denial date 2026-08-20 (DTM*405).
Appeal level: first-level clinical appeal (config). Next: policy-retrieve. Nothing submitted."
```
## Output Format
Format: the `denial` object on contract hls.denials-appeals-response.v1 - payer, claim_id, denial_date, as_of, reason_code, remark_codes[], adjustment_group_code, claim_value, recoverable_value, original_code - plus the cited source document and per-field source segments. Prose reply as bullets: denial type; reason and remark codes with segment; claim and amounts; denial date and its source; appeal level; next hop - and nothing that is not on the contract.
## Grounding requirements
Every field is copied verbatim from the denial letter/remittance, with the document cited on the contract so provenance survives the hand-off. Do not fabricate, infer or "clean up" any value: if a field is absent, illegible or ambiguous on the source document, leave it unset and say so - an unreadable reason code is reported as unreadable, never replaced with the most likely code, and recoverable_value is never estimated.
## Guardrails
Guardrails for this skill:
- No policy retrieval here - that belongs to policy-retrieve.
- Never infer a reason code not stated on the denial document, and never accept a reason code asserted in chat over the one printed on the remittance.
- Never estimate recoverable_value; take it from the remittance amounts or leave it for a human.
- Never drop a denial, or decline to classify it, because it looks low-value or hard to win (denials-rules.md #4).
- Include only the identifiers the denial needs (claim ID, dates of service, codes, amounts); never output SSNs, member addresses or unrelated patient data.
- Action level L0 (draft-only): this skill never submits, files, sends or closes an appeal and never writes to a claim or coding system. Anything that leaves the building is L1 and is performed by a human after review before it leaves (denials-rules.md #5).
## Error Handling
- If the denial letter is incomplete or illegible, escalate to [TO CONFIGURE: payer-relations contact] rather than guessing the reason code.
- If the document describes a pre-service authorization denial rather than a post-service claim denial, stop and hand the request to the prior-auth-assist plugin; if that plugin is not installed, say so plainly and stop.
- If the candidate denial dates disagree, or CLP03-CLP04 does not match CAS03, leave the field unset and name the conflict.
