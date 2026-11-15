# Vendor Risk Review — Default Outline

Used when no template is named in the request and none is present in
`Cowork Templates/Risk and Compliance/vendor-risk-review/`.

**A template replaces layout, never gates.** The CUEC count, the period gap, and the quoted
opinion survive every template.

**One gap list.** Every shortfall in this artifact (anything absent, unretrieved, partial,
mismatched, rejected, unverified, unperformed, unconfigured, or undated) is recorded exactly
once in the Open items list (§ 10), as its own bullet with an ID (G1, G2, ...), leading with its
marker, one shortfall per bullet. **Marker cells in this outline:** the § 2 `Assurance` cell
where no assurance is carried and the `Review period not covered` row; the § 3 `In scope` cells
and the scope-mismatch statement; the § 6 CUEC `State` cells; the § 7 `Disposition` cells
reading `unknown`, the `Identity resolution` cells, and the coverage-statement `Not searched`
and `Screening` lines; the § 8 residual-risk `Notes` cells; the workbook `Marker` cells. A
marker cell carries its marker followed by its G-ID in brackets, for example `GAP - period
mismatch: 3 months not covered (G1)`. Every other cell is a fact cell: it states what the source
says in plain words (for example `none stated in <source>`) and carries no marker token. A
search that returns nothing relevant is a gap: `NOT FOUND`, with its G-bullet. A marker token
written anywhere outside the Open items list, including prose, the chat reply, and the footer,
carries its (Gn) right after the marker phrase, and `NOT DETERMINED` carries its (Dn). Ordinary
prose, the chat reply, handling notes, and footer lines can mention a gap in plain words; every
gap mentioned anywhere has its G-bullet (`house-rules.md` § 4).

**Each determination is its own row or bullet.** Every owner determination listed in this
artifact carries its own marker. Never one blanket marker line over a list (`house-rules.md` § 9).

**One canonical list.** Every `NOT DETERMINED` item appears exactly once, with an ID (D1, D2,
...), in the Determinations outstanding list (§ 10), and the footer's `NOT DETERMINED` figure
is the number of bullets there. Each D-bullet holds exactly one decision; a secondary
question gets its own D-number.
No D-bullet contains " and ", " or ", "/", or a second question mark joining two decisions;
split any that does. Every `UNRESOLVED MATCH` disposition is its own D-bullet. Undecided matters go there, never in the Open items list. A summary list never groups
several determinations or gaps under one marker bullet: it refers to the canonical lists by ID
with no marker of its own (not counted).

---

## Memo (`.docx`)

### 1. Header

```
THIRD-PARTY RISK REVIEW — <vendor> / <service>
Report: <type> covering <period>
Destination: internal working paper | committee/board
Prepared: <date>    Preparer: <name>
Status: DRAFT — no risk rating, no approval decision. For third-party risk owner.
```

### 2. What was supplied

| Field | Value |
|---|---|
| Document supplied | SOC 2 Type II · Type I · SOC 3 · bridge letter · ISO cert · DDQ · contract |
| Assurance | Audited · management assertion (unaudited) · self-reported · `NOT FOUND - supplied documents carry no assurance (Gn)` |
| Report period | |
| **Review period not covered** | **`GAP - period mismatch: <n> months not covered (Gn)`. Stated explicitly** |
| Service auditor | |
| Read via | Native text · OCR · connector · upload |

> Where a Type I was supplied: **"Type I. Tests design at a point in time only. Says nothing
> about operating effectiveness."** — first line of the memo.

### 3. Scope

**Trust services criteria**

| Criterion | In scope |
|---|---|
| Security | |
| Availability | |
| Confidentiality | |
| Processing Integrity | |
| Privacy | |

> Out-of-scope criteria are **untested, not passed.** State that sentence.

`In scope` reads `yes`, or `GAP - out of scope: untested, not passed (Gn)` for each criterion not in
scope, one G-bullet naming every such criterion.

**Systems, products, and locations in scope.** Where these differ from what the firm is buying →
`GAP - scope mismatch (Gn)`.

**Subservice organizations**

| Organization | What it provides | Treatment |
|---|---|---|

`inclusive` = tested. **`carve-out` = not tested** — an unexamined dependency.

### 4. Opinion

> Quoted verbatim. Basis-for-qualification paragraph also quoted where present.

Type: unqualified · qualified · adverse · disclaimer.

### 5. Exceptions

| # | Control | Auditor's description (verbatim) | Items tested / deviations | Management's response (verbatim) | Auditor comment |
|---|---|---|---|---|---|

Never summarised as minor or immaterial. Record "n of N" exactly as stated.

### 6. Complementary user-entity controls

**Headline line, always present:**

```
The report specifies <n> complementary user-entity controls.
  confirmed adopted (with evidence):  n
  not adopted:                        n
  NOT DETERMINED — owner confirms:    n
```

| # | CUEC (verbatim) | Related control | State | Evidence | Owner |
|---|---|---|---|---|---|

Default state is `NOT DETERMINED - owner confirms (Dn)`. `adopted` requires cited evidence.

> Where the opinion is clean and CUECs are unadopted or undetermined, the memo states:
> **"A clean opinion with unadopted complementary user-entity controls is not a clean result."**

### 7. Public research

| Finding | Source | Date | Disposition | Identity resolution |
|---|---|---|---|---|

`Disposition`: allegation · investigation · charge · settlement without admission · conviction ·
overturned · **unknown** (written `unknown: NOT FOUND - <sources searched> have no record of the
outcome (Gn)`).

`Identity resolution`: attributed (state the corroborating identifier) ·
`UNRESOLVED MATCH - not attributed (Gn)`, with its disposition as its own D-bullet.

**Coverage statement, required:**

