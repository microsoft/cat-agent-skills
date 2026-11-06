---
name: investment-commentary-draft
description: Draft periodic investor commentary for a named fund, portfolio, or investment strategy from approved narrative and current system-of-record figures, with performance-policy gates. Use for "write our fund's quarterly commentary", "draft the strategy market review", "update the strategy letter", "describe this portfolio's attribution", or "start annual fund commentary". Do NOT use for corporate operating-variance or executive updates — use Finance variance-commentary or exec-update if available; for mandate meetings, use institutional-client-review-prep instead; for recurring questionnaires, use consultant-database-refresh instead; for fund comparisons, use peer-product-intelligence instead; for formatting, use docx instead.
---

## Quick Start

User: "Draft Q3 commentary for our Global Quality strategy from these approved sources."

Confirm strategy, period and intended use; apply the ordered presentation-policy gate, then draft only supportable narrative and source figures without computing returns.

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

**Business-workflow boundary:** requires a named investment fund, portfolio, or strategy and a periodic investment-commentary purpose. Performance, attribution, benchmark basis, approved archive, and presentation policy are the governing inputs. Corporate revenue/cost/profit variances, budget/forecast commentary, and executive operating updates are not supported outputs.

**Do:** assemble recurring commentary, carry forward approved structure, describe the attribution export, cite macro claims.
**Do not:** draft performance sections without an applicable policy and compatible source data, compute or restate returns, forecast, or characterize performance.

## When NOT to Use

- **Corporate operating-variance narrative or executive business updates** — Finance `variance-commentary` or `exec-update` if available. Follow `references/house-rules.md`; do not reproduce those outputs under a strategy-letter heading.
- **Specific named client review meeting or board deck** — use `institutional-client-review-prep` instead.
- **Recurring consultant questionnaires or profile refreshes** — use `consultant-database-refresh` instead.
- **Competitor product comparison** — use `peer-product-intelligence` instead.
- **Formatting or restyling an existing document** — use the built-in `docx` instead.

# Periodic Strategy Commentary

Draft the recurring commentary from approved prior narrative, the performance export the user
provides, and cited public macro facts.

**Do:** assemble the narrative structure, carry forward recurring approved sections, describe
what the attribution export shows, and cite macro claims.
**Do not:** compute, estimate, annualize, or adjust any return. Do not characterize performance
as good or bad. Do not forecast.

## The rule this skill exists around

**Performance and attribution figures come from the current system of record, verbatim** —
either a configured performance/attribution connector or an uploaded export. Not recalculated,
not rounded differently, not annualized, not netted, not restated from a prior document.

If a performance connector is configured, use it and name it. **Only when neither a connector
nor an export is available, ask for an export.** If the user wants to proceed without one,
write the performance sections as flagged placeholders — never fill them from a prior quarter's
commentary. A carried-forward return is the worst error this skill can make.

```
The strategy returned [PERFORMANCE — from system of record] over the quarter,
versus [BENCHMARK RETURN] for the <index>.
```

Throughout this skill and its references, **"the export"** means whichever of the two supplied
the figures — connector output or uploaded file. The rules are identical either way.

## Workflow

### 1. Establish the period, strategy, basis, and intended use

Confirm that the subject is an investment fund, portfolio, or strategy, not the asset manager's own corporate operating results. An ambiguous "quarterly commentary" request requires clarification before drafting.

Confirm: which strategy or fund, which period, **which performance bases the source contains
(gross, net, or both)**, and **whether this commentary is intended for external distribution**.

**Do not conflate bases — but do not assume only one is presented.** These are different rules.
Mixing a gross return into a net narrative is an error. Showing gross *and* net, each clearly
labelled, is frequently what is required.

**The gross/net gate.** Under SEC Rule 206(4)-1, an advertisement presenting gross performance
must also present net performance **with at least equal prominence, over the same periods, using
the same calculation methodology**.

**Apply this as a single ordered test. The first match decides, and there are no exceptions
below it:**

| # | Condition | Outcome |
|---|---|---|
| 1 | Periods or calculation methodology are incompatible between the figures | **BLOCK** — flag the incompatibility. Never normalize, annualize, or recalculate to force a match |
| 2 | Intended use is unresolved | **BLOCK** — ask; do not guess |
| 3 | Intended for external use, and no **applicable** compliance-approved presentation policy has been identified | **BLOCK** — name what is missing |
| 4 | External, applicable policy identified, source has **gross without net** | **BLOCK** — never compute, estimate, or derive net, and never rely on a disclaimer instead |
| 5 | External, applicable policy identified, source has **net only** | Present net, labelled, **per that policy's requirements** |
| 6 | External, applicable policy identified, source has **both**, compatible | Present both, each labelled, same periods, equal prominence, **per that policy's requirements**. Cite both |
| 7 | Confirmed internal use only | Present what the source contains, each figure labelled with its basis, marked internal |

