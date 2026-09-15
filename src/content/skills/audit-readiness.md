---
name: Audit Readiness
description: "Walk into the audit prepared: map the audit scope to the standard's clauses, gather and complete the evidence register, validate each piece of evidence against what the clause actually requires, flag every gap with a severity, and draft the readiness pack with owners and actions."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/evidence-gather","name":"evidence-gather","description":"Builds the evidence register for the mapped clauses from the uploaded QMS exports and document indexes. Use when the user says \"gather the evidence\", \"what do we have on file\", \"build the evidence register\", or after scope-map in a readiness run."},{"folder":"skills/gap-check","name":"gap-check","description":"Validates the evidence register against clause requirements and flags gaps with severity - the explicit Govern step and the core work of this plugin, via the deterministic gap_check engine. Use when the user says \"are we ready for the audit\", \"check for gaps\", \"will we pass\", or after evidence-gather in a readiness run."},{"folder":"skills/readiness-pack","name":"readiness-pack","description":"Drafts the audit-readiness pack - verdict, gaps with owners and actions, clause map, evidence index - from the contract payload. Use when the user says \"draft the readiness pack\", \"prep the audit binder\", or after gap-check in a readiness run."},{"folder":"skills/scope-map","name":"scope-map","description":"Maps the audit scope to the standard's clauses and required evidence types with the deterministic clause_map engine. Use when the user says \"we have an audit coming\", \"map the audit scope\", \"what clauses apply\", or when an audit-readiness run begins."}]
pluginConnectors: []
tags: [quality, audit, compliance, iso-9001, iatf-16949, readiness]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-01
updatedAt: 2026-09-04
bundle: bundles/audit-readiness.zip
---
Manufacturing Wave 2 Cowork plugin: walk into the audit prepared. Maps the audit scope to the standard's clauses (clause_map engine); gathers the evidence register and checks completeness; validates evidence against clause requirements and flags gaps with severity - the Govern category is the core work here (gap_check engine); drafts the readiness pack with gaps, owners and actions. Draft-first; document-grounded.
