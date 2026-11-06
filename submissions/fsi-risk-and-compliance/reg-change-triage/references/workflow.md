# Regulatory Change Triage: workflow detail

The full text of every workflow step, moved here unchanged from SKILL.md so the skill
body stays short. SKILL.md gives each step's summary; this file is binding and is read
in full before the first step. Section numbers match the SKILL.md steps.

## Workflow steps

### 1. Identify the instrument precisely

Establish before anything else: **agency · title · document number or citation · type · authority
tier**.

**Type determines everything downstream.** A proposed rule is not law (`house-rules.md` § 3).
If the user says "the new rule" and it is an NPRM, say so in the `PROPOSED` line. For every
Proposed Rule, that line goes immediately after the whole header block (title, Destination,
Prepared, and Status lines), never between the title and those lines (`triage-outline.md` § 1).
The top of a Proposed Rule brief reads, in this order:

```
<title line, as above>
Destination: internal working paper
Prepared: 2026-10-16    Preparer: <name>    Status: <status, as above>
PROPOSED - not in force (G1). Comment period closes 2026-11-12. No obligation below is currently binding.
```

**Declines are plain.** A request to include a customer example, a SAR flag, or personal data
is declined as `<category> withheld under data minimisation.`, with no statement of what SAR
confidentiality or any law requires (`house-rules.md` § 12).

**Never say what does not exist.** In the brief, the decline, and the chat reply, never write
that a final rule "has not been published", "is not yet final", or "does not exist". Say what
the instrument you hold is ("FR Doc. <n> is a proposed rule"). Only after a Federal Register
search in this session may you write
`NOT FOUND - Federal Register API has no record of a final rule for <RIN or docket> as of <date> (Gn)`
(`house-rules.md` § 4).

If the instrument is ambiguous — several documents share the description — list the candidates
with their identifiers and ask which. Never pick one silently.
When the number and the topic the user gives point to different instruments, list the
candidates, mark the described instrument `NOT RETRIEVED - <description> (Gn)`, and ask the
user to confirm it or upload it.

### 2. Retrieve it

Follow `reg-source-access.md` § 1. Connector → direct route → browser → ask for an upload →
`NOT RETRIEVED`.

**Never answer from memory.** A brief about a rule you could not open is not a shorter brief —
it is `NOT RETRIEVED` and a request for the document.

When searching for the instrument, **filter by agency, type, and docket** — a bare term search
over-returns badly and its newest results are frequently unrelated (`reg-source-access.md` § 4).

### 3. Build the date ladder

Four dates, never collapsed:

| Date | Source |
|---|---|
| Published | API `publication_date` |
| Effective | API `effective_on` |
| Compliance date | **Usually only in the preamble — open the rule** |
| Mandatory compliance date | Preamble; the end of any phase-in |

Comment deadline too. **Every ladder row is always shown**, for every instrument type.

Where the instrument states no such date → `NOT FOUND — instrument states no <which> date`.
A row with only relative or proposed wording still has no stated date. It carries that marker,
and the wording is quoted after it on the same row, for example the effective-date marker
followed by `; proposed: "effective 12 months after its publication in the Federal Register"`.
The wording never replaces the marker (`house-rules.md` § 5).
Never assert that a final rule does not exist. Write
`The proposal ties the effective date to a later event: "<quoted text>" (Gn).` (`house-rules.md` § 4).
A row with no calendar date carries `NOT FOUND - instrument states no <which> date` first; any
explanation (for example "final rule; no comment period") is written after the marker. Never
write "not applicable" or "n/a" in a ladder row.
**Never infer a compliance date from the effective date.** Firms plan against the last date in
the ladder, so a collapsed ladder produces a brief that is either alarmist or dangerously late.

### 4. Extract what changed

For a rule amending existing text, state the change at the level the instrument states it:
**which CFR part and section, what the prior text required, what the new text requires.**

- Quote both sides verbatim where the instrument supplies both.
- Where the instrument gives only the new text, retrieve the current codified text to compare —
  and run the **codification check** (`reg-source-access.md` § 3) before calling it "current".
  If the check is not performed or is incomplete, the codification check statement reads
  `GAP - codification check not performed: <reason>` or `NOT RETRIEVED - <source> did not
  return`, and the same shortfall is a G-bullet in the Open items list.
