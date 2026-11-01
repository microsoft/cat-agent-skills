---
name: promo-check
description: Answers "is this on promo / does this customer get the deal" using the deterministic three-part eligibility test already computed by policy_resolve. Use for any promotion, discount, or deal-eligibility question.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Store Operations}
---
# Promo Check
## Purpose
Present the engine's promo eligibility (window AND cluster AND SKU, #2.1) with the failing leg named when ineligible.
## When to use
Any promotion question; after policy-retrieve.
## Inputs
resolved.json (promo_check populated).
## Steps
1. Quote eligible/ineligible and the reasons verbatim - if the window closed yesterday, say exactly that with dates.
2. When ineligible, offer the policy-consistent alternative (e.g., raincheck clause) if one resolved.
## Output
Promo answer grounded in the promo_check hop.
## Grounding requirements
Cites the promo pack line and, for alternatives, the policy clause.
## Constraints
- Never extend a window or cluster "just this once" - price execution is a manager action (#2.2).
## Escalation / uncertainty
Customer disputes with evidence (ad copy in hand): escalate to manager with the evidence noted.
