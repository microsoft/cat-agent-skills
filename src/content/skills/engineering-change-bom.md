---
name: Engineering Change & BOM
description: "Turn a change request into a decision: read the ECR, spec delta and BOM, trace impact across the BOM with where-used, classify form/fit/function impact and flag interface violations, roll up document and inventory dispositions, and draft the ECN with the affected-item list."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
tags: [engineering-change, ecr, ecn, bom, where-used, plm]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-01
updatedAt: 2026-09-04
bundle: bundles/engineering-change-bom.zip
---
Manufacturing Wave 2 Cowork plugin: turn a change request into a decision. Reads the ECR, spec/drawing delta and BOM; traces impact across the BOM with where-used (where_used engine); classifies form/fit/function impact, flags interface violations and rolls up document and inventory dispositions (bom_impact engine); checks against drawing standards and design rules; drafts the ECN with the affected-item list. Draft-first; document-grounded.

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **bom-impact** — Traces the change across the BOM with where-used and rolls up form/fit/function impact, interface violations, document updates and inventory disposition - deterministically. Use when the user says "what does this change affect", "run where-used", "impact analysis", or after ecr-ingest in a change run.
- **ecn-draft** — Drafts the engineering change notice with the affected-item list, document updates, dispositions and open requirements from the contract payload. Use when the user says "draft the ECN", "write up the change", or after standards-check in a change run.
- **ecr-ingest** — Reads the engineering change request, spec/drawing delta and BOM export into the mfg.engineering-change-bom.v1 contract. Use when the user says "assess this change request", "work ECR <id>", "what does this change touch", or when an engineering-change run begins.
- **standards-check** — Checks the proposed change against drawing standards and internal design rules, citing each rule applied. Use when the user says "does this meet the design rules", "standards check", "is this change allowed", or after bom-impact in a change run.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
