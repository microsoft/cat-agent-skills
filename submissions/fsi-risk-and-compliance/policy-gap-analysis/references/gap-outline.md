# Gap Analysis — Default Outline

Used when no template is named in the request and none is present in
`Cowork Templates/Risk and Compliance/policy-gap-analysis/`.

**A template replaces layout, never gates.**

**One gap list.** Every shortfall in this artifact (anything absent, unretrieved, partial,
mismatched, rejected, unverified, unperformed, unconfigured, or undated) is recorded exactly
once in the Open items list (§ 7), as its own bullet with an ID (G1, G2, ...), leading with its
marker, one shortfall per bullet. **Marker cells in this outline:** the § 2 `Codification check`
and `Approval status` fields; the scope-note `Provision relied on` and `Determination` cells;
the coverage-table `Coverage` cell, the `Policy section` cell of a requirement row, and the
`Marker` cell; the § 5 `Policy:` line; the § 6 items not scored. Where no row can be scored, the headline reads
`No row scored: <reason> (Gn)` with no zero counts (`house-rules.md` § 4). The `Exemption` cell and the
`Policy section` cell of a non-scored row are fact cells. A marker cell carries its marker
followed by its G-ID in brackets, for example `NOT FOUND - policy has no matching section (G1)`.
Every other cell is a fact cell: it states what the source says in plain words (for example
`none stated in <source>`) and carries no marker token. A search that returns nothing relevant
is a gap: `NOT FOUND`, with its G-bullet. A marker token written anywhere outside the Open items
list, including prose, the chat reply, and the footer, carries its (Gn) right after the marker
phrase, and `NOT DETERMINED` carries its (Dn). Ordinary prose, the chat reply, handling notes,
and footer lines can mention a gap in plain words; every gap mentioned anywhere has its G-bullet
(`house-rules.md` § 4).

**Each determination is its own row or bullet.** Every owner determination listed in this
artifact carries its own marker. Never one blanket marker line over a list (`house-rules.md` § 9).

**One canonical list.** Every `NOT DETERMINED` item appears exactly once, with an ID (D1, D2,
...), in the Determinations outstanding list (§ 7), and the footer's `NOT DETERMINED` figure
is the number of bullets there. Each D-bullet holds exactly one decision; a secondary
question gets its own D-number.
No D-bullet contains " and ", " or ", "/", or a second question mark joining two decisions;
split any that does. Undecided matters go there, never in the Open items list. A summary list never groups
several determinations or gaps under one marker bullet: it refers to the canonical lists by ID
with no marker of its own (not counted).

---

## Coverage table (`.xlsx`)

One row per **discrete requirement**. Compound requirements are split; the citation stays exact.

| Column | Notes |
|---|---|
| Req ID | `<citation>-<n>` where a section yields several |
| Citation | To the sub-paragraph the text supports |
| Requirement text | **Verbatim.** Never paraphrased. Where the rule's definitions section is not retrieved, the covered-entity term reads `[covered entity]` and the G-bullet names the definitions section: `NOT RETRIEVED - <source> (Gn)` only if a request was made and failed, otherwise `GAP - <source> retrieval not attempted (Gn)` (`house-rules.md` § 2) |
| Obligation type | `requirement` · `permission` · `safe harbour` · `definition` |
| Condition / threshold | As printed |
| Exemption | Fact cell: as printed, or `none stated in <citation>` in plain words, with no marker; entity terms in quoted text follow `[covered entity]` (`house-rules.md` § 2). Three forms only (hard stop): verbatim quote with citation; `none stated in <citation>`; or `NOT DETERMINED - <decider> decides (Dn)`, where whether the firm can use the exemption is for the compliance owner and only its legal meaning is for counsel. Never "applies only to", "limited to", "excludes", or any other interpretation |
| Coverage | `covered` · `partial` · `not found` · `conflicts` · `NOT DETERMINED (Dn)` |
| Policy section | Section number and page. A requirement row with no matching policy text after the whole policy is searched: `NOT FOUND - policy has no matching section (Gn)`. A non-scored row (permission, safe harbour, definition, exemption): `-` with `(not scored)`, never `NOT FOUND` |
| Policy text | **Verbatim.** Never paraphrased |
| What is not addressed | Required whenever coverage is `partial`. Form: `<what is missing> (Gn)`. Every sentence in this cell ends with the row's (Gn), repeated here even when the `Coverage` or `Marker` cell already carries it |
| Suggested edit | Marked `PROPOSED DRAFTING — not approved` |
| Marker | Where the row carries one. Markers from `house-rules.md` only; never a new one such as `FORTHCOMING` |
| Source | Instrument · retrieval date · route · coverage. For a final rule not yet effective, add: forthcoming change, effective <date> |

