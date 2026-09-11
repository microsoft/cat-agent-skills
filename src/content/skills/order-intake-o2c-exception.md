---
name: Order Intake & O2C Exception
description: "Orders arriving by email, PDF and portal validated and exceptions routed instead of rekeyed: extract and normalise order lines, validate against customer, pricing, product and credit master data, queue exceptions with reason codes and a recommended correction, and draft the customer response."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/exception-route","name":"exception-route","description":"Queues validation exceptions with reason codes and a recommended correction per exception, deterministically. Use on \"route the exceptions\", \"what needs fixing before entry\", after order-validate."},{"folder":"skills/line-normalize","name":"line-normalize","description":"Normalises extracted order lines - whitespace, casing, UOM tokens, qty formats - without changing meaning, preparing them for validation. Use after order-ingest."},{"folder":"skills/order-ingest","name":"order-ingest","description":"Ingests orders arriving as email, PDF or portal export into the rtl.order-intake-o2c.v1 contract. Use when the user says \"order came in by email\", \"key in this PO\", \"process the attached order\", or an order document arrives."},{"folder":"skills/order-validate","name":"order-validate","description":"Validates the order against customer, pricing, product and credit masters deterministically with the order_validate engine. Use on \"is this order clean\", \"validate before entry\", after line-normalize."},{"folder":"skills/response-draft","name":"response-draft","description":"Drafts the customer confirmation or clarification message and the internal entry note from the routed payload. Use to close every order run - \"draft the reply to the customer\", \"write up the order status\"."}]
pluginConnectors: []
tags: [retailer, order-management, o2c, exception, validation, edi]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-07
updatedAt: 2026-09-08
bundle: bundles/order-intake-o2c-exception.zip
---
Retail Wave 2 Cowork plugin (heavy CPG usage): orders arriving by email, PDF and portal validated and exceptions routed instead of rekeyed. Extracts and normalises order lines; validates against customer, pricing, product and credit master data (order_validate); queues exceptions with reason codes and a recommended correction per exception (exception_route); drafts the customer response. Ships at action level L0-L2: order creation and release stay human-approved until the customer promotes the action level in config/.
