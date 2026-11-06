# Annual Review Packet Outline — default

Used when no house template is supplied. A customer template replaces the section order and field list; the symmetric comparison gate, marker rules, and placeholder sections still apply.

## 1. Review header

| Field | Content |
|---|---|
| Obligor | Exact legal name, jurisdiction, identifier |
| Facilities in scope | Each, with source |
| Prior review | Date and source document |
| Current review period | Period end and length |
| Prior-state coverage | `complete` · `partial — <what was not read>` · `unavailable` |
| Comparison basis | `full comparison` · `limited — novelty and removal unverified` |

The coverage value governs every comparison claim in the packet. State it here, before any comparison appears.

## 2. Financial comparison

One column per period, prior and current, each carrying period end, length, preparer, assurance level, accounting basis, and units scale.

Rows follow the spread schema. For each: prior value, current value, change as an amount, change as a percentage, and the source of each side.

Carry every marker through unchanged. A `NOT LEGIBLE` or `NOT COMPARABLE` figure stays marked and never becomes a number.

Where the accounting basis or fiscal period changed between the two sides, do not compute a change — output `NOT COMPARABLE — RECONCILIATION REQUIRED` for the affected rows only, and retain the rows that remain comparable.

Where no current financials were supplied:

```
NOT GENERATED — no spread or financial statements supplied this session. The spread is
produced by the financial-statement-spread skill; supply the statements or the completed
spread to populate this section.
```

## 3. What changed

Narrate movement as arithmetic. Direction, amount, percentage, period. Never characterise quality — no "improved", "deteriorated", "healthy", or "concerning".

**Claim language depends on prior-state coverage:**

| Prior coverage | Permitted |
|---|---|
| Complete | `added` · `removed` · `changed` · `unchanged` |
| Partial | `currently present; novelty unverified` · `currently absent; prior presence unverified` |
| Unavailable | Current state only — no comparison claims |

The restriction is symmetric. Partial coverage blocks "this was added" and "this was resolved" equally.

## 4. Covenant status

Restated from a supplied compliance check. Carry states and flags through **unchanged**.

| Column | Content |
|---|---|
| Covenant | Defined term |
| Section | Reference |
| Test date | As tested |
| Result | `PASS` · `FAIL` · `NOT TESTED` — exactly as supplied |
| Flags | As supplied |
| Source | The check document and date |

A `NOT TESTED` covenant appears in the table as `NOT TESTED`. Never omit it, and never let omission imply a pass.

Where no check was supplied:

```
NOT TESTED HERE — no compliance check supplied this session. Covenant testing is performed
by the covenant-compliance-check skill against the governing credit agreement.
```

Do not test covenants in this packet from a covenant summary or a prior memo's description.

## 5. Public-record refresh

Per search: source, jurisdiction, exact name searched, date run, and result — **including clean results**, which use the form in `public-records.md` and never read as "no liens".

Comparison against the prior review's findings follows the same symmetric gate: a filing is "new" only where the prior search covered the same index and jurisdiction.

## 6. Exceptions and action items

| Column | Content |
|---|---|
| Exception | What it is |
| Arose | Date and source document |
| Prior status | As recorded at the last review |
| Current evidence | What the current file shows, with source |
| Status | Carried forward unchanged — **not** closed, cleared, or waived here |
| Owner / due date | As documented, or `NOT FOUND — not stated` |

Carry forward every prior exception not shown to be resolved. An exception is not closed because it was not mentioned in the current file.

Where evidence suggests resolution, record the evidence and leave the status unchanged for the analyst.

## 7. Relationship and exposure

Facilities, outstandings, payment history, and ticklers **as supplied or from a connector**, each with its source and as-of date.

Where no LOS or core connector is configured, this section reflects only what the user supplied — say so rather than implying a complete facility picture.

## 8. Decision sections — never filled

```
[ RISK RATING — for analyst completion. Not generated. ]

[ REVIEW CONCLUSION — for analyst completion. Not generated. ]

[ EXCEPTION DISPOSITION — for analyst completion. Not generated. ]
```

Never delete, never fill, and never place equivalent content elsewhere under a different heading.

## Marker legend

| Marker | Meaning |
|---|---|
| `NOT LEGIBLE` | The figure is in a supplied document but could not be read. |
| `NOT FOUND` | The source answered and has no record. |
| `NOT RETRIEVED` | A source could not be reached this session. |
| `NEEDS FEED` | No source available for this field — names the connector that would supply it. |
| `GAP` | A record was returned but does not match on identity, period, or basis. |
| `N/M` | Not meaningful — zero or negative denominator. |
| `NOT COMPARABLE — RECONCILIATION REQUIRED` | Periods are on different bases. |

Markers are never zero and never enter arithmetic. Missing values are blank or the applicable marker, never `0`, because a zero silently corrupts downstream comparisons.

## Footer

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
Artifact handoff: <docx built-in>
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

Each field reports what actually happened. Do not report a full comparison when prior coverage was partial.
