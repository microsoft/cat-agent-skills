---
name: My MS Learn Plugin
description: "Ask Cowork anything about Microsoft products, services, or APIs and get answers grounded in official Microsoft Learn documentation."
platforms: [Cowork]
type: plugin
tags: [microsoft-learn, documentation, mcp, research]
author: Adriana Tamayo
authorUrl: "https://github.com/adrianatruji"
authorGithub: adrianatruji
version: 1.0.0
createdAt: 2026-10-09
updatedAt: 2026-10-09
bundle: bundles/ms-learn-plugin.zip
---
Grounds Cowork in official Microsoft documentation. Whenever you ask about Microsoft (MS / MSFT) products, services, APIs, docs, or guidance, Cowork looks it up on Microsoft Learn through the official Microsoft Learn MCP server and answers with up-to-date, cited content.

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Connectors

- **Microsoft Learn** (`mslearn-mcp`) — Use whenever the user asks about Microsoft, MS, or MSFT documentation, products, services, APIs, how-tos, or official guidance. Searches and fetches official Microsoft Learn content to ground the answer.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
