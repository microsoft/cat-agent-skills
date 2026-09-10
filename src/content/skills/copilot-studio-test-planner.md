---
name: Copilot Studio Test Planner
description: "Reads an exported Copilot Studio agent and generates a graded, runnable test suite (happy-path, paraphrase, disambiguation, negative, knowledge-grounding, multilingual, and safety cases) plus a regression set, ready to run in the free Copilot Studio test panel."
platforms: [Cowork]
type: plugin
pluginSkills: [{"folder":"skills/copilot-studio-test-planner","name":"copilot-studio-test-planner","description":"Generates a full test plan and eval set for a Microsoft Copilot Studio agent.\nUse when the user asks to \"create a test plan for my Copilot Studio agent\",\n\"generate test cases for an agent\", \"build an eval set\", \"write regression\ntests for my agent\", \"how do I test my agent\", or shares an exported agent\ndefinition, topic YAML, or solution and wants tests to run before shipping.\n"}]
pluginConnectors: []
tags: [qa, eval, regression, agent]
author: Elliot Margot
authorUrl: "https://e-margot.ch"
authorGithub: OwnOptic
version: 1.0.0
createdAt: 2026-07-18
updatedAt: 2026-07-18
bundle: bundles/copilot-studio-test-planner.zip
---
Copilot Studio Test Planner reads an exported Copilot Studio agent (solution ZIP, topic YAML, or pasted definition) and generates a full, graded test plan: happy-path, paraphrase, disambiguation, slot-filling, negative, knowledge-grounding, multilingual, and safety cases, plus a regression subset. It emits a coverage summary, a test matrix with expected topics or tools, and step-by-step instructions to run the suite in the free Copilot Studio test panel. It produces tests only and never modifies your tenant.
