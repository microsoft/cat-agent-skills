from planning_html import (RISK_STYLE, badge, day, h, ids, page, records, risk_rating, run, show, table)


GROUPS = (
    ("risks", "Risks", "Uncertain events that may affect the plan.", "Mitigation", "mitigation"),
    ("assumptions", "Assumptions", "Planning beliefs to validate.", "Validation action", "validation_action"),
    ("issues", "Issues", "Problems that have already occurred.", "Resolution action", "resolution_action"),
    ("dependencies", "Dependencies", "Inputs, decisions, or deliverables needed from elsewhere.", "Next action", "next_action"),
)

GROUP_ACCENTS = ("blue", "teal", "purple", "pink")
CSS = """
.register-heading { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem; }
"""
def references(values, anchors, known):
    links = []
    for ident in values:
        label = h(ident)
        if ident in anchors:
            links.append(f'<a href="#{anchors[ident]}">{label}</a>')
        else:
            links.append(f"{label} (not in this register)" if known else label)
    return ", ".join(links) or "None"


def render(data, project):
    sets = {key: records(data, key) for key, *_ in GROUPS}
    if not any(key in data for key, *_ in GROUPS):
        raise ValueError("supply at least one RAID array (risks, assumptions, issues, dependencies)")
    tasks = records(data, "tasks")
    task_anchors = {ident: f"task-{number}" for number, ident in enumerate(tasks, 1)}
    risk_anchors = {ident: f"risk-{number}" for number, ident in enumerate(sets["risks"], 1)}
    as_of = day(data, "as_of", "project")
    cards, sections = [], []
    for (key, label, meaning, action, field), accent in zip(GROUPS, GROUP_ACCENTS):
        items = sets[key]
        cards.append(f'<a class="metric" href="#{key}"><strong>{len(items) if key in data else "—"}</strong>'
                     f'<span>{label} &darr;</span></a>')
        rows = []
        headings = ("ID", "Title", "Details", "Owner", "Status", action, "Due / review date", "Task IDs", "Related risk IDs")
        for ident, item in items.items():
            due = day(item, "due_date", ident)
            id_cell = h(ident)
            if key == "risks":
                id_cell = f'<span id="{risk_anchors[ident]}">{id_cell}</span>'
            task_refs = references(ids(item, "task_ids", ident), task_anchors, "tasks" in data)
            risk_refs = references(ids(item, "risk_ids", ident), risk_anchors, True)
            row = (id_cell, h(item["title"]), show(item, "details"), show(item, "owner"), show(item, "status"),
                   show(item, field), h(due or "Not supplied"),
                   task_refs if item.get("task_ids") is not None else "Not supplied",
                   risk_refs if item.get("risk_ids") is not None else "Not supplied")
            if key == "risks":
                likelihood, severity, level = risk_rating(item)
                row += (h(likelihood or "Not supplied"), h(severity or "Not supplied"), badge(level))
            rows.append(row)
        if key == "risks":
            headings += ("Likelihood", "Severity", "Rating")
        content = table(label, headings, rows) if rows else (
            "<p>No entries supplied.</p>" if key in data else "<p>This category was not supplied.</p>")
        count = "Not supplied" if key not in data else f'{len(items)} {"entry" if len(items) == 1 else "entries"}'
        sections.append(f'<section id="{key}"><div class="register-heading"><h2>{label}</h2>'
                        f'<span class="chip chip-{accent}">{count}</span></div><p class="note">{meaning}</p>{content}</section>')
    task_table = table("Referenced project tasks", ("Task ID", "Task"),
                       [(f'<span id="{task_anchors[ident]}">{h(ident)}</span>', h(task["title"]))
                        for ident, task in tasks.items()]) if tasks else ""
    tasks_section = f"<section><h2>Task reference</h2>{task_table}</section>" if task_table else ""
    body = (f'<section><h2>Register overview</h2><p class="note">As of: {h(as_of or "Not supplied")}. '
            'A dash means no data was supplied for that category.</p>'
            f'<nav class="metrics" aria-label="Register categories">{"".join(cards)}</nav></section>'
            f'{"".join(sections)}{tasks_section}')
    return page(project, "RAID register", body, RISK_STYLE + CSS)


if __name__ == "__main__":
    run("Render an offline risks, assumptions, issues, and dependencies register.", render)
