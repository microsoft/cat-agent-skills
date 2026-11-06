# Financial Reporting Standards

> Reference file of the `financial-presentations` skill. Read it before you build a finance deck: the deck's figures follow its reporting conventions, and step 3 is the checklist for any workbook behind the deck.

The build contract for financial-reporting deliverables. The `financial-presentations` workflow (its `SKILL.md`) supplies the presentation method; this reference governs what must exist in the finished file, what must not be added to it, and how to verify it before returning it.

> **Important**: This skill assists with finance and accounting workflows but does not provide financial, tax, or audit advice. All outputs should be reviewed by qualified financial professionals before use in financial reporting, regulatory filings, or audit documentation.

These are checks on your own work, not a template to copy. The general build rules — the implementation-skill gate, structure lock, scope and structure fidelity, output formats — live in the `accounting-root-skill` skill and apply here too. For a workbook, load the `xlsx` skill first and use it to build and validate the file; this reference adds what is specific to reporting deliverables.

## 1. List the named deliverables before you build anything

Write down every artifact the request names — each tab or worksheet, each column, each statement, each reconciliation or roll-forward. Phrases like "a separate trial balance tab for each of the four entities", "a Consolidated tab and an Eliminations tab", "a commentary column for each KPI", or "trend graphs for EBITDA, Operating Income, Free Cash Flow and CapEx" are each a *separate* required artifact. Build every one.

- The largest source of lost credit is not wrong numbers — it is a named artifact that was never created. A tab you did not build scores zero however good the rest of the workbook is.
- A combined tab is not four entity tabs. A commentary *sheet* is not a commentary *column*. One chart carrying one series is not four trend graphs.
- If a named deliverable genuinely cannot be built from the source data, still create it and state in a visible cell why it is empty, rather than silently omitting it. Open that cell with `NOT AVAILABLE:` and then the reason — for example `NOT AVAILABLE: the source trial balance carries no intercompany detail, so eliminations cannot be derived.` The verification in step 3 recognises that sentence and accepts the tab; a bare instruction such as "Enter elimination amounts below" is not a reason and will be reported as a blank template.

**When a deliverable has more than one dimension, enumerate the grid, not the sentence.** Reporting requirements are routinely dimensional — *entities × statements*, *metrics × charts*, *periods × columns*, *accounts × reconciliations*. Writing the sentence down once and building one artifact scores zero on every cell you did not build.

| requirement as worded | dimensions | cells you must build |
|---|---|---|
| "a separate trial balance tab for each of the four entities" | entity (4) | `TB Entity A`, `TB Entity B`, `TB Entity C`, `TB Entity D` — four tabs |
| "a Consolidated tab and an Eliminations tab" | tab (2) | `Consolidated`, `Eliminations` — two tabs, both required |
| "trend graphs for EBITDA, Operating Income, Free Cash Flow and CapEx" | metric (4) | four charted series — charting EBITDA alone scores zero on the other three |
| "MTD and YTD variance for each account line" | period (2) × line (n) | both period columns on every line |

Count the cells. If the grid has twelve cells, twelve things must exist in the finished workbook. Step 3 checks every cell that is a *tab*, so a missing one is caught before you deliver rather than by the reviewer. Check the cells that are columns, charts or statements against the finished workbook the same way before returning it.

**Build the grid, and stop there.** The completeness rule is a floor, not an invitation. Two failure modes cost real credit and both come from doing *more* than was asked:

- **Scope.** If the task says "a single one-page report", "one tab", or "suitable for email", that shape is itself a graded requirement. Adding a conventions block, an assumptions tab, or a methodology sheet to a deliverable specified as one page makes it score *worse*. Add a tab only if a grid cell names it.
- **Fidelity.** Data given in the prompt or an attachment must appear **exactly as provided** — same values, labels, account captions, signs. Do not re-scale, re-round, re-caption, re-order or "correct" a supplied figure. If one looks wrong, reproduce it unchanged and note the concern in a separate cell. A restated input reads as an error even when the restatement is defensible.

