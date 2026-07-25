---
name: cowork-cost-tracker
description: >-
  After a Cowork task finishes, append an ESTIMATED Copilot Credit cost for that run and show the
  user's month-to-date estimated total as a short cost footer, then point to the Copilot Control
  System for billed actuals. Use when the user says "track my cowork costs", "how much did that
  cost", "show the cost of this run", "what's my cowork spend this month", "cost footer", "log my
  copilot credit usage", or asks to estimate or tally Cowork / Copilot Credit consumption. Do NOT
  use for actual billed invoices, tenant-wide or other users' spend, or Copilot Studio / Azure
  Foundry cost analysis — real billing data lives in the Microsoft 365 and Power Platform admin
  centers and Azure Cost Management, not in this session.
---

# Cowork Cost Tracker

Appends a per-run **estimated** Copilot Credit cost and a running **month-to-date** estimate after a
Cowork task, then reminds the user where the billed actuals live.

## Read this first — what this skill can and cannot do

This skill runs **inside** a Cowork session. It has **no tool that reads the live Copilot Credit
meter**, and no tool that reads the user's real month-to-date billed spend — that data exists only in
the **Copilot Control System** (Microsoft 365 admin center) and the **Power Platform admin center**,
which are admin-scoped and not callable from here.

Therefore this skill produces a **transparent estimate**, never a billed figure:

- It estimates the run's credits from what it *can* observe — the models used, the number of tool
  calls, the amount of retrieved context, document pages processed, and the elapsed runtime — using
  the rates-grounded constants below.
- It keeps a **self-maintained monthly log** of those estimates in the user's own workspace, so the
  "month to date" total only covers runs where this skill was applied — not the tenant meter.
- Every output is labeled **"estimated"** and points to the Copilot Control System for actuals.

**Never present an estimate as a billed charge, and never invent a credit number as if it were read
from a meter.** If asked for the real bill, say it must be read from the Copilot Control System /
Power Platform admin center and offer to explain where.

## When to use

- "How much did that cost?" / "show the cost of this run"
- "Track my Cowork costs" / "add a cost footer"
- "What's my Cowork spend this month?" / "month-to-date estimate"
- "Log my Copilot Credit usage"

## When NOT to use

- The user wants the **actual billed amount**, an invoice, or tenant/department totals → point them to
  the Copilot Control System and Power Platform admin center; do not estimate as if it were billed.
- The user wants **Copilot Studio** agent costs or **Azure Foundry** token/compute costs → those are
  different meters (Power Platform admin center / Azure Cost Management).
- Any request needing another user's or the whole tenant's spend → out of scope.

## Cost model (calibrated to Microsoft's published Copilot Credit rates)

Copilot Credits are priced at **$0.01 per credit** (official). Microsoft does **not** publish a fixed
per-action *Cowork* credit rate — Cowork credits genuinely vary with model use, retrieved context,
tool calls, and runtime. Because Cowork and Copilot Studio share the same **Copilot Credit** currency,
the constants below are **calibrated to Microsoft's published Copilot Studio credit rates for analogous
actions** (a defensible proxy), not arbitrary guesses. They remain user-tunable — fit them to your own
actuals from the Copilot Control System when you have them (see "Personal calibration" below).

```
CREDIT_USD          = 0.01   # $ per Copilot Credit (official)
BASE_CREDITS        = 2      # per task ≈ one generative answer          (published Studio rate: 2)
PER_TOOL_CALL       = 5      # per tool / action call ≈ one agent action (published: 5)
PER_RETRIEVAL       = 10     # per grounded retrieval / file read ≈ tenant-graph grounding (published: 10)
PER_PAGE_PROCESSED  = 8      # per document page processed ≈ content processing (published: 8)
PER_RUNTIME_MINUTE  = 2      # runtime / compute proxy — NOT a published text rate; the term to tune first
MODEL_MULTIPLIER    = 1.0    # ×1 standard; ×4 premium / reasoning (premium AI tools ≈ 5× a generative answer)

est_credits = MODEL_MULTIPLIER * (BASE_CREDITS
              + PER_TOOL_CALL      * tool_calls
              + PER_RETRIEVAL      * retrievals
              + PER_PAGE_PROCESSED * pages_processed
              + PER_RUNTIME_MINUTE * runtime_minutes)
est_usd     = round(est_credits * CREDIT_USD, 2)
```

