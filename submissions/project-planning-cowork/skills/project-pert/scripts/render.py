from collections import defaultdict
from decimal import Decimal
from fractions import Fraction

from planning_html import WORK_MODES, choice, h, id_list, page, records, run, scroll, show, table, task_graph, text


CSS = """
.network { display: block; max-width: none; }
.network rect { fill: var(--blue-tint); fill-opacity: var(--text-fill-opacity);
  stroke: var(--blue-line); stroke-width: 1.5; rx: 11px;
  filter: drop-shadow(0 0 5px var(--blue-glow)); }
.network text { fill: var(--text); font: 14px system-ui, sans-serif; }
.network .secondary { font-size: 12px; }
.network path.edge { fill: none; stroke: var(--text-muted); stroke-width: 1.5; }
.network path.critical, .network rect.critical { stroke: var(--violet-line); stroke-width: 2.5; }
.network path.critical { filter: drop-shadow(0 0 4px var(--violet-glow)); }
.network rect.critical { fill: var(--purple-tint); filter: drop-shadow(0 0 9px var(--violet-glow)); }
"""


def fmt(value):
    return format(Decimal(value.numerator) / Decimal(value.denominator), ".6g")


def estimates(task):
    ident = task["id"]
    keys = ("optimistic", "most_likely", "pessimistic")
    numbers = []
    for key in keys:
        value = task.get(key)
        if type(value) not in (int, Decimal) or not 0 <= value <= 10**12:
            raise ValueError(f"{ident}: {key} must be a supplied number from 0 to 10^12")
        if isinstance(value, Decimal) and value != 0 and value.as_tuple().exponent < -12:
            raise ValueError(f"{ident}: {key} must use at most 12 decimal places")
        numbers.append(Fraction(value) if value else Fraction(0))
    o, m, p = numbers
    if not o <= m <= p:
        raise ValueError(f"{ident}: estimates must satisfy optimistic <= most_likely <= pessimistic")
    if choice(task, "type", ("task", "milestone"), ident) == "milestone" and p:
        raise ValueError(f"{ident}: a milestone requires three zero durations")
    return o, m, p


def analyze(tasks):
    parents, children, order = task_graph(tasks, required=True)
    early, finish, late, slack, duration, depth, inputs = {}, {}, {}, {}, {}, {}, {}
    for ident in order:
        o, m, p = inputs[ident] = estimates(tasks[ident])
        duration[ident] = (o + 4 * m + p) / 6
        early[ident] = max((finish[parent] for parent in parents[ident]), default=0)
        finish[ident] = early[ident] + duration[ident]
        depth[ident] = max((depth[parent] + 1 for parent in parents[ident]), default=0)
    total = max(finish.values())
    for ident in reversed(order):
        late_finish = min((late[child] for child in children[ident]), default=total)
        late[ident] = late_finish - duration[ident]
        slack[ident] = late[ident] - early[ident]

    critical_parents = {
        ident: [parent for parent in parents[ident] if slack[parent] == slack[ident] == 0
                and finish[parent] == early[ident]]
        for ident in order
    }
    counts = {}
    for ident in order:
        counts[ident] = (sum(counts[parent] for parent in critical_parents[ident]) if parents[ident]
                         else int(slack[ident] == 0))
    ends = [ident for ident in order if not children[ident] and finish[ident] == total]
    path = [ends[0]]
    while critical_parents[path[-1]]:
        path.append(critical_parents[path[-1]][0])
    return (parents, order, inputs, duration, early, finish, late, slack, depth, critical_parents,
            total, list(reversed(path)), sum(counts[ident] for ident in ends))


