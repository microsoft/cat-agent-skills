---
name: policy-gap-analysis
description: Compares a firm policy to a regulation clause by clause, giving a coverage table with verbatim excerpts, suggested edits and a memo. Reports coverage states; never concludes compliance. Use when the user says "does our policy cover this regulation", "where are the gaps against this rule", "map our procedure to the requirements", "compare our AML policy to the rule", or "what needs to change in this policy". Do NOT use for customer or counterparty research or EDD packs (use kyc-research-pack), firm-wide triage of a new rule (use reg-change-triage), enforcement read-across (use enforcement-action-review), exam requests (use exam-request-response), vendor SOC 2 reviews (use vendor-risk-review), workbook formatting (use built-in xlsx), or sending email (use built-in outlook-email).
metadata: {icon: DocumentBulletListMultiple}
---

## Scope

**Do:** compare specific regulation sections to a firm policy clause by clause, quote both sides, assign coverage states, suggest owner-reviewed edits
**Do not:** conclude compliant, non-compliant, or in violation, score unretrieved requirements, treat drafts or unretrieved referenced documents as coverage, alter source systems, send, or file anything

## When NOT to Use

- **Triaging a newly published rule across the firm** — use `reg-change-triage` instead.
- **An examiner request list or PDL response tracker** — use `exam-request-response` instead.
- **Formatting, charting, or restyling an existing workbook** — use `xlsx` instead.

# Policy-to-Regulation Gap Analysis

Clause-by-clause: what the regulation requires, what the policy says, and whether the second
addresses the first.

**This skill never concludes compliance.** It reports coverage states with both sides quoted.
Whether the firm complies is a determination by a qualified owner — `house-rules.md` § 2.

---

## Read first

Read these in full before step 1. They are binding; this body only summarises them.

- `references/workflow.md` — the full text of every step below, with the guardrails, source
  resolution, and footer detail.
- `references/house-rules.md` — destination gate, determination gate, authority tiers, markers,
  footers, and § 12 data minimisation (every artifact, search, and chat reply, declines included).
- `references/reg-source-access.md` — routing, the codification gap, precision filtering.
- `references/document-extraction.md` — policy version and approval discipline.
- `references/gap-outline.md` — default table and memo structure: the output format.
- `references/self-check.md` — the final self-check (step 7).

---

## Workflow

### 1. Establish both sides before comparing

Detail: `workflow.md` § 1.

- **Regulation:** agency · citation · type · tier · sections in scope. Retrieve per
  `reg-source-access.md` and run the **codification check**; an effective later final rule
  governs (`PENDING CODIFICATION`), a future one is a forthcoming change in the `Source` cell.
  House-rules markers only, plus `PROPOSED DRAFTING`.
- **Policy:** name · version · approval status · approval date · owner · scope. A draft is
  `DRAFT — not approved`, never the control of record. When the policy given is a draft or
  superseded, find and open the approved version and state
  `Control of record: <doc> v<x>, approved <date> (<location>)` in § 2 and the chat reply: a fact,
  never a D-bullet. Version or approval unknown → `GAP — policy version not established`, and no
  row is scored as covered.
- **Scope is load-bearing.** Quote the policy's scope clause. Which entities, accounts, or
  products the rule covers is proposed applicability: `NOT DETERMINED`, compliance owner decides,
  with the retrieved defining provision cited. If that provision was not retrieved, the reasoning
  reads exactly `none - defining provision not retrieved`. No hedge words.

### 2. Decompose the regulation into requirements

Detail: `workflow.md` § 2.

- One row per discrete requirement; a sentence with three obligations is three rows. Keep
  conditions, thresholds, and exemptions with the requirement. Requirements are scored;
  permissions and safe harbours are recorded, not scored.
- Quote each requirement verbatim. With the definitions section not retrieved, every entity term
  in any quote or paraphrase reads `[covered entity]`, and the definitions section gets its
  G-bullet.
