---
name: demand-pull
description: Pulls the demand forecast and open orders for the plan week into the mfg.production-planning.v1 contract. Use when the user says "plan next week", "build the schedule", "pull the orders for line <x>", or when a planning run begins.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Operations}
---
# Demand Pull
## Purpose
Normalize the week's demand: open orders with run hours, families, due dates, commitments.
## When to use
Start of every planning run.
## Inputs
Open-order export (CSV/JSON) with routing run-hours; demand forecast; work-center calendar; material plan; changeover matrix. Emits the entry hop of mfg.production-planning.v1 (schema in contracts/).
## Steps
1. Extract orders: order_id, product, family, run_hours, due_date, committed flag.
2. Record plan_week, week_start, line; keep the exports' identities as citations.
3. Validate against the contract; write plan.json (+ workcenter.json, materials.json, changeovers.json passthrough).
## Output
plan.json - the entry hop.
## Grounding requirements
Every order row cites its export; commitments come from the order record, not from memory.
## Constraints
- Never invent run-hours or due dates; missing routing data stays missing and escalates (#6).
- No feasibility or sequencing opinions here.
## Escalation / uncertainty
Orders missing routing/material rows: record and continue - the engines apply the floor.
