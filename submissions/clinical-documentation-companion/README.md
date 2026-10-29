# Clinical Docs Companion

For clinicians and care teams turning a signed visit note into the documents that follow it.

It drafts the referral letter, after-visit summary and clinician handoff, builds the coding rationale for codes already on the claim and checks quality measures, each cited to a line of the note.

The design bet is evidence over completeness: a measure is only met, and a code only supported, when the note says so.

## How it works

1. **note-context** reads the signed encounter note into structured, cited clinical facts, and halts if the note is unsigned.
2. **document-derive** drafts the referral letter, after-visit summary and care plan update, each cited and marked draft.
3. **coding-rationale** assembles the documentation behind the visit level and diagnosis codes already on the claim and flags anything the note does not support.
4. **quality-gap-check** scores the encounter against your configured quality measures from documented facts only.
5. **handoff-draft** drafts the clinician handoff with every open gap and unsupported claim element listed.

## Try it

- **Draft the referral and visit summary:** "Draft the referral letter and after-visit summary from signed note [note id] in [folder]."
- **Check quality measures:** "Which quality measures are still open for the visit in note [note id]? The measure status request is in [file]."
- **Back the codes on the claim:** "Show the documentation behind the codes on the claim for note [note id] and flag anything the note does not support. The claim export is [file]."

## What you bring

Signed encounter notes, problem and medication lists, orders and results, the claim export and your quality measure definitions.

Suggested connectors: Salesforce, Box, Oracle Database, Snowflake, Azure Databricks and Adobe PDF Services.

## Before you use it

Each skill has a `config/` folder with settings marked `[TO CONFIGURE]`. Fill these in for your organisation; until you do, the skills report the item as not routed rather than guessing.

- `quality-measures.json`: the quality measures you track and what documents them.
- `escalation-policy.json`: who to route coding compliance and quality questions to.

## Boundaries

Drafts and rationales for clinician review. It never marks a measure met without documentation, never changes or upgrades a code and never sends anything.

Outputs are drafts that support, not replace, clinical and professional judgement. Use synthetic or de-identified data when trying it out.
