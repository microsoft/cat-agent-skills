---
name: Supplier Qualification
description: "Qualify a new supplier on the evidence: gather the dossier of certs, financials, audits and PPAP elements, score risk across quality, financial and geographic dimensions, compare against the approved vendor list and category requirements, and draft the qualification memo with conditions."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
tags: [supply-chain, sourcing, supplier-qualification, ppap, apqp, risk]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-01
updatedAt: 2026-09-04
bundle: bundles/supplier-qualification.zip
---
Manufacturing Wave 2 Cowork plugin: qualify a new supplier. Gathers the supplier dossier (certs, financials, audits, PPAP elements); scores risk across quality, financial and geographic dimensions (risk_score engine); compares against the approved vendor list and category requirements (avl_match engine); drafts the qualification memo with conditions. Draft-first; document-grounded.

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **avl-compare** — Compares the candidate against the approved vendor list and category requirements and produces the banded recommendation, using the deterministic avl_match engine. Use when the user says "how do they compare to our current vendors", "check the AVL", "should we qualify them", or after risk-score in a run.
- **dossier-ingest** — Gathers the supplier's qualification documents - certificates, financials, audit reports, PPAP elements - into the mfg.supplier-qualification.v1 contract. Use when the user says "qualify this supplier", "review the supplier package", "new vendor for <category>", or when a qualification run begins.
- **qualification-memo** — Drafts the supplier qualification memo for approval from the contract payload - outcome, conditions, risk detail, AVL position. Use when the user says "draft the qualification memo", "write it up for approval", or after avl-compare in a run.
- **risk-score** — Scores supplier risk across quality, financial and geographic dimensions with the deterministic risk_score engine. Use when the user says "score this supplier", "how risky are they", "run the risk assessment", or after dossier-ingest in a qualification run.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
