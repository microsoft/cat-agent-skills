---
name: Discharge Transition Packet
description: "The packet for a patient going home from hospital: reconcile admission, inpatient and discharge medications, draft the discharge summary and plain language patient instructions, and build a dated follow-up checklist with owners, each cited to the record."
platforms: [Cowork]
type: plugin
category: healthcare
builtByMicrosoft: true
tags: [healthcare, discharge, care-transition, medication-reconciliation, patient-instructions, follow-up]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.3
createdAt: 2026-10-28
updatedAt: 2026-10-28
bundle: bundles/discharge-care-transition.zip
---
Discharge Transition Packet prepares the packet for a patient going home from hospital. It reconciles admission, inpatient and discharge medications, drafts the discharge summary and plain language patient instructions, and builds a dated follow-up checklist with owners, each cited to the record. It never carries a flagged medication through silently and never signs or sends anything.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **admission-synthesise** — Builds the cited admission narrative (encounter, admission medications, inpatient changes) from notes, procedures, results and the problem list, as the entry hop of the discharge packet. Use when the user says "prep the discharge packet", "start the discharge packet", "pull together the hospital course", "what happened during this admission" or "summarise the stay for discharge". Do NOT use for medication reconciliation - use med-reconcile instead; do NOT use for the discharge summary prose - use summary-draft instead; do NOT use for patient-facing text - use patient-instructions instead; do NOT use for outpatient or pre-admission workups.
- **med-reconcile** — Deterministic engine: diffs admission, inpatient-change and draft discharge medication lists and reports every add, stop, change and unresolved discrepancy, each cited to a numbered rule. Use when the user says "reconcile the discharge meds", "check the discharge medication list", "did anything get stopped during the stay", "is it safe to carry the home med list forward" or "just pull the home med list forward". Do NOT use for writing the summary - use summary-draft instead; do NOT use for patient-facing medication wording - use patient-instructions instead; do NOT use it to correct the draft list, it reports and never edits.
- **summary-draft** — Drafts the clinician-facing discharge summary - course, procedures, results, medications, disposition - fully cited and marked draft for signature. Use when the user says "draft the discharge summary", "write up the hospital course", "put the discharge summary together" or "get the discharge summary ready for signature". Requests to finalize or sign it are answered with the draft still marked pending clinician signature. Do NOT use for the medication diff - use med-reconcile instead; do NOT use for patient-facing plain language - use patient-instructions instead; do NOT use for the admission narrative - use admission-synthesise instead; do NOT use to sign, file or transmit anything into the chart.
- **patient-instructions** — Produces plain-language patient discharge instructions from the reconciled evidence, with a deterministic readability check driven by config/readability-rules.json. Use when the user says "write the patient instructions", "what does the patient need to know at home", "make this readable for the patient", "plain-language discharge sheet" or "give the patient the same list as the summary". Do NOT use for the clinician-facing record - use summary-draft instead; do NOT use for the medication diff - use med-reconcile instead; do NOT use for the admission narrative - use admission-synthesise instead; do NOT use to hand instructions directly to a patient, a clinician approves first.
- **followup-plan** — Extracts follow-up appointments, pending results and referral orders into an owned, dated, cited checklist, verified by the followup_check engine. Use when the user says "what follow-up does this patient need", "build the follow-up checklist", "who is chasing the pending labs", "list the follow-up appointments to arrange" or "just list the pending potassium recheck". Do NOT use for the medication diff - use med-reconcile instead; do NOT use for the summary or the patient sheet - use summary-draft or patient-instructions instead; do NOT use for the admission narrative - use admission-synthesise instead; do NOT use to book, send or close anything.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
