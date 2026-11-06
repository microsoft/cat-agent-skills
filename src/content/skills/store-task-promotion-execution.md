---
name: Store Task & Promotion Execution
description: "Turn the HQ campaign pack into a store-specific, verifiable execution plan before launch day: map requirements to the store's format and cluster, flag pricing and signage conflicts deterministically, rank exceptions by revenue impact, and draft the readiness checklist and shift brief."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
tags: [retailer, store-operations, promotion, campaign, execution, readiness]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.5
createdAt: 2026-09-05
updatedAt: 2026-11-06
bundle: bundles/store-task-promotion-execution.zip
---
Store Task Promotion Execution prepares a store for a promotion launch. It reads the HQ campaign pack, price file and the store's records, tests readiness for missing items, fixture and price conflicts, ranks exceptions by revenue at stake and drafts the checklist, shift brief and escalation. It never changes POS prices, planograms or schedules.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **pack-ingest** — Ingests the HQ campaign pack, price-change file, planogram/signage list and task list for a store promotion launch into the rtl.store-task-promotion-execution.v1 contract (pack.json, the entry hop). Use when the user says "new campaign pack landed", "prep the store for the launch", "are we ready for Monday's promo", "get the promo pack into the contract", "ingest the campaign pack for store <id>", or when a store assignment arrives. Do NOT use for supplier PO delays or shortages — use disruption-intake instead; not for supplier item sheets or catalog SKU enrichment — use source-ingest instead; not for the store's own records — use store-map instead; not for the readiness verdict — use readiness-check instead.
- **store-map** — Retrieves one store's profile for the promotion readiness test — format, cluster, fixtures, received assets, completed tasks, prior execution history and current shelf prices — from the store master, receiving, task-system and POS exports into store.json + shelf-prices.json. Use after pack-ingest, or when the user asks "what does this store actually have", "pull the store profile for <id>", "what's been received at the store", "which launch tasks are done", "get the current shelf prices for store <id>". Do NOT use for floor plans, department layouts or wayfinding maps — use a store layout / planogram tool instead; not for the readiness verdict — use readiness-check instead; not for ingesting the HQ pack — use pack-ingest instead.
- **readiness-check** — Tests a store's readiness for a promotion launch against the campaign pack, deterministically, with the readiness_check engine — applicability, completeness, fixture conflicts, price integrity (promo vs shelf, pack vs price file) and the confidence floor. Use when the user asks "are we ready for the launch", "any gaps for launch", "check the pack against my store", "run the readiness check for store <id>", "is the store actually ready or just saying so". Do NOT use for maintenance work orders or spare parts — use parts-readiness instead; not for ingesting the pack — use pack-ingest instead; not for the store records — use store-map instead; not for ranking or the brief — use exception-raise instead for the ranking, use brief-draft instead for the brief.
- **exception-raise** — Ranks a store's promotion-launch readiness exceptions — missing kits, fixture conflicts, price conflicts from checked.json — by weekly revenue at stake with the exception_rank engine, and raises the exception list for the store and district manager. Use after readiness-check, or when the user asks "what do we fix first for the launch", "rank the readiness exceptions", "which gaps cost the most before Monday", "raise the exception list for the store", "what goes to the district manager". Do NOT use for product-content or listing completeness gaps — use the catalog enrichment completeness-score instead, or action-register instead for the fix order; not for the readiness test itself — use readiness-check instead; not for the checklist or shift brief — use brief-draft instead.
- **brief-draft** — Drafts the store readiness checklist, the shift brief in store language, and the exception escalation for a promotion launch from the ranked contract payload — draft-first, nothing sent. Use to close every execution run — "draft the shift brief", "write up the readiness pack", "build the launch checklist for store <id>", "what does the team do each shift", "write the escalation for the district manager". Do NOT use for field-sales store visit reports or action registers — use visit-report instead; not for the readiness test or ranking — use readiness-check instead for the test, use exception-raise instead for the ranking; not for ingesting the pack or store records — use pack-ingest instead for the pack, use store-map instead for the store records.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
