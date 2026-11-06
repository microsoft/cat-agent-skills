# EDD Research Record — Default Outline

Used when no template is named in the request and none is present in
`Cowork Templates/Risk and Compliance/kyc-research-pack/`.

**A template replaces layout, never gates.** The disclaimer, the coverage statement, and the
identity-resolution column survive every template. Where a customer template has no place for
them, add it.

**One gap list.** Every shortfall in this artifact (anything absent, unretrieved, partial,
mismatched, rejected, unverified, unperformed, unconfigured, or undated) is recorded exactly
once in the Open items list (§ 8), as its own bullet with an ID (G1, G2, ...), leading with its
marker, one shortfall per bullet. **Marker cells in this outline:** the § 2
no-corroborating-identifier statement and any identifier cell holding `NOT LEGIBLE`; the § 3
coverage-statement `Screening connector` and `Not searched` lines; the § 4 `Disposition` cells
reading `unknown`; the § 5 unresolved-match rows; the § 6 `PEP status` value where no source
states it; the source-log `Disposition`, `Identity resolution`, and `Marker` cells. The § 2
identifier cells are fact cells, for example Former names `none stated in brief`. A marker cell
carries its marker followed by its G-ID in brackets, for example `NEEDS FEED - screening
connector: none configured (G1)`. Every other cell is a fact cell: it states what the source
says in plain words (for example `none stated in <source>`) and carries no marker token. A
search that returns nothing relevant is a gap: `NOT FOUND`, with its G-bullet. A marker token
written anywhere outside the Open items list, including prose, the chat reply, and the footer,
carries its (Gn) right after the marker phrase, and `NOT DETERMINED` carries its (Dn). Ordinary
prose, the chat reply, handling notes, and footer lines can mention a gap in plain words; every
gap mentioned anywhere has its G-bullet (`house-rules.md` § 4).

**Each determination is its own row or bullet.** Every owner determination listed in this
artifact carries its own marker. Never one blanket marker line over a list (`house-rules.md` § 9).

**One canonical list.** Every `NOT DETERMINED` item appears exactly once, with an ID (D1, D2,
...), in the Determinations outstanding list (§ 8), and the footer's `NOT DETERMINED` figure
is the number of bullets there. Each D-bullet holds exactly one decision; a secondary
question gets its own D-number.
No D-bullet contains " and ", " or ", "/", or a second question mark joining two decisions;
split any that does. Every `UNRESOLVED MATCH` disposition is its own D-bullet. Undecided matters go there, never in the Open items list. A summary list never groups
several determinations or gaps under one marker bullet: it refers to the canonical lists by ID
with no marker of its own (not counted).

---

## Record (`.docx`)

### 1. Header and mandatory disclaimer

```
KYC / EDD PUBLIC-SOURCE RESEARCH RECORD
Subject: <primary subject>          File reference: <ref>
Destination: internal working paper
Prepared: <date>    Preparer: <name>
Status: DRAFT — research input to a human-owned CDD/EDD determination
```

> **This is a public-source research record, not a sanctions or PEP screen. It must not be relied
> on for OFAC or sanctions compliance. It contains no risk rating and no filing decision. All
> determinations rest with the responsible compliance owner.**

The disclaimer appears on the first page and in the footer. It is never abbreviated or removed,
and it appears whether or not a screening connector was used.

### 2. Subject set

| # | Subject | Type | Role / basis for inclusion |
|---|---|---|---|

**Identifiers held per subject** — the basis for all attribution:

| Subject | Legal name | Former names | Jurisdiction | Reg. no. | DOB / incorporation | Address | Stated ownership |
|---|---|---|---|---|---|---|---|

Identifier cells are fact cells, never blank: an identifier the supplied documents do not
state reads `none stated in <document>` in plain words, for example Former names
`none stated in brief`. An identifier searched for in a source that returned nothing relevant
is a gap, written in the no-corroborating-identifier statement below with its (Gn); text
present but unreadable is `NOT LEGIBLE - <what> on <document> p<n> (Gn)`.

