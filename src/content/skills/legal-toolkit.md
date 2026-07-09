---
name: Legal Toolkit
description: "A Cowork plugin bundling contract-analysis and clause-extraction skills, plus a case-law connector."
platforms: [Cowork]
type: plugin
tags: [legal, contracts, plugin, sample]
author: CAT Community
authorUrl: "https://github.com/microsoft/cat-agent-skills"
version: 1.0.0
createdAt: 2026-07-09
updatedAt: 2026-07-09
bundle: bundles/legal-toolkit.zip
---
A Cowork plugin bundling two legal-review skills — contract analysis and clause extraction — plus an optional connector to a case-law database. Use it to review agreements, surface risky clauses, and pull structured clause data during a Cowork session.

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **contract-analysis** — Use this skill whenever the user asks to review a contract, find risky clauses, or summarize an agreement's key terms.
- **clause-extractor** — Use this skill whenever the user asks to extract specific clauses (e.g. liability, termination, IP) from a contract into a structured table.

## Connectors

- **Case Law Database** (`case-law-db`) — Read-only access to case law and statute lookups.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
