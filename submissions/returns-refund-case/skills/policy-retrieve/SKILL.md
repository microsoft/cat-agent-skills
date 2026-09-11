---
name: policy-retrieve
description: Retrieves the applicable return, warranty and price-match policy text and the customer's configured windows for the case. Use after return-intake, or on "what does the return policy say for <category>".
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Customer Operations}
---
# Policy Retrieve
## Purpose
Bring the governing policy text and config values into the case with citations.
## When to use
After return-intake in every case.
## Inputs
case.json + policy documents + config/return-windows.json.
## Steps
1. Retrieve the clauses matching the category and case shape (window, receiptless, condition, warranty).
2. Attach clause ids and text as citations for the Govern step.
## Output
Case payload with policy context attached.
## Grounding requirements
Clause text quoted verbatim with ids; config values cite config/return-windows.json.
## Constraints
- Retrieval only; the determination belongs to eligibility-check.
## Escalation / uncertainty
Category missing from config: escalate to the policy owner; the case becomes needs_evidence.
