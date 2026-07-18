# Chart Builder

Turn a spreadsheet or table into a clean, good-looking chart — bar, line,
scatter, histogram, or pie — with a single request.

## Why use this?

Your agent can already make charts without any skill. When you ask for one, it
quietly writes a little chart-drawing code on the spot and runs it. That works —
but because it improvises every time, the results drift. Ask for "revenue by
region" twice and you might get two different color schemes, two different sizes,
labels that overlap in one but not the other, or a chart that fails on messy data.

Chart Builder replaces that improvisation with a **ready-made recipe**. Instead of
inventing a chart from scratch each time, the agent fills in a proven template:
you pick the chart and the data, and the skill handles the look and the details.

The payoff:

- **Consistent** — every chart uses the same tidy style and a color palette that's
  friendly to colorblind viewers, so a set of charts looks like it belongs
  together.
- **Faster** — one step instead of writing and debugging fresh code for each chart.
- **Dependable** — it quietly handles the fiddly bits: skipping blank rows,
  angling labels when they'd overlap, widening the chart when there are lots of
  categories, and keeping the legend out of the way.

Think of it as guardrails, not a new trick: the agent *could* draw the chart
free-hand, but this makes sure it does it well the same way every time.

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

Runs in the standard environment for Cowork, Copilot Studio, and Scout — nothing
to install or set up.