> **Where a subject has no corroborating identifier**, state it here:
> "Only a name is held for <subject>: NOT FOUND - supplied documents have no corroborating
> identifier for <subject> (Gn). Findings cannot be attributed; items are listed in § 5 as
> unresolved matches."

**Out of scope:** family members, unnamed associates, and persons identified only by
relationship — unless the user named them with a stated basis.

### 3. Coverage statement — required, before any findings

```
Nature:               non-exhaustive public-source research, not a screen
Screening connector:  <provider, run date>   |   NEEDS FEED - screening connector: none configured (Gn)
Sources searched:     <list>
Languages:            <list>
Jurisdictions:        <list>
Date range:           <from> – <to>
Not searched:         GAP - coverage: <paid databases, non-English sources, offline registries,
                       court systems without public access> (Gn)
This search cannot establish that no adverse information exists.
```

Findings are never presented before the coverage statement.

The `Nature` line, with the literal words "non-exhaustive", is required in every record.

### 4. Findings — attributed

Only items where identity resolution succeeded.

| # | Subject | Item | Type | Date | **Disposition** | Source | Retrieval date | Corroborating identifier |
|---|---|---|---|---|---|---|---|---|

`Type`: adverse media · litigation · regulatory · registry · ownership · insolvency · other.

`Disposition`: allegation · investigation · charge · settlement — no admission · civil judgment ·
conviction · dismissed / acquitted / overturned · **unknown** (written
`unknown: NOT FOUND - <sources searched> have no record of the outcome (Gn)`).

`Corroborating identifier` names what made attribution possible. A row without one belongs in
§ 5, not here.

Each item narrated beneath the table in the alleged register where applicable:

```
Item <n> — <subject>
Reported:    "<verbatim or close paraphrase>" — <outlet>, <date>
Disposition: <status>, <date>. <Quote the admission or outcome language>
Attributed:  <which identifier corroborated>
```

The quote never carries the name of a private individual outside the subject set: replace it
with `[another individual]` before quoting (`house-rules.md` § 12).

### 5. Unresolved matches — leads, not findings

| # | Name as it appeared | Item | Source | Date | Why unresolved |
|---|---|---|---|---|---|

Header line, always:

> **These items could not be attributed to a subject. They are leads for the analyst, not
> findings about the subject, and are excluded from all counts of findings.**

`Why unresolved`: no identifiers in the source · identifier conflict · common name · possible
well-known unrelated party.

Minimal detail for private individuals — enough to resolve, not a profile.

**No non-subject names in a lead.** Before quoting any source (a press release, indictment, or
article) in the `Item` cell or anywhere else in this section, replace the name of every private
individual outside the subject set with `[another individual]`. A verbatim quote or close
paraphrase never carries such a name; a co-defendant named in a press release appears as
`[another individual]`.

### 6. Factual risk attributes

| Attribute | Value | Source |
|---|---|---|
| Jurisdiction of incorporation | | |
| Jurisdictions of operation | | |
| Industry / products | | |
| Ownership structure and opacity | | |
| PEP status **as stated by a source** | | Source required. Never inferred. Where no source states it, `NOT FOUND - <sources searched> state no PEP status (Gn)` |

Recorded as facts with sources, never as judgments about people connected to a place.

**Prohibited as risk factors and absent from this record:** race, religion, ethnicity, national
origin as a proxy, language, name origin.

### 7. Structure reference

Which FinCEN advisories or typologies were used to structure the review — what was looked for.
**Not** a statement of what was found.

### 8. Determinations outstanding

One bullet per determination, each carrying its own marker in the form the wording table below
gives for a rating (`NOT DETERMINED` with the compliance owner as the decider). Never one
blanket marker line over the list. The decider for every bullet is the compliance owner unless
this outline names another; never invent a decider. Where the request names a decision body
(for example "the onboarding committee"), the bullet still names the compliance owner as the
decider and can mention the body as "(for the onboarding committee)".

