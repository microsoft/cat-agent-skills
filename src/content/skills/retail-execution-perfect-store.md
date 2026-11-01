---
name: Retail Execution & Perfect Store
description: "A prepared call and a complete, evidenced visit report: assemble the pre-call plan, score the perfect-store gap deterministically against the channel standard, rank gaps by revenue impact rather than count, and draft the visit report, action register and suggested order for the rep to confirm."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
tags: [cpg, field-sales, retail-execution, perfect-store, dsr, visit-report]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-07
updatedAt: 2026-09-08
bundle: bundles/retail-execution-perfect-store.zip
---
CPG Wave 2 Cowork plugin: a prepared call and a complete, evidenced visit report. Assembles the pre-call plan (outlet profile, open actions, promo status, recent scan data); scores the perfect-store gap deterministically against the channel/cluster standard (visit_score); ranks gaps by revenue impact, not count (gap_rank); drafts the visit report, action register and suggested order for the rep to confirm. Photos attach as evidence, never scored by vision. It does not place the order, change the planogram or issue trade credit.

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **action-register** — Ranks gaps by revenue at stake with the gap_rank engine and builds the action register and suggested order for the rep to confirm. Use on "what do I fix first", "rank the gaps", "build my order", after gap-score.
- **gap-score** — Scores perfect-store compliance deterministically from the visit audit answers with the visit_score engine - photos attach as evidence, never scored by vision. Use after the visit: "score the visit", "how compliant is the store".
- **standard-retrieve** — Retrieves the perfect-store / picture-of-success standard, planogram and promo calendar for the outlet's channel and cluster. Use on "what's the standard for this outlet", "what should this store look like", after visit-prep.
- **visit-prep** — Assembles the pre-call plan for a specific outlet - profile, last visit's open actions, promotion status, recent scan performance - into the rtl.retail-execution-perfect-store.v1 contract. Use when the rep says "prep me for <outlet>", "what's the plan for today's calls", "pre-call for store <id>".
- **visit-report** — Drafts the evidenced visit report and action register from the contract payload. Use to close every visit: "write the visit report", "log the visit".

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
