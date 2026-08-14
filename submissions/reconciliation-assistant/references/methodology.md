# Reconciliation methodology

The full matching rules, the tie-out identity, and worked examples. Read this before running Step 3.

## The mental model

A reconciliation compares two sources that *should* describe the same set of records. Every record ends in exactly one of five states:

| State | Meaning |
|---|---|
| Matched | Same record in both sources, amounts agree within tolerance. |
| Matched (with difference) | Same record in both sources, amounts disagree. A real break. |
| Probable (Needs Review) | No exact key, but a similarity pair cleared every threshold. A suggestion. |
| Grouped (Needs Review) | One record on one side corresponds to several on the other (split/partial). |
| Unmatched (A) / Unmatched (B) | Present in one source only. Reported with Difference Type "Missing in &lt;source name&gt;". |

The pool shrinks as tiers run: once a record is matched (or placed in a group), it leaves the pool and cannot match again. This guarantees one-to-one integrity and makes the result deterministic.

## Tier 1 - Exact match

Two records match exactly when their keys are equal under the `keyMap` (case-insensitive and trimmed if configured) **and** their normalized amounts are equal within `amountToleranceAbsolute` or `amountTolerancePercent`.

Worked example. Ledger row `INV-1001 | 1,250.00 | 2026-03-04`; bank row `inv-1001 | 1250.00 | 2026-03-05`. Keys equal after trim + case-fold; amounts equal within 0.01. State: **Matched**. The one-day date gap is irrelevant once the key matches.

## Tier 2 - Matched with difference

Keys equal, amounts differ by more than tolerance. The records are the same item, so this is NOT unmatched - it is a matched pair carrying a difference.

Worked example. Ledger `INV-1002 | 900.00`; bank `INV-1002 | 890.00`. Keys equal, amounts differ by 10.00 > 0.01. State: **Matched (with difference)**, signed difference `A - B = +10.00`. This 10.00 is part of what the tie-out identity must explain.

## Tier 3 - Similarity match (Needs Review)

Only for records with no exact key match, and only when `enableSimilarityMatching` is on (the user opts into this during setup; it is not forced). Pair an A record with a B record when **all three** hold:

- amounts within tolerance,
- dates within `dateWindowDays`,
- similarity of the key/description strings ≥ `similarityThreshold` (use a normalized edit-distance or token ratio in [0,1]).

A similarity pair is **Probable** and always goes to Needs Review. It is never promoted to Matched automatically, no matter how high the similarity.

Worked example. Ledger `GLOBEX INC | 4,300.00 | 2026-03-10` with no invoice number; bank `GLOBEX INC. | 4,300.00 | 2026-03-12`. No shared key, amounts equal, dates within 3 days, name similarity 0.95 ≥ 0.90. State: **Probable (Needs Review)** with the three signals recorded. A human confirms it.

Counter-example. Same amounts and dates but names `ACME CORP` vs `ACME CORPORATION` score only 0.72 similarity - below the 0.90 threshold, so they stay **Unmatched** on their respective sides rather than being paired. Do not match on amount+date alone; many unrelated transactions share a round amount on nearby dates, and even a plausible-looking name expansion can fall below threshold. If the user wants that pair matched, they lower `similarityThreshold` in config with eyes open.

## Tier 4 - Grouped match (Needs Review)

Detect one-to-many and many-to-one relationships when `enableGrouped` is on. A set of up to `groupedMaxMembers` records on one side whose amounts sum, within tolerance, to a single record on the other side.

Worked example. Ledger `INV-1005 | 3,000.00`; bank shows `PMT-A | 1,000.00`, `PMT-B | 1,000.00`, `PMT-C | 1,000.00`. The three payments sum to 3,000.00 within tolerance. State: **Grouped (Needs Review)**, with the invoice and all three payments listed together. Splits are legitimate but a human should see them, because a coincidental sum is possible.

