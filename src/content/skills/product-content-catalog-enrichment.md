---
name: Product Content & Catalog Enrichment
description: "Turn incomplete supplier data into channel-ready, claim-safe product records: normalise attributes against the taxonomy with GTIN validation, score completeness per channel, validate claims and regulated terms against the approved claim library, and draft the descriptions and review packet."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
tags: [retailer, merchandising, pim, gdsn, gtin, catalog]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.5
createdAt: 2026-09-05
updatedAt: 2026-11-06
bundle: bundles/product-content-catalog-enrichment.zip
---
Product Content Enrichment turns supplier item sheets into draft product records for a channel. It maps fields to your taxonomy, validates GTIN check digits, scores completeness, checks marketing claims against your approved claim library and drafts copy with a review packet. It never publishes, approves a claim or changes the taxonomy.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **source-ingest** — Structures a supplier's product package (item spreadsheet, spec sheets, marketing copy) into the rtl.product-content-enrichment.v1 entry hop - one record per SKU with the GTIN and every supplier field verbatim. Use when the user says "enrich these SKUs", "supplier sent the item sheet", "get these products channel-ready", "ingest the supplier item sheet", "start an enrichment batch" or "new SKUs from <supplier>". Do NOT use for sales, sell-through or trade-terms analysis - use xlsx or the trade-deduction skills instead; do NOT normalise, score or draft here - use attribute-normalize, completeness-score or content-draft instead.
- **attribute-normalize** — Maps supplier product fields to the retailer taxonomy through the mapping table only, converts units with the calculation shown, and validates every GTIN check digit (GS1). Use after source-ingest, or when the user says "map these to our taxonomy", "are these GTINs valid", "validate these GTINs", "check the GS1 check digit", "normalise the supplier attributes" or "which supplier columns are unmapped". Do NOT use for ad-hoc unit conversions or non-product data - answer in chat instead; do NOT use for completeness or missing fields - use completeness-score instead; do NOT use for claim wording - use claim-check instead.
- **completeness-score** — Product content / catalog completeness - scores each SKU's normalised attributes against the channel's required fields and names the missing fields per SKU, with the customer's completeness floor applied. Use after attribute-normalize, or when the user says "how complete are these SKUs", "what's missing per SKU", "completeness per SKU", "catalog gap report for <channel>", "which required product fields are blank" or "is this batch ready for the copy team". Do NOT use for store-visit or perfect-store compliance scoring - use the retail-execution gap-score (visit_score) instead; do NOT use for claim wording - use claim-check instead; do NOT use for project or task completeness - plain chat.
- **claim-check** — Validates product marketing claims and regulated terms in supplier copy against the approved claim library for that GTIN and market - the explicit Govern step. Use after completeness-score, or when the user says "is this copy safe", "can we say antibacterial", "check the claims", "validate the marketing claims", "is this regulated wording allowed in <market>" or "do we have substantiation for <claim>". Do NOT use for trade-deduction, invoice or insurance claims - use claim-ingest / claim-match instead; do NOT use to approve or add a claim to the library - that is the claim owner's decision; do NOT use to draft copy - use content-draft instead.
- **content-draft** — Drafts channel product descriptions, comparison copy and the steward review/approval packet from the governed enrichment payload, using normalised attributes and library-approved claims only. Use to close an enrichment batch, or when the user says "draft the product copy", "build the review packet", "write the channel listing copy", "draft the approval packet", "comparison copy for these SKUs" or "close the enrichment batch". Do NOT use for social posts, decks, blog or general marketing copy - use pptx, docx or plain drafting instead; do NOT publish to channel or approve claims - hand the DRAFT to the steward; do NOT use before claim-check has run - use claim-check instead; do NOT map attributes or validate GTINs - use attribute-normalize instead.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
