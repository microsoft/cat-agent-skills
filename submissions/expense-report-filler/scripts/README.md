# Expense Report Filler — Script Bundle

Helper scripts used by the **Expense Report Filler** Copilot Studio skill.

## Contents
- `build_report.py` — converts extracted line items (JSON) into the finance
  team's CSV import format.
- `policy_rules.json` — editable policy thresholds (meal limits, receipt age).

## Requirements
- Python 3.9+ (standard library only).

## Usage
```bash
python build_report.py line_items.json > expense_report.csv
```

`line_items.json` is the structured output the skill produces from receipts.
Adjust `policy_rules.json` to match your organization's expense policy.
