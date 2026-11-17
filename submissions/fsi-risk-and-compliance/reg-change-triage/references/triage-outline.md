# Triage Brief — Default Outline

Used when no template is named in the request and none is present in
`Cowork Templates/Risk and Compliance/reg-change-triage/`.

**A template replaces layout, never gates.** If a customer template has no place for a citation,
marker, date, or owner field required here, add it.

**One gap list.** Every shortfall in this artifact (anything absent, unretrieved, partial,
mismatched, rejected, unverified, unperformed, unconfigured, or undated) is recorded exactly
once in the Open items list (§ 9), as its own bullet with an ID (G1, G2, ...), leading with its
marker, one shortfall per bullet. **Marker cells in this outline:** the § 2 `Coverage` row; the
§ 3 date ladder rows; the PROPOSED line after the header block; the § 4 `Prior text` cell and
the codification check statement; the § 5 `Bites on` cell; the § 5 `Binds whom` cell where the definitions section is not
retrieved and the § 5 and tracker `Status` cell where it reads `PROPOSED - not in force`; the §
6 `Text relied on` and `Determination` cells and the ambiguity bullets; the § 7 outcomes and
`Approval status` cell; the § 8 `Suggested owner` and `Basis for suggestion` cells; the tracker date, `Suggested owner`,
`Determination`, and `Marker` columns. A marker cell carries its marker followed by its G-ID in brackets, for example
`NOT FOUND - instrument states no compliance date (G1)`. Every other cell is a fact cell: it
states what the source says in plain words (for example `none stated in <source>`) and carries
no marker token. A search that returns nothing relevant is a gap: `NOT FOUND`, with its
G-bullet. A marker token written anywhere outside the Open items list, including prose, the chat
reply, and the footer, carries its (Gn) right after the marker phrase, and `NOT DETERMINED`
carries its (Dn). Ordinary prose, the chat reply, handling notes, and footer lines can mention a
gap in plain words; every gap mentioned anywhere has its G-bullet (`house-rules.md` § 4).

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

## Brief (`.docx`)

### 1. Header

```
REGULATORY CHANGE TRIAGE — <instrument short name>
Destination: internal working paper | committee/board | regulator- or auditor-facing
Prepared: <date>    Preparer: <name>    Status: DRAFT — for compliance owner review
```

**If type is Proposed Rule**, the `PROPOSED` line goes immediately after the whole header block
above (title, Destination, Prepared, and Status lines), before any other content, and never
between the title and those lines. The top of the brief reads, in this order:

```
<title line, as above>
Destination: internal working paper
Prepared: 2026-10-16    Preparer: <name>    Status: <status, as above>
PROPOSED - not in force (G1). Comment period closes 2026-11-12. No obligation below is currently binding.
```

### 2. Instrument identification

| Field | Value |
|---|---|
| Agency | |
| Title | With the definitions section not retrieved: FR Doc number and short name, for example `FR Doc. 2026-18842 (CDD amendments)` (`house-rules.md` § 2) |
| Type | **Final rule / Proposed rule / Guidance / Bulletin / Order** |
| Authority tier | 1–6 |
| Identifier | FR document number · docket · RIN · CFR citation · bulletin number |
| Retrieved | Date · route (connector / direct / browser / upload) |
| Coverage | `complete`, or `GAP - partial: <what is missing> (Gn)` for partial, extract, or snippet coverage, or `NOT RETRIEVED - <source> <reason> (Gn)` where unavailable. Must agree with the footer Coverage value. The cell is `complete` alone, or a marker with its (Gn); a caveat such as "(annex not opened)" has its own G-bullet, and the cell carries its marker and (Gn) |

### 3. Date ladder

| Date | Value |
|---|---|
| Published | |
| Effective | |
| Compliance date | |
| Mandatory compliance date | |
| Comment deadline | |

Each absent date shows `NOT FOUND - instrument states no <which> date (Gn)`. Never inferred.

Every row is always shown, for every instrument type. A row with no calendar date carries
`NOT FOUND - instrument states no <which> date (Gn)` first, and any explanation is written after the
marker, for example `NOT FOUND - instrument states no comment deadline date (G2); final rule, no
comment period`. Never write "not applicable" or "n/a" in a ladder row.

A row with only relative or proposed wording has no stated date and still shows that marker. The
wording is quoted after the marker on the same row, for example the effective-date marker
followed by `; proposed: "effective 12 months after its publication in the Federal Register"`.
The wording never replaces the marker.

Never assert that a final rule does not exist. Approved wording:
`The proposal ties the effective date to a later event: "<quoted text>" (Gn).` (`house-rules.md` § 4).

### 4. What changed

Per affected CFR part or section:

| Section | Prior text | New text | Nature of change |
|---|---|---|---|

