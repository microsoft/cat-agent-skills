---
name: Quality Inspection & Nonconformance
description: "Clear an inspection lot end to end: read the part spec, drawing, inspection plan, CoC and measurement export, compare every actual against tolerance, grade each defect by severity and disposition, and draft the nonconformance report with every call cited back to the spec."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
tags: [quality, inspection, ncr, nonconformance, tolerance, mrb]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 3.1.1
createdAt: 2026-08-01
updatedAt: 2026-11-06
featured: true
bundle: bundles/quality-inspection.zip
---
Quality Inspection organizes supplied inspection evidence, computes tolerances, grades deviations and drafts cited nonconformance reports. Local source replay supports deterministic checks. No release authorization, QMS filing, supplier sending, stock movement or CAPA execution. Quality engineer review is required.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **defect-grade** — Recommends manufacturing defect severity and disposition from validated engine deviations. Use for "grade the defects", "what disposition?", "how bad is it?", "can we ship it?", or "certificate says pass". Do NOT use for document intake — use spec-ingest; tolerance math — use tolerance-check; NCR writing — use ncr-draft. No release approval or operational actions.
- **ncr-draft** — Writes a cited draft nonconformance report and inspection summary in Markdown (.md) from graded engine evidence. Use for "draft the NCR", "write up the nonconformance", "inspection summary please", "prepare the review report", or "draft supplier notification text". Do NOT use for intake — use spec-ingest; tolerance math — use tolerance-check; grading — use defect-grade; CAPA plans and DOCX/PDF conversion are outside this release. Never sends, files or executes actions.
- **spec-ingest** — Organizes cited inspection documents into engine-ready inputs without grading. Use for "load the inspection results", "read the part spec", "structure the lot documents", "intake inspection evidence", or "review lot documents". Do NOT use for deviation math — use tolerance-check; grading — use defect-grade; NCR writing — use ncr-draft. Never authorizes release or operational actions.
- **tolerance-check** — Computes inspection deviation statistics using a local deterministic engine. Use for "check tolerances", "compare against spec", "any out-of-spec?", "bore exceedance", or "measurement band consumption". Do NOT use for document intake — use spec-ingest; grading — use defect-grade; NCR or review-report Markdown — use ncr-draft. This release does not produce DOCX/PDF or other report formats. No release decisions or operational actions.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
