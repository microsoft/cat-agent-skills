---
name: Audit Readiness
description: "Walk into the audit prepared: map the audit scope to the standard's clauses, gather and complete the evidence register, validate each piece of evidence against what the clause actually requires, flag every gap with a severity, and draft the readiness pack with owners and actions."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
tags: [quality, audit, compliance, iso-9001, iatf-16949, readiness]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-01
updatedAt: 2026-09-04
bundle: bundles/audit-readiness.zip
---
Manufacturing Wave 2 Cowork plugin: walk into the audit prepared. Maps the audit scope to the standard's clauses (clause_map engine); gathers the evidence register and checks completeness; validates evidence against clause requirements and flags gaps with severity - the Govern category is the core work here (gap_check engine); drafts the readiness pack with gaps, owners and actions. Draft-first; document-grounded.

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **evidence-gather** — Builds the evidence register for the mapped clauses from the uploaded QMS exports and document indexes. Use when the user says "gather the evidence", "what do we have on file", "build the evidence register", or after scope-map in a readiness run.
- **gap-check** — Validates the evidence register against clause requirements and flags gaps with severity - the explicit Govern step and the core work of this plugin, via the deterministic gap_check engine. Use when the user says "are we ready for the audit", "check for gaps", "will we pass", or after evidence-gather in a readiness run.
- **readiness-pack** — Drafts the audit-readiness pack - verdict, gaps with owners and actions, clause map, evidence index - from the contract payload. Use when the user says "draft the readiness pack", "prep the audit binder", or after gap-check in a readiness run.
- **scope-map** — Maps the audit scope to the standard's clauses and required evidence types with the deterministic clause_map engine. Use when the user says "we have an audit coming", "map the audit scope", "what clauses apply", or when an audit-readiness run begins.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
