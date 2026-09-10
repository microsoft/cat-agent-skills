---
name: Customer Service & Order Support
description: "A grounded first response, and a clean escalation packet when it cannot resolve: classify intent against the taxonomy, assemble customer, order, loyalty and delivery context while detecting contradictions, retrieve the approved answer, and draft the resolution in channel and tone."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/context-assemble","name":"context-assemble","description":"Assembles customer, order, loyalty and carrier context, detects record-vs-account contradictions, and selects the resolution path deterministically with the context_assemble engine. Use after inquiry-intake, or on \"pull up everything on this order\"."},{"folder":"skills/handoff-packet","name":"handoff-packet","description":"Builds the structured escalation packet when the run cannot resolve - intent, context, contradictions, what was checked, recommended next step. Use on any low-confidence, contradicted, or out-of-scope run: \"escalate this\", \"hand off to tier 2\"."},{"folder":"skills/inquiry-intake","name":"inquiry-intake","description":"Takes the customer inquiry from any channel and classifies intent against the taxonomy with the deterministic intent_classify engine. Use when a service inquiry arrives - \"where is my order\", \"it says delivered but I never got it\", \"can I return this\", \"is it in stock\", \"how do I set this up\"."},{"folder":"skills/knowledge-retrieve","name":"knowledge-retrieve","description":"Retrieves the approved knowledge article, policy text or product doc that grounds the answer for the classified intent. Use after context-assemble, or on \"what's the approved answer for this\"."},{"folder":"skills/resolution-draft","name":"resolution-draft","description":"Drafts the customer-facing resolution in the right channel and tone from the assembled context and approved sources. Use to close resolvable runs - \"draft the reply\", \"answer the customer\"."}]
pluginConnectors: []
tags: [retailer, customer-service, contact-centre, wismo, intent, escalation]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.1
createdAt: 2026-09-05
updatedAt: 2026-09-08
bundle: bundles/customer-service-order-support.zip
---
Retail Wave 1 Cowork plugin: a grounded first response, and a clean escalation packet when it cannot resolve. Classifies intent against the taxonomy (intent_classify); assembles customer, order, loyalty and delivery context and detects contradictions (context_assemble); retrieves the approved answer; drafts the resolution in channel and tone or builds the structured handoff packet. Reliability beats reach: it does not issue goodwill credit, change payment details or grant unsupported policy exceptions.
