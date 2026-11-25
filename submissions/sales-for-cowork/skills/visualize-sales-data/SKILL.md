---
name: visualize-sales-data
description: turn sales, customer, usage, value, pipeline, and financial data from crm systems, excel workbooks, and other connected sources into one or more executive-ready powerpoint slides. use to visualize data, create charts or scorecards, add data-driven insights to a deck, update existing slides with current metrics, compare customers or periods, explain business performance, or build an executive sales narrative from quantitative data.
metadata:
  displayname: "Visualize Sales Data"
  domain: Sales
---

# Visualize Sales Data

Transform sales data into clear, decision-oriented PowerPoint slides containing charts, scorecards, executive insights, and recommended actions.

## Core principles

- Start with the business question, audience, and decision the slides must support.
- Use the most authoritative available data source.
- Preserve source definitions, filters, units, currencies, and reporting periods.
- Select visuals based on the analytical question, not visual novelty.
- Communicate the conclusion in the slide title.
- Distinguish observed facts from calculated metrics and interpretations.
- Keep slides concise enough for an executive audience.
- Never invent, estimate, or silently fill missing data.
- Preserve the presentation’s existing brand, theme, layouts, and terminology when editing a deck.

## Expected inputs

Accept one or more of the following:

- CRM data, such as accounts, opportunities, pipeline, stages, products, activities, forecasts, and close dates
- Excel workbooks containing customer, product, usage, value, revenue, cost, or forecast data
- Other connected data, reports, dashboards, or semantic models
- Tables or data included directly in the conversation
- An existing PowerPoint deck to update
- Instructions describing the audience, business question, customer, account, sales motion, or reporting period

If the request does not specify the audience, optimize for a sales leader or customer executive.

## Workflow

### 1. Define the analytical objective

Identify:

- The audience
- The decision or discussion the slides should support
- The relevant customer, account, opportunity, territory, product, or business unit
- The reporting period and comparison period
- Whether the presentation is internal, customer-facing, or partner-facing

Infer these details from the request and available deck when reasonably clear. Ask a question only when a missing detail would materially change the analysis or could produce a misleading slide.

### 2. Retrieve and inspect the data

Use the requested CRM, Excel, or other data source when available.

For each source:

- Identify the source name and refresh or extraction date
- Inspect field names, units, currencies, date ranges, and filters
- Determine the data grain, such as account, user, opportunity, month, product, or region
- Check for totals, subtotals, duplicates, nulls, outliers, and incompatible definitions
- Confirm whether monetary values are actual, forecast, pipeline, annualized, or cumulative
- Confirm whether usage metrics represent licensed users, eligible users, active users, actions, sessions, or another measure

When multiple sources conflict, prefer the source explicitly designated as authoritative. Otherwise, surface the discrepancy rather than silently reconciling it.

### 3. Prepare the analysis

Perform only transformations necessary to answer the business question.

Common calculations include:

- Period-over-period growth
- Actual versus target
- Forecast versus plan
- Pipeline coverage
- Conversion rate
- Win rate
- Average deal size
- Sales-cycle duration
- Product or workload mix
- Customer adoption rate
- Active-user penetration
- Utilization or consumption trend
- Value realized
- Remaining value opportunity
- Revenue, cost, margin, or return on investment
- Account or opportunity health scores

Document non-obvious calculations in speaker notes.

Do not present calculated metrics without enough underlying data to support them.

### 4. Select the visual format

Choose the simplest visual that communicates the conclusion.

Use:

- **Line chart** for trends over time
- **Column or bar chart** for comparisons across customers, products, regions, or periods
- **Stacked bar or column chart** for mix and composition
- **Waterfall chart** for changes between starting and ending values
- **Scatter or bubble chart** for relationships, segmentation, and account prioritization
- **Funnel chart** for sequential sales stages when the stages and populations are comparable
- **Scorecard** for a small set of headline metrics
- **Heat map** for comparative performance across two dimensions
- **Table** when exact values, status, and multiple attributes are more important than patterns
- **Combination chart** only when two related measures require different scales
- **Executive insight panel** for conclusions, implications, risks, and recommended actions

Avoid pie or doughnut charts when there are more than five categories or when small differences need to be compared.

Avoid three-dimensional charts, decorative gauges, excessive icons, and visuals that distort proportions.

### 5. Design the slide story

Create only the number of slides necessary to tell the story.

A useful multi-slide sequence is:

1. **Executive summary**  
   Show the most important metrics, conclusion, and recommended action.

2. **Performance or usage trend**  
   Explain what changed, when it changed, and how it compares with the target or prior period.

3. **Drivers and segmentation**  
   Identify the customers, products, regions, workloads, or opportunities driving the result.

4. **Value or financial impact**  
   Connect usage or sales activity to revenue, cost, savings, margin, or realized value.

5. **Risks and next actions**  
   Highlight gaps, dependencies, owners, and recommended follow-up.

