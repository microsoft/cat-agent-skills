---
name: Returns & Refund Case
description: "Consistent, policy-cited return decisions with a complete case packet on first touch: classify the return reason, validate eligibility deterministically with the policy clause cited, surface fraud signals without adjudicating them, and draft the recommendation and case packet."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
tags: [retailer, returns, refund, reverse-commerce, eligibility, fraud-signals]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-05
updatedAt: 2026-09-08
bundle: bundles/returns-refund-case.zip
---
Retail Wave 1 Cowork plugin: consistent, policy-cited return decisions with a complete case packet on first touch. Retrieves order, receipt, SKU attributes and warranty; classifies the return reason against the taxonomy (reason_classify); validates eligibility deterministically with the policy clause cited (eligibility_check - the explicit Govern step); surfaces fraud signals from a deterministic rule set without adjudicating them (fraud_signal); drafts the recommendation and case packet. Draft-first: it never authorises a refund, releases funds, adjudicates fraud, disposes inventory or books a carrier.

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **case-packet** — Drafts the return case packet - determination, recommendation, evidence list, fraud signals, customer response draft - from the contract payload. Use to close every return case: "build the case packet", "write up the return".
- **eligibility-check** — Determines return eligibility against the configured policy and surfaces fraud signals deterministically - the explicit Govern step of this plugin. Use on "is this returnable", "do they get a refund", "any red flags", after reason-classify.
- **policy-retrieve** — Retrieves the applicable return, warranty and price-match policy text and the customer's configured windows for the case. Use after return-intake, or on "what does the return policy say for <category>".
- **reason-classify** — Classifies the stated return reason against the customer's reason-code taxonomy with the deterministic reason_classify engine. Use after return-intake in every case, or on "what reason code is this".
- **return-intake** — Structures a return request - item, order/receipt, reason as stated, condition, serials, customer history - into the rtl.returns-refund-case.v1 contract. Use when the user says "customer wants to return", "process this return", "can they get a refund", or a return case begins.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
