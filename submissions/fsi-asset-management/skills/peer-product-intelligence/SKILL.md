---
name: peer-product-intelligence
description: Compare named investment funds or strategies in a sourced, share-class-specific matrix; describe differences without ranking products. Use for "how does our fund stack up", "build a competitive matrix", "benchmark this product against peers", "compare our fees to theirs", or "what differs between these funds". Do NOT use for issuer filing diffs — use security-research-brief instead; for new questionnaires, use rfp-ddq-response-draft instead; for recurring profiles, use consultant-database-refresh instead; for mandate reviews, use institutional-client-review-prep instead; for investment commentary, use investment-commentary-draft instead; for workbook formatting, use xlsx instead.
---

## Quick Start

User: "Build a product comparison for these three supplied fund share classes."

Confirm each share class, record comparable gross/net fees and dated source cells, distinguish all retrieval outcomes, and describe differences without a preference judgment.

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

**Do:** build a sourced product matrix, compare fields across funds, cite every cell, flag unavailable records.
**Do not:** conclude which product is better, compare gross to net fees, recalculate ratings or percentiles, or source from memory.

## When NOT to Use

- **Single issuer filing analysis** — use `security-research-brief` instead.
- **Questionnaire answers or recurring profile refreshes** — use `rfp-ddq-response-draft` or `consultant-database-refresh` instead.
- **Formatting, charting, or restyling an existing workbook** — use the built-in `xlsx` instead.

# Competitor Product Comparison

Build a sourced, side-by-side product matrix from public fund documents.

**Do:** assemble comparable fields across funds, cite each cell, and flag what is unavailable.
**Do not:** conclude which fund is better, rank them, or characterize fees as high or low. A
product specialist draws the conclusion; this builds the evidence.

## Workflow

### 1. Confirm the comparison set

Ask for the competitor funds if the user has not named them. Accept tickers or fund names —
tickers are far more reliable.

**Keep it to 3–5 funds including your own.** Each fund costs two or three browser page loads
and they are slow. If the user wants more, build the core set, deliver it, and offer to extend.

If the user names a fund family without a specific fund, **list the candidate share classes
with tickers and ask** — share classes differ in fee, and comparing the wrong class is a
substantive error, not a cosmetic one.

### 2. Pull each fund's summary prospectus

Read `references/edgar-access.md` first — it covers the retrieval routes and the fund lookup.

A fund **share-class ticker works directly** in EDGAR's company lookup, returning the trust's
filings. Open the most recent **497K summary prospectus**: 13–18 KB of text containing almost
everything this matrix needs.

| Field | Where it comes from |
|---|---|
| Investment objective | 497K, stated verbatim |
| Management fee, 12b-1, other expenses | 497K fee table |
| **Gross and net expense ratio** | 497K fee table — record **both** |
| Fee waiver and its expiry | 497K fee table footnotes |
| Principal investment strategy | 497K |
| Principal risks | 497K |
| Past performance | 497K annual return table |

**Record the filing date of each prospectus.** Comparing a 2026 prospectus against a 2024 one
is a real error; if dates differ materially, say so in the footer.

### 3. The fee trap — read this before filling the fee row

Fee tables show a **gross** expense ratio and a **net** ratio after contractual waivers, with an
expiry date.

Comparing one fund's gross ratio to another's net ratio is the single most likely substantive
error in this matrix, and it is invisible in the output once made.

**Record both for every fund**, plus the waiver expiry. If a waiver expires within twelve
months, flag it — the net figure is temporary.

### 4. Holdings, percentiles, ratings, and flows — source-dependent fields

These four fields rarely have a free public source that this workflow can use, but that is a
tendency, not a rule about the field. **Whether a cell is filled depends on what this session can
actually obtain, not on which category the field belongs to.** A rating published on an
issuer-authored page, a percentile in a supplied authoritative report, or a complete public
holdings filing all fill the cell exactly as a connector would. Never leave a cell flagged when
an authoritative source actually supplied it — that is the failure this section exists to
prevent — and never assume a field is unavailable without checking.

Resolve each cell in four separate steps, and do not collapse them:

1. **Is any source available?** A connector named in this file is not evidence it exists in this
   session, and its absence is not evidence that nothing else can supply the field. Check both.
2. **Did retrieval succeed?** A source can fail or be unauthorized. "No permission" and
   "retrieval failed" are different outcomes — report which.
3. **Did the search return anything?** A successful search that legitimately returns no record is
   a real finding, and is **not** the same as a failure. Report it as such.
4. **Is the record usable?** It must identify the **correct product and share class**, carry a
   **measurement date or period**, and state the **basis, unit, or methodology** where one
   applies. A record that does not match on identity, date, or basis is a gap — never a silent
   substitute for the cell you wanted.

