# Read-Across — Default Outline

Used when no template is named in the request and none is present in
`Cowork Templates/Risk and Compliance/enforcement-action-review/`.

**A template replaces layout, never gates.** The admission posture and the hypothesis framing
survive every template.

**One gap list.** Every shortfall in this artifact (anything absent, unretrieved, partial,
mismatched, rejected, unverified, unperformed, unconfigured, or undated) is recorded exactly
once in the Open items list (§ 9), as its own bullet with an ID (G1, G2, ...), leading with its
marker, one shortfall per bullet. **Marker cells in this outline:** the § 2 Date and Effective
Date rows and the admission-posture line where posture was not established; the § 4 `Retrieved`,
`Codification check`, and `What the rule text actually requires` cells; the § 5 Deadline cells;
the § 6 absence bullets; the § 8 control-mapping outcomes and `Determination` cells; the § 9
`Not located` and `Status` lines; the workbook `Rule retrieved`, `Determination`, and `Marker`
cells. A marker cell carries its marker followed by its G-ID in brackets, for example `NOT FOUND
- order states no calendar date (G1); "Within 90 days of the Effective Date"`. Every other cell
is a fact cell: it states what the source says in plain words (for example `none stated in
<source>`) and carries no marker token. A search that returns nothing relevant is a gap: `NOT
FOUND`, with its G-bullet. A marker token written anywhere outside the Open items list,
including prose, the chat reply, and the footer, carries its (Gn) right after the marker phrase,
and `NOT DETERMINED` carries its (Dn). Ordinary prose, the chat reply, handling notes, and
footer lines can mention a gap in plain words; every gap mentioned anywhere has its G-bullet
(`house-rules.md` § 4).

**Each determination is its own row or bullet.** Every owner determination listed in this
artifact carries its own marker. Never one blanket marker line over a list (`house-rules.md` § 9).

**One canonical list.** Every `NOT DETERMINED` item appears exactly once, with an ID (D1, D2,
...), in the Determinations outstanding list (§ 9), and the footer's `NOT DETERMINED` figure
is the number of bullets there. Each D-bullet holds exactly one decision; a secondary
question gets its own D-number.
No D-bullet contains " and ", " or ", "/", or a second question mark joining two decisions;
split any that does. Undecided matters go there, never in the Open items list. A summary list never groups
several determinations or gaps under one marker bullet: it refers to the canonical lists by ID
with no marker of its own (not counted).

---

## Memo (`.docx`)

### 1. Header

```
ENFORCEMENT ACTION READ-ACROSS
<agency> v. <respondent>   <docket/file no.>   <date>
Destination: internal working paper | committee/board
Prepared: <date>    Preparer: <name>
Status: DRAFT — observations for assessment. Not a determination about this firm.
```

### 2. The order

| Field | Value |
|---|---|
| Agency | |
| Respondent | |
| Docket / file number | |
| Date | Order date; where the order states none: `NOT FOUND - order states no date (Gn)`, then the explanation |
| Effective Date | Calendar date; where the order states none: `NOT FOUND - order states no calendar date for the Effective Date (Gn)`, then the explanation (for example how the order defines it) |
| Type | Consent order · CMP · cease and desist · settlement · litigated decision · DPA |
| **Admission posture** | **Quoted verbatim from the order** |
| Retrieved | Date · route · coverage |

> **Register note.** Reproduce the admission language here and state the register the memo uses:
> "The order resolves without admission or denial. Conduct below is described as **alleged**
> throughout."
>
> Where posture was not established: `GAP - admission posture not established (Gn). Alleged
> register used throughout.`

### 3. Alleged conduct

| ¶ | What the order alleges | Rule cited |
|---|---|---|

Quoted, with paragraph citations, in the register the posture requires.

The chat reply uses the same register. Every sentence about the respondent's conduct, in the
chat reply as well as the memo, reads "The order alleges that ...". A summary bullet list of
conduct starts with "The order alleges:" and each bullet keeps the alleged register.

