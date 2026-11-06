---
name: exam-request-response
description: Turns a regulator or auditor request list, PDL, IRL, or first-day letter into a tracked response register with original numbering, owners, candidate evidence, status, gaps, and a draft memo. Never asserts that evidence satisfies a request and never sends anything. Use when the user says "build a tracker for this PDL", "who owns each exam item", "find evidence for this request list", "draft responses to the first-day letter", or "what are we missing for the exam". Do NOT use for vendor SOC 2 or DDQ reviews (use vendor-risk-review), enforcement read-across (use enforcement-action-review), one policy against one rule (use policy-gap-analysis), new regulatory instruments (use reg-change-triage), document formatting (use built-in docx), or sending email (use built-in outlook-email).
metadata: {icon: ClipboardTaskListLtr}
---

## Scope

**Do:** parse regulator or auditor request lists, preserve item numbering, identify owners, locate candidate evidence, draft registers, narratives, and cover memos
**Do not:** assert evidence satisfies a request, renumber or merge items, mark owner confirmed without confirmation, omit evidence gaps, guess at ambiguous requests, send, submit, or file anything

## When NOT to Use

- **Comparing one policy against one rule** — use `policy-gap-analysis` instead.
- **Assessing a new regulatory instrument** — use `reg-change-triage` instead.
- **Formatting or restyling an existing document** — use `docx` instead.
- **Sending email**: use the built-in `outlook-email` instead.

# Exam / Audit Request-List Response Manager

Parse the request list, find the evidence, track the response. Regulator-facing work, drafted for
a named human owner.

**Nothing here is sent, submitted, or filed.** Nothing is asserted to satisfy a request — see
`house-rules.md` § 2.

---

## Read first

Read these in full before step 1. They are binding; this body only summarises them.

- `references/workflow.md` — the full text of every step below, with the guardrails, source
  resolution, and footer detail.
- `references/house-rules.md` — destination gate, determination gate, markers, footers, and § 12
  data minimisation (every artifact, search, and chat reply, declines included).
- `references/reg-source-access.md` — retrieving any rule a request item names; codification check.
- `references/document-extraction.md` — request-list parsing, item numbering, compound items.
- `references/register-outline.md` — default register columns and memo structure: the output format.
- `references/self-check.md` — the final self-check (step 8).

---

## Destination

This skill's output is almost always **regulator- or auditor-facing** (`house-rules.md` § 1) —
the highest-stakes column in the plugin. That means:

- Every item carries a **named accountable owner**.
- Every assertion is cited to a specific document with its location.
- Unresolved items are listed and individually owned. **No silent omissions.**
- The response is a **draft requiring review** before it leaves the firm.

If the user says the register is for internal planning only, treat it as an internal working
paper — but the evidence and determination rules are unchanged.

---

## Workflow

### 1. Parse the request list

Detail: `workflow.md` § 1.

- **Preserve the examiner's numbering exactly**, sub-letters and gaps included. A skipped number
  is one row reading `NOT FOUND - letter prints no item <n> (Gn)` in every cell.
- **Split compound items** into `4(a)`, `4(b)`, `4(c)` under the original number, and say so in
  the memo.
- Capture per item: number · verbatim request text · period · population or sample · format ·
  due date. A missing period or date reads `NOT FOUND - ... (Gn)`; day counts and weekdays are
  computed, with the calendar date.
- An item you cannot interpret is `GAP — item text ambiguous` and a clarification question for
  the examiner. Never guess.

### 2. Identify owners

Detail: `workflow.md` § 2. From policy ownership, prior responses, committees, correspondence,
each with its basis. No basis → `NOT FOUND - owner not identified (Gn)`, escalated in the memo.

### 3. Locate candidate evidence

Detail: `workflow.md` § 3. Search SharePoint, OneDrive, Teams, Outlook attachments, and any DMS
connector. **A folder the request names is where you start, not the limit:** search every
location the request or any document names for the item. Record per candidate: name · version ·
approval status · date · location · why candidate · which part of the item it addresses.

Check responsiveness against the request's own terms, each shortfall with its marker and G-bullet:

- **Period:** a document outside the period → `GAP — document date outside requested period`.
- **Superseded versions:** never state a superseded version's in-force span unless it prints one;
  a `Supersedes` line or the review period never supplies it →
  `NOT FOUND - <doc> states no effective span (Gn)`.
