---
name: policy-retrieve
description: Resolves the applicable policy clause and checks promotion eligibility deterministically with the policy_resolve engine. Use when the question involves returns, price match, rainchecks, promotions, eligibility, or "what does the policy say", after question-intake.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Store Operations}
---
# Policy Retrieve
## Purpose
Deterministic clause resolution (#1) and the three-part promo eligibility test (#2.1): window AND cluster AND SKU.
## When to use
After question-intake in every run.
## Inputs
question.json + config/policy-library.json + config/promo-pack.json.
## Steps
1. Validate against the contract.
2. Run scripts/policy_resolve.py --question question.json --policies policy-library.json --promos promo-pack.json --out resolved.json
3. Quote clause and determination verbatim. An exclusion clause (e.g., marketplace sellers excluded from price match) outranks the general clause - never soften it because the customer is standing there.
## Output
resolved.json - the {policy_resolution, promo_check} hop.
## Grounding requirements
Every determination cites its clause id; promo results cite the promo pack line (#1.1).
## Constraints
- Resolution is engine-only. Out-of-scope questions get an escalation draft, never improvised policy (#1.2).
- Price execution is a manager action either way (#2.2); this skill informs, it does not authorise.
## Escalation / uncertainty
Confidence < 0.75 or no clause -> shift-lead escalation with the draft attached (#4.1).
