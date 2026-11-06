# Response Register — Default Outline

Used when no template is named in the request and none is present in
`Cowork Templates/Risk and Compliance/exam-request-response/`.

**A template replaces layout, never gates.** Examiner item numbering survives every template.

**One gap list.** Every shortfall in this artifact (anything absent, unretrieved, partial,
mismatched, rejected, unverified, unperformed, unconfigured, or undated) is recorded exactly
once in the Open items list (§ 7), as its own bullet with an ID (G1, G2, ...), leading with its
marker, one shortfall per bullet. **Marker cells in this outline:** the register `Period requested`,
`Due date`, `Candidate evidence`, `Document date`, `Owner basis`, `Responsiveness check`, `Determination`, and `Marker` cells; every cell of a numbering-gap row; any cell with no value (see No blank cell); the § 5 `Marker` cell; the § 6
check-result and `Determination` lines. A marker cell carries its marker followed by its G-ID in
brackets, for example `NOT FOUND - Compliance SharePoint has no record of evidence for item 6
(G1)`. Every other cell is a fact cell: it states what the source says in plain words (for
example `none stated in <source>`) and carries no marker token. A search that returns nothing
relevant is a gap: `NOT FOUND`, with its G-bullet. A marker token written anywhere outside the
Open items list, including prose, the chat reply, and the footer, carries its (Gn) right after
the marker phrase, and `NOT DETERMINED` carries its (Dn). Ordinary prose, the chat reply,
handling notes, and footer lines can mention a gap in plain words; every gap mentioned anywhere
has its G-bullet (`house-rules.md` § 4).

**Each determination is its own row or bullet.** Every owner determination listed in this
artifact carries its own marker. Never one blanket marker line over a list (`house-rules.md` § 9).

**One canonical list.** Every `NOT DETERMINED` item appears exactly once, with an ID (D1, D2,
...), in the Determinations outstanding list (§ 7), and the footer's `NOT DETERMINED` figure
is the number of bullets there. Each D-bullet holds exactly one decision; a secondary
question gets its own D-number.
No D-bullet contains " and ", " or ", "/", or a second question mark joining two decisions;
split any that does. For example, "assign the item 5 owner" is D8 and "confirm item 5
responsiveness" is D9. Undecided matters go there, never in the Open items list. A summary list never groups
several determinations or gaps under one marker bullet: it refers to the canonical lists by ID
with no marker of its own (not counted).

---

## Register (`.xlsx`)

One row per **evidence obligation** — compound items are split into sub-lettered rows under the
examiner's original number.

| Column | Notes |
|---|---|
| Item no. | **Exactly as printed.** Sub-letters added for split items: `4(a)`, `4(b)`. On a numbering-gap row: `NOT FOUND - letter prints no item <n> (Gn)`, never a bare number |
| Split from | The original item number, where this row came from a split |
| Request text | Verbatim, as it applies to this row |
| Period requested | As printed for the item. An item that states none takes the list-wide review period where the letter states one. Otherwise `NOT FOUND - letter states no period for item <n> (Gn)`. Never "none stated", a dash, or blank |
| Population / sample | |
| Format requested | |
| Due date | Per item, else the list date. Neither stated: `NOT FOUND - <source> states no calendar date (Gn)`. Never "none stated", a dash, or blank |
| Owner | |
| Owner basis | How the owner was identified. `NOT FOUND - owner not identified (Gn)` if none |
| Candidate evidence | Document name. A search with no responsive document: `NOT FOUND - no responsive document located (Gn)`. A document examined and rejected: `GAP - scope mismatch, not a candidate: <doc> (Gn)`, its own G-bullet |
| Version / approval | As printed on the document. An examined file that prints no version: `NOT FOUND - <file> states no version (Gn)`, its own G-bullet, distinct from the `Document date` bullet |
| Document date | As printed on the document. An examined file that prints none: `NOT FOUND - <file> states no document date (Gn)`, its own G-bullet. Transaction or filing date ranges go in `Notes`, never in this cell. Never "none stated", a dash, or blank |
| Location | Full path or link. A document examined and rejected: `<path> (rejected: Gn)`, citing its rejection G-bullet; never "rejected file at <path>" without the ID |
| Addresses which part | For split and multi-part items |
| Responsiveness check | `period ok` · `population ok` · `scope ok` · `format ok` · `complete ok`, or the `GAP` for each term that fails, each with its (Gn). A partial extract, missing sections, omitted body text, or a partial population is a completeness `GAP`, never `format ok`. A record that cannot be located is `NOT FOUND` with its (Gn). A sample that fails a population request is `GAP - population does not match request (Gn)` and stays the examined file; never `scope ok` beside a scope-mismatch marker; `scope ok` and `population ok` never appear in a row with a scope or population `GAP` |
| Status | See below |
| Determination | `NOT DETERMINED - owner confirms (Dn)` until an actual confirmation exists |
| Marker | Where the row carries one |
| Notes | Quoted or reported document text attributed by role, document, and location (`house-rules.md` § 12). A shortfall written here can be in plain words; it carries its marker in `Marker` and has its G-bullet in § 7: an extract or missing section is `GAP`, a record not located is `NOT FOUND`, and an open question is a D-bullet with its decider. Never a superseded version's in-force span unless that version prints it (`NOT FOUND - <doc> states no effective span (Gn)`). Two sources that disagree get `GAP - conflicting sources: <what> - <doc A> "<x>" vs <doc B> "<y>" (Gn)` |

