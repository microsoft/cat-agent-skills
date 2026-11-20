# Project Planning for Cowork

A Microsoft 365 Copilot Cowork plugin by [Andrew Hess](https://github.com/AndrewHessMSFT) with four project-planning skills. Each produces a self-contained HTML visual with supporting details and no external chart assets.

| Skill | Use it for |
|---|---|
| Project Gantt | Calendar schedules, milestones, daily work plans, and suggested AI handoffs. |
| Project risk matrix | Qualitative likelihood-and-severity risk triage, including unassessed risks. |
| Project PERT | Three-point duration estimates, dependency networks, critical paths, and float. |
| Project RAID | Risks, assumptions, issues, dependencies, and follow-up actions. |

## Install

Download the plugin ZIP from this gallery page and upload it using Cowork's plugin installation flow. Keep the downloaded package intact: it contains the manifest, icons, and all four skills.

See Microsoft's [Cowork plugin documentation](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for installation requirements and organizational availability.

## Try it

Provide project notes, a table, an export, or JSON, then ask:

- "Create a Gantt chart from these tasks and dates."
- "Help me plan today's work and suggest useful AI handoffs."
- "Plot these risks in a likelihood and severity matrix."
- "Build a PERT network from these three-point estimates and dependencies."
- "Turn these project notes into a RAID register."

For a demonstration without project data, ask for a chart using the included synthetic onboarding example.

## Requirements and limits

The renderers use Python 3 and its standard library. Cowork needs code execution and file delivery to return the generated HTML.

Work IQ is optional: the skills can use relevant authorized results when available, or work from data you supply. The plugin does not configure a connector, send messages, assign tasks, book time, or update enterprise systems.

Missing information remains visible rather than being invented. Gantt uses supplied or confirmed calendar dates; PERT estimates dependency-driven duration without resource leveling or holiday calendars. The risk matrix uses a fixed qualitative policy, not numeric score multiplication.

## Privacy

The bundled Python renderers read project JSON and write HTML files in the execution environment. They do not make network requests or include telemetry. Generated HTML contains the supplied project information; review it before sharing.

Cowork and any connected Microsoft 365 services process data under their own privacy policies and your organization's settings. This plugin does not change those policies or settings.

## Terms of use

This plugin is distributed under the repository's [MIT license](https://github.com/microsoft/cat-agent-skills/blob/main/LICENSE), including its warranty disclaimer.
