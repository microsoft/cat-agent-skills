# Vendor Risk Review: workflow detail

The full text of every workflow step, moved here unchanged from SKILL.md so the skill
body stays short. SKILL.md gives each step's summary; this file is binding and is read
in full before the first step. Section numbers match the SKILL.md steps.

## Workflow steps

### 1. Establish what you were given

A "SOC 2" is frequently something else: a SOC 3, a bridge letter, an ISO certificate, a security
questionnaire, a marketing summary, or a report for a different product.

| Supplied | Treatment |
|---|---|
| SOC 2 Type II | Proceed |
| SOC 2 **Type I** | Proceed, but **design at a point in time only** — flag prominently |
| SOC 3 | A public summary. **No exceptions detail, no CUECs.** Say what it cannot tell you |
| Bridge letter | Management's assertion covering a gap period. **Not audited.** Tier it accordingly |
| ISO 27001 certificate | A different framework. Not a substitute; map only what it actually covers |
| Questionnaire or DDQ | **Self-reported and untested.** Never presented as assured |
| Marketing summary | `GAP — supplied document is a summary, not the report` |

Scanned and image-only reports are read directly (`document-extraction.md` § 1). OCR is a primary
path here — vendor reports arrive as locked or scanned PDFs constantly.

### 2. Extract the mandatory fields

All of them, per `document-extraction.md` § 4. Missing any one is a finding, not an omission:

**Type · report period · trust services criteria in scope · systems and locations in scope ·
opinion type · exceptions · CUECs · subservice organizations and their treatment.**

Three of these are the ones reviewers most often get wrong:

**Report period.** A report covering 1 Jan – 30 Jun that you are relying on in December leaves
**six months uncovered.** State the gap in months, explicitly. A bridge letter covering it is
management's unaudited assertion — say so.

**Criteria in scope.** Security only is common. Availability, Confidentiality, Processing
Integrity, and Privacy are **each** separately in or out. Out-of-scope criteria are **untested,
not passed.** Never describe a Security-only report as covering data privacy.

**Subservice organizations.** Inclusive means their controls were tested. **Carve-out means they
were not.** A carve-out for the vendor's cloud provider or subprocessor is a real, unexamined
dependency — list each carved-out organization and what it does.

### 3. Quote the opinion — never paraphrase

Unqualified · qualified · adverse · disclaimer. Quote the opinion paragraph verbatim.

**Every locator is read, not guessed.** For every quote from the report (opinion, exception,
CUEC, scope sentence), cite the section heading and page printed where the quote sits; read the
heading when you take the quote. In the self-check, re-open the page for each locator and
correct any that differ (`house-rules.md` § 6).

A qualified opinion's basis paragraph says what the qualification is about. Quote that too. A
paraphrased opinion is the most consequential possible misreading of the document.

### 4. Extract exceptions in full

Each exception with: the control it relates to · the auditor's description **verbatim** ·
management's response **verbatim** · whether the auditor commented on the response.

Never summarise an exception into "minor" or "not material." Materiality is the reviewer's
determination.

Where the report states the number of items tested and the number of deviations, record both.
"2 of 25" and "2 of 2" are very different findings.

### 5. Complementary user-entity controls — the point of the exercise

**A CUEC is a control the vendor assumes the firm operates.** The auditor's opinion depends on
them. An unadopted CUEC is an **open risk owned by the firm**, not by the vendor.

Extract **every** CUEC. For each:

| State | Means |
|---|---|
| `adopted` | The firm operates it **and there is evidence** — cite it |
| `not adopted` | It does not operate. **An open risk owned by the firm** |
| `NOT DETERMINED — owner confirms` | Default. Used wherever evidence was not located |

**Never mark a CUEC adopted without evidence.** The default is `NOT DETERMINED`.

When a searched document has no CUEC procedure (for example a header-only policy), the note
carries `GAP - partial: <what is missing>` or `NOT FOUND - <document> has no record of <x>`.
Never say what a folder "holds only" unless it was fully listed; say what was searched
(`house-rules.md` § 4).

State the count prominently: *"The report specifies 14 complementary user-entity controls. 0
confirmed adopted; 14 NOT DETERMINED."*

**A clean opinion with unadopted CUECs is not a clean result.** Say so in those words.

### 6. Public research — labelled, not exhaustive

Adverse media, litigation, breach history, regulatory actions, corporate and financial signals.

- Identity resolution applies (`house-rules.md` § 7). A vendor's name may be shared — attribute
  only with a corroborating identifier, else `UNRESOLVED MATCH — not attributed`.
- Disposition travels with every adverse item: allegation · investigation · charge · settlement
  without admission · conviction · overturned. A dismissed matter reported without its dismissal
  is wrong.
- **State coverage.** What was searched, what was not, and the limits. **A clean search is not
  proof of absence** — never write "no adverse findings." Write what was searched and what was
  found.
- With a screening connector configured, it becomes the authoritative source and the public pass
  is supplementary. Without one: `NEEDS FEED — screening provider` and the public pass is
  explicitly labelled non-exhaustive research, **not a screen**.

### 7. Residual risks and open questions

**Residual risks** are what the report leaves uncovered: out-of-scope criteria, the period gap,
carved-out subservice organizations, unadopted CUECs, exceptions without a tested remediation.
Each stated factually with its source.

