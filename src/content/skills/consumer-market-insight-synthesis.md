---
name: Consumer & Market Insight Synthesis
description: "Prior research reused instead of re-commissioned: retrieve and rank prior research and panel extracts, compare trends across markets and periods, flag contradictory evidence rather than smoothing it, check usage rights and claim provenance, and draft a cited insight brief with a provenance record."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/contradiction-flag","name":"contradiction-flag","description":"Surfaces contradictory evidence - studies moving the same metric in opposite directions - rather than a smoothed answer. Use on \"do the studies agree\", \"any conflicting evidence\", after trend-compare."},{"folder":"skills/insight-brief","name":"insight-brief","description":"Drafts the cited insight brief with the provenance and usage-rights record attached. Use to close every insight run: \"draft the brief\", \"write it up for the category review\"."},{"folder":"skills/provenance-check","name":"provenance-check","description":"Checks usage rights, geography and expiry for every retrieved study against the declared use - the explicit Govern step - with the deterministic provenance_check engine. Use on \"can we use this externally\", \"is this stat cleared for the board deck\", after trend-compare."},{"folder":"skills/research-retrieve","name":"research-retrieve","description":"Retrieves and ranks prior research, panel extracts and campaign results relevant to the question. Use when the user says \"what do we already know about <topic>\", \"find prior research on\", \"have we studied this before\", or an insight request begins."},{"folder":"skills/trend-compare","name":"trend-compare","description":"Compares trends across markets and periods like-for-like with the deterministic trend_compare engine. Use on \"how has this trended\", \"compare markets\", \"what changed since the last study\", after research-retrieve."}]
pluginConnectors: []
tags: [cpg, insights, consumer-research, category, panel, provenance]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-07
updatedAt: 2026-09-08
bundle: bundles/consumer-market-insight-synthesis.zip
---
CPG Wave 2 Cowork plugin: prior research reused instead of re-commissioned. Retrieves and ranks prior research and panel extracts; compares trends across markets and periods (trend_compare); flags contradictory evidence rather than smoothing it; checks usage rights, geography and claim provenance - the explicit Govern step (provenance_check); drafts a cited insight brief with a provenance record. Scoped to retrieval, comparison and citation - it does not forecast demand, approve claims or assert causal attribution, and it does not analyse large tabular files.
