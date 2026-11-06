# Spread Outline — default

Used when no house template is supplied. A customer template replaces the account schema, ratio set, and add-back treatment; the verification gate and marker rules in `document-extraction.md` still apply.

**Workflow boundary:** a standalone historical borrower-credit spread with source assurance/basis, visible normalization, and verified ratios. Do not populate an integrated three-statement model, including its historical block, or add forecast links. A customer schema cannot add that excluded business job.

## Workbook structure

Three tabs. Keep them separate — do not merge as-reported figures into the normalized tab.

### Tab 1 — Input (as reported)

One column per period. Header block carries, for each period column:

| Field | Example |
|---|---|
| Period end | `FYE 2025-12-31` |
| Period length | `12 months` |
| Document | `Ridgeline FY2025 statements.pdf` |
| Preparer and assurance | `Management-prepared, unaudited` |
| Accounting basis | `GAAP` |
| Units scale | `USD thousands` |

Rows are the borrower's captions **exactly as printed**, in the borrower's own order, with a page reference per line. Do not reclassify, reorder, or round here.

### Tab 2 — Normalized

Schema lines below, one column per period. Each line carries a **normalization note** naming the source caption it was mapped from. Where a source caption has no schema equivalent, keep it as an `Other` line and say so in the note rather than forcing a mapping.

Adjustments sit in their own clearly labelled rows beneath the reported figure, never replacing it. Each adjustment row names its supporting document, page, and asserter.

### Tab 3 — Ratios

Formula-driven, referencing Tab 2. Each ratio shows its formula and both inputs. Never paste a computed value.

## Account schema

**Income statement**
Revenue · Cost of goods sold · Gross profit · Selling, general and administrative · Depreciation and amortization · Other operating expense · Operating income · Interest expense · Other income (expense) · Pre-tax income · Income tax · Net income

**Balance sheet**
Cash and equivalents · Accounts receivable · Inventory · Other current assets · Total current assets · Net fixed assets · Intangibles · Other assets · Total assets
Accounts payable · Accrued expenses · Current portion of long-term debt · Revolving line of credit · Other current liabilities · Total current liabilities · Long-term debt · Subordinated debt · Other liabilities · Total liabilities · Equity · Total liabilities and equity

**Cash flow**
Net income · Depreciation and amortization · Other non-cash · Change in working capital · Cash from operations · Capital expenditures · Other investing · Cash from investing · Net borrowings · Distributions and dividends · Equity contributions · Cash from financing · Net change in cash

**Derived**
EBITDA · Funded debt · Net funded debt · Working capital · Fixed charges · Debt service

## Ratio set

Show the formula and both inputs on every line.

| Ratio | Formula |
|---|---|
| Revenue growth | (Revenue − prior Revenue) ÷ prior Revenue |
| Gross margin | Gross profit ÷ Revenue |
| Operating margin | Operating income ÷ Revenue |
| EBITDA margin | EBITDA ÷ Revenue |
| Funded debt / EBITDA | Funded debt ÷ EBITDA |
| Net funded debt / EBITDA | (Funded debt − Cash) ÷ EBITDA |
| Debt service coverage | (EBITDA − unfinanced capex − distributions − cash taxes) ÷ (Interest + scheduled principal) |
| Fixed charge coverage | (EBITDA − unfinanced capex − distributions − cash taxes) ÷ (Interest + scheduled principal + rent) |
| Interest coverage | EBITDA ÷ Interest expense |
| Current ratio | Total current assets ÷ Total current liabilities |
| Quick ratio | (Cash + Accounts receivable) ÷ Total current liabilities |
| Working capital | Total current assets − Total current liabilities |
| Days sales outstanding | Accounts receivable ÷ Revenue × days in period |
| Days inventory | Inventory ÷ Cost of goods sold × days in period |
| Days payable | Accounts payable ÷ Cost of goods sold × days in period |
| Cash conversion cycle | DSO + Days inventory − Days payable |
| Total liabilities / Equity | Total liabilities ÷ Equity |

**Coverage inputs vary by house convention.** Where the credit agreement defines a coverage or leverage term, compute it as defined and cite the section — the definition in the agreement governs over this table.

EBITDA follows the basis rules in `document-extraction.md`: borrower-reported with reconciliation, or operating income plus a D&A figure evidenced as sitting inside that same subtotal. Otherwise `NOT COMPARABLE — RECONCILIATION REQUIRED`.

Zero or negative denominator → `N/M`.

## Marker legend

Include on the workbook, so a reviewer reads the cells correctly.

| Marker | Meaning |
|---|---|
| `NOT LEGIBLE` | The figure is in the document but could not be read. Needs a cleaner copy. |
| `NOT FOUND` | The document set does not contain this line. |
| `NOT RETRIEVED` | A source could not be reached this session. |
| `NEEDS FEED` | No source available for this field — names the connector that would supply it. |
| `GAP` | A record was returned but does not match on identity, period, or basis. |
| `N/M` | Not meaningful — zero or negative denominator. |
| `NOT COMPARABLE — RECONCILIATION REQUIRED` | Inputs could not be evidenced as being on the same basis. |

Markers are never zero and never enter arithmetic. Missing values are blank or the applicable marker, never `0`, because a zero silently corrupts downstream ratios.

## Footer

Place on the first tab.

```
Documents used: <count> — <each: name, type, assurance level, basis, periods, pages read>
Extraction route: <connector name | direct read | page-image read>
Verification: <checks run and result; checks not run and why>
Retrieval coverage: <complete | partial — name what was partial>
Template: <bundled default | house template name>
Artifact handoff: <xlsx built-in>
Connectors used: <names, or "none">
Other sources used: <supplied documents | M365 | public primary | secondary, marked>
Output: inline draft | file created <identifier> | creation failed
Persistence: not attempted | saved <verified location> | failed
Save detail: <what was produced; where written; where not written; incomplete items>
Gaps: <NOT LEGIBLE / NOT FOUND / NOT RETRIEVED / NEEDS FEED / GAP items, or "none">
Generated: <date> — as-reported figures with derived metrics shown with their components.
No risk rating, credit decision, or creditworthiness assessment.
```

Each field reports what actually happened. Do not report a check as run when the inputs did not support it, and do not describe a period's basis or assurance level as anything other than what the source document states.
