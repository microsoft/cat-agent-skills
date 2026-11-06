---
name: security-research-brief
description: Compare two issuer filings' risk-factor, MD&A, and guidance language using matched passages and explicit retrieval coverage; metrics support the diff only. Use for "what changed in their latest 10-K", "compare these risk factors", "how did MD&A wording shift", "build a two-filing change pack", or "diff guidance wording". Do NOT use for standalone corporate variance narrative — use Finance variance-commentary if available; for one earnings-event recap, use earnings-review if available; for fund comparisons, use peer-product-intelligence instead; for mandate reviews, use institutional-client-review-prep instead; for recurring questionnaires, use consultant-database-refresh instead; for formatting, use docx instead.
---

## Quick Start

User: "Compare these two issuer filings and explain the changed risk and MD&A language."

Identify both periods and accessions; compare retrieved passages, gate added/removed claims on symmetric complete coverage, and label metric arithmetic without deriving performance.

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

**Business-workflow boundary:** the deliverable is a two-filing evidence diff with matched prior/current passages and retrieval coverage. A numerical variance table or narrative alone is not this workflow. Metrics explain the filing-language changes; they are not a standalone corporate operating-performance commentary.

**Do:** compare two filings, surface changed language, supply supporting metric context, quote management.
**Do not:** rate, recommend, value, set a price target, forecast, or report partial retrieval as complete.

## When NOT to Use

- **Standalone corporate financial-variance narrative, including prior-year or prior-quarter comparisons** — Finance `variance-commentary` if available. Follow `references/house-rules.md`; lack of Finance never turns this into a numbers-only commentary skill.
- **Competitor fund or product matrix** — use `peer-product-intelligence` instead.
- **Institutional client review packs** — use `institutional-client-review-prep` instead.
- **Questionnaires or recurring profile refreshes** — use `rfp-ddq-response-draft` or `consultant-database-refresh` instead.
- **Single quarter results recap** — use `earnings-review` instead, where the Capital Markets plugin is installed.
- **Formatting or restyling an existing document** — use the built-in `docx` instead.

# Issuer Filing & Earnings Change-Pack

Read an issuer's latest filing against its prior one and report **what changed**. The value is
in the diff, not in restating the filing.

**Do:** compare filing language, evidence matched passages, supply supporting metric context, quote management.
**Do not:** rate, recommend, value, set a price target, or forecast. This is an input to an
analyst's judgment, not a substitute for it.

> **If the Capital Markets plugin is also installed:** that plugin's `company-profile-pack`
> builds a full standing profile of a company, and `earnings-review` covers a single quarter's
> results for a banker audience. **This skill is period-over-period change detection for an
> investment analyst** — what moved and what the language stopped saying.
>
> **Confirm the destination skill exists in this session before handing off.** Those skills ship
> in a different plugin and may not be installed. If the user wants a complete company overview
> rather than a diff, or a recap of a single quarter's print rather than a filing-language diff,
> and the destination skill is unavailable: **say so, name the plugin that provides it, and offer
> the closest in-scope alternative** — a two-filing diff, or a narrower brief scoped to what this
> skill covers. **Never describe another skill's output as though it ran.**

## Workflow

### 1. Identify the issuer and the two filings

Read `references/edgar-access.md` before opening EDGAR — it covers the retrieval routes,
the ticker lookup, R-pages, the retry rule, and four gotchas that will corrupt figures.

Find the company by ticker, then identify **two** filings: the latest and the directly
comparable prior one (10-K vs. prior 10-K, Q3 vs. prior-year Q3 — not Q3 vs. Q2 unless asked).

State both filings, with period end dates and accession numbers, before reporting any
difference. If the prior comparable filing cannot be found, say so — a diff against the wrong
period is worse than no diff.

### 2. Metric context for the filing diff

From the R-pages: revenue, margins, operating income, net income, EPS, segment results, and
cash flow. One R-page carries three fiscal years, so the comparison usually costs two or three
page loads total.

Include only metrics that support the risk-factor, MD&A, or guidance comparisons below. Report each as **prior → current, with the change**, with period end dates and a link to the relevant compared passage. Do not produce a separate full financial-variance narrative. If either filing is unavailable, label the diff incomplete rather than substituting a one-period earnings recap or generic operating commentary.