Every constant except `PER_RUNTIME_MINUTE` is anchored to a Microsoft-published Copilot Studio rate;
runtime has no published text rate, so it is the first dial to adjust against real usage. Present the
result as a **range** (e.g. ±30%) when inputs are uncertain, and state the assumptions if the user asks
how the number was derived.

### Personal calibration (fit to your real burn rate)

The constants above are a rates-grounded proxy, not your tenant's actual per-task rate. To fit them to
reality, pull two numbers from the **Copilot Control System / Power Platform admin center** for a recent
period — **total Copilot Credits consumed by Cowork** and the **number of Cowork tasks** — and compute
your average credits per task. Then keep the published-rate *ratios* above and scale `BASE_CREDITS`
(and, if runtime dominates your tasks, `PER_RUNTIME_MINUTE`) up or down until a representative task lands
on that observed average. Re-check monthly, since Cowork's model mix and rates shift over time.

## Workflow

1. **Observe the finished run.** Count the tool/action calls made, the grounded retrievals or file
   reads, document pages processed, the model tier(s) used, and the approximate active runtime in
   minutes.
2. **Estimate.** Compute `est_credits` and `est_usd` with the formula above.
3. **Load the month log.** Read `cowork-cost-log/<YYYY-MM>.json` from the durable **user** surface
   (cross-session). If it does not exist, start a new one for the current month:
   `{"month": "<YYYY-MM>", "runs": [], "total_credits": 0}`.
4. **Append + tally.** Add `{ "ts", "task", "models", "tool_calls", "retrievals", "pages",
   "runtime_min", "est_credits", "est_usd" }`; recompute `total_credits` and the run count for the month.
5. **Persist.** Write the log back with the artifact tools on `surface="user"`
   (`EditArtifact`, or `CreateArtifact` on first use) — never a direct file write.
6. **Show the footer** (below). Keep it to a few lines; do not expand it into a report unless asked.

## Output format — the cost footer

Append this compact block to the end of the run's response:

```
— Cowork cost (estimated) —
This run:  ~<credits> credits  ≈ $<usd>   (<model>, <n> tool calls, ~<m> min)
Month to date (<Month YYYY>):  ~<credits> credits  ≈ $<usd>  across <k> tasks
Estimate only — billed actuals live in the Copilot Control System.
```

For a richer month-to-date view (3+ figures) you may render a small `render_ui` card instead, but the
one-line-per-fact footer is the default.

## Make it run after every task (optional)

A skill fires when its triggers match — it does not automatically append to *every* Cowork response on
its own. To make the cost footer appear after every task, add one line to your personal instructions
(`copilot-instructions.md`, effective next session):

> "After completing any task, apply the cowork-cost-tracker skill to append the estimated cost footer."

Offer to add this line for the user when they ask for always-on tracking.

## Guardrails

- **Estimate, never actual.** Always label figures "estimated" and cite the Copilot Control System for
  billed amounts. Never claim a number was read from the credit meter.
- **No fabrication.** If runtime or tool-call counts cannot be observed, say so and widen the range —
  do not guess a precise figure.
- **Current user, this-skill runs only.** The monthly total reflects only logged runs, not the tenant
  meter; never imply tenant-wide or other-user coverage.
- **Clean monthly rollover.** Key the log by `YYYY-MM`; never mix months in one total.
- **Local only.** Store the log in the user's own workspace/OneDrive; make no external calls.
