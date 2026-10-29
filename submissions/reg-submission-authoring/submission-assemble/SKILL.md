---
name: submission-assemble
description: >-
  Put the checked CSR or 510(k) sections together in template order with a reviewer-facing open-items register,
  as a draft package for human sign-off. Use when the user asks "assemble the CSR draft", "put the module
  together for review", "build the review package with the open items on top", "compile the 510(k) sections in
  order" or "package this up for the submission lead". Do NOT use for assembling an unchecked draft - use
  consistency-check instead. Do NOT use for loading protocol, SAP or TLF sources - use source-ingest instead.
  Do NOT use for compiling general documents or slide decks - use the built-in docx or pptx skill instead. Do
  NOT use for filing or submitting to a regulator - use the sponsor's validated gateway, operated by a human,
  instead. Guardrail: draft for human approval only (L1); status is draft_clean or draft_open_items, never
  submitted.
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: writing, domain: "Pharma / MedTech Regulatory & Quality", action_level: L1, icon: DocumentMultiple}
---
# Submission Assemble
## Purpose
Produce the assembled draft package, in template order, for reviewer sign-off.
## When to use
Use as the last skill in the chain, after consistency-check has written consistency_report and set
assembly_status, when a user says things like:
- "Assemble the CSR draft."
- "Put the module together for review."
- "Build the review package with the open items on top."
- "Compile the 510(k) sections in template order."
- "Package this up for the submission lead."
### When NOT to Use
Do NOT use when:
- `consistency_report` is absent or stale - use consistency-check instead; assembly never proceeds on trust.
- `coverage.missing` is non-empty - the package would misrepresent completeness; use section-draft on the missing
  required sections instead (required-section coverage, submission-rules.md #6).
- The ask is to mark, file, submit, publish or transmit the submission - refuse and hand back to the human;
  use the sponsor's validated gateway, operated by a human, instead (submission-rules.md #3).
- The ask is to hide or defer the open-items register so the package "reads better" - refuse.
- The ask is to write or fix a section - use section-draft instead.
- The ask is to load or extract source facts - use source-ingest instead.
- The ask is to compile a general document or slide deck - use the built-in docx or pptx skill instead.
## Inputs
`draft_sections` (including each section's `narrative`); `consistency_report` (required); `assembly_status`;
`config/submission-templates.json` `required_sections` for the target submission type.
## Steps
Tool: re-run the gate with the `bash` tool - `python3 base/scripts/consistency_check.py --question <payload.json>
--out <recheck.json>` - and compare its `consistency_report` and `assembly_status` with the ones supplied.
1. Verify mechanically that `consistency_report` exists and is current (the re-run matches it), that
   required-section coverage is complete (`coverage.missing` is empty), and that `assembly_status` was set by the
   engine; if any is untrue, stop and re-run consistency-check (submission-rules.md #6). Also check that every
   required section carries a non-empty `narrative`; list each one that does not as a completeness item.
2. Order draft_sections by the target structure's `required_sections` from config/submission-templates.json.
3. If `assembly_status` is `draft_open_items`, prepend an open-items register listing every finding with its rule
   number, section, field, asserted value and source value. If it is `draft_clean`, the register reads exactly
   "Open items: none (engine checked=<checked>, 0 findings, 0 missing sections)".
4. Copy the status from the engine - `draft_clean` or `draft_open_items`, never submitted, never filed; the
   contract permits no other value (submission-rules.md #3).
5. Under each section heading place its `narrative` verbatim, then a markdown table of its cited asserted values;
   mark any section with a finding "[OPEN ITEM - see register]". If a section has no narrative, write
   "[narrative not yet drafted - section-draft]" rather than composing prose.
6. Emit the package in the output format below and route it. Sign-off readiness is `READY` only when the engine
   status is `draft_clean` AND there are zero completeness items; otherwise it is `NOT READY` and the package goes
   back to the medical writer (engine findings) or to section-draft (missing narratives). A `READY` package goes to
   the reviewer for sign-off with the signature line left blank. The engine's `assembly_status` is never changed -
   readiness is a separate header line.
## Output
An assembled, clearly draft-marked markdown document: a `DRAFT - NOT FOR SUBMISSION` banner and status header
(`draft_clean` | `draft_open_items`) plus a `Sign-off readiness: READY | NOT READY` line, then the open-items
register (engine findings, verbatim), then a completeness list (sections with no narrative), then the sections in template order with their
narrative and cited asserted values, and a closing note naming the reviewing role and a blank sign-off line. The
contract carries `assembly_status` unchanged from the engine.
### Output Format
```markdown
# DRAFT - NOT FOR SUBMISSION - <product> <target_doc>
Status: `draft_open_items` | checked=10 | open items=1 | missing sections=0
Sign-off readiness: NOT READY (1 engine finding, 1 section without narrative)
### Open-items register
| # | rule | section | field | asserted | source |
|---|---|---|---|---|---|
| 1 | submission-rules.md #1 | Discussion and Overall Conclusions | completed_n | 252 | 248 |
### Completeness items (not engine findings)
- Efficacy Evaluation: narrative not yet drafted - route to section-draft
### 4. Discussion and Overall Conclusions [OPEN ITEM - see register]
<narrative verbatim>
| field | value | citation |
|---|---|---|
| completed_n | 252 | TLF Table 14.1.1 - Subject disposition |
Routing: back to the medical writer / biostatistician. Sign-off: ________ (not signed)
```
## Grounding requirements
The assembled document contains only sections already cross-checked by consistency-check, and the status, counts
and findings are copied verbatim from the engine, never asserted, softened or re-derived by the model. Never
fabricate a section, a figure, a citation or a sign-off, and never omit a finding from the register: the register
must match consistency_report exactly. Rules: base/references/submission-rules.md #3 and #6.
## Constraints
### Guardrails
Guardrails for this skill:
- Action level L1: assembles a draft for human approval. There is no L2/L3 action here - the plugin never files,
  submits, transmits or closes anything, and assembly_status is schema-constrained to draft_clean /
  draft_open_items so "submitted" is unrepresentable (submission-rules.md #3).
- Never assemble a package as final, approved or submitted, however the request is phrased.
- Never shorten, hide or bury the open-items register when findings exist.
- Never assemble when required sections are missing from coverage (submission-rules.md #6).
- Never add content that was not drafted and checked upstream.
- Never write a sign-off, approval or reviewer name that a human did not provide.
- Never route a package for sign-off while any required section has no narrative, even when the engine is clean.
- Never assert a regulatory determination, adequacy judgement or approvability opinion.
## Escalation / uncertainty
If `assembly_status` is `draft_open_items`, the package is explicitly routed back to the medical writer, not
forwarded for sign-off. If `consistency_report` is missing, stale or fails the contract, escalate to the submission
lead rather than assembling.
### Error Handling
- Gate re-run exits 2 (payload off-contract): stop, quote the engine error, escalate - no package is produced.
- Re-run result differs from the supplied report: the supplied report is stale; use the re-run result and say so.
- Re-run escalates `assembly_status_replaced` (the supplied status was e.g. `submitted`): say the supplied status
  is not a permitted value and use the engine's draft status (submission-rules.md #3).
- Submission type has no template in config: stop - section order cannot be taken from memory.
