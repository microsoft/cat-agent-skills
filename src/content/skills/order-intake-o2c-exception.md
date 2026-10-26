---
name: Order Intake & O2C Exception
description: "Orders arriving by email, PDF and portal validated and exceptions routed instead of rekeyed: extract and normalise order lines, validate against customer, pricing, product and credit master data, queue exceptions with reason codes and a recommended correction, and draft the customer response."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
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

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **exception-route** — Queues validation exceptions with reason codes and a recommended correction per exception, deterministically. Use on "route the exceptions", "what needs fixing before entry", after order-validate.
- **line-normalize** — Normalises extracted order lines - whitespace, casing, UOM tokens, qty formats - without changing meaning, preparing them for validation. Use after order-ingest.
- **order-ingest** — Ingests orders arriving as email, PDF or portal export into the rtl.order-intake-o2c.v1 contract. Use when the user says "order came in by email", "key in this PO", "process the attached order", or an order document arrives.
- **order-validate** — Validates the order against customer, pricing, product and credit masters deterministically with the order_validate engine. Use on "is this order clean", "validate before entry", after line-normalize.
- **response-draft** — Drafts the customer confirmation or clarification message and the internal entry note from the routed payload. Use to close every order run - "draft the reply to the customer", "write up the order status".

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
