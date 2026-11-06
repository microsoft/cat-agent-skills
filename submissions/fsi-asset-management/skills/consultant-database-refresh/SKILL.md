---
name: consultant-database-refresh
description: Refresh a recurring consultant questionnaire from approved content and a prior submission, showing prior versus proposed answers and aging-figure flags. Use for "refresh our eVestment profile", "update the Mercer questionnaire", "what changed since our Callan submission", "redline this manager profile", or "roll forward last year's answers". Do NOT use without a prior submission — use rfp-ddq-response-draft instead; for client mandate reviews, use institutional-client-review-prep instead; for investment commentary, use investment-commentary-draft instead; for fund comparisons, use peer-product-intelligence instead; for workbook formatting, use the built-in xlsx instead.
---

## Quick Start

User: "Update the Mercer questionnaire against our supplied prior submission."

Verify both documents, reconcile the question set, and draft the prior/proposed redline with independent refresh and wording-change flags. Keep stale values out of proposed answers.

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

**Do:** locate the new questionnaire and prior submission, draft from the approved library, diff changes, flag aging figures.
**Do not:** refresh without a prior submission, carry stale figures forward as current, reuse reworded answers without review, invent unsupported claims, or auto-submit.

## When NOT to Use

- **New or ad-hoc RFP or DDQ with no prior submission** — use `rfp-ddq-response-draft` instead.
- **Named client review meeting** — use `institutional-client-review-prep` instead.
- **Formatting, charting, or restyling an existing workbook** — use the built-in `xlsx` instead.

# Recurring Questionnaire Diff

Fill a recurring questionnaire from approved content, then show **what changed since the last
submission** so review effort goes where it belongs.

**Do:** fill from the library and prior submission, diff, and flag every figure that ages.
**Do not:** carry a performance, AUM, or headcount figure forward on your own authority. That
is the specific failure this skill exists to prevent.

> **Handoff:** if there is **no prior submission** to diff against — a new RFP, a first-time
> DDQ, an ad-hoc client questionnaire — use `rfp-ddq-response-draft` instead. This skill's value
> is the diff; without a prior submission it has none.

## Workflow

### 1. Establish both documents

You need two things:

1. The **new questionnaire template** (uploaded, or named in the prompt)
2. The **prior submission** — WorkIQ search SharePoint for the last submitted version

**If the prior submission cannot be found, stop and ask.** Do not silently fall back to
drafting fresh — the user asked for a refresh, and a fresh draft presented as a refresh hides
the fact that nothing was actually compared. Offer the handoff to `rfp-ddq-response-draft`.

**If the prior submission was located but could not be opened**, say that explicitly as
`NOT RETRIEVED` and name the document. That is a different problem from it not existing, and it
usually means retrying or asking for an upload rather than abandoning the refresh.

State both documents and the prior submission's date before proceeding.

### 2. Detect template changes

Consultant databases revise their questionnaires between cycles. Compare the new template's
question set against the prior one:

- **New questions** — no prior answer exists; these need drafting and SME review
- **Removed questions** — note them; the prior answer is retired
- **Reworded questions** — the most dangerous category. A prior answer may no longer be responsive to a subtly changed question

**Flag reworded questions explicitly.** Silently reusing an answer against a changed question
is the quiet failure mode here.

### 3. Carry forward, and mark what ages

For each question with a prior answer, carry the answer forward **and classify it**:

| State | Meaning |
|---|---|
| `UNCHANGED` | Answer still accurate and responsive |
| `UPDATED` | Library has newer approved content than the prior submission |
| `NEW` | No prior answer, **and** responsive approved content was found and drafted from |
| `GAP` | **No responsive approved answer exists for the question as now worded** — whether there was no prior answer, or the prior answer stopped being responsive after a rewording and nothing in the library covers it. Left blank with a suggested owner, **never reported as `NEW`** |

Two independent flags, set on top of whichever state applies:

| Flag | Reader-facing label | Set when |
|---|---|---|
| `figure-refresh-required` | `REFRESH REQUIRED` | The answer contains a date, figure, or fact that ages — performance, AUM, **fees, expense ratios, fee schedules, and waivers**, headcount, client counts, tenure, office locations |
| `question-changed` | `REVIEW — QUESTION CHANGED` | The question was reworded materially since the prior cycle |

