---
name: Supplier Qualification
description: "Qualify a new supplier on the evidence: gather the dossier of certs, financials, audits and PPAP elements, score risk across quality, financial and geographic dimensions, compare against the approved vendor list and category requirements, and draft the qualification memo with conditions."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/avl-compare","name":"avl-compare","description":"Compares the candidate against the approved vendor list and category requirements and produces the banded recommendation, using the deterministic avl_match engine. Use when the user says \"how do they compare to our current vendors\", \"check the AVL\", \"should we qualify them\", or after risk-score in a run."},{"folder":"skills/dossier-ingest","name":"dossier-ingest","description":"Gathers the supplier's qualification documents - certificates, financials, audit reports, PPAP elements - into the mfg.supplier-qualification.v1 contract. Use when the user says \"qualify this supplier\", \"review the supplier package\", \"new vendor for <category>\", or when a qualification run begins."},{"folder":"skills/qualification-memo","name":"qualification-memo","description":"Drafts the supplier qualification memo for approval from the contract payload - outcome, conditions, risk detail, AVL position. Use when the user says \"draft the qualification memo\", \"write it up for approval\", or after avl-compare in a run."},{"folder":"skills/risk-score","name":"risk-score","description":"Scores supplier risk across quality, financial and geographic dimensions with the deterministic risk_score engine. Use when the user says \"score this supplier\", \"how risky are they\", \"run the risk assessment\", or after dossier-ingest in a qualification run."}]
pluginConnectors: []
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
