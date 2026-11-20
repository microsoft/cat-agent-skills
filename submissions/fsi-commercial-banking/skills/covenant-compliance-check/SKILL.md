---
name: covenant-compliance-check
description: |
  Perform a standalone agreement-led covenant or borrowing-base review using amendments, defined terms, test dates, verified inputs, exclusive states, and independent flags. Use when the user says "check this agreement's covenants", "verify this compliance certificate", "show leverage-covenant headroom", "test the springing covenant", or "review the borrowing base". Do NOT use for integrated-model completion or its embedded covenant tab — use Finance 3-statements if available instead. Do NOT use for historical spreads — use financial-statement-spread instead. Do NOT use for memo narrative — use credit-memo-narrative instead. Do NOT use for workbook formatting — use xlsx instead.
license: MIT
metadata:
  plugin: fsi-commercial-banking
  persona: portfolio manager, loan operations, credit analyst
---

# Covenant & Borrowing-Base Check

Test borrower figures against the covenants as the credit agreement defines them, and show the work.

## Scope

**Business-workflow boundary:** a standalone facility/borrower monitoring worksheet led by the governing agreement and amendments, not completion of a covenant tab inside an integrated model. The agreement's definitions, applicability, verified inputs, exclusive states, independent flags, and borrowing-base eligibility rules remain mandatory. Model figures may be sourced inputs, not a reason to populate or repair the model.

**Do:** extract defined terms and thresholds, compute each test as defined, show inputs and arithmetic, cite the governing section, and flag what could not be tested.

**Do not:** declare an event of default, a breach, a waiver, a cure, or acceleration; characterise headroom as comfortable or tight; or recommend an action. A computed result is not a legal determination — that belongs to the banker and counsel. See the credit-decision gate in `references/house-rules.md`.

## When NOT to Use

- **Completing an integrated three-statement model or its embedded covenant schedule** — Finance `3-statements` if available. A separately requested agreement-led monitoring review may proceed as a distinct artifact, but do not populate the model. Follow `references/house-rules.md`.
- **Building the underlying financial spread** — use `financial-statement-spread` instead.
- **Drafting memo narrative** — use `credit-memo-narrative` instead.
- **Formatting, charting, or restyling an existing workbook** — use `xlsx` instead.

## Quick Start

For "verify this compliance certificate", identify the governing agreement and amendments first; compute its defined terms from verified inputs; retain every untestable covenant as NOT TESTED.

## Tool routing

1. Check actual connector availability; use `GetPluginConfig` when an expected plugin capability is missing. Do not assume a named vendor or optional Finance skill is connected.
2. For Microsoft 365 record sets use `ExecuteSql`; for topic/content discovery use `SearchM365`. Read located files with `ReadFileContent` (`full` for supported document text; `download` for exact bytes or spreadsheets). Scope reads to the borrower, purpose, and permissions.
3. Use available configured connector tools for their documented fields. If none supply an item, follow the existing source order and retain the correct gap marker; never claim a tool ran when it did not.
4. Delegate file construction to `xlsx`, `docx`, or `pptx` as specified below. Inline output is an inline draft, not a saved file. Report a save only from the action tool's successful result.

## Output format

One table row per covenant or collateral category, using the existing worksheet schema: cited definition and threshold, inputs and arithmetic, value, headroom, exactly one state, independent flags, and gaps. Include the existing footer and count states separately from flags.

## Workflow

### 1. Establish the governing document

Confirm that the user wants a separate agreement-led monitoring review. If the task is model completion, do not extract its covenant tab as a workaround to perform the excluded Finance job.

Covenant testing against a superseded agreement produces confident, wrong answers. Before extracting anything, record:

- **Agreement, date, and parties**, and whether the copy supplied is the execution version.
- **Amendments, waivers, and joinders** — ask explicitly whether any exist. If the user supplies only a base agreement and cannot confirm it is current, proceed but set the `amendment not confirmed` flag on every test.
- **Which facility and which borrower/guarantor group** the covenants attach to.

