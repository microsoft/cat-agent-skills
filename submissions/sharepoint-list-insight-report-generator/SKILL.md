---
name: sharepoint-list-insight-report-generator
description: Use this skill whenever the user asks for an insight report from a SharePoint list exposed by the configured SharePoint reporting tools. Before analysis, require deterministic list discovery, schema, paged item retrieval, and permission-safe report publishing capabilities; never treat a SharePoint knowledge source as write access.
---

Follow this procedure to create a downloadable, single-file HTML report from one
validated SharePoint list.

## 1. Verify the required tools

Before reading data, verify that the available tools provide all four
capabilities below. Tool names can differ, but their inputs and outputs must be
equivalent.

1. **List report sources**
   - Enumerates only the SharePoint sites and lists approved for this agent.
   - Returns stable `sourceId` and `listId` values, list title, site URL, list
     URL, item count, and a continuation token when more results exist.
2. **Get list schema**
   - Accepts only `sourceId` and `listId` values returned by list discovery.
   - Returns list metadata and visible columns, including display name, internal
     name, type, required/indexed state, and choice/lookup/person details where
     applicable.
3. **Get list items page**
   - Reads under the invoking user's effective permissions.
   - Accepts `sourceId`, `listId`, selected columns, an approved server-side
     filter, page size, and continuation token.
   - Returns stable item IDs, values, trusted item URLs, matching item count,
     retrieval time, `nextToken`, and the configured `maxRows` and
     `maxHtmlBytes` limits.
4. **Publish list report**
   - Is hard-bound to an approved SharePoint report destination; it must not
     accept an arbitrary site, library, or folder from the model.
   - Verifies that publishing cannot expose the report to a broader audience
     than the source data. A requester-only destination is the safe default.
   - Creates the HTML file and returns `status`, `fileName`, `webUrl`,
     `storagePath`, `permissionMode`, and explicit error details.

If any capability is missing, stop and name the missing capability. Do not use a
knowledge source as a substitute for deterministic enumeration, paged record
retrieval, permission validation, or file creation. Knowledge grounding may
help interpret business terminology, but all counts, records, URLs, and schema
facts in the report must come from the reporting tools.

## 2. Resolve the requested list

1. Extract the requested list title from the user's request.
2. Call **List report sources**, following continuation tokens until all
   approved lists have been returned.
3. Compare titles using a case-insensitive exact match.
4. Continue only when there is exactly one exact match or the user explicitly
   selects one of the returned lists.
5. If there is no exact match, stop and show the available titles. You may also
   show up to five closest title suggestions, but never select a suggestion on
   the user's behalf.
6. If more than one exact match exists on different sites, show the matching
   site and list URLs and ask the user to choose.

Use only the `sourceId`, `listId`, site URL, and list URL returned by discovery.
Never invent identifiers or turn a user-supplied arbitrary URL into a tool
target.

## 3. Discover schema and bound the scope

1. Call **Get list schema** for the selected identifiers.
2. Select only visible, business-relevant columns needed for the requested
   analysis. Exclude hidden/system fields and fields the user did not request.
   Never include credentials, secrets, tokens, or similarly sensitive values.
3. Use supported server-side filters for the requested date range, category,
   status, owner, or other scope. Keep the effective filter for the final
   report and publisher call.
4. Determine the matching item count before detailed analysis.
5. Use the tool's `maxRows`; if it does not return one, use a maximum of 1,000
   detailed records.
6. If the matching count exceeds that limit, stop before retrieving row data
   and ask the user to narrow the scope. Do not silently sample, truncate, or
   generate a report from the first page.

If the tool cannot provide a count up front, retrieve pages only until
`maxRows + 1` distinct IDs are observed. If the extra record exists, discard the
partial result and ask for a narrower filter.

## 4. Retrieve and analyze records

1. Request at most 200 records per page, or the lower limit returned by the
   tool.
2. Follow `nextToken` until it is empty. Reject repeated tokens, duplicate item
   IDs, or a page count inconsistent with the tool response; surface the error
   instead of claiming a complete result.
3. Record:
   - source list and site;
   - effective filter;
   - matching and retrieved counts;
   - selected fields;
   - retrieval timestamp;
   - any unsupported or omitted fields.
4. Calculate metrics only from the fully retrieved, in-scope records:
   - record count, distinct values, missing values, and completeness;
   - category frequencies when categorical fields exist;
   - ownership distribution when person fields exist;
   - time trends when a suitable date field exists;
   - numeric summaries when numeric fields exist;
   - exact duplicate and anomaly indicators whose rules can be explained.
