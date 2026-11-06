---
name: Prior Authorization Packet
description: "A cited prior authorization packet before the request goes to the payer: find the governing coverage policy, check the chart against each criterion, cite the notes that satisfy it, draft the medical necessity narrative and list what is still missing."
platforms: [Cowork]
type: plugin
category: healthcare
builtByMicrosoft: true
tags: [healthcare, prior-authorization, payer, utilization-management, medical-necessity, revenue-cycle]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.3
createdAt: 2026-10-28
updatedAt: 2026-10-28
bundle: bundles/prior-auth-assist.zip
---
Prior Authorization Packet gets a prior authorization request ready before it goes to the payer. It finds the coverage policy for the ordered service, checks the chart against each criterion, cites the notes that satisfy it, drafts the medical necessity narrative and lists what is still missing. It never approves, denies or submits a request.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **policy-ingest** — Finds which payer coverage policy governs an ordered service and writes its exact clause key into the prior-auth packet. Use when the user says "which Contoso policy covers a lumbar MRI", "what are the payer's rules for this procedure", "look up the coverage policy before we request auth", "which clause applies to this order". Do NOT use to read the chart or gather notes - use evidence-match instead; do NOT use to judge whether this patient qualifies - use criteria-extract instead; do NOT use to write the necessity narrative - use necessity-draft instead; do NOT use to report outstanding items - use gap-report instead; do NOT use on a policy already applied to a denied claim - use the denials-appeals-response plugin instead. An unlisted service is handed on as out_of_scope, never matched to a near-miss clause.
- **criteria-extract** — Checks a specific patient's pending prior-auth request against the payer's coverage-policy checklist, clause by clause, and reports which criteria the chart satisfies and which are still open. Use when the user says "does this patient meet Contoso's criteria for the procedure", "does this patient qualify for the MRI under the plan's policy", "run the auth criteria check on this order", "are we ready to request auth yet", "why would this request get pushed back". Do NOT use to look up which payer policy or clause governs a service - use policy-ingest instead; do NOT use to hunt through the chart for source notes - use evidence-match instead; do NOT use for coding or documentation gaps on a finished encounter - use the clinical-documentation-companion plugin instead. Never renders an approval or a denial.
- **evidence-match** — Finds the specific chart notes, dates and verbatim quotes that back a prior-auth request and attaches them as citations. Use when the user says "where in the chart does it show the conservative therapy", "find the notes supporting this auth request", "cite the documentation for the MRI request", "pull the PT records for this order". Do NOT use to decide whether the payer's criteria are met - use criteria-extract instead; do NOT use to write the justification - use necessity-draft instead; do NOT use to list what is still missing - use gap-report instead; do NOT use to audit a completed encounter's documentation or coding - use the clinical-documentation-companion plugin instead.
- **necessity-draft** — Writes the medical-necessity narrative that accompanies a pending prior-auth request, using only criteria the engine marked met and cited. Use when the user says "write the medical-necessity letter for this MRI request", "draft the clinical justification for the auth", "explain to the plan why this procedure is needed", "put together the necessity narrative". Do NOT use to list what is still missing or check packet readiness - use gap-report instead; do NOT use to decide whether the criteria are met - use criteria-extract instead; do NOT use to argue against a decision the payer has already made - use the denials-appeals-response plugin instead. Never writes approval, denial or clearance language.
- **gap-report** — After the criteria check has run, lists every piece of evidence still missing from a prior-auth packet and presents the packet as a draft for review. Use when the user says "what's still missing before we submit this auth", "what does the payer still need from us", "assemble the submission packet for review", "give me the outstanding items on this request". Do NOT use to check whether the patient meets the payer's criteria or why a request would be pushed back - use criteria-extract instead; do NOT use to locate documents in the chart - use evidence-match instead; do NOT use for general Word reports or documents - use docx instead; do NOT use on a claim the payer already denied - use the denials-appeals-response plugin instead. Never submits, files or uploads anything.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
