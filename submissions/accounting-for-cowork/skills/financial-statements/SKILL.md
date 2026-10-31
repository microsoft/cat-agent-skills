---
name: financial-statements
description: "Creates, analyzes, and ties out accounting reporting deliverables from source balances through final presentation and disclosure. Supports financial statements, trial balances, cash-flow workbooks, reporting packages, monthly close summaries, variance models, AR/AP aging, fixed-asset rollforwards, depreciation schedules, and footnote drafts. Calculates dollar and percentage variances, highlights material movements or unsupported balances, preserves drill-down to source data, and documents assumptions, adjustments, control checks, and review status. Use when preparing, analyzing, reconciling, explaining, or drafting financial statements, disclosures, reports, aging analyses, or supporting schedules."
metadata:
  version: '1.0.0'
  category: 'analysis'
  icon: 'DocumentTable'
  argument-hint: '<deliverable> [period]'
---

# Financial Reporting

**Important**: This skill guides financial-reporting workflows but does not provide financial advice. All statements, memos, and disclosures should be reviewed by qualified financial professionals before use in reporting or filings.

This is the general guideline for **financial reporting** — financial statements, reporting packages, footnotes and disclosures, technical accounting memos and position papers, management commentary, and financial-review / board / investment-committee decks. Match the guidance to the deliverable you must produce:

- **Statements & reporting packages** — the workflow below (income statement, trial-balance workbook, monthly summary, balance sheet, cash flow, GAAP presentation ASC 220/210/230, period-end adjustments) with period-over-period comparison and variance.
- **Technical accounting memos / position papers / reference guides** (impairment, capitalization, revenue recognition, lease/debt) — write the actual technical analysis, scaffolded: (1) entity/business background — nature of operations, offerings, customers, primary expense categories; (2) the governing ASC cited at subsection level, with **every** criterion, scope exception, and definitional component of the cited subsections enumerated and individually assessed — a correct gist that omits a listed exception or half of a two-part definition is incomplete; (3) the comparison the standard's **chosen path** requires — and only that path: a qualitative (step-0) assessment **provides a substantive section for each qualitative factor** — relevant macroeconomic conditions, industry and market considerations, cost factors, financial performance, entity-specific events — writing the actual conditions that apply (with figures and named developments) and tying each to management's specific facts, then concludes there; related-standard context that frames the analysis (e.g., ASC 730 R&D classification for pre-feasibility costs, feasibility elements under ASC 985) is part of the required substance, not padding, without proceeding to an unrequested quantitative test and without importing public-market indicators for a private reporting unit unless their relevance is explained; when the quantitative path applies, show it (e.g., fair value vs. carrying amount for impairment) with actual and forecast data; (4) for segment/CODM analyses, the CODM's title and review/allocation frequency. These are graded on substance, not brevity — a terse "no adverse change" conclusion fails.
- **Slide decks** (financial-review, board, investment-committee) — build the reporting content here, then use `financial-presentations` for deck structure, slide principles, and chart selection.

Clarify like the professional in the room: resolve a genuinely fatal ambiguity (two entities share the requested name; the reporting period is unstated) explicitly before building — but ask only what the requester's role can answer, never re-ask facts the conversation already gave, and list each recurring action once under its correct cadence (an item is monthly *or* annual, never duplicated as both).

**Read [Financial Reporting Standards](references/financial-reporting-standards.md) before you build** — the build contract these deliverables are graded on, applied as checks on your own work rather than a template: enumerate every named artifact as a grid before building, link derived figures with live formulas, apply only the reporting conventions that fit the requested shape, and work through its verification checklist before returning any workbook.

Whatever the deliverable: before handing over, re-open the delivered file and confirm every explicitly requested file, tab, section, and figure exists under its requested name and is internally consistent.

## Statement structure & tab discipline (read first)

Build the **specific statements and tabs the task names**, structured the way a reviewer expects — not a generic template dump.

