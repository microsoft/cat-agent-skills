# SharePoint List Insight Report Generator

Create a permission-safe, downloadable HTML insight report from a validated
SharePoint list. The report combines bounded data analysis, interactive charts,
filters, a searchable table, and record drill-down in one offline-capable file.

## What it does

- Selects a list only by exact title or explicit user choice.
- Reads schema and records through deterministic SharePoint tools.
- Pages through a bounded result set instead of silently truncating large lists.
- Produces evidence-based statistics, trends, quality indicators, and insights.
- Builds a dependency-free HTML report with hardened data and link handling.
- Publishes only through a tool that verifies the report will not broaden access
  to the source data.

## Required setup

This skill is not zero-configuration. A SharePoint knowledge source provides
grounding and analytical question answering, but it does not provide
deterministic schema enumeration or permission to upload a file. Configure the
knowledge source and the four tools below before installing the skill.

Microsoft references:

- [Add SharePoint as a knowledge source](https://learn.microsoft.com/en-us/microsoft-copilot-studio/knowledge-add-sharepoint)
- [Use connectors in Copilot Studio agents](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-connectors)

The tools can be connector actions, agent flows, or custom connector operations.
Their names are flexible, but their descriptions and contracts must make these
capabilities unambiguous to the agent.

| Capability | Required contract |
| --- | --- |
| **List report sources** | Enumerate only approved sites/lists. Return paged `lists[]` entries containing `sourceId`, `listId`, `title`, `siteUrl`, `listWebUrl`, and `itemCount`, plus `nextToken`. Do not accept an arbitrary site URL from the agent. |
| **Get list schema** | Accept a discovered `sourceId` and `listId`. Return list metadata and visible columns with display/internal names, types, required/indexed flags, and choice, lookup, or person details. |
| **Get list items page** | Accept discovered IDs, selected columns, a supported server-side filter, `pageSize`, and `continuationToken`. Read with the invoking user's effective permissions. Return stable item IDs, values, trusted item URLs, `matchingCount`, `retrievedAt`, `nextToken`, `maxRows`, and `maxHtmlBytes`. |
| **Publish list report** | Accept discovered source IDs, the effective filter, `fileName`, and `htmlContent`. Write only to a server-configured destination, validate its audience, create the file, and return `status`, `fileName`, `webUrl`, `storagePath`, `permissionMode`, `errorCode`, and `errorMessage`. |

The default detailed-report limit is 1,000 matching records when the reader
does not supply a lower `maxRows`. Set a conservative `maxHtmlBytes` that fits
your Copilot Studio, flow, connector, and SharePoint limits. The skill asks the
user to narrow the filter rather than silently sample data above the limit.

## Configure publishing permissions

Do not expose a generic SharePoint **Create file** action that lets the model
choose any destination. Wrap it in an agent flow or custom operation that is
hard-bound to an approved reports library and implements one of these modes:

1. **Requester-only (recommended):** create or reuse a folder whose inheritance
   is broken, grant access only to the authenticated requester and required
   administrators, re-read the effective permissions, and upload only after
   verification.
2. **Source-equivalent:** verify that the destination's effective principals are
   a subset of the source list's principals and that no included item has
   narrower unique permissions. Refuse the upload if either condition is
   unknown or false.

Return `permissionMode: requester-only` or
`permissionMode: source-equivalent` only after the verification succeeds.
Return a failed status and explicit error when it does not. Use delegated
end-user authentication for reads where possible; a maker-owned connection
must never expose records the invoking user cannot access.

## Report security

The runtime instructions require the generated report to:

- use no CDN or remote runtime dependencies;
- insert SharePoint content as text rather than HTML;
- safely serialize embedded JSON;
- enforce a restrictive Content Security Policy;
- allow only HTTPS item links on the trusted SharePoint origin;
- neutralize spreadsheet formulas in CSV exports; and
- embed only the selected report fields.

Keep these requirements intact if you customize the report design. SharePoint
may download `.html` files instead of rendering them in the site; the downloaded
file remains interactive when opened in a browser.

## Use

After adding the knowledge source, tools, and skill, ask the agent:

```text
Create an insight report for the Campaign SharePoint list.
```

If several sites contain that exact title, the agent asks you to choose. If the
scope exceeds the configured record limit, it asks for a date, category, status,
owner, or other supported filter before retrieving row-level data.

On success, the response includes the validated SharePoint download URL,
filename, storage path, analyzed scope and counts, schema summary, top insights,
and any material limitations.