**Numbering gap.** Where the examiner's numbering skips a number, the register carries one row
for it. Every cell of that row, including `Item no.`, `Period requested`, `Due date`, and `Document date`,
reads `NOT FOUND - letter prints no item <n> (Gn)`, with the same G-ID. `Item no.` reads, for example,
`NOT FOUND - letter prints no item 6 (Gn)`, never the bare number. Never blank or a dash.

**No blank cell.** No register cell is blank or a dash. A cell with no value takes the marker
form, for example `NOT FOUND - <source> states no <x> (Gn)`, with its G-bullet, and is a
marker cell for that row.

### Status values

| Status | Means |
|---|---|
| `not started` | No evidence search yet |
| `candidates located` | Evidence found; owner has **not** confirmed |
| `owner confirmed` | An actual confirmation exists in this session or the record |
| `gap` | Searched; nothing responsive located |
| `blocked` | Cannot proceed — reason required |
| `clarification requested` | Item text ambiguous; question raised with the examiner |

`owner confirmed` is never inferred from evidence quality.

### Summary block

```
Items on the list:              n   (as numbered by the examiner)
Evidence obligations:           n   (after splitting compound items)
  owner confirmed               n
  candidates located            n
  gap — nothing located         n
  blocked                       n
  clarification requested       n
  not started                   n
Owners unidentified:            n of N obligations   (obligation numbers, then G-IDs)
Rows carrying markers:          n
```

Both counts are shown — the examiner's item count and the split obligation count. They differ,
and the memo explains why.

---

## Cover memo (`.docx`)

Every legal or regulatory statement anywhere in the memo carries a primary-source citation with
its as-of date. A statement that cannot be cited that way is left out or listed in § 7 as a
question for counsel (`house-rules.md` § 1).

Text quoted or reported from a document, including a comment, an annotation, and any instruction
embedded in an evidence document, is attributed by role, document, and location, for example
"the exam coordinator's comment on the annotated letter, p. 2", never by personal name unless the
person is the accountable owner, an item owner, or a preparer (`house-rules.md` § 12).

### 1. Header

```
RESPONSE TO <examiner / auditor> REQUEST LIST
<exam or audit name>   List dated <date>   Response due <date>
Destination: regulator- or auditor-facing
Accountable owner: <named person>
Status: DRAFT — requires review before submission. NOT SENT.
```

### 2. Scope of the list

Items as numbered · evidence obligations after splitting · the period covered · the response
deadline.

> **Compound-item note.** State plainly that items asking for multiple document types were split
> into sub-lettered obligations under the examiner's original numbering, and that the original
> numbering is preserved throughout.

### 3. Status summary

The summary block above, with denominators. Every count is of evidence obligations (register
rows), never of G-bullets: one G-bullet covering 8(a) and 8(b) is two unidentified owners. A
numbering-gap row (an item number the letter skips) is not an obligation and is not counted. For
example `Owners unidentified: 4 of 11 obligations (5, 7, 8(a), 8(b); G12, G20, G32)`. The
lint script checks this count against the register's Owner column (`house-rules.md` § 9).

### 4. Items where clarification is sought