```
Searched:     <sources, languages, jurisdictions, date range>
Not searched: GAP - coverage: <what was not searched> (Gn)
Screening:    NEEDS FEED - screening provider (Gn); this is research, NOT a sanctions or PEP screen
```

Never "no adverse findings."

### 8. Residual risks

| Risk | Source | Notes |
|---|---|---|
| Out-of-scope criteria | Scope section | `GAP - out of scope: <criteria> (Gn)`; untested, not passed |
| Period gap | <n> months | `GAP - period mismatch: <n> months (Gn)`; bridge letter is unaudited, if supplied |
| Carved-out subservice orgs | Scope section | `GAP - carve-out: <organization> (Gn)`; untested dependency |
| Unadopted / undetermined CUECs | CUEC section | **Open risk owned by the firm**; each undetermined CUEC is in § 10 by ID |
| Exceptions without tested remediation | Exceptions section | |

The `Risk` cell carries its own (Gn) whenever it uses a gap phrase, for example "excerpt",
"missing", or "not covered": `Complementary controls section missing (Gn)`.

Stated factually with sources. **No rating.**

### 9. Open questions for the vendor

Numbered, specific, answerable. This is the section a reviewer actually uses.

### 10. Determinations outstanding

One bullet per determination, each carrying its own marker in the form the wording table below
gives for a rating (`NOT DETERMINED` with the third-party risk owner as the decider). Never one
blanket marker line over the list.

- Risk rating
- Tier
- Approval
- CUEC adoption confirmation, one bullet per CUEC whose state is `NOT DETERMINED`, by CUEC ID
- Whether the period gap is acceptable
- Any other open determination raised in the memo, one bullet each

This is the canonical list: each bullet has an ID (D1, D2, ...), and the footer's
`NOT DETERMINED` figure is the number of bullets here. A CUEC row and its bullet are one item
(`house-rules.md` § 9).

**Open items (G-list).** The canonical list of shortfalls, kept next to the
Determinations outstanding list. Every shortfall in this artifact, including those in
marker cells (listed at the top of this outline), the chat reply, and the footer, is listed here
exactly once as its own bullet with an ID (G1, G2, ...), leading with its marker, one
shortfall per bullet. A marker cell keeps its marker followed by the bullet's ID, for example
`(G1)`; every marker token outside this list carries its (Gn), every G-ID cited exists here,
and every bullet here is cited at least once or stands alone. One instrument's PROPOSED status,
or one document's DRAFT status, is one bullet naming every row it applies to; a DRAFT document
that is also rejected has its DRAFT bullet plus its GAP bullet (`house-rules.md` § 4).
Undecided matters go in the Determinations outstanding list, never here. For example:

```
- G1 - GAP - period mismatch: 3 months between report end and review date
- G2 - GAP - carve-out: subservice data-centre provider (§ 8)
```

### 11. Draft TPRM handoff

If a TPRM platform is available, include existing vendor IDs, service records, prior assessment IDs, owners, and current status read from it. The output is a draft import/export package for a human third-party risk owner to review and submit; state that no source-system update was performed.

### 12. Footer

Per `house-rules.md` § 9, including draft handoff status and that any platform update is the human's action.

Build the counts only after the rest of the draft is final, and only from the two canonical lists: for each marker type, the number of G-bullets in the Open items list leading with it, and for `NOT DETERMINED`, the number of D-bullets, each with the unit items (for example `NOT FOUND: 5 items`, `NOT DETERMINED: 7 items`). Give one number per marker type, never "plus", a sum of parts, or a range, and list every marker type that leads a G-bullet. Never count table cells, prose, the chat reply, or footer lines. Footer lines, including Coverage, Connectors, Web, Sources, Policy repository searched, Files, Codification, and Template, can describe gaps in plain words; every gap they mention has its G-bullet. A marker token in a footer line carries its (Gn). A Codification line with no rule text relied on reads `not performed: no rule text relied on (Gn)`, with the G-bullet `GAP - codification check not performed: no rule text relied on`. The Template line names the resolution step used; where `Cowork Templates/Risk and Compliance/vendor-risk-review/` held no template, the line says so and the Open items list carries `NOT FOUND - Cowork Templates folder has no vendor-risk-review template`. Recount the two lists before output and correct any figure that differs (`house-rules.md` § 9).

---

## Exceptions & CUEC workbook (`.xlsx`)

Two tabs, live formulas.

**Tab 1 — Exceptions.** Columns as § 5 above, plus `Marker` and `Source (section, page)`.

**Tab 2 — CUECs.** Columns as § 6 above, plus `Marker` and `Source (section, page)`.

### Summary block

```
Exceptions:                       n
  with management response        n
  with auditor comment            n
CUECs specified:                  n
  confirmed adopted               n
  not adopted                     n
  NOT DETERMINED                  n
Criteria in scope:                n of 5
Subservice orgs carved out:       n
Review period not covered:        n months
```

---

## Wording that must not appear

| Never | Instead |
|---|---|
| "Low risk" / "acceptable" / "tier 2" | `NOT DETERMINED — third-party risk owner` |
| "Clean SOC 2" | The quoted opinion, plus the CUEC headline |
| "Covers privacy and availability" (Security-only report) | "Security only. Other criteria untested, not passed" |
| "No exceptions noted" (Type I) | "Type I — design only at a point in time" |
| "The vendor is certified" (DDQ or questionnaire) | "Self-reported and untested" |
| "No adverse findings" | The coverage statement |
| "Minor exception" | The auditor's verbatim description |
| "Approved" / "we recommend onboarding" | Out of scope. Owner determines |
| "<name>, <title>, wrote…" (a document author or commenter) | "The <role>'s <comment / email / note> on <document>, <location>" (`house-rules.md` § 12) |