### 4. Rules cited — retrieved separately

| Rule as cited in the order | Retrieved | Tier | Codification check | What the rule text actually requires |
|---|---|---|---|---|

List every authority the order cites, jurisdictional and statutory cites included, never a subset.

Cited-as-violated · cited-as-background · supervisory expectation invoked without a rule — kept
distinct. Any rule not retrieved is `NOT RETRIEVED - <source> (Gn)` where a request failed, or
`GAP - <source> retrieval not attempted (Gn)` where none was made, and its requirements are not
characterised.

Before filling `What the rule text actually requires`, retrieve the rule's definitions section.
If the definitions section is not retrieved, quote only the operative act, with the
covered-entity term (for example "the institution") replaced by `[covered entity]` at every
occurrence, and add the G-bullet `NOT RETRIEVED - <source> did not return <definitions section>`
where a request failed, or `GAP - <source> retrieval not attempted` where none was made
(`house-rules.md` § 2). For example, 12 CFR 1005.17(b)(1) quoted while 12 CFR 1005.2 is not
retrieved shows `[covered entity]` wherever the text names the institution.

### 5. Required corrective actions

| Action | Deadline | Scope | One-time or ongoing |
|---|---|---|---|
| <action, quoted with paragraph> | <calendar date>, or for a deadline relative to an undated Effective Date: `NOT FOUND - order states no calendar date (Gn); "Within 90 days of the Effective Date"` | <scope> | <one-time / ongoing> |