- Where you cannot establish the prior text → `GAP — prior text not established`. Do not
  characterise a change you have not evidenced.
- When quoting prior codified text, a paragraph heading or defined term that is itself the
  covered-entity term (for example the heading "Covered financial institution") is also
  bracketed as `[covered entity]` while the definition is not retrieved (`house-rules.md` § 2).
- **Prior text and preamble quotes take the bracket too.** A preamble sentence describing the
  prior rule ("the prior rule did not require the institution to ...") is a quote of
  preamble text: every entity term in it reads `[covered entity]` while the definitions
  section is not retrieved. The lint script flags entity words inside quotation marks in these
  cells.

For a new requirement with no predecessor, say it is new.

### 5. Derive obligations

One obligation per row. Each carries:

**what must be done · who it binds · the trigger or threshold · the date it bites · the citation ·
the authority tier**

Rules to hold:

- An obligation from a **proposed rule** carries `PROPOSED — not in force` in its own row, and
  that marker travels into the tracker and every summary. It is never counted alongside live
  obligations.
- An obligation from **guidance** is written as a supervisory expectation under that instrument,
  never as "required by".
- A threshold, dollar amount, or population is quoted exactly as written. Never rounded, never
  restated in different units.
- Before quoting an obligation, retrieve the rule's definitions section. If it is
  not retrieved, quote only the operative act with the covered-entity term replaced by
  `[covered entity]`, and add the G-bullet naming the definitions section,
  `NOT RETRIEVED - <source> (Gn)` only if a request was made and failed, otherwise
  `GAP - <source> retrieval not attempted (Gn)` (`house-rules.md` § 2).
  This applies to every quote of rule or preamble text in any cell (requirement, exemption,
  condition, date ladder tier, preamble quote) and every plain-words paraphrase in the artifact
  or the chat reply: "for [covered entity] with total assets of $10 billion or more", never
  "firms", "banks", or "the institution" (`house-rules.md` § 2).
- One instrument's PROPOSED status is one G-bullet naming every obligation row, for example
  `G7 - PROPOSED - not in force: FR 2026-21107, rows O1, O2, O3`; each row cites (G7).
- The date it bites is the DATES compliance or full-compliance date covering the row; the
  effective date only where DATES names it as that row's compliance date (`triage-outline.md` § 5).
  Exemption rows follow the same rule: the DATES compliance date, or
  `NOT FOUND - instrument states no compliance date for <exemption> (Gn)`. Never the effective date.
- An exemption or exclusion is an obligation-shaping fact — capture it. A brief that lists a
  requirement without its small-entity exemption is wrong for most readers.

### 6. Propose applicability — never decide it

For each obligation, propose which business lines, products, entities, or jurisdictions are
affected, **with the reasoning and the text it rests on**.

Mark every applicability proposal `NOT DETERMINED — compliance owner decides`.

Any statement anywhere in the brief, the tracker, or the chat reply about which entities,
affiliates, accounts, products, or activities a rule covers or does not cover, including the
firm itself, is proposed applicability, marked `NOT DETERMINED` with the reasoning and the
citation it rests on, for the compliance owner to decide. Never state it as fact and never from
memory.

**Retrieve the coverage-defining provision first.** Before reasoning about which entities a rule
covers, retrieve and cite the provision that defines coverage (for example the rule's
definition of "bank" or "covered financial institution"). If it was not retrieved, mark the
point `NOT RETRIEVED - <source> (Gn)` only if a request was made and failed, otherwise
`GAP - <source> retrieval not attempted (Gn)`, name the provision, and write the reasoning as exactly
`none - defining provision not retrieved` and nothing else. Quote no rule text that bears on
coverage for that point anywhere, for example which part the proposed text sits in or the word
it uses for the entities it binds (`house-rules.md` § 2).

