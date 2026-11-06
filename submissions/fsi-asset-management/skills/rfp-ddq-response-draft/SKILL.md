---
name: rfp-ddq-response-draft
description: Draft a new institutional RFP/DDQ from approved library answers, citing each answer and separating internal gaps. Use for "draft answers to this RFP", "populate this DDQ", "respond to this due-diligence request", "fill what we can from the library", or "identify unanswered questionnaire items". Do NOT use for recurring profiles with a prior submission to diff — use consultant-database-refresh instead; for client mandate reviews, use institutional-client-review-prep instead; for product comparisons, use peer-product-intelligence instead; for investment commentary, use investment-commentary-draft instead; for document formatting, use the built-in docx instead.
---

## Quick Start

User: "Draft answers to this new institutional DDQ from the supplied approved library."

Preserve every question and limit; produce cited draft answers and a separate internal gap list. Block unsupported or policy-ineligible performance fields, not the rest of the response.

## Runtime capability checks

Read `references/house-rules.md` before drafting. "WorkIQ" below names a search capability, not an assumed callable API. Use `SearchM365` for M365 content discovery when available and `ExecuteSql` for supported structured record reads (for example, dated calendar records); inspect the actual tool schema before calling it. Check configured connector capabilities rather than assuming a named provider exists. Public retrieval may use an available direct-fetch tool or the browser; discovery alone is not source evidence. If a capability or destination skill is unavailable, disclose that specific limitation and use the existing upload/gap path, never invent a call or claim it ran. Create files only through the available format skill; otherwise provide the drafted content and state that file creation remains incomplete.

## Workflow handoffs — no scope expansion

Only perform the workflow defined in this skill's Scope. For a different job, check that the destination exists and accepts it before handing off; never claim an unavailable skill ran. Do not reinvoke yourself for the current job.

- For a new/ad-hoc institutional questionnaire, use rfp-ddq-response-draft instead.
- For a recurring consultant profile with a prior submission to compare, use consultant-database-refresh instead.
- For named fund/portfolio/strategy periodic investor commentary, use investment-commentary-draft instead.
- For a matched two-filing issuer-language diff, use security-research-brief instead.
- For a fund/share-class product comparison, use peer-product-intelligence instead.
- For a named institutional investment-client mandate review, use institutional-client-review-prep instead.

## Scope

**Do:** shred the questionnaire, retrieve approved answers, adapt wording, cite every answer, surface gaps and stale items.
**Do not:** invent unsupported answers, state current figures outside the system of record, upgrade hedged language, or auto-submit.

## When NOT to Use

- **Recurring consultant-database questionnaire with a prior submission to diff** — use `consultant-database-refresh` instead.
- **Competitor product matrix** — use `peer-product-intelligence` instead.
- **Investment commentary or strategy letters** — use `investment-commentary-draft` instead.
- **Formatting or restyling an existing document** — use the built-in `docx` instead.

# RFP / DDQ First-Draft Answering

Turn an incoming questionnaire into a cited first draft built from approved firm content, plus
an honest list of what the library could not answer.

**Do:** shred the questionnaire, retrieve the closest approved answers, adapt wording to the
question asked, cite every answer, and surface gaps with owners.
**Do not:** invent an answer the library does not support, state a current performance, AUM, or
fee figure from anything but the system of record, or soften a gap into vague language. An empty
answer with an owner is useful. A plausible invented answer is a liability.

> **Handoff:** if the user is updating a **recurring** consultant or database questionnaire and
> a prior submission exists, `consultant-database-refresh` is the right skill — it diffs against
> the last submission so the team reviews only what changed. This skill is for a **new or
> ad-hoc** questionnaire where there is no prior submission to diff.

## Workflow

### 1. Shred the questionnaire

Parse the uploaded document into discrete, numbered questions. Preserve the original
numbering, section headings, and any word or character limits — these matter at submission.

Record for each question: its number, section, the question text, any stated limit, and the
answer format required (narrative, yes/no, table, attachment).

**If the document is a spreadsheet**, treat each row as a question and preserve the column
structure for the response.

Report the count before drafting: *"Parsed 142 questions across 9 sections."* If parsing was
partial — a scanned PDF, a locked form — **say which sections you could not read** rather than
silently answering fewer questions than were asked.

### 2. Locate the approved library

Resolve in this order:

1. A library location the user named in the prompt
2. WorkIQ search across SharePoint for prior RFP/DDQ responses and approved boilerplate
3. Ask, naming what you're looking for: *"Which SharePoint library holds your approved RFP answers?"*

**State which library you used** in the footer so the user corrects it once and reuses it.

Cowork skills cannot read a runtime config file — the location is established per session or
named in the prompt.

### 3. Retrieve and draft

For each question, find the closest approved answer and adapt it to what was actually asked.

**Adapting means** re-scoping, trimming to a word limit, and matching the question's framing.
**It does not mean** strengthening a claim, adding specifics the source lacked, or merging two
answers into an assertion neither made.

