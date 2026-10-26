---
name: Quality Incident & CAPA
description: "Take an open NCR through to a closed CAPA: read the incident, complaint and inspection data, establish root cause with a structured method, build corrective and preventive actions with mandatory effectiveness checks, validate closure readiness, and draft the 8D report cited to the clause."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
tags: [quality, capa, 8d, root-cause, ncr, iso-9001]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-01
updatedAt: 2026-09-04
bundle: bundles/quality-incident-capa.zip
---
Manufacturing Wave 2 Cowork plugin: NCR to closed CAPA. Picks up where Quality Inspection & Nonconformance (01) leaves off - reads the open NCR, complaint and inspection data; establishes root cause with a structured method (pareto + rca_tree engines); builds corrective and preventive actions with mandatory effectiveness checks (capa_logic engine); validates closure readiness (explicit Govern step); drafts the 8D / CAPA report cited to the clause. Draft-first; document-grounded.

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **capa-build** — Builds corrective and preventive actions with mandatory effectiveness checks from the verified root cause, using the deterministic capa_logic engine. Use when the user says "build the CAPA", "what actions do we take", "corrective actions please", or after root-cause-analyze in a CAPA run.
- **closure-check** — Validates CAPA closure readiness against the closure rules - the explicit Govern step of this plugin. Use when the user says "can we close this CAPA", "is the 8D ready to close", "close it out", or before any closure recommendation.
- **eightd-draft** — Drafts the 8D / CAPA report from the contract payload, cited to the clause and rules, with open blockers leading. Use when the user says "draft the 8D", "write the CAPA report", or after closure-check in a CAPA run.
- **ncr-intake** — Reads the open NCR (the mfg.quality-inspection.v1 payload handed off by the Quality Inspection plugin), complaint log and inspection data into the mfg.quality-incident-capa.v1 contract. Use when the user says "open a CAPA for NCR <id>", "work the nonconformance", "start the 8D", or when a CAPA run begins.
- **root-cause-analyze** — Establishes root cause with a structured method - Pareto over the complaint window, then an evidenced 5-Why chain - using the deterministic pareto and rca_tree engines. Use when the user says "what's the root cause", "run the 5-why", "why does this keep happening", or after ncr-intake in a CAPA run.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
