---
name: rm-call-prep-followup
description: |
  Prepare an external commercial borrower/prospect relationship call from contact history, or write a memo and draft follow-up from supplied call notes. No terms, pricing, appetite, or commitments. Use when the user says "prep my borrower call", "what do we owe this borrower", "write up this borrower call", "draft the borrower follow-up", or "what did I commit to this client". Do NOT use for internal operating/forecast reviews — use Finance forecast-review-prep if available instead. Do NOT use for standalone stakeholder Q&A — use Finance stakeholder-qa-prep if available instead. Do NOT use for company research alone — use borrower-prospect-research instead. Do NOT use for generic transcript summaries — use meeting-intel instead. Do NOT use for email operations — use outlook-email instead.
license: MIT
metadata:
  plugin: fsi-commercial-banking
  persona: relationship manager, coverage banker
---

# RM Call Prep & Follow-up

Assemble what the relationship record and the public record actually say. Draft; never send.

## Scope

**Business-workflow boundary:** a named commercial borrower/prospect relationship call, with dated contact evidence, open commitments, and banking-specific no-terms/no-credit-decision restrictions. Follow-up is bounded by supplied notes for that call. Internal operating/forecast reviews and standalone stakeholder Q&A are excluded, even when the subject is a borrower.

**Do:** compile relationship history and open items, refresh public news, draft a call memo from supplied notes, draft a follow-up email, and list tasks with owners as stated.

**Do not:** send anything, commit to terms, quote or propose pricing, signal credit appetite or likelihood of approval, or record a decision that was not in the notes. See the credit-decision gate in `references/house-rules.md`.

## When NOT to Use

- **Internal operating/forecast reviews or standalone anticipated stakeholder Q&A** — Finance `forecast-review-prep` or `stakeholder-qa-prep` if available. Follow `references/house-rules.md`; do not substitute a generic meeting pack when relationship evidence is missing.
- **Public-record research on a company where no relationship history exists** — use `borrower-prospect-research` instead.
- **Summarizing a meeting transcript or recording** — use `meeting-intel` instead.
- **Sending, formatting, or searching email** — use `outlook-email` instead.

- **Standalone covenant tests** — use covenant-compliance-check instead.
- **Annual credit-monitoring packets** — use credit-annual-review-packet instead.
- **Transaction credit-memo narrative** — use credit-memo-narrative instead.
- **Historical financial spreads** — use financial-statement-spread instead.

## Quick Start

For "write up this borrower call", use only the supplied notes; a discussion is not a decision, unstated owners/dates are TBC, and nothing is sent.

## Tool routing

1. Check actual connector availability; use `GetPluginConfig` when an expected plugin capability is missing. Do not assume a named vendor or optional Finance skill is connected.
2. For Microsoft 365 record sets use `ExecuteSql`; for topic/content discovery use `SearchM365`. Read located files with `ReadFileContent` (`full` for supported document text; `download` for exact bytes or spreadsheets). Scope reads to the borrower, purpose, and permissions.
3. Use available configured connector tools for their documented fields. If none supply an item, follow the existing source order and retain the correct gap marker; never claim a tool ran when it did not.
4. Delegate file construction to `xlsx`, `docx`, or `pptx` as specified below. Inline output is an inline draft, not a saved file. Report a save only from the action tool's successful result.

## Output format

State Prep or Follow-up. Prep sections cover dated relationship evidence, open items, exposure gaps, sourced refresh, and factual talking points. Follow-up sections cover supplied notes, decisions only if stated, an action table with stated owner/date or TBC, and draft-only email text. Include the existing footer and Sent: nothing sent.

## Mode selection

State the mode at the start of the output.

| Signal | Mode |
|---|---|
| A future meeting, "prep me for", "before my call" | **Prep** |
| Supplied notes or transcript, "write up", "follow-ups from" | **Follow-up** |
| Both a transcript and a next meeting | Ask which; do not run both silently |

---

## Mode A — Prep

### 1. Resolve the client and the meeting

Establish the named borrower/prospect and external relationship-call purpose. If unclear, ask before preparing a brief. An in-scope call with no retrievable history gets explicit gaps, not an invented relationship or a corporate operating-review agenda.

Exact legal name and identifier where known, plus the names the client is referred to in mail and chat. Meeting date, time, attendees, and stated purpose from the calendar item. Where the calendar item was not found, say so and use what the user supplied.

### 2. Relationship history from M365

Search mail, Teams messages, meeting notes, shared files, and calendar for the client. Report what was found, with dates and where it came from.

**Coverage is part of the answer.** Say what you searched and what you could reach. Where a mailbox, channel, or site could not be read, mark `NOT RETRIEVED` and name it. Never let an unsearched location look like an empty one.

### 3. Open items

From prior meeting notes, mail threads, and task lists. Per item: what it is, who owns it, when it was due, and its current status **as documented**.

