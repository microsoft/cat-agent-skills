---
name: Clinical Docs Companion
description: "The documents that follow a signed visit note: draft the referral letter, after-visit summary and clinician handoff, build the coding rationale for codes already on the claim and check quality measures, each cited to a line of the note."
platforms: [Cowork]
type: plugin
category: healthcare
builtByMicrosoft: true
tags: [healthcare, clinical-documentation, referral, after-visit-summary, quality-measures, coding]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.3
createdAt: 2026-10-28
updatedAt: 2026-10-28
bundle: bundles/clinical-documentation-companion.zip
---
Clinical Docs Companion turns a signed visit note into the documents that follow it. It drafts the referral letter, after-visit summary and clinician handoff, builds the coding rationale for codes already on the claim and checks quality measures, each cited to a line of the note. It never marks a measure met without documentation and never sends anything.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **note-context** — Reads a signed encounter note into structured, cited clinical facts as the entry hop of the clinical-documentation-companion chain; if the note is unsigned or still a draft it halts and escalates to the clinician instead. Use when the user says "pull the facts out of today's note", "structure this visit note", "what did the note actually document?", "start the documentation run for this encounter" or "set up the encounter context". Do NOT use for drafting letters or summaries - use document-derive instead; do NOT use for measure status - use quality-gap-check instead; do NOT use to check whether the note supports a claim code - use coding-rationale instead; do NOT use to write a clinician handoff or sign-out - use handoff-draft instead.
- **document-derive** — Drafts the clinical artefacts that follow a signed note - referral letter, after-visit summary, care-plan update - each cited to the note and marked draft. It never sends, faxes or files, and if the note indicates no referral it says so instead of drafting one. Use when the user says "draft the referral letter", "write the after-visit summary", "AVS for this visit", "send the patient home with instructions" or "update the care plan from today's note". Do NOT use for Word/PDF formatting or letterhead on an existing document - use the built-in docx instead; do NOT use for coding evidence - use coding-rationale instead; do NOT use for a clinician-to-clinician handoff - use handoff-draft instead.
- **coding-rationale** — Assembles the cited documentation evidence for the visit level and diagnosis codes already on the claim and flags every element the note does not support. If asked to change, pick or upgrade a code it still builds the rationale and declines the change. Use when the user says "why is this coded 99214?", "does the note support this diagnosis?", "build the coding rationale", "what backs up this claim?" or "the coder is asking for the evidence". Do NOT use for quality-measure status - use quality-gap-check instead; do NOT use for documentation drafting - use document-derive instead; do NOT use to extract facts from the note - use note-context instead.
- **quality-gap-check** — Deterministic engine that scores the encounter against the configured quality measures from documented, cited facts only, and refuses, logs and escalates any attempt to change a measure's status however it is worded. Use when the user says "which quality measures are open?", "run the gap check", "mark this measure as met", "can you just count this one?" or "note that it was likely done so it counts this quarter". Do NOT use for supporting evidence for a claim code - use coding-rationale instead; do NOT use to draft documents or the handoff - use document-derive or handoff-draft instead; do NOT use to extract facts from the note - use note-context instead.
- **handoff-draft** — Drafts the clinician-to-clinician handoff for the encounter with every open quality gap and unsupported claim element listed explicitly as an open item. If asked to leave an item out, it drafts the full handoff and declines the omission. Use when the user says "write the handoff", "sign-out note for the next clinician", "what should the covering doctor know?", "summarise this visit for the care team" or "hand this over to the night team". Do NOT use for patient-facing summaries - use document-derive instead; do NOT use to compute measure status - use quality-gap-check instead; do NOT use to build or explain claim evidence - use coding-rationale instead; do NOT use to extract facts from the note - use note-context instead.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