Both sides quoted verbatim. Where prior text could not be established →
`GAP - prior text not established (Gn)`.
When quoting prior codified text, a paragraph heading or defined term that is itself the
covered-entity term (for example the heading "Covered financial institution") is also
bracketed as `[covered entity]` while the definition is not retrieved (`house-rules.md` § 2).
Every quote in the `Prior text` and `New text` cells follows `[covered entity]`
(`house-rules.md` § 2), whether it comes from codified text, rule text, or the preamble: while
the definitions section is not retrieved, "the institution", "a bank", "covered financial
institution", and every other entity term inside the quotation marks reads `[covered entity]`.
For example, the preamble's "did not require [covered entity] to record the verification
method used or its result", never "did not require the institution to ...".

**Codification check:** state the eCFR title, its `up_to_date_as_of`, its `latest_issue_date`,
and the result — no intervening final rule, or `PENDING CODIFICATION — <FR number>, effective
<date>`.
If the check is not performed or is incomplete, the codification check statement reads
`GAP - codification check not performed: <reason> (Gn)` or
`NOT RETRIEVED - <source> did not return (Gn)`, and the same shortfall is a G-bullet in § 9.

### 5. Obligations

| # | Obligation | Binds whom | Trigger / threshold | Bites on | Citation | Tier | Status |
|---|---|---|---|---|---|---|---|

`Status` is `in force`, `PROPOSED — not in force`, or `forthcoming — effective <date>`.
A `PROPOSED - not in force (Gn)` status cites the one G-bullet for the instrument, which names
every obligation row it applies to (`house-rules.md` § 4).
Every `Bites on` and compliance cell uses the DATES compliance or full-compliance date that
covers the row. The effective date is used only where the DATES section names it as the
compliance date for that row. Never infer a compliance date from the effective date. With no
such date, the cell follows `house-rules.md` § 5:
`NOT FOUND - <source> states no calendar date (Gn)`.
Exemption rows follow the same rule: the `Bites on` cell uses the DATES compliance date, or
`NOT FOUND - instrument states no compliance date for <exemption> (Gn)`. Never the effective date.
Every `Bites on` cell with a date carries its DATES citation, for example
`2027-03-01 (DATES, FR Doc. 2026-18842 p. 1)` (`house-rules.md` § 5).

Before quoting an obligation, retrieve the rule's definitions section. If it is not retrieved,
quote only the operative act with the covered-entity term replaced by `[covered entity]`,
`Binds whom` reads `NOT RETRIEVED - <definitions section> (Gn)` only if a request was made and
failed, otherwise `GAP - <definitions section> retrieval not attempted (Gn)`, and the G-bullet
names the definitions section with the same marker (`house-rules.md` § 2).

Thresholds quoted exactly. Exemptions and exclusions carried in their own rows or a dedicated
column — never dropped.

Whether an exemption is available to the firm is an applicability question: it goes to § 6 as
`NOT DETERMINED` with the reasoning, never with a likelihood word.

### 6. Proposed applicability

| Obligation # | Proposed scope | Reasoning | Text relied on | Determination |
|---|---|---|---|---|

Every row's `Determination` reads `NOT DETERMINED — compliance owner decides`.

The `Reasoning` cell gives the reasoning and names any missing fact (in its own bullet where the
defining provision is not retrieved), never a likelihood or hedge
word (probably, presumably, likely, unlikely, appears to, seems, would likely, should be). Exemption rows follow the same
rule.

