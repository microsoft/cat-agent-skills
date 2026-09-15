---
name: Product Content & Catalog Enrichment
description: "Turn incomplete supplier data into channel-ready, claim-safe product records: normalise attributes against the taxonomy with GTIN validation, score completeness per channel, validate claims and regulated terms against the approved claim library, and draft the descriptions and review packet."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/attribute-normalize","name":"attribute-normalize","description":"Normalises supplier fields to the taxonomy and validates GTIN check digits with the deterministic attribute_normalize engine. Use after source-ingest, or on \"map these to our taxonomy\", \"are these GTINs valid\"."},{"folder":"skills/claim-check","name":"claim-check","description":"Validates marketing claims and regulated terms against the approved claim library - the explicit Govern step - with the deterministic claim_check engine. Use on \"is this copy safe\", \"can we say antibacterial\", \"check the claims\", after gap-score."},{"folder":"skills/content-draft","name":"content-draft","description":"Drafts channel descriptions, comparison copy and the review/approval packet from the governed payload. Use to close every enrichment batch: \"draft the product copy\", \"build the review packet\"."},{"folder":"skills/gap-score","name":"gap-score","description":"Scores per-SKU completeness against the channel's required fields with the deterministic completeness_score engine. Use on \"how complete are these\", \"what's missing per SKU\", after attribute-normalize."},{"folder":"skills/source-ingest","name":"source-ingest","description":"Ingests supplier spreadsheets, spec sheets and copy into the rtl.product-content-enrichment.v1 contract. Use when the user says \"enrich these SKUs\", \"supplier sent the item sheet\", \"get these products channel-ready\", or an enrichment batch begins."}]
pluginConnectors: []
tags: [retailer, merchandising, pim, gdsn, gtin, catalog]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-05
updatedAt: 2026-09-08
bundle: bundles/product-content-catalog-enrichment.zip
---
Retail Wave 1 Cowork plugin (retailer-side, CPG-enabled): turn incomplete supplier data into channel-ready, claim-safe product records. Ingests supplier sheets and specs; normalises attributes against the taxonomy with GTIN validation (attribute_normalize); scores completeness per channel (completeness_score); validates claims and regulated terms against the approved claim library - the explicit Govern step (claim_check); drafts descriptions and the review packet. Ends at an approval-ready draft record: it does not publish to channel, approve a regulated claim or change the taxonomy.
