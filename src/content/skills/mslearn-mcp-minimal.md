---
name: Microsoft Learn MCP (minimal)
description: Minimal connector-only Cowork plugin that connects to the official Microsoft Learn MCP server. Test submission for pipeline validation.
platforms: [Cowork]
type: plugin
tags: [test, mcp, microsoft-learn]
author: Adriana Tamayo
authorUrl: "https://github.com/adrianatruji"
authorGithub: adrianatruji
version: 1.0.0
createdAt: 2026-10-08
updatedAt: 2026-10-08
bundle: bundles/mslearn-mcp-minimal.zip
---
Minimal connector to the official Microsoft Learn MCP server for Cowork testing.

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Connectors

- **Microsoft Learn** (`mslearn-mcp`) — Microsoft Learn MCP server.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
