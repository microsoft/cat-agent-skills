# Gantt Chart Builder — Cheat Sheet

The single function lives in `scripts/gantt.py`. It accepts a **DataFrame or a
path** to a `.csv` / `.tsv` / `.json` file as the first argument, draws a
horizontal Gantt chart, saves a PNG to `out`, and returns the saved path.

```python
from gantt import gantt
```

---

## Minimum required columns

| What | Column role |
|---|---|
| Task / phase label | y-axis labels (one row = one bar) |
| Start date | left edge of each bar |
| End date **or** Duration (days) | right edge of each bar |

---

## Full parameter reference

| Parameter | Type | Default | Description |
|---|---|---|---|
| `data` | DataFrame or str | **required** | Input data or path to .csv/.tsv/.json |
| `phase` | str | **required** | Column: task/phase name (y-axis) |
| `start` | str | **required** | Column: start date |
| `end` | str | `None` | Column: end date |
| `duration` | str | `None` | Column: duration in days (use if no `end`) |
| `group` | str | `None` | Column: group/project → colour-codes bars |
| `completion` | str | `None` | Column: 0–100 % done → hatch overlay |
| `today` | bool | `True` | Draw a vertical today reference line |
| `today_date` | date | `None` | Override today's date (datetime.date) |
| `date_fmt` | str | `"%Y-%m-%d"` | strptime format for string date columns |
| `title` | str | `""` | Chart title |
| `xlabel` | str | `"Timeline"` | X-axis label |
| `ylabel` | str | `None` | Y-axis label (defaults to `phase` col name) |
| `out` | str | `"gantt.png"` | Output path; `None` skips saving |
| `dpi` | int | `150` | Output resolution |
| `figsize` | tuple | `None` | `(width, height)` inches; auto-sized if omitted |
| `palette` | list | PALETTE | Hex colour list; cycles if more groups than colours |
| `bar_height` | float | `0.55` | Fractional bar height (0–1) |
| `annotate_dates` | bool | `True` | Show start/end date labels beside bars |
| `annotate_duration` | bool | `True` | Show duration-in-days label inside bars |

---

## When to use each optional column

| Column | Use when… |
|---|---|
| `group` | Tasks belong to different projects/workstreams → distinct colours |
| `completion` | You have progress data → hatched "done" portion inside each bar |
| `today` / `today_date` | You want a reference line marking the current date |
| `duration` | Your data has days of effort but no end date column |

---

## Copy-paste examples

### Python API

```python
from gantt import gantt
import pandas as pd

# 1. Simplest — CSV with Start/End columns
gantt("assets/sample_schedule.csv",
      phase="Phase", start="Start", end="End",
      title="Project Schedule", out="gantt.png")

# 2. Multi-project with group colours
gantt("assets/sample_schedule.csv",
      phase="Phase", start="Start", end="End",
      group="Project",
      title="Multi-Project Timeline", out="multi.png")

# 3. Completion overlay
gantt("assets/sample_schedule.csv",
      phase="Phase", start="Start", end="End",
      completion="PctDone",
      title="Schedule with Progress", out="progress.png")

# 4. Duration instead of end date
df = pd.DataFrame({
    "Task":  ["Design", "Build", "Test", "Deploy"],
    "Start": ["2026-01-05", "2026-01-19", "2026-03-02", "2026-03-23"],
    "Days":  [10, 30, 15, 5],
})
gantt(df, phase="Task", start="Start", duration="Days",
      title="Sprint Schedule", out="sprint.png")

# 5. Custom figure size, no today line
gantt("assets/sample_schedule.csv",
      phase="Phase", start="Start", end="End",
      today=False, figsize=(20, 10), dpi=200, out="large.png")
```

### CLI

```bash
# Basic
python scripts/gantt.py assets/sample_schedule.csv \
    --phase Phase --start Start --end End \
    --title "Project Schedule" --out gantt.png

# Multi-project with group colours
python scripts/gantt.py assets/sample_schedule.csv \
    --phase Phase --start Start --end End \
    --group Project --title "Multi-Project" --out multi.png

# With completion overlay, no today line
python scripts/gantt.py assets/sample_schedule.csv \
    --phase Phase --start Start --end End \
    --completion PctDone --no-today --out progress.png

# Duration instead of end date
python scripts/gantt.py schedule.csv \
    --phase Task --start Start --duration Days --out sprint.png

# Override today's date, custom size
python scripts/gantt.py assets/sample_schedule.csv \
    --phase Phase --start Start --end End \
    --today-date 2026-04-01 --figsize 20 10 --dpi 200 --out custom.png
```

---

## Notes
- `end` takes priority over `duration` if both are provided.
- Bars are drawn top-to-bottom in input row order.
- Rows missing `phase` or `start` are silently dropped.
- The palette cycles if there are more groups than colours (10 colours by default).
- `completion` values are clamped to 0–100; NaN rows show no hatch.
