---
name: reg-change-triage
description: Triages a new or changed regulatory instrument into a decision-ready brief covering what changed, date ladder, affected parties, obligations cited to primary source, candidate policies, gaps, and actions. Applicability is proposed with reasoning, never decided. Use when the user says "what does this new rule mean for us", "triage this SR letter", "summarize the impact of this regulatory change", "when do we have to comply", or "which policies does this hit". Do NOT use for enforcement actions, settlements, or consent orders (use enforcement-action-review), one policy against one rule (use policy-gap-analysis), request trackers (use exam-request-response), a vendor SOC 2 (use vendor-risk-review), workbook formatting (use built-in xlsx), or sending email (use built-in outlook-email).
metadata: {icon: DocumentSearch}
---

## Scope

**Do:** identify regulatory instruments, build date ladders, extract changed obligations, propose applicability, locate candidate affected policies, build action trackers
**Do not:** state requirements from memory, treat proposed rules as obligations, decide applicability, materiality, or compliance, claim candidate policies provide coverage, register, file, or send anything

## When NOT to Use

- **Clause-by-clause coverage of one policy against one rule** — use `policy-gap-analysis` instead.
- **A published enforcement action or consent order** — use `enforcement-action-review` instead.
- **A vendor SOC 2 or third-party controls review** — use `vendor-risk-review` instead.
- **Formatting, charting, or restyling an existing workbook** — use `xlsx` instead.

# Regulatory Change Triage Brief

Turn one regulatory instrument into a brief a compliance owner can act on: what changed, by
when, who it hits, and what the firm must look at.

**You propose. A qualified human decides.** Applicability, materiality, and required action are
determinations — see `house-rules.md` § 2.

---

## Read first

Read these in full before step 1. They are binding; this body only summarises them.

- `references/workflow.md` — the full text of every step below, with the guardrails, source
  resolution, and footer detail.
- `references/house-rules.md` — destination gate, determination gate, authority tiers, markers,
  footers, and § 12 data minimisation (every artifact, search, and chat reply, declines included).
- `references/reg-source-access.md` — routing, the codification gap, precision filtering, the
  date ladder.
- `references/document-extraction.md` — if the instrument was uploaded.
- `references/triage-outline.md` — default brief and tracker structure: the output format.
- `references/self-check.md` — the final self-check (step 10).

---

## Workflow

### 1. Identify the instrument precisely

Detail: `workflow.md` § 1. Agency · title · document number · type · authority tier, before
anything else.

- A proposed rule is not law. Its `PROPOSED - not in force (G1)` line goes right after the whole
  header block (title, Destination, Prepared, Status), never between them.
- **Declines are plain:** `<category> withheld under data minimisation.`, with no statement of
  what SAR confidentiality or any law requires.
- **Never say what does not exist** ("has not been published", "is not yet final"). Say what the
  instrument you hold is; only after a Federal Register search this session write
  `NOT FOUND - Federal Register API has no record of a final rule for <RIN> as of <date> (Gn)`.
- Ambiguous instrument: list the candidates and ask; never pick one silently.

### 2. Retrieve it

Detail: `workflow.md` § 2. Connector → direct route → browser → ask for an upload →
`NOT RETRIEVED`, per `reg-source-access.md` § 1. Never answer from memory. Filter searches by
agency, type, and docket.

### 3. Build the date ladder

Detail: `workflow.md` § 3. Published · Effective · Compliance date · Mandatory compliance date,
plus the comment deadline: every row always shown, never collapsed. A row with no stated date
leads with `NOT FOUND - instrument states no <which> date (Gn)`, then any quoted relative or
proposed wording. Never "n/a"; never infer a compliance date from the effective date.

### 4. Extract what changed

Detail: `workflow.md` § 4. CFR part and section, prior text, new text, both quoted verbatim. Run
the codification check before calling codified text current; no prior text →
`GAP — prior text not established`. While the definitions section is not retrieved, every entity
term in `Prior text` and `New text` quotes, preamble quotes included, reads `[covered entity]`.

