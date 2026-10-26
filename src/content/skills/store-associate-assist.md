---
name: Store Associate Assist
description: "The associate's cited answer on the shop floor: takes a question with store, role and department context, retrieves the applicable policy, product attributes and current promotion, resolves the policy and compares products deterministically, and returns a cited answer or a drafted escalation."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
tags: [retailer, store-operations, associate, policy, promotion, product-compare]
author: Industry Templates
authorUrl: "https://github.com/SravaniSeethi"
authorGithub: SravaniSeethi
version: 1.0.0
createdAt: 2026-09-05
updatedAt: 2026-09-08
featured: true
bundle: bundles/store-associate-assist.zip
---
Retail Wave 1 Cowork plugin: the associate's cited answer on the floor. Takes the question with store, role and department context; retrieves the applicable policy, product attributes and current promotion; resolves the policy and compares products deterministically (policy_resolve + product_compare engines); returns a cited answer or a drafted escalation. Answers and drafts only - it never overrides a price, authorises a refund, reserves inventory or changes a schedule.

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **answer-draft** — Drafts the cited answer for the associate - or the escalation when the question is out of scope or below confidence. Use to close every assist run.
- **policy-retrieve** — Resolves the applicable policy clause and checks promotion eligibility deterministically with the policy_resolve engine. Use when the question involves returns, price match, rainchecks, promotions, eligibility, or "what does the policy say", after question-intake.
- **product-compare** — Builds a side-by-side product comparison from the PIM extract with the deterministic product_compare engine. Use when the associate asks "what's the difference between these two", "which should I recommend", or names two SKUs.
- **promo-check** — Answers "is this on promo / does this customer get the deal" using the deterministic three-part eligibility test already computed by policy_resolve. Use for any promotion, discount, or deal-eligibility question.
- **question-intake** — Takes an associate's floor question with store, role and department context into the rtl.store-associate-assist.v1 contract. Use when an associate asks "can a customer return this", "do we price match", "is this on promo", "which of these two should I recommend", or any store policy, product or promotion question.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
