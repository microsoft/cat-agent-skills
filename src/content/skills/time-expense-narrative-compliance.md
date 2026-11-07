---
name: Time & Expense Narrative Check
description: "Pre-bill-ready time narratives: gather cited calendar and document activity, draft grounded narratives, recommend phase and task codes, check entries against client billing guidelines and missing time, and build the pre-bill exception packet. Time entries only."
platforms: [Cowork]
type: plugin
category: professional-services
builtByMicrosoft: true
tags: [professional-services, time-entry, billing, pre-bill, billing-guidelines, wip]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.13
createdAt: 2026-11-06
updatedAt: 2026-11-06
bundle: bundles/time-expense-narrative-compliance.zip
---
Drafts and checks time-entry narratives: gathers cited calendar and document activity, drafts grounded narratives, recommends phase and task codes, checks client billing guidelines and missing time, and builds a draft pre-bill exception packet. Draft-first: it never submits time, approves a pre-bill or sends anything without explicit confirmation. Expense reports and receipts are out of scope.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **activity-pull** — Gathers engagement-scoped calendar metadata, document activity and timesheet rows into a cited activity packet, honoring the config/signal-sources.json in this skill (mailbox sources off unless the firm enables them). Use it first in the time-entry chain, before narratives are drafted, when the user says "pull my activity for this matter", "gather my week for time entry", "what did I work on for this engagement?", "collect my calendar and document activity for billing" or "build my activity packet for this period". Do NOT use for writing narratives (use narrative-draft), finding missing or unrecorded time (use guideline-check), general calendar questions such as "what is on my calendar today" (use the built-in calendar), or expense reports and receipts (out of scope: time entries only).
- **narrative-draft** — Drafts grounded time-entry narratives for entries that have none and offers cited suggested rewrites beside existing narratives without replacing them, never inventing roles, attendees or purpose. Use it after activity-pull (run that first if no activity packet exists) when the user says "write up my time", "draft my time entries", "turn my calendar into narratives", "suggest a better narrative for this entry" or "draft narratives from my week". Do NOT use for gathering raw activity (use activity-pull), choosing task codes (use code-map), judging whether an entry will be rejected (use guideline-check), sending, submitting or approving anything (exception-report answers those requests), or expense reports and receipts (out of scope: time entries only).
- **code-map** — Maps drafted time entries to the client phase and task codes with the deterministic code_map engine and flags submitted-code mismatches with citations; it recommends codes only. Use it after narrative-draft and before guideline-check when the user asks "what code should this entry use?", "map my time to billing codes", "is this task code wrong?", "check my phase and task codes" or "recommend phase codes for my entries". Do NOT use for gathering activity (use activity-pull), narrative wording (use narrative-draft), overall compliance or rejection risk (use guideline-check), recoding entries in the billing or time system (never; submit and approve requests go to exception-report), or expense reports and receipts (out of scope: time entries only).
- **guideline-check** — Checks drafted, coded time narratives against the client billing guidelines with the deterministic guideline_check engine: block billing, prohibited or vague terms, minimum detail, non-billable work, duplicates, increments and unrecorded time. Use it after code-map, or directly, when the user asks "will this narrative get rejected?", "is my time compliant?", "catch block billing", "find prohibited terms" or "find my missing time". Do NOT use for drafting or rewriting narratives (use narrative-draft), building the manager-facing exception packet (use exception-report), approving, submitting or writing off time (exception-report answers those requests), or expense reports and receipts (out of scope: time entries only).
- **exception-report** — Builds a cited DRAFT pre-bill exception packet from guideline-check for internal billing review (rejects, holds, privacy exclusions and missing time). Handles every submit, approve or write-off request only to refuse it; nothing is sent without explicit confirmation. Use for "show me the pre-bill exceptions", "what needs fixing before billing?", "build the WIP cleanup list", "summarize rejected narratives", "draft the pre-bill packet", "approve the pre-bill", "submit my time" or "write off these hours". Do NOT use for gathering activity (use activity-pull), drafting narratives (use narrative-draft), task codes (use code-map), an entry's compliance or missing time (use guideline-check), client invoices or emails (use the built-in email), or expense reports and receipts (out of scope).

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
