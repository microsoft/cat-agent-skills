---
name: Staffing & Bench Match
description: "A ranked, partner-ready staffing slate for a signed engagement: extract the roles from the SOW, score bench fit against availability and rates, refuse conflicted or unavailable candidates with the rule cited and draft the recommendation."
platforms: [Cowork]
type: plugin
category: professional-services
builtByMicrosoft: true
tags: [professional-services, staffing, resource-management, bench, independence, conflicts]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.1.14
createdAt: 2026-11-06
updatedAt: 2026-11-06
bundle: bundles/engagement-staffing-bench-match.zip
---
Builds a ranked staffing slate for a signed engagement from the SOW, bench roster, availability, rates and conflicts register. Engines score fit and refuse conflicted or unavailable candidates, citing the rule. Draft-first: it drafts a partner recommendation and never approves, allocates or assigns staff, changes rates or overrides independence.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **role-intake** — Reads a signed engagement, SOW role extract, mobilisation note or staffing request into the ps.engagement-staffing-bench-match.v1 staffing contract (engagement, client affiliates and roles, each field cited) as the first step of every staffing slate. Use when the user says "new engagement signed", "staff this SOW", "mobilise this project", "start a staffing slate" or "extract the roles from this SOW". Do NOT use for contract-terms or commercial summaries (contract review is outside this plugin), loading the bench or conflicts register (use bench-query), scoring or ranking candidates (use fit-score), clearing conflicts (use constraint-check), drafting the slate (use slate-draft) or tool-script requests outside engagement staffing (use tool-scripts).
- **bench-query** — Normalizes bench, availability, rate and conflicts-register data into bench_candidates[] and constraints[] after role-intake, keeping every record and its citation without deciding fit or eligibility. Use when the user says "check the bench", "who is available?", "pull the roster", "include rates" or "load the conflicts extract". Do NOT use for job postings or recruiting copy, extracting roles from a SOW (use role-intake), fit scores (use fit-score), eligibility or conflict verdicts (use constraint-check), drafting the slate (use slate-draft), or for sales segmentation, general rate analysis or generic tool scripting outside engagement staffing (use d365-sales-segment-analysis or tool-scripts).
- **fit-score** — Computes deterministic, pre-governance candidate-role fit scores, utilisation context and provisional ranks with the bundled engines, after bench-query and before constraint-check. Use when the user says "rank the bench", "score the candidates", "who is the best fit?", "compare candidate fit for this role" or "show the provisional ranking". Do NOT use for RFP or vendor-proposal scoring, extracting roles (use role-intake), loading the bench (use bench-query), drafting the slate ("build me a slate"; use slate-draft), eligibility or conflicts (use constraint-check), sales pipeline prioritization (use d365-sales-pipeline-prioritizer), sales meeting prep (use d365-sales-meeting-prep) or ranking or tool scripts outside engagement staffing (use tool-scripts).
- **constraint-check** — Applies staffing independence, conflict, prior-role (including prior client board service), ethical-wall and availability rules to fit-scored candidates and refuses ineligible ones; it never clears a conflict or grants an exception. Use when the user says "is anyone conflicted?", "can we staff them?", "check independence for this engagement", "why can't we use the top match?" or "is this candidate independent of the client?". Do NOT use for corporate board or proxy-statement independence, extracting roles (use role-intake), loading the register (use bench-query), scoring candidates (use fit-score), drafting the slate (use slate-draft) or sales deal catch-up or pipeline review (use d365-sales-deal-catchup, d365-sales-pipeline-prioritizer or d365-sales-team-pipeline-review).
- **slate-draft** — Drafts the partner-ready staffing recommendation from constraint-check output (eligible slate, refused top matches, conflicts, utilisation context and gap statements); it is draft only and never sends, assigns or approves, and partner notes built from constraint-check output stay with slate-draft. Use when the user says "draft the recommendation", "build me a slate", "prepare the partner approval note", "summarize staffing options" or "write the resourcing approval draft". Do NOT use for general pages, one-pagers or apps (use create), client emails or thank-you notes (use an Outlook/email drafting skill), extracting roles (use role-intake), loading the bench (use bench-query), scoring or ranking candidates (use fit-score) or deciding eligibility (use constraint-check).

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