Every Deadline cell relative to an undated Effective Date ("Within 90 days of the Effective Date", "Ongoing from the Effective Date", "From Effective
Date", "5 years from the Effective Date") leads with
`NOT FOUND - order states no calendar date (Gn); ` and then the quoted relative wording. The undated
Effective Date is one G-bullet in § 9 naming the § 2 row and each such Deadline row.

Plus penalties, restitution, monitorship, reporting, and board-level obligations.

### 6. What the order does not say

Root cause · control design · detection interval · population affected — where absent, stated as
absent. **Never filled in.**

Each absent point is its own bullet that leads with `NOT FOUND - the order states no <what> (Gn)`,
and has its G-bullet in § 9. Every bullet in this section leads with that marker, including a
population, amount, or split the order does not give, for example
`NOT FOUND - the order states no split of affected consumers between the two allegations (G14)`.

### 7. Read-across themes

Each theme is a **question**, anchored to the order and the rule:

```
Theme <n>: <question the firm can test itself against>
Anchored to: ¶¶ <n>, rule <citation>
Pattern:     <the control-failure pattern, as a question or a generic pattern>
```

**Alleged register (hard stop).** The `Pattern:` line describes a control-failure pattern as a
question or a generic pattern. Any reference to the respondent's conduct, duration, or facts
stays in the alleged register: "the order alleges ...".

### 8. Control mapping

| Theme | Control / policy located | Version | Approval | Owner | Addresses | Does not address | Determination |
|---|---|---|---|---|---|---|---|

Every `Determination` reads `NOT DETERMINED - <function> assesses (Dn)`.

Outcomes: located · `NOT FOUND — no control located for <theme>` ·
`NOT RETRIEVED — <repository>` · `GAP — control version not established` ·
`NEEDS FEED — GRC control library`.
Each outcome marker carries its (Gn).

`Addresses` states only the topical link, for example "covers overdraft opt-in consent records,
the subject of Theme 2". It never says that the order or a cited rule requires, applies to, or
reaches a firm control, document, or entity.

**Themes with no located control are listed separately and prominently.** That is the finding the
read-across exists to produce.

### 9. Observations for assessment

```
Observation <n>
Theme:        <theme>
Located:      <what was found, cited>
Not located:  NOT FOUND - <source> has no record of <what was searched for> (Gn)
For assessment by: <function>
Status: NOT DETERMINED (Dn)
```

Each observation carries its own status line. Any statement about which of the firm's entities,
affiliates, accounts, products, or activities a cited rule covers or does not cover is proposed
applicability: `NOT DETERMINED` with the decider, the reasoning, and a citation to the retrieved
provision that defines coverage. If that provision was not retrieved, write `NOT RETRIEVED - <source> (Gn)` only if a request was made and failed, otherwise
`GAP - <source> retrieval not attempted (Gn)`
naming it, with the same marker as its G-bullet, and the reasoning reads exactly `none - defining provision not retrieved` and
nothing else (`house-rules.md` § 2).

**Determinations outstanding.** The canonical list: one bullet per determination, with an ID
(D1, D2, ...), `NOT DETERMINED`, and the assessing function as the decider. Every
`NOT DETERMINED` in § 8 and § 9 appears here once; a theme's control-mapping row and its
observation are one item.

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
- G1 - NOT FOUND - order states no calendar date for the Effective Date (§ 2; § 5 deadline rows 1 to 4)
- G2 - NOT FOUND - OneDrive Compliance folder has no record of an overdraft opt-in control (Theme 2)
```

### 10. Footer

Per `house-rules.md` § 9.

Build the counts only after the rest of the draft is final, and only from the two canonical lists: for each marker type, the number of G-bullets in the Open items list leading with it, and for `NOT DETERMINED`, the number of D-bullets, each with the unit items (for example `NOT FOUND: 5 items`, `NOT DETERMINED: 7 items`). Give one number per marker type, never "plus", a sum of parts, or a range, and list every marker type that leads a G-bullet. Never count table cells, prose, the chat reply, or footer lines. Footer lines, including Coverage, Connectors, Web, Sources, Policy repository searched, Files, Codification, and Template, can describe gaps in plain words; every gap they mention has its G-bullet. A marker token in a footer line carries its (Gn). A Codification line with no rule text relied on reads `not performed: no rule text relied on (Gn)`, with the G-bullet `GAP - codification check not performed: no rule text relied on`. The Template line names the resolution step used; where `Cowork Templates/Risk and Compliance/enforcement-action-review/` held no template, the line says so and the Open items list carries `NOT FOUND - Cowork Templates folder has no enforcement-action-review template`. Recount the two lists before output and correct any figure that differs (`house-rules.md` § 9).

---

## Control-gap table (`.xlsx`)

| Column | Notes |
|---|---|
| Theme ID | |
| Theme (as a question) | |
| Order ¶ | |
| Rule cited | |
| Rule retrieved | Yes / `NOT RETRIEVED (Gn)` / `GAP - retrieval not attempted (Gn)` |
| Control located | Name or ID |
| Control version / approval | |
| Control owner | |
| Addresses | |
| Does not address | |
| Determination | `NOT DETERMINED - <function> assesses (Dn)` |
| Marker | |
| Source | Order ¶ · repository · retrieval date |

### Summary block

```
Themes identified:              n
  control located               n
  NOT FOUND — no control        n   ← the headline finding
  GAP — version not established n
  NOT RETRIEVED — repository    n
Rules cited in the order:       n
  retrieved and read            n
  NOT RETRIEVED                 n
  GAP - retrieval not attempted n
```

---

## Wording that must not appear

| Never | Instead |
|---|---|
| "The respondent failed to…" (no-admission order) | "The order alleges that the respondent…" |
| "The firm has a gap in…" | "Theme n: NOT FOUND - <repository> has no control for <question> (Gn). NOT DETERMINED - <function> assesses (Dn)" |
| "We are exposed to…" | "Observation n — for assessment by <function>" |
| "This is a violation of…" | "The order cites <rule>. The rule text requires <retrieved text>" |
| "The root cause was…" | "NOT FOUND - the order states no root cause (Gn)" |
| "The firm should self-report" | Out of scope. A determination for counsel |
| "<name>, <title>, wrote…" (a document author or commenter) | "The <role>'s <comment / email / note> on <document>, <location>" (`house-rules.md` § 12) |
