---
name: credit-annual-review-packet
description: |
  Assemble a periodic credit-monitoring packet with no live transaction: prior/current financial comparison, covenant status, exceptions, public-record refresh, and factual changes. Leave rating and conclusion to the analyst. Use when the user says "put together the annual review", "build the credit monitoring review", "what changed on this credit since last year", "assemble the portfolio review packet", or "this borrower's annual is due". Do NOT use for new-money or renewal memos — use credit-memo-narrative instead. Do NOT use for standalone covenant tests — use covenant-compliance-check instead. Do NOT use for company background alone — use borrower-prospect-research instead. Do NOT use for document formatting — use docx instead.
license: MIT
metadata:
  plugin: fsi-commercial-banking
  persona: portfolio manager, credit analyst, credit officer
---

# Credit Annual Review Packet

Assemble what changed since the last review, with the limits of the comparison stated.

## Scope

**Do:** compare prior and current state, summarise covenant results, list open exceptions, refresh the public record, and narrate changes as facts.

**Do not:** re-rate the credit, conclude the review, clear an exception, characterise performance or trend quality, or recommend an action. See the credit-decision gate in `references/house-rules.md`.

Annual review is deliberately narrower than underwriting. It reports movement; the analyst judges it.

## When NOT to Use

- **New-money or renewal write-up** — use `credit-memo-narrative` instead.
- **Testing covenants in isolation** — use `covenant-compliance-check` instead.
- **Formatting or restyling an existing document** — use `docx` instead.

## Quick Start

For "put together the annual review", establish both periods and prior-file coverage before comparing; partial prior coverage cannot establish that an item is new or resolved.

## Tool routing

1. Check actual connector availability; use `GetPluginConfig` when an expected plugin capability is missing. Do not assume a named vendor or optional Finance skill is connected.
2. For Microsoft 365 record sets use `ExecuteSql`; for topic/content discovery use `SearchM365`. Read located files with `ReadFileContent` (`full` for supported document text; `download` for exact bytes or spreadsheets). Scope reads to the borrower, purpose, and permissions.
3. Use available configured connector tools for their documented fields. If none supply an item, follow the existing source order and retain the correct gap marker; never claim a tool ran when it did not.
4. Delegate file construction to `xlsx`, `docx`, or `pptx` as specified below. Inline output is an inline draft, not a saved file. Report a save only from the action tool's successful result.

## Output format

Draft packet sections: scope/periods; prior coverage; current facts and supported comparisons; supplied covenant states unchanged; documented exceptions/actions; public-record search limits; unfilled rating/conclusion; the existing footer. Use the selected template and keep comparison limits in the body.

## Workflow

### 1. Establish scope and periods

Record: obligor legal name and identifier, facilities in scope, the prior review date and its source document, and the current review period. Say which periods are being compared and on what basis.

If the prior review file was not supplied, say so and ask for it by name. **Do not reconstruct a prior state from inference** — a comparison against a guessed baseline is worse than no comparison.

### 2. Assemble prior state — and record its coverage

From the prior review, prior memo, or prior spread. Capture what was true at the last review: financial figures, risk rating as recorded, covenants and their results, exceptions then open, collateral, and structure.

**Record coverage explicitly**: `complete` where the full prior file was read, `partial` where only some sections were reachable, naming which. This coverage value governs every comparison claim below.

### 3. Assemble current state

Current financials come from a supplied spread or supplied statements. Read `references/document-extraction.md` for extraction and verification rules, and run the verification gate before using any figure.

If no current financials were supplied, say so. Name `financial-statement-spread` as the skill that produces the spread, and **never describe its output as though it ran.**

### 4. Compare — the completeness gate is symmetric

A comparison claim is only as good as the coverage of **both** sides.

| Coverage of prior state | What you may claim |
|---|---|
| Complete | `added`, `removed`, `changed`, `unchanged` — all four |
| Partial | `currently present; novelty unverified` and `currently absent; prior presence unverified`. **Never** `added` or `removed` |
| Unavailable | Current state only. No comparison claims at all |

**This cuts both ways.** An unread prior section looks exactly like a new item — and equally, an item you did not see in a partially-read prior file may never have gone away. If partial coverage blocks "this covenant was added," it blocks "this exception was resolved" by the same logic.

State on the packet that the comparison is not exhaustive whenever coverage is partial.

### 5. Covenant status

Summarise covenant results for the review period. Where a compliance check has been run and supplied, restate its states and flags unchanged — carry `PASS`, `FAIL`, and `NOT TESTED` through exactly, and never convert a `NOT TESTED` into a pass by omission.

Where no check has been run, say so and name `covenant-compliance-check` as the skill that performs it. Do not test covenants here from a covenant summary, and do not describe that skill's output as though it ran.

### 6. Refresh the public record

Re-run the entity, lien, litigation, and news searches using `references/public-records.md`. Resolve identity first; report the index, jurisdiction, exact name searched, and date for every search, including clean results.

Compare against the prior review's findings under the same symmetric rule: a new filing is only "new" if the prior search covered the same index and jurisdiction.

### 7. Exceptions and action items

List every open exception with: what it is, when it arose, its source document, and its current status **as documented**. Carry forward prior exceptions that were not shown to be resolved — an exception is not closed because it was not mentioned.

Do not clear, waive, or close an exception. Where the current file suggests resolution, say what evidence exists and leave the status for the analyst.

### 8. Resolve the template and produce

1. User named a template file → use it.
2. Else search M365 for `Cowork Templates/Commercial Banking/credit-annual-review-packet/` → most recent file there.
3. Else use `references/review-outline.md`.

