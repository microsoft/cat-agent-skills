---
name: Chart Builder
description: "Generate clean, consistently-styled matplotlib charts (bar, line, scatter, histogram, pie) from a DataFrame or CSV with one call."
agentDescription: "Use this skill whenever the user asks to visualize, chart, plot, or graph data (bar, line, scatter, histogram, pie) from a CSV, table, or DataFrame. It gives the agent prebuilt, parameterized matplotlib functions so charts are produced faster and more reliably — with consistent styling and sane defaults — instead of hand-writing matplotlib each time."
platforms: [Cowork, Copilot Studio, Scout]
tags: [data, charts, matplotlib, scripts]
author: CAT Agent Skills
authorUrl: "https://github.com/microsoft/cat-agent-skills"
version: 1.0.0
createdAt: 2026-07-14
updatedAt: 2026-07-14
featured: true
bundle: bundles/chart-builder.zip
---
Generate charts from tabular data via the bundled `scripts/charts.py` toolkit.
Each function takes a DataFrame or a file path plus the columns to plot, and
saves a PNG (returning the path). It handles theming, figure sizing, label
rotation, NaN dropping, legend placement, and saving.

## Instructions
1. Provide the data source: a pandas DataFrame, or a path to a `.csv` / `.tsv` /
   `.json` file.
2. Call the function for the chart you need, passing the column names:
   - `bar(data, x, y)` — one value per category (`horizontal=True` for barh)
   - `grouped_bar(data, x, y, group)` — value per category split by `group`
     (`stacked=True` to stack)
   - `line(data, x, y, group=None)` — value over an ordered axis, one line per
     `group`
   - `scatter(data, x, y, group=None, size=None)` — two numeric columns
   - `histogram(data, y, bins=20, group=None)` — distribution of one column
   - `pie(data, x, y, donut=False)` — share of `y` per category `x`
3. Optional keyword args on every chart: `title`, `xlabel`, `ylabel` (derived
   from column names if omitted), `out` (default `"chart.png"`; pass `None` to
   skip saving), `dpi` (default `150`), `figsize`, `palette`.
4. The function returns the saved image path. See `references/cheatsheet.md` for
   full signatures and a chart-selection table.

## Usage
Import:
```python
from charts import bar, line, pie
bar("sales.csv", x="region", y="revenue", title="Revenue by region",
    out="revenue.png")
```

CLI:
```bash
python scripts/charts.py grouped_bar sales.csv \
    --x region --y revenue --group quarter --stacked --out by_quarter.png
```

## Bundled files
- `scripts/charts.py` — the toolkit: `load_data`, `apply_theme`, `save_fig`, and
  six chart functions (`bar`, `grouped_bar`, `line`, `scatter`, `histogram`,
  `pie`), plus a CLI. Depends on `matplotlib` and `pandas`; runs headless.
- `references/cheatsheet.md` — chart-selection table, full signatures, and
  copy-paste CLI examples.
- `assets/sample_sales.csv` — a small demo dataset that exercises every chart.

## Defaults
- Colorblind-friendly palette and a shared theme across charts.
- Figure size, x-label rotation, and legend placement adapt to the data.
- Rows with missing values in the plotted columns are dropped before drawing.
- Output is a saved PNG at 150 DPI by default (override `out` and `dpi`).