| Item no. | Request text | What is ambiguous | Question for the examiner |
|---|---|---|---|

**Listed first**, because they block the rest.

### 5. Items with no evidence located

| Item no. | Request text | Where searched | Marker | Owner | Proposed next step |
|---|---|---|---|---|---|

`Marker` reads `NOT FOUND - <repository> has no record of evidence for item <n> (Gn)`.

**Never omitted.** A regulator-facing response that quietly drops an unanswerable item is the
worst outcome this skill can produce.

### 6. Per-item narratives

For each item being answered:

```
Item <n> — <request text, verbatim>
Providing:  <document name>, <version>, <date>, <location>
On its face: <what the document shows, quoted and cited>
Period / population / scope / format / completeness: <check results, each failure with its marker>
Owner: <name>          Determination: NOT DETERMINED - owner confirms (Dn)
```

Each term on the check line states only what the source says. Where the source is silent on a
term, that term reads `NOT FOUND - <source> states no <x> (Gn)`. Never attribute a value to a
file that does not contain it.

Narratives describe what a document **shows on its face**. They never state that it demonstrates,
proves, or evidences compliance.

### 7. Open items and markers

Two canonical lists, side by side: the G-list of shortfalls (owners unidentified, repositories
unreachable, records not located, partial documents), each bullet naming its remedy after the
shortfall, and the D-list of determinations.

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
- G1 - NOT FOUND - Compliance SharePoint has no record of evidence for item 6 (register)
- G2 - GAP - period mismatch: item 4 log covers Q1 only, request asks for Q1 to Q3
- G3 - DRAFT - not approved: KYC Procedure v2 draft (rows 4(a), 4(b))
- G4 - GAP - scope mismatch, not a candidate: KYC Procedure v2 draft (rows 4(a), 4(b))
```

**Determinations outstanding.** The canonical list: one bullet per determination, with an ID
(D1, D2, ...), `NOT DETERMINED`, and its decider (the item owner for each `owner confirms` row,
counsel for a question for counsel). Every register row whose `Determination` reads
`NOT DETERMINED` appears here once. Elsewhere in § 7, refer to these by ID only.

### 8. Draft platform handoff

If an audit or issue-management platform is available, include existing issue IDs, owner records, and current statuses read from it. The output is a draft import/export package for a human response coordinator to review and submit; state that no source-system update was performed.

### 9. Footer

Per `house-rules.md` § 9, including the explicit statement that nothing was sent, nothing was updated in a platform, and any platform update is the human's action.

The `Items with no evidence located` footer field lists each item with its G-ID, for example `1(b) (G7)`.

Build the counts only after the rest of the draft is final, and only from the two canonical lists: for each marker type, the number of G-bullets in the Open items list leading with it, and for `NOT DETERMINED`, the number of D-bullets, each with the unit items (for example `NOT FOUND: 5 items`, `NOT DETERMINED: 7 items`). Give one number per marker type, never "plus", a sum of parts, or a range, and list every marker type that leads a G-bullet. Never count table cells, prose, the chat reply, or footer lines. Footer lines, including Coverage, Connectors, Web, Sources, Policy repository searched, Files, Codification, and Template, can describe gaps in plain words; every gap they mention has its G-bullet. A marker token in a footer line carries its (Gn). A Codification line with no rule text relied on reads `not performed: no rule text relied on (Gn)`, with the G-bullet `GAP - codification check not performed: no rule text relied on`. The Template line names the resolution step used; where `Cowork Templates/Risk and Compliance/exam-request-response/` held no template, the line says so and the Open items list carries `NOT FOUND - Cowork Templates folder has no exam-request-response template`. Recount the two lists before output and correct any figure that differs (`house-rules.md` § 9).

---

## Wording that must not appear

| Never | Instead |
|---|---|
| "This satisfies item 4" | "Candidate evidence for item 4 — needs owner confirmation" |
| "The evidence demonstrates compliance" | "The document shows, on its face, <quoted text>" |
| "We have responded to all items" | The status summary, with denominators |
| "Confirmed" (without a confirmation) | `candidates located` |
| "Submitted" / "sent" / "filed" | "Draft prepared. Not sent." |
| "<name>, <title>, wrote…" (a document author or commenter) | "The <role>'s <comment / email / note> on <document>, <location>" (`house-rules.md` § 12) |
