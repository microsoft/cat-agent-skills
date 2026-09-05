# Knowledge Source Router

Keep country-specific answers grounded in the documents that actually apply.
This skill uses a SharePoint library's `Country` metadata to choose the complete
document set before searching its contents.

## Why use it?

Policies, benefits, pricing, legal requirements, and product availability can
differ by country. A normal content search may blend documents from several
countries because the country is often stored in metadata rather than written
in the document itself.

The router reverses that order:

1. Discover the library's `Country` column and recorded values.
2. Select every document assigned to the requested country.
3. Search only those document URLs.
4. Read the full scoped set and cite the sources used.

It also reports unassigned files and relevant documents excluded by the
country filter, making the answer's boundaries explicit.

## An intentionally strict example

A capable agent may not need instructions this prescriptive to use metadata
filtering and knowledge search correctly. This skill deliberately demonstrates
a stricter flow so the sequence is explicit, repeatable, and easy to inspect.

Use it as both a working routing pattern and an example of how the two tools
complement each other: `sharepoint_metadata_filter` determines which documents
apply, and `knowledge_search_sharepoint` searches their contents through
`scopeUrls`. Adapt the level of instruction to the agent and scenario rather
than assuming every implementation needs every guardrail in this skill.

## Requirements

Use this skill with a Copilot Studio agent that has:

- A SharePoint document library with a populated `Country` metadata column.
- A `sharepoint_metadata_filter` tool that can discover columns, group values,
  filter rows, and return document URLs.
- A `knowledge_search_sharepoint` tool that accepts `scopeUrls`.
- File-type skills needed to open and preprocess the library's documents.

Country values should be consistent and meaningful to users. The skill follows
the values recorded in the library and does not infer assignments for blank
files.

## What changed in version 2

Version 2 replaces fixed source buckets with metadata-first routing. It now
derives the searchable document set from the library's `Country` column,
prevents unscoped searches, covers every matching file, and reports metadata
coverage and exclusions.
