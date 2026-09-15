---
name: Safety Incident Assist
description: "Handle an EHS incident the same way every time: take the report from a form, email or voice note, classify severity, near-miss status and OSHA recordability, route it to the right investigator with the regulatory clocks attached, and draft the incident summary and RCA template."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/ehs-knowledge-retrieve","name":"ehs-knowledge-retrieve","description":"Retrieves the OSHA recordability criteria, ISO 45001 clauses, JHA/HIRA and internal EHS policy relevant to an incident and attaches them plus prior similar incidents to the mfg.safety-incident-assist.v1 contract. Use when the user says \"pull the OSHA criteria\", \"get the JHA for this task\", \"have we had this incident before\", \"what does policy say\", or after incident-intake completes."},{"folder":"skills/incident-intake","name":"incident-intake","description":"Receives a safety-incident report from a form, email or voice note and pulls it into the mfg.safety-incident-assist.v1 contract inputs. Use when the user says \"log this incident\", \"new incident report\", \"someone got hurt\", \"intake this near miss\", \"process this safety report\", or when a Safety Incident Agent run begins."},{"folder":"skills/incident-writeup","name":"incident-writeup","description":"Drafts the incident summary and the root-cause-analysis (RCA) template from the assembled contract payload, with every determination cited to OSHA, ISO 45001, the JHA and internal policy. Use when the user says \"draft the incident summary\", \"write up the incident\", \"give me the RCA template\", \"prepare the OSHA writeup\", or after routing-notify completes."},{"folder":"skills/routing-notify","name":"routing-notify","description":"Routes a classified incident to the right investigator, builds the owner-notification list, and starts any OSHA regulatory clock, deterministically. Use when the user says \"who investigates this\", \"who do we notify\", \"route this incident\", \"start the OSHA clock\", \"who owns this\", or after severity-recordability completes."},{"folder":"skills/severity-recordability","name":"severity-recordability","description":"Classifies a safety incident's severity, near-miss status, OSHA recordability (with the OSHA 300 column) and reportability (with the 1904.39 clock), deterministically. Use when the user says \"is this recordable\", \"classify this incident\", \"is this an OSHA reportable\", \"what severity is this\", \"do we have to report this\", or after ehs-knowledge-retrieve completes."}]
pluginConnectors: []
tags: [ehs, safety, incident, osha, recordable, iso-45001]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-08-01
updatedAt: 2026-09-04
bundle: bundles/safety-incident.zip
---
Manufacturing Wave 1 Cowork plugin: handle an EHS incident consistently. Receives the report from a form, email or voice note, classifies severity, near-miss and OSHA recordability plus reportability (deterministic recordability_classify), routes to the right investigator and builds the owner-notification list with regulatory clocks (deterministic routing_notify), then drafts the incident summary and root-cause (RCA) template. Draft-first; keeps the reporting checklist and audit trail intact. NOT auto-filing OSHA reports or auto-notifying (a human signs off). Grounded in OSHA 300/300A, ISO 45001, JHA/HIRA and internal EHS policy.