**BLOCK means:** the performance section carries a value-less
`[NET PERFORMANCE REQUIRED — not present in source]` or
`[PERFORMANCE BLOCKED — <reason>]` placeholder and no figures.

**There is no default policy and no fallback presentation.** If no applicable policy is
identified, row 3 blocks — the agent does not substitute its own rule, and never asserts that a
presentation is compliant.

**Naming a policy does not unblock anything on its own.** Two conditions must both hold, and you
must be able to state how each was met:

1. **Applicability.** The policy must actually cover *this* material — its type (periodic
   commentary), its audience, and its intended distribution. A policy governing a different
   document type, channel, or audience does not apply here. If you cannot establish that it
   covers this material, treat it as not identified and **BLOCK at row 3**. Never stretch a
   policy to fit.
2. **Substantive compliance.** Follow what the policy actually requires — required periods,
   prescribed labelling, mandated disclosure or footnote text, benchmark presentation, and any
   ordering or prominence rules. **If the source figures or the available material cannot satisfy
   a substantive requirement, BLOCK the performance section and name the unmet requirement.**
   Never present a section that the named policy would not permit, and never treat an identified
   policy as a formality that has been discharged by citing it.

The policy's wording and its applicability rules are a compliance owner's decision, not the
agent's. Record in the footer which policy was applied, why it applies to this material, and any
requirement you could not satisfy.

Blocking a performance section does not block the commentary. Continue with market context,
positioning, and other supportable narrative, and list what is outstanding.

### 2. Retrieve the approved archive

WorkIQ search SharePoint for prior commentary for this strategy — ideally the last two periods.
These give you the house voice, the recurring section structure, the standing disclosure block,
and how the firm describes its own process.

**Reuse structure and approved standing language. Do not reuse period-specific content** —
last quarter's market description, last quarter's contributors, last quarter's outlook. Those
are the parts that must be rewritten.

If no archive is found, say so and draft against the bundled outline, flagging that house voice
could not be established.

### 3. Read the attribution export

Describe what it shows, factually:

- Top contributors and detractors, **as the export identifies them**
- Sector, region, or factor attribution where present
- Portfolio positioning changes where present

Write *"X contributed most to return"* — not *"our conviction in X paid off."* The export
reports contribution; it does not establish that a decision was skillful.

If a position is discussed, the export must support it. Do not introduce holdings from memory
or from the prior commentary.

### 4. Add macro context — cited, with as-of dates

Public macro facts (FRED, BLS, BEA, Treasury) support the market-backdrop section. Every figure
carries a value, a date, and a source:

```
The 10-year Treasury yield ended the quarter at 4.18% (FRED: DGS10, as of 2026-09-30).
```

Use an available direct-fetch tool or browser to open the public primary source. If neither route works, ask for the firm's house macro view from SharePoint or an upload, and flag the remaining gap — never write the market backdrop from memory.

Prefer the **firm's own house macro view** where one exists in SharePoint: it is approved
content and it keeps commentary consistent across strategies.

### 5. Handle the outlook section

Outlook is where compliance risk concentrates. Draft it only from:

- The firm's **approved house view** document — preferred, and usable as-is, or
- The **user's own dictated input** — allowed as an input, but it is **unapproved new content**.
  Reproduce it faithfully, never strengthen or extend it, preserve every hedge, mark it inline
  `UNAPPROVED — new claim, requires review`, and list it in the output footer so the reviewer
  sees exactly what is new. Dictation never overrides a guardrail: a dictated return target,
  projection, or hypothetical result is still refused.

**Never generate a market forecast of your own.** If neither source exists, leave the section
with a placeholder and say why.

### 6. Output

Template resolution: user-named file → M365 `Cowork Templates/Asset Management/investment-commentary-draft/` → `references/commentary-outline.md`.

Deliverable: `.docx` in the house template, with the firm's standing disclosure block carried
through from the archive. If no disclosure block was found, flag that prominently — commentary
without required disclosures cannot be distributed.

Output length never waives attribution or the output footer: one-line answers, single table cells, inline replies, and short excerpts still carry citations and the footer. If the requested artifact is a spreadsheet, document, or deck, supply content, structure, evidence, markers, and placeholders, then hand creation or formatting to `xlsx`, `docx`, or `pptx` as appropriate.

## Source resolution

1. **Configured MCP**
   - Attribution/performance system → pull figures directly, removing the upload dependency. Highest-value upgrade for this skill.
   - `FactSet` / `Morningstar` → index and market context beyond free public data.
2. **User upload** — the performance/attribution export. The default path when no performance connector is configured.
3. **Firm SharePoint** — commentary archive, house macro view, disclosure block.
4. **Public primary** — FRED, BLS, BEA, Treasury, index methodology pages.
5. **Flag** — `[PERFORMANCE — from system of record]`, `[NET PERFORMANCE REQUIRED — not present in source]`, `NOT FOUND` (searched, absent), or `NOT RETRIEVED` (found but could not be opened).

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