Owner and date come from the record. Where the record does not state them, `TBC` — never assign an owner by inference from who happened to send the message.

### 4. Exposure and product usage

From a configured connector where one exists. Without one, this section reflects only what the user supplied or what appears in supplied files — say so. Never estimate balances, utilisation, or fee income.

Where no core, treasury, or CRM connector is configured:
`NEEDS FEED — relationship exposure source (e.g. CRM, core banking, treasury connector)`.

### 5. Public refresh

News, filings, and announcements since the last recorded contact. Use `references/public-records.md` for identity resolution and source handling. Publisher and date on every item. Secondary coverage is marked.

### 6. Talking points — facts, not positions

Each point is an observation with its source: a change in the public record, an open item, an upcoming date documented in a file. **Not** a recommendation, a product pitch with terms, or an indication of what the bank would do.

### 7. Produce

Template resolution:
1. User named a template file → use it.
2. Else search M365 for `Cowork Templates/Commercial Banking/rm-call-prep-followup/` → most recent file there.
3. Else use `references/prep-outline.md`.

Default document output is delegated to the built-in `docx`: the skill supplies sourced content, section structure, evidence, and placeholders; `docx` builds the file. Missing values remain blank or marked, never `0`.

Default `.docx` brief. Offer to save; do not save without being asked.

---

## Mode B — Follow-up

### 1. Establish what you were given

Identify the borrower/prospect call to which the supplied notes belong. Generic transcript summarization without a borrower-relationship write-up remains a built-in `meeting-intel` job.

Name the input: transcript, user-written notes, recording summary, or a chat thread. **The call memo is bounded by this input.** Where the input is partial notes, the memo is a write-up of partial notes and says so.

### 2. Draft the call memo

Attendees, date, topics discussed, decisions stated, and next steps — each traceable to the input.

- A decision appears only where the input states one. Never infer a decision from discussion.
- A topic is "discussed" only where the input shows it. Never record a topic as covered because it was on the agenda.
- Quotations must be verbatim from the input. Where the input is paraphrased notes, do not present anything as a quotation.
- Where the input does not cover something the user asked about, `NOT FOUND — not in the supplied notes`.

### 3. Action items

Per item: the action, the owner, and the due date **as stated**. `TBC` where not stated. Do not assign owners, do not set dates, and do not invent an item that follows logically but was not said.

**Unnamed and first-person implied owners remain `TBC`.** A promise written as "I will", "we will", or "I said I would" does not identify the action owner unless the supplied input explicitly maps that speaker to an identified owner. Do not fill the Owner cell with an inferred "note author", "user", "RM", or "caller", even if you add "name TBC" after it. An unnamed or inferred owner is `TBC` in the action table, task list, draft email, and footer; do not count that owner as stated. Repeat an explicitly identified owner only when the input actually assigns that action to them.

**Reconcile the footer to the final action table.** Count only explicitly identified, assigned owners as `owners stated`; every `TBC` owner counts in the unresolved-owner total. `owners stated + TBC owners = total open items`. Due-date uncertainty is counted separately and cannot turn an unknown owner into a stated one. Before returning, compare the table, draft follow-up, task list, and footer and correct any inconsistent ownership or counts.

### 4. Draft follow-up email

A draft only. Recap what the memo records, confirm the actions, and leave the sign-off for the RM.

No pricing, no terms, no commitment, no indication of credit appetite or approval likelihood, and no restatement of anything the memo marked as not found.

### 5. Tasks

Offer a task list. Creating tasks in Planner or To Do requires the user to ask for it. Report what was actually created, and report failures as failures.

### 6. Produce

Same template resolution as Mode A, falling back to `references/callmemo-outline.md`.

**Nothing is sent.** Creating a draft email object is not sending; report it as a draft created. If no draft object was created, do not describe one as existing — present the text inline.

---

## Source resolution

Ordering follows `references/house-rules.md`.

1. **Configured connector.** CRM (`Dynamics 365`, `Salesforce`) → official relationship record, pipeline, prior call reports. Core/treasury → balances and product usage.
2. **M365 via WorkIQ** — mail, Teams, meeting notes, calendar, SharePoint, Planner.
3. **Public primary** — company site, registry, EDGAR.
4. **Secondary** — marked `UNVERIFIED — secondary source`.
5. **Flag the gap.**

**If a configured connector supplies the item in front of you, use it and do not open the browser
for that item.** Browsing is for items no connector covers — narrative and covenant language, as-reported figures where the accounting basis matters, and anything whose citation needs a primary identifier. A connector being
present does not mean it holds the item: if it returns nothing, that is a connector miss, so
continue down this list. Never treat it as a dead end, and never report it as the item not
existing.

**A partial or stale connector answer is a miss for whatever it does not cover.** Where the item
is a count, an "all of X" set, an absence claim, or a point-in-time status, a non-empty connector
answer does not end the search — confirm completeness and currency against the authoritative
source, or mark that coverage `partial` and name what was not covered. A vendor's subset reported
as the whole manufactures a finding that was never established, and a connector never settles a
determination or a point-in-time status on its own.

