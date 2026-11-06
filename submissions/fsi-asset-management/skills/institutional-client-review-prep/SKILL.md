---
name: institutional-client-review-prep
description: Prepare a named institutional investment-client mandate review from IPS/guidelines, relationship commitments, and prior materials; separate the internal brief and client deck. Use for "prep our endowment client's review", "get ready for this client's consultant", "build the mandate review", "what do we owe this plan sponsor", or "pull the client's IPS". Do NOT use for the manager's own board/operating/forecast review or standalone stakeholder Q&A — use Finance forecast-review-prep or stakeholder-qa-prep if available; for commentary, use investment-commentary-draft instead; for questionnaires, use rfp-ddq-response-draft instead; for transcript summaries, use meeting-intel if available.
---

## Quick Start

User: "Prepare the Northstar Endowment investment-mandate review from these supplied records."

Confirm the mandate and logistics, reconcile OPEN/CLOSED/UNCLEAR commitments, summarize the IPS without a compliance judgment, and keep internal observations out of the client deck.

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

**Business-workflow boundary:** requires a named institutional investment client/mandate, or a consultant acting on that client's review. A client trustee/board review is in scope only in that investment-relationship context; the manager's own board, operating, budget, and forecast reviews are not. The IPS/guidelines and client commitments distinguish this deliverable from a general business pre-read.

**Do:** gather relationship history, prior materials, open items, logistics, build a briefing and deck skeleton.
**Do not:** fill performance, attribution, holdings, or compliance pages without system-of-record data, assess guideline compliance, characterize relationship health, or auto-send.

## When NOT to Use

- **Internal operating, forecast, company-board, or generic business-review preparation** — Finance `forecast-review-prep` if available; **standalone anticipated stakeholder Q&A** — Finance `stakeholder-qa-prep` if available. Follow `references/house-rules.md`; never fill an evidence gap with a generic review pack.
- **Strategy-level commentary not tied to a meeting** — use `investment-commentary-draft` instead.
- **Filling out a questionnaire** — use `rfp-ddq-response-draft` instead.
- **Meeting transcript summaries or extracted action items** — use the built-in `meeting-intel` instead.

# Institutional Investment-Client Review Prep

Assemble what the team already knows about a relationship into a briefing and a deck skeleton,
so preparation starts from the record rather than from memory.

**Do:** gather relationship history, prior materials, open items, and logistics; build the deck
structure from approved content.
**Do not:** fill performance, attribution, holdings, or compliance pages from a prior deck, a
prior document, memory, or your own calculation; invent commitments; or characterize the
relationship's health. Current field-appropriate system-of-record data is necessary for those pages, not sufficient: performance and performance-bearing attribution also require the actual-output presentation gate to permit them. Holdings and guideline-compliance records need their own system of record. Otherwise the affected pages stay value-less placeholders.

> **Boundary:** this is **institutional investment-client** service — a plan sponsor, endowment,
> or its consultant/trustee board reviewing the investment mandate. Individual-household advisor
> prep belongs to Wealth Management `client-meeting-prep-pack` if available; that skill organizes
> personal financial context but does not make suitability determinations. Confirm availability
> before handing off, and never claim another skill ran.

## Workflow

### 1. Identify the relationship and the meeting

Resolve the client/mandate and the consultant's relationship to it before gathering a pack. "Board presentation" or "quarterly review" alone is not enough: clarify whether this is an investment-client mandate review or an internal business review. If the client purpose is established but an IPS or prior review is unavailable, retain that gap explicitly; do not substitute a corporate operating-review structure.

Confirm the client or consultant name and the meeting date. Check the calendar for the meeting
to get attendees, duration, and format.

**Attendees matter.** A review with the consultant present is a different conversation from one
with the sponsor alone. List who is expected, with their organization and role where known.

If multiple meetings match, list them and ask.

### 2. Gather the relationship record

Search WorkIQ across the signed-in user's own access:

- **Outlook** — recent correspondence with the client and consultant, especially unanswered threads and anything containing a commitment
- **Teams** — internal discussion about the relationship
- **SharePoint** — the prior review deck, the IPS or investment guidelines, the current agreement, prior meeting notes
- **Planner** — open action items on this relationship

**Distinguish four outcomes per source, and never merge them:** the capability is not available
in this session; it is available but access was denied; retrieval failed; retrieval succeeded and
returned nothing. "No open action items" and "Planner was not reachable" are different findings,
and only the first is information about the relationship. Say which you got.

If a source is unavailable, **continue with the rest** — the review is still useful — and list
what could not be checked so the reader knows the coverage.

Search a defined window — default the last two quarters, or since the prior review if you can
identify it — and **say which window you used.**

### 3. Surface open items — the part that actually gets people in trouble

From prior meeting notes, Planner, and email, extract:

