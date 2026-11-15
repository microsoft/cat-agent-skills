# Credit Memo Outline — default

Used when no house template is supplied. A customer template replaces section order, headings, and required fields; the sourcing rules, marker rules, and decision-section placeholders still apply.

Decision sections appear in every draft with their headings intact and are never filled.

## 1. Transaction summary

| Field | Content |
|---|---|
| Obligor | Exact legal name, jurisdiction, identifier |
| Facility type | As requested |
| Amount | As requested |
| Purpose | As stated in the deal material |
| Tenor / maturity | As requested |
| Amortization | As requested |
| Collateral offered | As documented |
| Guarantors | Named, with form of guaranty |
| Pricing | **As supplied only** — quoted from the deal material, never proposed. If not supplied, `NOT FOUND — not stated in supplied deal material` |

Each field names the document it came from. Never infer a term that was not stated.

## 2. Sources and uses

Two columns, each line with its source. Present only where the deal material supplies it.

Where the two sides do not balance, show the difference and say so. Do not plug. Where only one side was supplied, present that side and mark the other `NOT FOUND — not stated in supplied deal material`.

## 3. Borrower description

Legal entity and structure first — name, jurisdiction, identifier, formation date, status, with the registry and retrieval date.

Then: what the business does, markets served, locations, headcount and size indicators, and operating history. Attribute each to the borrower's own material, a public record, or trade press, with a date. Distinguish what the company says about itself from what an independent source reports.

## 4. Ownership and management

Owners with percentages **only from a document that states them** — operating agreement, cap table, or filing. Never infer ownership from titles or surnames.

Management: name, role, tenure, and relevant business background. Business-relevant detail only. No protected characteristics, and no personal financial or legal history.

Where a corporate family tree is not evidenced, `NEEDS FEED — corporate hierarchy source (e.g. D&B, S&P Capital IQ)`.

## 5. Industry overview

Sector description, demand drivers, and conditions, each attributed with publisher and date.

Benchmarks appear only from a source that supplies them. With none configured:
`NEEDS FEED — industry benchmark source (e.g. RMA, Moody's, S&P Capital IQ)`. Never present a "typical" margin or leverage level assembled from general knowledge as a benchmark.

## 6. Financial recap

**Restates a supplied spread or supplied statements. Never creates one.**

Where none was supplied, this section reads:

```
NOT GENERATED — no spread or financial statements supplied this session. The spread is
produced by the financial-statement-spread skill; supply the statements or the completed
spread to populate this section.
```

Where figures are available, present per period:

| Field | Content |
|---|---|
| Period end and length | `FYE 2025-12-31, 12 months` |
| Preparer and assurance | `Management-prepared, unaudited` |
| Accounting basis | `GAAP` |
| Revenue, margin, EBITDA, net income | Value with source, marker carried through if marked |
| Leverage, coverage, liquidity | Value with formula and inputs, or marker |
| Trend | Direction, amount, and percentage, as arithmetic |

Describe movement, never quality. Carry every marker through unchanged — a marked figure never becomes a number or a rounded approximation in the narrative.

## 7. Collateral

Per collateral item: type, description, stated value with its source and date, valuation method where stated, and lien position **as documented**.

Where a value is borrower-stated or from an undated appraisal, label it. Where lien position depends on a search that was not run, say so rather than asserting priority.

## 8. Guarantors

Per guarantor: legal name and identifier, relationship to the obligor, form and scope of guaranty as documented, and whether financial information was supplied. Guarantor financial analysis follows the same rules as the borrower's — no characterisation.

## 9. Banking relationship

Existing facilities, deposit and treasury relationship, and history, **as supplied or from a connector**. Where an LOS or core connector is not configured, the existing-exposure view comes from what the user supplied; say so rather than implying a complete relationship picture.

## 10. Decision sections — never filled

Present with headings intact:

```
[ RISK RATING — for analyst completion. Not generated. ]

[ RECOMMENDATION AND CONDITIONS — for banker completion. Not generated. ]

[ EXCEPTIONS AND MITIGANTS — for banker completion. Not generated. ]
```

Never delete these sections, never fill them, never overwrite prior decision rationale, and never place equivalent content elsewhere in the memo under a different heading. Updates append and mark changes.

## Marker legend

| Marker | Meaning |
|---|---|
| `NOT LEGIBLE` | The figure is in a supplied document but could not be read. |
| `NOT FOUND` | The source answered and has no record, or the deal material does not state it. |
| `NOT RETRIEVED` | A source could not be reached this session. |
| `NEEDS FEED` | No source available for this field — names the connector that would supply it. |
| `GAP` | A record was returned but does not match on identity, period, or basis. |
| `UNVERIFIED — secondary source` | From something reproducing the record rather than the record itself. |

## Footer

```
Obligor: <exact legal name, jurisdiction, identifier>
Request: <facility, amount, purpose, tenor — as supplied, source named>
Financial basis: <spread supplied | statements supplied | none — recap not generated>
Sources: <count> — <each with document/publisher and date>
Retrieval coverage: <complete | partial — name what was partial>
Template: <bundled default | house template name>
Artifact handoff: <docx built-in>
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

Each field reports what actually happened. Do not report a financial recap as generated when no figures were supplied.