When in doubt: everything the task named, exactly as the task named it, and nothing else.

## 2. Link derived figures with live formulas — never hand-type a computed number

Any cell computed from, or tracing to, other data — especially summary, dashboard, or KPI cells — must be a live reference or formula pointed at the source (`=Detail!D12`, `=SUM(...)`, `='Source - Actual FS'!C7`), not a retyped constant. You cannot see the values your formulas resolve to, so a hand-typed number can silently drift from its source.

**Two formula rules:**

- **Write modern functions plainly.** Type `XLOOKUP`, `IFS`, `TEXTJOIN`, `LET` and the like without the `_xlfn.` prefix: Cowork's workbook tools store the prefixed form Excel needs.
- **Arithmetic against a text cell yields `#VALUE!`.** `=B7/12` breaks when `B7` holds `"n/a"` rather than a number, and every cell depending on it breaks with it. Aggregations are not the risk: `SUM` and `SUMIFS` skip text inside their ranges. It is *direct* cell-to-cell arithmetic that fails, so confirm both operands are numeric before dividing or subtracting.

## 3. Verify the workbook (MANDATORY for any workbook you create or edit)

You cannot see the values your own formulas resolve to while you write them, so check the finished workbook before you return it. Read it back the way the `xlsx` skill describes (in Cowork, the live workbook's model: its sheet list, and each sheet's formulas and calculated values) and work through every check below:

1. **Every named tab exists and holds data.** Compare the sheet list with the tabs on your step 1 list. Match names loosely, ignoring case, spaces and punctuation (`Trial Balance`, `Trial_Balance` and `TrialBalance` are the same tab), but give each required tab its own sheet: `Entity 1` is not satisfied by a sheet called `Entity 10`. A required tab that exists but holds no data counts as missing.
2. **No blank templates.** A sheet with headers or labels but no numbers and no formulas has not been built. Build it, or open a visible cell with `NOT AVAILABLE:` and the reason, as step 1 describes. A bare instruction such as "Enter elimination amounts below" is not a reason.
3. **No half-filled value columns.** A column that carries numbers or formulas for most of its labeled rows but is blank for a real share of them is missing actuals or inputs. Memo and support tabs can be legitimately partial; leave those alone.
4. **No formula errors.** No calculated value may be an Excel error: `#REF!`, `#VALUE!`, `#DIV/0!`, `#N/A`, `#NAME?`, `#NUM!`, `#NULL!`, `#SPILL!` or `#CALC!`. Fix the cause; do not hide it with `IFERROR`.
5. **Typed totals foot.** A Total or Subtotal row holding a typed number must equal the sum of the data rows directly above it. Roll-forward balances and ratio rows are not sums, so they are exempt. Formula totals foot on their own, so this check is for typed totals only.

**This is a loop, not a single pass.** Fix what fails in the workbook itself, read it back again, and repeat until every check passes: any edit can break a check that passed before. A sheet whose values the read-back could not return in full is not verified. If you cannot get every check to pass, say so in your reply and name what still fails rather than delivering silently.

## Worked pattern — building a financial statement from a trial balance

When a task asks for statements (Balance Sheet, Income Statement, Cash Flow, or a consolidation) built from a trial balance or supporting schedules:

**1. One row per real caption, linked by formula.** Each statement line pulls its number from the source tab with `SUMIFS` keyed on the mapping — never a typed constant:

```
# Balance Sheet tab, cell B7 (Cash), current year column
=SUMIFS('TB Detail'!$Balance, 'TB Detail'!$FS_Line, $A7, 'TB Detail'!$Year, B$4)
```

Only add a caption row if the trial balance actually has an account mapped to it. Do not paste a standard template of captions (e.g., "Interest income", "Deferred tax assets") that this entity has no account for — an empty $0 caption reads as a defect.

**2. Subtotals and totals are `SUM` of the rows above, not retyped:**

```
Total current assets   =SUM(B7:B10)
TOTAL ASSETS           =B_TotalCurrentAssets + B_TotalNonCurrentAssets
```

