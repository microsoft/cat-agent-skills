---
name: lookup-dataverse-table
description: >-
  Use this skill whenever the user wants to search, browse, or look up records
  in a Microsoft Dataverse table — for example "look up accounts", "find
  opportunities for Contoso", "show me contact details", or "search cases by
  status". Always prefer this skill (which queries Dataverse live via the
  Dataverse MCP Server) BEFORE answering any question about Dataverse records.
---

Help the user search any Microsoft Dataverse table, browse matching records, and
view full record details — all sourced live from Dataverse via the Dataverse MCP
Server tool.

## Data source (critical)

- Always source data **dynamically** from Microsoft Dataverse using the Dataverse
  MCP Server tool.
- **NEVER** fabricate, invent, hardcode, guess, or reuse records from examples or
  prior general knowledge. Every record and every field value you show must come
  from a live query via the tool.
- If the tool returns no results or fails, say so plainly and ask the user to try
  again or refine their search. Do not make up data.

## Workflow

### Step 1 — Identify the table

- If the user names a table (e.g. "accounts", "opportunities", "contacts"), use
  that table.
- If the user is ambiguous, ask: *"Which table would you like to search? For
  example: contacts, accounts, opportunities, leads, etc."*
- Use the `search` or `describe('tables/')` tool to resolve the table's logical
  name if needed.

### Step 2 — Discover the schema

Before querying, call `describe('tables/{tablename}')` to retrieve:

- The table's **primary name field** (used for display).
- The table's **primary key field** (used internally for record lookup).
- Available columns and their logical names and types.

Store the primary key GUID **internally** — never display it to the user.

### Step 3 — Find records

1. Query the table using `read_query`, always retrieving at least:
   - The **primary name field**
   - A **key identifier field** (e.g. email, account number, status)
   - The **primary key** (for internal use only)
2. Apply any search filters the user provides (name, keyword, status, date range,
   related record, etc.).
3. Return **at most 15 rows**. If more than 15 records match, show the first 15
   and prompt the user to narrow the search.
4. If a field has no value, show `(none)`.

Present results as a numbered markdown list or a three-column table:

| # | Record Name | Key Identifier |
|---|-------------|----------------|
| 1 | Example Corp | account@example.com |
| 2 | Another Record | 555-0100 |
### Step 4 — Select a record

When the user selects a record (by number, name, or identifier):

1. Re-query the Dataverse table using the internally stored primary key GUID.
2. Display the most useful ~20 fields for that record, presented as a readable
   labeled list or table.
3. Omit empty/null fields unless the user requests the full record.
4. Never reveal GUIDs or internal identifiers.

Example detail view:

| Field | Value |
|-------|-------|
| **Name** | Example Corp |
| **Email** | account@example.com |
| **Phone** | 555-0100 |
| **City** | Seattle |
| **State** | WA |

## Remembering preferred fields

- If the user requests a different set of fields (add, remove, or replace),
  **remember those preferences** using memory tools.
- Default to the user's preferred field set on all subsequent detail lookups — in
  this and future conversations — until the user changes it again.

## Supported tables

The skill works with **any** Dataverse table. Common examples:

| Table display name | Logical name |
|--------------------|--------------|
| Contacts | contact |
| Accounts | account |
| Opportunities | opportunity |
| Leads | lead |
| Cases | incident |
| Products | product |
| Orders | salesorder |
| Invoices | invoice |
| Activities | activitypointer |
| Users | systemuser |

Use `describe('tables/')` to discover all available tables in the environment.

## Guardrails

- Present matching records as a numbered markdown list or a two-column table
  (Record Name / Key Identifier).
- Do **not** expose raw GUIDs, internal IDs, query syntax, or raw tool payloads
  to the user.
- Do **not** emit adaptive card or suggested-action code blocks.
- When a search yields no results, say so clearly and suggest alternative search
  terms.
- When a table is not found, suggest similar table names or ask the user to
  clarify.
- When more than 15 records match, always prompt the user to refine the search
  rather than paginating silently.

## Tone

Be concise and helpful. Explain uncertainty rather than hiding it, and never
present fabricated data as if it came from Dataverse.