def network(order, parents, depth, slack, critical_parents):
    rank = defaultdict(int)
    long_edges = [(parent, ident) for ident in order for parent in parents[ident]
                  if depth[ident] - depth[parent] > 1]
    lanes = {edge: 14 + i * 10 for i, edge in enumerate(long_edges)}
    top = 20 + len(lanes) * 10
    coords = {}
    for ident in order:
        column = depth[ident]
        coords[ident] = (20 + column * 222, top + rank[column] * 84)
        rank[column] += 1
    width, height = max(rank) * 222 + 214, max(rank.values()) * 84 + top - 8
    edges, nodes = [], []
    for index, ident in enumerate(order, 1):
        x, y = coords[ident]
        for parent in parents[ident]:
            px, py = coords[parent]
            flag = " critical" if parent in critical_parents[ident] else ""
            marker = "critical-arrow" if flag else "arrow"
            path = f"M{px + 172} {py + 27}"
            if (parent, ident) in lanes:
                # Keep edges that skip columns clear of intermediate nodes.
                lane = lanes[parent, ident]
                path += f" H{px + 187} V{lane} H{x - 15} V{y + 27} H{x}"
            else:
                middle = (px + 172 + x) // 2
                path += f" C{middle} {py + 27}, {middle} {y + 27}, {x} {y + 27}"
            edges.append(f'<path class="edge{flag}" marker-end="url(#{marker})" d="{path}"/>')
        label = ident if len(ident) <= 10 else ident[:9] + "…"
        flag = "critical" if slack[ident] == 0 else ""
        status = "Critical" if flag else "Has float"
        nodes.append(f'<g><title>{h(ident)} · {status}</title>'
                     f'<rect class="{flag}" x="{x}" y="{y}" width="172" height="54"/>'
                     f'<text x="{x+10}" y="{y+22}">#{index} · {h(label)}</text>'
                     f'<text class="secondary" x="{x+10}" y="{y+40}">{status}</text></g>')
    markers = "".join(
        f'<marker id="{name}" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="5" markerHeight="5" '
        f'orient="auto"><path style="fill:var(--{color})" d="M0 0L10 5L0 10z"/></marker>'
        for name, color in (("arrow", "text-muted"), ("critical-arrow", "violet-line"))
    )
    return scroll("PERT dependency network", f'<svg class="network" width="{width}" height="{height}" '
                  f'role="img" aria-labelledby="net-title net-desc"><title id="net-title">PERT dependency network</title>'
                  f'<desc id="net-desc">Arrows connect predecessors to successors. All critical edges are violet. '
                  f'The task table gives the full IDs and dependencies.</desc><defs>{markers}</defs>'
                  f'{"".join(edges)}{"".join(nodes)}</svg>', plot=True)


def render(data, project):
    tasks = records(data, "tasks", required=True)
    if not tasks:
        raise ValueError("PERT requires at least one task")
    unit = text(data, "duration_unit", "project", required=True)
    calendar = text(data, "calendar_assumption", "project", required=True)
    (parents, order, inputs, duration, early, finish, late, slack, depth,
     critical_parents, total, path, count) = analyze(tasks)
    rows = []
    for index, ident in enumerate(order, 1):
        task = tasks[ident]
        mode = choice(task, "work_mode", WORK_MODES, ident)
        rows.append((h(ident), str(index), h(task["title"]), WORK_MODES.get(mode, "Not supplied"), show(task, "owner"),
                     id_list(parents[ident]), *(fmt(x) for x in (*inputs[ident], duration[ident], early[ident],
                                                                finish[ident], late[ident], slack[ident])),
                     id_list(critical_parents[ident]), "Critical" if slack[ident] == 0 else "Has float",
                     show(task, "notes")))
    timings = table(f"Task timings in {unit}, rounded for display",
                    ("ID", "Node", "Task", "Work mode", "Owner", "Predecessors", "Optimistic", "Most likely",
                     "Pessimistic", "Expected", "Early start", "Early finish", "Late start", "Total float",
                     "Critical predecessors", "Path status", "Notes"), rows)
    body = (f'<section><h2>Critical path</h2><div class="metrics">'
            f'<div class="metric"><strong>{fmt(total)} {h(unit)}</strong><span>Expected network duration</span></div>'
            f'<div class="metric"><strong>{count}</strong><span>Critical path count</span></div></div>'
            f'<p><strong>One critical path:</strong> {" &rarr; ".join(map(h, path))}.</p>'
            f'<p>Calendar assumption: {h(calendar)}</p>'
            '<p class="note">Expected duration = (optimistic + 4 × most likely + pessimistic) / 6. '
            'Starts are relative to zero; dates, resource constraints, and actual AI execution are not modeled. '
            'This is a dependency-only estimate, not a deadline or probability forecast.</p></section>'
            '<section><h2>Dependency network</h2><p class="note">Read left to right. Columns show dependency depth, '
            'not elapsed time. Violet marks all critical paths.</p>'
            '<p><span class="chip chip-purple">Critical</span> <span class="chip chip-blue">Has float</span></p>'
            f'{network(order, parents, depth, slack, critical_parents)}</section>'
            f'<section><h2>Task timings</h2>{timings}</section>')
    return page(project, "PERT chart", body, CSS)


if __name__ == "__main__":
    run("Render an offline PERT dependency network.", render)
