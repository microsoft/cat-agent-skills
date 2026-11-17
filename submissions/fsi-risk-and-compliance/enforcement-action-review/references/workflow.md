# Enforcement-Action Read-Across: workflow detail

The full text of every workflow step, moved here unchanged from SKILL.md so the skill
body stays short. SKILL.md gives each step's summary; this file is binding and is read
in full before the first step. Section numbers match the SKILL.md steps.

## Workflow steps

### 1. Retrieve the order

Per `reg-source-access.md` § 1. Connector → direct route → browser → ask for an upload →
`NOT RETRIEVED`.

Establish: **agency · respondent · docket or file number · date · type** (consent order, civil
money penalty, cease and desist, settlement, litigated decision, deferred prosecution agreement).

**Type changes what the document means.** A litigated decision contains findings by a tribunal.
A consent order usually contains allegations the respondent neither admitted nor denied. Never
treat them alike.

### 2. Establish the admission posture — before anything else

Search the order for its admission language and **quote it**. Typical forms:

- "without admitting or denying the findings"
- "the Respondent neither admits nor denies"
- "the Respondent admits the facts set out in Section IV"
- findings entered after a contested hearing

Whatever it says governs every subsequent sentence about the respondent.

| Posture | How the whole memo must speak |
|---|---|
| No admission | "the order alleges", "the Bureau found for purposes of this order" |
| Partial admission | Admitted facts may be stated as admitted; **everything else remains alleged** |
| Full admission | May be stated as admitted, attributed to the order |
| Litigated finding | "the tribunal found", with the forum named |

Where the posture cannot be established → `GAP — admission posture not established`, and the memo
speaks in the alleged register throughout.

**Never write "the firm did X" where the order says it is alleged.** This is the single most
common defect in enforcement summaries and it is defamatory.

