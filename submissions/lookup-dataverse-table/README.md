# Dataverse Table Lookup

A Copilot Studio skill that searches any Microsoft Dataverse table, browses
matching records, and drills into full record details — all sourced **live** via
the Dataverse MCP Server.

## Genesis

A conversational agent is great at exchanging information, but when a choice must be
specific and exact, the user needs an authoritative list of options to select from.
That list has to come from the system of record.

This skill wraps a disciplined, schema-aware lookup workflow around the Dataverse
MCP Server so the agent provides simple and dependable lookups: identify the
table, discover its schema (primary name + key fields), query for matches, then
drill into a selected record. GUIDs and internal identifiers stay hidden, results
are capped, and the agent prompts you to narrow the search rather than paging
silently. It also remembers your preferred field set across conversations.

## What it does

- **Search** any Dataverse table by name, keyword, status, date range, or related
  record.
- **Browse** matches as a clean numbered list (or a table with a leading number
  column) showing record name + key identifier.
- **Drill in** to a selected record's most useful fields, omitting empties.
- **Remembers** preferred fields so detail views match how you like to work.

## Why a numbered list?

The numbered-list pattern isn't just a stylistic choice — it's a deliberate design
decision. In **the new Copilot Studio experience**, the richer UI affordances often used in classic/standard agents are not available:

- **Suggested actions** are not supported.
- **Adaptive cards** are not supported.
- **Custom entities** are not supported.

Given those constraints, a plain numbered list is a simple and effective way to
present options to the user: it renders reliably as text, needs no special UI
components, and lets the user pick an option quickly by replying with a number.

## Guardrails

Live data only — never invented. No raw GUIDs, query syntax, or tool payloads
leak to the user. When nothing matches, it says so and suggests alternatives rather
than guessing.

## Requirements

Runs in **Copilot Studio** with the **Dataverse MCP Server** tool wired up.