If the agreement was not supplied, say what you need by name. Do not test against a covenant summary, a term sheet, or a prior memo's description of the covenants — those are secondary and do not govern.

### 2. Extract the covenant set

For each covenant, capture as printed:

- The **defined term**, quoted, with its section reference.
- Every **component definition** it depends on — EBITDA, Funded Debt, Fixed Charges, Consolidated Net Income — since these are usually defined separately and carry carve-outs, add-backs, and caps.
- The **threshold**, including any step-down or step-up schedule and its effective dates.
- The **test date and frequency**, and whether testing is on a trailing or period basis.
- Any **equity cure, holiday, or springing** provision.

Show the extracted text alongside the section reference. An analyst must be able to check your reading against the document. Where a definition is ambiguous or incorporates a term you could not locate, set the `definition ambiguous` flag and quote what you found.

### 3. Assemble the tested inputs

Inputs come from the spread, a compliance certificate, or a borrowing-base certificate. Read `references/document-extraction.md` for extraction and verification rules.

For every input record: the value, its source document, its page, its accounting basis, and whether it is verified or borrower-reported. Where the agreement's defined term differs from the generic metric, **compute the defined term** — not the spread's standard ratio.

### 4. Test each covenant

Compute as defined, then assign exactly one state.

**States — mutually exclusive, in precedence order. First match wins.**

| # | State | When |
|---|---|---|
| 1 | `NOT TESTED` | A required input is missing, unreadable, unverified, or on an incompatible basis; the definition could not be extracted; the test date has not occurred; the computed value is undefined or not meaningful (`N/M` — a zero or negative denominator, for example), so there is no valid figure to compare with the threshold; or the covenant is springing or conditional and its applicability cannot be established from the evidence |
| 2 | `FAIL` | Computed value does not satisfy the threshold as stated |
| 3 | `PASS` | Computed value satisfies the threshold as stated |

`NOT TESTED` takes precedence over both others. Never report `PASS` on an assumed input, and never report `FAIL` on an input you could not verify — say it was not tested and name what is missing. Where a covenant is `NOT TESTED` because its computed value is `N/M` or its applicability is not established, headroom is not operative — report it as `unavailable`, never as `0`. A conditional arithmetic distance may be shown separately and labelled as such, never as covenant headroom.

**Flags — independent, and any number may apply to any state.**

| Flag | Meaning |
|---|---|
| `borrower-reported input` | A tested value came from a borrower certificate rather than verified statements |
| `definition ambiguous` | The defined term admits more than one reading |
| `period mismatch` | The tested period does not align with the agreement's test date or basis |
| `basis mismatch` | Inputs are on different accounting bases |
| `amendment not confirmed` | The governing document may have been amended |
| `curative item applied` | An equity cure, add-back, or carve-out was included — name it and its section |

**Flags are not states.** Count states and flags separately and say the counts are not additive — a single covenant can be `PASS` with three flags.

### 5. Produce the worksheet

Default spreadsheet output is delegated to the built-in `xlsx`; memo-form documents are delegated to `docx`. The skill supplies rows, formulas as specified, evidence, markers, and placeholders; the built-in builds the file. Missing values are blanks or markers, never `0`.

Default `.xlsx`; `.docx` if the user asks for a memo form. One row per covenant:

covenant · section · defined threshold · computed value · headroom · state · flags · every input with its source · the arithmetic

Headroom is the arithmetic distance to the threshold, stated as a number. Do not characterise it. Where the state is `NOT TESTED` because the value is `N/M` or the covenant's applicability is not established, headroom is `unavailable`, not a number.

For a borrowing base, the same structure applies per collateral category: eligible balance, ineligibles deducted with the criterion cited, advance rate, and availability — each with its source and section.

### 6. Resolve the template

1. User named a template file → use it.
2. Else search M365 for `Cowork Templates/Commercial Banking/covenant-compliance-check/` → most recent file there.
3. Else use `references/compliance-outline.md`.

State which template you used.

## Source resolution

Ordering follows `references/house-rules.md`.