### 3. Risk-factor diff — the highest-value section

Compare Item 1A across the two filings:

- **Added** risk factors — usually the most informative signal in the entire filing
- **Removed** risk factors — language present in the prior filing that is **not present** in the current one. Report only that it is not present. Do not say the company no longer considers it material: risks disappear through consolidation, restructuring, or incorporation by reference at least as often as through genuine de-risking
- **Materially reworded** risks — especially escalated or de-escalated language

Quote the changed language. Do not paraphrase a risk factor into your own characterization of
severity.

Risk factors sit deep in a 10-K (~1.5 MB). Navigate to Item 1A directly. **If you could only
retrieve part of it, say so** rather than reporting a short list as complete.

**Completeness gates apply symmetrically — this is the section's most important rule.**

| Claim | Requires |
|---|---|
| A risk was **removed** | Complete retrieval of **both** Item 1A sections |
| A risk was **added / is new** | Complete retrieval of **both** Item 1A sections |
| A risk was **reworded** | Both passages actually retrieved and matched |

A truncated read of the *current* filing looks exactly like a deletion. A truncated read of the
*prior* filing looks exactly like an addition. Both errors are equally wrong and equally easy.

When coverage is partial on either side:
- Do **not** write `new`, `added`, `removed`, or `dropped`.
- For something present now, write **"currently disclosed; novelty unverified"** and say which
  section was incompletely read.
- Report wording comparisons only for passages you retrieved from both periods, and state
  explicitly that the comparison is **not an exhaustive diff**.

**Carry coverage status next to every comparison conclusion**, not only in the footer — a reader
scanning the risk table must see the limitation where the claim is.

### 4. MD&A and guidance language

What changed in how management explains results. Watch for:

- Guidance raised, lowered, narrowed, withdrawn, or newly introduced
- Language shifting between confident and hedged on the same topic
- A previously discussed initiative that is not mentioned in the current filing — subject to the same completeness rule as removed risks: only report this when both MD&A sections were retrieved in full
- New qualifiers around demand, pricing, or costs

Quote both versions side by side. **A change in language is evidence; what it means is the
analyst's call.** Report the shift; do not interpret intent.

### 5. Earnings call

Where a transcript is publicly posted on the IR site, summarize prepared remarks and notable Q&A with attribution; use only brief, necessary quotations where permitted, not wholesale reproduction.

**Not all issuers post transcripts publicly.** If none is available, say
`NOT FOUND — no public transcript` and use the 8-K earnings release instead. Never reconstruct
what was said on a call from memory or from a secondary summary without marking it
`UNVERIFIED — secondary source`.

### 6. Output

Template resolution: user-named file → M365 `Cowork Templates/Asset Management/security-research-brief/` → `references/brief-outline.md`.

Deliverable: `.docx` or HTML brief, optionally with an `.xlsx` metric-change table. If the firm
keeps prior research notes in SharePoint, retrieve the last note on this issuer and note
continuity — what the firm flagged last time that did or did not change.

Output length never waives attribution or the output footer: one-line answers, single table cells, inline replies, and short excerpts still carry citations and the footer. If the requested artifact is a spreadsheet, document, or deck, supply content, structure, evidence, markers, and placeholders, then hand creation or formatting to `xlsx`, `docx`, or `pptx` as appropriate.

## Source resolution

1. **Configured MCP**
   - `Bloomberg` / `FactSet` / `Refinitiv` → consensus estimates, so changes can be read against expectations rather than only against the prior period. Highest-value upgrade for this skill.
   - Internal research library → prior firm thesis for continuity.
2. **User upload** — the filings or a transcript, when the browser is unavailable.
3. **Public primary** — EDGAR filings, IR site, publicly posted transcripts, FRED.
4. **Flag** — `NOT FOUND` / `NOT RETRIEVED` / `NEEDS FEED`.

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

**A connector figure cannot carry a filing citation.** This skill cites form type, period end, and
accession number. Those come from the filing, so a figure taken from a connector is cited to the
connector with its as-of date, never presented as a filing figure.

