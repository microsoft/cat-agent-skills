# Document Extraction and Verification

Shared reference for skills that read figures out of borrower documents. Read with `house-rules.md`, which governs source tiers, accounting basis, and the credit-decision gate.

## Retrieval and extraction routes

Check what this session supports; do not assume a route or hardcode one.

1. If a document-extraction or IDP connector is configured and covers this document type, use it and record its per-field confidence where it provides one.
2. Otherwise read the document directly — native text where the file has a text layer, page-image reading where it does not.
3. If neither route can read the document, report `NOT RETRIEVED` and ask for the file in a different format.

Reading a scanned page is a normal route, not a fallback that needs an apology. What matters is that every figure passes the verification gate below before it reaches a spread, a covenant test, or a memo.

## Document quality

Quality determines how much verification a figure needs, never whether the document is usable.

| Input | Expect | Handling |
|---|---|---|
| Spreadsheet, CSV | Exact values | Verify the gate; check for hidden rows, filters, and off-sheet formulas |
| PDF with a text layer | Exact values | Verify the gate |
| Clean scan or photo | Accurate but not guaranteed | Verify the gate; re-read any figure in a failed tie |
| Poor scan, fax, skewed or shadowed photo | Errors likely | Verify the gate; report `NOT LEGIBLE` per figure rather than guessing |
| Handwriting, stamps, marginalia | Not reliable | Report `NOT LEGIBLE` and ask whether the annotation is authoritative |

When a figure cannot be read with confidence, the marker is `NOT LEGIBLE — <document>, page <n>, <line item>`. The remedy is a cleaner copy. Do not report it as `NOT FOUND`, which means the source has no such record, and do not report it as `NOT RETRIEVED`, which means the document could not be opened at all.

**Never supply a figure that was not read.** If a digit, caption, or line item is obscured, cut off, or illegible, it is `NOT LEGIBLE` even when its value could be inferred arithmetically. Never guess a digit, never infer a number from a subtotal, and never carry a partially read figure into a calculation. If extraction quality is poor across a statement, say so and stop rather than producing a spread, covenant test, or recap built on guesses.

## Scale, signs, and captions

These four traps cause the largest errors, and all four are silent.

- **Scale.** Statements state their units once, usually in a header: *"in thousands"*, *"in millions"*, *"$000s"*. Read it and record it on every extraction. A missed scale marker is a 1,000× error. If the units are not stated anywhere, mark the set `GAP — units not stated` and ask; do not assume dollars.
- **Signs.** `(31,096)` is negative thirty-one thousand and ninety-six. Preserve the sign. Some statements show negatives with a minus, some in parentheses, some in red — colour is lost in monochrome scans, so never rely on it. Record expenses and uses of cash with the sign as presented, and say which convention the document uses.
- **Column discipline.** Comparative statements place two or more periods side by side, often with similar magnitudes. Confirm which column is which period from the column header, not from position, and re-check after any failed tie. Column bleed is the most common OCR failure on financial statements and it is invisible in the output.
- **Captions.** Extract the caption as printed. "Selling, general and administrative" and "Operating expenses" are not interchangeable, and mapping one to the other is a normalisation decision that must be shown, not hidden.

Footnote markers attached to a caption — `Inventory (2)` — belong to the caption, not the number.

## Verification gate — mandatory

Run every check that the supplied statements make possible, **before** any figure is used downstream. These are arithmetic identities, so a failure means either a misread figure or a genuine defect in the source. Both matter.

1. **Balance sheet balances.** Total assets = total liabilities + total equity, each period.
2. **Subtotals sum.** Every subtotal equals its components, on every statement.
3. **Comparatives agree.** The prior-period column matches the prior period's own statement, where both were supplied.
4. **Cash ties.** Cash-flow net change in cash = the balance-sheet cash delta for the same period.
5. **Equity rolls forward.** Closing retained earnings = opening + net income − distributions, where the movement is disclosed.

Record which checks ran and which could not — an income-statement-only submission supports only check 2.

### When a check fails