Guard against combinatorial blow-up: the reference implementation restricts the candidate pool to the **same sign** as the target and to members no larger in magnitude than the target, searches larger-magnitude members first, and caps both the pool size and the number of subset attempts. A split therefore matches when several **same-sign** items sum to the target (the overwhelmingly common case - an invoice settled by several payments); a group that only nets to the target through offsetting positive and negative members (e.g. an amount reached via a credit memo) is intentionally left as separate one-sided breaks rather than paid for with an unbounded search. Cap group size at `groupedMaxMembers`.

## Tier 5 - Unmatched

Whatever remains after Tiers 1-4. Records only in A are **Unmatched (A)**; records only in B are **Unmatched (B)**. In the delivered report these carry the Difference Type **"Missing in &lt;source name&gt;"** (e.g. "Missing in Bank statement"), so the one-sided breaks name the source that lacks the record rather than "A"/"B". These are the genuine one-sided breaks: a payment with no matching invoice, an invoice never paid, a statement line the ledger never recorded.

## Tier 4b - Timing differences (annotation)

Runs when `enableTimingDetection` is on and `timingKeyColumn` names the period/date component of the key (e.g., `Period` in a GL reconciliation, or the posting-date column elsewhere). It is checked against the records still unmatched after Tiers 1-4, before they are finalized as one-sided breaks.

A **timing difference** is the same record posted to a **different period**: the same identity minus the period (the "reduced key" - e.g., Company + Account with Period removed), the **same amount** within tolerance, but a different period value. This is the single most common "false" one-sided break in period-based reconciliations - the item is not missing, it landed in the wrong month.

Pair an unmatched A record with an unmatched B record when **all** hold:

- their reduced keys are equal (identity matches once the period is set aside),
- their amounts are equal within tolerance,
- their period values **differ** (same period is not a timing difference - that would have matched at Tier 1).

Timing detection **does not create a new match state**. The two lines **remain `Unmatched (A)` and `Unmatched (B)`** - so the counts and the tie-out still reflect one break on each side - but each is **annotated** with an evidence note ("Possible timing difference - same amount in <other period>"). In the delivered formula workbook these two lines are additionally classified with **Root Cause = Timing** (the "Missing in <source>" line has an offsetting "Missing in <other source>" line for the same reduced key). This keeps two confusing one-sided breaks readable as a single timing story without inventing a state the tie-out would have to special-case.

Worked example. SAP GL has `Co 900001 | Accrued Liabilities | 2025-09 | -5,000`; the internal ledger has `Co 900001 | Accrued Liabilities | 2025-08 | -5,000`. No exact key match (periods differ), so both fall to Unmatched. The reduced key (`Co 900001 | Accrued Liabilities`) and the amount (`-5,000`) are identical and the periods differ, so both lines are annotated as a possible timing difference and classified Root Cause = Timing in the workbook - the accrual was booked a month apart in the two systems.

Because the two lines carry equal and opposite amounts, their net contribution to the tie-out identity is zero - annotating them as timing does not change whether the reconciliation ties.

## The tie-out identity

A reconciliation is only trustworthy if the pieces add back to the whole. With amounts normalized to a common sign convention:

```
TotalA - TotalB
  = Σ(signed differences on Matched-with-difference)
  + Σ(Unmatched A)
  - Σ(Unmatched B)
  + net effect of grouped/probable items not yet confirmed
```

Compute the left side (from the raw control totals in Step 1) and the right side (from the classified results) and confirm they are equal within tolerance. If they do not close, there is a defect - a double-counted match, a sign not normalized, a row dropped - and the result must be presented as **not tied**, with the residual amount shown, rather than as a finished reconciliation.

For a clean run where every item is either matched-equal, matched-with-difference, or one-sided unmatched, the identity reduces to: the net difference between the two control totals equals the sum of the differences plus the one-sided items. If that number is not what the user expected, the breaks in the report explain exactly why.

## GL vs sub-ledger (record-to-record) worked example

A classic detail-vs-detail reconciliation. Source A is the GL detail for an AP control account; Source B is the AP sub-ledger. They share a document number.

