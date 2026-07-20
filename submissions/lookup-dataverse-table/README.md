# Dataverse Table Lookup

A Copilot Studio skill that searches any Microsoft Dataverse table, browses
matching records, and drills into full record details — all sourced **live** via
the Dataverse MCP Server.

## Genesis

Agents are prone to *hallucinating* business data: asked about a CRM record, an LLM
will happily invent a plausible-looking account or contact. For Dataverse-backed
scenarios that's unacceptable — the answer has to come from the system of record.

This skill wraps a disciplined, schema-aware lookup workflow around the Dataverse
MCP Server so the agent always queries live and never fabricates: identify the
table, discover its schema (primary name + key fields), query for matches, then
drill into a selected record. GUIDs and internal identifiers stay hidden, results
are capped and paginated by prompting, and the agent remembers the user's preferred
field set across conversations.

## What it does

- **Search** any Dataverse table by name, keyword, status, date range, or related
  record.
- **Browse** matches as a clean numbered list / two-column table (record name + key
  identifier).
- **Drill in** to a selected record's most useful fields, omitting empties.
- **Remembers** preferred fields so detail views match how you like to work.

## Why a numbered list?

The numbered-list pattern isn't just a stylistic choice — it's a deliberate design
decision that came out of discussions in Teams with Adi Leibowitz and others. In
**enhanced orchestrator agents**, the richer UI affordances you might reach for
simply aren't available:

- **Suggested actions** are not supported.
- **Adaptive cards** are not supported.
- **Custom entities** are not supported — so backing the experience with a standard
  **Dataverse table** is a great way to get structured, queryable data instead.

Given those constraints, a plain numbered list is a simple and effective way to
present options to the user: it renders reliably as text, needs no special UI
components, and lets the user pick an option quickly just by replying with a number.
It turns a lookup-and-select interaction into something that works well within the
capabilities the enhanced orchestrator actually offers.

## Guardrails

Live data only — never invented. No raw GUIDs, query syntax, or tool payloads
leak to the user. When nothing matches, it says so and suggests alternatives rather
than guessing.

## Requirements

Runs in **Copilot Studio** with the **Dataverse MCP Server** tool wired up.
