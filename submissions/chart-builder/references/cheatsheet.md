# Chart Builder — function cheat sheet

All functions live in `scripts/charts.py`. They accept a **DataFrame or a path**
to a `.csv` / `.tsv` / `.json` file as the first argument, and save a PNG to
`out` (returning the saved path). Import them or use the CLI.

```python
from charts import bar, grouped_bar, line, scatter, histogram, pie
```

## When to use which chart
| Chart | Use when… | Required cols |
| --- | --- | --- |
| `bar` | comparing one value across categories | `x` (category), `y` (value) |
| `grouped_bar` | comparing a value across categories **and** a second dimension | `x`, `y`, `group` |
| `line` | a value changing over an ordered axis (time, sequence) | `x`, `y` (+ optional `group`) |
| `scatter` | relationship between two numeric variables | `x`, `y` (numeric) |
| `histogram` | the distribution / spread of one numeric variable | `y` (numeric) |
| `pie` | parts-of-a-whole share (few categories) | `x` (category), `y` (value) |

## Common keyword arguments
Every chart accepts: `title`, `xlabel`, `ylabel` (auto-derived from column names
if omitted), `out` (default `"chart.png"`, pass `None` to skip saving),
`dpi` (default `150`), `figsize` (auto-sized from the data if omitted), and
`palette`.

## Signatures
```python
bar(data, x, y, *, horizontal=False, ...)
grouped_bar(data, x, y, group, *, stacked=False, ...)
line(data, x, y, *, group=None, markers=True, ...)
scatter(data, x, y, *, group=None, size=None, ...)
histogram(data, y, *, bins=20, group=None, ...)
pie(data, x, y, *, donut=False, max_slices=8, ...)
```

Notes:
- `grouped_bar` aggregates with `pivot_table(..., aggfunc="sum")`, so duplicate
  `(x, group)` rows are summed automatically.
- `pie` sorts slices and rolls everything past `max_slices` into an "Other"
  slice, so it stays legible even with a long-tailed category column.
- `scatter`'s `size` column is min-max scaled into a readable marker-size range.
- Legends auto-move outside the plot when there are more than four series.
- Rows with NaN in the plotted columns are dropped before drawing.

## CLI
```bash
python scripts/charts.py bar        assets/sample_sales.csv --x region --y revenue --out bar.png
python scripts/charts.py grouped_bar assets/sample_sales.csv --x region --y revenue --group quarter --stacked --out stacked.png
python scripts/charts.py line       assets/sample_sales.csv --x month --y revenue --group region --out line.png
python scripts/charts.py scatter    assets/sample_sales.csv --x ad_spend --y revenue --group region --out scatter.png
python scripts/charts.py histogram  assets/sample_sales.csv --y revenue --bins 8 --out hist.png
python scripts/charts.py pie        assets/sample_sales.csv --x region --y revenue --donut --out pie.png
```
