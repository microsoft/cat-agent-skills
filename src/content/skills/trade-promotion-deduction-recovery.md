---
name: Trade Promotion & Deduction Recovery
description: "Invalid deductions caught and disputed with evidence: match each claim to the governing promotion, allowance or trade term, classify validity deterministically and quantify the disputable amount with the calculation shown, and draft the dispute packet and post-event brief."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/claim-ingest","name":"claim-ingest","description":"Extracts deduction records and claim backup (PDFs, portal exports) into the rtl.trade-deduction-recovery.v1 contract. Use when the user says \"retailer deducted from the invoice\", \"work this deduction\", \"claim backup arrived\", or a deduction case begins."},{"folder":"skills/claim-match","name":"claim-match","description":"Matches each claim to its governing promotion or trade term deterministically with the claim_match engine. Use on \"does this deduction match anything we signed\", after term-retrieve."},{"folder":"skills/dispute-packet","name":"dispute-packet","description":"Drafts the dispute packet and the post-event promotion brief from the governed payload. Use to close every deduction case: \"draft the dispute\", \"build the packet for the retailer\"."},{"folder":"skills/term-retrieve","name":"term-retrieve","description":"Retrieves the governing trade terms, promotion calendar entries and agreements for the customer and period. Use on \"what did we actually sign\", \"what's the agreed rate\", after claim-ingest."},{"folder":"skills/validity-classify","name":"validity-classify","description":"Classifies deduction validity and quantifies the disputable amount with the calculation shown - the explicit Govern step - and runs promotion lift only where the RGM scoping allows. Use on \"is this deduction valid\", \"how much can we dispute\", \"should we write it off\", after claim-match."}]
pluginConnectors: []
tags: [cpg, rgm, trade-promotion, deduction, dispute, tpm]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-07
updatedAt: 2026-09-08
bundle: bundles/trade-promotion-deduction-recovery.zip
---
CPG Wave 2 Cowork plugin: invalid deductions caught and disputed with evidence. Extracts deduction records and claim backup; matches each claim to the governing promotion, allowance or trade term (claim_match); classifies validity deterministically and quantifies the disputable amount with the calculation shown - the explicit Govern step (deduction_classify); computes promotion lift on a fixed baseline only where the account P&L foundation exists per config scoping (promo_lift); drafts the dispute packet and post-event brief. It determines and drafts: it does not post credits, write off deductions, approve trade spend or change terms.
