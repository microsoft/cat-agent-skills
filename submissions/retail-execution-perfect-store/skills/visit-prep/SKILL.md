---
name: visit-prep
description: Assembles the pre-call plan for a specific outlet - profile, last visit's open actions, promotion status, recent scan performance - into the rtl.retail-execution-perfect-store.v1 contract. Use when the rep says "prep me for <outlet>", "what's the plan for today's calls", "pre-call for store <id>".
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Field Sales}
---
# Visit Prep
## Purpose
The prepared call: outlet profile (channel, cluster), open actions from last visit, active promos, recent scan lines - one page before walking in.
## When to use
Before every visit; start of every execution run.
## Inputs
Outlet master extract, visit history, promotion calendar, scan extract. Emits the entry hop (schema in contracts/).
## Steps
1. Build outlet{} (channel, cluster - the standard key), open actions with dates, active_promo_skus from the calendar.
2. Attach recent scan lines for the outlet's range.
3. Validate against the contract.
## Output
Pre-call plan + visit.json scaffold.
## Grounding requirements
Every item cites its extract (visit id, calendar line, scan row).
## Constraints
- Prep only; no compliance claims before the audit answers exist.
## Escalation / uncertainty
Missing scan extract -> ranking will degrade; note it in the plan (#5).
