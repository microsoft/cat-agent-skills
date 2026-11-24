---
name: Safety Incident Assist
description: "Prepare cited incident drafts from supplied local evidence, with draft classification, proposed unsent routing, and a write-up for qualified EHS review."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
tags: [safety, ehs, incident, manufacturing, drafting]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 2.0.0-rc.7
createdAt: 2026-11-10
updatedAt: 2026-11-10
bundle: bundles/safety-incident-assist.zip
licenseName: MIT
licenseFile: LICENSE
---
Safety Incident Assist turns authorized supplied incident files into cited, privacy-conscious drafts for qualified EHS review: intake, local evidence and history, draft classification, proposed unsent routing, and write-up. Use only in an organization-approved environment, with human review. No live retrieval, official regulatory or clinical determinations, equipment instructions, sending, filing, or closure. Source candidate 2.0.0-rc.7 is represented by numeric manifest version 2.0.0 for packaging compatibility only; this does not promote it to a stable or certified release.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **ehs-knowledge-retrieve** — Attaches cited local OSHA, ISO summaries, JHA and policies and computes supplied-log history. Use for "find cited local safety evidence", "pull the OSHA criteria", "get the JHA", "attach local EHS evidence", or "have we had this incident before". Do NOT use for incident intake, recordability decisions or drafting — use incident-intake, severity-recordability or incident-writeup. No live retrieval; EHS REVIEW REQUIRED.
- **incident-intake** — Preserves cited authorized user-supplied incident files, including real incidents, as v2 inputs for human-reviewed drafts only. Use for "preserve conflicting incident accounts", "intake this incident", "process this safety report", "extract incident facts", or "intake this near miss". Do NOT use for classification, routing or terminal drafting — use severity-recordability, routing-notify or incident-writeup respectively. No live retrieval or official determinations; EHS REVIEW REQUIRED.
- **incident-writeup** — Revalidates and recomputes every terminal v2 hop, then renders a null-aware local Markdown draft and blank RCA template. Use for "prepare an evidence-grounded incident draft", "draft the incident summary", "write up the incident", "give me the RCA template", or "prepare the OSHA writeup". Do NOT use for intake, classification or routing — use incident-intake, severity-recordability or routing-notify. No operational actions; EHS REVIEW REQUIRED.
- **routing-notify** — Computes proposed investigators and unsent recipients from validated local classification, history and governance. Use for "propose unsent incident recipients", "who investigates this", "route this incident", "who do we notify", or "start the OSHA clock" (only to explain the blocked clock). Do NOT use for classification or terminal drafting — use severity-recordability or incident-writeup. Never sends, files or starts a clock; EHS REVIEW REQUIRED.
- **severity-recordability** — Runs the deterministic local v2 draft classifier; reporting/deadlines remain undetermined. Use for "explain blocked reporting determination", "is this recordable", "classify this incident", "what severity is this", or "is this OSHA reportable". Do NOT use for source intake, history retrieval or routing — use incident-intake, ehs-knowledge-retrieve or routing-notify. No diagnosis or operational decision; EHS REVIEW REQUIRED.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
