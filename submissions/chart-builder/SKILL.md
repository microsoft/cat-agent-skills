---
name: chart-builder
description: "Use this skill whenever the user asks to visualize, chart, plot, or graph data (bar, line, scatter, histogram, pie) from a CSV, table, or DataFrame. It gives the agent prebuilt, parameterized matplotlib functions so charts are produced faster and more reliably — with consistent styling and sane defaults — instead of hand-writing matplotlib each time."
---

Produce clean, consistently-styled charts from tabular data in one call —
without hand-writing matplotlib. The bundled `scripts/charts.py` toolkit owns
the plumbing (theming, defaults, auto figure sizing, label rotation, NaN
handling, saving) so you only choose the chart type and the columns to plot.

## When to use this
Use it any time the user wants to *see* data: "chart revenue by region",
"plot the trend", "show the distribution", "make a pie of the breakdown", or
when a table/CSV would land better as a picture. It's the fast, reliable path —
prefer it over writing matplotlib from scratch.

## Why prebuilt functions (even without knowing the data shape)
The functions are **parameterized, not hardcoded**. You don't need to know the
dimensions or column names ahead of time — you pass the data plus which columns
map to `x`, `y`, and (optionally) `group`. The library supplies the rest, which
is why it's both faster and more consistent than bespoke plotting code.

## Instructions
1. Identify the data source (a DataFrame, or a `.csv` / `.tsv` / `.json` path)
   and the columns to plot.
2. Pick the chart that fits the question (see the table in
   `references/cheatsheet.md`):
   - `bar` — one value across categories
   - `grouped_bar` — a value across categories split by a second dimension
     (add `stacked=True` for a stacked bar)
   - `line` — a value over an ordered axis; add `group=` for one line per series
   - `scatter` — relationship between two numeric columns
   - `histogram` — distribution of one numeric column
   - `pie` — parts-of-a-whole share for a few categories
3. Call the function, passing the column names and a `title`. Every function
   returns the saved image path.
4. Surface the resulting image path (or the file) to the user. If a chart type
   doesn't fit the columns (e.g. a non-numeric axis for `scatter`), pick a
   better-suited chart rather than forcing it.

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

## Defaults & guarantees
- Consistent, colorblind-friendly palette and understated theme across charts.
- Figure size, x-label rotation, and legend placement adapt to the data.
- Rows with missing values in the plotted columns are dropped before drawing.
- Output is a saved PNG at 150 DPI by default (override `out` and `dpi`).