- Risk rating
- PEP determination
- Sanctions screening (separate system)
- Whether EDD is satisfied
- Onboarding, exit, restriction
- Any filing decision
- Any other open determination raised in the record, one bullet each

This is the canonical list: each bullet has an ID (D1, D2, ...), and the footer's
`NOT DETERMINED` figure is the number of bullets here (`house-rules.md` § 9).

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
- G1 - NEEDS FEED - screening connector: none configured (coverage statement)
- G2 - UNRESOLVED MATCH - 2024 press report name hit not attributed to the subject (§ 5)
```

### 9. Footer

Per `house-rules.md` § 9, including the mandatory disclaimer verbatim.

Build the counts only after the rest of the draft is final, and only from the two canonical lists: for each marker type, the number of G-bullets in the Open items list leading with it, and for `NOT DETERMINED`, the number of D-bullets, each with the unit items (for example `NOT FOUND: 5 items`, `NOT DETERMINED: 7 items`). Give one number per marker type, never "plus", a sum of parts, or a range, and list every marker type that leads a G-bullet. Never count table cells, prose, the chat reply, or footer lines. Footer lines, including Coverage, Connectors, Web, Sources, Policy repository searched, Files, Codification, and Template, can describe gaps in plain words; every gap they mention has its G-bullet. A marker token in a footer line carries its (Gn). A Codification line with no rule text relied on reads `not performed: no rule text relied on (Gn)`, with the G-bullet `GAP - codification check not performed: no rule text relied on`. The Template line names the resolution step used; where `Cowork Templates/Risk and Compliance/kyc-research-pack/` held no template, the line says so and the Open items list carries `NOT FOUND - Cowork Templates folder has no kyc-research-pack template`. Recount the two lists before output and correct any figure that differs (`house-rules.md` § 9).

---

## Source log (`.xlsx`)

One row per **item reviewed** — including items reviewed and excluded.

| Column | Notes |
|---|---|
| Item ID | |
| Subject | Or `unattributed` |
| Source name | Outlet, court, registry, regulator |
| URL / citation | |
| Publication date | |
| Retrieval date | |
| Item type | |
| Summary | Alleged register where applicable |
| **Disposition** | Including `unknown`, written with its `NOT FOUND` marker as in § 4 |
| Disposition date | |
| **Identity resolution** | `attributed` · `UNRESOLVED MATCH - not attributed to <subject> (Gn)` · `GAP - identifier mismatch (Gn)` |
| Corroborating identifier | |
| Duplicate of | Where collapsed |
| Marker | |

### Summary block

```
Items reviewed:                    n
  attributed to a subject          n
  UNRESOLVED MATCH                 n   ← leads, excluded from findings counts
  GAP — identifier mismatch        n
  excluded as duplicates           n
Attributed items by disposition:
  allegation / investigation       n
  charge                           n
  settlement — no admission        n
  civil judgment / conviction      n
  dismissed / acquitted            n
  unknown                          n
```

Counts state denominators. Unattributed items never enter a findings count.

---

## Wording that must not appear

| Never | Instead |
|---|---|
| "No adverse findings" / "the subject is clean" | The coverage statement, then what was found |
| "Not on the SDN list" | "OFAC lists consulted as public reference. This is not a screen" |
| "High risk" / "medium risk" / a score | `NOT DETERMINED — compliance owner` |
| "The subject is a PEP" (inferred) | PEP status as stated by a named source, or `NOT FOUND` |
| "X committed fraud" (from an allegation) | "<Outlet> reported that X was accused of…" |
| "Recommend filing a SAR" / "recommend exit" | Out of scope. Owner determines |
| "Screening completed" | "Public-source research completed. Not a screen" |
| Any mention of race, religion, ethnicity, or national origin as risk | The documented jurisdictional or industry factor |
| "<name>, <title>, wrote…" (a document author or commenter) | "The <role>'s <comment / email / note> on <document>, <location>" (`house-rules.md` § 12) |
