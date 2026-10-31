---
name: "dcf-valuation"
description: >-
  Builds discounted cash flow valuation models as banker-readable Excel
  workbooks with live formulas, a WACC x terminal-growth sensitivity grid, a
  reverse-DCF, and an explicit readiness gate. Use when the user asks to "build
  a DCF", "what is this company worth on a DCF basis", "run the WACC and
  terminal value", "what is the intrinsic value per share", or "what is the
  market implying". Do NOT use for LBO sponsor returns (use lbo-model),
  completing an existing three-statement template (use 3-statements), peer
  trading multiples, or non-valuation spreadsheets (use xlsx).
metadata:
  icon: CalculatorMultiple
---

# DCF Valuation

Build a defensible discounted cash flow model as an Excel workbook, with calculation integrity
and decision readiness reported as two separate verdicts.

## When NOT to Use

- Comparable-company screens or precedent-transaction analysis with no DCF —
  outside this skill's scope.
- LBO sponsor returns — use `lbo-model`; filling an existing three-statement template —
  use `3-statements`. Merger/accretion-dilution analysis — outside this skill's scope.
- Internal budgets, forecasts, expense trackers, or any non-valuation spreadsheet → use `xlsx`
- Reviewing or fixing an existing deck → use `pptx`
- General finance questions with no model deliverable — answer inline

## Workflow

### 1. Preflight: source discovery (once per session, cache the result)

Check only the sources needed for this request, once per session. User-supplied
inputs come first; do not enumerate connections or call Power BI when they suffice.
For sources still needed, check what is reachable before assuming anything:

- `powerplatform-ListConnections` — is there a usable connection at all?
- `powerplatform-FindConnectors` — look only for what a DCF needs: a live Excel read
  (`shared_excelonlinebusiness`), and any market/financial data source.
- Note availability of Power BI (`pbi_fabricaihub-*`) and Dataverse for internal actuals.

There is normally **no market-data connector**. When none is reachable, fall back to
`host-web_search` and label every market input as web-sourced with the retrieval date. Never
present a web-sourced figure as if it came from a data feed.

### 2. Intake: new workbook or update in place

**If the user attached or named an existing workbook, ask once** with `core-AskUserQuestion`:
build a new dated workbook (reads theirs as input, leaves it untouched) or update theirs in
place (preserves their formatting and downstream links, but overwrites a live file). Never
guess — guessing "update" is destructive.

If nothing was attached, do not ask. Build fresh.

### 3. Gather inputs — source ladder, in this order

1. **Uploaded files** — check `input/` first, always. Read with `xlsx`/`pdf` handling.
2. **SharePoint / OneDrive** — `sharepoint_onedrive-SearchDrive` and `m365_search-SearchM365`
   for existing models, filings, and board materials. Use the Excel Online connector for a
   live cell-level read when the user wants their working model treated as the source.
3. **Power BI / Dataverse** — internal actuals where the company is the user's own or a
   portfolio company.
4. **Web search** — market data only (share price, risk-free rate, comps). Timestamp everything.

**Never fabricate a number.** A missing input becomes a clearly marked placeholder such as
`[Add FY25 EBITDA]`, and the placeholder count drives the readiness gate in step 6.

### 4. Build the workbook with xlsx

Invoke the `xlsx` skill, or delegate to `xlsx-agent`, to build the workbook directly. Tab order is
fixed — see [references/workbook-spec.md](references/workbook-spec.md). Methodology (FCFF build,
CAPM, both terminal-value methods, the bridge, the reverse-DCF) is in
[references/dcf-method.md](references/dcf-method.md).

- **Live formulas everywhere downstream of an input.** Every calculated cell references the
  Assumptions & Sources tab; never paste computed results.
- **Never substitute a default for a placeholder.** An unresolved input stays visibly marked
  (`[Add FY25 EBITDA]`), and every cell that depends on it shows as not computable rather than
  being filled with an assumed value to make the grid or the reverse-DCF compute.
- **The sensitivity grid recalculates live.** Each grid cell is its own formula over the FCF Build
  rows at that cell's WACC and terminal growth (for example, SUMPRODUCT of FCF and discount
  factors plus the discounted terminal value), so the centre cell equals the base case by
  construction.
- **The reverse-DCF is solved against the live model.** Implied terminal growth has a closed form
  and stays a live formula. For WACC or an operating assumption, solve iteratively against the
  recalculated model and label the result as a solved value with its date and the inputs used.
- Recalculate with the xlsx workflow's supported recalculation before reading any value, then
  deliver through the xlsx workflow.

### 5. Read the checks before describing anything

Run the check battery in the method reference against the recalculated workbook and record each
result on the Checks tab. **Never narrate success from the fact that the workbook was built.**
Report each check as PASS, FAIL, NOT RUN or NOT APPLICABLE with evidence. Missing evidence is
NOT RUN, never PASS; unresolved inputs, unsourced assumptions, future/stale dates or failed checks
force Screen-grade. A material failed check blocks the model.

### 6. Gate: two separate verdicts

The Summary tab carries two explicitly labeled fields that are allowed to disagree:

- **Calculation integrity** — tie-outs, formula-error scan, discounting consistency, bridge math.
- **Decision readiness** — evidence quality. Forced to **Screen-grade** whenever the placeholder
  count is above zero, a market input is stale, or terminal assumptions are unsupported.

A workbook whose formulas all pass is *not* "OK" while forecast, WACC, terminal value, bridge, or
share-count evidence remains open. Say so plainly.

### 7. Rating and reverse-DCF

Only for a resolved, positive-price, positive-equity case, calculate the fixed
threshold analytical label from the method reference, never a personalized trade
recommendation. If inputs or verification are unresolved, emit **No rating — not
verified** instead of an actionable Buy/Hold/Sell. Same verified numbers must
produce the same analytical label. When readiness is Screen-grade, render it as
**"Indicative — Screen-grade"** and name the unresolved inputs.

Whenever the rating is Buy or Sell, the reverse-DCF is **mandatory**: hold the framework constant
and solve for the operating assumption, WACC, or terminal growth that reconciles to the current
price. State it as "the market is implying X" rather than "the market is wrong." Proximity to a
downside or upside scenario is not a substitute for this test.

### 8. Companions

- **PowerPoint** — build automatically **only when the request names an audience** ("for the
  investment committee", "for the board", "I'm presenting this", "send to the client"). Otherwise
  build the workbook only and close with a one-line offer: "Want this as a committee deck?"
- **HTML** — only on explicit request.
- Every companion is generated **from the Checks tab and workbook outputs**, never from chat
  recollection, and carries the readiness stamp on its first slide or header.
- Render and visually inspect a companion before delivering it.

## Output Format

**Hero:** `model.xlsx`, opening on Summary.
**Companion:** `dcf_summary.pptx` when audience signal is present; HTML on request.

Chat response leads with the valuation range, the implied premium/discount to current price, the
two readiness verdicts, the top three value drivers, and open items — in that order. Cite headline
outputs to workbook tab and cell.

## Guardrails

- Never fabricate financials, share counts, prices, betas, or comps. Placeholder instead.
- Never overwrite a user's workbook without asking (step 2).
- Never send, email, or post the model or deck anywhere — deliver to `output/` only.
- Every market input carries a source label and retrieval date; flag any input past its staleness
  window on the Summary tab.
- Headline outputs (EV, equity value, per-share value, premium/discount, solved assumption) must
  trace to their upstream operating, WACC, terminal, bridge, share-count, and market inputs.
- Do not present a rating without the readiness verdict next to it.
- This is analytical support, not investment advice — state that on the Summary tab.
