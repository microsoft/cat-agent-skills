# Policy-to-Regulation Gap Analysis: workflow detail

The full text of every workflow step, moved here unchanged from SKILL.md so the skill
body stays short. SKILL.md gives each step's summary; this file is binding and is read
in full before the first step. Section numbers match the SKILL.md steps.

## Workflow steps

### 1. Establish both sides before comparing

Neither side may be assumed.

**The regulation.** Agency · citation · type · authority tier · the exact sections in scope.
Retrieve via `reg-source-access.md`. **Run the codification check** — if a final rule published
after the title's `latest_issue_date` amends the part in scope and is effective, that text
governs and carries `PENDING CODIFICATION`.

If that final rule's effective date is still in the future, report it as a forthcoming change
with its date ladder (`reg-source-access.md` § 3, step 4). That is a status, written in the
row's `Source` cell and in the memo, not a marker. Use only the markers defined in
`house-rules.md` (§ 3 and § 4) plus this skill's `PROPOSED DRAFTING` label; never coin a new
one such as `FORTHCOMING`.

If the user names a rule loosely ("the CDD rule"), resolve it to a citation and confirm it back.
eCFR full-text search is the right entry point; confirm by opening the section, because a search
hit is `snippet only` until you do.

**The policy.** Name · version · approval status · approval date · owner · scope. Per
`document-extraction.md` § 4:

- An unapproved draft is `DRAFT — not approved` and is **never** the control of record. It may be
  analysed, but every coverage state derived from it carries the marker.
- **Name the control of record.** When the policy given is a draft or a superseded version,
  search for the approved current version, open it far enough to read version, approval status,
  and approval date, and state `Control of record: <doc> v<x>, approved <date> (<location>)` in
  § 2 and in the chat reply. This is a fact from the tiers in `house-rules.md` § 3, never a
  D-bullet. None located: `NOT FOUND - <repository> has no record of an approved version of <doc> (Gn)`.
- Where version or approval cannot be established → `GAP — policy version not established`, and
  **no row is scored as covered**.
- **Scope is load-bearing.** A policy that does not cover the entity, product, or jurisdiction the
  requirement binds cannot close a gap for it, regardless of its text. Check scope first and say
  so if it does not reach, by quoting the policy's scope clause. Which entities the rule binds is
  itself a coverage point (next bullet).
