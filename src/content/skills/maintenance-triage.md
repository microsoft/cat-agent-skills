---
name: Maintenance Triage
description: "Move a fault forward: read the fault note, alarm codes and asset history, rank the likely failure modes against OEM manuals and past work orders, prioritise by asset criticality and downtime cost, and draft the work-order update with a recommended action."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
tags: [maintenance, triage, cmms, reliability, failure-mode, work-order]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.3.1
createdAt: 2026-08-01
updatedAt: 2026-11-06
featured: true
bundle: bundles/maintenance-triage.zip
---
Maintenance Triage organizes fault evidence, retrieves supplied history, ranks likely causes and priorities, and drafts work-order updates. The bundled CP-200 pump rules are limited and require applicable OEM/domain review. No predictive maintenance, live CMMS connector, dispatch, notifications or repair authorization.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **criticality-rank** — Prioritizes the fault by asset criticality and downtime cost into a P1-P4 maintenance priority with a response target and cost estimate, deterministically. Use when the user says "how urgent is this", "what's the priority", "rank by criticality", "what will downtime cost", or after failure-mode-rank completes. Do NOT use for intake — use fault-intake; history retrieval — use history-retrieve; cause ranking — use failure-mode-rank; drafting — use work-order-update.
- **failure-mode-rank** — Ranks the likely failure modes for a fault against the failure-mode library, symptoms, alarm codes and repeat-failure history, deterministically. Use when the user says "what's the likely cause", "rank the failure modes", "diagnose this fault", "is this the real root cause?", or after history-retrieve completes. Do NOT use for intake — use fault-intake; history retrieval — use history-retrieve; priority — use criticality-rank; drafting — use work-order-update.
- **fault-intake** — Reads maintenance fault notes, operator reports, alarm/event logs, asset IDs and location into the mfg.maintenance-triage.v1 contract inputs. Use when the user says "triage this fault", "work this breakdown", "read the fault note for <asset>", "what's wrong with pump <id>", or when a maintenance triage run begins. Do NOT use for history retrieval — use history-retrieve; cause ranking — use failure-mode-rank; priority — use criticality-rank; drafting — use work-order-update. Not employee-injury recordability.
- **history-retrieve** — Retrieves the asset's maintenance history — prior work orders, similar failures, PM records — and the relevant OEM manual and troubleshooting sections, and attaches them to the mfg.maintenance-triage.v1 contract. Use when the user says "pull the history for <asset>", "has this failed before?", "find the manual section", "any prior work orders?", or after fault-intake completes. Do NOT use for intake — use fault-intake; cause ranking — use failure-mode-rank; priority — use criticality-rank; drafting — use work-order-update.
- **work-order-update** — Drafts the work-order update and recommended action from the triaged contract payload, with every determination cited to the manual, history and rules. Use when the user says "draft the work order", "write up the WO update", "what should we do", "recommend the fix", or after criticality-rank completes. Do NOT use for intake — use fault-intake; history retrieval — use history-retrieve; cause ranking — use failure-mode-rank; priority calculation — use criticality-rank.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
