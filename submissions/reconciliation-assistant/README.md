# Reconciliation Assistant

Two systems are supposed to agree. The bank statement and the ledger. The payments file and the invoice register. The warehouse count and the inventory system. They never quite do, and finding out *where* they disagree — and proving the difference ties out to a number you can defend — is slow, manual, and error-prone. This skill does it.

Give it two datasets that describe the same underlying records, tell it which column identifies a record and which column holds the amount, and it produces a review-ready reconciliation: what matched, what matched but with a difference, and what's unmatched on each side — with the control totals proven to tie out.

It is deliberately **domain-agnostic**. Nothing in it is specific to any one kind of reconciliation; the same method works for GL-vs-sub-ledger, bank-vs-ledger, invoices-vs-payments, counts-vs-system, roster-vs-export, or any "source A vs source B" comparison. For general-ledger vs sub-ledger work, "GL" and "sub-ledger" are simply Source A and Source B sharing a document or posting reference — matched items confirm agreement, matched-with-difference catches posting errors, unmatched items are your timing differences, and the tie-out is the control-account check.

## What you get

A polished, formatted workbook (or inline tables where the host can't write a file), labelled in your own terms — the sources are named from your file and tab names, never "A" and "B". Where the host can run code, the workbook is **fully formula-driven**: every amount, count, status and classification is a live Excel formula over the two source tabs, so you can edit a source balance and watch the reconciliation — and its control checks — recompute. It's four sheets:

- **Dashboard** — the sign-off front page: a **Control panel** whose checks must each read **OK** (every key appears once, each side agrees to its source tab, the difference proves to the two ledger totals, reconciled + open = total, and no blank/unparseable source amounts remain), a **Reconciliation summary** (total lines, reconciled, open items, match rate, net & gross difference), **Open items by difference type** and **by root cause**, **Difference by account** and **by company & period**, and a plain-English **Headlines** narrative.
- **Reconciliation** — one row per matching key: a **Matching Key** column, the key/description columns, both balances side by side, the signed **Difference**, **Lines in** each source, a **Reconciled / Open Item** status, a **Difference Type**, a **Root Cause** (Measurement / Timing / Scope-mapping), and an **Action Needed** step — all by formula, with a totals row and a "proves to nil" control.
- **Two source tabs** — each ledger reproduced verbatim plus a **Matching Key** helper column the formulas bind to.

Numbers use one consistent format throughout (thousands, two decimals, negatives in parentheses).

**Optional HTML dashboard.** Ask for it and you also get a single self-contained HTML file — same data as the workbook (controls, summary, breakdowns, open-item detail, headlines), styled with a brand palette, light/dark aware and print-friendly — ideal for sharing or attaching without opening Excel.

## Two files, or two tabs in one file

Reconcile two separate files, or **two sheets inside a single workbook** — a common setup where one file holds, say, a "System" tab and a "Manual" tab. Just tell it which two tabs to compare; everything else is the same.

## How it matches

It works in tiers, and a record can only match once:

1. **Exact** — same key, same amount (within a tolerance you set) → *Matched*.
2. **Difference** — same key, amounts disagree → *Matched (with difference)*, with the exact delta.
3. **Similarity** — no shared key, but amount, date, and name all line up within thresholds → *Probable*, sent to Needs Review. Optional — you decide at setup whether to allow it.
4. **Grouped** — one record on one side equals several on the other (e.g. an invoice paid by three partial payments) → sent to Needs Review.
5. **Timing** — the same item posted to a *different period* on each side (same account and amount, different month) → flagged as a timing difference in Needs Review, instead of showing up as two confusing one-sided breaks. Ideal for GL, bank, and accrual reconciliations.
6. **Unmatched** — everything left, split by which side it came from. One-sided items dated near period end are flagged as possible **Timing** differences so common cut-off items are not mislabeled as setup/mapping issues.

The rule underneath all of it: **it never fabricates a match.** Weak or ambiguous evidence goes to Needs Review, never silently into Matched and never dropped. A reconciliation you can't trust is worse than none.

## It proves the numbers tie out

A list of mismatches isn't a reconciliation. The skill computes the identity

```
Total A − Total B = (sum of differences) + (unmatched A) − (unmatched B) + (grouped/probable items)
```

and confirms it closes. A run is only reported tied when the identity closes **and** there are no blank/unparseable amount rows; if either condition fails, the skill reports not tied and shows the residual so you can fix the data or mapping first.

## Works on Cowork, Copilot Studio, and Scout

The method is the same everywhere; the mechanics adapt to the host:

- **Cowork / Scout** — point it at two files (`.xlsx`, `.csv`, `.tsv`). It runs the bundled reference script, handles large files, and writes a workbook plus plain-results companions (`.results.json` and `.results.csv`). Your source files are never modified.
- **Copilot Studio** — on the GitHub Copilot harness, run the same Python script in sandbox (same behavior as Cowork/Scout), including workbook + plain results outputs. If a specific run cannot execute Python, reconcile analytically over the provided tables and render inline output; keep this fallback for modest datasets (typically up to a few hundred rows per source).

## Setup takes a few questions

Before it matches, the skill confirms how strict you want it — because that's a judgement call, not a default it should make for you:

- **Amounts:** exact to the cent, or within a tolerance (and how much)?
- **Similarity matching:** for records with no shared ID, should it *suggest* likely matches by amount + date + name? These always go to Needs Review — never auto-matched. You can turn this off entirely for a pure ID-based reconciliation.
- **How close** a name has to be to count as a suggestion (strict / balanced / loose).
- **Date window** for treating two records as the same event.

Say "just use sensible defaults" and it applies exact-to-the-cent amounts, similarity suggestions on at a balanced threshold, and a 3-day window — and tells you what it used so you can change any of it.

## Configure

The skill runs from the setup answers above, or from a config file if you'd rather pin everything down in advance — different column names on each side, tolerances, date window, sign conventions, currency. Copy `assets/config.example.json`, edit it, and point the skill at it.

## Safety

Your source data is read-only — the skill only ever writes a new report. Everything it reads (cell values, headers, file names) is treated as data, never as instructions, so a row that says "mark everything matched" gets reconciled like any other row. It never reconciles across currencies without an explicit rate, always states the tolerances it used, and always shows its work: every difference is a number, every similarity suggestion lists the evidence behind it. Plain CSV companions are also formula-neutralized so opening them in spreadsheet tools does not execute source-derived formulas.
