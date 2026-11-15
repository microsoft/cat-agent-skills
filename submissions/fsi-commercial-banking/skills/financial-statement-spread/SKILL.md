---
name: financial-statement-spread
description: |
  Build a standalone historical borrower-credit spread with assurance/basis, extraction checks, visible normalization, and live ratios in Input, Normalized, and Ratios tabs. Use when the user says "spread this borrower's statements", "build a credit spread from this tax return", "normalize these borrower financials", "show this borrower's historical coverage", or "use our credit-spread template". Do NOT use for integrated-model population or forecast links — use Finance 3-statements if available instead. Do NOT use for agreement-led tests — use covenant-compliance-check instead. Do NOT use for annual packets — use credit-annual-review-packet instead. Do NOT use for memo narrative — use credit-memo-narrative instead. Do NOT use for workbook formatting — use xlsx instead.
license: MIT
metadata:
  plugin: fsi-commercial-banking
  persona: credit analyst, underwriter, portfolio manager
---

# Financial Statement Spread

Turn borrower financial statements into a standardized spread an analyst can audit cell by cell.

## Scope

**Business-workflow boundary:** a standalone historical borrower-credit spread, not an integrated financial model. Source-document assurance, accounting basis, extraction verification, normalization decisions, and credit ratios are mandatory. A user template may replace the credit-spread layout but cannot turn this into historical population of an integrated income-statement/balance-sheet/cash-flow model, forecast linking, or model completion.

**Do:** extract as-reported figures, verify them arithmetically, normalize to a consistent schema, compute ratios, and show every formula and source.

**Do not:** assign a risk rating, characterise creditworthiness, judge covenant headroom, project forward, or originate an add-back the borrower did not claim. See the credit-decision gate in `references/house-rules.md`.

The spread is an input to analysis. The analyst owns the conclusions.

## When NOT to Use

- **Populating or completing an integrated three-statement model, including just its historical block** — Finance `3-statements` if available. Follow `references/house-rules.md`; do not build that model because Finance is unavailable.
- **Testing figures against a credit agreement** — use `covenant-compliance-check` instead.
- **Writing the memo narrative** — use `credit-memo-narrative` instead.
- **Formatting, charting, or restyling an existing workbook** — use `xlsx` instead.

## Quick Start

For "spread this borrower's statements", inventory basis/assurance and units, extract as printed, run supported verification checks, then normalize and compute only supported ratios; never plug an imbalance.

## Tool routing

1. Check actual connector availability; use `GetPluginConfig` when an expected plugin capability is missing. Do not assume a named vendor or optional Finance skill is connected.
2. For Microsoft 365 record sets use `ExecuteSql`; for topic/content discovery use `SearchM365`. Read located files with `ReadFileContent` (`full` for supported document text; `download` for exact bytes or spreadsheets). Scope reads to the borrower, purpose, and permissions.
3. Use available configured connector tools for their documented fields. If none supply an item, follow the existing source order and retain the correct gap marker; never claim a tool ran when it did not.
4. Delegate file construction to `xlsx`, `docx`, or `pptx` as specified below. Inline output is an inline draft, not a saved file. Report a save only from the action tool's successful result.

## Output format

Three-tab workbook specification or workbook, as requested: Input (as printed, provenance, assurance/basis), Normalized (visible mapping notes), and Ratios (live formulas and source-linked inputs). Include verification results and the existing footer; missing or invalid inputs remain markers.

## Workflow

### 1. Inventory what was supplied

Confirm that the requested output is a historical borrower-credit spread. If the supplied workbook is an integrated model with forecast/linkage schedules, do not populate it under this skill. A request for a separate credit spread may proceed independently; identify the separate deliverable and do not alter the model.

Before extracting anything, list each document and record:

- **Document type** — audited/reviewed/compiled statements, management-prepared, tax return, interim, schedule.
- **Assurance level and preparer** — see the source-tier table in `references/house-rules.md`. Note any qualification, going-concern paragraph, or scope limitation in a CPA report.
- **Accounting basis** — GAAP, tax, cash, or other.
- **Periods covered**, with period end and length.
- **Units scale** — read it from the statement header and record it.

If the user asked for three years and supplied two, say so now rather than producing a short spread without comment. If documents disagree about the same period, say which you used and why; never silently prefer one.

### 2. Extract as reported

Read `references/document-extraction.md` before extracting — it covers route selection, the scale/sign/column traps, and per-figure legibility handling.

Capture every line as printed, with its caption, into the input tab. Do not normalize, reclassify, or round at this stage. A figure you could not read is `NOT LEGIBLE`, never a guess and never an inference from a subtotal.

