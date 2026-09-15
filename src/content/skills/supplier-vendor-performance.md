---
name: Supplier & Vendor Performance Review
description: "A defensible supplier review pack assembled from records instead of a week of spreadsheet work: roll up the OTIF, defect and dispute scorecard with trends, cluster recurring issues with evidence, retrieve the governing trading term, and draft the agenda, corrective action request and commitment tracker."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/issue-cluster","name":"issue-cluster","description":"Clusters recurring issues by type and lane with record evidence, and maps scorecard breaches to governing trading terms, deterministically. Use on \"what keeps going wrong\", \"cluster the issues\", after scorecard-roll."},{"folder":"skills/record-pull","name":"record-pull","description":"Pulls PO, receipt, invoice, return, quality and dispute records for the vendor and review period into the rtl.supplier-vendor-performance.v1 contract. Use when the user says \"prep the vendor review for <supplier>\", \"pull the supplier records\", \"quarterly business review coming up\"."},{"folder":"skills/review-pack","name":"review-pack","description":"Drafts the vendor review agenda, corrective action request and commitment tracker from the contract payload. Use to close every review prep: \"draft the review pack\", \"build the QBR agenda\"."},{"folder":"skills/scorecard-roll","name":"scorecard-roll","description":"Rolls up the OTIF / defect / dispute scorecard by quarter with trend flags, deterministically, with the scorecard_roll engine. Use on \"how are they performing\", \"roll the scorecard\", after record-pull."},{"folder":"skills/term-retrieve","name":"term-retrieve","description":"Retrieves and quotes the governing contract or trading term for any performance question. Use on \"what does the agreement say about OTIF\", \"do we have a rebate right\", or after issue-cluster."}]
pluginConnectors: []
tags: [retailer, merchandising, supplier, vendor, otif, scorecard]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-07
updatedAt: 2026-09-08
bundle: bundles/supplier-vendor-performance.zip
---
Retail Wave 2 Cowork plugin: a defensible supplier review pack assembled from records instead of a week of spreadsheet work. Pulls PO, receipt, invoice, return and quality records; rolls up the OTIF / defect / dispute scorecard with trends (scorecard_roll); clusters recurring issues with evidence (issue_cluster); retrieves the governing trading term; drafts the review agenda, corrective action request and commitment tracker. Read-only: it does not change a PO, place a payment hold, amend a contract or deselect a supplier.
