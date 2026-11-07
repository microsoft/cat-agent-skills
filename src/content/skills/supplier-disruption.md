---
name: Supplier Disruption Assist
description: "Get ahead of a supply problem: take a late PO, shipment delay or supplier notice, map the shortage through BOM where-used to the affected products, lines, open orders and at-risk dates, recommend expedite / substitute / reschedule, and draft both the supplier follow-up and the internal escalation brief."
platforms: [Cowork]
type: plugin
category: manufacturing
builtByMicrosoft: true
tags: [supply-chain, procurement, shortage, po, erp, mrp]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.4.3
createdAt: 2026-08-01
updatedAt: 2026-11-06
bundle: bundles/supplier-disruption.zip
---
Supplier Disruption Assist organizes supplied supplier notices and planning evidence, maps shortage impact, recommends draft mitigation and prepares unsent follow-ups. Single-component, single-receipt local planning only; freshness, units, usable stock and demand attestations are mandatory. No live ERP, supplier contact, purchasing, spending or schedule writes.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **disruption-intake** — Extracts cited local supplier delay notices into draft contract inputs. Use for "a PO is late", "process this supplier notice", "intake this disruption", "extract the delay facts", or "our supplier is delayed". Do NOT use for impact mapping, retrieval, mitigation or terminal drafts — use shortage-impact-map, supply-knowledge-retrieve, mitigation-recommend or disruption-writeup instead. Offline only; no supplier or ERP actions.
- **disruption-writeup** — Renders one fixed Markdown draft containing a cited supplier follow-up and internal escalation brief from a local packet. Use for "draft the supplier follow-up", "write the escalation brief", "draft the supplier email", "write it up", or "prepare the internal brief". No audience-switching or document conversion. Do NOT use for intake, retrieval, mapping or mitigation — use disruption-intake, supply-knowledge-retrieve, shortage-impact-map or mitigation-recommend. No sending, ERP writes or spending, even after approval.
- **mitigation-recommend** — Runs the local deterministic draft mitigation and unsent owner-notification engine. Use for "recommend a mitigation", "should we expedite or substitute", "who do we notify", "who do we escalate to", or "what do we do about it". Do NOT use for intake, retrieval, mapping or terminal drafts — use disruption-intake, supply-knowledge-retrieve, shortage-impact-map or disruption-writeup instead. No procurement, supplier or ERP actions.
- **shortage-impact-map** — Runs the local deterministic shortage impact engine. Use for "map the impact", "which lines and orders are hit", "what is at risk", "when does this bite", or "what does this shortage affect". Do NOT use for intake, source retrieval, mitigation or terminal drafts — use disruption-intake, supply-knowledge-retrieve, mitigation-recommend or disruption-writeup instead. Offline draft assessment; missing evidence blocks mapping.
- **supply-knowledge-retrieve** — Attaches cited supplied inventory, supplier master, BOM, open orders and delivery history to a local draft. Use for "where is this used", "what is our on-hand", "is this single-source", "has this supplier been late before", or "retrieve supply evidence". Do NOT use for intake, impact mapping, mitigation or drafts — use disruption-intake, shortage-impact-map, mitigation-recommend or disruption-writeup instead. No live ERP access.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
