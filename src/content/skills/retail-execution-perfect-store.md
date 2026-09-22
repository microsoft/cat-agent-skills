---
name: Retail Execution & Perfect Store
description: "A prepared call and a complete, evidenced visit report: assemble the pre-call plan, score the perfect-store gap deterministically against the channel standard, rank gaps by revenue impact rather than count, and draft the visit report, action register and suggested order for the rep to confirm."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/action-register","name":"action-register","description":"Ranks gaps by revenue at stake with the gap_rank engine and builds the action register and suggested order for the rep to confirm. Use on \"what do I fix first\", \"rank the gaps\", \"build my order\", after gap-score."},{"folder":"skills/gap-score","name":"gap-score","description":"Scores perfect-store compliance deterministically from the visit audit answers with the visit_score engine - photos attach as evidence, never scored by vision. Use after the visit: \"score the visit\", \"how compliant is the store\"."},{"folder":"skills/standard-retrieve","name":"standard-retrieve","description":"Retrieves the perfect-store / picture-of-success standard, planogram and promo calendar for the outlet's channel and cluster. Use on \"what's the standard for this outlet\", \"what should this store look like\", after visit-prep."},{"folder":"skills/visit-prep","name":"visit-prep","description":"Assembles the pre-call plan for a specific outlet - profile, last visit's open actions, promotion status, recent scan performance - into the rtl.retail-execution-perfect-store.v1 contract. Use when the rep says \"prep me for <outlet>\", \"what's the plan for today's calls\", \"pre-call for store <id>\"."},{"folder":"skills/visit-report","name":"visit-report","description":"Drafts the evidenced visit report and action register from the contract payload. Use to close every visit: \"write the visit report\", \"log the visit\"."}]
pluginConnectors: []
tags: [cpg, field-sales, retail-execution, perfect-store, dsr, visit-report]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-07
updatedAt: 2026-09-08
bundle: bundles/retail-execution-perfect-store.zip
---
CPG Wave 2 Cowork plugin: a prepared call and a complete, evidenced visit report. Assembles the pre-call plan (outlet profile, open actions, promo status, recent scan data); scores the perfect-store gap deterministically against the channel/cluster standard (visit_score); ranks gaps by revenue impact, not count (gap_rank); drafts the visit report, action register and suggested order for the rep to confirm. Photos attach as evidence, never scored by vision. It does not place the order, change the planogram or issue trade credit.
