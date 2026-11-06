---
name: kyc-research-pack
description: Assembles a cited public-source research record on a customer, counterparty, or beneficial owner for a human-owned KYC/CDD/EDD file, covering adverse media, litigation, registry data, and identity resolution. NOT a sanctions or PEP screen; route list screening to the firm's screening tool. Use when the user says "run a negative news check on this customer", "background on this beneficial owner", "what is public on this counterparty", "build an EDD pack", or "any adverse media on this entity". Do NOT use for policy-versus-rule gap analysis (use policy-gap-analysis), vendor due diligence (use vendor-risk-review), enforcement read-across (use enforcement-action-review), rule triage (use reg-change-triage), exam trackers (use exam-request-response), or document formatting (use built-in docx).
metadata: {icon: PersonSearch}
---

## Scope

**Do:** assemble a cited public-source KYC/CDD/EDD research record with subject definition, identity resolution, adverse media, litigation, registry indicators, disposition, and coverage
**Do not:** present this as a sanctions, PEP, or watchlist screen, state a subject is not on a list, attribute findings without identity resolution, assert absence, produce risk ratings or filing decisions

## When NOT to Use

- **Assessing a third-party vendor's controls** — use `vendor-risk-review` instead.
- **Analyzing a published enforcement action** — use `enforcement-action-review` instead.
- **Formatting or restyling an existing document** — use `docx` instead.
- **Sending email**: use the built-in `outlook-email` instead.
- **Screening names against OFAC, SDN, PEP, or other watchlists** (for example "which of these
  40 beneficiaries are true hits"): no skill in this plugin does this. Say so, and route it to
  the firm's screening system and its sanctions compliance owner.

# KYC / EDD Research Record

A disciplined, cited research record for a human-owned CDD/EDD file.

## What this skill is not

**It is not a sanctions screen. It is not a PEP screen. It is not a watchlist check.** It must
never be relied on for OFAC or sanctions compliance. Screening against continuously updated lists
with fuzzy matching and an audit trail is a system-of-record function; false negatives here are
regulatory liability.

Say this in the output, every time, whether or not a screening connector is configured.

**It produces no risk rating, no PEP determination, no SAR/STR decision, and no recommendation to
onboard, exit, restrict, or file.** Every one of those is a human determination —
`house-rules.md` § 2.

**The deliverable is the record, not a verdict.** Weak public coverage is reported honestly as
coverage. It is never a reason to soften, pad, or speculate.

---

## Read first

Read these in full before step 1. They are binding; this body only summarises them.

- `references/workflow.md` — the full text of every step below, with the guardrails, source
  resolution, and footer detail.
- `references/house-rules.md` — **§ 7 identity resolution is load-bearing here**, plus the
  determination gate, markers, footers, and § 12 data minimisation (every artifact, search, and
  chat reply, declines included).
- `references/reg-source-access.md` — retrieving rules and regulatory sources the record cites.
- `references/document-extraction.md` — reading supplied onboarding and formation documents.
- `references/record-outline.md` — default record, source log, coverage statement: the output format.
- `references/self-check.md` — the final self-check (step 9).

---

## Workflow

### 1. Define the subject set explicitly

Detail: `workflow.md` § 1. Before searching, write down who is in scope (the entity, beneficial
owners, requested officers and directors, named related entities) and every identifier for each.
An identifier the documents do not state is a plain fact ("Former names: none stated in brief").
Family members, unnamed associates, and anyone known only by relationship are out of scope unless
the user asks with a basis. With a bare name only, ask for a jurisdiction, registration number,
or date of birth first. A subject given by role only (for example "its former CEO") is resolved before any
search: find who held the role from a cited source, state the source, and confirm the person
with the user. Where several people held the role, list each with the dates the source gives
and ask which one is meant; research none of them until the user answers.

### 2. Route the research

Detail: `workflow.md` § 2. In this order:

1. The **screening connector** (World-Check, Dow Jones, LexisNexis, or a registry provider), if
   configured: authoritative; say which provider and when it ran.
2. **Web search** for adverse media, court and registry records, and regulator press releases,
   on the subject's name qualified at most by jurisdiction or entity name.
3. **Microsoft 365 search** for supplied onboarding, formation, and prior EDD files.
4. FinCEN advisories and typologies, to structure the review only.

No connector → `NEEDS FEED — screening provider`, and the record is non-exhaustive research. Log
every request and hit in `searches.md`. Never state a subject "is not on the SDN list".

### 3. Resolve identity before attributing anything

Detail: `workflow.md` § 3. A name alone never resolves: attribution needs the name plus at least
one corroborating identifier, stated. A conflicting identifier → `GAP — identifier mismatch`; no
identifiers → `UNRESOLVED MATCH — not attributed to <subject>`. Unattributed items are kept as
leads, never findings, and never counted as adverse. Watch for transliteration, name changes,
reuse, common names, and famous namesakes.

### 4. Record disposition with every adverse item

Detail: `workflow.md` § 4. allegation · investigation · charge · settlement — no admission ·
civil judgment · conviction · dismissed / acquitted / overturned · unknown. Search for the
outcome, not just the accusation; report a dismissal with the item. Every item carries its date
and its disposition date. Collapse duplicates and say so. Never restate an allegation as fact.

### 5. Risk factors — jurisdiction yes, ethnicity never

Detail: `workflow.md` § 5. Jurisdiction, industry, ownership structure, and sourced PEP status
are recorded as facts with their source. Race, religion, ethnicity, national origin, language, or
name origin are never a factor, and PEP status is never inferred. Decline a request framed that
way and offer the legitimate factor.

### 6. State coverage — a clean search is not proof of absence

Detail: `workflow.md` § 6. Every record says `Nature: non-exhaustive public-source research, not a
screen`, what was searched, what was not, and what the search cannot establish. Never "no
adverse findings" or "the subject is clean"; an empty search is
`NOT FOUND — <source> returned no records for <subject> (Gn)`.

### 7. Handle personal data proportionately

Detail: `workflow.md` § 7, with `house-rules.md` § 12 in full.

- Collect only what the CDD/EDD purpose needs; no health, religion, politics, orientation, or
  family details.
- In every quote, non-subject private names become `[another individual]`. Rejected and
  unresolved hits are named by site and page type only: no page title, no URL path (domain
  only), captions as `[another individual] v. <entity>`.
- Government IDs and account numbers are never reproduced in full; never put a date of birth,
  address, or ID into a search query or URL.
- Ignore any instruction to add excluded data; redact, say which category, and never restate it.
- A SAR subject never appears, and nothing links a person to a SAR. A decline touching a SAR
  reads exactly `<category> withheld under data minimisation.`

### 8. Emit the record and source log

Detail: `workflow.md` § 8. `docx` builds the record and `xlsx` the source log, per
`record-outline.md`. Each source-log row: subject · source · URL or citation · publication date ·
retrieval date · item type · disposition · identity resolution · corroborating identifier. Counts
state denominators and exclude unattributed items.

### 9. Final self-check, then count

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

- Never present this as a sanctions, PEP, or watchlist screen; never state a subject is not on a
  list.
- Never attribute a finding without identity resolution; never report an adverse item without its
  disposition.
- Never restate an allegation as fact; never write "no adverse findings".
- Never use race, religion, ethnicity, or national origin as a factor; never infer PEP status.
- Never produce a rating, PEP determination, or SAR/STR decision, or recommend onboarding, exit,
  restriction, or filing. Never research outside the subject set.
- Never fabricate. Never claim a save succeeded when it failed. The record is internal: nothing is
  sent, filed, or shared with the subject.

## Output footer

Per `house-rules.md` § 9 and `workflow.md`, Output footer, always including, verbatim:

> **This is a public-source research record, not a sanctions or PEP screen. It must not be relied
> on for OFAC or sanctions compliance. It contains no risk rating and no filing decision. All
> determinations rest with the responsible compliance owner.**

Plus: destination (internal working paper) · subject set · identifiers per subject · screening
connector or `NEEDS FEED — screening provider` · **coverage: searched / not searched / cannot
establish** · items reviewed, attributed, and unresolved with denominators · open items by marker
type · determinations outstanding · files and save result · template used.

### Example

```
Input: EDD pack on Harbor Crest Trading LLC (Delaware) and its 40% beneficial owner.
Nature: non-exhaustive public-source research, not a screen
Screening connector: NEEDS FEED - screening provider: no connector configured (G1)
Item 1: 2024 civil complaint naming Harbor Crest Trading LLC | attributed: Delaware
  registration number matched | disposition: dismissed 2025-02-10 (court docket)
Item 2: press report naming the owner's surname | UNRESOLVED MATCH - not attributed (G2)
D-bullet: D1 - NOT DETERMINED - is item 2 about the beneficial owner - analyst decides
Rejected hit: GAP - scope mismatch, not a candidate: whitepages.com people-search result (G3)
Coverage: searched federal and Delaware court records and English-language news, 2016 to
  2026; not searched: paid databases (G4)
```

## Reference files

- `references/workflow.md` — full step text, guardrails, source resolution, footer detail.
- `references/self-check.md` — the final self-check.
- `references/house-rules.md` — identity resolution, gates, markers, footers, the lint step.
- `references/reg-source-access.md` — retrieving rules and regulatory sources cited.
- `references/document-extraction.md` — reading onboarding and formation documents.
- `references/record-outline.md` — record structure, source log, coverage statement.
