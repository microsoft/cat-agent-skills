---
name: cowork-credit-estimator
description: "estimates cowork task credits before work runs and tracks month-to-date usage. use when the user asks how many credits a task may use, asks to estimate a task's cost, wants to track or log credits, asks about monthly usage or proximity to a limit, or creates or edits a recurring task. estimate only: do not start the priced work or retrieve files, mail, meetings, or web content for sizing. do not use for microsoft pricing, licensing, billing, or copilot subscription questions."
---

# Cowork Credit Estimator

Estimate consumption before a Cowork task runs, track a user-maintained
month-to-date ledger, and stop for the user's decision before doing the
priced work.

## Core rules

- Count up, not down. Report the task estimate and projected month-to-date
  total. Do not present a remaining balance.
- State that every number is a heuristic estimate or arithmetic over the
  user's ledger. This skill cannot read a live credit meter.
- If the host provides a built-in usage command such as `/cost`, treat its
  result as more authoritative than this estimator and use it to calibrate
  future estimates.
- Estimate from the prompt text and existing ledger only. Do not read files,
  search mail, open transcripts, browse the web, or run the requested work
  merely to improve the estimate.
- After reporting the estimate, stop. Let the user choose to run in Cowork,
  use a no-consumption alternative when available, or stop.
- Never make claims about another person's usage or organization-wide
  consumption.

## When not to use

Do not use this skill for:

- Microsoft pricing, licensing, billing, plans, entitlements, or subscription
  questions.
- Organization-wide consumption reporting or comparisons between users.
- Work already in progress, unless the user explicitly asks for a mid-run
  estimate.
- Deciding whether a different agent or application is functionally capable
  of the task. This skill can keep a free alternative visible, but it only
  estimates Cowork consumption.

## Ledger

Use one JSON file named `credit-ledger.json` in the user's Cowork folder root.

Read from `/mnt/user-config/credit-ledger.json`. To update it, write the new
version to `working/credit-ledger.json`, then publish it to the user's Cowork
folder root only after the user approves the write.

Example:

```json
{
  "plan": "capped",
  "monthly_cap": 10000,
  "calibration": 1.3,
  "runs": [
    {
      "date": "2026-09-18",
      "label": "Q3 rollup deck and workbook",
      "band": "L",
      "estimate": 1820,
      "actual": null,
      "note": ""
    }
  ]
}
```

Rules:

- The calendar month is the cycle. Entries automatically group into new months
  by their `date`; never ask the user to reset the ledger.
- Recompute month-to-date totals every time as the sum of `actual` when
  present, otherwise `estimate`, for entries in the selected month.
- `plan` is `capped` or `unlimited`. On unlimited plans, track usage but do
  not warn against a cap.
- `calibration` is a multiplier tuned from user-provided actual usage. Default
  to `1.3` for a new ledger, but describe it as a starting heuristic rather
  than a published rate.
- If the ledger does not exist, say the tracker is starting empty. Do not
  claim the user has consumed zero credits.
- Use `scripts/credit_ledger.py` for all totals, percentages, estimates,
  history, and writes. Do not calculate them by hand.

## Workflow

### 1. Load status

Run:

```bash
python scripts/credit_ledger.py status \
  --ledger /mnt/user-config/credit-ledger.json
```

Check `ledger_found` before describing a zero. Use the returned plan, cap,
month-to-date estimate, percentage, calibration, and flag.

### 2. Size the prompt

Choose the heaviest matching band:

| Band | Typical work | Base estimate |
| --- | --- | ---: |
| XS | One lookup or answer; a few tool calls; no file | 50 |
| S | One summary or short draft; under about 10 tool calls | 200 |
| M | Multi-source retrieval plus one deliverable; about 10 to 30 tool calls | 550 |
| L | Several deliverables or one large build; about 30 to 80 tool calls; iteration | 1,400 |
| XL | Deep research, multiple agents, large multi-file work, or long iterative development | 3,500 |

