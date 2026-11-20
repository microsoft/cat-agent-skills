from datetime import date, datetime
import re

from planning_html import WORK_MODES, choice, h, id_list, page, records, run, scroll, show, table, task_graph, text


CSS = """
.timeline { --rail: 13rem; min-width: 51rem; padding: .75rem 1rem; }
.timeline.daily { --rail: 5.5rem; }
.day-priorities { margin-block: .75rem 1rem; }
.day-priorities h3 { font-size: .95rem; }
.day-priorities ol { margin: .25rem 0 0; padding-inline-start: 1.4rem; overflow-wrap: anywhere; }
.day-priorities li + li { margin-top: .2rem; }
.timeline-row { display: grid; grid-template-columns: var(--rail) minmax(0, 1fr); }
.axis { min-height: 2.15rem; color: var(--text-dim); font-size: .73rem; font-weight: 700;
  border-inline: 1.5px solid transparent; }
.axis .rail { --group-tint: #edf2fb; border-radius: 9px; }
.rail { --rail-fill: color-mix(in srgb, var(--group-tint) var(--text-fill-opacity), transparent);
  position: sticky; left: 0; z-index: 2; background: var(--group-tint);
  background: linear-gradient(var(--rail-fill), var(--rail-fill)), var(--surface); padding: .3rem .6rem;
  min-width: 0; border-right: 1px solid var(--border); }
.dates, .track { position: relative; min-width: 0; }
.tick, .guide { position: absolute; inset-block: 0; border-left: 1px solid #d5dfed; }
.tick { padding: .32rem .3rem; white-space: nowrap; }
.band { --group-tint: var(--teal-tint); --group-ink: var(--teal); --band-line: var(--cyan-line);
  --band-glow: var(--cyan-glow); margin-top: .45rem; border: 1.5px solid var(--band-line); border-radius: 12px;
  box-shadow: 0 0 12px var(--band-glow); }
.band-1 { --group-tint: var(--purple-tint); --group-ink: var(--purple); --band-line: var(--violet-line);
  --band-glow: var(--violet-glow); }
.band-2 { --group-tint: var(--amber-dim); --group-ink: var(--amber); --band-line: var(--amber-line);
  --band-glow: var(--amber-glow); }
.band .track { background: rgb(255 255 255 / 54%); min-height: 2rem; }
.band .timeline-row:first-child .rail { border-top-left-radius: 11px; }
.band .timeline-row:last-child .rail { border-bottom-left-radius: 11px; }
.band-title h3 { font-size: .85rem; color: var(--group-ink); }
.band .timeline-row + .timeline-row { border-top: 1px solid rgb(215 226 240 / 52%); }
.task-row .rail { display: flex; align-items: center; gap: .35rem; }
.task-row .rail a { min-width: 0; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
  color: var(--text-head); font-size: .79rem; font-weight: 650; }
.role-dot { flex: 0 0 .45rem; height: .45rem; border-radius: 50%; background: var(--color); }
.bar, .group-span, .milestone { position: absolute; top: 50%; transform: translateY(-50%); }
.bar, .group-span { border-radius: 999px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
  text-align: center; font-size: .7rem; font-weight: 700; height: 1.05rem; line-height: 1.05rem; }
.bar { background: var(--color); color: white; overflow: visible;
  box-shadow: 0 0 0 1.5px var(--role-line), 0 0 12px var(--role-glow); }
.bar:not(.tentative):has(~ .label-on) {
  background-color: color-mix(in srgb, var(--color) var(--text-fill-opacity), transparent);
}
.group-span { background: var(--group-tint); color: var(--group-ink); outline: 1px solid var(--group-ink); outline-offset: -1px; }
.group-span { background-color: color-mix(in srgb, var(--group-tint) var(--text-fill-opacity), transparent); }
.milestone { color: var(--color); height: 1.8rem; width: 0; z-index: 1; }
.milestone::before { content: ''; position: absolute; top: 50%; left: 0; width: .9rem; height: .9rem;
  transform: translate(-50%, -50%) rotate(45deg); border: 2px solid currentColor; border-radius: 2px;
  background: currentColor; box-shadow: 0 0 0 2px #fff, 0 0 12px var(--role-glow); }
.milestone.pending::before { background: #fff; }
.timeline-label { display: flex; align-items: baseline; gap: .3rem; position: absolute; top: 50%;
  transform: translateY(-50%); max-width: 100%;
  color: var(--color); font-size: .73rem; font-weight: 700; line-height: 1.35;
  white-space: nowrap; }
.timeline-label span { min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.timeline-label time { flex: none; font-size: .68rem; }
.label-after { left: calc(var(--edge) + var(--gap)); max-width: calc(100% - var(--edge) - var(--gap)); }
.label-before { right: calc(100% - var(--edge) + var(--gap)); max-width: calc(var(--edge) - var(--gap)); }
.label-on { left: var(--edge); width: var(--size); justify-content: center;
  padding-inline: .36rem; color: white; }
.tentative ~ .label-on { color: var(--color); }
.tentative { background: repeating-linear-gradient(135deg, var(--tint) 0 5px, #fff 5px 10px);
  background-image: repeating-linear-gradient(135deg,
    color-mix(in srgb, var(--tint) var(--text-fill-opacity), transparent) 0 5px, #fff 5px 10px);
  color: var(--color); outline: 1px dashed var(--color); outline-offset: -1px; }
.human { --color: var(--teal); --tint: var(--teal-tint); --role-line: var(--cyan-line); --role-glow: var(--cyan-glow); }
.ai-prep { --color: var(--pink); --tint: var(--pink-tint); --role-line: var(--pink-line); --role-glow: var(--pink-glow); }
.human-review { --color: var(--blue); --tint: var(--blue-tint); --role-line: var(--blue-line); --role-glow: var(--blue-glow); }
.unknown { --color: var(--text-dim); --tint: var(--surface2); --role-line: var(--border); --role-glow: transparent; }
.roles { display: flex; flex-wrap: wrap; gap: .35rem .6rem; list-style: none; margin-block: .65rem; }
.roles li { background-color: color-mix(in srgb, var(--tint) var(--text-fill-opacity), transparent);
  color: var(--color); padding: .19rem .55rem; border-radius: 999px;
  font-size: .74rem; font-weight: 700; box-shadow: inset 0 0 0 1px var(--role-line); }
@media (max-width: 600px) {
  .timeline { --rail: 7.5rem; }
  .rail { padding-inline: .5rem; }
}
"""


MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
DAY = 24 * 60


def time_pair(obj, start_key, end_key, context):
    values = []
    for key in (start_key, end_key):
        raw = text(obj, key, context)
        if raw is None:
            values.append(None)
            continue
        try:
            if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", raw):
                values.append(date.fromisoformat(raw))
                continue
            if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}", raw):
                values.append(datetime.fromisoformat(raw))
                continue
        except ValueError:
            pass
        raise ValueError(f"{context}: {key} must be a valid YYYY-MM-DD or local YYYY-MM-DDTHH:MM (no offset)")
    start, end = values
    if start is not None and end is not None and type(start) is not type(end):
        raise ValueError(f"{context}: {start_key} and {end_key} must both be dates or both be local datetimes")
    return start, end


def minute(value, *, end=False):
    base = value.toordinal() * DAY
    if isinstance(value, datetime):
        return base + value.hour * 60 + value.minute
    return base + (DAY if end else 0)


def calendar_day(value):
    return date.fromordinal(value // DAY)


def short_date(value):
    return f"{MONTHS[value.month - 1]} {value.day}"


def clock(value):
    hour, mins = divmod(value % DAY, 60)
    return f"{hour % 12 or 12}{f':{mins:02d}' if mins else ''} {'AM' if hour < 12 else 'PM'}"


def display_at(value, timed=False):
    if value == (date.max.toordinal() + 1) * DAY:
        return "End of Dec 31, 9999"
    label = short_date(calendar_day(value))
    return f"{label} {clock(value)}" if timed else label


def iso(value):
    return value.isoformat(timespec="minutes") if isinstance(value, datetime) else str(value)


def step_for(span, candidates, target=7):
    return next((step for step in candidates if span <= target * step), (span + target - 1) // target)


def ticks(start, end, scale):
    span = end - start
    if scale == "hour":
        multi_day = start // DAY != (end - 1) // DAY
        step = 60 * step_for((span + 59) // 60, (1, 2, 3, 4, 6, 8, 12, 24), 6 if multi_day else 10)
        marks = [(0, display_at(start, True) if multi_day else clock(start))]
        for value in range((start // step + 1) * step, end, step):
            ratio = 100 * (value - start) / span
            if ratio - marks[-1][0] >= (14 if multi_day else 7) and ratio <= (88 if multi_day else 92):
                marks.append((ratio, display_at(value, True) if multi_day else clock(value)))
        return marks
    if scale == "day":
        step = DAY * step_for((span + DAY - 1) // DAY, (1, 2, 3, 5, 10))
        marks = [(0, display_at(start))]
        for value in range((start // DAY) * DAY + step, end, step):
            ratio = 100 * (value - start) / span
            if ratio - marks[-1][0] >= 10 and ratio <= 88:
                marks.append((ratio, display_at(value)))
        return marks
    if scale == "week":
        first = start - start % DAY - calendar_day(start).weekday() * DAY
        step = 7 * DAY * step_for((span + 7 * DAY - 1) // (7 * DAY), (1, 2, 3, 4, 8, 13, 26, 52))
        marks = [(0, f"Wk of {display_at(first)}")]
        for value in range(first + step, end, step):
            ratio = 100 * (value - start) / span
            if ratio - marks[-1][0] >= 12 and ratio <= 88:
                marks.append((ratio, f"Wk of {display_at(value)}"))
        return marks

    start_day, last_day = calendar_day(start), calendar_day(end - 1)
    month = start_day.year * 12 + start_day.month - 1
    last_month = last_day.year * 12 + last_day.month - 1
    interval = next(step for step in (1, 2, 3, 6, 12, 24, 60, 120, 600, 2400, 24000)
                    if last_month - month <= step * 7)
    year_marks = interval >= 12
    output = [(0, f"{short_date(start_day)}, {start_day.year}" if year_marks else short_date(start_day))]
    for index in range(((month // interval) + 1) * interval, last_month + 1, interval):
        year, month_index = divmod(index, 12)
        offset = 100 * (minute(date(year, month_index + 1, 1)) - start) / span
        if offset - output[-1][0] >= 12 and offset <= 88:
            output.append((offset, str(year) if year_marks else f"{MONTHS[month_index]} {year}"))
    return output


def geometry(start, end, view_start, span):
    return 100 * (start - view_start) / span, 100 * (end - start) / span


def task_label(title, offset, width, milestone=None):
    end = offset + width
    gap = ".84rem" if milestone else ".45rem"
    if 100 - end >= 28:
        placement, edge = "after", end
    elif offset >= 28:
        placement, edge = "before", offset
    else:
        placement, edge = "on", offset
    date_label = (f'<time datetime="{iso(milestone)}">'
                  f'{display_at(minute(milestone), isinstance(milestone, datetime))}</time>') if milestone else ""
    return (f'<span class="timeline-label label-{placement}" '
            f'style="--edge:{edge:.8f}%;--size:{width:.8f}%;--gap:{gap}">'
            f'<span>{h(title)}</span>{date_label}</span>')


def chart(groups, view_start, view_end, has_workstreams, scale, timed, single_day):
    span = view_end - view_start
    labels = ticks(view_start, view_end, scale)
    axis = "".join(f'<span class="tick" style="left:{offset:.8f}%">{label}</span>' for offset, label in labels)
    guides = "".join(f'<span class="guide" style="left:{offset:.8f}%"></span>' for offset, _ in labels)
    if single_day:
        groups = {None: sorted((task for rows in groups.values() for task in rows), key=lambda task: task[0])}
    bands = []
    for number, (name, tasks) in enumerate(groups.items()):
        bands.append(f'<div class="band band-{number % 3}">')
        if not single_day:
            label = name or ("No workstream specified" if has_workstreams else "Project tasks")
            first = min(task[0] for task in tasks)
            last = max(task[1] for task in tasks)
            bounds = display_at(first, timed)
            if timed and first != last:
                bounds += f" – {clock(last) if first // DAY == last // DAY else display_at(last, True)}"
            elif not timed and first // DAY != (last - 1) // DAY:
                bounds += f" – {display_at(last - 1)}"
            summary = ""
            if len(tasks) > 1 or tasks[0][5] != "milestone":
                offset, width = geometry(first, last, view_start, span)
                summary = (f'<span class="group-span" style="left:{offset:.8f}%;width:{width:.8f}%">'
                           f'{bounds if width >= 19 else ""}</span>')
            bands.append(f'<div class="timeline-row band-title">'
                         f'<div class="rail"><h3 title="{h(bounds)}">{h(label)}</h3></div>'
                         f'<div class="track" aria-hidden="true">{guides}{summary}</div></div>')
        for left, right, ident, title, source_dates, kind, mode, certainty, placement, anchor, milestone in tasks:
            offset, width = geometry(left, right, view_start, span)
            palette = mode or "unknown"
            work = WORK_MODES.get(mode, "Work mode not supplied")
            certainty_label = certainty or "confirmation not supplied"
            detail = f"{source_dates}; {kind}; {certainty_label}; {placement}"
            if kind == "milestone":
                center = offset + width / 2
                status = "" if certainty == "confirmed" else " pending"
                glyph = (f'<span class="milestone {palette}{status}" style="left:{center:.8f}%" '
                         f'title="{h(detail)}"></span>')
                callout = task_label(title, center, 0, milestone)
            else:
                status = " tentative" if certainty != "confirmed" else ""
                glyph = (f'<span class="bar {palette}{status}" style="left:{offset:.8f}%;width:{width:.8f}%" '
                         f'title="{h(title)} — {h(detail)}"></span>')
                callout = task_label(title, offset, width)
            bands.append(f'<div class="timeline-row task-row"><div class="rail">'
                         f'<span class="role-dot {palette}" aria-hidden="true"></span>'
                         f'<a href="#{anchor}" aria-label="{h(ident)}: {h(title)}" '
                         f'title="{h(title)} — {h(work)}; {h(detail)}">{h(ident)}</a>'
                         f'</div><div class="track {palette}" aria-hidden="true">{guides}{glyph}{callout}</div></div>')
        bands.append("</div>")
    column = "Task ID" if single_day else "Workstream / task ID"
    layout = " daily" if single_day else ""
    return scroll("Scrollable dated project timeline",
                  f'<div class="timeline plot-surface{layout}" data-time-scale="{scale}"><div class="timeline-row axis">'
                  f'<div class="rail">{column}</div><div class="dates">{axis}</div></div>'
                  f'{"".join(bands)}</div>', chart=True)


def handoff_details(handoffs, anchors):
    rows = []
    for ident, handoff in handoffs.items():
        task_id = text(handoff, "task_id", ident, required=True)
        if task_id not in anchors:
            raise ValueError(f"{ident}: ai_handoffs task_id {task_id} does not match a task")
        rows.append((h(handoff["title"]), f'<a href="#{anchors[task_id]}">{h(task_id)}</a>',
                     h(text(handoff, "deliverable", ident, required=True)),
                     h(text(handoff, "human_review", ident, required=True))))
    if not rows:
        return ""
    return ('<h3>Suggested AI handoffs</h3><p class="note">Suggestions only; nothing has been assigned or started.</p>'
            + table("AI preparation and what to review",
                    ("Suggestion", "Related task", "AI deliverable", "Human review"), rows))


def day_priorities(tasks, anchors, single_day):
    items = []
    for ident, task in tasks.items():
        reason = text(task, "priority_reason", ident)
        if reason is not None:
            items.append(f'<li><a href="#{anchors[ident]}">{h(task["title"])}</a> — {h(reason)}</li>')
    if len(items) > 2:
        raise ValueError("use priority_reason on at most two tasks")
    if not items:
        return ""
    if not single_day:
        raise ValueError("priority_reason requires a single-day view")
    return '<div class="day-priorities"><h3>Today’s priorities</h3><ol>' + "".join(items) + "</ol></div>"


def render(data, project):
    scale = choice(data, "timeScale", ("auto", "hour", "day", "week", "month"), "project") or "auto"
    tasks = records(data, "tasks", required=True)
    handoffs = records(data, "ai_handoffs")
    parents, _, order = task_graph(tasks)
    anchors = {ident: f"task-{number}" for number, ident in enumerate(order, 1)}
    schedule = {}
    workstreams = {}
    warnings = []
    for ident in order:
        task = tasks[ident]
        workstreams[ident] = text(task, "workstream", ident)
        kind = choice(task, "type", ("task", "milestone"), ident) or "task"
        mode = choice(task, "work_mode", WORK_MODES, ident)
        certainty = choice(task, "date_status", ("confirmed", "tentative"), ident)
        start, end = time_pair(task, "start", "end", ident)
        if kind == "milestone":
            if start and end and start != end:
                raise ValueError(f"{ident}: milestone dates/times must match; use a task for an interval")
            start = end = start or end
        if start and end and start > end:
            raise ValueError(f"{ident}: start is after end")
        if kind == "task" and isinstance(start, datetime) and start == end:
            raise ValueError(f"{ident}: a timed task must end after it starts; use a milestone for an instant")
        for parent in parents[ident]:
            _, finish, parent_kind, _, _ = schedule[parent]
            if start and finish:
                if isinstance(start, datetime) and isinstance(finish, datetime):
                    conflict = start < finish
                else:
                    first_day, last_day = calendar_day(minute(start)), calendar_day(minute(finish))
                    conflict = first_day < last_day or (first_day == last_day and parent_kind != "milestone")
                if conflict:
                    warnings.append(f"{ident} starts before {parent} is available.")
        schedule[ident] = (start, end, kind, mode, certainty)

    window_start, window_end = time_pair(data, "view_start", "view_end", "project")
    if bool(window_start) != bool(window_end) or (window_start and minute(window_start) >= minute(window_end, end=True)):
        raise ValueError("supply both view_start and view_end in chronological order; timed windows must have positive duration")
    dated = [d for start, end, *_ in schedule.values() for d in (start, end) if d]
    if window_start:
        view_start, view_end = minute(window_start), minute(window_end, end=True)
    elif dated:
        window_start = min(dated, key=minute)
        window_end = max(dated, key=lambda value: minute(value, end=True))
        view_start, view_end = minute(window_start), minute(window_end, end=True)
        if view_start == view_end:
            # A single timed instant needs an hour of context, not a zero-width axis.
            view_start = view_start // 60 * 60
            view_end = view_start + 60
    else:
        view_start = view_end = None

    timeline = '<p class="note">No dated timeline available.</p>'
    rows = []
    groups = {}
    has_workstreams = any(workstreams.values())
    timed = isinstance(window_start, datetime) or isinstance(window_end, datetime)
    timed_visible = timed
    single_day = view_start is not None and view_start // DAY == (view_end - 1) // DAY

    for ident in order:
        task = tasks[ident]
        start, end, kind, mode, certainty = schedule[ident]
        mode_label = WORK_MODES.get(mode, "Not supplied")
        name = workstreams[ident]
        anchor = anchors[ident]
        placement = "Unscheduled (missing date)"
        if start and end:
            first, last = minute(start), minute(end, end=True)
            point = first == last
            left, right = max(first, view_start), min(last, view_end)
            visible = left < right or (point and left == right and
                                       (right < view_end or isinstance(window_end, datetime)))
            if not visible:
                placement = "Outside view"
            else:
                placement = "Clipped to view" if (left, right) != (first, last) else "In view"
                source_dates = f"{iso(start)} to {iso(end)}" if kind == "task" else iso(start)
                timed_visible |= isinstance(start, datetime)
                groups.setdefault(name, []).append((left, right, ident, task["title"], source_dates,
                                                    kind, mode, certainty, placement, anchor, start if kind == "milestone" else None))
        dependency = id_list(parents[ident]) if task.get("predecessors") is not None else "Not supplied"
        rows.append((f'<span id="{anchor}">{h(ident)}</span>', h(task["title"]), h(kind), mode_label,
                     show(task, "owner"), iso(start) if start else "Not supplied", iso(end) if end else "Not supplied",
                     h(certainty or "Not supplied"), placement, dependency, show(task, "notes"), h(name or "Not supplied")))

    if groups:
        count = sum(map(len, groups.values()))
        span = view_end - view_start
        if scale == "auto":
            scale = ("hour" if timed_visible and span <= 2 * DAY else "day" if span <= 28 * DAY
                     else "week" if span <= 60 * DAY else "month")
        window = (f"{display_at(view_start, True)} – {display_at(view_end, True)} (local time)"
                  if timed else f"{window_start} to {window_end}")
        timeline = (f'<p><strong>{window}</strong> · {count} of {len(tasks)} items shown.</p>'
                    '<ul class="roles" aria-label="Work mode legend">' +
                    "".join(f'<li class="{mode}">{label}</li>' for mode, label in WORK_MODES.items()) +
                    '</ul>' + chart(groups, view_start, view_end, has_workstreams, scale, timed_visible, single_day))
    elif window_start:
        timeline = f'<p>No fully dated tasks in the view {iso(window_start)} to {iso(window_end)}.</p>'

    notice = ""
    if warnings:
        notice = '<div class="warning"><p>Dependency conflicts</p><ul>' + "".join(
            f"<li>{h(message)}</li>" for message in warnings) + "</ul></div>"
    details = table("All tasks, including unscheduled and out-of-view work",
                    ("ID", "Task", "Type", "Work mode", "Owner", "Start", "End", "Date status", "Timeline",
                     "Predecessors", "Notes", "Workstream"), rows) if rows else "<p>No tasks supplied.</p>"
    body = (f'<section><h2>Project timeline</h2>{day_priorities(tasks, anchors, single_day)}{timeline}'
            '<p class="note">'
            + ('Pale bands show each workstream’s visible date span, not progress. ' if groups and not single_day else '')
            + 'Solid task pills are confirmed; '
            'striped pills and hollow diamonds are tentative or unconfirmed. Diamonds mark milestones. '
            'Dates are inclusive calendar days. '
            + ('Timed tasks use exact local start/end times; no time zone conversion is applied. ' if timed_visible else '')
            + ('Overlapping bars show concurrent work or calendar conflicts. See Schedule details for owners and context. '
               'The plan does not start AI work.' if single_day else
               'Simultaneous bars are plans, not proof of resource availability or launched AI work.')
            + '</p></section>'
            f'<section><h2>Schedule details</h2>{notice}{handoff_details(handoffs, anchors)}{details}</section>')
    return page(project, "Gantt chart", body, CSS)


if __name__ == "__main__":
    run("Render an offline date-based Gantt chart.", render)
