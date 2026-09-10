---
name: Quality Inspection & Nonconformance
description: "Clear an inspection lot end to end: read the part spec, drawing, inspection plan, CoC and measurement export, compare every actual against tolerance, grade each defect by severity and disposition, and draft the nonconformance report with every call cited back to the spec."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/defect-grade","name":"defect-grade","description":"Grades each out-of-tolerance characteristic by severity and recommends a disposition (use-as-is / rework / scrap / return-to-vendor / hold-for-review) using the deterministic disposition rules engine. Use when the user says \"grade the defects\", \"what disposition?\", \"how bad is it?\", \"can we ship it?\", or after tolerance-check finds any out-of-tolerance characteristic."},{"folder":"skills/ncr-draft","name":"ncr-draft","description":"Drafts the nonconformance report (NCR) and inspection summary from the graded contract payload, with every determination cited to the spec and rules. Use when the user says \"draft the NCR\", \"write up the nonconformance\", \"inspection summary please\", or after defect-grade completes with defects."},{"folder":"skills/spec-ingest","name":"spec-ingest","description":"Reads part specs, drawings, inspection plans, certificates of conformance and measurement exports for an inspection lot, and normalizes them into the mfg.quality-inspection.v1 contract inputs. Use when the user says \"clear this inspection lot\", \"load the inspection results\", \"read the spec for part <PN>\", \"review lot <LOT-ID>\", or when an inspection lot review begins."},{"folder":"skills/tolerance-check","name":"tolerance-check","description":"Compares actual measurements against spec tolerances for an inspection lot, computes per-characteristic statistics, flags out-of-tolerance and marginal characteristics, and cross-checks certificate claims against measured reality - deterministically. Use when the user says \"check tolerances\", \"compare against spec\", \"any out-of-spec?\", or after spec-ingest completes in a lot review."}]
pluginConnectors: []
tags: [quality, inspection, ncr, nonconformance, tolerance, mrb]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 2.0.0
createdAt: 2026-08-01
updatedAt: 2026-09-04
featured: true
bundle: bundles/quality-inspection.zip
---
Manufacturing Wave 1 Cowork plugin: clear an inspection lot. Reads part specs, drawings, inspection plans, CoC and measurement exports; compares actual measurements against tolerances (deterministic tolerance_check, with CoC-vs-measurement cross-check); grades each defect by severity and disposition (deterministic defect_grade rules engine); drafts the nonconformance report with every call cited to the spec. Draft-first; document-grounded. Ends at NCR creation and hands off to Quality Incident & CAPA (Wave 2).
