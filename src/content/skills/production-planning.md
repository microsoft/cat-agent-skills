---
name: Production Planning
description: "Turn demand into a publishable shift plan: pull the forecast and open orders, check capacity, constraints and material availability, sequence the week to minimise changeovers with a deterministic campaign heuristic, and draft the shift plan for the planner to publish."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/capacity-check","name":"capacity-check","description":"Checks capacity, constraints and material availability for the plan week with the deterministic capacity_check engine. Use when the user says \"do we have capacity\", \"does the week fit\", \"check materials\", or after demand-pull in a planning run."},{"folder":"skills/demand-pull","name":"demand-pull","description":"Pulls the demand forecast and open orders for the plan week into the mfg.production-planning.v1 contract. Use when the user says \"plan next week\", \"build the schedule\", \"pull the orders for line <x>\", or when a planning run begins."},{"folder":"skills/schedule-optimize","name":"schedule-optimize","description":"Optimizes the weekly sequence for changeovers with the deterministic campaign heuristic - naive vs optimized compared side by side - using the sequence_optimize engine. Use when the user says \"optimize the schedule\", \"sequence the week\", \"minimize changeovers\", or after capacity-check in a planning run."},{"folder":"skills/shift-plan-draft","name":"shift-plan-draft","description":"Drafts the shift plan from the optimized schedule for the planner to review and publish. Use when the user says \"draft the shift plan\", \"write up the week\", \"publish the plan\" (which produces the draft), or after schedule-optimize in a planning run."}]
pluginConnectors: []
tags: [operations, scheduling, production-planning, changeover, capacity]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-01
updatedAt: 2026-09-04
bundle: bundles/production-planning.zip
---
Manufacturing Wave 2 Cowork plugin - the heaviest build in the set. Pulls the demand forecast and open orders; checks capacity, constraints and material availability (capacity_check engine); optimizes the weekly sequence for changeovers with a deterministic campaign heuristic (sequence_optimize engine); drafts the shift plan for the planner to publish. Draft-first, document-grounded; a live solver/APS is the graduation, not v1.
