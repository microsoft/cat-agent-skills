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

## Guardrails

Live data only — never invented. No raw GUIDs, query syntax, or tool payloads
leak to the user. When nothing matches, it says so and suggests alternatives rather
than guessing.

## Requirements

Runs in **Copilot Studio** with the **Dataverse MCP Server** tool wired up.
