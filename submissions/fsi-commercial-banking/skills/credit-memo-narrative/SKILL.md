---
name: credit-memo-narrative
description: |
  Draft sourced descriptive credit-memo sections for a new-money, increase, or renewal request; recap only supplied financials. Leave rating, recommendation, and conditions to the banker. Use when the user says "write up this credit request", "draft the memo narrative", "start the approval package", "write the business description for this deal", or "draft the industry section". Do NOT use for spreads — use financial-statement-spread instead. Do NOT use for periodic monitoring — use credit-annual-review-packet instead. Do NOT use for standalone covenant tests — use covenant-compliance-check instead. Do NOT use for company background alone — use borrower-prospect-research instead. Do NOT use for document formatting — use docx instead.
license: MIT
metadata:
  plugin: fsi-commercial-banking
  persona: credit analyst, underwriter, relationship manager
---

# Credit Memo Narrative

Draft the parts of a credit memo that describe, so the analyst spends their time on the parts that judge.

## Scope

**Do:** draft transaction, business, ownership, industry, collateral, and guarantor sections from sourced material, and recap financial trends as facts.

**Do not:** assign or recommend a risk rating, recommend approval or declination, propose structure, pricing, or conditions, characterise creditworthiness, or project forward. Those sections are left explicitly empty and labelled for the banker. See the credit-decision gate in `references/house-rules.md`.

## When NOT to Use

- **Building the financial spread** — use `financial-statement-spread` instead.
- **Periodic review with no live request** — use `credit-annual-review-packet` instead.
- **Formatting or restyling an existing document** — use `docx` instead.

- **General research outside a live credit request** — use deep-research instead, if available; company background alone stays with borrower-prospect-research. This does not exclude the sourced industry section of an in-scope credit memo.

## Quick Start

For "draft the memo narrative", quote the documented request, assemble only sourced descriptive sections, and retain decision headings for the banker. Without supplied financials, label the recap NOT GENERATED.

## Tool routing

1. Check actual connector availability; use `GetPluginConfig` when an expected plugin capability is missing. Do not assume a named vendor or optional Finance skill is connected.
2. For Microsoft 365 record sets use `ExecuteSql`; for topic/content discovery use `SearchM365`. Read located files with `ReadFileContent` (`full` for supported document text; `download` for exact bytes or spreadsheets). Scope reads to the borrower, purpose, and permissions.
3. Use available configured connector tools for their documented fields. If none supply an item, follow the existing source order and retain the correct gap marker; never claim a tool ran when it did not.
4. Delegate file construction to `xlsx`, `docx`, or `pptx` as specified below. Inline output is an inline draft, not a saved file. Report a save only from the action tool's successful result.

## Output format

Draft memo sections follow the selected template: documented request and sources/uses; sourced business/ownership/industry; supplied financial recap or NOT GENERATED with the missing input; documented collateral/guarantors; unfilled decision headings; the existing footer. Never invent figures or source citations.

## Workflow

### 1. Establish the request

Capture the transaction from the supplied deal material — term sheet, application, approval request, or the email thread. Record:

facility type · amount · purpose · tenor · structure · collateral offered · guarantors · pricing **as supplied, quoted, never proposed**

If the request is not documented in what you were given, ask. Do not infer an amount, a purpose, or a structure from context — a memo that misstates the request is worse than one with a gap.

### 2. Sources and uses

Only where the deal material supplies both sides. Show each line with its source. Where sources and uses do not balance, report the difference rather than plugging it. Where only one side was supplied, present that side and mark the other `NOT FOUND — not stated in supplied deal material`.

### 3. Business, ownership, and management

From the borrower's own materials, public records, and the company's site.

Use `references/public-records.md` for entity resolution and search limits. State the legal entity, jurisdiction, and identifier before describing the business. Where the memo concerns a group, say which entity is the obligor.

Ownership percentages come from a document that states them — an operating agreement, cap table, or filing. Never infer ownership from titles or surnames.

### 4. Industry overview

From public sources: trade press, association material, government statistics, and — where a public comparable exists — filed descriptions of the sector.

Attribute every claim with publisher and date. Where no connector supplies industry benchmarks, say so:
`NEEDS FEED — industry benchmark source (e.g. RMA, Moody's, S&P Capital IQ)`. Do not assemble a "typical" margin or leverage level from general knowledge and present it as a benchmark.

### 5. Financial recap — facts only

