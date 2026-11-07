---
name: Store Associate Assist
description: "The associate's cited answer on the shop floor: takes a question with store, role and department context, retrieves the applicable policy, product attributes and current promotion, resolves the policy and compares products deterministically, and returns a cited answer or a drafted escalation."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
tags: [retailer, store-operations, associate, policy, promotion, product-compare]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.9
createdAt: 2026-09-05
updatedAt: 2026-11-06
featured: true
bundle: bundles/store-associate-assist.zip
---
Store Associate Assist answers an associate's floor question with the source cited. It resolves the return, price match or raincheck clause, tests promotion eligibility by window, cluster and SKU, compares two products from your PIM export and drafts the answer or a shift lead escalation. It never overrides a price, authorises a refund or reserves stock.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **question-intake** — Takes an associate's floor question with store, role and department context into the rtl.store-associate-assist.v1 contract (question.json, the entry hop). Use when an associate asks "can she return this", "do we price match", "is this still on promo", "what's the difference between these two", "customer is asking about the return policy", or any new floor question about policy, product or promotion. Do NOT use to resolve the policy - use policy-retrieve instead; not to present promo results - use promo-check; not to compare two SKUs from a resolved payload - use product-compare; not for the final answer - use answer-draft; not for staffing, scheduling, inventory or refund requests.
- **policy-retrieve** — Resolves the applicable policy clause and checks promotion eligibility deterministically with the policy_resolve engine (window AND cluster AND SKU). Use after question-intake on "what does the policy say", "is this return within the window", "can we price match this competitor", "is the customer eligible for the promo", "does the raincheck clause apply". Do NOT use for a fresh floor question with no question.json - use question-intake instead; not for a pure two-SKU spec comparison - use product-compare; not to present an already-computed promo result - use promo-check; not to draft the answer - use answer-draft.
- **promo-check** — Presents the promotion eligibility already computed by policy_resolve - the three-part test (window AND cluster AND SKU) with the failing leg and exact dates named. Use for "is this on promo", "does this customer get the deal", "is the discount still running", "why isn't the promo applying", "did the offer end". Do NOT use to resolve the clause or compute eligibility - use policy-retrieve instead (it populates promo_check); not for return or price-match questions - use policy-retrieve; not for product comparisons - use product-compare; not to draft the floor answer - use answer-draft.
- **product-compare** — Builds a side-by-side product comparison from the PIM extract with the deterministic product_compare engine - differences stated, missing shown as MISSING, never guessed. Use when the associate asks "what's the difference between these two", "which should I recommend", "compare SKU A and SKU B", "side-by-side on these two models", "which one has the longer warranty". Do NOT use for a fresh floor question with no resolved payload - use question-intake instead; not for single-SKU promo or price questions - use promo-check or policy-retrieve; not to draft the final answer - use answer-draft; not for specs outside the PIM extract.
- **answer-draft** — Drafts the cited floor answer for the associate - or the shift-lead escalation when the payload is out of scope or below confidence - from the completed rtl.store-associate-assist.v1 payload, using the answer template. Use to close every assist run: "draft the floor answer", "write up the answer for the associate", "close out the assist run", "draft the escalation to the shift lead", "what can I tell the customer". Do NOT use for a new question with no resolved payload - use question-intake instead; not to compute eligibility - use policy-retrieve or promo-check; never send, post or execute anything - drafts only.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
