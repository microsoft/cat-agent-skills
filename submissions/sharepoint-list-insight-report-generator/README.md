# SharePoint List Insight Report Generator

This Copilot Studio skill turns any validated SharePoint list into an interactive business intelligence report with automated schema discovery, data analysis, visual insights, and downloadable HTML reporting.

## Who it's for

Microsoft 365 users who need fast insights from SharePoint list data without building Power BI reports or performing manual analysis.

## What it does

The skill automatically:

* Validates that the requested SharePoint list exists in the selected knowledge source before any processing begins.
* Discovers list structure, metadata, field types, and schema details.
* Analyzes all accessible list records.
* Identifies business trends, data quality issues, ownership patterns, and anomalies.
* Generates actionable business insights and recommendations.
* Produces a fully interactive HTML report that can be stored in SharePoint and shared with stakeholders.

## Key capabilities

### Intelligent List Discovery

The skill:

* Enumerates all available SharePoint lists in the selected knowledge source.
* Performs case-insensitive matching.
* Validates list existence before analysis.
* Prevents incorrect list selection through semantic guessing.
* Suggests available lists and closest matches when a requested list cannot be found.

### Data Analysis

The skill evaluates:

#### General Statistics

* Total records
* Distinct values
* Missing values
* Completeness score

#### Trend Analysis

* Monthly trends
* Annual trends
* Growth patterns

#### Category Analysis

* Most common categories
* Frequency distribution
* Rankings

#### Ownership Analysis

* Records by contributor
* Top contributors
* Ownership distribution

#### Data Quality Analysis

* Missing information
* Duplicate records
* Suspected anomalies
* Data consistency issues

### Business Insights

The report highlights:

* High-value trends
* Frequently used categories
* Fast-growing areas
* Potential process bottlenecks
* Data quality concerns
* Recommended corrective actions

Insights are prioritized based on business relevance and actionability.

## Interactive HTML Report

The generated report is a self-contained HTML5 application built using browser-safe technologies:

* HTML5
* Bootstrap 5
* DataTables
* Chart.js

### Executive Dashboard

Displays:

* List name
* Record count
* Column count
* Last update date
* Top insights
* Key performance indicators

### Dynamic Filters

Supports filtering on:

* Text fields
* Choice fields
* Lookup fields
* Person fields
* Date fields

All filters dynamically update charts, KPIs, and data tables.

### Interactive Charts

Automatically generates the most appropriate visualizations:

* Bar charts
* Pie charts
* Doughnut charts
* Line charts

Features include:

* Hover tooltips
* Interactive legends
* Dynamic filtering

### Advanced Data Table

Provides:

* Sorting on every column
* Ascending and descending sorting
* Global search
* Pagination
* Column visibility controls
* Export options

Export formats:

* CSV
* Excel
* Copy to clipboard

### Record Detail View

Selecting a row opens a responsive detail modal showing:

* All field display names
* Internal field names
* Current values
* Complete record details

## Report Output

Generated reports follow the naming convention:

```text
Report_<ListName>_<yyyyMMdd_HHmmss>.html
```

## How to Use

* Create new Copilot Studio agent using new UI.
* Add skill and knowledge source to your agent.

<img width="522" height="709" alt="image" src="https://github.com/user-attachments/assets/e083b4fc-11b5-4b74-8376-5d38996a2c94" />

* Use simple instructions like
```text
Using sharepoint-list-insight-report-generator, create an HTML report based on the selected SharePoint knowledge source.​
```
