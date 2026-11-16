# Schema questions, extraction states, and the DOCX / XLSX structures

Loaded on demand by `compare-key-terms`. Nothing here overrides the guardrails in SKILL.md.

## The three scoping questions

Resolve these once, because changing the schema after extraction is expensive. Derive each answer
from the materials first and ask only about what genuinely remains open.

1. **Which terms do you wish to extract?** Offer the derived schema as a concrete default the user
   can accept or amend, naming the actual proposed columns.
2. **What pre-defined values should the report use?** For each classified column, offer the option
   set — `Mutual / One-way / Not stated` — so the vocabulary is fixed before extraction.
3. **Do you have a prior schema or report whose format you would like to copy?** Offer the derived
   schema, a supplied template, or a named earlier workbook. If one is named, locate and inspect it
   before mirroring its column names and order.

If the request and materials already resolve all three, proceed without asking. Put every unresolved
question into one question card and stop for the answer; never ask a second round. Use
one flat question per decision with complete, independently actionable options, and a **Custom (type
it below)** option where the listed choices cannot cover every supported answer. The card allows at
most four questions, has no conditional logic, and displays every question it receives. If the user
declines or says to proceed with defaults, use the derived schema and option sets, record every
assumption in the output's `Schema` section, and identify the assumed schema in the delivery reply.

Prefer constrained values over drifting prose. For each term define a short review question and one
value type: exact text, classification, date, duration, currency, number, or concise summary.

## Extraction states

Every document-term combination gets exactly one state.

| State | Meaning |
| --- | --- |
| `Found` | The source states the term clearly. |
| `Not stated` | The source was reviewed and does not address the term. |
| `Unclear` | Related language exists but is ambiguous, incomplete, or internally inconsistent. |
| `Needs review` | The answer depends on an unreadable source, missing referenced material, external facts, or legal or commercial judgement. |

An unreadable document still gets a row, with every affected term marked `Needs review`.

## Word document

Hand the content brief to Cowork's built-in Word document creator to create one professionally formatted `.docx`, using
landscape orientation where needed to keep the comparison table readable. Include the same **Scope
and assumptions**, **Review**, **Coverage** and **Schema** sections as the chat output, plus a
**Source evidence** appendix with one row per document-term combination:

`Document | Term | Value | State | Exact source text | Location | Source URL | Evidence note`

Use human-readable document names, clause or section locators, exact short quotes and source URLs;
never put internal identifiers or workspace paths in the DOCX. Complete the Word document creator's generation,
validation, rendering, visual QA and delivery workflow. The finished document lands in `output/` (or
on the `live` surface where offered) through the artifact tools — never a direct write to a durable
folder — and is delivered exactly once, after all corrections and QA are complete.

## Excel workbook

1. Hand the normalised dataset to Cowork's built-in Excel workbook creator to create one `.xlsx` with a concise filename, and
   retain the returned file reference as the target for all subsequent workbook operations.
2. Populate and format that one workbook through the Excel workbook creator using batched, bounded
   two-dimensional range writes; never write cell by cell.
3. Do not claim delivery if workbook creation is unavailable or fails, and never replace the file
   with a Markdown table while claiming workbook delivery.

Create four sheets.

**Review** — one row per source document:
`Document | Source scope | Document type | Overall status | [term columns...] | Flags`

Use `Main document`, `Supplied file` or `Retrieved source` for `Source scope`. Write `Not stated`,
`Unclear` or `Needs review` directly in a term cell where there is no positive value.

**Sources** — one row per document-term combination:
`Document | Term | Value | State | Exact source text | Location | Source URL | Evidence note`

Leave `Exact source text` blank only for `Not stated`, or where the evidence note explains why exact
text is unavailable. Store source URLs as plain text; never fabricate them or create hyperlink
formulas.

**Coverage** — one row per discovered source:
`Source | Scope | File type | Included | Read status | Coverage limitation`

Expose unreadable, unsupported, duplicate, excluded and missing sources.

**Schema** — one row per extraction term:
`Order | Column | Review question | Value type | Allowed values | Notes`

Convert each populated range to a filtered Excel table, freeze the header row on every sheet, use
readable role-based column widths, and wrap evidence text. Keep the style restrained. Colour states
consistently: white `Found`, grey `Not stated`, yellow `Unclear`, orange `Needs review`. Do not add
charts, dashboards, decorative images or companion files unless the user explicitly asks.

## Citation discipline

For every substantive claim grounded in a source, quote the operative wording, cite the governing
section, clause, heading or page by name, and name the source file by its exact filename. Every
`Found`, `Unclear` or `Needs review` value supported by available source text carries that evidence.
Never expose internal paths or workspace directories in prose or in a generated file.