- **Build exactly the tabs requested.** If the task asks for a per-entity trial balance for each entity plus a Consolidated tab and an Eliminations tab, produce exactly those named tabs. Do not substitute a pile of generic raw-schedule tabs for the specific statement/consolidation structure asked. Every statement the task names (Balance Sheet, Statement of Operations, Statement of Equity, Cash Flows) must exist as its own clearly-labeled tab.
- **Suppress empty boilerplate captions.** Include only statement captions that have a matching, non-zero account in the trial balance. Do **not** add standard-template caption rows (e.g., "Interest income", "Long-term investments", "Deferred tax assets") that this entity's trial balance has no account for and that resolve to $0 — an empty $0 caption reads as a defect. Add a caption only when it ties to real source data.
- **Make the balance sheet balance.** Total Assets must equal Total Liabilities + Equity, tied by formula; show the check. If it does not tie, fix the mapping before delivering.
- **Cash flow per ASC 230.** When a statement of cash flows is requested, break it into Operating, Investing, and Financing sections, and (for a rollforward) tie the change in cash to the balance-sheet cash movement.
- **Consolidation & eliminations.** Eliminate intercompany balances only to the extent the receivable and payable sides match; flag any unresolved residual with its dollar amount rather than forcing it to net to zero. Distinguish an account with no supporting schedule from one that genuinely ties to a $0 difference.
- **Build requested footnote breakouts.** When the task asks for a footnote detail (e.g., PPE by asset class, preferred stock by unit/series, debt by instrument), create that breakout as its own section/tab.

## Usage

```
/financial-statements <deliverable> [period]
```

### Arguments

- `deliverable` — The financial-reporting output to produce (e.g., `income-statement`, `balance-sheet`, `cash-flow`, `trial-balance-workbook`, `monthly-financial-summary`, `reporting-package`, `gaap-presentation`, `technical-accounting-memo`, `disclosure`, `board-deck`)
- `period` — The reporting period, when applicable (e.g., `2024-12`, `2024-Q4`, `2024`, `2024-YTD`), with its comparison basis. Common period types: `monthly` (prior month + prior-year month), `quarterly` (prior quarter + prior-year quarter), `annual` (prior year), `ytd` (prior-year YTD). If omitted, ask for the period and comparison basis (prior period, prior year, budget/forecast).

## Workflow

### 1. Gather Financial Data

If an ERP system or data warehouse is connected:
- Pull trial balance or income statement data for the specified period
- Pull comparison period data (prior period, prior year, budget/forecast)
- Pull account hierarchy and groupings for presentation

If no data source is connected:
> Connect an ERP system or data warehouse to pull financial data automatically. You can also paste trial balance data, upload a spreadsheet, or provide income statement data for analysis.

Prompt the user to provide:
- Current period revenue and expense data (by account or category)
- Comparison period data (prior period, prior year, and/or budget)
- Any known adjustments or reclassifications

### 2. Generate Income Statement

Present in standard multi-column format:

```
INCOME STATEMENT
Period: [Period description]
(in thousands, unless otherwise noted)

                              Current    Prior      Variance   Variance   Budget    Budget
                              Period     Period     ($)        (%)        Amount    Var ($)
                              --------   --------   --------   --------   --------  --------
REVENUE
  Product revenue             $XX,XXX    $XX,XXX    $X,XXX     X.X%       $XX,XXX   $X,XXX
  Service revenue             $XX,XXX    $XX,XXX    $X,XXX     X.X%       $XX,XXX   $X,XXX
  Other revenue               $XX,XXX    $XX,XXX    $X,XXX     X.X%       $XX,XXX   $X,XXX
                              --------   --------   --------              --------  --------
TOTAL REVENUE                 $XX,XXX    $XX,XXX    $X,XXX     X.X%       $XX,XXX   $X,XXX

COST OF REVENUE
  [Cost items]                $XX,XXX    $XX,XXX    $X,XXX     X.X%       $XX,XXX   $X,XXX
                              --------   --------   --------              --------  --------
GROSS PROFIT                  $XX,XXX    $XX,XXX    $X,XXX     X.X%       $XX,XXX   $X,XXX
  Gross Margin                XX.X%      XX.X%

OPERATING EXPENSES
  Research & development      $XX,XXX    $XX,XXX    $X,XXX     X.X%       $XX,XXX   $X,XXX
  Sales & marketing           $XX,XXX    $XX,XXX    $X,XXX     X.X%       $XX,XXX   $X,XXX
  General & administrative    $XX,XXX    $XX,XXX    $X,XXX     X.X%       $XX,XXX   $X,XXX
                              --------   --------   --------              --------  --------
TOTAL OPERATING EXPENSES      $XX,XXX    $XX,XXX    $X,XXX     X.X%       $XX,XXX   $X,XXX

OPERATING INCOME (LOSS)       $XX,XXX    $XX,XXX    $X,XXX     X.X%       $XX,XXX   $X,XXX
  Operating Margin            XX.X%      XX.X%

OTHER INCOME (EXPENSE)
  Interest income             $XX,XXX    $XX,XXX    $X,XXX     X.X%
  Interest expense           ($XX,XXX)  ($XX,XXX)   $X,XXX     X.X%
  Other, net                  $XX,XXX    $XX,XXX    $X,XXX     X.X%
                              --------   --------   --------
TOTAL OTHER INCOME (EXPENSE)  $XX,XXX    $XX,XXX    $X,XXX     X.X%

INCOME BEFORE TAXES           $XX,XXX    $XX,XXX    $X,XXX     X.X%
  Income tax expense          $XX,XXX    $XX,XXX    $X,XXX     X.X%
                              --------   --------   --------

NET INCOME (LOSS)             $XX,XXX    $XX,XXX    $X,XXX     X.X%       $XX,XXX   $X,XXX
  Net Margin                  XX.X%      XX.X%
```