| Outcome | Cell |
|---|---|
| A matching record was obtained | The value, with **cell-level attribution**: source, product/share class, as-of date, basis |
| No source available for this field | `NEEDS FEED — <source that would supply it>` |
| Source exists but access was denied | `NOT RETRIEVED — <source> access denied` |
| Source exists, retrieval failed | `NOT RETRIEVED — <source> did not return` |
| **Source searched successfully, no record exists** | **`NOT FOUND — <source> has no record for <fund / share class / period>`** |
| Retrieved but wrong share class, stale, or incompatible period/basis | `GAP — <source> record does not match <identity / date / basis>` |

**`NOT FOUND` and `NOT RETRIEVED` are opposite findings.** `NOT FOUND` means the source worked
and the fund genuinely has no such record — a fund with no rating because it is too new, for
instance, which is itself informative. `NOT RETRIEVED` means you never got an answer. Reporting
one as the other tells the reader to take the wrong next step.

**Report ratings and percentiles exactly as published.** Never recalculate a percentile, derive a
rating, or convert between scales — and never conclude from them that one product is better.

Top holdings also come from each **fund company's public fact sheet** — an issuer-authored
document, cited with its as-of date, not marked as secondary. It typically shows the top ten.
State that it is the top ten and give the date.

**Full portfolio holdings usually have no workable public route.** The N-PORT filing measured for
one large fund was 488 KB of raw XML and 9.5 MB rendered — far past what a page read can handle.
Treat that as the scale to expect, not as a universal rule: **if this session can retrieve a
complete public holdings filing, use it** and state the coverage. A successfully retrieved,
complete N-PORT is a filed record and fills the row — it does not need a connector to be citable.
Do not claim a large filing is always retrievable, and do not refuse one solely on assumed size.

**The rule is about whether a matching record was obtained, not about which kind of source
obtained it.** Fill the row when any authoritative source supplies one. When none does, use the
outcome marker that matches what actually happened — `NEEDS FEED` only when no source exists for
the field, not when retrieval failed or a record did not match. Full holdings remain the clearest
single reason for this plugin's users to add a connector, so state that plainly rather than
quietly omitting the row.

### 5. Our own fund

Fill the descriptive fields — objective, strategy, structure, share classes, inception —
from **approved internal sources**: the product master, approved fact sheet, or approved
library. Never from memory.

**Our current figures follow the stricter rule.** Our performance, fees, and AUM come verbatim
from an uploaded system-of-record export or a field-appropriate connector, or the cell holds a
value-less `[VERIFY vs. system of record]` placeholder. An approved fact sheet is not evidence
that its number is still current — approval clears a claim, it does not date-stamp it. Our own
**filed** 497K may be cited for what it states as of its filing date, labelled as such.

**Competitor figures follow the tier table, not this rule.** A competitor's expense ratio or
past performance in its own 497K is a **filed record**, and its own fact sheet is an
**issuer-authored** document — both cited plainly, neither flagged `[VERIFY vs. system of
record]`. That marker means "check against our books," which is meaningless for someone else's
fund. Only reproductions — aggregators, news, search results — carry `UNVERIFIED — secondary
source`. The same tiers apply to our own documents, so the two columns stay comparable.

### 6. Output

Template resolution: user-named file → M365 `Cowork Templates/Asset Management/peer-product-intelligence/` → `references/matrix-outline.md`.

Deliverable: `.xlsx` matrix — one column per fund, one row per field, with a source-and-date
cell for every value. Optional `.docx` summary describing the differences factually.

Output length never waives attribution or the output footer: one-line answers, single table cells, inline replies, and short excerpts still carry citations and the footer. If the requested artifact is a spreadsheet, document, or deck, supply content, structure, evidence, markers, and placeholders, then hand creation or formatting to `xlsx`, `docx`, or `pptx` as appropriate.

## Source resolution

1. **Configured MCP**
   - `Morningstar Direct` / `eVestment` → peer percentiles, ratings, flows, and **full holdings**. The upgrade that removes this skill's main v1 limitation.
   - Internal product master → our-fund **descriptive** fields (objective, strategy, structure, share classes, inception) from approved data. It supplies a current fee, AUM, or return **only** where the firm designates it the system of record for that field; otherwise those cells stay value-less.
2. **User upload** — competitor fact sheets, prior comparison files.
3. **Public primary** — 497K summary prospectuses, fund-company fact sheets, and public holdings filings where one can be retrieved in full.
4. **Flag** — `NEEDS FEED` for percentiles, ratings, flows, and full holdings **only when no source supplies them**; `NOT RETRIEVED` when a source existed but access was denied or retrieval failed; `NOT FOUND` when a source answered and no record exists; `GAP` when a record was returned but does not match on product, share class, date, or basis.

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

