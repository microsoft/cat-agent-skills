---
name: Engineering Change & BOM
description: "Turn a change request into a decision: read the ECR, spec delta and BOM, trace impact across the BOM with where-used, classify form/fit/function impact and flag interface violations, roll up document and inventory dispositions, and draft the ECN with the affected-item list."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/bom-impact","name":"bom-impact","description":"Traces the change across the BOM with where-used and rolls up form/fit/function impact, interface violations, document updates and inventory disposition - deterministically. Use when the user says \"what does this change affect\", \"run where-used\", \"impact analysis\", or after ecr-ingest in a change run."},{"folder":"skills/ecn-draft","name":"ecn-draft","description":"Drafts the engineering change notice with the affected-item list, document updates, dispositions and open requirements from the contract payload. Use when the user says \"draft the ECN\", \"write up the change\", or after standards-check in a change run."},{"folder":"skills/ecr-ingest","name":"ecr-ingest","description":"Reads the engineering change request, spec/drawing delta and BOM export into the mfg.engineering-change-bom.v1 contract. Use when the user says \"assess this change request\", \"work ECR <id>\", \"what does this change touch\", or when an engineering-change run begins."},{"folder":"skills/standards-check","name":"standards-check","description":"Checks the proposed change against drawing standards and internal design rules, citing each rule applied. Use when the user says \"does this meet the design rules\", \"standards check\", \"is this change allowed\", or after bom-impact in a change run."}]
pluginConnectors: []
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
