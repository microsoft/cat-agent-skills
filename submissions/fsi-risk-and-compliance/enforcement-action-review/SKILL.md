---
name: enforcement-action-review
description: Reads a public enforcement action, complaint, settlement, or consent order and produces a read-across against the firm's controls covering alleged conduct, cited rules, and corrective actions. Exposure is framed as hypotheses for human review, never admissions. Use when the user says "could this happen here", "what does this consent order mean for us", "lessons learned from this enforcement action", "read this across to our controls", or "which controls does this implicate". Do NOT use for customer or counterparty research (use kyc-research-pack), new rules, bulletins, SR letters, or proposed or final regulations (use reg-change-triage), request trackers (use exam-request-response), document formatting (use built-in docx), or sending email (use built-in outlook-email).
metadata: {icon: Gavel}
---

## Scope

**Do:** retrieve enforcement orders, quote admission posture, extract alleged conduct, cited rules, remedies, derive read-across themes, map candidate firm controls
**Do not:** restate allegations as fact, rely on an order's rule characterization, state the firm has a violation, deficiency, or compliance gap, infer root cause, file, send, or commit anything

## When NOT to Use

- **Researching a customer or counterparty** — use `kyc-research-pack` instead.
- **Triaging a newly published rule** — use `reg-change-triage` instead.
- **Formatting or restyling an existing document** — use `docx` instead.

# Enforcement-Action Read-Across

What the regulator actually penalised, what it required, and where the firm should look.

**Two directions of care.** Allegations against the respondent are not facts about the
respondent. Exposure observations about the firm are not admissions by the firm. Both rules hold
at once — `house-rules.md` § 2 and § 6.

---

## Read first

Read these in full before step 1. They are binding; this body only summarises them.

- `references/workflow.md` — the full text of every step below, with the guardrails, source
  resolution, and footer detail.
- `references/house-rules.md` — destination gate, determination gate, authority tiers, markers,
  footers, and § 12 data minimisation (every artifact, search, and chat reply, declines included).
- `references/reg-source-access.md` — retrieving the order and the rules it cites.
- `references/document-extraction.md` — consent-order extraction, allegation vs finding.
- `references/readacross-outline.md` — default memo and control-gap table: the output format.
- `references/self-check.md` — the final self-check (step 8).

---

## Workflow

### 1. Retrieve the order

Detail: `workflow.md` § 1. Connector → direct route → browser → ask for an upload →
`NOT RETRIEVED`. Establish agency · respondent · docket · date · type. A litigated decision holds
findings; a consent order usually holds allegations. Never treat them alike.

### 2. Establish the admission posture — before anything else

Detail: `workflow.md` § 2. Find and **quote** the admission language. It governs every sentence
about the respondent: no admission → "the order alleges"; partial → only admitted facts stated as
admitted; litigated → "the tribunal found". Posture unknown →
`GAP — admission posture not established`, and the alleged register throughout. **The chat reply
uses the alleged register too**; a conduct list starts "The order alleges:". Never "the firm did
X" where the order alleges it.

### 3. Extract the conduct, the rules, and the remedies

Detail: `workflow.md` § 3.

- **Alleged conduct:** quoted, with paragraph citations, in the posture's register.
- **Rules cited:** list them as cited, then **retrieve each one**; never rely on the order's
  characterisation. Run the codification check. With the definitions section not retrieved,
  every entity term in a rule quote or paraphrase reads `[covered entity]`.
- **Remedies:** each with deadline, scope, one-time or ongoing, quoted as
  `The order requires the respondent to "<text>" (¶ n)`. Never a plain-English paraphrase such as
  "stop charging these fees": it presupposes the conduct. An undated Effective Date makes every
  relative deadline lead with `NOT FOUND - order states no calendar date (Gn); "<wording>"`.
- **What the order does not say:** root cause, control design, detection interval, population.
  Each absence is its own bullet leading with `NOT FOUND - the order states no <what> (Gn)`.

### 4. Derive read-across themes

Detail: `workflow.md` § 4. Turn the alleged conduct into control-failure patterns the firm can
test itself against, each phrased as a question and anchored to the order's paragraphs and the
cited rule. Never a conclusion about the firm.

### 5. Map to the firm's controls

Detail: `workflow.md` § 5. Locate controls in M365 or a GRC connector: control ID or policy ·
version · approval status · owner · what it addresses (topical link only) · what it does not. A
theme with no control is `NOT FOUND - <repository> has no record of a control for <theme> (Gn)`:
a genuine finding, never a blank.

### 6. Frame exposure as hypotheses

Detail: `workflow.md` § 6. Every observation is a question for a named function, marked
`NOT DETERMINED — <function> assesses`, with what was and was not located. Coverage of the firm's
entities or products is proposed applicability, with the retrieved defining provision cited, or
`none - defining provision not retrieved`. **Never write that the firm has a deficiency, gap, or
violation.** A read-across memo can become discoverable.

### 7. Emit the memo and table

Detail: `workflow.md` § 7. `docx` builds the memo and `xlsx` the workbook, per
`readacross-outline.md`. Counts state their denominators.

### 8. Final self-check, then count

1. Save the artifact text, the chat reply (`reply.md`), and the search log (`searches.md`: one
   `REQ | <source> | ok / failed / not attempted` line per request and one
   `HIT | <query> | <document> | used / rejected (Gn) / duplicate (Gn) / set aside` line per document returned).
2. Run `python scripts/lint_deliverable.py <artifact> --reply reply.md --searches searches.md`.
   Fix every `ERROR`, resolve every `CHECK`, and re-run until it prints `ERROR: 0`
   (`house-rules.md` § 13).
3. Work through every item in `references/self-check.md`, including the alleged-register grep
   the script cannot fully judge.
4. Build the footer counts from the G-list and D-list last, then recount.

---

## Guardrails

Full list: `workflow.md`, Guardrails.

- Never restate an allegation as fact, in the memo or the chat reply; never omit "without
  admitting or denying" where the order has it.
- Never rely on the order's characterisation of a rule; retrieve it, and run the codification
  check before calling it current.
- Never state that the firm has a violation, deficiency, or compliance gap; never infer a root
  cause the order does not state.
- Never paraphrase a remedy; quote it. Never treat a supervisory expectation as a rule.
- Never fabricate. Never claim a save succeeded when it failed. Nothing is filed, sent, or
  committed on the firm's behalf.

## Output footer

Per `house-rules.md` § 9 and `workflow.md`, Output footer: destination · order with agency,
docket, date, and type · **admission posture, quoted** · route and retrieval date · rules cited
and retrieved · codification checks · control repository searched · connectors · themes and
themes with no control · open items by marker type · determinations outstanding · files and save
result · template used.

### Example

```
Input: Agency consent order, Respondent neither admits nor denies findings.
Output: Admission posture quoted; conduct described as "the order alleges" throughout.
Theme 1: Are fee disclosures reviewed against product terms before release?
Control mapping: NOT FOUND - no control located for Theme 1 (G1).
Observation: NOT DETERMINED - Compliance assesses (D1); no firm violation stated.
```

## Reference files

- `references/workflow.md` — full step text, guardrails, source resolution, footer detail.
- `references/self-check.md` — the final self-check.
- `references/house-rules.md` — gates, tiers, markers, footers, data minimisation, the lint step.
- `references/reg-source-access.md` — retrieving the order and the cited rules.
- `references/document-extraction.md` — consent-order extraction, allegation vs finding.
- `references/readacross-outline.md` — default memo and control-gap table.
