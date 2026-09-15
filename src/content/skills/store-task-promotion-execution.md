---
name: Store Task & Promotion Execution
description: "Turn the HQ campaign pack into a store-specific, verifiable execution plan before launch day: map requirements to the store's format and cluster, flag pricing and signage conflicts deterministically, rank exceptions by revenue impact, and draft the readiness checklist and shift brief."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/brief-draft","name":"brief-draft","description":"Drafts the store readiness checklist, the shift brief in store language, and the exception escalation from the contract payload. Use to close every execution run - \"draft the shift brief\", \"write up the readiness pack\"."},{"folder":"skills/exception-raise","name":"exception-raise","description":"Ranks readiness exceptions by revenue at stake with the exception_rank engine and raises the exception list. Use when the user asks \"what do we fix first\", \"rank the gaps\", or after readiness-check."},{"folder":"skills/pack-ingest","name":"pack-ingest","description":"Ingests the HQ campaign pack, price file, planogram and task list into the rtl.store-task-promotion-execution.v1 contract. Use when the user says \"new campaign pack landed\", \"prep the store for the launch\", \"are we ready for Monday's promo\", or when a store assignment arrives."},{"folder":"skills/readiness-check","name":"readiness-check","description":"Tests store readiness against the campaign pack deterministically - applicability, completeness, fixture conflicts and price integrity - with the readiness_check engine. Use when the user asks \"are we ready\", \"any gaps for launch\", \"check the pack against my store\"."},{"folder":"skills/store-map","name":"store-map","description":"Retrieves the store profile - format, cluster, fixtures, received assets, completed tasks, prior execution history - for the readiness test. Use after pack-ingest, or when the user asks \"what does this store actually have\"."}]
pluginConnectors: []
tags: [retailer, store-operations, promotion, campaign, execution, readiness]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-05
updatedAt: 2026-09-08
bundle: bundles/store-task-promotion-execution.zip
---
Retail Wave 1 Cowork plugin: turn the HQ campaign pack into a store-specific, verifiable execution plan before launch day. Ingests the pack, price file, planogram and task list; maps requirements to the store's format and cluster; tests completeness and flags pricing and signage conflicts deterministically (readiness_check engine); ranks exceptions by revenue impact (exception_rank engine); drafts the readiness checklist, shift brief and exception list. It does not change POS prices, planograms, labour schedules or campaign funding.
