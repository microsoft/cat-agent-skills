---
name: review-pack
description: 'Drafts the vendor review agenda, corrective action request and commitment tracker from the contract payload. Use to close every review prep: "draft the review pack", "build the QBR agenda".'
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Merchandising & Supply}
---
# Review Pack
## Purpose
Terminal artifacts: agenda + CAR draft + commitment tracker, populated only from the contract payload.
## When to use
End of every review prep.
## Inputs
clustered.json (full payload).
## Steps
1. Validate against the contract; trend flags and term triggers lead the agenda.
2. Agenda: scorecard by quarter, clusters with evidence, term citations. CAR: breach, clause, requested actions, response window. Tracker: commitments with owners and dates.
3. Mark DRAFT - the buyer runs the review; nothing changes a PO, holds a payment, amends a contract or deselects the supplier (plugin boundary).
## Output
REVIEW-<vendor>-<period>.md + CAR + tracker - terminal artifacts.
## Grounding requirements
Every line cites a record, cluster or clause.
## Constraints
- Read-only posture; relationship warmth never edits a number (#4.1).
## Escalation / uncertainty
Open items (missing clauses, incomplete quarters) listed explicitly in the agenda.
