---
name: project-gantt
description: Creates an offline Gantt chart with an adaptive timeline, workstreams, milestones, and schedule details. Use for "get my tasks today", planning a productive day from calendar and work context, suggesting AI handoffs, or mapping project schedules and dependencies.
---

# Project Gantt chart

Use the Gantt view when the user has proposed or confirmed dates. Use a PERT view instead to analyze dependency-based duration from three-point estimates; do not convert those estimates into scheduled dates without an agreed calendar and schedule.

## Input and workflow

1. Use project data the user supplies (table, export, notes, JSON) or facts returned by an authorized Work IQ tool when available and in scope. If it is unavailable or has no result, ask for the relevant data; do not imply it was queried. Keep conflicting facts visible until confirmed. Use the bundled data only for a clearly labeled demo.
2. Normalize to UTF-8 JSON with a `project` title and a `tasks` array. Use the same `id`, `title`, `predecessors`, `work_mode`, `owner`, and `notes` values in any PERT handoff; keep task IDs referenced in RAID.
3. Run the renderer, resolve validation errors without dropping rows, and review the schedule warnings and unscheduled rows. Return the HTML and call out consequential missing dates, tentative dates, and conflicts. Never start, assign, or schedule live work as a side effect.

Each task requires a nonblank string `id` and `title`. Optional fields are:

| Field | Meaning |
|---|---|
| `type` | `task` (default) or `milestone`. A milestone marks an instant or a calendar day. Supply either endpoint, or both if identical. For a timed activity that ends with a milestone, use a task for the interval and a separate milestone for the event. |
| `start`, `end` | Inclusive calendar dates (`YYYY-MM-DD`) or local datetimes (`YYYY-MM-DDTHH:MM`, e.g. `2026-11-20T08:30`). Put times in these fields, not just in task titles. Use the same precision for both endpoints and one local time zone throughout; offsets and time zone conversion are not supported. Timed tasks must end after they start. Missing either task endpoint keeps it unscheduled. |
| `date_status` | `confirmed` or `tentative`. Absent confirmation stays visible and uses the tentative visual style. |
| `work_mode` | `human`, `ai-prep`, or `human-review`. Do not infer this from a task name; an absent mode stays unknown. |
| `workstream` | Optional name supplied by the user. Tasks without a workstream stay together rather than being assigned one. |
| `predecessors` | In-project task IDs for finish-to-start constraints. `[]` means explicitly none; omission means unknown. Unknown IDs and cycles fail validation. |
| `owner`, `notes` | Optional text. Use notes for date assumptions, capacity conflicts, handoff requirements, or external dependencies. |
| `priority_reason` | Single-day views only. A brief reason to protect this task today, based on the source context. Mark one or two tasks at most, in priority order in the `tasks` array. The list above the chart links to Schedule details; a priority may be unscheduled. |

Omit `view_start` and `view_end` to fit the supplied schedule, or give both as dates or both as local datetimes to specify the visible window. Leave `timeScale` unset or `auto` by default: a timed view of up to 48 hours uses hour labels, otherwise views up to 28 days use days, up to 60 days use Monday-based weeks, and longer views use months. Set `timeScale` to `hour`, `day`, `week`, or `month` only when the user requests that scale. Labels can skip intervals to stay readable; the scale does not round task positions or change dates.

## Daily plans

1. Treat "get my tasks today" as a request for a work plan, not a calendar recap. Use the user's supplied context and, where available and authorized, use Work IQ to check the calendar **and** relevant tracked tasks (such as Planner or To Do), recent email and Teams commitments, and meeting notes or project documents that contain open actions. Look for today's deadlines, meeting prep, promised follow-ups, and blockers. Deduplicate and omit completed or irrelevant items. Cite the source or supplied context in each task's `notes`; distinguish explicit commitments from suggested priorities. If only the calendar is available, say what was not checked rather than implying there is no other work.
2. Return one Gantt for the user's local day. Highlight one or two priorities above the chart with `priority_reason` when the context supports them (e.g. a due-today deliverable or an action that unblocks others); otherwise omit the list. Propose a small number of **tentative** focus blocks with buffer. Actively look for independent work that can run in parallel: for example, a teammate can validate a checklist during your review meeting, or a known background process can run while you draft. Preserve real overlaps, including calendar conflicts; note which overlaps are intentional and which need a decision. For proposed overlaps, check predecessors and who or what can do each task, put supported owners in `owner`, and explain why they can overlap in `notes`. Do not double-book the same person for attention-heavy work or assume that a tentative meeting is free time. If timing or capacity is too uncertain, leave the task unscheduled or explain the conditional overlap in the details. Do not invent deadlines, availability, or all-day bars for due-today tasks. Keep supplied workstreams in the table.
3. Suggest AI handoffs only when they help with a specific task and have a useful output, such as a first draft, briefing, recap, or checklist. Name the output and what the user must verify or decide. Put suggestions in the top-level `ai_handoffs` array (optional); each record has `id`, `title`, `task_id` (an existing task), `deliverable`, and `human_review`. Example: `{"id":"AI-1","title":"Draft a follow-up","task_id":"T-04","deliverable":"Draft reply from the meeting notes and open actions","human_review":"Check commitments and recipients before sending"}`. This list appears under **Schedule details**, not on the timeline. Only add an AI preparation bar to a daily plan if the user explicitly asks for it and there is a known or clearly proposed time block; otherwise include only the human work or review blocks. Suggestions are not assignments or completed work. Do not start tasks, send messages, or book time.

Timed and date-only rows can coexist: date-only tasks occupy whole inclusive calendar days and date-only milestones appear centered in their displayed day. The window clips bars but the table retains every task and its original precision. Workstream summaries show the visible span, not progress; a workstream with just one milestone has no summary bar. For timed dependencies, a task may start at its predecessor's exact finish. If either endpoint is date-only, the check compares calendar days: a task predecessor occupies its entire end day, while a milestone predecessor permits a same-day handoff. Missing data limits this check.

## Generate and deliver

Keep the output light regardless of host theme. The bundled `scripts/planning_html.py` provides the shared project planning design; no separate skill or network assets are needed. Run from this skill directory with Python 3 (standard library only):

```sh
python3 scripts/render.py examples/onboarding.json gantt.html
```

In the [synthetic onboarding example](examples/onboarding.json), human access checks and AI draft preparation overlap after scope is confirmed; human review waits for both. The launch milestone is tentative and follow-up is unscheduled. Keep rows compact and bars rounded. Show only the linked task ID in the left rail and the name as plain text beside the bar where space permits or inside wide bars, without a separate bubble, fill, or outline. Let long chart labels truncate without changing dates; the linked details table preserves full names and metadata. Milestones show their actual dates beside the diamonds. Overlap is a planning choice, not evidence that resources are free or that Cowork can run concurrent jobs.

If the host cannot run Python or return files, say so and provide the normalized inputs and local command rather than claiming generation.