Tag every answer with a confidence state:

| State | Meaning |
|---|---|
| `MATCHED` | A close approved answer exists; adapted with minor edits |
| `ADAPTED` | Assembled from related approved content; needs SME review of the fit |
| `GAP` | The library has nothing responsive. Left blank with a suggested owner |
| `STALE` | An answer exists but carries a date, figure, or fact that must be refreshed |

**Never leave a question silently unanswered.** Every question gets a state.

### 4. Flag every figure that ages

Performance, AUM, headcount, client counts, and fee figures are **never** carried forward on
the agent's authority. The placeholder replaces the number — nothing sits next to it:

```
The firm managed [VERIFY vs. system of record — total firm AUM, as of current quarter end]
in assets.
```

No prior value appears anywhere in the answer block. If a prior document states a figure, that
belongs in the gap list, which is the reviewer-facing section.

This is the most common failure mode in RFP work and the most likely to cause a problem. Treat
a confidently stated stale number as worse than a blank — and a flagged stale number as barely
better, because it can still be copied into a live submission unchanged.

### 5. Build the gap list — internal, not part of the response

A separate **internal reviewer appendix** listing every `GAP` and `STALE` item: question number,
what is needed, the prior value where one is known *(reference only)*, and a suggested owner
(investment team, compliance, performance, HR, legal) inferred from the subject matter. Label
owners as suggestions — you are not assigning work.

**The gap list is a working document for the response team. It is never part of the submitted
questionnaire and must be removed before the response goes to the prospect, client, or
consultant.** State that on the section itself. It is the only place a prior figure may appear,
and it exists precisely because that figure must not travel in the answer.

Also list, separately, any library document that was **identified but could not be opened** as
`NOT RETRIEVED`, naming the document. A source you could not read is not a source that lacks the
answer, and a reviewer needs to know the difference before deciding the library has a gap.

### 6. Output

Template resolution: user-named file → M365 `Cowork Templates/Asset Management/rfp-ddq-response-draft/` → `references/answer-format.md`.

Deliverable: `.docx` by default, or the questionnaire's native format when it was a
spreadsheet — preserving original numbering so the response maps to the request. Answers
carry their citation and state. **Deliver the gap list as a separate internal file**, not as a
trailing section of the response document, so it cannot be submitted by accident.

Output length never waives attribution or the output footer: one-line answers, single table cells, inline replies, and short excerpts still carry citations and the footer. If the requested artifact is a spreadsheet, document, or deck, supply content, structure, evidence, markers, and placeholders, then hand creation or formatting to `xlsx`, `docx`, or `pptx` as appropriate.

## Performance-presentation gate

Apply the shared **Performance presentation across externally intended drafts** gate in `references/house-rules.md` before populating performance or performance-bearing attribution. Establish intended use for **each actual artifact/field**, not once for a mixed internal/client pack. Current field-appropriate system-of-record data is necessary but is not presentation permission.

For externally intended performance fields, require a compliance-approved policy applicable to that actual material type, audience and distribution, and satisfy its substantive requirements. External gross-only data, missing/inapplicable policy, unmet requirements, incompatible periods/methodology, or unresolved intended use leaves value-less `[PERFORMANCE BLOCKED — <reason>]` fields. Never compute net, normalize, or substitute a disclaimer.

Preserve the shared gate's confirmed-internal-only branch: current source figures may appear with their basis and `INTERNAL USE ONLY — NOT FOR EXTERNAL DISTRIBUTION` labels without an external presentation policy, subject to the other source/compatibility rules. Historical prior values may remain only in clearly separate internal reviewer `PRIOR` lines or gap/change records, never in proposed answers or the client deck. An externally intended draft is not internal-only merely because a reviewer sees it first; rerun the external gate before moving any internal figure into external material.

Continue every other supportable draft section, preserve existing question states/flags and internal/client separation, and record each artifact's intended use, policy applicability, unmet requirements and gate outcome in its footer. This records draft evidence, never a legal-compliance determination or distribution approval.

## Source resolution

1. **Configured MCP**
   - RFP platform (`Loopio`, `Responsive`, `Qvidian`) → curated answers **with approval status**, which is the highest-value upgrade for this skill: it replaces inferred approval with recorded approval.
   - CRM (`Salesforce`, `Dynamics`) → prospect-specific fields and relationship context.
   - Performance system → verified returns and AUM, removing most `[VERIFY]` flags.
2. **User upload** — prior responses, firm boilerplate, the current ADV.
3. **Firm SharePoint** — the approved answer library and prior RFPs.
4. **Flag** — `GAP` with an owner. Never fill from general knowledge.

**If a configured MCP supplies the item in front of you, use it and do not open the browser
for that item.** Browsing is for items no connector covers — narrative text, as-reported figures where the accounting basis matters, and anything whose citation needs a primary identifier. A connector being
present does not mean it holds the item: if it returns nothing, that is a connector miss, so
continue down this list. Never treat it as a dead end, and never report it as the item not
existing.