Only rows with `Obligation type = requirement` are scored for coverage. Permissions, safe
harbours, and definitions are recorded and excluded from the counts — state that, in the
approved fact wording, which needs no ID: "<n> non-requirement rows (definitions, exemptions) are recorded for reference and excluded from the counts."

The Exemption cell is a fact cell (`none stated in <citation>`). A `NOT FOUND` in a requirement
row's Policy section cell does not take the row out of scoring. Only the markers under `Not scored` do.

### Summary block

```
Requirements analysed:          n
  covered                       n
  partial                       n
  not found                     n
  conflicts                     n
Not scored (markers):           n
  NOT RETRIEVED — reg text      n
  GAP - reg text not attempted  n
  GAP — policy version          n
  NOT DETERMINED                n
Non-requirement rows recorded:  n   (permissions, safe harbours, definitions)
```

Every percentage carries its denominator. Marker rows stay visible and never enter a count.

---

## Memo (`.docx`)

### 1. Header

```
POLICY-TO-REGULATION GAP ANALYSIS
<policy name> v<version>  against  <regulation citation>
Destination: internal working paper | committee/board | regulator- or auditor-facing
Prepared: <date>    Preparer: <name>    Status: DRAFT — for policy owner review
```

### 2. Documents analysed

**Regulation**

| Field | Value |
|---|---|
| Agency · title · citation | |
| Type and authority tier | |
| Sections in scope | |
| Retrieved | Date · route · coverage |
| Codification check | `up_to_date_as_of` · `latest_issue_date` · result, or `GAP - codification check not performed: <reason> (Gn)` / `NOT RETRIEVED - <source> did not return (Gn)` |

**Policy**

| Field | Value |
|---|---|
| Name · version | |
| Approval status · approval date | An unapproved draft shows `DRAFT - not approved (Gn)`, one G-bullet for the document |
| Control of record | The approved current version: `<doc> v<x>, approved <date> (<location>)`, or `NOT FOUND - <repository> has no record of an approved version of <doc> (Gn)`. Required when the policy analysed is a draft or superseded; a fact, never a D-bullet |
| Owner | |
| Scope: entities, products, jurisdictions | The policy's scope clause, quoted verbatim with section and page |
| Location | |