- **Exemption cell, three forms only (hard stop):** verbatim quote with citation;
  `none stated in <citation>`; or `NOT DETERMINED - <decider> decides (Dn)`. Whether the firm can
  use an exemption is for the **compliance owner**; only its legal meaning goes to counsel.

### 3. Locate the policy text for each requirement

Detail: `workflow.md` § 3. Quote verbatim with section and page. Search the whole document,
appendices, and referenced procedures before concluding absence. A document incorporated by
reference is not coverage until retrieved and analysed: otherwise `NOT RETRIEVED` (request failed)
or `GAP - <name> retrieval not attempted (Gn)`. State only the topical link for a match.

### 4. Assign a coverage state

Detail: `workflow.md` § 4. `covered` · `partial` (say which part is missing, with its (Gn)) ·
`not found` (searched and absent) · `conflicts` (quote both sides) · `NOT DETERMINED`. Substance,
not vocabulary; the same act, not the same topic. A requirement whose text was not retrieved is
never scored. Adequacy is not a coverage question.

### 5. Suggest edits

Detail: `workflow.md` § 5. For every `partial`, `not found`, or `conflicts` row, propose policy
language marked `PROPOSED DRAFTING`, anchored to the requirement it serves. Never presented as
approved and never written into the policy.

### 6. Emit the table and memo

Detail: `workflow.md` § 6. Build the table with `xlsx` and the memo with `docx`, following
`gap-outline.md`. Counts carry denominators and exclude marker rows, which stay visible. The memo
headline and the chat reply read, for example,
`covered 3 of 9; partial 4 of 9 (G11 to G14); not found 2 of 9 (G9, G10); conflicts 1 of 9 (G8)`.

### 7. Final self-check, then count

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

- Never "compliant", "non-compliant", or "in violation"; coverage states only.
- Never score a requirement whose text was not retrieved, a draft as the control of record, or an
  incorporated document you did not retrieve.
- Never state what a rule covers as fact or from memory; never "will require you to".
- Never paraphrase either side into the table; never merge compound requirements.
- Never present suggested language as approved; never invent a marker; never fabricate.
- Never claim a save succeeded when it failed. Nothing is written into a policy, sent, filed, or
  committed in a source system.

## Output footer

Per `house-rules.md` § 9 and `workflow.md`, Output footer: destination · regulation with tier,
sections, retrieval date and route · codification check and result · policy version and approval ·
requirements analysed and scored · coverage headline with G-IDs · open items by marker type ·
determinations outstanding · files and save result · template used.

### Example

```
Input: CDD Policy v3.2 (approved 2026-03-18) against 31 CFR 1010.230(b)(2), (d) and (g).
Row 1010.230-2 | Requirement: "[covered entity] shall ... document the verification method
  used" (31 CFR 1010.230(b)(2)) | Policy § 4.2: "Beneficial ownership information is verified
  at onboarding." | Coverage: partial - no text on recording the method used (G4)
Row 1010.230-4 | Exemption: NOT DETERMINED - compliance owner decides (D2)
Headline: covered 2 of 9; partial 3 of 9 (G4 to G6); not found 3 of 9 (G7 to G9); conflicts 1 of 9 (G3)
D-bullet: D2 - NOT DETERMINED - can the firm rely on the (g) exemption - compliance owner decides
Suggested edit: PROPOSED DRAFTING - "Record the verification method used and its result." (1010.230-2)
```

---

## Reference files

- `references/workflow.md` — full step text, guardrails, source resolution, footer detail.
- `references/self-check.md` — the final self-check.
- `references/house-rules.md` — gates, tiers, markers, footers, data minimisation, the lint step.
- `references/reg-source-access.md` — routing, codification gap, citation fields.
- `references/document-extraction.md` — policy version, approval status, scope, incorporation.
- `references/gap-outline.md` — default coverage table and memo structure.
