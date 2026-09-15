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
   - Log Analytics index: `https://learn.microsoft.com/azure/azure-monitor/reference/tables-index`
   - Defender XDR index: `https://learn.microsoft.com/defender-xdr/advanced-hunting-schema-tables`
   - Sentinel data lake asset tables: `https://learn.microsoft.com/azure/sentinel/datalake/asset-data-tables`

   Use whatever documentation tool the host provides — a Microsoft Learn MCP server
   if one is connected, otherwise a direct page fetch. Read off the exact column
   list and record the URL.

   **A failed lookup is not a verdict.** A timeout, a 403, a redirect that does not
   land, a URL template that has moved — and a 404, which Learn also serves for a
   slug it simply does not recognise — say nothing on their own about the schema.
   Retry once, then go to the index page. Never convert a retrieval result into a
   conclusion about the table.

   **Absence is established by a page you actually read**: an index that lists the
   surface's schema and does not list your table. That is information, not failure,
   and it means one of three things — the name is wrong, the table is custom to the
   tenant, or the table is in preview with no reference published yet. Say which the
   evidence supports. Where nothing distinguishes them, report the schema as
   unavailable rather than picking one; the three have different remedies. Where you
   could not read an index either, the answer is that the lookup failed, and you
   stop there.

4. **Retrieve prior art.** Search published queries for the verified tables and
   adapt proven patterns rather than composing from nothing. KQL Search
   (`kqlsearch.com`, available as an MCP server) indexes KQL published across
   GitHub; the Azure-Sentinel repository is the other source. Re-verify the columns
   those queries use — published queries go stale too.

5. **Compose using only verified identifiers.** Time filter first, high-selectivity
   `where` early, explicit join kinds, an explicit final `project`. Handle dynamic
   columns per their documented type with `parse_json()`, `tostring()` and
   `mv-expand`.

   `has` and `has_any` index whole terms and are the faster choice, but they are not
   a drop-in replacement for `contains`: anything that needs substring matching —
   inside a URL, a file path, a command line, a domain fragment — requires
   `contains` or an explicit term split. Choose on the semantics the hunt needs and
   say which you chose.

   The timestamp column is a property of the surface and is never carried across:
   `TimeGenerated` on Log Analytics and Sentinel, `Timestamp` on Defender XDR
   Advanced Hunting, and on the Sentinel data lake whatever the table's own schema
   documents. `TimeGenerated` is usual in the lake but not universal — federated
   tables may lack it or carry it in a form the time range cannot use, and asset
   tables also carry `_SnapshotTime` and `_ReceivedTime`. Read it off the schema
   like any other column, and account for the lake's ingestion latency rather than
   querying up to `now()`.

6. **Self-check line by line before answering.** Every table in the verified set;
   every operator supported on the target surface; the correct timestamp column
   throughout. Check the two kinds of column name differently: a **source column**
   read from a table must appear in that table's verified schema (watch for
   Defender-versus-Sentinel differences on tables present in both), while a name
   created by the query itself — `extend`, `summarize`, a renaming `project`, a
   join's right-hand prefix — is checked against the query's own dataflow, that it
   is defined before it is used and not shadowed later. Fix any failure and
   re-check, or report it as a gap. Never answer past a failed check.

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
    functions) — ask the user for the schema, from the portal's schema tab or a
    `getschema` run. What they supply becomes your source: the identifier is then
    verified against their tenant rather than against Learn, and the result is
    marked environment-dependent throughout. If they cannot supply it, stop.
    A `column_ifexists()` version is offered only if the user asks for one, and it
    is labelled a diagnostic rather than a query to keep: a name that is not there
    resolves silently to the default for every row, so a filter on it matches
    nothing or everything and a `summarize` collapses into one bucket. The query
    runs, and what comes back is a false negative wearing the shape of a real
    result. Say that in the answer, every time.
  - **The user asserts an identifier without a schema to back it** — that is a
    claim about their environment, not a source. It does not put the name in the
    query. Ask for the schema tab or a `getschema` run, which turns it into the
    case above; until then the answer is the gap, not a marked-up guess.
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
