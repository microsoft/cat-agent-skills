# Cowork Credit Estimator

Estimate the relative Cowork credit consumption of a task before it runs, track a user-maintained month-to-date ledger, and pause for the user's decision before starting the priced work.

## What it does

- Sizes a prompt from XS through XL using transparent planning anchors.
- Applies multipliers for research, images, iterative code, large inputs, repeated work, and recurrence.
- Projects the task against a personal monthly ledger.
- Supports capped and unlimited plans.
- Records user-provided actual usage and recalibrates future estimates.
- Keeps a no-consumption alternative visible when one is available.

All figures are heuristic estimates or arithmetic over the user's own ledger. The skill cannot read a live credit meter and does not present its planning anchors as Microsoft-published rates.

## Files

```text
cowork-credit-estimator/
├── metadata.json
├── README.md
├── SKILL.md
└── scripts/
    └── credit_ledger.py
```

## Example requests

- "How many credits will this task use?"
- "Estimate the monthly cost of this weekday scheduled prompt."
- "How many credits have I logged this month?"
- "Log that task at the estimate and update my ledger."
- "Am I close to my configured monthly cap?"

## Data and privacy

The helper performs local arithmetic over `credit-ledger.json`. It does not call a metering service, inspect another person's usage, or produce organization-wide consumption claims. Ledger writes are approval-gated and stay in the user's own Cowork storage.

## Limitations

- Estimates are planning aids, not billing records.
- The default cap and calibration are configurable examples, not universal Microsoft limits.
- A host-provided usage reading such as `/cost` is more authoritative and should be used to calibrate the ledger.
- The skill is not for Microsoft pricing, licensing, billing, subscription, or entitlement questions.