- Commitments the firm made, and whether the record shows them closed
- Questions the client asked that the record shows no answer to
- Items carried over from the prior review

**Mark each as `OPEN`, `CLOSED`, or `UNCLEAR`.** Do not report an item as closed unless the
record shows it. `UNCLEAR` is honest and useful; a wrongly-closed item is the thing that
surfaces awkwardly in the meeting.

### 4. Read the IPS and guidelines

Where an IPS or guidelines document exists, summarize the objective, constraints, permitted
ranges, and any reporting the client is owed.

**Do not assess compliance with guidelines.** Stating that a portfolio is within or outside its
ranges requires holdings and a system of record. If the user wants that, say it needs the
performance or compliance system.

### 5. Build the deck skeleton

Structure from the prior review deck where one exists — it reflects what this client expects to
see. Populate only sections that approved content supports:

- Firm and team updates → approved boilerplate
- Market backdrop → approved house view, or cited public macro (FRED, BLS, Treasury). Open the public primary source through a working direct-fetch or browser route; retry once on transient failure, then ask for an upload. Search snippets or third-party reproductions remain `UNVERIFIED — secondary source`; a primary document actually opened and read retains its primary provenance. Do not put unreviewed secondary material into the client deck
- Strategy commentary → the approved commentary archive
- **Performance and performance-bearing attribution → value-less placeholders** until a current field-appropriate system-of-record connector/export supplies the figures **and** the presentation gate permits this actual client-deck output. A current export alone is never sufficient.
- **Holdings and guideline compliance → flagged placeholders** unless their own field-appropriate system of record supplies the current record verbatim; never assess compliance yourself

```
[PERFORMANCE — populate from system of record]
```

Never fill a performance page from a prior deck. Last quarter's numbers in this quarter's deck
is the failure mode this placeholder exists to prevent.

**Audience-separation preflight.** Before finalizing the client artifact, compare it against every source item marked internal/reviewer-only. Exclude the private content, its paraphrases, preparation/ownership checks, and metadata revealing what was excluded. Do not write a client-facing sentence such as "an internal note about <topic> was excluded" — that still discloses the topic. Only the separate internal briefing may discuss those notes. Keep independently supported client commitments visible in client-appropriate wording; do not suppress a legitimate client open item merely because an internal preparation note concerns the same general subject. Apply this check to slide text, speaker/source notes, appendices and the client footer; a generic statement that a separate internal briefing exists must reveal no private subject.

### 6. Output

Template resolution: user-named file → M365 `Cowork Templates/Asset Management/institutional-client-review-prep/` → `references/prep-outline.md`.

Deliverables: a `.docx` briefing for the team, and a `.pptx` deck skeleton for the client
meeting. Keep them separate — the briefing contains internal observations that should not
travel into a client-facing document.

Output length never waives attribution or the output footer: one-line answers, single table cells, inline replies, and short excerpts still carry citations and the footer. If the requested artifact is a spreadsheet, document, or deck, supply content, structure, evidence, markers, and placeholders, then hand creation or formatting to `xlsx`, `docx`, or `pptx` as appropriate.

## Performance-presentation gate

Apply the shared **Performance presentation across externally intended drafts** gate in `references/house-rules.md` before populating performance or performance-bearing attribution. Establish intended use for **each actual artifact/field**, not once for a mixed internal/client pack. Current field-appropriate system-of-record data is necessary but is not presentation permission.

For externally intended performance fields, require a compliance-approved policy applicable to that actual material type, audience and distribution, and satisfy its substantive requirements. External gross-only data, missing/inapplicable policy, unmet requirements, incompatible periods/methodology, or unresolved intended use leaves value-less `[PERFORMANCE BLOCKED — <reason>]` fields. Never compute net, normalize, or substitute a disclaimer.

Preserve the shared gate's confirmed-internal-only branch: current source figures may appear with their basis and `INTERNAL USE ONLY — NOT FOR EXTERNAL DISTRIBUTION` labels without an external presentation policy, subject to the other source/compatibility rules. Historical prior values may remain only in clearly separate internal reviewer `PRIOR` lines or gap/change records, never in proposed answers or the client deck. An externally intended draft is not internal-only merely because a reviewer sees it first; rerun the external gate before moving any internal figure into external material.

Continue every other supportable draft section, preserve existing question states/flags and internal/client separation, and record each artifact's intended use, policy applicability, unmet requirements and gate outcome in its footer. This records draft evidence, never a legal-compliance determination or distribution approval.

## Source resolution

1. **Configured MCP**
   - `CRM` (`Salesforce`, `Dynamics`) → the full relationship record, prior notes, and action items in one place. Highest-value upgrade for this skill.
   - Performance/attribution system → supplies current figures verbatim, but the **performance and attribution** pages populate only after the presentation gate permits this actual output. Source resolution never grants presentation permission. This system does **not** establish holdings or guideline compliance — those stay placeholders unless their own system of record supplies them.
