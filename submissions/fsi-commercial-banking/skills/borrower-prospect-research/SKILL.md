---
name: borrower-prospect-research
description: |
  Build a sourced public-record background brief on a commercial borrower or prospect, with entity identity, jurisdiction, retrieval date, and search limits. Use when the user says "what do we know about this company", "run background on this borrower", "pull public records on Acme", "who owns this business", or "any liens or litigation on this prospect". Do NOT use for financial spreads — use financial-statement-spread instead. Do NOT use for relationship-history call prep — use rm-call-prep-followup instead. Do NOT use for standalone covenant tests — use covenant-compliance-check instead. Do NOT use for document formatting — use docx instead.
license: MIT
metadata:
  plugin: fsi-commercial-banking
  persona: relationship manager, coverage banker, credit analyst
---

# Borrower & Prospect Research Brief

Assemble what the public record says about a company, with the limits of each search stated.

## Scope

**Do:** resolve the legal entity, gather public-record facts, cite each one with its jurisdiction and retrieval date, and state what each search does and does not establish.

**Do not:** score, rate, pre-qualify, opine on credit appetite, or characterise the company as a good or bad credit. See the credit-decision gate in `references/house-rules.md`.

This brief is **research input**. It is not a credit bureau report, not a formal lien search, and not a sanctions, PEP, or adverse-media screen — those obligations are met through the bank's own processes.

## When NOT to Use

- **Spreading financial statements** — use `financial-statement-spread` instead.
- **Meeting agenda or call prep built from relationship history** — use `rm-call-prep-followup` instead.
- **Formatting or restyling an existing document** — use `docx` instead.

## Quick Start

For "run background on this borrower", resolve the legal entity before collecting records; cite exact searches and limits; if the name is ambiguous, ask instead of choosing a match.

## Tool routing

1. Check actual connector availability; use `GetPluginConfig` when an expected plugin capability is missing. Do not assume a named vendor or optional Finance skill is connected.
2. For Microsoft 365 record sets use `ExecuteSql`; for topic/content discovery use `SearchM365`. Read located files with `ReadFileContent` (`full` for supported document text; `download` for exact bytes or spreadsheets). Scope reads to the borrower, purpose, and permissions.
3. Use available configured connector tools for their documented fields. If none supply an item, follow the existing source order and retain the correct gap marker; never claim a tool ran when it did not.
4. Delegate file construction to `xlsx`, `docx`, or `pptx` as specified below. Inline output is an inline draft, not a saved file. Report a save only from the action tool's successful result.

## Output format

One-to-two-page draft brief: entity identity; sourced business/background facts; public-record search table (source, jurisdiction, exact name, date, result, limit); relationship context; explicit gaps; the existing output footer. Preserve the bundled or chosen template's section order.

## Workflow

### 1. Resolve the entity — before searching anything

Read the entity-identity section of `references/public-records.md`. Findings attached to the wrong entity are worse than no findings.

Establish and record: exact legal name with suffix, jurisdiction of formation, entity or file number, formation date, current status, and any trade names, former names, or d/b/a registrations.

**Keep registry/filing jurisdiction separate from formation/incorporation jurisdiction.** A state registry entry, active status, registration number, office address, or foreign registration establishes only what that record expressly says. Unless a source explicitly states the place of formation or incorporation, label the known field `registry/filing jurisdiction` and leave `formation/incorporation jurisdiction` unestablished with the appropriate gap marker. Never relabel a registry state as a formation state. In a candidate-disambiguation table, use `registry/filing jurisdiction` when that is all the supplied search establishes; ask which candidate is intended without adding a legal-identity fact.

Where the user gave only a trading name or an ambiguous name, resolve it first. If several entities plausibly match, list the candidates with their jurisdiction and identifier and **ask** — never pick one.

Where a group is in scope, say which entity each finding attaches to. Do not merge parent and subsidiary records.

### 2. Gather the public record

Work through the sources in `references/public-records.md`, recording for each search: the source, the jurisdiction, the exact name searched, and the date run.

- **Registry** → legal status, formation, registered agent, officers where filed.
- **UCC index** → secured filings of record under the name searched.
- **County recorder** → recorded mortgages, deeds, and some liens, per county searched.
- **Court index** → filed cases where the index is public.
- **EDGAR** → filings where the company, its parent, or a named competitor is a registrant. Most commercial borrowers are private; `NOT FOUND` here is a normal result.
- **Company site and press releases** → what the company states about itself.
- **News and trade press** → reported events, attributed to publisher and date.

Retry a failed source once, then record `NOT RETRIEVED` naming the source. Never let an unreachable registry become a silent omission, and never substitute an aggregator for the registry without marking it.

### 3. Add relationship context from M365

Search Outlook, Teams, and SharePoint for prior contact with this name: earlier briefs, prior credit files, past correspondence. Report what exists and when, so the user knows whether this is a cold prospect or a returning name.

Stay inside the signed-in user's permissions. Where nothing is found, say the search was run and returned nothing — that is a useful result.

### 4. Resolve the template

1. User named a template file → use it.
2. Else search M365 for `Cowork Templates/Commercial Banking/borrower-prospect-research/` → most recent file there.
3. Else use `references/brief-outline.md`.

State which template you used.

### 5. Produce the brief

Default document output is delegated to the built-in `docx`: the skill supplies sourced content, section structure, evidence, and placeholders; `docx` builds the file. Missing values remain blank or marked, never `0`.

