---
name: Store Associate Assist
description: "The associate's cited answer on the shop floor: takes a question with store, role and department context, retrieves the applicable policy, product attributes and current promotion, resolves the policy and compares products deterministically, and returns a cited answer or a drafted escalation."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
pluginSkills: [{"folder":"skills/answer-draft","name":"answer-draft","description":"Drafts the cited answer for the associate - or the escalation when the question is out of scope or below confidence. Use to close every assist run."},{"folder":"skills/policy-retrieve","name":"policy-retrieve","description":"Resolves the applicable policy clause and checks promotion eligibility deterministically with the policy_resolve engine. Use when the question involves returns, price match, rainchecks, promotions, eligibility, or \"what does the policy say\", after question-intake."},{"folder":"skills/product-compare","name":"product-compare","description":"Builds a side-by-side product comparison from the PIM extract with the deterministic product_compare engine. Use when the associate asks \"what's the difference between these two\", \"which should I recommend\", or names two SKUs."},{"folder":"skills/promo-check","name":"promo-check","description":"Answers \"is this on promo / does this customer get the deal\" using the deterministic three-part eligibility test already computed by policy_resolve. Use for any promotion, discount, or deal-eligibility question."},{"folder":"skills/question-intake","name":"question-intake","description":"Takes an associate's floor question with store, role and department context into the rtl.store-associate-assist.v1 contract. Use when an associate asks \"can a customer return this\", \"do we price match\", \"is this on promo\", \"which of these two should I recommend\", or any store policy, product or promotion question."}]
pluginConnectors: []
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