2. **User upload** — a prior deck, the IPS, or meeting notes not in SharePoint. An uploaded system-of-record export supplies matching fields verbatim; performance-bearing pages still require the actual-output presentation gate, and holdings/compliance require their own appropriate records.
3. **M365 / WorkIQ** — Outlook, Teams, SharePoint, Calendar, Planner.
4. **Flag** — `NOT FOUND` (searched, not there — say where you searched) or `NOT RETRIEVED` (found but could not be opened). Never report the second as the first.

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

- Current source data alone never authorizes external performance. Apply the actual-output presentation gate; preserve its internal-only branch and separate historical reviewer records without allowing an external-field bypass.

- **Named investment-client mandate review only.** No generic board/forecast packs or standalone stakeholder Q&A, including through customer templates.
- Output length never waives attribution or the output footer. A one-line answer, single table cell, inline reply, or short excerpt still carries its citation and this skill's footer.
- Never fabricate a figure, quote, date, source, approval status, or document state. Use the skill's gap marker instead.
- If an input page or source document is unreadable, report `NOT LEGIBLE — <document>, page <n>`, ask for a cleaner copy, and never guess.
- Distinguish unavailable sources exactly: no source exists is `NEEDS FEED`; a source exists but retrieval failed or was denied is `NOT RETRIEVED`; a source answered and has no record is `NOT FOUND`. Never collapse these outcomes.
- Never delete or overwrite existing content, prior submissions, decision sections, reviewer notes, or source files; append, redline, or preserve unless the user explicitly supplies a new blank artifact.
- Format handoffs: spreadsheets go to `xlsx`, documents to `docx`, decks to `pptx`. This skill supplies content, structure, evidence, markers, and placeholders; the built-in creates or formats the file.
- If a save, export, or write fails, never claim it succeeded. Report what was produced, where it was and was not written, and what remains incomplete.
- Nothing is sent, submitted, filed, posted, committed to a consultant database, client portal, other portal/database, or emailed by this skill. A draft is a draft and is reported as a draft; the human submits.
- Reuse firm-approved library material only within the firm's authorized rights and this task. For third-party filings, policies, or other protected text, use only brief necessary excerpts where permitted; otherwise summarize with attribution or request authorized source material. Attribution does not grant reproduction rights. Never present third-party wording as the firm's own or relabel a source's classification into another scheme.
- **Performance and performance-bearing attribution populate only from current field-appropriate system-of-record data verbatim AND after the actual-output presentation gate permits them. Holdings and guideline compliance require their own appropriate current system-of-record records verbatim. Otherwise the affected fields remain value-less placeholders. There is no third path** — never from a prior deck, prior document, memory, your own calculation, or a template bypass.
- Never assess guideline or IPS compliance yourself; a performance connector does not satisfy this.
- Never report an open item as closed without record evidence; `UNCLEAR` is the honest marker.
- Operate only within the signed-in user's own M365 permissions.
- Keep the internal briefing separate from the client-facing deck.
- The deck is marketing material: label it `MARKETING MATERIAL — COMPLIANCE REVIEW REQUIRED`.
- Nothing auto-sends; no meeting invitations or client emails are sent.
- Do not characterize the relationship as healthy, strained, or at risk — report what the record shows.

See `references/house-rules.md` for citation format, gap markers, and the marketing-material rules.

## Output footer

Output length never waives this footer. A one-line answer, single table cell, inline reply, or short excerpt still carries its citations and the footer below.

```
Workflow: institutional investment-client mandate review
Performance intended use: <internal confirmed | external | unresolved>
Presentation policy: <name, applicability to this material, or missing/inapplicable>
Performance gate: <permitted basis and periods | BLOCKED — reason>
Policy requirements not satisfied: <requirement(s) or none>
Relationship: <client / consultant>      Meeting: <date, attendees>
Search window: <period covered>
Sources: <Outlook / Teams / SharePoint documents / Planner — named>
Open items: <n OPEN · n UNCLEAR · n CLOSED>
Placeholders requiring system of record: <count>
Template: <file used>
Connectors: <MCPs used, or "none — M365 content only">
Gaps: <NOT FOUND items and where searched · NOT RETRIEVED items and what failed>
Briefing is internal. Deck is MARKETING MATERIAL — COMPLIANCE REVIEW REQUIRED. Nothing sent.
```
---

## Reference files

- `references/house-rules.md` — shared decision gate, attribution and sourcing rules, blocked-vs-absent states, markers, and output footers.
- `references/prep-outline.md` — default meeting-prep pack: agenda, holdings and performance sections, open items, and question list.