### 5. Derive obligations

Detail: `workflow.md` § 5. One obligation per row: what must be done · who it binds · trigger or
threshold · the date it bites · citation · tier.

- A proposed rule's obligations carry `PROPOSED - not in force`, one G-bullet naming every row.
- Guidance is a supervisory expectation, never "required by". Thresholds are quoted exactly.
- Quotes and paraphrases use `[covered entity]` while the definitions section is not retrieved.
- `Bites on` is the DATES compliance date covering the row, with its DATES citation, or
  `NOT FOUND - instrument states no compliance date for <row> (Gn)`. Never the effective date.
- Capture every exemption and exclusion.

### 6. Propose applicability — never decide it

Detail: `workflow.md` § 6. For each obligation, propose the business lines, products, entities,
or jurisdictions affected, with the reasoning and the text it rests on, marked
`NOT DETERMINED — compliance owner decides`. Retrieve the coverage-defining provision first; if
it was not retrieved, the reasoning reads exactly `none - defining provision not retrieved`. No
hedge words. Name any missing fact (for example total assets) with its marker. State each scope
ambiguity as an open question with its decider. Never "will require you to".

### 7. Locate candidate affected policies

Detail: `workflow.md` § 7. Search M365 for policies touching each obligation: name · version ·
approval status · approval date · location · why candidate (the topical link only). Nothing found
→ `NOT FOUND - <repository> has no record of a policy for <obligation> (Gn)`. Each rejected document
gets its own `GAP - scope mismatch, not a candidate` bullet. A candidate is never coverage; hand
clause-level work to `policy-gap-analysis`.

### 8. Build the action list

Detail: `workflow.md` § 8. Proposed actions only: the obligation served · a suggested owner with
its basis · the driving date · what closes it. No basis → only
`NOT FOUND - owner not identified (Gn)`.

### 9. Emit the tracker and draft handoff

Detail: `workflow.md` § 9. Build the workbook with `xlsx` per `triage-outline.md`. A GRC
connector is read for pre-fill only; the deliverable is a draft export, and the register update
is the human's action. No connector → `NEEDS FEED — GRC change register`.

### 10. Final self-check, then count

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

- Never state a requirement from memory or cite anything reached only through a snippet.
- Never present a proposed rule as an obligation or guidance as a legal requirement.
- Never collapse the four dates; never report codified text as current without the check.
- Never decide applicability, materiality, or compliance; no hedge words on a determination.
- Never fabricate a document number, docket, section, date, owner, or figure.
- Never claim a save succeeded when it failed. Nothing is registered, filed, sent, or committed
  in a source system.

## Output footer

Per `house-rules.md` § 9 and `workflow.md`, Output footer: destination · instrument and
identifiers · route · tier · coverage · codification check and result · policy repository searched
and found · connectors · open items by marker type · determinations outstanding · draft export,
no source-system update · files and save result · template used.

### Example

```
Input: FinCEN proposed rule RIN 1506-ABCD; search AML policy owners.
Output row: Obligation 1 - PROPOSED - not in force (G1); comment deadline 2026-11-12.
Candidate policy: AML Program Standard v4; Determination: NOT DETERMINED - compliance owner decides (D1).
Owner: NOT FOUND - owner not identified (G2).
No match: NOT FOUND - Compliance/Policies has no record of a policy for O2 (G3).
D-bullet: D1 - NOT DETERMINED - does O1 reach the firm - compliance owner decides
Handoff: Draft register export prepared; no source-system update performed.
```

## Reference files

- `references/workflow.md` — full step text, guardrails, source resolution, footer detail.
- `references/self-check.md` — the final self-check.
- `references/house-rules.md` — gates, tiers, markers, footers, data minimisation, the lint step.
- `references/reg-source-access.md` — routing, codification gap, precision filtering, date ladder.
- `references/document-extraction.md` — reading an uploaded instrument or policy.
- `references/triage-outline.md` — default brief structure and tracker columns.
