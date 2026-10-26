---
name: schedule-optimize
description: Optimizes the weekly sequence for changeovers with the deterministic campaign heuristic - naive vs optimized compared side by side - using the sequence_optimize engine. Use when the user says "optimize the schedule", "sequence the week", "minimize changeovers", or after capacity-check in a planning run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Operations}
---
# Schedule Optimize
## Purpose
Deterministic sequencing: family campaigns (#3) inside material gates (#2), committed orders protected (#4); reports the naive due-date sequence alongside so the changeover cost of "obvious" ordering is visible.
## When to use
After capacity-check in every run.
## Inputs
checked.json + changeovers.json (family-to-family hours matrix).
## Steps
1. Validate against the contract.
2. Run scripts/sequence_optimize.py --checked checked.json --changeovers changeovers.json --out optimized.json
3. Quote both sequences and both changeover totals verbatim. If the naive sequence misses a committed order once changeovers are counted, lead with that - it is the whole point.
4. This is a heuristic, not a solver (#5 graduation note); say so when precision is questioned.
## Output
optimized.json - the {schedule} hop.
## Grounding requirements
Changeover numbers cite the matrix; lateness calls cite due dates and commitments.
## Constraints
- Sequencing is engine-only; the model never hand-edits a sequence, and never trades a committed order for changeover savings (#4.1).
## Escalation / uncertainty
Overload (#1.2) or unresolvable lateness: escalate to the planner with the tradeoff stated.
