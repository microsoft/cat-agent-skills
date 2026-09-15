---
name: visit-report
description: 'Drafts the evidenced visit report and action register from the contract payload. Use to close every visit: "write the visit report", "log the visit".'
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Field Sales}
---
# Visit Report
## Purpose
Terminal artifacts: visit report with evidence references + action register + suggested order, populated only from the contract payload.
## When to use
End of every visit run.
## Inputs
ranked.json (full payload).
## Steps
1. Validate against the contract; the top-ranked gap leads the report, whatever the compliance % says.
2. Report: compliance table with photo references, ranked gaps with value at stake, actions with owners/dates, suggested order for confirmation.
3. Mark DRAFT - the rep confirms the order and owns the submission; no planogram changes, no trade credit (plugin boundary).
## Output
VISIT-<outlet>-<date>.md - terminal artifact.
## Grounding requirements
Every line cites standard, audit answer, scan row or photo reference.
## Constraints
- Photos are evidence references, never "verified by AI" claims (#3.1).
- The plugin never places the order (#4.1).
## Escalation / uncertainty
Promo-week gaps escalate to the territory manager same-day.