- GL `DOC-4400 | 12,000.00` and sub-ledger `DOC-4400 | 12,000.00` → **Matched**. Agreement confirmed.
- GL `DOC-4401 | 8,500.00` and sub-ledger `DOC-4401 | 8,050.00` → **Matched (with difference)**, +450.00. A posting error - a transposition to investigate, not a missing item.
- Sub-ledger `DOC-4402 | 3,200.00` with no GL line → **Unmatched (B)**. A **timing difference**: the invoice is in the sub-ledger but not yet posted to the GL.
- GL `DOC-4403 | 1,000.00` with no sub-ledger line → **Unmatched (A)**. A GL entry the sub-ledger never recorded - a manual journal or a mis-post.

The tie-out then proves it: `GL total − sub-ledger total = +450.00 (difference) + 1,000.00 (unmatched A) − 3,200.00 (unmatched B)`. If that identity closes, the reconciliation is defensible; the four line items above are exactly the exceptions an accountant would chase.

## Control-total tie-out mode

Used when one side is a control figure, not a list. The method is a sum-and-compare, not a line-by-line match.

**Single control figure.** Control side: AP control account balance `482,300.00`. Detail side: 214 sub-ledger rows. Sum the detail (`481,850.00`) and compare. Variance `+450.00`. The control does **not** tie; the 450.00 is the number to investigate (and, if the detail is itemized, the record-to-record mode would locate it). Report is a single tie-out line: control, detail sum, variance, not-tied.

**Multiple control accounts.** Control side: three GL control balances keyed by account (`2000 AP = 482,300`, `2100 Accruals = 91,000`, `2200 Payroll = 60,500`). Detail side: sub-ledger rows each carrying an account code. Group the detail by account code, sum each group, tie each to its control balance:

| Account | Control | Detail sum | Variance | Tied |
|---|---|---|---|---|
| 2000 AP | 482,300.00 | 481,850.00 | +450.00 | No |
| 2100 Accruals | 91,000.00 | 91,000.00 | 0.00 | Yes |
| 2200 Payroll | 60,500.00 | 60,500.00 | 0.00 | Yes |

Plus orphans: any detail row whose account code is not one of the three control accounts, and any control account with no detail rows, are surfaced explicitly. Control-total mode never labels individual detail rows "Matched" - there is no counterpart to match them to; the deliverable is the per-account variance and the orphans.

## Duplicates and ambiguity

- **Intra-source duplicates** (same key twice in one source) make a one-to-one match ambiguous. Report them in Diagnostics and, when matching, pair by nearest amount/date, leaving the surplus duplicate as unmatched for review rather than arbitrarily consuming a partner.
- **Multiple exact-key candidates** across sources (same key appears twice on both sides) are matched by nearest amount then nearest date; any leftover goes to Needs Review.
- **Ambiguous dates** (a column that parses as both `MM/DD` and `DD/MM`) are flagged, not silently resolved.

## What this skill is not

- Not a join/enrich tool: it does not glue extra columns from B onto A for records that are not being reconciled.
- Not a deduplicator for a single list.

## How the states map to the delivered workbook

The formula-driven workbook (Cowork/Scout code path) presents one row per matching key and derives, by live Excel formula:

- **Status** — *Reconciled* where the difference rounds to nil, otherwise *Open Item*.
- **Difference Type** — *Amount mismatch* (both sides present, amounts disagree), *Missing in &lt;source&gt;* (present on only one side), or *None* (agrees).
- **Root Cause** — *Measurement* for an amount mismatch; *Timing* where an offsetting *Missing in &lt;other source&gt;* line exists for the same key minus its period (the classic "posted a month apart" case, matching Tier 4b); *Scope / mapping* otherwise.
- **Action Needed** — a plain-language next step keyed off the root cause.

The Dashboard rolls these up (control panel, summary, open items by difference type and by root cause, difference by account and by company/period) — every figure a formula over the two source tabs, so editing a source balance recomputes the whole reconciliation and its controls. The optional HTML dashboard is generated from the identical computation, so it always agrees with the workbook.
- Not a general analytics tool: the only question it answers is "do these two sources agree, and if not, exactly where and by how much".
