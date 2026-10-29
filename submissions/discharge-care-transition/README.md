# Discharge Transition Packet

For hospitalists, nurses and case managers preparing a patient to go home from hospital.

It reconciles admission, inpatient and discharge medications, drafts the discharge summary and plain language patient instructions, and builds a dated follow-up checklist with owners, each cited to the record.

The design bet is safety over speed: a medication discrepancy or an unowned follow-up is surfaced, never smoothed over.

## How it works

1. **admission-synthesise** summarises the inpatient stay from notes, procedures, medications, labs and imaging.
2. **med-reconcile** reconciles admission, inpatient and discharge medications and flags every unexplained change.
3. **summary-draft** drafts the discharge summary with each medication and change cited.
4. **patient-instructions** writes plain language instructions at your configured reading level.
5. **followup-plan** builds the follow-up checklist with an owner and date for every pending result and referral.

## Try it

- **Reconcile discharge medications:** "Reconcile the discharge medications for patient [patient id] against the admission history and inpatient orders in [folder]."
- **Draft the discharge packet:** "Draft the discharge summary and plain language instructions for patient [patient id]. The records are in [folder]."
- **Check the follow-up plan:** "What follow-up is still unowned or undated for patient [patient id]? The checklist, referrals and pending results are in [folder]."

## What you bring

Inpatient notes, procedure reports, the medication administration record, labs, imaging, the problem list, discharge orders, referrals and pending results.

Suggested connectors: Salesforce, Oracle Database, Snowflake, Box, ServiceNow, Smartsheet and Adobe PDF Services.

## Before you use it

Each skill has a `config/` folder with settings marked `[TO CONFIGURE]`. Fill these in for your organisation; until you do, the skills report the item as not routed rather than guessing.

- `readability-rules.json`: reading level, sentence length, banned jargon and required sections for patient instructions.
- `followup-rules.json`: required fields, allowed owners and the maximum days to first follow-up.

## Boundaries

Draft packets for clinician review. It never carries a flagged medication through silently and never signs or sends anything.

Outputs are drafts that support, not replace, clinical and professional judgement. Use synthetic or de-identified data when trying it out.