5. Tie every insight to a visible metric. Do not invent trends, causes,
   benchmarks, or recommendations that the data does not support.

## 5. Build a hardened single-file report

Create one HTML file containing all CSS, JavaScript, and report data. Do not
load Chart.js, fonts, stylesheets, scripts, images, or any other dependency from
a CDN or remote host. Draw charts with embedded browser APIs such as SVG or
Canvas.

### Data minimization and safe rendering

- Embed only the selected report fields. Do not hide unused source fields in
  JavaScript or the DOM.
- Serialize data with a real JSON serializer. Before placing JSON inside a
  `<script>` element, escape `<`, `>`, `&`, U+2028, and U+2029 so values cannot
  terminate the element or create markup.
- Build data-driven UI with `document.createElement`, `textContent`, and safe
  property assignment. Never insert list titles, field names, values, insights,
  or URLs through `innerHTML`, `outerHTML`, `insertAdjacentHTML`,
  `document.write`, `eval`, or `new Function`.
- Include this restrictive baseline Content Security Policy in a meta tag:

  ```text
  default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'
  ```

- Treat every SharePoint value as untrusted text, including rich-text fields.
  Display rich text as plain text unless a separately configured sanitizer is
  available.

### Links

For an **Open SharePoint item** action:

1. Use only the item URL returned by the trusted read tool.
2. Parse it with the browser `URL` API.
3. Allow it only when the protocol is `https:`, it has no embedded username or
   password, and its origin exactly matches the trusted site URL's origin.
4. If validation fails, omit the link and record the omission in the report.
5. Open valid links with `target="_blank"` and
   `rel="noopener noreferrer"`.

Never use a URL stored in an arbitrary list column as an item link. Explicitly
reject `javascript:`, `data:`, `file:`, and all non-HTTPS schemes.

### Report contents

Include:

- an executive summary with list name, scope, retrieved count, selected column
  count, retrieval time, and key evidence-based insights;
- text, choice, lookup, person, and date filters when those field types exist;
- appropriate bar, line, pie, or doughnut visualizations;
- KPIs and charts that update when filters change;
- a searchable, sortable, paginated table;
- column visibility controls;
- a responsive modal showing all selected report fields for the chosen record;
- CSV and copy-to-clipboard exports for the filtered rows.

For CSV export, quote fields correctly and neutralize values whose first
non-whitespace/control character is `=`, `+`, `-`, or `@` by prefixing an
apostrophe before export. This prevents spreadsheet formula injection. Label
the download **CSV (Excel-compatible)**; do not claim to produce a native
`.xlsx` file.

## 6. Publish safely

1. Sanitize the list title to the allowlist `[A-Za-z0-9_-]`, replace other
   runs with `_`, trim separators, cap the sanitized portion at 80 characters,
   and use `SharePointList` if nothing remains.
2. Create a UTC timestamped filename:

   ```text
   Report_<SanitizedListName>_<yyyyMMdd_HHmmss>.html
   ```

3. Confirm the encoded HTML is no larger than `maxHtmlBytes`. If the limit is
   missing or exceeded, stop and report the size problem.
4. Before a shared-destination publication, tell the user the effective scope,
   record count, selected fields, and destination, then obtain explicit
   confirmation. A requester-only destination may proceed without a second
   confirmation when the original request explicitly asked to create and save
   the report.
5. Invoke **Publish list report** with the discovered source identifiers,
   effective filter, filename, and HTML content. Do not supply an arbitrary
   destination.
6. Treat publication as successful only when:
   - `status` is `succeeded`;
   - `permissionMode` is `requester-only` or `source-equivalent`;
   - `webUrl`, `fileName`, and `storagePath` are present; and
   - the returned URL passes the same HTTPS and trusted-host validation used
     for item links.

If permission equivalence cannot be established, an included item has narrower
unique permissions than the destination, or the publisher returns an unknown
permission mode, stop without creating or sharing the report. Surface the
publisher's explicit error code and message; never return a guessed URL.

## 7. Return the result

On success, return:

1. the validated SharePoint report URL;
2. the report filename and storage path;
3. the selected list and effective filter;
4. retrieved versus matching record counts and retrieval timestamp;
5. the selected schema summary;
6. the top evidence-based insights;
7. omitted fields, unavailable links, and other material limitations.

If the requested list is unresolved, the scope is over the limit, a required
tool is missing, paging is incomplete, HTML exceeds the configured limit, or
publication fails, return that stopped state plainly. Never present a partial
analysis or an uncreated file as a completed report.
