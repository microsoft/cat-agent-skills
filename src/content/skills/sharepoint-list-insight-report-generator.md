---
name: SharePoint List Insight Report Generator
description: "Automatically discovers and validates a SharePoint list within a connected knowledge source, analyzes its structure and data, identifies key business insights, and generates a downloadable interactive HTML report. The report includes dynamic filters, interactive charts, sortable and searchable tables with pagination, detailed record drill-down through modal popups, and direct links to open items in SharePoint. If the requested list is not found, the skill suggests available lists and closest matches before stopping the analysis."
agentDescription: "Use this skill whenever the user asks for an insights/reporting analysis of a SharePoint list from a connected SharePoint knowledge source; first validate the list exists, then generate and save a single-file interactive HTML report to a pre-approved SharePoint destination whose audience is no broader than the source list and items, and return its SharePoint URL."
platforms: [Copilot Studio]
tags: [sharepoint, microsoft-365, lists, report, html]
author: Marco Rocca
authorUrl: "https://www.linkedin.com/in/marco-rocca"
authorGithub: marcorocca1973
version: 1.0.0
createdAt: 2026-07-24
updatedAt: 2026-07-24
---
Before starting, verify that configured SharePoint connector actions, agent flows, or equivalent tools can discover approved lists and their schemas, retrieve list items page by page, and invoke **Create file** to return the created file's URL or path. A SharePoint knowledge source alone does not guarantee these capabilities. If any capability is unavailable, stop and name the missing capability.

## Step 1 – Identify the Target List

1. Read the user request and identify the requested SharePoint list name.
2. Inspect the selected SharePoint knowledge source.
3. Retrieve all available SharePoint lists.
4. Perform a case-insensitive exact match on list title (and any explicit aliases in list metadata).
5. Proceed only on an exact match or an explicit user selection; otherwise stop and prompt the user to choose from the available lists.

### Validation Logic
Before performing any analysis, enumerate all SharePoint lists available in the selected knowledge source.

  The requested data source must be explicitly mapped to an existing SharePoint list.

  Allowed conditions to continue:
  - Exact list name match.
  - User explicitly selects a list from the available lists.
  - Alias defined in list metadata.

  Forbidden behavior:
  - Do not infer lists from business terminology.
  - Do not infer lists from column names.
  - Do not infer lists from data values.
  - Do not infer lists from semantic similarity.
  - Do not select a list because it appears related.

  Examples:

  User request:
  Create a report for Campaign

  Available lists:
  - Campaign
  - Product Catalog

  Result:
  Proceed with Campaign.

  User request:
  Create a report for sales data

  Available lists:
  - Campaign
  - Product Catalog

  Result:
  Stop.
  Return available lists.
  Ask the user to select one.

  User request:
  Create a report for quarterly revenue

  Available lists:
  - Campaign
  - Product Catalog

  Result:
  Stop.
  Do not select Campaign.

### If the requested list does not exist:

- Stop the process immediately.
- Do not analyze data.
- Do not generate a report.
- Return all available SharePoint lists.
- Return closest matching list names.

Proceed only if the requested list exists.
For example: if the user requests "sales" and only a "Product" list exists that happens to contain sales-related data, stop and ask the user to choose an existing list from the knowledge source.

---

## Step 2 – Discover List Structure

Retrieve:

- List title
- Internal name
- Item count
- Created date
- Last modified date
- All columns
- Column types
- Required fields
- Indexed fields
- Lookup fields
- Choice fields
- Person fields
- Managed metadata fields

Generate a schema summary.

---

## Step 3 – Analyze Data

Analyze all accessible records within the confirmed scope, retrieving them page by page through the configured tool and following its continuation tokens. Before retrieving a detailed report, enforce the tool's row and report-size limits; when either limit is absent, also use a conservative cap of 1,000 rows. If the scope would exceed an applicable limit, ask the user to narrow it. Never silently truncate or sample records.

Generate:

### General Statistics

- Total records
- Distinct values
- Missing values
- Data completeness score

### Trend Analysis

- Monthly trends
- Annual trends
- Growth trends

### Category Analysis

- Top categories
- Frequency distribution
- Ranking statistics

### Ownership Analysis

- Records by owner
- Top contributors

### Quality Analysis

