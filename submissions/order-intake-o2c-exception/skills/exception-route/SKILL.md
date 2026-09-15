---
name: exception-route
description: Queues validation exceptions with reason codes and a recommended correction per exception, deterministically. Use on "route the exceptions", "what needs fixing before entry", after order-validate.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Commerce}
---
# Exception Route
## Purpose
Deterministic routing: reason code -> queue + recommended correction; action level carried from config (#5.1).
## When to use
After order-validate whenever the order has exceptions.
## Inputs
validated.json + config/o2c-config.json.
## Steps
1. Run scripts/exception_route.py --validated validated.json --config o2c-config.json --out routed.json
2. Quote queues and corrections verbatim; credit review queues the order without bouncing the customer (#4.1).
## Output
routed.json - the {exceptions} hop.
## Grounding requirements
Every exception cites the routing table and config.
## Constraints
- The plugin never self-promotes its action level (#5.1); creation/release stay human-approved at L0-L2.
## Escalation / uncertainty
Exception volume spikes vs history -> note to order-management lead.