Default document output is delegated to the built-in `docx`: the skill supplies sourced content, checklist structure, evidence, and placeholders; `docx` builds the file. Missing values remain blank or marked, never `0`.

Default `.docx` packet plus an exceptions/action checklist. The rating and conclusion sections appear with headings intact and an explicit placeholder; never fill them.

## Source resolution

Ordering follows `references/house-rules.md`.

1. **Configured connector.** LOS / servicing (`nCino`) → exposure, payment history, ticklers, prior rating, covenant schedule. Core/GL → balances and actuals. Business credit (`D&B`, `Experian` commercial) → public-record and score refresh.
2. **Supplied documents and M365** — prior review, prior memo, current statements, spread, certificates, correspondence.
3. **Public primary** — registry, court index, EDGAR, company site.
4. **Secondary** — marked `UNVERIFIED — secondary source`.
5. **Flag the gap.**

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

With no LOS connector, exposure and payment history come from what the user supplied. Say so rather than implying a complete facility picture.

**Capabilities.** Reading supplied files (PDF, DOCX, XLSX, PPTX, CSV, images with OCR); web retrieval of public sources; Microsoft 365 search where the user has access; configured MCP connectors where present. Artifact creation is delegated — spreadsheets to `xlsx`, documents to `docx`, decks to `pptx`.

**When a capability is unavailable:** say which one, name what it would have supplied, and continue with what is available. Never silently skip a step and never present an unavailable source as returning nothing.

**Source markers.** Distinguish `NEEDS FEED` (no source exists in this session), `NOT RETRIEVED` (source exists, but retrieval failed or was denied), and `NOT FOUND` (source answered, with no record). Never collapse them.

**Artifact handoff.** The skill supplies the content, structure, formulas as specified, evidence, and placeholders; the built-in creates the file. Spreads and covenant workbooks go to `xlsx`; memos, credit write-ups, briefs, packets, and call memos go to `docx`.

## Guardrails
- **Nothing auto-sends.** No email, submission, posting to a system of record, file submission, or commitment to a borrower is sent or made automatically. A draft is a draft and is reported as a draft.
- **Never delete decision sections.** Existing approvals, conditions, exceptions, risk ratings, and prior decision rationale are preserved. Updates append and mark changes; they never overwrite or remove.
- **Unreadable statements stop calculations.** If a financial statement figure cannot be read with confidence, output `NOT LEGIBLE — <document>, page <n>, <line item>`, ask for a cleaner copy, never guess a digit, never infer a number from a subtotal, and never carry a partially read figure into a calculation. If extraction quality is poor across a statement, say so and stop rather than producing a spread or covenant test built on guesses.
- **Unavailable sources stay distinct.** Use `NEEDS FEED` when no source exists in this session, `NOT RETRIEVED` when a source exists but retrieval failed or was denied, and `NOT FOUND` when the source answered with no record. Never collapse them.
- **Failed saves are failures.** Never claim a save succeeded unless it was verified. Report what was produced, where it was and was not written, and what remains incomplete.
- **Missing values are never zero.** In spreadsheets, covenant worksheets, memos, and packet tables, write a blank or the applicable marker; never write `0` for missing, unreadable, unretrieved, or unavailable values.
- **Comparison claims require coverage on both sides.** Partial prior coverage permits only `currently present; novelty unverified` and `currently absent; prior presence unverified`.
- **Never reconstruct a prior baseline** from inference. Never invent a figure, source, prior status, or completion claim.
- **Carry states and markers through unchanged.** A `NOT TESTED` covenant stays `NOT TESTED`; a marked figure stays marked.
- **Never clear or close an exception.** Report evidence; leave status to the analyst.
- **Never re-rate or conclude the review.**
- **Never characterise trend quality.** State the movement and the arithmetic.
- **Never describe another skill's output as though it ran.**

## Output footer

```
Obligor: <exact legal name, jurisdiction, identifier>
Review period: <current period> compared with <prior review date and document>
Prior-state coverage: <complete | partial — name what was not read | unavailable>
Comparison basis: <full comparison | limited — novelty and removal unverified>
Current financials: <spread supplied | statements supplied | none — comparison not generated>
Verification: <checks run and result; checks not run and why>
Covenant status: <restated from supplied check | no check supplied — not tested here>
Searches run: <each: source, jurisdiction, exact name searched, date, result>
Exceptions: <open <n> | carried forward <n> | evidence of resolution <n>, status not changed>
Template: <bundled default | house template name>
Artifact handoff: <xlsx | docx | pptx | none — inline only>
Connectors used: <names, or "none">
Other sources used: <supplied documents | M365 | public primary | secondary, marked>
Sections left for completion: <rating | review conclusion | others>
Output: inline draft | file created <identifier> | creation failed
Persistence: not attempted | saved <verified location> | failed
Save detail: <what was produced; where written; where not written; incomplete items>
Gaps: <NOT LEGIBLE / NOT FOUND / NOT RETRIEVED / NEEDS FEED / GAP items, or "none">
Generated: <date> — assembled comparison and refresh. No risk rating, review conclusion,
exception clearance, or credit decision.
```

Every field states what actually happened. Do not report a full comparison when prior coverage was partial. Do not report covenant results as tested here when they were restated from a supplied check.

## Reference files

- `references/document-extraction.md` — extraction routes, verification gate, periods, derived figures.
- `references/public-records.md` — entity identity, what each source establishes, search limits.
- `references/house-rules.md` — citation format, source tiers, credit-decision gate, markers.
- `references/review-outline.md` — default packet structure, comparison table, exception list.