### 3. Variance Analysis

For each line item, calculate and flag material variances.

#### Variance Calculation

For each line item, calculate:
- **Dollar variance:** Current period - Prior period (or current period - budget)
- **Percentage variance:** (Current - Prior) / |Prior| x 100
- **Basis point change:** For margins and ratios, express change in basis points (1 bp = 0.01%)

#### Materiality Thresholds

Define what constitutes a "material" variance requiring investigation. Common approaches:

- **Fixed dollar threshold:** Variances exceeding a set dollar amount (e.g., $50K, $100K)
- **Percentage threshold:** Variances exceeding a set percentage (e.g., 10%, 15%)
- **Combined:** Either the dollar OR percentage threshold is exceeded
- **Scaled:** Different thresholds for different line items based on their size and volatility

> **Thresholds gate the narrative, not the presentation.** A materiality threshold decides which variances get a written explanation — it never removes account lines from the statement or schedule. When the user provides detailed account data, present every provided line and reserve the threshold for selecting what to investigate/narrate.

*Example thresholds (adjust for your organization):*

| Line Item Size | Dollar Threshold | Percentage Threshold |
|---------------|-----------------|---------------------|
| > $10M        | $500K           | 5%                  |
| $1M - $10M    | $100K           | 10%                 |
| < $1M         | $50K            | 15%                 |

#### Variance Decomposition

Break down total variance into component drivers:

- **Volume/quantity effect:** Change in volume at prior period rates
- **Rate/price effect:** Change in rate/price at current period volume
- **Mix effect:** Shift in composition between items with different rates/margins
- **New/discontinued items:** Items present in one period but not the other
- **One-time/non-recurring items:** Items that are not expected to repeat
- **Timing effect:** Items shifting between periods (not a true change in run rate)
- **Currency effect:** Impact of FX rate changes on translated results

#### Investigation and Narrative

For each material variance:
1. Quantify the variance ($ and %)
2. Identify whether favorable or unfavorable
3. Decompose into drivers using the categories above
4. Provide a narrative explanation of the business reason
5. Assess whether the variance is temporary or represents a trend change
6. Note any actions required (further investigation, forecast update, process change)

### 4. Key Metrics Summary

```
KEY METRICS
                              Current    Prior      Change
Revenue growth (%)                                  X.X%
Gross margin (%)              XX.X%      XX.X%      X.X pp
Operating margin (%)          XX.X%      XX.X%      X.X pp
Net margin (%)                XX.X%      XX.X%      X.X pp
OpEx as % of revenue          XX.X%      XX.X%      X.X pp
Effective tax rate (%)        XX.X%      XX.X%      X.X pp
```

### 5. Material Variance Summary

List all material variances requiring investigation:

| Line Item | Variance ($) | Variance (%) | Direction | Preliminary Driver | Action |
|-----------|-------------|-------------|-----------|-------------------|--------|
| [Item]    | $X,XXX      | X.X%        | Unfav.    | [If known]        | Investigate |

