# Overview

Ask a model for a KQL query and you get one straight away. Good formatting, sensible
operators, and every so often a column that has never existed in that table.

The model has no schema stored anywhere to check against. It writes a column name
because that name usually follows in KQL, and whether it exists in that table never
gets looked up. A real column and an invented one look the same coming out, so you
cannot tell from the answer which one you got.

Microsoft security tables make this worse than most. Retired names sit in far more
training data than the names that replaced them, tables get renamed mid-year,
documentation lags the portal, and some preview tables ship with no published column
reference at all.

This skill stops the model answering until it has checked.

## Before you start

One thing is required: some way for the agent to read a web page, whether that is a
built-in fetch or browse tool or an MCP server. The skill is built around reading
Microsoft Learn, and where a host offers no lookup at all it says verification is not
possible and stops rather than falling back on what the model remembers. Two
connections make it considerably better:

| Connection | What it adds |
|---|---|
| **Microsoft Learn MCP** | Grounded documentation lookups instead of raw page fetches. |
| **KQL Search MCP** (`kqlsearch.com`) | The community query corpus, searchable by table, keyword or technique. This is what makes the prior-art step work. |

Without the Learn MCP, schema verification still works through ordinary page fetches.
Without a search capability the prior-art step is skipped altogether, and the answer
says so — queries then come from the verified schemas alone.

## How to use it

Just ask for what you need. The skill triggers on any KQL-shaped request, including
ones that never use the word:

- "Find local AI agents discovered by Defender, with their MCP servers"
- "Why is this query returning nothing?" (paste the query)
- "Write a Sentinel detection for agents authenticating from a new country"

What comes back is a query, the documentation pages that were checked with links, and
the assumptions being made — custom tables, connector coverage, licence gates,
ingestion lag. Where an identifier cannot be verified, you are told so instead of
being handed a query built on it.

## Good to know

**It is slower.** Every table the query needs gets fetched and every column checked, so
something that would have appeared instantly takes several tool calls. For quick
exploration that is a poor trade. For anything going into a workbook, a detection rule
or a customer report, it is the version worth trusting.

**A 404 is not a verdict.** Learn serves one for a slug it does not recognise as readily
as for a table that does not exist, so a 404 on its own — like a timeout or a 403 — means
the lookup failed, and the skill says so. What settles it is the index page: a schema
index that does not list your table is evidence, and then the name is wrong, the table is
custom, or it is in preview with nothing published yet. The skill says which the evidence
supports and asks, rather than reaching for a similar name.

**Snapshot tables catch people out.** `AgentsInfo` stores repeated snapshots, so
`summarize arg_max(Timestamp, *)` without `by AgentId` returns a single row — a whole
fleet reduced to one, in a query that runs perfectly. Grounding helps here because
Microsoft's own published sample queries use the correct form, and the prior-art step
finds them.

**Preview tables are the hard limit.** Where no column reference has been published,
nothing can be verified. The skill asks you for the schema — the portal's schema tab
or a `getschema` run — and stops if you do not have it. Ask and you can have a
`column_ifexists()` version, but it is a diagnostic, not a query to keep: a column
that is not there resolves silently to the default for every row, so a filter on it
matches nothing or everything and a `summarize` collapses into one bucket. It runs,
and what comes back is a false negative wearing the shape of a real result.

**Documentation is not your tenant.** Confirming a table exists says nothing about
whether it is populated for you. That is a licensing and connector question, and the
skill calls it out rather than implying coverage.
