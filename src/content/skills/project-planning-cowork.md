---
name: Project Planning
description: "Turn project data into Gantt charts, risk matrices, PERT dependency networks, and RAID registers with a four-skill Cowork plugin."
platforms: [Cowork]
type: plugin
tags: [project-planning, project-management, gantt, risk, productivity]
author: Andrew Hess
authorUrl: "https://github.com/AndrewHessMSFT"
authorGithub: AndrewHessMSFT
version: 1.0.0
bundle: bundles/project-planning-cowork.zip
---
Turn project data into four self-contained HTML visuals with supporting tables: Gantt schedules, qualitative risk matrices, PERT dependency networks, and RAID registers. Use your own project data or try the included synthetic examples.

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **project-gantt** — Creates an offline Gantt chart with an adaptive timeline, workstreams, milestones, and schedule details. Use for "get my tasks today", planning a productive day from calendar and work context, suggesting AI handoffs, or mapping project schedules and dependencies.
- **project-risk-matrix** — Plots project risks in an offline 5-by-5 likelihood and severity matrix with a qualitative rating policy and supporting risk details. Use for risk heatmaps, triage, workshops, or visualizing the risk section of a RAID register.
- **project-pert** — Builds an offline Program Evaluation and Review Technique dependency network and critical-path table from optimistic, most-likely, and pessimistic task durations. Use for parallel branches, sequencing, and schedule sensitivity before committing to dates.
- **project-raid** — Creates an offline RAID dashboard and action register for project risks, assumptions, issues, and dependencies. Use to consolidate planning blockers, review follow-up ownership, or track actions linked to task and risk IDs.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