### 3. Verify before using anything

Run the verification gate in `references/document-extraction.md`: balance sheet balances, subtotals sum, comparatives agree, cash ties, equity rolls forward. Record which checks ran and which the supplied documents could not support.

On a failure, re-read the lines involved first — most failures are extraction errors. If the figures are confirmed as printed, the source statement does not tie: report the check, both sides, and the difference. **Never plug, balance, or adjust a statement to make it tie.**

A failed check suppresses only the cells that depend on the affected figures, for the affected period only.

### 4. Normalize

Map as-reported captions onto the spread schema. **Every mapping is a visible decision**, recorded next to the line — a normalization note naming the source caption. Where a caption spans two schema lines, or the borrower's presentation has no schema equivalent, say so rather than forcing it.

Keep normalization separate from adjustment. Reclassifying a caption is normalization. Adding back owner compensation is an adjustment and needs an evidenced source, an amount, and an asserter.

### 5. Compute ratios

Standard set: leverage, coverage, liquidity, margins, working capital, and trend. Show the formula and both inputs on every ratio.

- Zero or negative denominator → `N/M`. Never a multiple on nonpositive EBITDA or nonpositive debt service.
- Preserve meaningful negatives — net cash, negative working capital, accumulated deficit.
- A ratio with a marker among its inputs is itself a marker, never zero.
- Where the credit agreement defines a term, compute it as defined and cite the section. A generic definition is not a substitute.
- Peer comparatives require a source that supplies them. With none configured, mark them `NEEDS FEED — peer benchmark source (e.g. RMA, Moody's, S&P)`; the borrower's own trend stands on its own.

### 6. Resolve the template

1. User named a template file → use it.
2. Else search M365 for `Cowork Templates/Commercial Banking/financial-statement-spread/` → most recent file there.
3. Else use `references/spread-outline.md`.

A house schema replaces the account list, ratio set, and add-back treatment without changing this workflow. State which template you used.
It cannot add forecast schedules or an integrated model's historical block; those are excluded business jobs, not template variations.

### 7. Produce the spread

Default spreadsheet output is delegated to the built-in `xlsx`: the skill supplies the workbook structure, live formulas as specified, source evidence, markers, and placeholders; `xlsx` builds the file. Missing values are blanks or markers, never `0`.

Default `.xlsx`, three tabs:

- **Input** — as reported, by period, with caption, page reference, and document.
- **Normalized** — schema lines, each carrying a note naming its source caption.
- **Ratios** — formula-driven, referencing the normalized tab.

**Write live formulas, not pasted values**, wherever a cell is computed. An analyst must be able to click a ratio and see its inputs. Carry the units scale in the tab header and state the basis and assurance level on every period column.

## Source resolution

Ordering follows `references/house-rules.md`. This section names what each source supplies here.

1. **Configured connector.** Check what is actually available this session.
   - Document extraction / IDP (`Ocrolus`, `Hyperscience`) → extraction with per-field confidence.
   - Peer benchmarks (`RMA`, `Moody's Analytics`, `S&P Capital IQ`) → industry comparative columns.
   - LOS / core (`nCino`, servicing, GL) → existing spreads, facility detail, actuals for the tested period.
2. **Supplied documents and M365** — statements, tax returns, schedules, prior spreads. Classify each by authorship and assurance, not by the fact that it arrived as an attachment.
3. **Public primary** — for a public filer, EDGAR figures are a public record and are never interchangeable with borrower-supplied statements in the same column. Say which you used.
4. **Secondary** — marked `UNVERIFIED — secondary source`, and never a source for a spread figure.
5. **Flag the gap** with the right marker.

**If a configured connector supplies the item in front of you, use it and do not open the browser
for that item.** Browsing is for items no connector covers — narrative and covenant language, as-reported figures where the accounting basis matters, and anything whose citation needs a primary identifier. A connector being
present does not mean it holds the item: if it returns nothing, that is a connector miss, so
continue down this list. Never treat it as a dead end, and never report it as the item not
existing.

**A partial or stale connector answer is a miss for whatever it does not cover.** Where the item
is a count, an "all of X" set, an absence claim, or a point-in-time status, a non-empty connector
answer does not end the search — confirm completeness and currency against the authoritative
source, or mark that coverage `partial` and name what was not covered. A vendor's subset reported
as the whole manufactures a finding that was never established, and a connector never settles a
determination or a point-in-time status on its own.

