---
name: Quality Inspection & Nonconformance
description: "Clear an inspection lot end to end: read the part spec, drawing, inspection plan, CoC and measurement export, compare every actual against tolerance, grade each defect by severity and disposition, and draft the nonconformance report with every call cited back to the spec."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
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

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **defect-grade** — Grades each out-of-tolerance characteristic by severity and recommends a disposition (use-as-is / rework / scrap / return-to-vendor / hold-for-review) using the deterministic disposition rules engine. Use when the user says "grade the defects", "what disposition?", "how bad is it?", "can we ship it?", or after tolerance-check finds any out-of-tolerance characteristic.
- **ncr-draft** — Drafts the nonconformance report (NCR) and inspection summary from the graded contract payload, with every determination cited to the spec and rules. Use when the user says "draft the NCR", "write up the nonconformance", "inspection summary please", or after defect-grade completes with defects.
- **spec-ingest** — Reads part specs, drawings, inspection plans, certificates of conformance and measurement exports for an inspection lot, and normalizes them into the mfg.quality-inspection.v1 contract inputs. Use when the user says "clear this inspection lot", "load the inspection results", "read the spec for part <PN>", "review lot <LOT-ID>", or when an inspection lot review begins.
- **tolerance-check** — Compares actual measurements against spec tolerances for an inspection lot, computes per-characteristic statistics, flags out-of-tolerance and marginal characteristics, and cross-checks certificate claims against measured reality - deterministically. Use when the user says "check tolerances", "compare against spec", "any out-of-spec?", or after spec-ingest completes in a lot review.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
