---
name: Knowledge Source Router
description: "Route country-specific SharePoint questions through Country metadata first, then search only the complete set of matching documents."
agentDescription: "Required whenever a knowledge request names or implies a country, asks what applies \"here,\" or compares countries. Treat Country as document metadata, not as a content-search term. Before any content search, general-knowledge answer, or clarification, use sharepoint_metadata_filter to discover and filter the Country column. Then pass every matching document URL to knowledge_search_sharepoint through scopeUrls."
platforms: [Copilot Studio]
tags: [knowledge, routing, sharepoint, metadata, grounding]
author: Adi Leibowitz
authorUrl: "https://microsoft.github.io/mcscatblog/"
authorGithub: adilei
version: 2.0.0
createdAt: 2026-06-23
updatedAt: 2026-09-01
featured: true
---
# Knowledge Source Router

Route country-specific questions through SharePoint metadata before searching
document content. A country identifies which documents apply; it is not a
keyword to search for inside those documents.

Follow this workflow in order. The content search depends on URLs returned by
the metadata filter, so it cannot run in parallel with metadata discovery.

## 1. Discover the Country metadata

Start with a broad metadata call:

```text
sharepoint_metadata_filter(includeColumns: ["*"])
```

Read `availableColumns` as the authoritative list of library metadata.

- If `Country` exists, use that exact column name and its recorded values.
- If `Country` is absent, state that the library does not track Country and stop.
- If the request does not identify a specific country, inspect the available
  Country values before asking the user to choose one.

Do not infer a file's country from its title, folder, contents, or general
knowledge.

## 2. Establish the complete country set

First inspect the whole library:

```text
sharepoint_metadata_filter(groupByColumn: "Country")
```

Use the returned `groups`, `totalMatched`, and `blankCount` directly. The
expected relationship is:

```text
sum(groups) + blankCount == totalMatched
```

Do not pre-filter this call with `keyword`. A keyword would reveal only files
about that term, not every file assigned to the country.

Then enumerate all files for the requested country:

```text
sharepoint_metadata_filter(
  columnFilter: { column: "Country", operator: "eq", value: "<recorded value>" },
  includeColumns: ["*"]
)
```

For a comparison, retrieve the countries together:

```text
sharepoint_metadata_filter(
  columnFilter: {
    column: "Country",
    operator: "in",
    values: ["<recorded value 1>", "<recorded value 2>"]
  },
  includeColumns: ["*"]
)
```

Match the library's recorded values rather than silently normalizing,
expanding, or substituting them. Include every returned file, including
underscore-prefixed files and index files.

The grouping and enumeration calls may run in parallel after `Country` has
been discovered because neither depends on the other's output.

## 3. Search only the matching documents

Collect the `url` from every file returned by the country filter, then call:

```text
knowledge_search_sharepoint(
  search_query: "<the user's question in natural language>",
  scopeUrls: ["<url 1>", "<url 2>", "..."]
)
```

Never omit `scopeUrls` for a country-specific request. Do not start this call
until the country filter has returned the complete URL set; otherwise the
search can mix content from other countries or unassigned files into the
answer.

If no files match the requested country, report that result instead of running
an unscoped search.

## 4. Read the complete scoped set

A country may map to several documents, and the obvious filename may not hold
the complete answer. For every scoped URL:

1. Open the file.
2. Use the appropriate file-type skill to preprocess it.
3. Read it in full.

Answer from the union of the relevant content, and state which documents were
read. Do not stop after the first apparently complete file.

## 5. Report boundaries without filling gaps

Include the scope boundaries that help the user interpret the answer:

- Report `groups`, `totalMatched`, and `blankCount` from the metadata response
  when describing library coverage.
- Note relevant-looking documents excluded because they carry a different
  Country value.
- Describe an empty Country value as blank or unassigned. Never backfill it
  from the file's title, folder, contents, or the active filter.

## 6. Cite the documents used

Cite the `ReferenceId` for every document that contributes to the answer, such
as `[doc:turn1doc1]`. Cite only documents actually used. Never expose a SAS
token or signed query string from a document URL.

## Guardrails

| Avoid | Why |
| --- | --- |
| Searching document content for a country name | Prose mentions do not establish applicability, and tagged files may never name the country. |
| Running metadata discovery and content search together | The scoped URL set does not exist until metadata filtering completes. |
| Using `keyword` to establish country membership | It silently omits matching documents that do not contain the keyword. |
| Reading only the name-matching file | Other files assigned to the same country may contain required terms or exceptions. |
| Counting displayed rows | `totalMatched`, `groups`, and `blankCount` are the authoritative counts. |
| Assigning blank metadata from context | An inference is not a recorded Country value. |

## Example

For "What employee benefits apply in the United States?":

1. Discover `Country` with
   `sharepoint_metadata_filter(includeColumns: ["*"])`.
2. Group by `Country` and filter using the library's exact value for the United
   States.
3. Collect every returned URL.
4. Search with the original question and all URLs in `scopeUrls`.
5. Read every scoped document and answer from their combined content.
6. Report excluded Country values and unassigned files, then cite each source
   used.