Default `.docx`, one to two pages, following `references/brief-outline.md` unless a house template overrides it.

Every fact carries its source and date. Every clean search states the name, jurisdiction, index, and date it was run under.

## Source resolution

Ordering follows `references/house-rules.md`.

1. **Configured connector.** Business credit and firmographics (`D&B`, `Experian`, `Equifax` commercial), company data (`S&P Capital IQ`, `PitchBook`), CRM (`Salesforce`, `DealCloud`) → scores, corporate family tree, aggregated liens, prior calls and ownership. Record the connector and its as-of date.
2. **Public primary** — the issuing registry, regulator, or EDGAR, reached by whatever route this session supports.
3. **Supplied documents and M365** — a certificate of good standing, a prior lien search report, an earlier brief.
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

With no connector configured, the brief has no business credit score, no aggregated multi-state lien view, and no corporate family tree. Mark those `NEEDS FEED — business credit source (e.g. D&B, Experian commercial)` rather than assembling a partial substitute and presenting it as equivalent.

**Capabilities.** Reading supplied files (PDF, DOCX, XLSX, PPTX, CSV, images with OCR); web retrieval of public sources; Microsoft 365 search where the user has access; configured MCP connectors where present. Artifact creation is delegated — spreadsheets to `xlsx`, documents to `docx`, decks to `pptx`.

**When a capability is unavailable:** say which one, name what it would have supplied, and continue with what is available. Never silently skip a step and never present an unavailable source as returning nothing.

**Source markers.** Distinguish `NEEDS FEED` (no source exists in this session), `NOT RETRIEVED` (source exists, but retrieval failed or was denied), and `NOT FOUND` (source answered, with no record). Never collapse them.

**Artifact handoff.** The skill supplies the content, structure, formulas as specified, evidence, and placeholders; the built-in creates the file. Spreads and covenant workbooks go to `xlsx`; memos, credit write-ups, briefs, packets, and call memos go to `docx`.

## Guardrails
- **Nothing auto-sends.** No email, submission, posting to a system of record, file submission, or commitment to a borrower is sent or made automatically. A draft is a draft and is reported as a draft.
- **Never delete decision sections.** Existing approvals, conditions, exceptions, risk ratings, and prior decision rationale are preserved. Updates append and mark changes; they never overwrite or remove.
- **Unreadable statements stop calculations.** If a financial statement figure cannot be read with confidence, output `NOT LEGIBLE — <document>, page <n>, <line item>`, ask for a cleaner copy, never guess a digit, never infer a number from a subtotal, and never carry a partially read figure into a calculation. If extraction quality is poor across a statement, say so and stop rather than producing a spread or covenant test built on guesses.
- **Unavailable sources stay distinct.** Use `NEEDS FEED` when no source exists in this session, `NOT RETRIEVED` when a source exists but retrieval failed or was denied, and `NOT FOUND` when the source answered with no record. Never collapse them.
- **Failed saves are failures.** Never claim a save succeeded unless it was verified. Report what was produced, where it was and was not written, and what remains incomplete.
- **Missing values are never zero.** In spreadsheets, covenant worksheets, memos, and packet tables, write a blank or the applicable marker; never write `0` for missing, unreadable, unretrieved, or unavailable values.
- **Resolve identity first.** Every finding names the entity and identifier it was found under. A plausible but unconfirmed match is `GAP — possible match, identity not confirmed`, never merged in as fact. Registry/filing jurisdiction is not formation/incorporation jurisdiction unless the source explicitly evidences the latter; active status or an entity number is not that evidence.
- **A clean search is not proof of absence.** Report the index, jurisdiction, name searched, and date. Never write "no liens," "unencumbered," or "no litigation."
- **Never characterise the company's credit.** No score, no pre-qualification, no appetite signal, no "strong" or "risky."
- **Attribute, never assert.** News and allegations are reported with publisher and date, never restated as findings.
- **No protected characteristics.** Never collect, infer, or repeat race, colour, religion, national origin, sex, marital status, age, or receipt of public assistance — even where a public source states them.
- **Personal detail stays business-relevant** — role, tenure, business affiliations. Not personal financial or legal history.

## Output footer

```
Entity: <exact legal name, jurisdiction, identifier, status, as of date>
Searches run: <each: source, jurisdiction, exact name searched, date, result>
Sources: <count> — <each with publisher/registry and date>
Retrieval coverage: <complete | partial — name what was partial | sources not reached>
Template: <bundled default | house template name>
Artifact handoff: <xlsx | docx | pptx | none — inline only>
Connectors used: <names, or "none">
Other sources used: <public registry | supplied documents | M365 | secondary, marked>
Output: inline draft | file created <identifier> | creation failed
Persistence: not attempted | saved <verified location> | failed
Save detail: <what was produced; where written; where not written; incomplete items>
Gaps: <NOT FOUND / NOT RETRIEVED / NEEDS FEED / GAP items, or "none">
Generated: <date> — public-record research only. Not a credit bureau report, formal lien
search, or sanctions/PEP/adverse-media screen. No credit assessment or recommendation.
```

Every field states what actually happened. Do not claim a registry was searched when it could not be reached. Do not describe coverage as complete when a jurisdiction was skipped.

## Reference files

- `references/public-records.md` — routes, entity identity, what each source establishes, search limits, freshness, scope boundaries. Read before searching.
- `references/house-rules.md` — citation format, source tiers, credit-decision gate, markers.
- `references/brief-outline.md` — default section order and field list.
