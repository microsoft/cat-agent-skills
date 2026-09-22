---
name: history-retrieve
description: Retrieves the asset's maintenance history — prior work orders, similar failures, PM records — and the relevant OEM manual and troubleshooting sections, and attaches them to the mfg.maintenance-triage.v1 contract. Use when the user says "pull the history for <asset>", "has this failed before?", "find the manual section", "any prior work orders?", or after fault-intake completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Maintenance
---

# History Retrieve

## Purpose
Enrich the fault payload with grounded history: the asset's prior work orders (with their
recorded failure modes and dates), similar failures on like assets, PM compliance, and the
OEM manual / troubleshooting-guide sections that describe the candidate failure modes.

## When to use
- After fault-intake, in every triage run.
- "Has <asset> failed like this before?" / "pull the work-order history" / "find the manual section".

## Inputs
- `fault-intake.json` (contract inputs from fault-intake).
- Work-order history export (CSV): date, asset, failure_mode, action, downtime.
- OEM manual excerpt (PDF) and troubleshooting guide (Markdown).
- Optional: historian sample (CSV) — vibration/temperature trend. History input is optional;
  the plugin runs from documents alone.

## Steps
1. Filter the work-order history to this `asset_id`; extract each prior WO as
   `{failure_mode, days_ago, action}` into `history.prior_work_orders[]`.
2. Set `history.window_days` to the span covered and count repeat symptomatic fixes.
3. Locate the OEM manual / troubleshooting sections matching the reported symptoms; carry
   their citations forward (they become the `citation` on ranked causes).
4. Write the enriched `history{}` block back onto the contract payload.

## Output
The contract payload with a populated `history{}` object and manual/guide citations — the
input to failure-mode-rank.

## Grounding requirements
Every prior work order cites its CMMS record ID; every manual reference cites the manual
section (e.g. "OEM Pump Manual CP-200 §6.3").

## Constraints
- Retrieval only — do not diagnose or rank here (engine/LLM split).
- Do not infer a failure mode for a prior WO that its record does not state.
- Historian data is optional context, never a required input.

## Escalation / uncertainty
- If history is unavailable, proceed on documents alone and note it in `escalations[]`;
  do not block the run.
