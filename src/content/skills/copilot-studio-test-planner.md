---
name: Copilot Studio Test Planner
description: "Reads an exported Copilot Studio agent and generates a graded, runnable test suite (happy-path, paraphrase, disambiguation, negative, knowledge-grounding, multilingual, and safety cases) plus a regression set, ready to run in the free Copilot Studio test panel."
platforms: [Cowork]
type: plugin
tags: [qa, eval, regression, agent]
author: Elliot Margot
authorUrl: "https://e-margot.ch"
authorGithub: adilei
version: 1.0.0
createdAt: 2026-07-18
updatedAt: 2026-07-18
bundle: bundles/copilot-studio-test-planner.zip
---
Copilot Studio Test Planner reads an exported Copilot Studio agent (solution ZIP, topic YAML, or pasted definition) and generates a full, graded test plan: happy-path, paraphrase, disambiguation, slot-filling, negative, knowledge-grounding, multilingual, and safety cases, plus a regression subset. It emits a coverage summary, a test matrix with expected topics or tools, and step-by-step instructions to run the suite in the free Copilot Studio test panel. It produces tests only and never modifies your tenant.

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **copilot-studio-test-planner** — Generates a full test plan and eval set for a Microsoft Copilot Studio agent.
Use when the user asks to "create a test plan for my Copilot Studio agent",
"generate test cases for an agent", "build an eval set", "write regression
tests for my agent", "how do I test my agent", or shares an exported agent
definition, topic YAML, or solution and wants tests to run before shipping.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
