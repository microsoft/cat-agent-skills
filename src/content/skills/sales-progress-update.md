---
name: Sales Progress Update
description: "Create a sales progress update covering work completed, deal movement, forecast position, and help needed."
agentDescription: "Creates or refreshes a sales progress update for a manager or team about work done, deal movement, pending outcomes, supported forecast position, and help needed. Use when asked to \"create my weekly sales update\", \"refresh my sales progress deck\", \"report my forecast position\", \"where do I stand against my quarter forecast\", or \"catch my manager up on committed deals\". Do NOT use for non-sales project updates, a since-date deal change digest, momentum or blocker analysis, meeting prep, or outreach drafting."
platforms: [Cowork]
category: sales
builtByMicrosoft: true
tags: [sales, reporting, forecasting]
author: Copilot Cowork team
authorUrl: "https://www.microsoft.com/en-us/copilot/features/cowork"
createdAt: 2026-10-31
---
# Sales Progress Update

## When NOT to Use

Invoke only for a sales-related progress update or sales forecast-position report. Do not invoke for general project, personal, operational, or other non-sales progress updates, or for standalone seller-activity tasks that do not request a sales progress update. A user's seller role or the presence of sales activity is not sufficient to trigger this skill.

For standalone deal momentum and blocker analysis, use `customer-engagement-and-deal-risk-insights`.

## Purpose and core job

Help the seller show work done, progress made, pending outcomes, quarter position, and help needed in the format expected by their manager or team. The core job is: “Show what I’ve worked on, what moved, what’s still pending, and where I stand against my quarter forecast.”

Trigger requests include “Create my weekly sales update,” “Update my sales progress deck,” “Where do I stand against this quarter’s forecast,” “Catch my manager up on committed deals,” and “Add stuck-deal discussion to existing update.”

## Workflow
1. Confirm inputs (below) and ask once for an export, template, or prior update.
2. Select the mode automatically: new update or refresh.
3. Gather and interpret evidence from CRM, mail, meetings, and uploads.
4. Calculate quarter position in code; keep forecast separate from quota.
5. Incorporate a stuck-deal recap when requested.
6. Refresh and carry forward: mark what is new, changed, or resolved.
7. Build the Output pages, save the artifact, and verify the save before reporting.

## Confirm inputs

Check the materials already provided and the available CRM access. Ask once: “Would you like to upload a pipeline export, template, or previous update before I begin? You can also continue with the information already available.” Do not repeat this question if it has already been answered, and do not ask the user to select a data mode.

Establish seller or team scope, reporting period, audience, and the previous update. If the period is absent, use a clearly stated weekly default. Verify fiscal-quarter boundaries before making quarter-specific claims.

## Select the mode automatically

With live CRM, cover forecast and seller work, verifying fields individually. With an uploaded pipeline only, cover the snapshot forecast and seller work; identify the snapshot date separately from newer observations. With neither, report seller work and customer progress, not a verified pipeline forecast.

When both CRM and an upload are available, compare their dates and scope, and flag conflicts. A template defines the format, not the reliability of the evidence. Treat missing fields as unknown.

## Gather and interpret evidence

Use authorized email, Teams, meetings, transcripts, calendar entries, documents and files, CRM records, notes, milestones and activities, uploaded pipeline data, and previous updates. Select meaningful seller work rather than listing every interaction.

For each item, capture what happened and when, the deal or account, the result or pending outcome, and the next action, owner, and agreed date where supported. Do not mix opportunities belonging to the same account. A scheduled meeting is not evidence that the meeting occurred.

Use the previous update as the comparison baseline. If there is no previous update, report current state and dated events without inventing changes.

## Output

Deliver both a concise chat summary and one saved primary editable artifact, following the
sections below. The artifact must show seller sales related progress, pending outcomes and
help needed.

### Chat summary

Summarize the reporting period, supported quarter or period position, key progress, pending
outcomes, and help needed. Highlight the next priority and material evidence gaps; link the
saved update.

### Artifact content

Use the user’s format first and preserve the structure of an existing document or deck. When no format exists, use the five-slide starter below; a Word or one-page equivalent is also supported. Keep slides concise and place supporting evidence in notes.

| Starter page | Required content |
| --- | --- |
| Quarter at a glance | Forecast target, closed-won, remaining OPEN Commit, gap, and key developments. Distinguish forecast from quota. |
| Work done | Meetings, demos, proposals, outreach, and internal coordination by deal or account, with outcomes or pending results. Include future-quarter work. |
| Committed-deal progress | Deal, value, expected close, recent progress, remaining milestones or blocker, and next action. |
| Risks, blockers, and help | Evidence, timing impact, blocker ownership, attempts made, and the specific support or decisions needed. |
| Next-period priorities | Actions, owners, dates, intended outcomes, carryforward commitments, and potential gap coverage. Do not assume wins. |

Without pipeline evidence, change the first page to “Period at a glance” and the third to “Active customer engagements.” Retain work, risks, help, and the plan. Omit unsupported amounts, stages, categories, dates, and forecast exposure.

Include this disclosure when pipeline evidence is unavailable: “This update reflects available work and customer-engagement evidence, not a verified pipeline or forecast.”

### Artifact selection

Choose one format for the complete sales progress update, respecting the user's requested format:

- **PowerPoint:** Default for a manager or team presentation, including the five-slide starter.
- **Word:** For a narrative update or one-page document.
- **Markdown:** When requested or the preferred format is unavailable or fails.

Use authorized, format-specific workflows. Keep content concise and styling simple. Plan changes together and apply them in as few supported batches as practical. Update authorized existing artifacts without creating duplicates or changing unrelated content. Follow Delivery and control for saving and reporting.

### Delivery and control

Verify the save before reporting success and provide the actual link or location. If saving fails, disclose it and provide clearly labeled unsaved content in chat. Keep slides concise, with evidence in notes; use simple headings and tables in documents.

## Calculate quarter position

Calculate only when quarter scope, currency, and measurement basis are verified and consistent. Use code for the calculation: Gap = forecast target − closed-won − remaining OPEN Commit. Exclude won deals from open Commit and count each opportunity once.

Explain that this gap assumes the remaining Commit closes; it is not guaranteed attainment. If the result is negative, show the above-target amount. If necessary data is missing, omit the calculation and explain why.

## Incorporate a stuck-deal recap

Add the recap to the relevant deal section in the same update, rather than creating a separate artifact by default. Include blocker and context, options, actual decisions, agreed actions with owners and dates, unresolved questions, and help needed. Do not convert suggestions into commitments or discussions into decisions.

## Refresh and carry forward

Distinguish new items from carried-forward items. Move resolved blockers out of the active risk list, but retain material resolutions in progress reporting. Update completed, changed, and overdue commitments. Preserve meaningful seller effort even when there is no response or stage advance.

## Guardrails

- Activity is not impact, but seller work must remain visible. Lower activity alone is not a risk. Missing access means incomplete evidence, not inactivity. Do not evaluate or rank employees.
- Do not invent wins, values, probabilities, roles, or commitments. Do not present a snapshot as live data. Separate observed evidence from interpretation and show conflicts.
- Requested artifact edits are permitted. Do not send the update, change CRM records, or establish recurrence without explicit user intent.

## Success criteria

The update answers six questions: Where do I stand? What work have I done? What moved? What is pending? What comes next? What help do I need?
