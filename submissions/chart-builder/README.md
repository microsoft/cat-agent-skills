# Chart Builder

Turn a spreadsheet or table into a clean, good-looking chart — bar, line,
scatter, histogram, or pie — with a single request.

## Why use this?

Your agent can already make charts without any skill. When you ask for one, it
writes a fresh, one-off chart script on the spot and runs it. That works, but
because it starts from scratch each time, the results vary. Ask for "revenue by
region" twice and you might get two different color schemes, two different sizes,
or labels that overlap in one but not the other.

Chart Builder swaps that ad hoc approach for a fixed, reusable set of chart
functions. Instead of writing new plotting code for each request, the agent
calls a function that's already built: you pick the chart and the data, and the
skill handles the styling and the details.

The benefits:

- **Usually faster** — calling a ready-made function skips the work of writing
  and debugging new plotting code on each request.
- **More consistent** — charts share the same tidy style and a color palette
  that's friendly to colorblind viewers, so a set of charts looks like it
  belongs together.
- **Fewer rough edges** — the functions handle the fiddly bits: skipping blank
  rows, angling labels when they'd overlap, widening the chart when there are
  lots of categories, and keeping the legend out of the way.

The best way to judge the difference is to try both on your own data: ask for a
few charts the normal way, then with this skill, and compare the speed and the
results.

## What you get

Six chart types from one toolkit:

| Chart | Best for |
| --- | --- |
| Bar | comparing a value across categories |
| Grouped / stacked bar | comparing across categories **and** a second grouping |
| Line | a value changing over time or sequence |
| Scatter | the relationship between two numbers |
| Histogram | the spread of a single number |
| Pie / donut | parts of a whole |

Just tell the agent what to plot, for example:

> Make a stacked bar chart of revenue by region and quarter.

A sample dataset (`assets/sample_sales.csv`) is included so you can try any of the
charts right away.

## Requirements

Runs in the standard Python environment for Cowork, Copilot Studio, and Scout,
with matplotlib and pandas — nothing to install or set up.
