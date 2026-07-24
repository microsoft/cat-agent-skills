---
name: sharepoint-list-insight-report-generator
description: Automatically discovers and validates a SharePoint list within a connected knowledge source, analyzes its structure and data, identifies key business insights, and generates a downloadable interactive HTML report. The report includes dynamic filters, interactive charts, sortable and searchable tables with pagination, detailed record drill-down through modal popups, and direct links to open items in SharePoint. If the requested list is not found, the skill suggests available lists and closest matches before stopping the analysis.
---
## Step 1 – Identify the Target List

1. Read the user request and identify the requested SharePoint list name.
2. Inspect the selected SharePoint knowledge source.
3. Retrieve all available SharePoint lists.
4. Perform a case-insensitive comparison.
5. Identify the best matching list.

### Validation Logic
Before performing any analysis, enumerate all SharePoint lists available in the selected knowledge source.

  The requested data source must be explicitly mapped to an existing SharePoint list.

  Allowed conditions to continue:
  - Exact list name match.
  - User explicitly selects a list from the available list.
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

###If the requested list does not exist:

- Stop the process immediately.
- Do not analyze data.
- Do not generate a report.
- Return all available SharePoint lists.
- Return closest matching list names.

Proceed only if the requested list exists.
For example if the user create a request for sales and the product list contains sales data stop the process. The user request must be related to existing knwoledge source.

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

Generate a single self-contained HTML5 report.

### Technologies

Use:

- HTML5
- Bootstrap 5
- DataTables
- Chart.js

Use only library that can be used safetly by brower.

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
- Use target="_blank"

---

## Step 6 – Save Report 

After generating the HTML report:

- Generate a unique name using:

   Report_<ListName>_<yyyyMMdd_HHmmss>.html

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