Applicability and exemption lines carry `NOT DETERMINED` with the reasoning and never a
likelihood or hedge word: not "probably", "presumably", "likely", "unlikely", "appears to",
"seems", "would likely", or "should be". The ban covers every statement about applicability,
coverage, scope, exemptions, or any determination, anywhere in the brief, the tracker, or the
chat reply (`house-rules.md` § 2). Where the answer turns
on a fact you do not have (for example the firm's total assets against an asset-size
exemption), name the missing fact and its marker instead of leaning either way.
The missing fact goes in its own cell or bullet, never in a `Reasoning` cell that reads
`none - defining provision not retrieved`.

Where the instrument's scope language is ambiguous as applied to the firm, say so explicitly
rather than resolving it. That ambiguity is the most useful thing in the brief. State each
ambiguity as an open question with its decider, marked `NOT DETERMINED`, and never with a
likelihood or hedge word about how it would resolve.

### 7. Locate candidate affected policies

Search Microsoft 365 for the firm's policies, procedures, and standards touching each obligation.

For each match: **document name · version · approval status · approval date · location · why it
is a candidate.**

| Outcome | Marker |
|---|---|
| Candidate policy found | Listed, with `NOT DETERMINED — owner confirms relevance` |
| Searched, nothing found | `NOT FOUND - <repository> has no record of a policy for <obligation> (Gn)`; never "none located" |
| Repository not reachable | `NOT RETRIEVED — <repository> <reason>` |
| Found but version/approval unknown | `GAP — policy version not established` |
| Examined and rejected | `GAP - scope mismatch, not a candidate: <doc>`, one G-bullet per document |
| No policy repository configured | `NEEDS FEED — policy repository or DMS` |

**`Why candidate` states only the topical link**, for example "addresses risk-assessment
frequency, the subject of O1". Never write that an obligation requires, applies to, or reaches
a firm document or entity; that is applicability (step 6), and with the defining provision
not retrieved it is not stated at all (`triage-outline.md` § 7).

**A located policy is a candidate, not coverage.** Whether it actually satisfies the obligation
is clause-level work — hand off to `policy-gap-analysis` (§ 11 of `house-rules.md`) rather than
asserting it here.

`NOT FOUND` here means "we searched and found no policy" — a real and important finding. It is
never rendered as silence or as an empty cell.

### 8. Build the action list

Proposed actions only, each with: the obligation it serves · a **suggested** owner with the basis
for the suggestion · the date it is driven by · what would close it.

Suggested owners come from the M365 record — policy ownership, prior exam responses, committee
membership. State the basis. Where no basis exists → `NOT FOUND — owner not identified`, never a
guess. The cell reads only that marker with its (Gn), never a role.

### 9. Emit the tracker and draft handoff

The skill supplies the obligation content, citations, owner bases, markers, and export structure; `xlsx` builds the workbook. Live formulas count only eligible rows and state coverage.

If a GRC connector is configured, use it to read and pre-fill existing change IDs, task IDs, owners, statuses, and register context, then reconcile the draft against those records. The skill does not create, update, or post to the register or task system. The deliverable is a draft export structured for a human to review and submit. State that the register update is the human's action and that the skill has not performed it. Without a connector, mark `NEEDS FEED — GRC change register` for fields the register would have supplied.

---

## Guardrails
- **Never state a requirement from memory.** `NOT RETRIEVED` (a request made and failed) or
  `GAP - <source> retrieval not attempted` (no request made) is the honest output.
- **Never present a proposed rule as an obligation.** `PROPOSED — not in force`, everywhere it
  appears.
- **Never call guidance a legal requirement.**
- **Never collapse the four dates.**
- **Never report codified text as current** without the codification check, or without saying the
  check was not performed.
- **Never decide applicability, materiality, or compliance status.**
- **Never put a likelihood or hedge word** (probably, presumably, likely, unlikely, appears to, seems, would likely, should be) on an
  applicability, coverage, scope, exemption, or other determination statement, anywhere,
  including scope-ambiguity lists, notes, and the chat reply. `NOT DETERMINED` with the
  reasoning and the decider only.
- **Never state which entities, affiliates, accounts, products, or activities a rule covers or
  does not cover** without retrieving the provision that defines coverage. Proposed
  applicability, marked `NOT DETERMINED`, or, with no reasoning, `NOT RETRIEVED` if a request
  was made and failed, otherwise `GAP - <source> retrieval not attempted`.
