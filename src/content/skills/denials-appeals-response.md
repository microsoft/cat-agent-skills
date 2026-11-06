---
name: Denials & Appeals Response
description: "A denied claim from the remittance to a draft appeal: classify the denial and its reason codes, attach the governing payer policy and chart evidence, rank the queue by deadline then recoverable value and draft the appeal at the right level."
platforms: [Cowork]
type: plugin
category: healthcare
builtByMicrosoft: true
tags: [healthcare, denials, appeals, revenue-cycle, payer, claims]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.3
createdAt: 2026-10-28
updatedAt: 2026-10-28
bundle: bundles/denials-appeals-response.zip
---
Denials & Appeals Response works a denied claim from the remittance to a draft appeal. It classifies the denial and its reason codes, attaches the governing payer policy and chart evidence, ranks the queue by deadline then recoverable value and drafts the appeal at the right level. It never recodes a claim the chart does not support and never submits an appeal.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **denial-classify** — Parses a post-service denial letter or remittance (X12 835 / EOB) into denial type, CARC/RARC reason codes, amounts and appeal level, with every field cited to its source. Use when asked "we got a denial from Contoso", "what kind of denial is this", "read this remittance / EOB / 835", "why was this claim denied", "start an appeal on claim CLM-10021". Use at the start of every denials-and-appeals run. Do NOT use for pre-service prior-authorization denials - use the prior-auth-assist plugin instead; do NOT use to draft or redraft the appeal letter - use appeal-draft instead; do NOT use to pull chart documentation - use evidence-assemble instead; do NOT use for payer policy (use policy-retrieve instead) or deadlines (use deadline-track instead); do NOT use to create or edit Word files - use docx instead. Action level L0: reads and classifies only.
- **policy-retrieve** — Pulls the governing payer policy clause, contract term and coding guidance for a denial reason and attaches them as citations, or reports that none was found. Use when asked "what policy does this denial cite", "find the Contoso medical policy for CO-50", "which contract term applies here", "what does the payer's policy actually say". Use after denial-classify, on every denial. Do NOT use to search the patient's chart - use evidence-assemble instead; do NOT use to write the appeal letter - use appeal-draft instead; do NOT use to compute deadlines - use deadline-track instead. Never quotes policy from memory. Action level L0: retrieves and cites only, never submits or negotiates anything.
- **evidence-assemble** — Gathers and cites the clinical and coding evidence that answers the stated denial reason, note by note and date by date, and names the gaps. Use when asked to "pull the chart evidence for this appeal", "does the note support the code we billed", "what in the record answers this medical-necessity denial", "find the documentation for CLM-10021". Use after policy-retrieve, before deadline-track and appeal-draft. Do NOT use to read a remittance or classify a denial - use denial-classify instead; do NOT use to retrieve payer policy language - use policy-retrieve instead; do NOT use to write the letter - use appeal-draft instead; do NOT use to decide whether a recode is allowed - use deadline-track instead. Action level L0: cites the record, never edits it.
- **deadline-track** — Deterministic engine: calculates the appeal deadline and days remaining from today, flags urgent and expired deadlines on every queued claim, ranks the queue by deadline then recoverable value, and enforces the coding-integrity boundary. Use when asked "when is this appeal due", "how many days do we have left", "which denial should we work first", "can we recode this to a 99215 and refile", "that payer isn't in our config, just use 30 days". Run before appeal-draft and again as the last step of every run. Do NOT use for drafting the letter - use appeal-draft instead; do NOT use for gathering evidence - use evidence-assemble instead; do NOT use for payer policy - use policy-retrieve instead. Never applies a coding change: refused recodes go to a human as an evidence gap. Action level L0: calculates and ranks only.
- **appeal-draft** — Drafts the level-appropriate appeal letter from the cited policy clause and chart evidence already on the contract, with the deadline status in the header. Use when asked to "draft the appeal letter", "write the appeal for this denial", "put together our response to Contoso", "redraft this appeal on the original code". Use after evidence-assemble and deadline-track. Do NOT use to classify a new denial or "start an appeal" from a remittance - use denial-classify instead; do NOT use to gather evidence - use evidence-assemble instead; do NOT use to find policy - use policy-retrieve instead; do NOT use to compute the deadline - use deadline-track instead. Never sends, files or uploads the appeal: hand it to the human coordinator. Action level L0: draft text only.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