Apply every relevant multiplier:

| Signal | Multiplier |
| --- | ---: |
| Web research or many fetches | 1.4 |
| Image generation for each few images | 1.3 |
| App build or iterative code loop | 1.6 |
| Long transcripts or large mailbox pagination | 1.3 |
| Repeating the work across many items | 1.5 |
| Repeat of a comparable logged run | 0.8 |

Then apply the ledger's calibration:

```bash
python scripts/credit_ledger.py estimate \
  --ledger /mnt/user-config/credit-ledger.json \
  --band L \
  --flags web,app
```

These bands are relative planning anchors, not Microsoft-published rates.
If the prompt is too vague, give a range across two bands and name the
assumption. Do not retrieve more context to narrow it.

### 3. Size recurring work by the month

For scheduled or recurring tasks, report both per-run and monthly estimates:

```bash
python scripts/credit_ledger.py estimate \
  --ledger /mnt/user-config/credit-ledger.json \
  --band M \
  --recurrence weekdays
```

Supported recurrence values are `none`, `monthly`, `biweekly`, `weekly`,
`weekdays`, and `daily`. The script applies the monthly frequency
multipliers.

### 4. Use the script's verdict

Do not invent thresholds. Use the returned verdict:

- `GO`: projected total is below 60% of a capped plan, or the plan is
  unlimited.
- `HEADS_UP`: projected total is 60% to under 80%.
- `TRIM`: projected total is 80% to 100%. Suggest two concrete scope
  reductions.
- `OVER`: projected total exceeds the cap. Suggest splitting work into
  staged runs, trimming it, or waiting for the next monthly cycle.

### 5. Report and stop

Use no more than five short lines:

```text
Size: L — multi-source pull plus a deck and workbook.
This task: ~1,820 credits, a heuristic rather than a metered figure.
Month to date: ~6,900 -> ~8,720 after this task, based on the user's ledger.
Verdict: Trim — reuse the existing workbook and remove the web-research leg.
Your call: run it here, use a no-consumption alternative if available, or stop?
```

For a pure status request, show only the month-to-date line and the estimate
disclaimer.

An estimate-shaped prompt is estimate-only. Do not begin the underlying task
until the user explicitly chooses to proceed.

### 6. Log approved work

After an M, L, or XL task, offer to log it. Only write after approval:

```bash
python scripts/credit_ledger.py log \
  --ledger /mnt/user-config/credit-ledger.json \
  --label "the user's own task label" \
  --band L \
  --estimate 1820 \
  --out working/credit-ledger.json
```

Publish the resulting `working/credit-ledger.json` to `credit-ledger.json`
in the user's Cowork folder root. Confirm success only after the publish
operation succeeds.

If the user provides a post-run actual, record it as `actual`. Actual values
override estimates in later totals.

### 7. History and calibration

History:

```bash
python scripts/credit_ledger.py history \
  --ledger /mnt/user-config/credit-ledger.json
```

Calibration from a known monthly actual:

```bash
python scripts/credit_ledger.py calibrate \
  --ledger /mnt/user-config/credit-ledger.json \
  --actual 9200 \
  --out working/credit-ledger.json
```

The script sets `calibration = actual_total / estimated_total` for the month.
Explain the new factor and that future estimates use it.

Switch plan type:

```bash
python scripts/credit_ledger.py set-plan \
  --ledger /mnt/user-config/credit-ledger.json \
  --plan unlimited \
  --out working/credit-ledger.json
```

## Guardrails

- Never state estimated consumption as fact.
- Never fabricate a ledger, actual reading, cap, total, or plan type.
- Never perform retrieval or the underlying task merely to size it.
- Never write the ledger without approval.
- Never publish the ledger outside the user's own Cowork folder.
- Never compare users or generalize one ledger to a team or organization.
- If the user chooses to run the work despite a warning, proceed without
  re-asking or re-pricing.