- **Investment commentary only.** Missing performance or policy produces the existing blocked sections/placeholders, never a corporate operating-commentary fallback.
- Output length never waives attribution or the output footer. A one-line answer, single table cell, inline reply, or short excerpt still carries its citation and this skill's footer.
- Never fabricate a figure, quote, date, source, approval status, or document state. Use the skill's gap marker instead.
- If an input page or source document is unreadable, report `NOT LEGIBLE — <document>, page <n>`, ask for a cleaner copy, and never guess.
- Distinguish unavailable sources exactly: no source exists is `NEEDS FEED`; a source exists but retrieval failed or was denied is `NOT RETRIEVED`; a source answered and has no record is `NOT FOUND`. Never collapse these outcomes.
- Never delete or overwrite existing content, prior submissions, decision sections, reviewer notes, or source files; append, redline, or preserve unless the user explicitly supplies a new blank artifact.
- Format handoffs: spreadsheets go to `xlsx`, documents to `docx`, decks to `pptx`. This skill supplies content, structure, evidence, markers, and placeholders; the built-in creates or formats the file.
- If a save, export, or write fails, never claim it succeeded. Report what was produced, where it was and was not written, and what remains incomplete.
- Nothing is sent, submitted, filed, posted, committed to a consultant database, client portal, other portal/database, or emailed by this skill. A draft is a draft and is reported as a draft; the human submits.
- Reuse firm-approved library material only within the firm's authorized rights and this task. For third-party filings, policies, or other protected text, use only brief necessary excerpts where permitted; otherwise summarize with attribution or request authorized source material. Attribution does not grant reproduction rights. Never present third-party wording as the firm's own or relabel a source's classification into another scheme.
- **Never compute, estimate, annualize, or restate a return.** Verbatim from the configured performance connector or the uploaded export, or flagged.
- Never carry period-specific content forward from prior commentary.
- Never write an outlook or forecast of your own. Approved house view, or the user's dictated input marked `UNAPPROVED — new claim, requires review` with all hedging preserved.
- Never produce projected, targeted, hypothetical, or backtested performance — including when the user dictates it.
- Never characterize performance as strong, disappointing, or pleasing — describe it.
- **State the basis on every performance figure, and never conflate bases.** Where gross is presented in externally intended material, net must appear with equal prominence, same periods, same methodology — or the section is blocked. Never compute or convert between bases.
- Every macro claim carries a source and an as-of date.
- Marketing material: label `MARKETING MATERIAL — COMPLIANCE REVIEW REQUIRED`.
- Carry the firm's disclosure block, or flag loudly that it is missing.

See `references/house-rules.md` for citation format, gap markers, and the marketing-material rules.

## Output footer

Output length never waives this footer. A one-line answer, single table cell, inline reply, or short excerpt still carries its citations and the footer below.

```
Workflow: named fund/portfolio/strategy investment commentary
Strategy / period: <name>, <period> — figures on a <gross | net | gross and net> basis
Performance source: <export filename, connector name, or "NOT PROVIDED — placeholders left">
Archive used: <prior commentary documents referenced>
Macro sources: <FRED series / house view document, with as-of dates>
Intended use: <internal (confirmed) | external distribution | UNRESOLVED — performance section blocked>
Performance basis: <both presented | net only | gross only (internal use — not for external distribution) | PERFORMANCE BLOCKED — gate row <n>: <reason>>
Presentation policy: <named policy, and why it applies to this material | not applicable — confirmed internal use | none identified — performance section blocked | identified but not applicable to this material — performance section blocked>
Policy requirements not satisfied: <named requirement(s) that blocked a section — or "none">
Unapproved dictated claims: <count, and where they appear — or "none">
Template: <file used>
Connectors: <MCPs used, or "none">
Gaps: <NOT FOUND / NOT RETRIEVED / placeholder / blocked-section items>
MARKETING MATERIAL — COMPLIANCE REVIEW REQUIRED (omit this line only where intended use is
confirmed internal; use INTERNAL USE ONLY — NOT FOR EXTERNAL DISTRIBUTION instead). Performance
figures used verbatim from the named system-of-record source; none were computed, adjusted, or
converted between gross and net. Any claim marked UNAPPROVED came from user dictation and has
not been through approval. This footer records what the draft contains; it is not a compliance
determination. Draft for review; nothing sent.
```

**Where a gross-only performance section was permitted under confirmed internal use (gate row
7), the draft carries `INTERNAL USE ONLY — NOT FOR EXTERNAL DISTRIBUTION` on the performance
section itself, not only in the footer.** That figure has not passed the external gate, so it
cannot be lifted into client-facing material without re-running the gate.
---

## Reference files

- `references/house-rules.md` — shared decision gate, attribution and sourcing rules, blocked-vs-absent states, markers, and output footers.
- `references/commentary-outline.md` — default commentary structure: period framing, attribution, positioning, outlook, and required disclosure blocks.