**Open questions for the vendor** — the deliverable a reviewer actually uses. Specific and
answerable: "Confirm whether the Privacy criterion will be in scope for the next report period,"
not "clarify privacy posture."

### 8. Emit the memo, table, and draft handoff

The skill supplies the memo content, exception/CUEC rows, citations, markers, residual risks, and open questions; `docx` builds the memo and `xlsx` builds the workbook. Live formulas count only eligible rows and state denominators.

With a TPRM connector configured, use it to read and pre-fill the vendor record, service, contract, prior assessment IDs, current status, owners, and screening references, then reconcile the draft against those records. The skill does not create, update, or post an assessment to the TPRM, GRC, or vendor-management system. The deliverable is a draft export structured for a human third-party risk owner to review and submit. State that any platform update is the human's action and that the skill has not performed it. It still carries no rating.

---

## Guardrails
- **No risk rating, score, tier, or approval decision.**
- **Never paraphrase the opinion.** Quote it.
- **Never describe out-of-scope criteria as passed.** Untested is not passed.
- **Never mark a CUEC adopted without evidence.**
- **Never present a Type I as evidence of operating effectiveness.**
- **Never present a DDQ, questionnaire, or bridge letter as assured.**
- **Never treat a carve-out as covered.**
- **Never write "no adverse findings."** State coverage.
- **Never attribute research to the vendor without identity resolution.**
- **Never characterise an exception as minor or immaterial.**
- **Never fabricate** a figure, quote, date, source, owner, status, or identifier; use the appropriate marker instead.
- **Unreadable input is `NOT LEGIBLE`.** Name the document and page, ask for a cleaner copy, and never guess the value.
- **Never delete or overwrite existing content, prior entries, or decision sections.** Append new draft material and preserve the original.
- **Never claim a save succeeded when it failed.** Report what was produced, where it was and was not written, and what remains incomplete.
- **Quote third-party text with attribution by role, document, and location.** Never present regulator, auditor, vendor, policy, media, filing, or report wording as the firm's own. Attribute a document's author or commenter by role, document, and location (for example "the exam coordinator's comment on the annotated letter, p. 2"), never by personal name unless the person is a named owner or preparer the artifact requires, or the subject the task is about (`house-rules.md` § 12). This holds in the chat reply too, including when you report an instruction embedded in a document.
- **Nothing is sent, submitted, filed, posted to, or committed in a source system.** Deliverables are drafts or exports for human review and human action.
- Markers never become values; counts state their denominators.
- Nothing is sent to the vendor.

---

## Source resolution

Ordering follows `references/house-rules.md`. This section names what each source supplies here.

**Capabilities.** Reading supplied files (PDF, DOCX, XLSX, PPTX, CSV, images with OCR); web retrieval of public sources; Microsoft 365 search where the user has access; configured MCP connectors where present. Artifact creation is delegated — spreadsheets to `xlsx`, documents to `docx`, decks to `pptx`.

**When a capability is unavailable:** say which one, name what it would have supplied, and continue with what is available. Use `NEEDS FEED` when no source exists, `NOT RETRIEVED` when a source exists but retrieval failed, and `NOT FOUND` when a source answered with no record. Never silently skip a step and never present an unavailable source as returning nothing.

1. **Configured MCP** — TPRM, GRC, DMS, contract, and screening-provider connectors add vendor records, assessment history, contracts, authoritative screening results, current status, and owners for reading, pre-fill, and reconciliation only.
2. **Public primary** — Rarely has a free public source for the vendor assurance report. Public registries, court records, regulator releases, breach notices, and news supply labelled, non-exhaustive research only.
3. **Supplied or M365 document** — SOC reports, bridge letters, DDQs, contracts, policies, evidence of CUEC adoption, vendor correspondence, and prior assessments supply the review record.

---

## Output footer

Per `house-rules.md` § 9: destination · document type actually supplied · report type and period ·
**months of the review period not covered** · criteria in and out of scope · opinion type quoted ·
exception count · **CUEC count and how many confirmed adopted** · subservice organizations and
treatment · research coverage and limits · connectors used or unavailable · open items by marker type (G-list) ·
determinations outstanding · draft export prepared for human TPRM update · explicit statement that no source-system update was performed · files created and whether saves succeeded · template used.

**Count from the two lists last.** Only after the rest of the draft is final, build the counts from the Open items list (G-bullets per marker type) and the Determinations outstanding list (D-bullets for `NOT DETERMINED`), unit items, for example `NOT FOUND: 5 items`. Give one number per marker type, never "plus" or a range, and list every marker type that leads a G-bullet. Never count table cells, prose, the chat reply, or footer lines. Footer lines can describe gaps in plain words; each gap they mention has its G-bullet, and a marker token in a footer line carries its (Gn). Any mention of a file left unopened under data minimisation, the footer included, cites its G-bullet `GAP - not opened: <file> withheld under data minimisation (Gn)` (`house-rules.md` § 4, § 12). With no rule text relied on, the Codification line reads `not performed: no rule text relied on (Gn)`, with the G-bullet `GAP - codification check not performed: no rule text relied on`. Where no Cowork template was found, the Template line says so and the Open items list carries `NOT FOUND - Cowork Templates folder has no vendor-risk-review template`. Run the final self-check (step 9), then recount and correct any figure that differs (`house-rules.md` § 9).