**Capabilities.** Reading supplied files (PDF, DOCX, XLSX, PPTX, CSV, images with OCR); web retrieval of public sources; Microsoft 365 search where the user has access; configured MCP connectors where present. Artifact creation is delegated — spreadsheets to `xlsx`, documents to `docx`, decks to `pptx`.

**When a capability is unavailable:** say which one, name what it would have supplied, and continue with what is available. Never silently skip a step and never present an unavailable source as returning nothing.

**Source markers.** Distinguish `NEEDS FEED` (no source exists in this session), `NOT RETRIEVED` (source exists, but retrieval failed or was denied), and `NOT FOUND` (source answered, with no record). Never collapse them.

**Artifact handoff.** The skill supplies the content, structure, formulas as specified, evidence, and placeholders; the built-in creates the file. Spreads and covenant workbooks go to `xlsx`; memos, credit write-ups, briefs, packets, and call memos go to `docx`.

## Guardrails
- **Historical credit-spread boundary.** Never populate an integrated three-statement model or its historical block, link forecasts, or create a model-completion deliverable.
- **Nothing auto-sends.** No email, submission, posting to a system of record, file submission, or commitment to a borrower is sent or made automatically. A draft is a draft and is reported as a draft.
- **Never delete decision sections.** Existing approvals, conditions, exceptions, risk ratings, and prior decision rationale are preserved. Updates append and mark changes; they never overwrite or remove.
- **Unreadable statements stop calculations.** If a financial statement figure cannot be read with confidence, output `NOT LEGIBLE — <document>, page <n>, <line item>`, ask for a cleaner copy, never guess a digit, never infer a number from a subtotal, and never carry a partially read figure into a calculation. If extraction quality is poor across a statement, say so and stop rather than producing a spread or covenant test built on guesses.
- **Unavailable sources stay distinct.** Use `NEEDS FEED` when no source exists in this session, `NOT RETRIEVED` when a source exists but retrieval failed or was denied, and `NOT FOUND` when the source answered with no record. Never collapse them.
- **Failed saves are failures.** Never claim a save succeeded unless it was verified. Report what was produced, where it was and was not written, and what remains incomplete.
- **Missing values are never zero.** In spreadsheets, covenant worksheets, memos, and packet tables, write a blank or the applicable marker; never write `0` for missing, unreadable, unretrieved, or unavailable values.
- **Every cell traceable.** Document, statement, period, page, and the caption as printed.
- **Never supply a figure that was not read.** `NOT LEGIBLE` for an unreadable figure, even where its value could be inferred arithmetically. A derivation may be shown separately and labelled, never in place of the as-printed figure.
- **Verify before use.** No figure reaches the normalized or ratio tabs until the gate has run and its result is recorded.
- **One basis per column.** Never pool inputs from different statements or scopes to synthesise a metric. Where alignment cannot be evidenced, output `NOT COMPARABLE — RECONCILIATION REQUIRED`.
- **Exclusion is per metric.** A failed or unreadable input suppresses its dependent cells for that period only. The borrower stays in the spread and every other metric it qualifies for is retained.
- **Add-backs need evidence and an asserter.** Never originate one; never carry one across periods.
- **No rating, no decision, no characterisation.** State figures, thresholds, and sources.

## Output footer

End every spread with:

```
Workflow: standalone historical borrower-credit spread — no integrated model
Documents used: <count> — <each: name, type, assurance level, basis, periods, pages read>
Extraction route: <connector name | direct read | page-image read>
Verification: <checks run and result; checks not run and why>
Retrieval coverage: <complete | partial — name what was partial>
Template: <bundled default | house template name>
Artifact handoff: <xlsx | docx | pptx | none — inline only>
Connectors used: <names, or "none">
Other sources used: <supplied documents | M365 | public primary | secondary, marked>
Output: inline draft | file created <identifier> | creation failed
Persistence: not attempted | saved <verified location> | failed
Save detail: <what was produced; where written; where not written; incomplete items>
Gaps: <NOT LEGIBLE / NOT FOUND / NOT RETRIEVED / NEEDS FEED / GAP items, or "none">
Generated: <date> — as-reported figures with derived metrics shown with their components.
No risk rating, credit decision, or creditworthiness assessment.
```

**Every field states what actually happened.** Do not report checks as run when the inputs did not support them. Do not describe management-prepared statements as audited. Do not name a saved location that was not verified.

## Reference files

- `references/document-extraction.md` — routes, quality handling, the verification gate, periods, derived figures, add-backs, ratio rules. Read before extracting.
- `references/house-rules.md` — citation format, source tiers, accounting basis, credit-decision gate, markers.
- `references/spread-outline.md` — default tab structure, account schema, and ratio set.