- Empty fields
- Duplicate values
- Potential anomalies

---

## Step 4 – Generate Insights

Create business-oriented insights.

Examples:

- Most used categories
- Fastest growing areas
- Data quality issues
- Process bottlenecks
- Trends and anomalies

Prioritize actionable recommendations.

---

## Step 5 – Build Interactive HTML Report

Produce a single HTML file with all CSS and JavaScript embedded inline, except that Chart.js (version 4) may be loaded from an exact versioned CDN URL with matching SRI `integrity` metadata and `crossorigin="anonymous"` as the only permitted external dependency. If the exact version and matching SRI cannot be verified, do not load the CDN asset and use embedded browser APIs instead. Do not use external Bootstrap, DataTables, fonts, stylesheets, scripts, or other CDN resources. Implement table filtering, sorting, pagination, and responsive styling using embedded CSS and JavaScript.

Treat SharePoint field names and values as untrusted data. Use a real JSON serializer; before embedding serialized data in a `<script type="application/json">` element, escape `<`, `>`, `&`, U+2028, and U+2029, then read it via `textContent` and parse it. Insert data-driven content using `textContent`, `document.createElement`, and other safe DOM APIs, never `innerHTML`. Render rich-text fields as plain text unless a trusted sanitizer is available.

### Technologies

Use:
- Chart.js

Use only libraries that can be used safely in a browser.

### Executive Summary

Display:

- List name
- Record count
- Column count
- Last update date
- Top insights

### Interactive Filters

Provide filters for:

- Text fields
- Choice fields
- Lookup fields
- Person fields
- Date fields

Filters must update charts, KPIs and tables dynamically.

### Interactive Charts

Generate appropriate charts automatically.

Support:

- Bar charts
- Pie charts
- Doughnut charts
- Line charts

Provide hover tooltips and legend controls.

### Data Table

Requirements:

- Sort on every column
- Ascending and descending sorting
- Search box with placeholder:
  Quick search in table...
- Pagination
- Column visibility controls
- Export buttons:
  - CSV (Excel-compatible)
  - Copy

For CSV export, neutralize spreadsheet formulas by prefixing an apostrophe when a cell's first non-whitespace or control character is `=`, `+`, `-`, or `@`.

### Detail Modal Popup

Selecting a row must open a modal displaying:

- All list fields
- Display names
- Internal names
- Values

Use a responsive two-column layout.

### Open SharePoint Item Button

Inside the modal popup provide:

Open SharePoint Item

Requirements:

- Open in a new browser tab
- Use only the trusted SharePoint item URL returned by the configured connector or tool
- Permit the link only when it uses HTTPS and its origin matches the selected SharePoint site's origin; otherwise omit it
- Use target="_blank" and rel="noopener noreferrer"
---

## Step 6 – Save Report

After generating the HTML report:

- Generate a unique name using a sanitized list name: retain `[A-Za-z0-9_-]`, replace other runs with `_`, trim leading and trailing separators, cap the sanitized list-name portion at 80 characters, and use `SharePointList` if empty.

   Report_<SanitizedListName>_<yyyyMMdd_HHmmss>.html

- Verify that the configured destination's audience is no broader than the source list and included items. If this cannot be verified, do not upload the report.
- Invoke the configured SharePoint **Create file** action or flow to save the report in the pre-approved SharePoint destination whose audience is no broader than the source list and included items.
- Capture the URL or path returned by **Create file** and use it in the response. If file creation fails or returns no URL or path, report the failure honestly and never guess a URL.

---

## Output Requirements

Return:

1. Report summary.
2. SharePoint URL of the generated report.
3. Report file name.
4. List schema summary.
5. Insights summary.
6. Storage location within the configured SharePoint destination.

---

## Success Criteria

A successful execution must:

- Detect the requested SharePoint list.
- Validate its existence.
- Suggest available lists when not found.
- Discover schema.
- Analyze data.
- Generate insights.
- Create an interactive HTML report.
- Save the report in the pre-approved SharePoint destination whose audience is no broader than the source list and included items.
- Return the direct SharePoint URL of the report.
- Provide sortable tables.
- Provide pagination.
- Provide quick search.
- Provide modal detail view.
- Provide Open SharePoint Item action.
- Generate a unique report name.
- Support responsive user experience.
