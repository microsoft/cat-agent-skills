---
name: section-draft
description: >-
  Write or revise the language for one planned CSR or 510(k) section - synopsis, efficacy, safety, discussion,
  device description - using only figures already in the cited fact map, each with its TLF or SAP citation.
  Use when the user asks "draft the Synopsis from our locked tables", "write up safety from Table 14.3.1",
  "give me a first pass at the discussion", "draft the device description for the 510(k)" or "tighten the
  wording of the Discussion section". Do NOT use for supplying a number not already in source_facts - use
  source-ingest instead. Do NOT use for verifying a draft's figures - use consistency-check instead. Do NOT use
  for appeal letters, clinical notes or discharge summaries - use the matching HLS plugin instead. Guardrail:
  drafts for human approval only (L1); never asserts an unsourced number or harmonises two figures.
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: writing, domain: "Pharma / MedTech Regulatory & Quality", action_level: L1, icon: Compose}
---
# Section Draft
## Purpose
Produce - or revise the wording of - the cited first-draft language for a section the plan has marked ready.
## When to use
Use after section-plan, once a section is marked `ready`, when a user says things like:
- "Draft the Synopsis from our locked tables."
- "Write the efficacy evaluation section."
- "Give me a first pass at the discussion."
- "Write up safety from Table 14.3.1."
- "Draft the device description for the 510(k)."
- "Tighten the wording of the Discussion - it reads clunky." (a revision: prose changes, asserted values do not)
### When NOT to Use
Do NOT use when:
- The section is still `blocked-on-missing-fact` - use source-ingest to source the fact first; drafting against a
  gap is how invented numbers enter a submission. Use section-plan to confirm readiness instead.
- The ask is to change a figure a reviewer disputes, or to make two sections agree - that is an open item for
  consistency-check to report, not a drafting decision - run consistency-check instead.
- The ask is to check or assemble rather than write - use consistency-check or submission-assemble instead.
- The document is not a regulatory submission section (appeal letter, clinical note, discharge summary, general
  business document) - use the relevant HLS plugin or the built-in docx skill instead.
- The user asks for a number "roughly", "about" or "close enough" - decline and quote the source value.
## Inputs
`source_facts` (each `{value, citation}`, keyed per config/field-dictionary.json); the section plan entry for this
section; the target section's name from `config/submission-templates.json`; `config/style-guide.json`. For a
revision, the existing `draft_sections` entry.
## Steps
Tool: read inputs with the file-read tool; after drafting, hand the payload to consistency-check, which runs
`python3 base/scripts/consistency_check.py --question <payload.json> --out <report.json>` with the `bash` tool.
1. Confirm the section is marked `ready` in the plan; if it is blocked, stop and return it to source-ingest.
2. Draft (or, for a revision, rewrite) the narrative prose for the section. A revision may change wording only -
   every asserted value, and its citation, stays exactly as it was.
3. For every number, date and population definition the prose asserts, copy the value verbatim from source_facts
   into `draft_sections[].asserted` under the same key (submission-rules.md #1 and #4) - never re-derive, round or
   recompute it, and never compute a percentage or ratio the fact map does not hold.
4. Carry the source fact's citation onto each asserted value unchanged; the engine compares the two strings
   (submission-rules.md #5).
5. Keep "enrolled", "randomized", "completed" and "safety population" strictly distinct, exactly as the SAP defines
   them, even where the counts look interchangeable (submission-rules.md #2; enforced from
   config/style-guide.json `population_terms_must_match_sap`). If the source figures look anomalous (for example a
   subset count larger than its parent population), add a reviewer note naming both values - never reconcile them.
6. Emit the section in the output format below and hand off to consistency-check - drafting is never the last hop.
## Output
A `draft_sections` entry on the contract with `section`, `status: "drafted"`, the `narrative` string and the
`asserted` map, plus the prose for the reviewer headed "DRAFT - for medical writer / biostatistician review; not
approved", with an inline `[source]` marker after each quantitative claim and a markdown list of open items (facts
the section needed but could not source) and reviewer notes.
### Output Format
```json
{"section": "Safety Evaluation", "status": "drafted",
 "narrative": "The safety population comprised 259 subjects [TLF Table 14.1.1 - Subject disposition]. ...",
 "asserted": {"safety_population_n": {"value": 259, "citation": "TLF Table 14.1.1 - Subject disposition"},
              "teae_subjects_n": {"value": 201, "citation": "TLF Table 14.3.1 - Treatment-emergent adverse events"}}}
```
Open items: - incidence percentages by arm: not in source_facts - route to source-ingest.
## Grounding requirements
Every asserted value is copied verbatim from source_facts, never re-derived, rounded, averaged or estimated by the
model (config/style-guide.json `numeric_format`). Never fabricate a number, date, population definition, citation
or result - not to fill a sentence, not to make prose flow, and not because a plausible value is obvious. If the
fact is not in source_facts it is not written; it is raised as an open item. Narrative prose may summarise, but
every quantitative claim must be one of the cited asserted values. Rules: base/references/submission-rules.md #1,
#2, #4, #5.
## Constraints
### Guardrails
Guardrails for this skill:
- Action level L1: produces a draft for human approval; nothing is filed, sent or transmitted.
- Never assert a number that does not appear in source_facts - the engine reports it as an unsourced assertion and
  it is never a silent pass (submission-rules.md #4).
- Never assert a value without its citation, even when the prose is asked to read "clean": the prose may omit
  citation markers, the contract may not (submission-rules.md #5).
- Never silently correct, harmonise or round a figure so two sections agree - that is reported, not fixed
  (submission-rules.md #1).
- Never substitute one population count for another, however close the numbers (submission-rules.md #2).
- Never include subject-level identifiers (IDs, initials, dates of birth) - source_facts is aggregate only.
- Never decide or calculate a numeric result; the model drafts language only.
- Never present a draft as final, approved or reviewed.
## Escalation / uncertainty
If a section needs a fact that is not in source_facts, mark it as an open item and route it back to source-ingest
rather than inventing a plausible value. If a user presses for a figure to be adjusted, restate both values with
their citations and escalate to the medical writer / biostatistician.
### Error Handling
- Section not in the plan, or plan missing: stop and ask for section-plan to run first.
- Section name not in config/submission-templates.json for the submission type: stop - the structure comes from
  config, never from the model.
- consistency-check reports findings on the new draft: return them to the user unchanged; do not redraft numbers to
  make the findings go away.
