---
name: vendor-risk-review
description: Reviews a vendor's SOC 2 report, DDQ, contract, or public vendor research against the interagency third-party risk lifecycle, covering report type, scope, opinion, exceptions, CUECs, residual risks, public findings, and open questions. Produces no risk rating and no approval decision. Use when the user says "review this SOC 2", "assess this third party", "what are the exceptions in this report", "write up a vendor risk review", or "what should we ask this vendor". Do NOT use for customer or beneficial-owner research (use kyc-research-pack), request trackers (use exam-request-response), regulatory-change triage (use reg-change-triage), enforcement read-across (use enforcement-action-review), workbook formatting (use built-in xlsx), or sending email (use built-in outlook-email).
metadata: {icon: ShieldTask}
---

## Scope

**Do:** review vendor SOC 2 reports, DDQs, contracts, CUECs, exceptions, subservice organizations, residual risks, public research, and vendor questions
**Do not:** issue a risk rating, score, tier, or approval decision, paraphrase the opinion, treat out-of-scope criteria or carve-outs as covered, mark CUECs adopted without evidence, send anything to the vendor

## When NOT to Use

- **Researching a customer or beneficial owner** — use `kyc-research-pack` instead.
- **Triaging a regulatory change** — use `reg-change-triage` instead.
- **Formatting, charting, or restyling an existing workbook** — use `xlsx` instead.

# Third-Party / Vendor Risk Review

Read the report properly, surface what it does and does not cover, and hand a reviewer the open
questions.

**No risk rating. No tier. No approval or rejection.** Those are the third-party risk owner's
determinations — `house-rules.md` § 2.

Framework: the interagency guidance on third-party relationships (OCC Bulletin 2023-17 and its
interagency counterparts), which rescinded OCC 2013-29 and 2020-10.

---

## Read first

Read these in full before step 1. They are binding; this body only summarises them.

- `references/workflow.md` — the full text of every step below, with the guardrails, source
  resolution, and footer detail.
- `references/house-rules.md` — destination gate, determination gate, identity resolution,
  markers, footers, and § 12 data minimisation (every artifact, search, and chat reply).
- `references/reg-source-access.md` — retrieving rules and guidance the review cites.
- `references/document-extraction.md` § 4 — **SOC 2 extraction. The field list there is mandatory.**
- `references/vendor-outline.md` — default memo and exceptions table: the output format.
- `references/self-check.md` — the final self-check (step 9).

---

## Workflow

### 1. Establish what you were given

Detail: `workflow.md` § 1. A "SOC 2" is often something else. Type II → proceed. Type I → design
at a point in time only, flagged. SOC 3 → no exceptions or CUECs. Bridge letter → management's
unaudited assertion. ISO certificate → a different framework. DDQ → self-reported and untested.
Marketing summary → `GAP — supplied document is a summary, not the report`. Scanned reports are
read with OCR.

### 2. Extract the mandatory fields

Detail: `workflow.md` § 2. Type · report period · criteria in scope · systems and locations ·
opinion type · exceptions · CUECs · subservice organizations and their treatment. A missing field
is a finding.

- **Period:** state the uncovered part explicitly, in months and `calendar days`.
- **Criteria:** out-of-scope criteria are **untested, not passed**.
- **Subservice organizations:** carve-out means not tested; list each one and what it does.

### 3. Quote the opinion — never paraphrase

Detail: `workflow.md` § 3. Quote the opinion paragraph, and a qualified opinion's basis
paragraph, verbatim. **Every locator is read, not guessed:** cite the section heading and page
printed where each quote sits, and re-open the page in the self-check.

### 4. Extract exceptions in full

Detail: `workflow.md` § 4. The control · the auditor's description verbatim · management's
response verbatim · any auditor comment · items tested and deviations ("2 of 25"). Never "minor"
or "not material".

### 5. Complementary user-entity controls — the point of the exercise

