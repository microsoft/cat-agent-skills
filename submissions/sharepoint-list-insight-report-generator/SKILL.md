---
name: sharepoint-list-insight-report-generator
description: Use this skill whenever the user asks for an insights/reporting analysis of a SharePoint list from a connected SharePoint knowledge source; first validate the list exists, then generate and save a self-contained interactive HTML report to the site’s Documents library and return its SharePoint URL.
---
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

Analyze all accessible records.

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

Produce a single, completely self-contained HTML file with all CSS and JavaScript embedded inline. Chart.js (version 4) may be loaded from a CDN and is the only permitted external dependency. Do not use external Bootstrap, DataTables, fonts, stylesheets, scripts, or other CDN resources. Implement table filtering, sorting, pagination, and responsive styling using embedded CSS and JavaScript.

### Technologies

Use:
- Chart.js

Use only libraries that can be used safely by browser.

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
  - CSV
  - Excel
  - Copy

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
- Use SharePoint item URL when available
- Use target="_blank" and rel="noopener noreferrer"
---

## Step 6 – Save Report 

After generating the HTML report:

- Generate a unique name using a sanitized list name (replace spaces with `_` and remove/replace characters SharePoint disallows in filenames).

   Report_<SanitizedListName>_<yyyyMMdd_HHmmss>.html

---

## Output Requirements

Return:

1. Report summary.
2. SharePoint URL of the generated report.
3. Report file name.
4. List schema summary.
5. Insights summary.
6. Storage location within the SharePoint Documents library.

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
- Save the report in the Documents library of the SharePoint site associated with the selected knowledge source.
- Return the direct SharePoint URL of the report.
- Provide sortable tables.
- Provide pagination.
- Provide quick search.
- Provide modal detail view.
- Provide Open SharePoint Item action.
- Generate a unique report name.
- Support responsive user experience.