- **Rule coverage is proposed applicability.** Quoting what the policy's own scope statement
  covers or excludes is a fact. Any statement about which entities, affiliates, accounts,
  products, or activities the rule covers or does not cover, including the firm itself and the
  in-scope bank and its accounts as much as an affiliate the policy excludes, is proposed
  applicability: mark it `NOT DETERMINED` with the compliance owner as the decider, and give the
  reasoning and the citation to the retrieved provision it rests on. Never state it as fact and
  never from memory. Before reasoning about coverage, retrieve the provision that defines it
  (for example the rule's definition of "covered financial institution"). If it was not
  retrieved, mark it `NOT RETRIEVED - <source> (Gn)` only if a request was made and failed,
  otherwise `GAP - <source> retrieval not attempted (Gn)`, name the provision, and write the reasoning as exactly
  `none - defining provision not retrieved`, quoting no rule text that bears on coverage.
  No likelihood or hedge word (probably, presumably, likely, unlikely, appears to, seems, would likely, should be)
  appears on any coverage point (`house-rules.md` § 2).

### 2. Decompose the regulation into requirements

One row per discrete requirement, not one row per sentence or per paragraph number.

- A sentence imposing three obligations becomes **three rows**. Compound requirements hide gaps —
  a policy commonly covers two of three and looks covered.
- Keep the citation to the sub-paragraph level the text supports.
- Capture conditions, thresholds, and exemptions as part of the requirement. A requirement
  stripped of its exemption is a different requirement.
- Distinguish a **requirement** ("must") from a **permission** ("may") from a **safe harbour**.
  Only requirements are scored for coverage; the others are recorded and marked as such.
  State them in the approved fact wording, which needs no ID:
  "<n> non-requirement rows (definitions, exemptions) are recorded for reference and excluded from the counts."

Quote each requirement verbatim. Never paraphrase the regulation into the table. Before quoting,
retrieve the rule's definitions section. If it is not retrieved, quote only the operative act
with the covered-entity term replaced by `[covered entity]`, and add the G-bullet naming the
definitions section, `NOT RETRIEVED - <source> (Gn)` only if a request was made and failed, otherwise
`GAP - <source> retrieval not attempted (Gn)` (`house-rules.md` § 2).
This applies to every quote of rule or preamble text in any cell (requirement, exemption,
condition, date ladder tier, preamble quote) and every plain-words paraphrase in the artifact
or the chat reply: "for [covered entity] with total assets of $10 billion or more", never
"firms", "banks", or "the institution" (`house-rules.md` § 2).

The Exemption cell has three forms only (hard stop, `house-rules.md` § 2): the provision's
verbatim text in quotation marks with its citation; `none stated in <citation>`; or
`NOT DETERMINED - <decider> decides (Dn)`. Never a word of your own about what the provision
reaches or limits ("applies only to", "only the <x> element", "limited to", "excludes").
Whether the firm can use the exemption is a coverage point for the **compliance owner**, like
every scope-note row (`gap-outline.md` § 2), for example
`D4 - NOT DETERMINED - can <firm> rely on the (g) exemption - compliance owner decides`.
Only what the exemption means as a matter of law goes to counsel, as its own D-bullet.
A non-scored row's Policy section cell reads `-` with `(not scored)`, never `NOT FOUND`
(`gap-outline.md`).

### 3. Locate the policy text for each requirement

Search the policy for text addressing the requirement. Quote **verbatim**, with section number
and page.

Where you explain why a policy section was matched to a requirement, state only the topical
link, for example "addresses beneficial-ownership verification, the subject of Req 1010.230-2".
Never write that a requirement requires, applies to, or reaches a firm document or entity.

Search the whole document before concluding absence — obligations are frequently met in a
different section than expected, in an appendix, or in a referenced procedure.

Where the policy **incorporates another document by reference**, that reference is not coverage
on its own. Either retrieve the referenced document and analyse it, or mark
`NOT RETRIEVED — <name> referenced but not provided` where the request failed, or
`GAP - <name> retrieval not attempted (Gn)` where none was made. A referenced-but-absent procedure is a gap,
never an assumption of coverage.

### 4. Assign a coverage state

Five states. No sixth, and **no compliance conclusion**.

| State | Means |
|---|---|
| `covered` | Policy text addresses the requirement in substance. Quote both sides |
| `partial` | Policy addresses part of it. **Say precisely which part is not addressed**, as `<what is missing> (Gn)`, every sentence ending with the row's (Gn), repeated even when the `Coverage` or `Marker` cell carries it |
| `not found` | Searched the whole policy; no text addresses it |
| `conflicts` | Policy text is inconsistent with the requirement. Quote both and state the inconsistency |
| `NOT DETERMINED` | Coverage turns on a judgment only a qualified owner can make |

Rules:

- **`covered` is about substance, not vocabulary.** A policy that imposes the obligation in
  different words covers it. A policy that merely quotes the rule without assigning an obligation,
  owner, or action does **not** — that is `partial`, and say so.
- **Same act, not the same topic.** `covered` or `partial` requires policy text that addresses
  the act the requirement names. For a requirement to document the verification method used, a
  clause about retaining verification documents in general does not address documenting the
  method; that row is `not found`, not `partial`.
- **`not found` is a finding, not a blank.** It means searched and absent.
- A requirement whose regulatory text was not retrieved is `NOT RETRIEVED - <source> (Gn)` where a request
  failed, or `GAP - <source> retrieval not attempted (Gn)` where none was made, and is **never
  scored** — not as covered, not as a gap.
- Use `NOT DETERMINED` honestly. Whether a control is *adequate* is not a coverage question.

### 5. Suggest edits

For every `partial`, `not found`, or `conflicts` row, suggest policy language that would address
the requirement.

Suggested language is **proposed drafting for the policy owner**, marked as such. It is never
presented as approved, never as the firm's position, and never written into the policy. Anchor it
to the specific requirement and cite the requirement it serves.

### 6. Emit the table and memo

The skill supplies the clause-by-clause content, quotes, citations, coverage states, markers, and memo structure; `xlsx` builds the table and `docx` builds the memo. Live formulas compute counts with denominators and preserve marker rows.

Coverage counts exclude rows carrying markers and say so:

```
Requirements analysed:        n
  covered                     n
  partial                     n
  not found                   n
  conflicts                   n
Rows not scored (markers):    n   ← NOT RETRIEVED / GAP / NOT DETERMINED
```

**Never report a coverage percentage without its denominator**, and never let marker rows silently
drop out of it.
The memo headline and the chat reply state coverage in the `house-rules.md` § 4 form:
`covered 3 of 9; partial 4 of 9 (G11 to G14); not found 2 of 9 (G9, G10); conflicts 1 of 9 (G8)`.

---

## Guardrails
- **Never output "compliant", "non-compliant", or "in violation."** Coverage states only.
- **Never score a requirement whose text could not be retrieved.**
- **Never treat an unapproved draft as the control of record.**
- **Never treat an incorporated-by-reference document as coverage** without retrieving it.
- **Never state which entities, affiliates, accounts, products, or activities a rule covers or
  does not cover** as fact or from memory, including for the firm itself. It is proposed
  applicability, marked `NOT DETERMINED` with the reasoning and citation to the retrieved
  coverage-defining provision, for the compliance owner to decide, or, with no reasoning where
  that provision was not retrieved, `NOT RETRIEVED` if a request was made and failed, otherwise
  `GAP - <source> retrieval not attempted`.
- **Never paraphrase either side** into the table — both are quoted verbatim with locations.
- **Never merge compound requirements** into one row.
- **Never present suggested language as approved or adopted.**
- **Never report codified text as current** without the codification check.
- **Never invent a marker.** House-rules markers only; a not-yet-effective rule is stated as a
  forthcoming change in the row's `Source` cell.
- **Never fabricate** a figure, quote, date, source, owner, status, or identifier; use the appropriate marker instead.
- **Unreadable input is `NOT LEGIBLE`.** Name the document and page, ask for a cleaner copy, and never guess the value.
- **Never delete or overwrite existing content, prior entries, or decision sections.** Append new draft material and preserve the original.
- **Never claim a save succeeded when it failed.** Report what was produced, where it was and was not written, and what remains incomplete.
- **Quote third-party text with attribution by role, document, and location.** Never present regulator, auditor, vendor, policy, media, filing, or report wording as the firm's own. Attribute a document's author or commenter by role, document, and location (for example "the exam coordinator's comment on the annotated letter, p. 2"), never by personal name unless the person is a named owner or preparer the artifact requires (`house-rules.md` § 12). This holds in the chat reply too, including when you report an instruction embedded in a document.
- **Nothing is sent, submitted, filed, posted to, or committed in a source system.** Deliverables are drafts or exports for human review and human action.
- Percentages always carry their denominator; marker rows never silently vanish.
- Nothing is written into a policy, sent, filed, or committed in a source system.

---

## Source resolution

Ordering follows `references/house-rules.md`. This section names what each source supplies here.

**Capabilities.** Reading supplied files (PDF, DOCX, XLSX, PPTX, CSV, images with OCR); web retrieval of public sources; Microsoft 365 search where the user has access; configured MCP connectors where present. Artifact creation is delegated — spreadsheets to `xlsx`, documents to `docx`, decks to `pptx`.

**When a capability is unavailable:** say which one, name what it would have supplied, and continue with what is available. Use `NEEDS FEED` when no source exists, `NOT RETRIEVED` when a source exists but retrieval failed, and `NOT FOUND` when a source answered with no record. Never silently skip a step and never present an unavailable source as returning nothing.

1. **Configured MCP** — Policy, DMS, and GRC connectors add firm policy repositories, approval metadata, owner records, and referenced procedures where configured. Regulations.gov docket access is an extensibility item and needs a free API key.
2. **Public primary** — eCFR supplies codified CFR text as a compilation, not the law. Federal Register supplies final rules for the codification check; effective amendments missing from eCFR are marked `PENDING CODIFICATION`.
3. **Supplied or M365 document** — The target policy or procedure, incorporated documents, approval records, scope statements, and version evidence supply the firm side of the comparison.

---

## Output footer

Per `house-rules.md` § 9: destination · regulation identified with tier, sections, retrieval date
and route · **codification check and result** · policy name, version, approval status and date ·
requirements analysed and how many scored · coverage counts with denominators, in the step 6 headline form with G-IDs · open items by marker type (G-list) · determinations outstanding · files created and whether saves succeeded · template used.

**Count from the two lists last.** Only after the rest of the draft is final, build the counts from the Open items list (G-bullets per marker type) and the Determinations outstanding list (D-bullets for `NOT DETERMINED`), unit items, for example `NOT FOUND: 5 items`. Give one number per marker type, never "plus" or a range, and list every marker type that leads a G-bullet. Never count table cells, prose, the chat reply, or footer lines. Footer lines can describe gaps in plain words; each gap they mention has its G-bullet, and a marker token in a footer line carries its (Gn). Any mention of a file left unopened under data minimisation, the footer included, cites its G-bullet `GAP - not opened: <file> withheld under data minimisation (Gn)` (`house-rules.md` § 4, § 12). With no rule text relied on, the Codification line reads `not performed: no rule text relied on (Gn)`, with the G-bullet `GAP - codification check not performed: no rule text relied on`. Where no Cowork template was found, the Template line says so and the Open items list carries `NOT FOUND - Cowork Templates folder has no policy-gap-analysis template`. Run the final self-check (step 7), then recount and correct any figure that differs (`house-rules.md` § 9).
