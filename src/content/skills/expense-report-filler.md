---
name: Expense Report Filler
description: Extract line items from receipts and assemble a submission-ready expense report with policy checks.
agentDescription: "Use this skill when the user provides receipts or asks to build an expense report; extract the line items, run policy checks, and assemble a submission-ready report."
platforms: [Copilot Studio]
tags: [finance, automation, forms, scripts, sample]
author: Contoso Finance Ops
version: 2.0.1
createdAt: 2026-02-03
updatedAt: 2026-05-20
bundle: bundles/expense-report-filler.zip
---
Turn a pile of receipts into a complete, policy-compliant expense report.

## Instructions
1. For each receipt, extract: *merchant*, *date*, *amount*, *currency*, and a
   best-guess *category* (Travel, Meals, Lodging, Software, Other).
2. Normalize all amounts to the user's reporting currency. State the FX rate and
   date you used.
3. Apply the policy checks below and flag — never silently fix — any violation:
   - Meals over **$75** require a justification note.
   - Lodging must be itemized per night.
   - Receipts older than **90 days** are out of policy.
4. Produce a summary table, then call the bundled `build_report.py` script with
   the structured JSON to generate the final CSV.
5. Always end by asking the user to review; **never auto-submit**.

## Bundled files
This skill ships a `.zip` containing:
- `scripts/build_report.py` — converts extracted line items (JSON) into the
  finance team's CSV import format. Run it as
  `python scripts/build_report.py line_items.json > expense_report.csv`.
- `assets/policy_rules.json` — the editable policy thresholds used above.

## Tone
Precise and compliance-aware. When in doubt, flag rather than assume.