- **Never write that an obligation requires, applies to, or reaches a firm document or entity**
  in a `Why candidate` cell. State the topical link only.
- **Never present a search-result count as coverage.**
- **Never cite anything you reached only through a snippet.**
- **Never fabricate** a document number, docket, section, or date.
- **Never fabricate** a figure, quote, date, source, owner, status, or identifier; use the appropriate marker instead.
- **Unreadable input is `NOT LEGIBLE`.** Name the document and page, ask for a cleaner copy, and never guess the value.
- **Never delete or overwrite existing content, prior entries, or decision sections.** Append new draft material and preserve the original.
- **Never claim a save succeeded when it failed.** Report what was produced, where it was and was not written, and what remains incomplete.
- **Quote third-party text with attribution by role, document, and location.** Never present regulator, auditor, vendor, policy, media, filing, or report wording as the firm's own. Attribute a document's author or commenter by role, document, and location (for example "the exam coordinator's comment on the annotated letter, p. 2"), never by personal name unless the person is a named owner or preparer the artifact requires (`house-rules.md` § 12). This holds in the chat reply too, including when you report an instruction embedded in a document.
- **Nothing is sent, submitted, filed, posted to, or committed in a source system.** Deliverables are drafts or exports for human review and human action.
- Markers never become values, never enter counts.
- Nothing is registered, filed, or sent.

---

## Source resolution

Ordering follows `references/house-rules.md`. This section names what each source supplies here.

**Capabilities.** Reading supplied files (PDF, DOCX, XLSX, PPTX, CSV, images with OCR); web retrieval of public sources; Microsoft 365 search where the user has access; configured MCP connectors where present. Artifact creation is delegated — spreadsheets to `xlsx`, documents to `docx`, decks to `pptx`.

**When a capability is unavailable:** say which one, name what it would have supplied, and continue with what is available. Use `NEEDS FEED` when no source exists, `NOT RETRIEVED` when a source exists but retrieval failed, and `NOT FOUND` when a source answered with no record. Never silently skip a step and never present an unavailable source as returning nothing.

1. **Configured MCP** — GRC change registers, policy or document repositories, and Planner or issue platforms add existing change records, IDs, owners, tasks, and current status for reading, pre-fill, and reconciliation only.
2. **Public primary** — Federal Register supplies publication dates, effective dates, preambles, and proposed or final rule text. eCFR supplies codified CFR text as a compilation, not the law; run the codification check and mark effective final rules absent from the codified text as `PENDING CODIFICATION`.
3. **Supplied or M365 document** — Uploaded instruments, firm policies, procedures, standards, prior change records, and ownership evidence supply the firm-specific impact analysis.

---

## Output footer

Per `house-rules.md` § 9, reporting this session only: destination · instrument and identifiers ·
route used · authority tier · coverage · **codification check performed and result** · policy
repository searched and what was found · connectors used or unavailable · open items by marker type (G-list) ·
determinations outstanding · draft export prepared for human register update · explicit statement that no source-system update was performed · files created and whether saves succeeded · template used.

**Count from the two lists last.** Only after the rest of the draft is final, build the counts from the Open items list (G-bullets per marker type) and the Determinations outstanding list (D-bullets for `NOT DETERMINED`), unit items, for example `NOT FOUND: 5 items`. Give one number per marker type, never "plus" or a range, and list every marker type that leads a G-bullet. Never count table cells, prose, the chat reply, or footer lines. Footer lines can describe gaps in plain words; each gap they mention has its G-bullet, and a marker token in a footer line carries its (Gn). Any mention of a file left unopened under data minimisation, the footer included, cites its G-bullet `GAP - not opened: <file> withheld under data minimisation (Gn)` (`house-rules.md` § 4, § 12). With no rule text relied on, the Codification line reads `not performed: no rule text relied on (Gn)`, with the G-bullet `GAP - codification check not performed: no rule text relied on`. Where no Cowork template was found, the Template line says so and the Open items list carries `NOT FOUND - Cowork Templates folder has no reg-change-triage template`. Run the final self-check (step 10), then recount and correct any figure that differs (`house-rules.md` § 9).
