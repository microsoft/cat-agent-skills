# Cowork Cost Tracker

Adds a short **cost footer** to the end of a Cowork run: an **estimated** Copilot Credit cost for that
run plus a **month-to-date** running total, then points you to the Copilot Control System for the
billed actuals.

## What it does

- Estimates each run's credits from observable signals — model tier, tool/action calls, grounded
  retrievals, document pages processed, and runtime — using constants calibrated to Microsoft's
  **published Copilot Studio credit rates** as a proxy (Microsoft does not publish per-action *Cowork*
  rates).
- Keeps a self-maintained monthly log (`cowork-cost-log/<YYYY-MM>.json`) in your own workspace, so the
  month-to-date total covers only the runs where the skill was applied.
- Labels every figure **"estimated"** and never presents it as a billed charge.

## Important limitations

- **It is an estimate, not a meter.** No tool inside a Cowork session reads the live Copilot Credit meter.
- **The runtime term is not a published rate** — it is the first constant to calibrate against real usage.
- **Billed actuals** live in the **Copilot Control System** (Microsoft 365 admin center) and the
  **Power Platform admin center** — not in this skill.

## How to use

Say "how much did that cost", "track my cowork costs", "add a cost footer", or "what's my cowork spend
this month". To make it run after every task, add a one-line rule to your personal
`copilot-instructions.md`.

## Calibrate it

Pull your real Cowork credit total and task count from the Copilot Control System for a recent period,
compute average credits per task, and scale the constants until a representative task lands on that
average.
