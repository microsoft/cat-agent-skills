---
name: Maintenance Triage
description: "Move a fault forward: read the fault note, alarm codes and asset history, rank the likely failure modes against OEM manuals and past work orders, prioritise by asset criticality and downtime cost, and draft the work-order update with a recommended action."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/criticality-rank","name":"criticality-rank","description":"Prioritizes the fault by asset criticality and downtime cost into a P1-P4 maintenance priority with a response target and cost estimate, deterministically. Use when the user says \"how urgent is this\", \"what's the priority\", \"rank by criticality\", \"what will downtime cost\", or after failure-mode-rank completes."},{"folder":"skills/failure-mode-rank","name":"failure-mode-rank","description":"Ranks the likely failure modes for a fault against the failure-mode library, symptoms, alarm codes and repeat-failure history, deterministically. Use when the user says \"what's the likely cause\", \"rank the failure modes\", \"diagnose this fault\", \"is this the real root cause?\", or after history-retrieve completes."},{"folder":"skills/fault-intake","name":"fault-intake","description":"Reads maintenance fault notes, operator reports, alarm/event logs, asset IDs and location into the mfg.maintenance-triage.v1 contract inputs. Use when the user says \"triage this fault\", \"work this breakdown\", \"read the fault note for <asset>\", \"what's wrong with pump <id>\", or when a maintenance triage run begins."},{"folder":"skills/history-retrieve","name":"history-retrieve","description":"Retrieves the asset's maintenance history — prior work orders, similar failures, PM records — and the relevant OEM manual and troubleshooting sections, and attaches them to the mfg.maintenance-triage.v1 contract. Use when the user says \"pull the history for <asset>\", \"has this failed before?\", \"find the manual section\", \"any prior work orders?\", or after fault-intake completes."},{"folder":"skills/work-order-update","name":"work-order-update","description":"Drafts the work-order update and recommended action from the triaged contract payload, with every determination cited to the manual, history and rules. Use when the user says \"draft the work order\", \"write up the WO update\", \"what should we do\", \"recommend the fix\", or after criticality-rank completes."}]
pluginConnectors: []
tags: [maintenance, triage, cmms, reliability, failure-mode, work-order]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-08-01
updatedAt: 2026-09-04
featured: true
bundle: bundles/maintenance-triage.zip
---
Manufacturing Wave 1 Cowork plugin: move a fault forward. Reads fault notes, alarm codes and asset history; identifies the likely failure mode from OEM manuals and past work orders (deterministic fault_rank); prioritizes by asset criticality and downtime cost (deterministic criticality_score); and drafts the work-order update with the recommended action. Draft-first; document-grounded, historian optional. NOT predictive maintenance (that is Wave 3).