1. **Re-read the lines involved.** Most failures are extraction errors: a misread digit, a bled column, a missed scale marker.
2. **If the figures are confirmed as printed**, the source statement itself does not tie. That is a finding for the analyst, not a bug to fix. Report it: name the check, the two sides, and the difference. Do not adjust, balance, or plug the statement to make it tie.
3. **Either way, mark the affected figures.** A figure that fails verification is not usable for a ratio or a covenant test until it is resolved.

**Scope of exclusion is per metric.** A failed check suppresses the cells that depend on the affected figures, for the affected period only. It does not invalidate the borrower, the other periods, or unrelated metrics. If cost of goods sold cannot be verified, gross margin is suppressed — revenue, cash, and leverage remain.

Never present a figure that failed verification as though it passed, and never describe a set as "verified" when checks were skipped for lack of inputs.

## Periods

- State the period end and the period length on every column: `FYE 2025-12-31`, `9ME 2026-09-30`.
- Never compare a stub period to a full year, or an interim to an annual, without labelling both. Annualising a stub period is a projection — say so, or do not do it.
- A trailing-twelve-month figure requires four consecutive periods on the same basis and the same entity. If any component is missing, restated, or on a different basis, output `NOT COMPARABLE — RECONCILIATION REQUIRED` rather than an approximate TTM.
- Where the fiscal year end changed, or the statements cover a transition period, say so and do not compute a trend across the break.
- Where a prior period was restated, use the restated figures and note the restatement. Never subtract a restated period from an unrestated one.

## Derived figures

Every derived figure names its basis, shows its arithmetic, and is labelled derived.

**One basis per column. Never pool inputs from different scopes.** The common error is combining depreciation and amortisation taken from the cash-flow statement with an operating income figure from the income statement: cash-flow D&A is an entity-total and need not equal the D&A embedded in operating income, so the error differs by borrower and is invisible.

Acceptable bases for a derived EBITDA, in order:

1. A borrower-reported EBITDA with its reconciliation shown.
2. Operating income plus a D&A figure evidenced as sitting inside that same operating income subtotal — for example a D&A line presented on the face of the income statement above operating income.
3. Neither available → `NOT COMPARABLE — RECONCILIATION REQUIRED`.

**Scope the marker to the cells that depend on it.** `NOT COMPARABLE` on EBITDA withholds only the EBITDA-dependent cells — EBITDA itself, EBITDA margin, leverage, coverage, and any summary statistic computed from them. Every other metric the period still qualifies for — revenue, growth, operating margin, working capital, net debt — is retained and stays in its own summaries. The period is never dropped from the spread.

The same discipline applies to every constructed metric: fixed-charge coverage, funded debt, working capital, and any covenant-defined term.

**Covenant-defined terms override generic definitions.** Where a credit agreement defines EBITDA, Funded Debt, or Fixed Charges, compute it as the agreement defines it and cite the defined-term section. A generic market definition is not a substitute and must never be silently used in its place.

## Add-backs and adjustments

Every add-back needs an evidenced source, an amount, and an asserter.

- Name the document and page supporting it, and who asserted it: borrower, CPA, or the credit agreement's defined term.
- Label borrower-asserted add-backs `borrower-asserted, not independently verified`.
- Never originate an add-back the borrower did not claim, and never apply an add-back from one period to another.
- Show adjusted and unadjusted figures side by side. Never replace a reported figure with an adjusted one.

## Ratios

- Show the formula and both inputs for every ratio.
- Where a denominator is zero or negative, output `N/M` — never a coverage or leverage multiple on nonpositive EBITDA or nonpositive debt service. `N/M` is not zero.
- Preserve genuinely meaningful negatives. Net cash, negative working capital, and an accumulated deficit are real values, not errors.
- Markers never become numbers. `NOT LEGIBLE`, `NOT FOUND`, `NOT RETRIEVED`, `NEEDS FEED`, `GAP`, and `N/M` never enter arithmetic and are never treated as zero. Missing values must be blank or the marker, never `0`, because a zero silently corrupts downstream ratios. A ratio with a marker among its inputs is itself a marker.
- Peer or industry comparatives require a source that provides them. Where none is configured, the borrower's own ratios and trend stand alone — mark comparatives `NEEDS FEED — peer benchmark source (e.g. RMA, Moody's, S&P)` rather than estimating a norm.