> **Scope note.** Start from the policy's own scope. Quote its scope clause verbatim, with
> section and page. That quotation is a fact and stays unmarked.
>
> Then list each point about what the rule covers or does not cover as its own row, including
> the firm itself, each in-scope entity, that entity's accounts as a separate point, and each affiliate the policy excludes:
>
> | # | Coverage point (as a question) | Provision relied on | Reasoning | Determination |
> |---|---|---|---|---|
>
> - `Determination` is `NOT DETERMINED` on every row, with the compliance owner as the decider.
> - `Provision relied on` cites the retrieved provision that defines coverage (for example the
>   rule's definition of "covered financial institution"). Retrieve it before writing any
>   reasoning. If it was not retrieved, the cell reads `NOT RETRIEVED - <source> (Gn)` only if a request was
>   made and failed, otherwise `GAP - <source> retrieval not attempted (Gn)`, naming the provision
>   with the same marker as its G-bullet, and
>   `Reasoning` reads exactly `none - defining provision not retrieved` and nothing else. No rule
>   text bearing on coverage for that point is quoted anywhere (`house-rules.md` § 2).
> - No sentence in the note states what the rule covers, binds, or reaches outside these rows.
>   No likelihood or hedge word (probably, presumably, likely, unlikely, appears to, seems, would likely, should be)
>   appears in the note (`house-rules.md` § 2).
>
> Where the quoted policy scope does not reach an entity, product, or jurisdiction named in a
> coverage point, requirement rows for that point cannot be `covered` regardless of their text.

### 3. Method

Two sentences: requirements decomposed to discrete obligations; both sides quoted verbatim;
coverage states only; no compliance conclusion.

### 4. Coverage summary

The summary block above, reproduced, with denominators. Above it, one headline line in the
`house-rules.md` § 4 form, for example
`covered 3 of 9; partial 4 of 9 (G11 to G14); not found 2 of 9 (G9, G10); conflicts 1 of 9 (G8)`.

### 5. Gaps and conflicts

Ordered `conflicts` → `not found` → `partial`. Each entry:

```
Req <ID> — <citation>
Requirement:   "<verbatim>"
Policy:        "<verbatim>" (§ <n>, p<n>)   or   NOT FOUND - policy has no matching section, whole policy searched (Gn)
Coverage:      <state> (Gn)                  (Gn) for every state except covered
Not addressed: <what is missing> (Gn)          (partial only; every sentence ends with the row's Gn)
Suggested:     "<proposed language>"  — PROPOSED DRAFTING — not approved
```

Where an entry explains why a policy section was matched to a requirement, it states only the
topical link, for example "addresses beneficial-ownership verification, the subject of
Req 1010.230-2". It never says that a requirement requires, applies to, or reaches a firm
document or entity.

### 6. Items not scored

Every marker row with its reason and remedy. `NOT RETRIEVED` and `GAP - <source> retrieval not
attempted` requirements are listed here, never silently dropped.

Handling notes can describe gaps in plain words. Each gap they mention has its G-bullet in § 7:
a record looked for and not located is `NOT FOUND`, an incomplete or partial document is `GAP`;
an open question (for example who made a change to a document) is a D-bullet with its decider.

### 7. Determinations outstanding

What a qualified owner must decide before this analysis is used. Each determination is its own
bullet with its own `NOT DETERMINED` marker and decider. Always includes: whether the policy's
controls are **adequate**, which is not a coverage question. It also lists, one bullet each,
every coverage point from the scope note and every other open question in the memo. This is
the canonical list: each bullet has an ID (D1, D2, ...) and the compliance owner as the decider
unless this outline names another.

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
- G1 - NOT FOUND - policy has no matching section for Req 1010.230-3 (coverage table)
- G2 - GAP - partial: policy v3.1 extract omits Appendix B
- G3 - DRAFT - not approved: AML Policy v3.2 (§ 2 Approval status)
```

Every `partial`, `not found`, and `conflicts` row has its G-bullet; the row stays in the coverage
counts.

### 8. Footer

Per `house-rules.md` § 9.

Build the counts only after the rest of the draft is final, and only from the two canonical lists: for each marker type, the number of G-bullets in the Open items list leading with it, and for `NOT DETERMINED`, the number of D-bullets, each with the unit items (for example `NOT FOUND: 5 items`, `NOT DETERMINED: 7 items`). Give one number per marker type, never "plus", a sum of parts, or a range, and list every marker type that leads a G-bullet. Never count table cells, prose, the chat reply, or footer lines. A footer line giving coverage-state counts uses the § 4 headline form, for example `covered 3 of 9; partial 4 of 9 (G11 to G14); not found 2 of 9 (G9, G10); conflicts 1 of 9 (G8)`; marker counts stay bare. Footer lines, including Coverage, Connectors, Web, Sources, Policy repository searched, Files, Codification, and Template, can describe gaps in plain words; every gap they mention has its G-bullet. A marker token in a footer line carries its (Gn). A Codification line with no rule text relied on reads `not performed: no rule text relied on (Gn)`, with the G-bullet `GAP - codification check not performed: no rule text relied on`. The Template line names the resolution step used; where `Cowork Templates/Risk and Compliance/policy-gap-analysis/` held no template, the line says so and the Open items list carries `NOT FOUND - Cowork Templates folder has no policy-gap-analysis template`. Recount the two lists before output and correct any figure that differs (`house-rules.md` § 9).

---

## Wording that must not appear

| Never | Instead |
|---|---|
| "The policy is compliant with…" | "Coverage: covered — requirement addressed at § n" |
| "The firm is in violation of…" | "Coverage: not found — no policy text located" |
| "This satisfies the requirement" | "Coverage: covered" with both quotations |
| "Adequate" / "sufficient" / "effective" | `NOT DETERMINED — policy owner decides` |
| "We recommend the firm adopt…" | "PROPOSED DRAFTING — not approved, for owner review" |
| "<affiliate> is also a covered institution under <rule>" | "Proposed applicability: <reasoning>, <citation>", marked `NOT DETERMINED` for the compliance owner |
| "The rule reaches <entity or accounts>" / "<entity> is not covered" | A coverage-point row in the scope note, marked `NOT DETERMINED` for the compliance owner, or, where the defining provision was not retrieved, `NOT RETRIEVED - <source> (Gn)` if a request failed, otherwise `GAP - <source> retrieval not attempted (Gn)` |
| "<policy> presumably / likely / appears to govern" | The open question, with `NOT DETERMINED` and its decider |
| "<name>, <title>, wrote…" (a document author or commenter) | "The <role>'s <comment / email / note> on <document>, <location>" (`house-rules.md` § 12) |
