# Reg Submission Authoring

For regulatory and medical writing teams drafting a clinical study report or 510(k) submission.

It turns a locked protocol, statistical analysis plan and tables, listings and figures into a cited first draft. It plans the sections, drafts each one from source facts, checks every number and population against the sources and assembles the draft with its open items.

The design bet is traceability over prose: every number in the draft points back to a locked source.

## How it works

1. **source-ingest** builds a cited fact map from the protocol, SAP, TLFs and prior submissions.
2. **section-plan** plans the required sections for the submission type and the facts each one needs.
3. **section-draft** drafts each section from cited source facts in your house style.
4. **consistency-check** checks every number, population and required section against the sources.
5. **submission-assemble** assembles the draft with the open items on top, only after the consistency check.

## Try it

- **Load the study sources:** "The locked protocol, SAP and TLF set for study [study id] are in [folder]. Build the cited fact map for the [CSR or 510(k)]."
- **Draft a section:** "Draft the [section] for study [study id] from the locked tables in [folder]."
- **Check the numbers, then assemble:** "Do the numbers in the [CSR or 510(k)] draft in [file] match the tables? If they do, assemble it with the open items on top."

## What you bring

The locked protocol, statistical analysis plan, tables, listings and figures, the investigator brochure, prior approved submissions and your style guide.

Suggested connectors: Box, Egnyte, Azure Databricks, Snowflake, Confluence, Adobe PDF Services, Smartsheet and Jira.

## Before you use it

Each skill has a `config/` folder with settings marked `[TO CONFIGURE]`. Fill these in for your organisation; until you do, the skills report the item as not routed rather than guessing.

- `submission-templates.json`: required sections for each submission type (CSR and 510(k) today).
- `field-dictionary.json`: the source fact keys.
- `style-guide.json`: your house style.

## Boundaries

A cited draft for regulatory review. It never files or submits anything.

Outputs are drafts that support, not replace, clinical and professional judgement. Use synthetic or de-identified data when trying it out.