**A partial or stale connector answer is a miss for whatever it does not cover.** Where the item
is a count, an "all of X" set, an absence claim, or a point-in-time status, a non-empty connector
answer does not end the search — confirm completeness and currency against the authoritative
source, or mark that coverage `partial` and name what was not covered. A vendor's subset reported
as the whole manufactures a finding that was never established, and a connector never settles a
determination or a point-in-time status on its own.


**Capabilities.** Reading supplied files (PDF, DOCX, XLSX, PPTX, CSV, images with OCR); web retrieval of public sources; Microsoft 365 search where the user has access; configured MCP connectors where present. Artifact creation is delegated — spreadsheets to `xlsx`, documents to `docx`, decks to `pptx`.

**When a capability is unavailable:** say which one, name what it would have supplied, and continue with what is available. Never silently skip a step and never present an unavailable source as returning nothing. If no source exists for a field, use `NEEDS FEED — <source that would supply it>`; if a source exists but retrieval failed or access was denied, use `NOT RETRIEVED — <source> <failure>`; if the source answered and has no record, use `NOT FOUND — <source> has no record for <what>`.

## Guardrails

- Current source data alone never authorizes external performance. Apply the actual-output presentation gate; preserve its internal-only branch and separate historical reviewer records without allowing an external-field bypass.

- Output length never waives attribution or the output footer. A one-line answer, single table cell, inline reply, or short excerpt still carries its citation and this skill's footer.
- Never fabricate a figure, quote, date, source, approval status, or document state. Use the skill's gap marker instead.
- If an input page or source document is unreadable, report `NOT LEGIBLE — <document>, page <n>`, ask for a cleaner copy, and never guess.
- Distinguish unavailable sources exactly: no source exists is `NEEDS FEED`; a source exists but retrieval failed or was denied is `NOT RETRIEVED`; a source answered and has no record is `NOT FOUND`. Never collapse these outcomes.
- Never delete or overwrite existing content, prior submissions, decision sections, reviewer notes, or source files; append, redline, or preserve unless the user explicitly supplies a new blank artifact.
- Format handoffs: spreadsheets go to `xlsx`, documents to `docx`, decks to `pptx`. This skill supplies content, structure, evidence, markers, and placeholders; the built-in creates or formats the file.
- If a save, export, or write fails, never claim it succeeded. Report what was produced, where it was and was not written, and what remains incomplete.
- Nothing is sent, submitted, filed, posted, committed to a consultant database, client portal, other portal/database, or emailed by this skill. A draft is a draft and is reported as a draft; the human submits.
- Reuse firm-approved library material only within the firm's authorized rights and this task. For third-party filings, policies, or other protected text, use only brief necessary excerpts where permitted; otherwise summarize with attribution or request authorized source material. Attribution does not grant reproduction rights. Never present third-party wording as the firm's own or relabel a source's classification into another scheme.
- **Never write a claim about the firm that approved content does not support.** Not process, not people, not results, not risk controls.
- **Never state a current performance, AUM, fee, or headcount figure unless it came verbatim from an uploaded system-of-record export or a field-appropriate connector.** Otherwise the field is a value-less `[VERIFY vs. system of record]` placeholder. An approved library document is not evidence of currency.
- Never upgrade hedged approved language into confident language.
- Never present an answer as approved when you could not establish that it was — say the approval state is unknown.
- Preserve original question numbering and any word limits.
- The deliverable is marketing material: label it `MARKETING MATERIAL — COMPLIANCE REVIEW REQUIRED`.
- Nothing auto-sends. The human submits.

See `references/house-rules.md` for citation format, gap markers, and the marketing-material rules.

## Output footer

Output length never waives this footer. A one-line answer, single table cell, inline reply, or short excerpt still carries its citations and the footer below.

```
Questions parsed: <n> across <n> sections
Performance intended use: <internal confirmed | external | unresolved>
Presentation policy: <name, applicability to this material, or missing/inapplicable>
Performance gate: <permitted basis and periods | BLOCKED — reason>
Policy requirements not satisfied: <requirement(s) or none>
Answered: <n> MATCHED · <n> ADAPTED · <n> STALE · <n> GAP
Library documents identified but unreadable: <n> NOT RETRIEVED — named in the gap list
Library used: <SharePoint location>
Template: <file used>
Connectors: <MCPs used, or "none — approved library only">
Figures needing verification: <count>
MARKETING MATERIAL — COMPLIANCE REVIEW REQUIRED. Draft for SME review; nothing has been sent.
```
---

## Reference files

- `references/house-rules.md` — shared decision gate, attribution and sourcing rules, blocked-vs-absent states, markers, and output footers.
- `references/answer-format.md` — RFP/DDQ answer construction: reuse rules, answer states, evidence requirements, and reviewer hand-off.