**The recap restates a spread; it does not create one.** Use figures from a spread or statements actually supplied in this session.

If no spread or statements were supplied, say so and ask for them. Name `financial-statement-spread` as the skill that produces the spread, and **never describe its output as though it ran** — do not write a trend recap from figures you do not have.

Where figures are available:

- Restate the trend as arithmetic — direction, amount, and percentage — with the period ends and the basis.
- Carry through every marker. A `NOT LEGIBLE`, `NOT FOUND`, or `NOT COMPARABLE` figure stays marked in the memo; it never becomes a number or a rounded approximation.
- Carry through assurance level and accounting basis on every period referenced.
- Describe movement, never quality. "Revenue increased 9.7% to $42,180K" — not "revenue grew strongly."

### 6. Collateral and guarantors

Describe what the deal documents state: collateral type, stated value with its source and date, lien position as documented, and guarantor identity and form of guaranty.

Where a stated value comes from the borrower or an undated appraisal, label it. Where lien position depends on a search you did not run, say so rather than asserting priority.

### 7. Resolve the template

1. User named a template file → use it.
2. Else search M365 for `Cowork Templates/Commercial Banking/credit-memo-narrative/` → most recent file there.
3. Else use `references/memo-outline.md`.

A house memo format replaces section order, headings, and required fields without changing this workflow. State which template you used.

### 8. Produce the draft

Default document output is delegated to the built-in `docx`: the skill supplies sourced content, section structure, evidence, and placeholders; `docx` builds the file. Missing values remain blank or marked, never `0`.

Default `.docx`. Decision sections appear in the document with their headings intact and an explicit placeholder:

```
[ RISK RATING — for analyst completion. Not generated. ]
[ RECOMMENDATION AND CONDITIONS — for banker completion. Not generated. ]
```

Never delete these sections and never fill them.

## Source resolution

Ordering follows `references/house-rules.md`.

1. **Configured connector.** LOS (`nCino`) → exposure, relationship, prior memos, facility detail. CRM (`Salesforce`, `DealCloud`) → relationship history and ownership. Company data (`S&P Capital IQ`, `Moody's`, `D&B`) → industry section, entity hierarchy, benchmarks.
2. **Supplied documents and M365** — term sheet, application, statements, spread, prior memo, org chart, appraisal, deal email thread.
3. **Public primary** — registry, EDGAR, regulator, company site.
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
- **Every claim sourced.** Anything unsourced is marked as a gap in the text, not quietly dropped and not asserted.
- **Never generate a decision or proposed terms.** Rating, recommendation, and conditions remain empty and labelled. Transaction pricing and structure may be quoted only as explicitly supplied, with attribution; never propose them or present them as approved.
- **Never characterise credit quality.** State the figure, the period, and the source.
- **Never describe another skill's output as though it ran.** If a spread was not supplied, say what is needed.
- **Markers carry through.** A marked figure stays marked in the narrative.
- **Quote the request; never propose it.** Pricing and structure appear only as supplied.
- **No protected characteristics** anywhere in the memo, even from a public source.

## Output footer

```
Obligor: <exact legal name, jurisdiction, identifier>
Request: <facility, amount, purpose, tenor — as supplied, source named>
Financial basis: <spread supplied | statements supplied | none — recap not generated>
Sources: <count> — <each with document/publisher and date>
Retrieval coverage: <complete | partial — name what was partial>
Template: <bundled default | house template name>
Artifact handoff: <xlsx | docx | pptx | none — inline only>
Connectors used: <names, or "none">
Other sources used: <supplied documents | M365 | public primary | secondary, marked>
Sections left for completion: <rating | recommendation | conditions | others>
Output: inline draft | file created <identifier> | creation failed
Persistence: not attempted | saved <verified location> | failed
Save detail: <what was produced; where written; where not written; incomplete items>
Gaps: <NOT LEGIBLE / NOT FOUND / NOT RETRIEVED / NEEDS FEED / GAP items, or "none">
Generated: <date> — descriptive sections only. No risk rating, recommendation, pricing,
structure, or credit decision.
```

Every field states what actually happened. Do not report a financial recap as generated when no figures were supplied. Do not list a connector that was not used.

## Reference files

- `references/public-records.md` — entity identity, what each public source establishes, search limits.
- `references/house-rules.md` — citation format, source tiers, accounting basis, credit-decision gate, markers.
- `references/memo-outline.md` — default section order, required fields, and decision-section placeholders.
