---
name: gantt-chart-generator
description: "Use this skill whenever the user asks to visualize a project schedule, timeline, Gantt chart, or phase/task breakdown over time. It gives the agent a prebuilt, parameterized gantt() function so Gantt charts are produced instantly and consistently — with colour-coded groups, completion overlays, a today reference line, and auto-scaled date axes — instead of hand-writing matplotlib each time."
---

Generate horizontal Gantt charts from schedule data via the bundled `scripts/gantt.py` toolkit.
The `gantt()` function accepts a DataFrame or file path plus column names, and saves a PNG (returning the path).
It handles theming, date parsing, bar colour-coding, completion overlays, today-line, legend, and saving.

## Trigger keywords
Invoke this skill when the user mentions: Gantt, timeline chart, project schedule, phase schedule, task schedule, WBS, schedule visualization.

## Instructions

1. Provide the data source: a pandas DataFrame, or a path to a `.csv` / `.tsv` / `.json` file.
   - One row = one task / phase.
   - Required columns: a **phase/task name** column, a **start date** column, and either an **end date** column OR a **duration-in-days** column.

2. Import and call `gantt()`:

```python
import sys
sys.path.insert(0, "scripts")   # adjust path to where gantt.py is deployed
from gantt import gantt

# Basic — start + end columns
gantt("schedule.csv", phase="Phase", start="Start", end="End",
      title="Project Schedule", out="/app/created/gantt.png")

# Group colour-coding + today line
gantt(df, phase="phase", start="planned_start", end="planned_end",
      group="project", today=True, out="/app/created/schedule.png")

# Duration instead of end date
gantt(df, phase="task", start="start_date", duration="days",
      out="/app/created/schedule.png")

# Completion % hatch overlay
gantt(df, phase="Phase", start="Start", end="End",
      completion="PctDone", out="/app/created/gantt.png")
```

3. See `references/cheatsheet.md` for full parameter reference and CLI examples.

## Bundled files
- `scripts/gantt.py`      — the full toolkit (load_data, apply_theme, save_fig, gantt, CLI)
- `references/cheatsheet.md` — parameter quick-reference and copy-paste examples
- `assets/sample_schedule.csv` — demo dataset that exercises every feature

## Defaults & behaviour
- Colorblind-friendly palette (matches chart-builder skill for visual consistency).
- Date axis auto-scales: weekly ticks ≤90 days, monthly ≤365 days, bi-monthly beyond.
- Bars ordered top-to-bottom matching input row order.
- Rows with missing phase or start values are silently dropped before drawing.
- Output PNG at 150 DPI by default.
- Provide `end` OR `duration` — not both; `end` takes priority if both are present.
