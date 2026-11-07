---
name: Work Order Assistant
description: "Everything a technician or planner needs for a work order in one place: asset context, the relevant SOPs and OEM manuals, the most similar past jobs ranked, a parts-readiness check against the storeroom and supersession table, and clean drafted notes with the next best action."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
tags: [maintenance, work-order, cmms, sop, parts, storeroom]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 4.0.1
createdAt: 2026-08-01
updatedAt: 2026-11-06
bundle: bundles/work-order-assist.zip
---
Work Order Assist assembles cited work-order evidence, ranks similar prior work, checks parts snapshots and drafts technician/planner notes. Offline drafting only; no scheduling, assignment, reservations, purchasing, closure or CMMS writes. Human maintenance and safety review is required.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **knowledge-retrieve** — Attaches cited SOPs, manuals, prior fixes and usage evidence to draft inputs. Use for "retrieve the SOP", "find the manual section", "pull prior fixes", or "get parts history". Do NOT use for intake — use wo-intake instead; ranking — use similar-work-rank instead; stock checks — use parts-readiness instead; terminal notes — use work-order-writeup instead. No scheduling, orders or live write-back.
- **parts-readiness** — Computes cited stock sufficiency and replacement-part availability from supplied extracts. Use for "check parts readiness", "are the parts in stock", "is this part current", or "show stock shortages". Do NOT use for intake — use wo-intake instead; retrieval — use knowledge-retrieve instead; ranking — use similar-work-rank instead; terminal notes — use work-order-writeup instead. Never reserves, orders or schedules.
- **similar-work-rank** — Computes deterministic similarity and recurring-failure evidence from supplied history. Use for "rank similar past work", "have we repaired this before", "find the closest prior fix", or "explain similarity scores". Do NOT use for intake — use wo-intake instead; retrieval — use knowledge-retrieve instead; stock checks — use parts-readiness instead; terminal notes — use work-order-writeup instead. Local draft evidence only.
- **wo-intake** — Extracts cited work-order identity and asset context into draft inputs. Use for "intake this work order", "pull WO-4507", "extract the asset context", or "start the work-order packet". Do NOT use for evidence retrieval — use knowledge-retrieve instead; ranking — use similar-work-rank instead; stock checks — use parts-readiness instead; terminal notes — use work-order-writeup instead. Offline synthetic evidence only; no operational actions.
- **work-order-writeup** — Renders one fixed-layout cited Markdown work-order draft for technician/planner review. Use for "draft technician notes", "write up this work order", "give the planner summary", or "show the proposed next action". No audience-switching or document-conversion feature. Do NOT use for intake — use wo-intake; retrieval — use knowledge-retrieve; ranking — use similar-work-rank; stock checks — use parts-readiness. No CMMS write-back, closure, scheduling or purchasing, even when approved.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