### 6. Output

Provide:
1. Formatted income statement with comparisons
2. Key metrics summary
3. Material variance listing with investigation flags
4. Suggested follow-up questions for unexplained variances
5. Offer to drill into any specific variance in more detail

## Trial Balance Workbook

A trial balance (snapshot) workbook links every account balance to its supporting schedule and adjustments, so a reviewer can trace any GL balance to its support and immediately see what does not tie out.

### Workbook Structure

Organize the workbook with one tab per layer:

1. **Trial Balance (lead tab)** — every account, organized by financial statement section, with formula links to support
2. **Lead schedules** — one tab per significant account or account group (cash, AR, prepaid, fixed assets, AP, accruals, debt, equity), each independently totaling to the amount it supports
3. **Adjustments tab** — all post-close and top-side adjustments in one register, referenced from the TB by entry number
4. **Tie-out summary (reviewer tab)** — exception listing of every account whose support does not reconcile to the GL

### Trial Balance Tab Format

| Account # | Account Name | FS Section | Opening Balance | Activity | Adjustments | Ending Balance | Support Ref | Per Support | Difference | Status |
|-----------|--------------|------------|-----------------|----------|-------------|----------------|-------------|-------------|------------|--------|
| [#] | [Name] | Assets — Current | $X,XXX | $X,XXX | $X,XXX | $X,XXX | [Tab name] | $X,XXX | $0 | Tied / Exception |

**Construction rules:**

1. **Separate opening balance, activity, and adjustments.** Ending balance must be a formula: `Opening + Activity + Adjustments` — never a hardcoded number.
2. **Link, don't retype.** "Per Support" pulls from the lead schedule tab by formula; "Difference" is `Ending Balance - Per Support`. A retyped number defeats the tie-out.
3. **Reference every adjustment.** Each adjustment amount on the TB references an entry number in the adjustments register, with the register carrying the description, preparer, and approval.
4. **Distinguish manual from system-posted entries.** Tag each adjustment as system-posted or manual/top-side — manual entries get reviewer focus.
5. **Make the tie-out binary.** Status is a formula: difference of zero = "Tied," anything else = "Exception." No judgment calls embedded in the workbook.

### Tie-Out Summary Format

The reviewer tab lists only exceptions:

| Account # | Account Name | GL Balance | Per Support | Difference | Cause (if known) | Owner | Resolution |
|-----------|--------------|-----------|-------------|------------|------------------|-------|------------|
| [#] | [Name] | $X,XXX | $X,XXX | $X,XXX | [Missing schedule / timing / error] | [Name] | [Action + date] |

Include summary counts: accounts tied / total accounts, total unexplained difference in dollars, and number of accounts with no supporting schedule (unsupported balances are exceptions even when no difference is visible).

## Monthly Financial Summary

A one-to-two page management summary that combines headline financial results with close health — what changed this month, what is unreconciled, and what needs follow-up before next close.

### Summary Structure

```
MONTHLY FINANCIAL SUMMARY — [Period]

HEADLINE RESULTS
| Metric | Actual | Budget | Var ($) | Var (%) | Prior Month |
|--------|--------|--------|---------|---------|-------------|
| Revenue / Gross margin / Operating income / Net income / Cash |

KEY BALANCE SHEET MOVEMENTS
[3-5 bullets: the largest balance changes this month and why —
e.g., "AR up $1.2M on two large invoices billed in final week;
collection expected mid-next-month."]

TOP INCOME STATEMENT VARIANCES
[3-5 bullets from the material variance summary: item, $ and %
variance, driver, and whether it persists.]

RECONCILIATION STATUS
| Category | Reconciled | Open Items | Open $ | Oldest Item |
|----------|-----------|------------|--------|-------------|
| Cash / AR / AP / Other BS accounts |

[One line per category; detail stays in the rec workbook.]

CASH IMPACTS AND TIMING
[Significant cash inflows/outflows this month and known items
hitting next month — debt payments, tax deposits, large receipts.]

FOLLOW-UP FOR NEXT CLOSE
[Numbered list: open items with owner and due date — unresolved
reconciling items, expected adjustments, process issues that
slowed this close.]
```

### Writing Guidance

1. **Lead with what changed**, not what stayed the same. A reader should learn the month's story in the first half page.
2. **Tie every callout to a number.** "AR aged past 90 days grew $340K" — not "receivables aging worsened."
3. **Connect close health to financial risk.** An unreconciled account is a potential misstatement — state the exposure, not just the count.
4. **Keep follow-ups accountable.** Every follow-up item carries an owner and a date; reuse them as the starting checklist for next month's summary.

## GAAP Presentation Requirements

### Income Statement (ASC 220 / IAS 1)

- Present all items of income and expense recognized in a period
- Classify expenses either by nature (materials, labor, depreciation) or by function (COGS, R&D, S&M, G&A) — function is more common for US companies
- If classified by function, disclose depreciation, amortization, and employee benefit costs by nature in the notes
- Present operating and non-operating items separately
- Show income tax expense as a separate line
- Extraordinary items are prohibited under both US GAAP and IFRS
- Discontinued operations presented separately, net of tax

**Common presentation considerations:**

- **Revenue disaggregation:** ASC 606 requires disaggregation of revenue into categories that depict how the nature, amount, timing, and uncertainty of revenue are affected by economic factors
- **Stock-based compensation:** Classify within the functional expense categories (R&D, S&M, G&A) with total SBC disclosed in notes
- **Restructuring charges:** Present separately if material, or include in operating expenses with note disclosure
- **Non-GAAP adjustments:** If presenting non-GAAP measures (common in earnings releases), clearly label and reconcile to GAAP

### Balance Sheet (ASC 210 / IAS 1)

- Distinguish between current and non-current assets and liabilities
- Current: expected to be realized, consumed, or settled within 12 months (or the operating cycle if longer)
- Present assets in order of liquidity (most liquid first) — standard US practice
- Accounts receivable shown net of allowance for credit losses (ASC 326)
- Property and equipment shown net of accumulated depreciation
- Goodwill is not amortized — tested for impairment annually (ASC 350)
- Leases: recognize right-of-use assets and lease liabilities for operating and finance leases (ASC 842)

### Cash Flow Statement (ASC 230 / IAS 7)

- Indirect method is most common (start with net income, adjust for non-cash items)
- Direct method is permitted but rarely used (requires supplemental indirect reconciliation)
- Interest paid and income taxes paid must be disclosed (either on the face or in notes)
- Non-cash investing and financing activities disclosed separately (e.g., assets acquired under leases, stock issued for acquisitions)
- Cash equivalents: short-term, highly liquid investments with original maturities of 3 months or less
- **Tie-outs are formulas on the face of the statement**: beginning and ending cash each tie to the balance-sheet cash balance for their date; ending cash = beginning cash + net change, shown as a visible check that recomputes. When building from balance-sheet data, derive each line item via a balance-sheet rollforward (the change in each account mapped to its operating/investing/financing line — every balance-sheet account's movement accounted for, none dropped or lumped beyond the prompt's grouping), and call out supplementary disclosures for significant non-cash items alongside the statement.

## Changes in Accounting Estimate (ASC 250)

A revision to an asset's **useful life or salvage/residual value** — e.g., management shortens a truck's life from 10 years to 7 — is a **change in accounting estimate**, not an error and not a change in principle. It is applied **prospectively**. This rule governs depreciation, amortization, allowances, and any other estimate-driven balance.

**How to apply a useful-life change prospectively:**

1. **Do not restate prior periods.** Accumulated depreciation through the change date stays exactly as originally recorded (on the original life/method). Never recompute prior-year depreciation as if the new life had always applied.
2. **Depreciate the remaining book value over the remaining revised life.** New annual depreciation = (net book value at the start of the change period − revised salvage) ÷ **remaining** revised useful life.
   - Remaining revised life = revised total life − years already elapsed. Example: a 7-year revised life with 1 year already elapsed depreciates the remaining NBV over **6** remaining years — not over 7 years from original cost.
3. **Carry the correct beginning balances.** Beginning accumulated depreciation and beginning NBV must equal the originally reported figures (computed on the original basis), so the schedule ties to the prior period.
4. **State the treatment explicitly in the deliverable.** Add a note that (a) identifies the change as a **change in accounting estimate**, and (b) states that **prior-period depreciation is not restated** and the change is applied prospectively over the remaining life.

Contrast: a **change in accounting principle** (e.g., switching depreciation *methods* where required) or the correction of an **error** may require retrospective treatment. A plain useful-life or salvage revision does not — keep it prospective.

## Balance Sheet Reference Format

```
ASSETS
Current Assets
  Cash and cash equivalents
  Short-term investments
  Accounts receivable, net
  Inventory
  Prepaid expenses and other current assets
Total Current Assets

Non-Current Assets
  Property and equipment, net
  Operating lease right-of-use assets
  Goodwill
  Intangible assets, net
  Long-term investments
  Other non-current assets
Total Non-Current Assets

TOTAL ASSETS

LIABILITIES AND STOCKHOLDERS' EQUITY
Current Liabilities
  Accounts payable
  Accrued liabilities
  Deferred revenue, current portion
  Current portion of long-term debt
  Operating lease liabilities, current portion
  Other current liabilities
Total Current Liabilities

Non-Current Liabilities
  Long-term debt
  Deferred revenue, non-current
  Operating lease liabilities, non-current
  Other non-current liabilities
Total Non-Current Liabilities

Total Liabilities

Stockholders' Equity
  Common stock
  Additional paid-in capital
  Retained earnings (accumulated deficit)
  Accumulated other comprehensive income (loss)
  Treasury stock
Total Stockholders' Equity

TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY
```

## Cash Flow Statement Reference Format (Indirect Method)

```
CASH FLOWS FROM OPERATING ACTIVITIES
Net income (loss)
Adjustments to reconcile net income to net cash from operations:
  Depreciation and amortization
  Stock-based compensation
  Amortization of debt issuance costs
  Deferred income taxes
  Loss (gain) on disposal of assets
  Impairment charges
  Other non-cash items
Changes in operating assets and liabilities:
  Accounts receivable
  Inventory
  Prepaid expenses and other assets
  Accounts payable
  Accrued liabilities
  Deferred revenue
  Other liabilities
Net Cash Provided by (Used in) Operating Activities

CASH FLOWS FROM INVESTING ACTIVITIES
  Purchases of property and equipment
  Purchases of investments
  Proceeds from sale/maturity of investments
  Acquisitions, net of cash acquired
  Other investing activities
Net Cash Provided by (Used in) Investing Activities

CASH FLOWS FROM FINANCING ACTIVITIES
  Proceeds from issuance of debt
  Repayment of debt
  Proceeds from issuance of common stock
  Repurchases of common stock
  Dividends paid
  Payment of debt issuance costs
  Other financing activities
Net Cash Provided by (Used in) Financing Activities

Effect of exchange rate changes on cash

Net Increase (Decrease) in Cash and Cash Equivalents
Cash and cash equivalents, beginning of period
Cash and cash equivalents, end of period
```

## Common Adjustments and Reclassifications

### Period-End Adjustments

1. **Accruals:** Record expenses incurred but not yet paid (AP accruals, payroll accruals, interest accruals)
2. **Deferrals:** Adjust prepaid expenses, deferred revenue, and deferred costs for the period
3. **Depreciation and amortization:** Book periodic depreciation/amortization from fixed asset and intangible schedules
4. **Bad debt provision:** Adjust allowance for credit losses based on aging analysis and historical loss rates
5. **Inventory adjustments:** Record write-downs for obsolete, slow-moving, or impaired inventory
6. **FX revaluation:** Revalue foreign-currency-denominated monetary assets and liabilities at period-end rates
7. **Tax provision:** Record current and deferred income tax expense
8. **Fair value adjustments:** Mark-to-market investments, derivatives, and other fair-value items

### Reclassifications

1. **Current/non-current reclassification:** Reclassify long-term debt maturing within 12 months to current
2. **Contra account netting:** Net allowances against gross receivables, accumulated depreciation against gross assets
3. **Intercompany elimination:** Eliminate intercompany balances and transactions in consolidation
4. **Discontinued operations:** Reclassify results of discontinued operations to a separate line item
5. **Equity method adjustments:** Record share of investee income/loss for equity method investments
6. **Segment reclassifications:** Ensure transactions are properly classified by operating segment