**3. Make the balance sheet BALANCE, and prove it.** Add an explicit check row; it must evaluate to 0:

```
Balance check (must = 0)   =TOTAL_ASSETS - (TOTAL_LIABILITIES + TOTAL_EQUITY)
```

If it is not zero, a caption is mis-mapped or missing — fix the mapping. Never force it to zero with a plug.

**4. Cash flow (ASC 230) is three sections that foot to the cash change:**

```
Net cash from Operating   =SUM(operating lines)
Net cash from Investing   =SUM(investing lines)
Net cash from Financing   =SUM(financing lines)
Net change in cash        =Operating + Investing + Financing
Check (must = 0)          =Net change in cash - (Ending cash - Beginning cash from Balance Sheet)
```

**5. Consolidation:** one trial-balance tab per entity, a `Consolidated` tab that sums the entities, and an `Eliminations` tab. Eliminate intercompany balances only to the extent the receivable and payable sides match; if a residual remains, show it with its dollar amount rather than plugging it to zero.

Build exactly the tabs the task names, then run the verify step above.

## Worked pattern — variance analysis (budget vs actual, review packages)

**1. Present every provided line — never summarize the data away.** One row per account/line item exactly as supplied, with no added and no omitted lines. Adding subtotal/total rows is fine; replacing detail with a "key drivers" subset or total-only rollup is a defect. Keep the account hierarchy (indent children under parents). If a metric is provided (MLR %, membership, headcount, a named ratio), analyze it for **every period requested** (e.g., both MTD **and** YTD). **Materiality never removes lines from the schedule** — it only decides which variances get a written narrative.

**2. Variance columns are formulas, with F/(U) and color.** Compute `$ Var = Actual - Budget` and `% Var` by formula per line. Label each Favorable/Unfavorable **by account type** (for revenue a positive variance is F; for expense a positive variance is U) and apply visible cell color (green = favorable, red = unfavorable) — a text label alone does not satisfy a color-coding requirement.

**3. Write a real narrative for every material variance.** For each variance above threshold:
- **Specific & causal** — names the actual driver and explains WHY, not "higher than expected."
- **Quantified** — dollar and % impact of each contributing driver.
- **Forward-looking & actionable** — one-time vs continuing, and any follow-up (monitor / investigate / update forecast).

Avoid circular ("revenue up due to higher revenue"), vague ("expenses elevated"), or bare-"timing" narratives. 2–4 sentences per material line. A schedule of numbers with no interpretation for material movements is an incomplete deliverable.

## Reporting conventions (apply the ones that fit — do not pad)

Close the workbook out with the presentation conventions that match the deliverable's shape. **Only add what applies; never add a tab, column, or convention line the task does not call for.**

- **Workbooks whose shape the request left open** — add a short **Assumptions & Conventions** area (a titled block on an existing summary/read-me tab, not a whole extra tab) documenting only the conventions the workbook actually uses:
  - **Sign/display** for unfavorable variances — parentheses, red fill, or a signed `F/(U)` label; state which.
  - **Rounding / units** — e.g. "whole dollars, no scaling" or "$ in thousands".
  - **Zero-budget / zero-denominator %** — show `N/A` or `n/m`, never `#DIV/0!`.
  - **Zero-variance ($0)** — e.g. label "On Budget" rather than leaving blank.
  - **Snapshot vs. refreshable** — one line stating which this is.

  **Constrained shapes are exempt.** If the request says "one tab", "a single one-page report", "suitable for email", "do not add anything", or supplies a fixed template with no room for this block, do **not** add it — the scope rule in step 1 wins.
- **Statement / trial-balance / audit workbooks** — when two periods are provided, show **both period columns side-by-side** on each statement; if the source supplies an owner/preparer/reviewer per account, **populate that column for every account line**.
- **Variance / review packages** — apply the sign convention above and populate owners if provided; do **not** force a comparative-period layout or extra tabs onto a single-tab snapshot.
- **When required inputs are missing** — request them and defer, rather than inventing values or leaving materially-flagged rows blank.
