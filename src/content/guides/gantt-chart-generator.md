# Gantt Chart Builder

Turn a project schedule into a clean matplotlib Gantt chart — colour-coded
groups, completion overlays, and a today reference line — with one call.

## How to use it

Point the agent at a CSV (or table) with a phase/task column, a start date, and
either an end date or a duration in days. For example:

> "Make a Gantt from assets/sample_schedule.csv, colour by Project, show % done,
> and draw today's line."

Or call the toolkit directly:

```python
from gantt import gantt
gantt("schedule.csv", phase="Phase", start="Start", end="End",
      group="Project", completion="PctDone", today=True,
      title="Project Schedule", out="gantt.png")
```

## What you get

- Horizontal bars ordered as in your data
- Optional group colour-coding and completion hatch overlay
- Auto-scaled date axis (weekly / monthly / bi-monthly)
- PNG output at 150 DPI by default

See `references/cheatsheet.md` for the full parameter list and CLI examples.
Try `assets/sample_schedule.csv` for a ready-made demo.