**The chat reply uses the alleged register too.** Every sentence about the respondent's
conduct, in the chat reply as well as the memo, uses the alleged register ("The order alleges
that the respondent charged overdraft fees without opt-in consent"), never a plain statement
of fact. A summary bullet list of conduct starts with "The order alleges:" and each bullet
keeps the alleged register.

### 3. Extract the conduct, the rules, and the remedies

**Alleged conduct.** What the order says happened, quoted, with paragraph citations, in the
register the admission posture requires.

**Rules actually cited.** List them exactly as the order cites them, then **retrieve each one**
(`reg-source-access.md`). Do not rely on the order's characterisation of what a rule requires —
an order is a tier 2 or 4 instrument about the respondent, not an authority on the rule's text.
Run the codification check on anything you will describe as a current requirement.

Before filling "What the rule text actually requires", retrieve the rule's definitions section.
If it is not retrieved, quote only the operative act with the covered-entity term (for example
"the institution") replaced by `[covered entity]`, and add the G-bullet naming the definitions
section, `NOT RETRIEVED - <source> (Gn)` only if a request was made and failed, otherwise
`GAP - <source> retrieval not attempted (Gn)` (`house-rules.md` § 2; `readacross-outline.md` § 4).
This applies to every quote of rule or preamble text in any cell (requirement, exemption,
condition, date ladder tier, preamble quote) and every plain-words paraphrase in the artifact
or the chat reply: "for [covered entity] with total assets of $10 billion or more", never
"firms", "banks", or "the institution" (`house-rules.md` § 2).

Distinguish clearly: a rule cited as violated · a rule cited as background · a supervisory
expectation invoked without a rule.

**Required corrective actions.** Each with its deadline, its scope, and whether it is one-time or
ongoing. Quote each remedy verbatim with its paragraph, as what the order requires:
`The order requires the respondent to "<text>" (¶ n)`. Never a plain-English paraphrase such
as "stop charging these fees" or "pay customers back": it presupposes the alleged conduct.
This applies to the memo's "what they must do" list and the chat reply too. Capture penalties, restitution, monitorships, reporting obligations, and any board-level
requirement.
Where the order gives the Effective Date no calendar date, every Deadline cell relative to it
("Within 90 days of the Effective Date", "Ongoing from the Effective Date", "From Effective
Date", "5 years from the Effective Date") leads with
`NOT FOUND - order states no calendar date (Gn); ` and then the quoted relative wording. The order
header Date and Effective Date rows put the marker first, then the explanation, and the undated
Effective Date is one G-bullet in the Open items list naming those rows (`readacross-outline.md`
§ 2 and § 5).

**What the order does not say.** Frequently as informative as what it does — root cause, control
design, how long it went undetected. State the absence rather than filling it. Each absence
is its own bullet carrying `NOT FOUND - the order states no <what> (Gn)`, and has its G-bullet.

### 4. Derive read-across themes

Convert the alleged conduct into **themes the firm can test itself against** — the control
failure pattern, not the respondent's specific facts.

A theme is a question, not a conclusion. "Are marketing disclosures reviewed against the product
terms before release, and is that review evidenced?" — not "the firm has a disclosure problem."

Anchor each theme to the order's paragraphs and to the cited rule.

### 5. Map to the firm's controls

Locate the firm's relevant controls, policies, and procedures in M365, or via a GRC connector if
one is configured.

For each theme: **control ID or policy name · version · approval status · owner · what it
addresses · what it does not.**

"What it addresses" states only the topical link, for example "covers overdraft opt-in consent
records, the subject of Theme 2". Never write that the order or a cited rule requires, applies
to, or reaches a firm control, document, or entity.

| Outcome | Marker |
|---|---|
| Control located | Listed with `NOT DETERMINED — owner assesses` |
| Searched, nothing found | `NOT FOUND — no control located for <theme>` |
| Repository unreachable | `NOT RETRIEVED — <repository> <reason>` |
| Located but version/approval unknown | `GAP — control version not established` |
| No control library configured | `NEEDS FEED — GRC control library` |

**`NOT FOUND` here is a genuine, important finding** — a theme with no located control is exactly
what the read-across exists to surface. It is never a blank.

### 6. Frame exposure as hypotheses

Every exposure observation is:

- A **question for a human owner**, not a conclusion about the firm.
- Marked `NOT DETERMINED — <function> assesses`.
- Supported by what was and was not located, with citations.

Any statement about which of the firm's entities, affiliates, accounts, products, or activities
a cited rule covers or does not cover, including the firm itself, is proposed applicability,
marked `NOT DETERMINED` with the reasoning and the citation it rests on, for the owner to
decide. Never state it as fact and never from memory. Before reasoning about coverage, retrieve
the provision that defines it (for example the rule's definition of "bank" or "covered
financial institution"). If it was not retrieved, mark the point `NOT RETRIEVED - <source> (Gn)` only if a request was made and failed, otherwise
`GAP - <source> retrieval not attempted (Gn)`, name the
provision, and write the reasoning as exactly `none - defining provision not retrieved` and
nothing else (`house-rules.md` § 2).

**Never write that the firm has a deficiency, gap in compliance, or violation.** Write that a
theme was identified, what was located, what was not, and who should assess it.

This matters beyond accuracy: a read-across memo can become discoverable. A speculative
self-accusation in a draft is a real harm. Say what was observed; let the owner conclude.

### 7. Emit the memo and table

The skill supplies the read-across content, citations, hypotheses, markers, and table structure; `docx` builds the memo and `xlsx` builds the workbook. Live formulas count only eligible rows and state denominators.

---

## Guardrails
- **Never restate an allegation as established fact.** The admission posture governs every
  sentence about the respondent, in the chat reply as well as the memo: "The order alleges
  that ...", and a summary bullet list of conduct starts with "The order alleges:" with each
  bullet kept in the alleged register. A Theme `Pattern:` line states a generic control-failure
  pattern; any respondent conduct, duration, or fact in it stays in the alleged register.
- **Never omit "without admitting or denying"** where the order contains it.
- **Never rely on the order's characterisation of a rule** — retrieve the rule.
- **Never state that the firm has a violation, deficiency, or compliance gap.** Hypotheses,
  marked `NOT DETERMINED`.
- **Never infer root cause** the order does not state.
- **Never write that the order or a cited rule requires, applies to, or reaches a firm
  control, document, or entity** when explaining a candidate control. State the topical link
  only.
- **Never treat a supervisory expectation as a rule.**
- **Never report a cited rule as a current requirement** without the codification check.
- **Never fabricate** a figure, quote, date, source, owner, status, or identifier; use the appropriate marker instead.
- **Unreadable input is `NOT LEGIBLE`.** Name the document and page, ask for a cleaner copy, and never guess the value.
- **Never delete or overwrite existing content, prior entries, or decision sections.** Append new draft material and preserve the original.
- **Never claim a save succeeded when it failed.** Report what was produced, where it was and was not written, and what remains incomplete.
- **Quote third-party text with attribution by role, document, and location.** Never present regulator, auditor, vendor, policy, media, filing, or report wording as the firm's own. Attribute a document's author or commenter by role, document, and location (for example "the exam coordinator's comment on the annotated letter, p. 2"), never by personal name unless the person is a named owner or preparer the artifact requires, or the subject the task is about (`house-rules.md` § 12). This holds in the chat reply too, including when you report an instruction embedded in a document.
- **Nothing is sent, submitted, filed, posted to, or committed in a source system.** Deliverables are drafts or exports for human review and human action.
- Markers never become values; counts state their denominators.
- Nothing is filed, sent, or committed on the firm's behalf.

---

## Source resolution

Ordering follows `references/house-rules.md`. This section names what each source supplies here.

**Capabilities.** Reading supplied files (PDF, DOCX, XLSX, PPTX, CSV, images with OCR); web retrieval of public sources; Microsoft 365 search where the user has access; configured MCP connectors where present. Artifact creation is delegated — spreadsheets to `xlsx`, documents to `docx`, decks to `pptx`.

**When a capability is unavailable:** say which one, name what it would have supplied, and continue with what is available. Use `NEEDS FEED` when no source exists, `NOT RETRIEVED` when a source exists but retrieval failed, and `NOT FOUND` when a source answered with no record. Never silently skip a step and never present an unavailable source as returning nothing.

1. **Configured MCP** — GRC control libraries, policy repositories, DMS, and legal matter systems add firm controls, owners, issues, and approval metadata where configured.
2. **Public primary** — Regulator sites, including SEC, FinCEN, OCC, FRB, and CFPB enforcement or litigation pages, supply orders, complaints, settlements, and releases. eCFR and Federal Register supply cited rule text and codification checks.
3. **Supplied or M365 document** — Firm controls, policies, procedures, prior issues, committee materials, and uploaded orders supply the read-across and control mapping.

---

## Output footer

Per `house-rules.md` § 9: destination · order identified with agency, docket, date and type ·
**admission posture, quoted** · route and retrieval date · rules cited and which were retrieved ·
codification checks performed · control repository searched · connectors used or unavailable ·
themes identified · themes with no control located · open items by marker type (G-list) · determinations
outstanding · files created and whether saves succeeded · template used.

**Count from the two lists last.** Only after the rest of the draft is final, build the counts from the Open items list (G-bullets per marker type) and the Determinations outstanding list (D-bullets for `NOT DETERMINED`), unit items, for example `NOT FOUND: 5 items`. Give one number per marker type, never "plus" or a range, and list every marker type that leads a G-bullet. Never count table cells, prose, the chat reply, or footer lines. Footer lines can describe gaps in plain words; each gap they mention has its G-bullet, and a marker token in a footer line carries its (Gn). Any mention of a file left unopened under data minimisation, the footer included, cites its G-bullet `GAP - not opened: <file> withheld under data minimisation (Gn)` (`house-rules.md` § 4, § 12). With no rule text relied on, the Codification line reads `not performed: no rule text relied on (Gn)`, with the G-bullet `GAP - codification check not performed: no rule text relied on`. Where no Cowork template was found, the Template line says so and the Open items list carries `NOT FOUND - Cowork Templates folder has no enforcement-action-review template`. Run the final self-check (step 8), then recount and correct any figure that differs (`house-rules.md` § 9).