- **Conflicting sources:** both values with their sources, plus
  `GAP - conflicting sources: <what> - <doc A> "<x>" vs <doc B> "<y>" (Gn)`.
- **Named locations:** searched, or their own `GAP - <location> retrieval not attempted (Gn)`.
- **Population:** a sample against "all instances" → `GAP — population does not match request`;
  never `scope ok` or `population ok` on that row.
- **Scope, format, completeness, absent records:** as in `workflow.md` § 3; each rejected
  document is its own G-bullet.

### 4. Never assert sufficiency

Detail: `workflow.md` § 4. **The hardest rule in the skill.** A document is a **candidate**. It
never satisfies, answers, demonstrates, or evidences a request; that is
`NOT DETERMINED — owner confirms`.

### 5. Track status

Detail: `workflow.md` § 5. `not started` · `candidates located` · `owner confirmed` (only when
the owner actually confirmed, in this session or the record) · `gap` · `blocked` ·
`clarification requested`.

### 6. Draft narratives and the cover memo

Detail: `workflow.md` § 6. Narratives say what the firm provides and what it shows on its face,
quoted and cited. Attribute document text by role, document, and location, never by name unless
a required owner or preparer. The memo gives counts by status with denominators, clarification
questions, and every item with no evidence, **listed explicitly**. Every legal statement carries
a primary-source citation with its as-of date, or goes to counsel as `NOT DETERMINED`. An
omission touching a SAR reads exactly `<category> withheld under data minimisation.`

### 7. Emit the register, memo, and draft handoff

Detail: `workflow.md` § 7. `xlsx` builds the register and `docx` the memo, per
`register-outline.md`. `Owners unidentified` counts obligations (register rows), not G-bullets,
and never the numbering-gap row. A connected audit platform is read for pre-fill only; no
connector → `NEEDS FEED — audit/issue platform`. Draft emails are drafts and are not sent.

### 8. Final self-check, then count

1. Save the artifact text, the chat reply (`reply.md`), and the search log (`searches.md`: one
   `REQ | <source> | ok / failed / not attempted` line per request and one
   `HIT | <query> | <document> | used / rejected (Gn) / duplicate (Gn) / set aside` line per document returned).
2. Run `python scripts/lint_deliverable.py <artifact> --reply reply.md --searches searches.md`.
   Fix every `ERROR`, resolve every `CHECK`, and re-run until it prints `ERROR: 0`
   (`house-rules.md` § 13).
3. Work through every item in `references/self-check.md`, including the ones the script cannot
   judge.
4. Build the footer counts from the G-list and D-list last, then recount.

---

## Guardrails

Full list: `workflow.md`, Guardrails.

- Never assert that evidence satisfies a request; candidates only.
- Never renumber or merge items; never mark `owner confirmed` without a confirmation.
- Never omit an item with no evidence; never guess at an ambiguous request.
- Never put an uncited legal statement in the memo, narratives, or notes.
- Never treat a document as responsive without checking period, population, scope, format, and
  completeness. Never fabricate.
- Never claim a save succeeded when it failed. Nothing is sent, submitted, filed, or committed in
  a source system.

## Output footer

Per `house-rules.md` § 9 and `workflow.md`, Output footer: destination · list, date, and item
count · compound items split · repositories searched · connectors · items by status with
denominators · items with no evidence (each with its G-ID) · clarification questions · open items
by marker type · owners unidentified · files and save result · **nothing was sent; draft export
for human platform update; no source-system update** · template used.

### Example

```
Input: PDL item 4 asks for policies, procedures, and training for Jan-Jun 2026.
Output: split into 4(a) policy, 4(b) procedure, 4(c) training; original numbering preserved.
4(a): candidate evidence — needs owner confirmation; Status: candidates located.
4(c): NOT FOUND - Compliance SharePoint has no record of evidence for item 4(c) (G1);
      Owner: NOT FOUND - owner not identified (G2).
Handoff: Draft platform export prepared; no source-system update performed.
```

## Reference files

- `references/workflow.md` — full step text, guardrails, source resolution, footer detail.
- `references/self-check.md` — the final self-check.
- `references/house-rules.md` — gates, markers, footers, data minimisation, the lint step.
- `references/document-extraction.md` — request-list parsing, numbering, compound items.
- `references/reg-source-access.md` — retrieving a rule a request names; codification check.
- `references/register-outline.md` — register columns, memo structure, status definitions.
