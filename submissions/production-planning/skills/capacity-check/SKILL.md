---
name: capacity-check
description: Checks capacity, constraints and material availability for the plan week with the deterministic capacity_check engine. Use when the user says "do we have capacity", "does the week fit", "check materials", or after demand-pull in a planning run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Operations}
---
# Capacity Check
## Purpose
Deterministic load vs available hours (#1) and material gates (#2). Run-hours feasibility only - changeovers are the optimizer's job, and the pairing of the two is where naive plans die.
## When to use
After demand-pull in every run.
## Inputs
plan.json + workcenter.json + materials.json.
## Steps
1. Validate against the contract.
2. Run scripts/capacity_check.py --plan plan.json --workcenter workcenter.json --materials materials.json --out checked.json
3. Quote utilization and gates verbatim. State explicitly that the number excludes changeovers (#1.1) - "92% fits" is not a plan.
## Output
checked.json - the {capacity} hop.
## Grounding requirements
Capacity cites the work-center calendar; gates cite the material plan rows.
## Constraints
- All arithmetic in the engine; a material gate is a hard constraint, never "we'll figure it out" (#2.1).
## Escalation / uncertainty
Missing routing data (#6) or gates: engine escalates; pass them through verbatim.