Every statement about which entities, affiliates, accounts, products, or activities the rule
covers or does not cover, including the firm itself, is a row here, never a plain statement
elsewhere in the brief. `Text relied on` cites the retrieved provision that defines coverage
(for example the rule's definition of "bank" or "covered financial institution"). If that
provision was not retrieved, `Text relied on` reads `NOT RETRIEVED - <source> (Gn)` only if a request was made and failed, otherwise
`GAP - <source> retrieval not attempted (Gn)`, naming the
provision with the same marker as its G-bullet, and
`Reasoning` reads exactly `none - defining provision not retrieved` and nothing else. No rule
text bearing on coverage for that point (for example which part the provision sits in, or the
word it uses for the entities it binds) is quoted anywhere (`house-rules.md` § 2).

Ambiguities in scope language get their own subsection. **This is the most valuable part of the
brief — do not resolve them.**

In that subsection, each ambiguity is its own bullet: the quoted scope language, the open
question, and `NOT DETERMINED` with the compliance owner as the decider. Each bullet holds one question; a
second question (for example "and under what letter?") is its own bullet. No likelihood or hedge
word (probably, presumably, likely, unlikely, appears to, seems, would likely, should be) appears there or anywhere
else about how an ambiguity would resolve.

### 7. Candidate affected policies

| Obligation # | Policy | Version | Approval status | Approval date | Location | Why candidate |
|---|---|---|---|---|---|---|

Outcomes: listed candidate · `NOT FOUND - <repository> has no record of a policy for <obligation>` · `NOT RETRIEVED — <repository>` ·
`GAP — policy version not established` · `NEEDS FEED — policy repository or DMS` ·
`GAP - scope mismatch, not a candidate: <doc>` (one per rejected document).
Each outcome marker carries its (Gn). A `Version` or `Approval date` the document does not
print reads `NOT FOUND - <doc> states no <version / approval date> (Gn)`, never "none stated"
(`house-rules.md` § 4).

`Why candidate` states only the topical link, for example "addresses risk-assessment frequency,
the subject of O1". It never says that an obligation requires, applies to, or reaches a firm
document or entity; that is applicability (§ 6), and with the defining provision
not retrieved it is not stated at all.

Footer line: **"Candidates only. Whether a policy satisfies an obligation is clause-level work —
see `policy-gap-analysis`."**

### 8. Proposed actions

| # | Obligation # | Proposed action | Suggested owner | Basis for suggestion | Driven by date | Closes when |
|---|---|---|---|---|---|---|

Owner suggestions state their basis. No basis: the `Suggested owner` cell reads only `NOT FOUND - owner not identified (Gn)`, never a guessed role.

### 9. Open items

Two canonical lists, side by side: the G-list of shortfalls, each bullet naming its remedy after
the shortfall, and the D-list of determinations.

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
- G1 - NOT FOUND - instrument states no compliance date (date ladder)
- G2 - NOT RETRIEVED - eCFR did not return 31 CFR 1020.210 (codification check)
- G3 - PROPOSED - not in force: FR 2026-21107, rows O1, O2, O3
```

**Determinations outstanding.** The canonical list: one bullet per determination, with an ID
(D1, D2, ...), `NOT DETERMINED`, and the compliance owner as the decider unless this outline
names another. It includes every § 6 row, every scope ambiguity, every exemption question, and
every candidate policy awaiting the owner's relevance confirmation. Undecided matters are
listed here only, never in the G-list.

### 10. Draft register handoff

If a GRC register is available, include existing register IDs, task IDs, owners, and current statuses read from it. The output is a draft import/export package for a human to review and submit; state that no source-system update was performed.

### 11. Footer

Per `house-rules.md` § 9, including the draft handoff status and that any register update is the human's action.

Build the counts only after the rest of the draft is final, and only from the two canonical lists: for each marker type, the number of G-bullets in the Open items list leading with it, and for `NOT DETERMINED`, the number of D-bullets, each with the unit items (for example `NOT FOUND: 5 items`, `NOT DETERMINED: 7 items`). Give one number per marker type, never "plus", a sum of parts, or a range, and list every marker type that leads a G-bullet. Never count table cells, prose, the chat reply, or footer lines. Footer lines, including Coverage, Connectors, Web, Sources, Policy repository searched, Files, Codification, and Template, can describe gaps in plain words; every gap they mention has its G-bullet. A marker token in a footer line carries its (Gn). A Codification line with no rule text relied on reads `not performed: no rule text relied on (Gn)`, with the G-bullet `GAP - codification check not performed: no rule text relied on`. The Template line names the resolution step used; where `Cowork Templates/Risk and Compliance/reg-change-triage/` held no template, the line says so and the Open items list carries `NOT FOUND - Cowork Templates folder has no reg-change-triage template`. Recount the two lists before output and correct any figure that differs (`house-rules.md` § 9).

---

## Tracker (`.xlsx`)

One row per obligation. Live formulas for every count.

| Column | Notes |
|---|---|
| Obligation ID | `<instrument>-<n>` |
| Obligation text | |
| Status | in force / PROPOSED — not in force / forthcoming |
| Citation | |
| Authority tier | 1–6 |
| Published / Effective / Compliance / Mandatory compliance | Four columns, never merged; a cell with no calendar date follows `house-rules.md` § 5 |
| Binds whom | |
| Trigger or threshold | As printed |
| Proposed scope | |
| Determination | `NOT DETERMINED - compliance owner decides (Dn)` |
| Candidate policy | Policy name, or `NOT FOUND - <repository> has no record of a policy for <obligation> (Gn)`; never "none located" |
| Policy version | |
| Policy approval status | |
| Proposed action | |
| Suggested owner | No basis: only `NOT FOUND - owner not identified (Gn)` |
| Basis for owner | |
| Marker | Where the row carries one |
| Source | Instrument · location · retrieval date · route |

**Summary block** states counts and their coverage explicitly:

```
Obligations in force:        n   (of N rows)
Proposed, not in force:      n   (excluded from all in-force counts)
Forthcoming (future effect): n
Rows carrying markers:       n   (excluded from the counts above)
Policies located:            n
No policy located:           n   ← NOT FOUND, a finding, not a blank
```

Marker rows stay visible. A marker never becomes zero and never enters a count.