Do not create every slide in this sequence unless the available data and request justify it.

### 6. Write executive insights

Use conclusion-led slide titles that communicate the primary finding.

Prefer:

- “Enterprise usage grew 18%, led by three strategic accounts”
- “Pipeline coverage is below target in two priority regions”
- “Adoption is increasing, but realized value remains concentrated”
- “Expansion opportunity is highest among licensed but inactive users”

Avoid:

- “Usage Analysis”
- “Pipeline Chart”
- “Customer Data”
- “Financial Overview”

For each slide, include up to three concise insights:

- **What happened**
- **Why it matters**
- **What should happen next**

Base insights on visible data. Label interpretations and recommendations appropriately.

### 7. Create or update the PowerPoint slides

When an existing presentation is provided:

- Apply the already used presentation brand kit or preserve the presentation theme, fonts, colors, and layout conventions
- Reuse existing chart and scorecard styles when suitable
- Place new slides in the position implied by the presentation narrative
- Update existing slides rather than duplicating them when the request is a data refresh
- Avoid altering unrelated content

When creating new slides:

- Use a clear information hierarchy
- Use consistent scales, units, colors, and number formats
- Label axes and series directly when practical
- Emphasize the most important value or series
- Keep supporting detail subordinate to the main conclusion
- Use whitespace to separate the chart, metrics, and insights
- Ensure text remains readable in presentation mode

Use semantic colors consistently:

- Neutral colors for context
- Accent colors for the central series or finding
- Green for favorable performance only when the meaning is unambiguous
- Red for risks or unfavorable performance only when the meaning is unambiguous
- Gray for prior periods, benchmarks, or secondary information

### 8. Add source and methodology notes

Add a concise source note to each data-driven slide or its speaker notes.

Include, when available:

- Data source
- Report, workbook, table, dashboard, or CRM object
- Reporting period
- Refresh or extraction date
- Material filters
- Currency and units
- Definition of calculated metrics

Do not expose confidential system details, credentials, internal query text, or unnecessary customer information.

### 9. Validate the result

Before completing the task, verify:

- Chart values match the analyzed data
- Totals and percentages reconcile
- Dates, currencies, units, and number formats are consistent
- Categories have not been unintentionally omitted
- Axis scales do not exaggerate or conceal differences
- Slide titles accurately reflect the evidence
- Customer-facing slides contain no inappropriate internal commentary
- Confidential or account-sensitive data is limited to the intended audience
- The deck remains visually consistent
- Every recommended action follows from the analysis

## Output requirements

Produce one or more PowerPoint slides that include:

- A conclusion-led title
- An appropriate chart, scorecard, table, or visual comparison
- Clearly labeled figures and reporting periods
- Executive insights tied to the visual evidence
- A recommended action when the data supports one
- A source or methodology speaker note

When useful, provide a brief completion summary containing:

- Slides created or updated
- Data sources used
- Important filters or assumptions
- Data-quality issues or unresolved discrepancies
- The primary executive takeaway

## Common scenarios

### Customer usage and adoption

Visualize:

- Active versus licensed users
- Usage trends
- Product or workload adoption
- Depth and frequency of use
- Adoption by team, geography, or persona
- Underused capacity and expansion opportunity

Connect usage metrics to customer outcomes only when evidence supports the relationship.

### Customer value

Visualize:

- Value realized to date
- Value by use case or business unit
- Estimated versus validated value
- Progress toward a value target
- Remaining opportunity
- Adoption-to-value relationships

Clearly distinguish measured value from modeled or projected value.

### Pipeline and opportunity health

Visualize:

- Pipeline by stage
- Pipeline coverage
- Deal movement
- Aging and stalled opportunities
- Forecast categories
- Close-date concentration
- Risk by opportunity
- Expected versus committed revenue

Do not treat pipeline value as booked revenue.

### Financial performance

Visualize:

- Revenue and growth
- Actual versus target
- Forecast versus plan
- Cost, savings, or margin
- Return on investment
- Product or customer mix
- Variance drivers

Keep actual, forecast, pipeline, and modeled values visually distinct.

### Executive account review

Combine:

- Account health scorecard
- Usage and adoption
- Business value
- Open opportunities
- Risks and blockers
- Recommended executive actions

Prioritize the two or three findings most likely to affect the account outcome.

## Failure handling

If usable data cannot be retrieved:

- State which source or fields are unavailable
- Do not create charts containing synthetic values
- Create a clearly labeled slide structure only if the user explicitly requests a template
- Identify the minimum data needed to complete the analysis

If the data is incomplete:

- Use the valid subset when it can answer the question without distortion
- Disclose the limitation in the slide or speaker notes
- Avoid extrapolation unless explicitly requested
- Label any requested projection as an estimate and document its method

If the requested chart is inappropriate for the data:

- Select a more accurate visual
- Briefly explain the substitution in the completion summary