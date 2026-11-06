# Exam Request Response: workflow detail

The full text of every workflow step, moved here unchanged from SKILL.md so the skill
body stays short. SKILL.md gives each step's summary; this file is binding and is read
in full before the first step. Section numbers match the SKILL.md steps.

## Workflow steps

### 1. Parse the request list

Per `document-extraction.md` § 4.

**Preserve the examiner's numbering exactly.** Including sub-item letters, including gaps in the
sequence. Regulators and auditors track by their own numbers; a register that renumbers is
unusable in the conversation it exists to support.

**Split compound items.** An item asking for "policies, procedures, and training materials" is
**three** evidence obligations. Keep the original number and add sub-letters — `4(a)`, `4(b)`,
`4(c)` — and **state in the memo that you did so**. A register that treats a compound item as one
will under-deliver against it.

Capture per item:

| Field | Notes |
|---|---|
| Item number | **As printed**. On a numbering-gap row: `NOT FOUND - letter prints no item <n> (Gn)` |
| Request text | Verbatim |
| Period requested | "for the year ended…", "for the period 1 Jan – 30 Jun" |
| Population or sample | "all instances", "a sample of 25", "the complete list" |
| Format requested | Native files, a listing, a walkthrough |
| Due date | Per item where stated, else the list's overall date |

Where you say how far away a due date is or what weekday it falls on, in the register, memo, or
chat reply, compute it per `house-rules.md` § 5 and state the calendar date with it. If you
cannot compute it, give the calendar date only. A period or date the list does not state
follows `register-outline.md`: `NOT FOUND - ... (Gn)`, never "none stated", a dash, or blank.
A skipped item number is one register row reading `NOT FOUND - letter prints no item <n> (Gn)`
in every cell, `Item no.` included (for example `NOT FOUND - letter prints no item 6 (Gn)`, never a bare
number); never blank or a dash. An examined file with no document date reads
`NOT FOUND - <file> states no document date (Gn)` in `Document date`, its own G-bullet.

An item you cannot interpret is `GAP — item text ambiguous` and becomes a **clarification
question for the examiner**, listed in the memo. Never guess at intent — a misread request
answered confidently is worse than a question asked.

### 2. Identify owners

From the M365 record: policy ownership, prior exam responses, committee membership,
correspondence on the subject.

Each owner carries **the basis for the assignment**. No basis → `NOT FOUND — owner not
identified`, which is an open item for the response coordinator, never a guess.

In a regulator-facing register, an item with no owner is escalated in the memo, not left blank.

### 3. Locate candidate evidence

Search M365 — SharePoint, OneDrive, Teams, Outlook attachments — plus a DMS connector if one is
configured. A folder the request names is where you start, not the limit of the search: search
every location the request or any document names for an item (for example a policy folder for
item 2) before writing that item's row (`house-rules.md` § 4).

For each candidate: **document name · version · approval status · date · location · why it is a
candidate · which part of the item it addresses.**

**Responsiveness is checked against the request's own terms:**

- **Period.** A policy approved after the requested period does not evidence that period.
  `GAP — document date outside requested period`.
- **Superseded versions.** Never state when a superseded version was in force unless that
  version prints its own effective span. A successor's `Supersedes` line, its effective date,
  and the review period never supply it. Write what is printed, then
  `NOT FOUND - <doc> states no effective span (Gn)` (`house-rules.md` § 5). This applies to
  the Notes cell, the item narrative, and the chat reply.
- **Conflicting sources.** Where two files give different values for the same figure (for
  example a completion rate in committee minutes and in a workbook), report both with their
  sources and add `GAP - conflicting sources: <what> - <doc A> "<x>" vs <doc B> "<y>"` (Gn).
- **Named locations.** Where the letter, minutes, or any file names a location for evidence
  (a SharePoint site, a system, a team), search it or give it its own
  `GAP - <location> retrieval not attempted (Gn)` bullet, never another location's bullet.
- **Population.** A sample does not satisfy a request for all instances.
  `GAP — population does not match request`.
  The sample stays listed as the examined file, never relabelled "scope mismatch", and its
  responsiveness cell never reads `scope ok` while the marker says scope mismatch.
  `scope ok` and `population ok` never appear in a row with a scope or population `GAP`.
- **Scope.** A document covering a different entity, product, or business line is
  `GAP — scope mismatch`, not a candidate. Each rejected document is its own
  G-bullet (`house-rules.md` § 4).
