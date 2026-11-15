# Compliance Worksheet Outline — default

Used when no house template is supplied. A customer template replaces the column set and layout; the state model, flag model, and marker rules still apply.

**Workflow boundary:** a separate agreement/amendment-led covenant or borrowing-base monitoring worksheet. Do not complete an integrated model or its embedded covenant tab. Model outputs may be sourced inputs for a separately requested review; templates do not expand the job.

## Covenant worksheet

One row per covenant. Never omit a covenant because it could not be tested — report it as `NOT TESTED`.

| Column | Content |
|---|---|
| Covenant | Defined term as printed in the agreement |
| Section | Section reference for the covenant and for each component definition |
| Test date / frequency | As stated, including trailing or period basis |
| Threshold | As stated, including the step schedule and effective date in force for this test |
| Computed value | The result of the defined calculation |
| Arithmetic | The formula with its inputs substituted |
| Inputs | Each input: value, document, page, basis, and `verified` or `borrower-reported` |
| Headroom | Arithmetic distance to the threshold, as a number — not characterised. Reported as `unavailable` where the state is `NOT TESTED` for an `N/M` value or unestablished applicability |
| State | Exactly one of `PASS` · `FAIL` · `NOT TESTED` |
| Flags | Any number, or none |

### State legend

Mutually exclusive, in precedence order. First match wins.

| State | When |
|---|---|
| `NOT TESTED` | Required input missing, unreadable, unverified, or on an incompatible basis; definition not extractable; the test date has not occurred; the computed value is undefined or not meaningful (`N/M`, e.g. a zero or negative denominator) so there is no valid figure to compare with the threshold; or the covenant is springing or conditional and its applicability cannot be established from the evidence |
| `FAIL` | Computed value does not satisfy the threshold as stated |
| `PASS` | Computed value satisfies the threshold as stated |

`NOT TESTED` outranks the other two. An untested covenant is never reported as passing. Where the state is `NOT TESTED` because the value is `N/M` or applicability is not established, headroom is not operative — report it as `unavailable`, never as `0`. A conditional arithmetic distance may be shown separately and labelled as such.

### Flag legend

Independent of state. Any number may apply.

| Flag | Meaning |
|---|---|
| `borrower-reported input` | A tested value came from a borrower certificate rather than verified statements |
| `definition ambiguous` | The defined term admits more than one reading — quote what was found |
| `period mismatch` | Tested period does not align with the agreement's test date or basis |
| `basis mismatch` | Inputs are on different accounting bases |
| `amendment not confirmed` | The governing document may have been amended |
| `curative item applied` | An equity cure, add-back, or carve-out was included — name it and its section |

States and flags are counted separately. The counts are **not additive** — one covenant can be `PASS` with three flags.

## Extracted definitions

Record alongside the worksheet so the reading can be checked.

| Field | Content |
|---|---|
| Defined term | Quoted as printed |
| Section | Reference |
| Components | Each dependent defined term, quoted, with its own section |
| Carve-outs, caps, add-backs | As printed, with limits |
| Step schedule | Each level with its effective date |
| Cure / holiday / springing | As printed |

## Borrowing base

One row per collateral category.

| Column | Content |
|---|---|
| Category | As defined in the agreement |
| Gross balance | Value, source document, page, and as-of date |
| Ineligibles | Each deduction with the eligibility criterion and section cited |
| Eligible balance | Gross less ineligibles, with arithmetic |
| Advance rate | As stated, with section |
| Availability | Eligible × advance rate, with arithmetic |
| Sublimit / cap | As stated, with section |
| State and flags | Same model as covenants |

Total availability compares against outstandings only where outstandings were supplied with a source. Where they were not, report availability alone and mark the comparison `NOT TESTED`.

## Marker legend

| Marker | Meaning |
|---|---|
| `NOT LEGIBLE` | The figure is in the document but could not be read. Needs a cleaner copy. |
| `NOT FOUND` | The document set does not contain this item. |
| `NOT RETRIEVED` | A source could not be reached this session. |
| `NEEDS FEED` | No source available for this field — names the connector that would supply it. |
| `GAP` | A record was returned but does not match on identity, period, or basis. |
| `N/M` | Not meaningful — zero or negative denominator. |

Markers are never zero and never enter arithmetic. Missing values are blank or the applicable marker, never `0`, because a zero silently corrupts covenant and borrowing-base calculations.

## Footer

```
Governing document: <agreement, date, parties> — <execution version | copy, not confirmed>
Amendments: <listed and reviewed | none supplied — currency not confirmed>
Covenants in scope: <count> — PASS <n> · FAIL <n> · NOT TESTED <n>
Flags raised: <count by type — not additive with states>
Inputs: <verified from statements <n> | borrower-reported <n> | connector <n>>
Verification: <checks run and result; checks not run and why>
Template: <bundled default | house template name>
Artifact handoff: <xlsx built-in | docx built-in>
Connectors used: <names, or "none">
Other sources used: <supplied documents | M365 | public primary>
Output: inline draft | file created <identifier> | creation failed
Persistence: not attempted | saved <verified location> | failed
Save detail: <what was produced; where written; where not written; incomplete items>
Gaps: <NOT LEGIBLE / NOT FOUND / NOT RETRIEVED / NEEDS FEED / GAP items, or "none">
Generated: <date> — computed tests against cited agreement sections. Not a determination of
default, breach, waiver, or cure, and not a credit decision.
```

Each field reports what actually happened. Do not report amendments as reviewed when none were supplied, and do not describe a borrower-reported input as verified.
