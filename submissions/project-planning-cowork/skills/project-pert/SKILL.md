---
name: project-pert
description: Builds an offline Program Evaluation and Review Technique dependency network and critical-path table from optimistic, most-likely, and pessimistic task durations. Use for parallel branches, sequencing, and schedule sensitivity before committing to dates.
---

# Project PERT chart

Use PERT to estimate dependency-driven elapsed duration. Use Gantt for concrete calendar dates. This skill does not estimate capacity or execute the plan.

## Input and workflow

1. Use the user's supplied project data (table, export, notes, JSON) or relevant authorized Work IQ results when available. Ask for missing estimates, task relationships, units, and calendar assumptions; don't imply an unavailable source was queried. Never infer three estimates from one unconfirmed duration. Use the bundled inputs only for explicitly synthetic examples.
2. Normalize to UTF-8 JSON with `project`, a nonblank `duration_unit` (e.g. `working days`), a `calendar_assumption` explaining the time basis, and a nonempty `tasks` array. Map accepted dependencies to finish-to-start with no lag. Confirm any conversion from another relationship type or lag; do not silently discard it.
3. Generate and check the network, critical path count, and table before returning the HTML. If inputs are missing or invalid, report the offending tasks and ask for corrections; never prune tasks and present a partial network as complete.

Each task needs a unique string `id`, `title`, `predecessors` (array of known task IDs; use `[]` for intentional start nodes), and three numeric fields: `optimistic`, `most_likely`, `pessimistic`. They must be nonnegative and ordered low to high, no greater than `10^12` in the chosen unit, with at most 12 decimal places. A `type` of `milestone` requires three explicit zeros. Optional `owner`, `notes`, and `work_mode` (`human`, `ai-prep`, `human-review`) use the same meanings as Gantt. Preserve IDs and predecessors if the user later adds scheduled dates to a Gantt.

The renderer rejects missing estimates or predecessor lists, unknown predecessors, duplicate IDs, and cycles. It calculates `(optimistic + 4 × most_likely + pessimistic) / 6` with exact arithmetic, then applies forward and backward passes across a common time-zero start and project finish. Parallel branches may run simultaneously in the mathematical model; nothing in the output confirms actual staffing or Cowork concurrency. The calendar assumption is displayed, not used to convert offsets into dates. No calendars with holidays, lags, resource leveling, or probability forecasts are calculated.

## Generate and deliver

Keep the output light regardless of host theme. Use the bundled `scripts/planning_html.py` design and the violet critical-path cues; no separate skill or network assets are needed. Run from this skill directory with Python 3 (standard library only):

```sh
python3 scripts/render.py examples/onboarding.json pert.html
```

The [synthetic onboarding example](examples/onboarding.json) has a human access check in parallel with AI drafting, both required by human review. Review follows the longer draft branch; the access branch has float. Deliver the standalone HTML with its network, one representative critical path and the count of all ties, and the supporting table. The chart highlights all critical paths; the table lists every critical predecessor, the three estimates, expected durations, early/late times and float. Values are rounded for display only.

If the host cannot run Python or return files, say so and provide the normalized inputs and local command rather than claiming generation.