With no CRM connector, the relationship picture is reconstructed from M365. Say that, rather than presenting it as the relationship record.

**Capabilities.** Reading supplied files (PDF, DOCX, XLSX, PPTX, CSV, images with OCR); web retrieval of public sources; Microsoft 365 search where the user has access; configured MCP connectors where present. Artifact creation is delegated — spreadsheets to `xlsx`, documents to `docx`, decks to `pptx`.

**When a capability is unavailable:** say which one, name what it would have supplied, and continue with what is available. Never silently skip a step and never present an unavailable source as returning nothing.

**Source markers.** Distinguish `NEEDS FEED` (no source exists in this session), `NOT RETRIEVED` (source exists, but retrieval failed or was denied), and `NOT FOUND` (source answered, with no record). Never collapse them.

**Artifact handoff.** The skill supplies the content, structure, formulas as specified, evidence, and placeholders; the built-in creates the file. Spreads and covenant workbooks go to `xlsx`; memos, credit write-ups, briefs, packets, and call memos go to `docx`.

## Guardrails
- **Borrower relationship work only.** No internal business-review prep or standalone stakeholder Q&A; templates and connectors do not change this boundary.
- **Nothing auto-sends.** No email, submission, posting to a system of record, file submission, or commitment to a borrower is sent or made automatically. A draft is a draft and is reported as a draft.
- **Never delete decision sections.** Existing approvals, conditions, exceptions, risk ratings, and prior decision rationale are preserved. Updates append and mark changes; they never overwrite or remove.
- **Unreadable statements stop calculations.** If a financial statement figure cannot be read with confidence, output `NOT LEGIBLE — <document>, page <n>, <line item>`, ask for a cleaner copy, never guess a digit, never infer a number from a subtotal, and never carry a partially read figure into a calculation. If extraction quality is poor across a statement, say so and stop rather than producing a spread or covenant test built on guesses.
- **Unavailable sources stay distinct.** Use `NEEDS FEED` when no source exists in this session, `NOT RETRIEVED` when a source exists but retrieval failed or was denied, and `NOT FOUND` when the source answered with no record. Never collapse them.
- **Failed saves are failures.** Never claim a save succeeded unless it was verified. Report what was produced, where it was and was not written, and what remains incomplete.
- **Missing values are never zero.** In spreadsheets, covenant worksheets, memos, and packet tables, write a blank or the applicable marker; never write `0` for missing, unreadable, unretrieved, or unavailable values.
- **Never invent facts, quotations, decisions, owners, dates, or completion claims.**
- **Report actual provenance.** Name what was searched and what was reachable. Never use a generic "M365 and public sources" line that does not describe this session.
- **A decision must be in the input.** Never infer one from discussion.
- **Owners and dates come from the record**, else `TBC`. An unnamed first-person speaker is not an identified owner; do not substitute note author/user/RM/caller, and include every unknown owner in the footer's TBC count. Footer owner counts must reconcile with the action table.
- **Quotations are verbatim** from the supplied input, or there are no quotations.
- **An unsearched location is not an empty one.** Mark `NOT RETRIEVED` and name it.
- **No pricing, terms, commitments, or credit signals.**
- **Never describe another skill's output as though it ran.**

## Output footer

```
Workflow: external commercial borrower/prospect relationship call
Mode: prep | follow-up
Client: <name as used; legal name and identifier where established>
Meeting: <date, attendees, purpose — source named, or "as supplied by user">
Input (follow-up): <transcript | user notes | partial notes | chat thread> — <what it covers>
Searched: <each location searched and whether it was reachable>
Coverage: <complete | partial — name what was not reachable>
Connectors used: <names, or "none — relationship reconstructed from M365">
Other sources used: <M365 | supplied notes | public primary | secondary, marked>
Open items: <count> — <owners stated <n>, TBC <n>>
Template: <bundled default | house template name>
Output: inline draft | file created <identifier> | creation failed
Draft email: not created | created as draft <identifier> | creation failed
Tasks: not created | created <count> in <location> | creation failed
Persistence: not attempted | saved <verified location> | failed
Sent: nothing sent
Gaps: <NOT FOUND / NOT RETRIEVED / NEEDS FEED items, or "none">
Generated: <date> — draft for RM review. No pricing, terms, commitments, or credit signals.
```

Every field states what actually happened this session. Do not report a draft email object that was not created, tasks that were not created, or a save that was not verified.

## Reference files

- `references/public-records.md` — entity identity, what each source establishes, search limits.
- `references/house-rules.md` — citation format, source tiers, credit-decision gate, markers.
- `references/prep-outline.md` — default pre-call brief structure.
- `references/callmemo-outline.md` — default call memo, follow-up email, and task list structure.