Every question receives **exactly one answer-resolution state** from the table above, plus **any
independent flags that also apply**. The state answers "do we have an answer?" The flags answer
"what else is unresolved?" A question can be reworded *and* unanswered *and* carry a stale
figure — all three must stay visible.

| Independent flag | Set when |
|---|---|
| `question-changed` | The question's wording changed materially since the prior cycle |
| `figure-refresh-required` | The answer contains a time-sensitive figure needing the system of record |

**Precedence for the single state**, applied in order:

1. No responsive approved content for the question as now worded → `GAP`
2. No prior answer, but responsive approved content was found → `NEW`
3. Library has newer approved content than the prior submission → `UPDATED`
4. Otherwise → `UNCHANGED`

Then set flags independently of that choice. Two consequences to get right:

- **Question changed but the approved answer still responds** → state is `UNCHANGED` (or
  `UPDATED`), flag `question-changed`. Show the wording change; **do not invent a substantive
  change** to justify the flag.
- **Question unchanged but a figure has aged** → flag `figure-refresh-required`. Never present
  it as an unchanged, ready-to-submit answer.

`REFRESH REQUIRED` and `REVIEW — QUESTION CHANGED` remain as the reader-facing labels for the
two flags; they are flags, not states, and they never displace `GAP`. A `GAP` with a stale prior
figure is `GAP` + `figure-refresh-required`, never one at the expense of the other.

**Stale values never enter the proposed answer** regardless of state or flag. The prior figure
lives in the `PRIOR` line; the proposed answer holds a value-less verification placeholder until
the system of record supplies it.

**Every figure that changes with time carries the `figure-refresh-required` flag.** Including
ones that look static — team tenure, office count, and client numbers all drift. **Fees always
carry the flag**: an expense ratio, fee schedule, or waiver carried forward unchecked is both the
easiest error to make here and the one most likely to be treated as a misrepresentation.

Note that a fee answer whose approved text is still responsive is state `UNCHANGED` **plus**
`figure-refresh-required` — the state describes the answer, the flag describes the figure. The
flag is what prevents the value being submitted unchecked, so it is never dropped because the
state looks settled.

`NEW` and `GAP` are separate states in the change log and the footer. A question that
nothing could be drafted for is a gap the firm must fill, not a question that was answered.

**Retrieval failure is not a state.** If a library document was identified but could not be
opened, that is `NOT RETRIEVED` — reported in a **separate retrieval-failures list** with the
document named, not as a question state and not inside the question totals. Retrieval health and
answer confidence are different things, and mixing them distorts both counts. If the **prior
submission itself** could not be opened, retry once, then ask for an upload and stop — do not
assign per-question states against a document you could not read.

### 4. Never carry a stale number

In the redline, the prior column shows what was submitted. The proposed column does **not**
restate it:

```
Prior (submitted 2026-01-15):  Firm AUM: $847bn, as of 2025-12-31
Proposed:                      Firm AUM: [REFRESH REQUIRED — confirm vs. system of record,
                                          as of current quarter end]
```

The reviewer sees exactly what is being replaced, and no usable stale number sits in the field
that actually gets submitted. Never present a prior figure as current.

### 5. Build the redline

The deliverable's main value. For every question, show prior versus proposed, with changes
marked. A reviewer should be able to read only the changed items and be confident the rest is
genuinely unchanged.

Order retrieval failures first, then by state: `GAP`, `NEW`, `UPDATED`, `UNCHANGED`. Within each
state, flagged items come before unflagged ones.

Include a summary count at the top. **States partition the questions; flags overlap them**, so
report the two separately and never add them together:
*"142 questions by state: 26 gap, 9 new, 12 updated, 95 unchanged. Flags (overlapping):
31 refresh required, 4 questions reworded. 2 documents NOT RETRIEVED, listed separately and not
counted above."*

### 6. Output

Template resolution: the uploaded questionnaire's own format governs the filled response. The
accompanying change log follows user-named file → M365 `Cowork Templates/Asset Management/consultant-database-refresh/` → `references/diff-outline.md`.

Deliverables: the filled questionnaire in its native format (`.docx` or `.xlsx`), plus a
separate change log / redline.

**Never submit to a portal.** The agent drafts and diffs; the human submits.

Output length never waives attribution or the output footer: one-line answers, single table cells, inline replies, and short excerpts still carry citations and the footer. If the requested artifact is a spreadsheet, document, or deck, supply content, structure, evidence, markers, and placeholders, then hand creation or formatting to `xlsx`, `docx`, or `pptx` as appropriate.

