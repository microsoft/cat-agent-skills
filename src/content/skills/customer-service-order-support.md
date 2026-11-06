---
name: Customer Service & Order Support
description: "A grounded first response, and a clean escalation packet when it cannot resolve: classify intent against the taxonomy, assemble customer, order, loyalty and delivery context while detecting contradictions, retrieve the approved answer, and draft the resolution in channel and tone."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
tags: [retailer, customer-service, contact-centre, wismo, intent, escalation]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.4
createdAt: 2026-09-05
updatedAt: 2026-11-06
bundle: bundles/customer-service-order-support.zip
---
Customer Service Order Support works retail order inquiries such as where is my order and delivered but not received. It classifies the inquiry, assembles order, carrier and loyalty records, flags contradictions and drafts a grounded reply or a tier 2 escalation packet. It never issues goodwill credit, changes payment details or sends replies.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **inquiry-intake** — Takes a retail customer's service inquiry from any channel (chat, mail, voice transcript) and classifies intent against the taxonomy with the deterministic intent_classify engine - the first hop of every Customer Service & Order Support run. Use when a service inquiry arrives: "where is my order", "it says delivered but I never got it", "new customer inquiry", "a chat just came in", "classify this contact", "start the service run". Do NOT use for supplier or purchase-order delays - use disruption-intake instead; not for return requests - use return-intake instead; not for the approved answer - use knowledge-retrieve instead; not for drafting the response - use resolution-draft instead; not for general mailbox tasks - use outlook-email instead.
- **context-assemble** — Assembles a retail customer's order, carrier and loyalty context after inquiry-intake, detects record-vs-account contradictions (carrier says delivered, customer says not received) and selects the resolution path deterministically with the context_assemble engine. Use after inquiry-intake, or on "pull up everything on this order", "what does the record show", "is there a contradiction", "which path applies", "check the instant-refund gate". Do NOT use for maintenance work orders - use wo-intake instead; not for building the escalation packet - use handoff-packet instead; not for drafting the reply - use resolution-draft instead.
- **knowledge-retrieve** — Retail customer-service grounding step: attaches the approved knowledge article, policy clause or records-only grounding that backs the customer answer for a classified inquiry (order status, delivered-not-received, returns, stock, how-to). Use after context-assemble, or on "what's the approved answer for this", "what's the approved wording", "find the policy clause for", "cite the article", "is there an approved script". Do NOT use for SOPs, OEM manuals or work orders - use the work-order-assist knowledge-retrieve instead; not for drafting the reply - use resolution-draft instead.
- **resolution-draft** — Drafts the customer-facing service reply (chat, email or voice script) for a resolvable retail order inquiry - order status, delivery ETA, in-stock or how-to answers - from the assembled context and approved grounding, marked DRAFT for the agent to send. Use to close resolvable runs: "draft the reply", "answer the customer", "write the customer response", "reply on chat", "answer the where-is-my-order question". Do NOT use when escalations or contradictions are present - use handoff-packet instead; not for purchase-order confirmations or order-entry notes - use the order-intake response-draft instead; not for general mailbox tasks - use outlook-email instead.
- **handoff-packet** — Builds the structured tier-2 escalation packet for a retail customer-service run that cannot resolve - intent and confidence, cited context, contradiction flags with the carrier scan, everything already checked, the recommended next step, goodwill as a proposal, plus an interim customer reply draft. Use on any low-confidence, contradicted, ungrounded or money-boundary run: "escalate this", "hand off to tier 2", "build the escalation packet", "we can't resolve this", "below confidence, hand it over". Do NOT use for resolvable runs - use resolution-draft instead; not for work-order handovers - use work-order-writeup instead; not for return cases - use case-packet instead.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