1. **Configured connector.** Covenant tracking or LOS (`nCino`, servicing) → the covenant schedule, test dates, and prior results. Core/GL → actuals for the tested period. Always reconcile a connector's covenant schedule against the agreement text where both are available, and report any difference as a `GAP`.
2. **Supplied documents** — credit agreement and amendments, compliance certificate, borrowing-base certificate, spread.
3. **Public primary** — for a public filer, the agreement may be a filed exhibit. Cite form, period, and accession.
4. **Flag the gap.** Never test against a covenant you could not read.

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
- **Standalone loan monitoring only.** No integrated-model completion or embedded-model covenant schedule, even when a customer template requests it.
- **Nothing auto-sends.** No email, submission, posting to a system of record, file submission, or commitment to a borrower is sent or made automatically. A draft is a draft and is reported as a draft.
- **Never delete decision sections.** Existing approvals, conditions, exceptions, risk ratings, and prior decision rationale are preserved. Updates append and mark changes; they never overwrite or remove.
- **Unreadable statements stop calculations.** If a financial statement figure cannot be read with confidence, output `NOT LEGIBLE — <document>, page <n>, <line item>`, ask for a cleaner copy, never guess a digit, never infer a number from a subtotal, and never carry a partially read figure into a calculation. If extraction quality is poor across a statement, say so and stop rather than producing a spread or covenant test built on guesses.
- **Unavailable sources stay distinct.** Use `NEEDS FEED` when no source exists in this session, `NOT RETRIEVED` when a source exists but retrieval failed or was denied, and `NOT FOUND` when the source answered with no record. Never collapse them.
- **Failed saves are failures.** Never claim a save succeeded unless it was verified. Report what was produced, where it was and was not written, and what remains incomplete.
- **Missing values are never zero.** In spreadsheets, covenant worksheets, memos, and packet tables, write a blank or the applicable marker; never write `0` for missing, unreadable, unretrieved, or unavailable values.
- **The agreement governs.** Compute defined terms as defined, cite the section, and never substitute a generic market definition.
- **Never declare a default, breach, waiver, or cure.** Report the computed result against the cited threshold.
- **Never characterise headroom.** State the number.
- **One state per covenant, flags independent**, counted separately and non-additively.
- **`NOT TESTED` is not a pass.** An untested covenant is reported as untested, never omitted from the worksheet.
- **Show every input and its arithmetic**, with source, page, and whether it is verified or borrower-reported.
- **Markers never become numbers.** `N/M` for zero or negative denominators.

## Output footer

```
Workflow: standalone agreement-led loan monitoring — no integrated model
Governing document: <agreement, date, parties> — <execution version | copy, not confirmed>
Amendments: <listed and reviewed | none supplied — currency not confirmed>
Covenants in scope: <count> — PASS <n> · FAIL <n> · NOT TESTED <n>
Flags raised: <count by type — not additive with states>
Inputs: <verified from statements <n> | borrower-reported <n> | connector <n>>
Verification: <checks run and result; checks not run and why>
Template: <bundled default | house template name>
Artifact handoff: <xlsx | docx | pptx | none — inline only>
Connectors used: <names, or "none">
Other sources used: <supplied documents | M365 | public primary>
Output: inline draft | file created <identifier> | creation failed
Persistence: not attempted | saved <verified location> | failed
Save detail: <what was produced; where written; where not written; incomplete items>
Gaps: <NOT LEGIBLE / NOT FOUND / NOT RETRIEVED / NEEDS FEED / GAP items, or "none">
Generated: <date> — computed tests against cited agreement sections. Not a determination of
default, breach, waiver, or cure, and not a credit decision.
```

Every field states what actually happened. Do not report amendments as reviewed when none were supplied. Do not describe a borrower-reported input as verified.

## Reference files

- `references/document-extraction.md` — extraction routes, verification gate, periods, derived figures, covenant-defined-term precedence.
- `references/house-rules.md` — citation format, source tiers, accounting basis, credit-decision gate, markers.
- `references/compliance-outline.md` — default worksheet columns, state and flag legend, borrowing-base layout.