- **Format.** Where a native file is requested and only a summary exists, say so.
- **Completeness.** A partial extract, a document with missing sections or omitted body text, or
  a partial population is `GAP`, naming what is incomplete, never `format ok`.
- **Absent record.** A record the request or a document refers to that cannot be located (for
  example a call, meeting, or approval with no record in the repository) is `NOT FOUND`,
  naming the repository searched and the record not located.

Every shortfall against any of these terms carries its marker on the row, in the
`Responsiveness check` and `Marker` columns, and has its G-bullet in the Open items list; a
`Notes` sentence can describe it in plain words (`house-rules.md` § 4).

| Outcome | Marker |
|---|---|
| Candidate located | Listed, `candidate evidence — needs owner confirmation` |
| Searched, nothing found | `NOT FOUND - <repository searched> has no record of evidence for item <n> (Gn)` |
| Repository unreachable | `NOT RETRIEVED — <repository> <reason>` |
| Found but does not match the request's terms | `GAP` for the term that fails: period, population, scope, format, or completeness |
| No document repository configured | `NEEDS FEED — document management system` |

### 4. Never assert sufficiency

**This is the hardest rule in the skill.**

The register says a document is a **candidate**. It never says the document satisfies, answers,
addresses, demonstrates, or evidences the request. Whether evidence is responsive and sufficient
is the owner's determination — `NOT DETERMINED — owner confirms`.

An item with three strong candidates is still `needs owner confirmation`. Confidence is not
authority.

### 5. Track status

| Status | Means |
|---|---|
| `not started` | No evidence search yet |
| `candidates located` | Evidence found, owner has not confirmed |
| `owner confirmed` | **Only when the owner actually confirmed in this session or in the record** |
| `gap` | Searched, nothing responsive located |
| `blocked` | Cannot proceed — reason stated |
| `clarification requested` | Item text ambiguous; question raised with the examiner |

`owner confirmed` is never inferred from the strength of the evidence. If no confirmation exists
in the record, the status is `candidates located`.

### 6. Draft narratives and the cover memo

Per-item narratives describe **what the firm is providing and what it shows on its face** — not
what it proves. Quote and cite; never characterise a document as demonstrating compliance.

**Attribute by role, document, and location.** When a narrative, a note, the memo, or the chat
reply quotes or reports text from a document, including a comment, an annotation, an email, or
an instruction embedded in an evidence document, attribute it by role, document, and location,
for example "the exam coordinator's comment on the annotated letter, p. 2". Never use the
person's name unless they are the named accountable owner, an item owner, or a preparer the
register requires (`house-rules.md` § 12).

The cover memo states: the exam or audit, the list and its date, the response date, item counts
by status **with denominators**, items where clarification is sought, and items with no evidence
located — **listed explicitly, never omitted**.

Where an item has a gap, the memo says so plainly. A regulator-facing response that quietly omits
an unanswerable item is the worst outcome this skill can produce.

**Cite every legal or regulatory statement.** Every statement in the memo, narratives, or notes
about what a law, rule, or regulatory obligation requires, permits, or prohibits carries a
primary-source citation with its as-of date (`house-rules.md` § 1, `reg-source-access.md` § 7).
If you cannot cite it that way, leave it out or list it in the memo as a question for counsel,
marked `NOT DETERMINED` with counsel as the decider. Never add background law from memory, for
example on SAR confidentiality, to explain an omission. An omission that touches a SAR reads
exactly `<category> withheld under data minimisation.` (`house-rules.md` § 12).

### 7. Emit the register, memo, and draft handoff

This skill owns the regulatory request handling, evidence mapping, owner/status logic, and response drafting. It supplies the register content, memo structure, citations, markers, and placeholders; `xlsx` builds the workbook and `docx` builds the cover memo.

If an audit or issue-management connector is configured, use it to read and pre-fill existing issue IDs, item records, owners, and current status, then reconcile the draft register against those records. The skill does not create, update, or alter records in the audit, issue-management, GRC, or Planner system. The deliverable is a draft export structured for a human response coordinator to review and submit. State that any platform update is the human's action and that the skill has not performed it. Without a connector, mark `NEEDS FEED — audit/issue platform` for fields the platform would have supplied.

Draft emails are **drafts**. If a draft object was created, say it was created and that it was not sent.

---

