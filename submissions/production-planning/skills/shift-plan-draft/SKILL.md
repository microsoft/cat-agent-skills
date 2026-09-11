---
name: shift-plan-draft
description: Drafts the shift plan from the optimized schedule for the planner to review and publish. Use when the user says "draft the shift plan", "write up the week", "publish the plan" (which produces the draft), or after schedule-optimize in a planning run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Operations}
---
# Shift Plan Draft
## Purpose
Terminal artifact: the shift plan rendered from templates/shift-plan-template.md, populated only from the contract payload.
## When to use
End of every planning run.
## Inputs
optimized.json (full payload).
## Steps
1. Validate against the contract; escalations (gates, overload, protected commitments) lead the draft.
2. Fill the template: sequence with families and changeovers, material-gated starts, utilization with changeovers included, naive-vs-optimized comparison.
3. Mark DRAFT - the planner publishes to execution systems; this plugin never does (#5).
## Output
SHIFT-PLAN-<week>.md - terminal artifact.
## Grounding requirements
Every line cites the engine output; the comparison table is the engine's, verbatim.
## Constraints
- Draft-first (#5): never claim the plan is published or systems updated.
- Nothing in the plan that is not in the contract payload.
## Escalation / uncertainty
A plan with unresolved late committed orders is titled a TRADEOFF DRAFT, not a plan.
