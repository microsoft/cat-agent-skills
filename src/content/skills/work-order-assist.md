---
name: Work Order Assistant
description: "Everything a technician or planner needs for a work order in one place: asset context, the relevant SOPs and OEM manuals, the most similar past jobs ranked, a parts-readiness check against the storeroom and supersession table, and clean drafted notes with the next best action."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
tags: [maintenance, work-order, cmms, sop, parts, storeroom]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-08-01
updatedAt: 2026-09-04
bundle: bundles/work-order-assist.zip
---
Manufacturing Wave 1 Cowork plugin: everything for a work order in one place. Pulls the current work order and asset context, retrieves the relevant SOPs, OEM manuals, prior fixes and parts history, ranks the most similar past work (deterministic similar_work) and checks parts readiness against the storeroom and supersession table (deterministic parts_readiness), then drafts clean technician notes or a planner summary with the next-best action. Draft-first; document-grounded. NOT auto-scheduling or CMMS write-back (that is Wave 3).

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **knowledge-retrieve** — Retrieves the SOPs, OEM manuals, prior fixes and parts history relevant to a work order and attaches them to the mfg.work-order-assist.v1 contract. Use when the user says "find the SOP and manual", "pull prior fixes for <asset>", "get the parts history", "what did we do last time", or after wo-intake completes.
- **parts-readiness** — Checks whether a work order's parts are ready — storeroom stock, shortages, and part supersession — and computes a READY/PARTIAL/BLOCKED status, deterministically. Use when the user says "are the parts in stock", "check parts readiness", "can we schedule this", "is that part still current", or after similar-work-rank completes.
- **similar-work-rank** — Ranks the most similar past work orders for the current job and surfaces recurring failures and superseding fixes, deterministically. Use when the user says "find similar past work", "have we done this before", "what's the closest prior fix", "is this a repeat failure", or after knowledge-retrieve completes.
- **wo-intake** — Pulls the current work order and its asset context into the mfg.work-order-assist.v1 contract inputs. Use when the user says "assemble the work order packet", "pull up WO <id>", "get me everything for this work order", "work order for <asset>", or when a Work Order Assistant run begins.
- **work-order-writeup** — Drafts the technician notes or planner summary for a work order from the assembled contract payload, with every determination cited to the SOP, manual, history and parts data. Use when the user says "draft the technician notes", "write up the work order", "give me the planner summary", "what's the next best action", or after parts-readiness completes.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