## Performance-presentation gate

Apply the shared **Performance presentation across externally intended drafts** gate in `references/house-rules.md` before populating performance or performance-bearing attribution. Establish intended use for **each actual artifact/field**, not once for a mixed internal/client pack. Current field-appropriate system-of-record data is necessary but is not presentation permission.

For externally intended performance fields, require a compliance-approved policy applicable to that actual material type, audience and distribution, and satisfy its substantive requirements. External gross-only data, missing/inapplicable policy, unmet requirements, incompatible periods/methodology, or unresolved intended use leaves value-less `[PERFORMANCE BLOCKED — <reason>]` fields. Never compute net, normalize, or substitute a disclaimer.

Preserve the shared gate's confirmed-internal-only branch: current source figures may appear with their basis and `INTERNAL USE ONLY — NOT FOR EXTERNAL DISTRIBUTION` labels without an external presentation policy, subject to the other source/compatibility rules. Historical prior values may remain only in clearly separate internal reviewer `PRIOR` lines or gap/change records, never in proposed answers or the client deck. An externally intended draft is not internal-only merely because a reviewer sees it first; rerun the external gate before moving any internal figure into external material.

Continue every other supportable draft section, preserve existing question states/flags and internal/client separation, and record each artifact's intended use, policy applicability, unmet requirements and gate outcome in its footer. This records draft evidence, never a legal-compliance determination or distribution approval.

## Source resolution

1. **Configured MCP**
   - `eVestment` / consultant-database MCP → **read** current profile fields directly and identify drift without manual comparison. Read-only: the connector populates and compares; it never writes back or submits. Highest-value upgrade for this skill.
   - Performance system → resolves most `REFRESH REQUIRED` flags automatically.
   - HR / org system connector → current team, tenure, and headcount for staffing sections. A SharePoint HR document qualifies **only** if it is explicitly a current HR system-of-record export carrying its own as-of date; an HR library document is not automatically authoritative for a current headcount.
2. **User upload** — the new questionnaire template, and the prior submission if not in SharePoint.
3. **Firm SharePoint** — prior submission and approved content library.
4. **Flag** — `figure-refresh-required` with the prior value shown in the `PRIOR` line only, `question-changed` where wording moved, `GAP` as the state where nothing responsive exists for the question as worded, or `NOT RETRIEVED` in the separate retrieval-failures list where a document was found but could not be opened.

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
- **Never carry a time-sensitive figure forward as current.** The stale figure appears only in the labelled `PRIOR` field with its as-of date. The `PROPOSED` field stays value-less unless the current system of record supplies it.
- Never proceed as a "refresh" without a prior submission — hand off instead.
- Never reuse an answer against a reworded question without flagging it for review.
- Never auto-submit to a consultant portal or database.
- Never write firm claims the approved library does not support.
- Marketing material: label `MARKETING MATERIAL — COMPLIANCE REVIEW REQUIRED`.

See `references/house-rules.md` for citation format, gap markers, and the marketing-material rules.

## Output footer

Output length never waives this footer. A one-line answer, single table cell, inline reply, or short excerpt still carries its citations and the footer below.

```
Questionnaire: <name>          Prior submission: <document, date>
Performance intended use: <internal confirmed | external | unresolved>
Presentation policy: <name, applicability to this material, or missing/inapplicable>
Performance gate: <permitted basis and periods | BLOCKED — reason>
Policy requirements not satisfied: <requirement(s) or none>
Questions by state: <n> total — <n> GAP · <n> NEW · <n> UPDATED · <n> UNCHANGED
Flags (overlapping states, not additive): <n> REFRESH REQUIRED · <n> QUESTION CHANGED
Retrieval failures: <n> NOT RETRIEVED — documents named in a separate list, not counted above
Template changes vs. prior cycle: <n new, n removed, n reworded>
Library used: <SharePoint location>
Connectors: <MCPs used, or "none — library and prior submission only">
Figures requiring refresh: <count>
MARKETING MATERIAL — COMPLIANCE REVIEW REQUIRED. Nothing has been submitted to any portal.
```
---

## Reference files

- `references/house-rules.md` — shared decision gate, attribution and sourcing rules, blocked-vs-absent states, markers, and output footers.
- `references/diff-outline.md` — default change log: answer states, refresh flags, added/removed/changed sections, and completeness reconciliation.
