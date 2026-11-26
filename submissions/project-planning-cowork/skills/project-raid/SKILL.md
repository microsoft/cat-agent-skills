---
name: project-raid
description: Creates an offline RAID dashboard and action register for project risks, assumptions, issues, and dependencies. Use to consolidate planning blockers, review follow-up ownership, or track actions linked to task and risk IDs.
---

# Project RAID register

Use RAID for action tracking across four kinds of planning information. Use the risk matrix for visual risk triage, and Gantt or PERT for schedule dependencies between tasks.

## Input and workflow

1. Use user-supplied data (table, export, notes, JSON) or authorized Work IQ results when available and in scope. If no source is available, ask for the relevant records; don't claim a lookup, invent owners/dates, or turn a possible event into an occurred issue. Use the bundled information only for a labeled demo.
2. Normalize to UTF-8 JSON with `project` and at least one of the arrays below. Use `[]` for an explicitly empty category and omit a category if it was not supplied. Preserve stable IDs. An optional `as_of` date records the register snapshot; it is not guessed from the current date.

| Array | What belongs here | Action field |
|---|---|---|
| `risks` | An uncertain event and its potential effect | `mitigation` |
| `assumptions` | A planning belief that needs validation | `validation_action` |
| `issues` | A problem that has already occurred | `resolution_action` |
| `dependencies` | A needed input, decision, or deliverable | `next_action` |

Every item needs a nonblank string `id` (unique within its category) and `title`. The optional action field and `owner`, `details`, `status` are text; `due_date` and `as_of` are `YYYY-MM-DD` dates. `task_ids` and `risk_ids` are optional arrays of referenced IDs; `[]` explicitly means none. An optional `tasks` array of `id` and `title` objects makes known task references clickable. Related risks present in the register are linked; absent targets remain visible. If an issue materializes from a risk, keep distinct IDs and link the issue's `risk_ids` back to the original risk.

For risks, use optional `likelihood` (`Very Likely`, `Likely`, `Possible`, `Unlikely`, `Very Unlikely`) and `severity` (`Negligible`, `Minor`, `Moderate`, `Significant`, `Severe`) with the shared qualitative risk-matrix policy, not numeric multiplication. Pass the same `risks` array to the matrix skill. Missing ratings stay unassessed; invalid labels are rejected.

3. Run the renderer. Check the categories, follow-up actions, and missing owners/dates with the user. Deliver the register without updating enterprise systems or treating planned AI support as assigned or executed work.

## Generate and deliver

Keep the output light regardless of host theme. The bundled `scripts/planning_html.py` provides the shared project planning design; no separate skill or network assets are needed. Run from this skill directory with Python 3 (standard library only):

```sh
python3 scripts/render.py examples/onboarding.json raid.html
```

The [synthetic onboarding example](examples/onboarding.json) links an actual access issue to a wider access risk and to the relevant task. The output is one offline HTML dashboard with four category counts, separate actionable tables, ID links where a target is present, and visible gaps for missing fields.

If the host cannot run Python or return files, say so and provide the normalized inputs and local command rather than claiming generation.