## Guardrails
- **Never assert that evidence satisfies a request.** Candidates only.
- **Never renumber an examiner's items.**
- **Never merge a compound item.**
- **Never mark `owner confirmed`** without an actual confirmation.
- **Never omit an item with no evidence** from the memo.
- **Never guess at an ambiguous request** — raise a clarification question.
- **Never put an uncited legal or regulatory statement** in the memo, narratives, or notes. Cite
  the primary source with its as-of date, or route the point to counsel.
- **Never treat a document as responsive** without checking period, population, scope, format,
  and completeness.
- **Nothing sends, submits, or files.** Ever.
- **Never fabricate** a figure, quote, date, source, owner, status, or identifier; use the appropriate marker instead.
- **Unreadable input is `NOT LEGIBLE`.** Name the document and page, ask for a cleaner copy, and never guess the value.
- **Never delete or overwrite existing content, prior entries, or decision sections.** Append new draft material and preserve the original.
- **Never claim a save succeeded when it failed.** Report what was produced, where it was and was not written, and what remains incomplete.
- **Quote third-party text with attribution by role, document, and location.** Never present regulator, auditor, vendor, policy, media, filing, or report wording as the firm's own. Attribute a document's author or commenter by role, document, and location (for example "the exam coordinator's comment on the annotated letter, p. 2"), never by personal name unless the person is a named owner or preparer the artifact requires (`house-rules.md` § 12). This holds in the chat reply too, including when you report an instruction embedded in a document.
- **Nothing is sent, submitted, filed, posted to, or committed in a source system.** Deliverables are drafts or exports for human review and human action.
- Markers never become values; counts state their denominators.

---

## Source resolution

Ordering follows `references/house-rules.md`. This section names what each source supplies here.

**Capabilities.** Reading supplied files (PDF, DOCX, XLSX, PPTX, CSV, images with OCR); web retrieval of public sources; Microsoft 365 search where the user has access; configured MCP connectors where present. Artifact creation is delegated — spreadsheets to `xlsx`, documents to `docx`, decks to `pptx`.

**When a capability is unavailable:** say which one, name what it would have supplied, and continue with what is available. Use `NEEDS FEED` when no source exists, `NOT RETRIEVED` when a source exists but retrieval failed, and `NOT FOUND` when a source answered with no record. Never silently skip a step and never present an unavailable source as returning nothing.

1. **Configured MCP** — DMS, audit, issue-management, GRC, and Planner connectors add repository search, existing item IDs, owner and status records, and task context for reading, pre-fill, and reconciliation only.
2. **Public primary** — Rarely has a free public source. Public regulator or auditor pages may identify context, but request ownership and evidence come from firm records.
3. **Supplied or M365 document** — Request lists, PDLs, IRLs, first-day letters, policies, procedures, evidence files, prior responses, emails, Teams messages, and owner records supply the response register.

---

## Output footer

Per `house-rules.md` § 9: destination · list identified, its date and item count · compound items
split and how many · repositories searched · connectors used or unavailable · items by status with
denominators · items with no evidence located (each item with its G-ID, for example `1(b) (G7)`) · clarification questions raised · open items by marker type (G-list) · owners unidentified (each with its G-ID) · files created and whether saves succeeded · **explicit statement that
nothing was sent · draft export prepared for human platform update · explicit statement that no source-system update was performed** · template used.

**Count from the two lists last.** Only after the rest of the draft is final, build the counts from the Open items list (G-bullets per marker type) and the Determinations outstanding list (D-bullets for `NOT DETERMINED`), unit items, for example `NOT FOUND: 5 items`. Give one number per marker type, never "plus" or a range, and list every marker type that leads a G-bullet. Never count table cells, prose, the chat reply, or footer lines. Footer lines can describe gaps in plain words; each gap they mention has its G-bullet, and a marker token in a footer line carries its (Gn). Any mention of a file left unopened under data minimisation, the footer included, cites its G-bullet `GAP - not opened: <file> withheld under data minimisation (Gn)` (`house-rules.md` § 4, § 12). With no rule text relied on, the Codification line reads `not performed: no rule text relied on (Gn)`, with the G-bullet `GAP - codification check not performed: no rule text relied on`. Where no Cowork template was found, the Template line says so and the Open items list carries `NOT FOUND - Cowork Templates folder has no exam-request-response template`. Run the final self-check (step 8), then recount and correct any figure that differs (`house-rules.md` § 9).