Detail: `workflow.md` § 5. Extract every CUEC: `adopted` only with cited evidence, `not adopted`
(an open risk the firm owns), otherwise `NOT DETERMINED — owner confirms`. State the count
prominently. A clean opinion with unadopted CUECs is not a clean result; say so in those words.

### 6. Public research — labelled, not exhaustive

Detail: `workflow.md` § 6. Adverse media, litigation, breaches, regulatory actions. Attribute
only with a corroborating identifier, else `UNRESOLVED MATCH`. Every adverse item keeps its
disposition. State what was searched and its limits; never "no adverse findings". No screening
connector → `NEEDS FEED — screening provider`, and the pass is labelled research, not a screen.
Rejected hits about private individuals are named by site and page type only: no titles, no URL
paths, captions as `[another individual] v. <entity>`.

### 7. Residual risks and open questions

Detail: `workflow.md` § 7. Residual risks: out-of-scope criteria, the period gap, carve-outs,
unadopted CUECs, untested remediations, each with its source. Open questions for the vendor are
specific and answerable.

### 8. Emit the memo, table, and draft handoff

Detail: `workflow.md` § 8. `docx` builds the memo and `xlsx` the workbook, per
`vendor-outline.md`. A TPRM connector is read for pre-fill only; the deliverable is a draft
export for the risk owner. Still no rating.

### 9. Final self-check, then count

1. Save the artifact text, the chat reply (`reply.md`), and the search log (`searches.md`: one
   `REQ | <source> | ok / failed / not attempted` line per request and one
   `HIT | <query> | <document> | used / rejected (Gn) / duplicate (Gn) / set aside` line per document returned).
2. Run `python scripts/lint_deliverable.py <artifact> --reply reply.md --searches searches.md`.
   Fix every `ERROR`, resolve every `CHECK`, and re-run until it prints `ERROR: 0`
   (`house-rules.md` § 13).
3. Work through every item in `references/self-check.md`, re-opening the page for every quote
   locator.
4. Build the footer counts from the G-list and D-list last, then recount.

---

## Guardrails

Full list: `workflow.md`, Guardrails.

- No risk rating, score, tier, or approval decision.
- Never paraphrase the opinion; never describe out-of-scope criteria as passed or a carve-out as
  covered.
- Never mark a CUEC adopted without evidence; never call an exception minor or immaterial.
- Never present a Type I as operating effectiveness, or a DDQ or bridge letter as assured.
- Never write "no adverse findings"; never attribute research without identity resolution.
- Never fabricate. Never claim a save succeeded when it failed. Nothing is sent to the vendor or
  committed in a source system.

## Output footer

Per `house-rules.md` § 9 and `workflow.md`, Output footer: destination · document type supplied ·
report type and period · **review period not covered** · criteria in and out of scope · opinion
quoted · exception count · **CUEC count and how many confirmed adopted** · subservice treatment ·
research coverage and limits · connectors · open items by marker type · determinations
outstanding · draft export, no source-system update · files and save result · template used.

### Example

```
Input: <vendor> SOC 2 Type II, Security only, period ended 2026-06-30.
Output: Review period not covered: GAP - period mismatch: 92 calendar days not covered (G1).
Privacy: GAP - scope: Privacy criteria outside the report's scope, untested (G2).
CUECs: 8 specified; each NOT DETERMINED - owner confirms adoption (D1 to D8).
Question: Confirm whether Privacy will be in scope next period (G2).
Handoff: Draft TPRM export prepared; no source-system update performed.
```

## Reference files

- `references/workflow.md` — full step text, guardrails, source resolution, footer detail.
- `references/self-check.md` — the final self-check.
- `references/house-rules.md` — gates, identity resolution, markers, footers, the lint step.
- `references/document-extraction.md` — SOC 2 mandatory fields, CUECs, subservice treatment.
- `references/reg-source-access.md` — retrieving rules and guidance the review cites.
- `references/vendor-outline.md` — default memo, exceptions and CUEC tables.