- Output length never waives attribution or the output footer. A one-line answer, single table cell, inline reply, or short excerpt still carries its citation and this skill's footer.
- Never fabricate a figure, quote, date, source, approval status, or document state. Use the skill's gap marker instead.
- If an input page or source document is unreadable, report `NOT LEGIBLE — <document>, page <n>`, ask for a cleaner copy, and never guess.
- Distinguish unavailable sources exactly: no source exists is `NEEDS FEED`; a source exists but retrieval failed or was denied is `NOT RETRIEVED`; a source answered and has no record is `NOT FOUND`. Never collapse these outcomes.
- Never delete or overwrite existing content, prior submissions, decision sections, reviewer notes, or source files; append, redline, or preserve unless the user explicitly supplies a new blank artifact.
- Format handoffs: spreadsheets go to `xlsx`, documents to `docx`, decks to `pptx`. This skill supplies content, structure, evidence, markers, and placeholders; the built-in creates or formats the file.
- If a save, export, or write fails, never claim it succeeded. Report what was produced, where it was and was not written, and what remains incomplete.
- Nothing is sent, submitted, filed, posted, committed to a consultant database, client portal, other portal/database, or emailed by this skill. A draft is a draft and is reported as a draft; the human submits.
- Reuse firm-approved library material only within the firm's authorized rights and this task. For third-party filings, policies, or other protected text, use only brief necessary excerpts where permitted; otherwise summarize with attribution or request authorized source material. Attribution does not grant reproduction rights. Never present third-party wording as the firm's own or relabel a source's classification into another scheme.
- **Never conclude which fund is better, cheaper, or stronger.** Present fields; the specialist concludes.
- **Never compare gross to net expense ratio.** Record both for every fund.
- Never compare across share classes without labelling which class each column is.
- **Fill peer percentiles, star ratings, flows, and full holdings whenever any authoritative source supplies a matching record** — a connector, an issuer-authored publication, or a complete public filing — with cell-level attribution. Flag them only when no source exists, retrieval failed, no record was found, or the record does not match. Never leave an available value unfilled, never treat a field as unavailable without checking, and never use `NEEDS FEED` to describe a retrieval failure or a genuine absence.
- **Never recalculate a percentile or derive a rating.** Report them exactly as published.
- Never source competitor facts from memory; every cell cites a document and date.
- **Competitor fees and past performance come from the fund's own 497K** — that is the primary record, cited, not flagged against our system of record. Only **our** figures carry `[VERIFY vs. system of record]`.
- Note when prospectus dates differ materially across the set.
- **Our-fund current performance, fees, and AUM come verbatim from the system of record or a field-appropriate connector** — otherwise a value-less `[VERIFY vs. system of record]` cell. An approved fact sheet establishes approval, not currency.
- If shown to any client or prospect this becomes marketing material — label it `MARKETING MATERIAL — COMPLIANCE REVIEW REQUIRED` and present fields fair-and-balanced rather than selecting flattering ones.

See `references/house-rules.md` for citation format, gap markers, and the marketing-material rules.

## Output footer

Output length never waives this footer. A one-line answer, single table cell, inline reply, or short excerpt still carries its citations and the footer below.

```
Funds compared: <name (ticker, share class)> × n
Prospectus dates: <date per fund — flag if they differ materially>
Expense ratios: <gross and net recorded per fund; waiver expiry where applicable>
Holdings: top-10 from fact sheets as of <dates> | full holdings <source + as-of | outcome marker>
Source-filled cells: <source, fields, as-of dates, basis — or "none">
Our figures requiring verification: <count — [VERIFY vs. system of record]>
Secondary-sourced cells: <count — UNVERIFIED>
Template: <file used>
Connectors: <MCPs used, or "none">
Other sources used: <public prospectuses | fact sheets | public filings | supplied documents>
Gaps: <NEEDS FEED (no source exists) / NOT RETRIEVED (access denied or retrieval failed) / NOT FOUND (source answered, no record exists) / GAP (record did not match)>
MARKETING MATERIAL — COMPLIANCE REVIEW REQUIRED if shown externally. Describes differences
between products; draws no conclusion about which is preferable.
```
---

## Reference files

- `references/house-rules.md` — shared decision gate, attribution and sourcing rules, blocked-vs-absent states, markers, and output footers.
- `references/edgar-access.md` — capability-aware SEC EDGAR access, company and accession resolution, and filing-section retrieval. Read before citing a filing.
- `references/matrix-outline.md` — default peer comparison matrix: field definitions, source-outcome states, and coverage reconciliation.