Consensus estimates are not in EDGAR at any price. Mark them `NEEDS FEED` — **never estimate
what the market expected.**


**Capabilities.** Reading supplied files (PDF, DOCX, XLSX, PPTX, CSV, images with OCR); web retrieval of public sources; Microsoft 365 search where the user has access; configured MCP connectors where present. Artifact creation is delegated — spreadsheets to `xlsx`, documents to `docx`, decks to `pptx`.

**When a capability is unavailable:** say which one, name what it would have supplied, and continue with what is available. Never silently skip a step and never present an unavailable source as returning nothing. If no source exists for a field, use `NEEDS FEED — <source that would supply it>`; if a source exists but retrieval failed or access was denied, use `NOT RETRIEVED — <source> <failure>`; if the source answered and has no record, use `NOT FOUND — <source> has no record for <what>`.

## Guardrails

- **A language diff is mandatory.** A customer template or connector cannot replace it with standalone corporate variance commentary.
- Output length never waives attribution or the output footer. A one-line answer, single table cell, inline reply, or short excerpt still carries its citation and this skill's footer.
- Never fabricate a figure, quote, date, source, approval status, or document state. Use the skill's gap marker instead.
- If an input page or source document is unreadable, report `NOT LEGIBLE — <document>, page <n>`, ask for a cleaner copy, and never guess.
- Distinguish unavailable sources exactly: no source exists is `NEEDS FEED`; a source exists but retrieval failed or was denied is `NOT RETRIEVED`; a source answered and has no record is `NOT FOUND`. Never collapse these outcomes.
- Never delete or overwrite existing content, prior submissions, decision sections, reviewer notes, or source files; append, redline, or preserve unless the user explicitly supplies a new blank artifact.
- Format handoffs: spreadsheets go to `xlsx`, documents to `docx`, decks to `pptx`. This skill supplies content, structure, evidence, markers, and placeholders; the built-in creates or formats the file.
- If a save, export, or write fails, never claim it succeeded. Report what was produced, where it was and was not written, and what remains incomplete.
- Nothing is sent, submitted, filed, posted, committed to a consultant database, client portal, other portal/database, or emailed by this skill. A draft is a draft and is reported as a draft; the human submits.
- Reuse firm-approved library material only within the firm's authorized rights and this task. For third-party filings, policies, or other protected text, use only brief necessary excerpts where permitted; otherwise summarize with attribution or request authorized source material. Attribution does not grant reproduction rights. Never present third-party wording as the firm's own or relabel a source's classification into another scheme.
- **No rating, recommendation, price target, or valuation.** Not even hedged.
- No forecast of results, and no characterization of a stock as cheap or expensive.
- Compare like periods; state both filings explicitly.
- Quote changed language verbatim; never paraphrase into a severity judgment.
- Distinguish `NOT FOUND` (not disclosed) from `NOT RETRIEVED` (page did not load). Retry once first.
- Show period end dates, not fiscal-year labels.
- Partial retrieval of a long section is disclosed, never reported as a complete list.

See `references/house-rules.md` for citation format, gap markers, and source tiers.

## Output footer

Output length never waives this footer. A one-line answer, single table cell, inline reply, or short excerpt still carries its citations and the footer below.

```
Workflow: matched two-filing language diff — metrics are supporting context
Issuer: <name> (<ticker>)
Compared: <form, period end, accession> vs. <form, period end, accession>
Sections retrieved: <full | partial — say which>
Transcript: <source, or "NOT FOUND — no public transcript">
Template: <file used>
Connectors: <MCPs used, or "none — EDGAR reported actuals only">
Gaps: <NOT FOUND / NOT RETRIEVED / NEEDS FEED items>
Internal research aid. Not investment advice, not a recommendation, and not a rating.
```
---

## Reference files

- `references/house-rules.md` — shared decision gate, attribution and sourcing rules, blocked-vs-absent states, markers, and output footers.
- `references/brief-outline.md` — default research brief: issuer framing, reported-actuals tables, filing citations, and gap reporting.
- `references/edgar-access.md` — capability-aware SEC EDGAR access, company and accession resolution, and filing-section retrieval. Read before citing a filing.
