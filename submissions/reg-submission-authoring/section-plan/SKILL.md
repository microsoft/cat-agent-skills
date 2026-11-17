---
name: section-plan
description: >-
  Work out which sections a CSR or 510(k) requires, from the templates in config, check each one against the
  cited fact map, and name what is missing before a word is drafted. Use when the user asks "what do we still
  need before we can draft the CSR?", "which sections are ready to start?", "what's blocking the performance
  data section?", "do we have everything for the synopsis?" or "map our tables to the E3 structure". Do NOT use
  for writing section language - use section-draft instead. Do NOT use for cross-checking a finished draft - use
  consistency-check instead. Do NOT use for outlining general Word documents or business reports - use the
  built-in docx skill instead. Only structures with a template in config are supported. Guardrail: plans only;
  never marks a section ready on a missing fact and never invents a structure.
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: analysis, domain: "Pharma / MedTech Regulatory & Quality", action_level: L0, icon: DocumentFlowchart}
---
# Section Plan
## Purpose
Ensure nothing is drafted against a gap in the source set, and that every required section is accounted for.
## When to use
Use immediately after source-ingest, for every submission-authoring run, when a user says things like:
- "What do we still need before we can draft the CSR?"
- "Which sections are ready to start on?"
- "What's blocking the 510(k) performance data section?"
- "Do we have everything for the synopsis?"
- "Map our tables to the ICH E3 structure."
### When NOT to Use
Do NOT use when:
- The ask is to produce section prose - use section-draft instead.
- The ask is to verify numbers in an existing draft - use consistency-check instead.
- The ask is to build the review package - use submission-assemble instead.
- The ask is to outline a general Word document, agenda or business report - use the built-in docx skill instead.
- The target submission type has no template in config/submission-templates.json (for example an IND/NDA module
  or a PMA today) - stop and have the sponsor add it to config instead; the model never invents a structure.
- source_facts has not been built yet - use source-ingest first; there is nothing to plan against.
## Inputs
`source_facts` from source-ingest (each `{value, citation}`, keyed per config/field-dictionary.json);
`submission.submission_type`; `config/submission-templates.json` `required_sections` and `section_fields` for that
type.
## Steps
Tool: read config/submission-templates.json, config/field-dictionary.json and the payload with the file-read tool;
no script is needed and none is emulated.
1. Look up the submission type's `required_sections` in config/submission-templates.json - the structure comes from
   config, never from the model (submission-rules.md #6). If the type is absent, stop (see Error Handling).
2. For each required section, take the fields it needs from `section_fields[<section>]` in config. If that list is
   empty (not yet configured), propose the needed fields using only config/field-dictionary.json keys whose
   description genuinely covers that section's content, label the entry `needs_source: "proposed - not configured"`,
   and escalate (see below). If no dictionary key covers the section, the needs list is `["[TO CONFIGURE:
   section_fields]"]` - never an empty list and never a borrowed key.
3. Check each needed field is present in source_facts and carries a citation.
4. Mark the section `ready` only when its needs list names at least one real field and every needed field is
   present and cited; otherwise `blocked-on-missing-fact`, naming the specific field (or the missing configuration)
   and why. An empty needs list, a `[TO CONFIGURE]` need, or facts taken from a payload whose `submission_type`
   differs from the requested type can never make a section `ready`.
5. Keep every required section on the plan in template order - a blocked section stays visible as an open item and
   is never quietly dropped (submission-rules.md #4 and #6).
6. Emit the plan in the output format below and hand off to section-draft for the ready sections only.
## Output
A section plan: an ordered list covering every required section, rendered as a markdown table and as the JSON list
below, each entry `{section, status: ready | blocked-on-missing-fact, needs_source: config | proposed - not
configured, needs: [<field>], missing: [<field>], evidence: "<field> = <value> (<citation>)"}`, plus a one-line
summary of how many sections are ready versus blocked.
### Output Format
```json
[{"section": "Performance Data", "status": "blocked-on-missing-fact", "needs_source": "config",
  "needs": ["<field-dictionary key>"], "missing": ["<field-dictionary key>"], "evidence": "none present"},
 {"section": "Synopsis", "status": "ready", "needs_source": "proposed - not configured",
  "needs": ["enrolled_n", "completed_n"], "missing": [],
  "evidence": "enrolled_n = 260 (TLF Table 14.1.1 - Subject disposition); completed_n = 248 (TLF Table 14.1.1 - Subject disposition)"}]
```
Summary: 1 of 2 required sections ready, 1 blocked.
## Grounding requirements
Every ready/blocked determination cites the specific source_facts field checked, by name and citation, and the
required-section list is quoted from config, not recalled from memory. Never fabricate a section, a requirement or
a fact to make a section look ready: if a needed field is absent, the honest output is `blocked-on-missing-fact`.
The model never estimates a value to unblock a section. Rules: base/references/submission-rules.md #4 and #6.
## Constraints
### Guardrails
Guardrails for this skill:
- Action level L0: plans only; produces no submission text and files nothing.
- Never mark a section ready when a required source_facts field is absent or uncited (submission-rules.md #4).
- Never estimate, back-fill or borrow a value from a neighbouring field to unblock a section.
- Never substitute one population count for another when checking a section's needs (submission-rules.md #2).
- Never take the target structure from memory - it comes from config/submission-templates.json only.
- Never drop a required section from the plan because it looks unnecessary for this study.
- Never present proposed (unconfigured) section needs as sponsor-approved requirements.
- Never mark a section ready on an empty needs list, or on facts gathered for a different submission type.
## Escalation / uncertainty
If more than one required section is blocked, escalate to the submission lead before section-draft runs, listing
each blocked section and the missing field. If any section's needs are `proposed - not configured`, tell the
submission lead the readiness gate is advisory until `section_fields` is configured.
### Error Handling
- Submission type not in config/submission-templates.json: stop, report `unknown_submission_type`, and ask the
  sponsor to add the template - required-section coverage cannot be gated without it.
- source_facts empty or missing: stop and route to source-ingest.
- Payload `submission_type` differs from the type the user asked about: plan against the requested type's template,
  treat the payload's facts as unverified for it, and flag the mismatch.
- A source_facts key not in config/field-dictionary.json: treat it as present only under its exact key and flag it
  for the sponsor; never map it onto a dictionary key by guesswork.
