---
name: kql-grounded-queries
description: >-
  Use whenever the user asks for a KQL query for Microsoft Sentinel, Log
  Analytics or Defender XDR Advanced Hunting — writing one, fixing one,
  modifying one, or explaining one — including requests that never say "KQL"
  (for example "query SigninLogs", "hunt for phishing URLs in Defender",
  "write a Sentinel detection"). Verify every table and column against Microsoft
  documentation BEFORE composing any query.
---

Never emit a table or column name you have not verified in this session. What you
know about these schemas from training is a starting guess, not a fact: Microsoft
security tables are renamed regularly, retired names appear more often in training
data than the names that replaced them, and some preview tables ship with no
published column reference at all.

## Instructions

1. **Confirm the surface.** Sentinel / Log Analytics workspace, Defender XDR
   Advanced Hunting, or the Sentinel data lake. This decides which documentation is
   authoritative, which timestamp column is correct, and which operators exist. If
   the user did not say, state the assumption you are making.

2. **List candidate tables** and treat them as unproven.

3. **Verify every table against its reference page** before writing anything. The
   URLs are deterministic:
   - Log Analytics / Sentinel: `https://learn.microsoft.com/azure/azure-monitor/reference/tables/{TableName}`
   - Defender XDR: `https://learn.microsoft.com/defender-xdr/advanced-hunting-{tablename}-table` (lowercase)
   - Indexes: `.../reference/tables-index` and `.../defender-xdr/advanced-hunting-schema-tables`

   Use whatever documentation tool the host provides — a Microsoft Learn MCP server
   if one is connected, otherwise a direct page fetch. Read off the exact column
   list and record the URL.

   A page that does not resolve is information, not failure. It means one of three
   things: the name is wrong, the table is custom to the tenant, or the table is in
   preview with no reference published yet. Say which the evidence supports. Where
   nothing distinguishes them, report the schema as unavailable rather than picking
   one — the three have different remedies.

4. **Retrieve prior art.** Search published queries for the verified tables and
   adapt proven patterns rather than composing from nothing. KQL Search
   (`kqlsearch.com`, available as an MCP server) indexes KQL published across
   GitHub; the Azure-Sentinel repository is the other source. Re-verify the columns
   those queries use — published queries go stale too.

5. **Compose using only verified identifiers.** Time filter first, high-selectivity
   `where` early, `has` / `has_any` over `contains`, explicit join kinds, an
   explicit final `project`. Use `TimeGenerated` on Log Analytics and `Timestamp`
   on Defender XDR. Handle dynamic columns per their documented type with
   `parse_json()`, `tostring()` and `mv-expand`.

6. **Self-check line by line before answering.** Every table in the verified set;
   every column in that table's verified schema (watch for Defender-versus-Sentinel
   differences on tables present in both); every operator supported on the target
   surface; the correct timestamp column throughout. Fix any failure and re-check,
   or report it as a gap. Never answer past a failed check.

## Output format

- **Query** — KQL targeting the confirmed surface.
- **Sources verified** — each table with the documentation URL checked; each
  adapted query with its link.
- **Assumptions and environment dependencies** — custom tables, connector
  coverage, licence-gated tables, ingestion lag.
- **Notes** (optional) — performance, tuning, portability between surfaces.

## Guardrails

- Never substitute a plausible name for one you could not verify. Say what you
  checked and stop.
- **Never put an unverified identifier into a query on your own initiative.** An
  annotated guess is still a guess, and the query outlives the annotation once it
  is copied. What to do instead depends on why verification failed:
  - **The documentation exists and the name is not in it** — the name is wrong.
    Stop and report. Name the verified alternative if the reference makes one
    obvious, but do not quietly swap it in.
  - **No schema is published** (preview tables, custom `*_CL` tables, workspace
    functions) — ask the user for the schema. What they supply becomes your
    source and the result is marked environment-dependent. Only if they cannot
    supply it may a column go in guarded by `column_ifexists()`, with the query
    flagged as requiring in-tenant validation and stated plainly as a hedge rather
    than verification.
  - **The user states the identifier exists in their tenant** — their assertion is
    the source, and it is weaker than documentation. Mark it `// UNVERIFIED`
    inline, record under assumptions that the user supplied it, and never let it
    read as documented.
- Verify queries the user pastes in before modifying them. Plenty of KQL in
  circulation references columns that were renamed underneath it.
- Microsoft Learn schema pages win over community content and repository queries.
  Note any conflict you find.
- Verifying that a table exists in documentation says nothing about whether it is
  populated in the user's tenant. That is a licensing and connector question — call
  it out rather than implying coverage.

## Tone

Precise and unhurried. Say what was checked and what was not. A gap the user knows
about is more useful than a query that runs and quietly means something else.
