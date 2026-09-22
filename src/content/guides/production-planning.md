# Production Planning

For the planner who has to publish a shift plan on Friday and knows that the spreadsheet's
"84% loaded" is not the same thing as a plan that will actually run.

It pulls the demand forecast and open orders, checks capacity, constraints and material
availability, sequences the week to minimise changeovers with a deterministic campaign
heuristic, and drafts the shift plan for the planner to publish.

## How it works

1. Pulls the demand forecast and open orders.
2. Checks work-centre capacity, constraints and material availability (deterministic).
3. Sequences for changeovers with a campaign heuristic (deterministic).
4. Drafts the shift plan for the planner to publish.

## Example scenario

"84% loaded, run it by due date." Three things that number hides:

- The naive due-date sequence alternates product families — pump, valve, pump, valve — and burns
  **more than ten hours** in changeovers. Run-hours utilisation is not a plan.
- One committed order is material-gated until Wednesday.
- Between the changeovers and the gate, the naive sequence finishes a **committed customer
  order late**.

The engine reports the naive miss, produces a campaign sequence that protects both committed
orders, drops the changeover hours, and names the material gate in the escalation.

## What you bring

The demand plan and open orders, work-centre capacity, the changeover matrix and material
availability. JSON or spreadsheet exports both work.

## Boundaries

The shift plan is a draft for the planner to review and publish. Sequencing uses a campaign
heuristic rather than an optimisation solver.
