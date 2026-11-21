"""Canonical project planning design and renderer utilities; sync into each skill."""

import argparse
from collections import deque
from datetime import date
from decimal import Decimal
from html import escape
import json
from pathlib import Path
import re


WORK_MODES = {"human": "Human work", "ai-prep": "AI preparation", "human-review": "Human review"}
LIKELIHOODS = ("Very Likely", "Likely", "Possible", "Unlikely", "Very Unlikely")
SEVERITIES = ("Negligible", "Minor", "Moderate", "Significant", "Severe")
LEVELS = ("Low", "Low Med", "Medium", "Med Hi", "High")
POLICY = (
    (1, 2, 3, 4, 4),
    (0, 1, 2, 3, 4),
    (0, 1, 2, 3, 3),
    (0, 1, 1, 2, 3),
    (0, 0, 1, 2, 2),
)

STYLE = """
:root {
  color-scheme: light;
  --bg: #f7f9fd; --surface: #fff; --surface2: #f0f4fb; --border: #dce4ef;
  --text: #222c43; --text-head: #141d34; --text-dim: #465570; --text-muted: #596a83;
  --blue: #2456b8; --blue-tint: #e9f1ff;
  --teal: #08736e; --teal-tint: #dcf6ef;
  --purple: #5b2ab5; --purple-tint: #f1eafe;
  --pink: #9c216a; --pink-tint: #fce8f4;
  --amber: #8c5700; --amber-dim: #fff3da;
  --cyan-line: #0fafff; --blue-line: #2764e7; --violet-line: #8b52f4; --pink-line: #f24a9d;
  --amber-line: #ffb357;
  --text-fill-opacity: 90%;
  --cyan-glow: rgb(15 175 255 / 24%); --blue-glow: rgb(39 100 231 / 20%);
  --violet-glow: rgb(139 82 244 / 22%); --pink-glow: rgb(242 74 157 / 22%); --amber-glow: rgb(255 179 87 / 32%);
  --plot-bg: #f8faff; --plot-dot: #d5dfed;
  --accent: linear-gradient(100deg, var(--cyan-line), var(--blue-line) 32%,
    var(--violet-line) 66%, var(--pink-line));
  --radius: 18px; --shadow: 0 8px 26px rgb(34 54 100 / 7%);
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font: 15px/1.55 system-ui, sans-serif;
  padding: 0 clamp(.75rem, 3vw, 2rem); }
main { max-width: 1260px; margin: 0 auto; padding: clamp(1rem, 3vw, 2.5rem) 0 4rem; overflow-wrap: anywhere; }
.hero { position: relative; overflow: hidden; border: 1px solid var(--violet-line); border-radius: var(--radius);
  background: linear-gradient(112deg, #fff 38%, #e9faf8 62%, #eef0ff 80%, #fcebf7);
  box-shadow: 0 0 20px var(--violet-glow), 18px 10px 30px var(--pink-glow);
  padding: clamp(1.2rem, 4vw, 2.6rem); }
.hero::before { content: ''; position: absolute; inset: 0 0 auto; height: 3px; background: var(--accent); }
.hero .eyebrow { margin: 0 0 .45rem; }
h1, h2, h3 { color: var(--text-head); line-height: 1.18; }
h1 { font-size: clamp(1.85rem, 5vw, 3.1rem); font-weight: 750; letter-spacing: -.045em; }
h2 { font-size: clamp(1.2rem, 2.8vw, 1.48rem); letter-spacing: -.025em; }
main > section { --panel-line: var(--cyan-line); --panel-glow: var(--cyan-glow); margin-top: 1.4rem;
  background: var(--surface); border: 1px solid var(--panel-line);
  border-radius: var(--radius); box-shadow: 0 0 18px var(--panel-glow), var(--shadow);
  padding: clamp(.85rem, 2.6vw, 1.65rem); }
main > section:nth-of-type(3n + 2) { --panel-line: var(--violet-line); --panel-glow: var(--violet-glow); }
main > section:nth-of-type(3n) { --panel-line: var(--pink-line); --panel-glow: var(--pink-glow); }
p { margin: .55rem 0; }
.eyebrow { color: var(--purple); font-weight: 750; font-size: .7rem; text-transform: uppercase; letter-spacing: .12em; }
.note { color: var(--text-dim); }
.metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 9rem), 1fr));
  gap: .6rem; margin-block: .85rem; }
.metric { --metric-fill: var(--blue-tint); --metric-glow: var(--blue-glow); display: block;
  min-width: 0; border: 1.5px solid var(--blue-line); border-radius: 12px; padding: .7rem .85rem;
  background-color: var(--metric-fill);
  background-color: color-mix(in srgb, var(--metric-fill) var(--text-fill-opacity), transparent);
  color: var(--text-head);
  box-shadow: 0 0 16px var(--metric-glow); }
.metric:nth-child(3n + 2) { --metric-fill: var(--teal-tint); border-color: var(--cyan-line); --metric-glow: var(--cyan-glow); }
.metric:nth-child(3n) { --metric-fill: var(--purple-tint); border-color: var(--violet-line); --metric-glow: var(--violet-glow); }
.metric:nth-child(4n) { --metric-fill: var(--pink-tint); border-color: var(--pink-line); --metric-glow: var(--pink-glow); }
.metric strong { display: block; font-size: clamp(1.2rem, 3vw, 1.65rem); line-height: 1.2;
  font-variant-numeric: tabular-nums; letter-spacing: -.025em; }
.metric span { display: block; color: var(--text-dim); font-size: .79rem; margin-top: .22rem; }
a.metric { text-decoration: none; }
a.metric:hover span, a.metric:focus-visible span { text-decoration: underline; }
.warning { border-left: 3px solid var(--amber); background: var(--amber-dim); border-radius: 10px;
  background-color: color-mix(in srgb, var(--amber-dim) var(--text-fill-opacity), transparent);
  padding: .55rem 1rem; margin-top: .75rem; }
.warning ul { padding-left: 1.5rem; }
.scroll { overflow-x: auto; margin: .8rem 0 .25rem; border: 1px solid var(--border); border-radius: 12px; }
.chart-frame { border: 1.5px solid var(--panel-line, var(--blue-line));
  box-shadow: 0 0 18px var(--panel-glow, var(--blue-glow)); }
.plot-surface { background: radial-gradient(circle, var(--plot-dot) 1px, transparent 1px) 0 0 / 14px 14px, var(--plot-bg); }
.chip { display: inline-block; padding: .15rem .55rem; border-radius: 999px;
  box-shadow: inset 0 0 0 1.5px var(--chip-line, var(--border)), 0 0 10px var(--chip-glow, transparent);
  background: var(--chip-fill, var(--surface2));
  background-color: color-mix(in srgb, var(--chip-fill, var(--surface2)) var(--text-fill-opacity), transparent);
  color: var(--chip-ink, var(--text-dim));
  font-size: .75rem; font-weight: 700; }
.chip-blue { --chip-fill: var(--blue-tint); --chip-ink: var(--blue); --chip-line: var(--blue-line); --chip-glow: var(--blue-glow); }
.chip-teal { --chip-fill: var(--teal-tint); --chip-ink: var(--teal); --chip-line: var(--cyan-line); --chip-glow: var(--cyan-glow); }
.chip-purple { --chip-fill: var(--purple-tint); --chip-ink: var(--purple); --chip-line: var(--violet-line); --chip-glow: var(--violet-glow); }
.chip-pink { --chip-fill: var(--pink-tint); --chip-ink: var(--pink); --chip-line: var(--pink-line); --chip-glow: var(--pink-glow); }
:focus-visible { outline: 2px solid var(--blue); outline-offset: -2px; }
a { color: var(--blue); text-underline-offset: .15em; }
table { width: 100%; border-collapse: collapse; font-size: .85rem; }
caption { text-align: left; padding: .55rem .85rem; color: var(--text-dim); background: var(--surface); }
th, td { min-width: 5rem; padding: .65rem .82rem; border-top: 1px solid var(--border);
  max-width: 24rem; overflow-wrap: break-word; text-align: left; vertical-align: top; }
thead th { background: var(--surface2); color: var(--text-head); font-size: .76rem; letter-spacing: .015em; }
tbody td, tbody th { background: var(--surface); }
tbody td:nth-child(2) { min-width: 9rem; }
"""

RISK_STYLE = """
.level-0 { --risk-fill: #56ae58; --risk-ink: #142519; }
.level-1 { --risk-fill: #a8d66b; --risk-ink: #142519; }
.level-2 { --risk-fill: #fff078; --risk-ink: #2d260e; }
.level-3 { --risk-fill: #ffc059; --risk-ink: #30200c; }
.level-4 { --risk-fill: #9b241a; --risk-ink: #ffffff; }
.level-unknown { --risk-fill: var(--surface2); --risk-ink: var(--text-dim); }
.level { display: inline-block; padding: .15rem .55rem; border-radius: 999px; font-weight: 700;
  background: var(--risk-fill); color: var(--risk-ink); }
.level:not(.level-unknown) {
  background-color: color-mix(in srgb, var(--risk-fill) var(--text-fill-opacity), transparent);
}
"""


def h(value):
    return escape(str(value), quote=True)


def text(obj, key, context, *, required=False):
    value = obj.get(key)
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise ValueError(f"{context}: {key} must be a nonblank string or null")
    if required and value is None:
        raise ValueError(f"{context}: {key} is required")
    return value


def show(obj, key, missing="Not supplied"):
    return h(text(obj, key, obj.get("id", "project")) or missing)


def choice(obj, key, options, context):
    value = text(obj, key, context)
    if value is not None and value not in options:
        raise ValueError(f"{context}: {key} must be one of {', '.join(options)}")
    return value


def day(obj, key, context):
    value = text(obj, key, context)
    if value is not None:
        try:
            if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
                return date.fromisoformat(value)
        except ValueError:
            pass
        raise ValueError(f"{context}: {key} must be a valid YYYY-MM-DD date")
    return None


def ids(obj, key, context, *, required=False):
    value = obj.get(key)
    if value is None and not required:
        return []
    if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
        raise ValueError(f"{context}: {key} must be an array of nonblank IDs (use [] for none)")
    if len(set(value)) != len(value):
        raise ValueError(f"{context}: duplicate IDs in {key}")
    return value


def records(data, key, *, required=False):
    if key not in data and not required:
        return {}
    items = data.get(key)
    if not isinstance(items, list):
        raise ValueError(f"{key} must be an array of records")
    result = {}
    for index, row in enumerate(items, 1):
        if not isinstance(row, dict):
            raise ValueError(f"{key} row {index} must be an object")
        ident = text(row, "id", f"{key} row {index}", required=True)
        if ident in result:
            raise ValueError(f"duplicate ID {ident} in {key}")
        text(row, "title", ident, required=True)
        result[ident] = row
    return result


def task_graph(tasks, *, required=False):
    predecessors = {}
    successors = {ident: [] for ident in tasks}
    for ident, task in tasks.items():
        predecessors[ident] = ids(task, "predecessors", ident, required=required)
        for parent in predecessors[ident]:
            if parent not in tasks:
                raise ValueError(f"{ident}: unknown predecessor {parent}")
            successors[parent].append(ident)
    remaining = {ident: len(parents) for ident, parents in predecessors.items()}
    queue = deque(ident for ident in tasks if not remaining[ident])
    order = []
    while queue:
        ident = queue.popleft()
        order.append(ident)
        for child in successors[ident]:
            remaining[child] -= 1
            if not remaining[child]:
                queue.append(child)
    if len(order) != len(tasks):
        blocked = ", ".join(ident for ident in tasks if remaining[ident])
        raise ValueError(f"dependency cycle; cannot order: {blocked}")
    return predecessors, successors, order


def risk_rating(item):
    ident = item["id"]
    likelihood = choice(item, "likelihood", LIKELIHOODS, ident)
    severity = choice(item, "severity", SEVERITIES, ident)
    level = None if likelihood is None or severity is None else POLICY[
        LIKELIHOODS.index(likelihood)][SEVERITIES.index(severity)]
    return likelihood, severity, level


def badge(level):
    if level is None:
        return '<span class="level level-unknown">Unassessed</span>'
    return f'<span class="level level-{level}">{LEVELS[level]}</span>'


def id_list(values):
    return ", ".join(map(h, values)) or "None"


def scroll(label, content, *, chart=False, plot=False):
    styles = "scroll" + (" chart-frame" if chart or plot else "") + (" plot-surface" if plot else "")
    return f'<div class="{styles}" tabindex="0" role="region" aria-label="{h(label)}">{content}</div>'


def table(caption, headings, rows):
    head = "".join(f'<th scope="col">{h(name)}</th>' for name in headings)
    body = "".join(
        f'<tr><th scope="row">{first}</th>{"".join(f"<td>{cell}</td>" for cell in rest)}</tr>'
        for first, *rest in rows
    )
    return scroll(caption, f'<table><caption>{h(caption)}</caption>'
                  f'<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>')


def page(project, kind, body, css=""):
    title = h(project)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | {kind}</title><style>{STYLE}{css}</style></head>
<body><main><header class="hero"><p class="eyebrow">Project planning &nbsp;/&nbsp; {kind}</p><h1>{title}</h1></header>
{body}
</main></body></html>
"""


def reject_constant(token):
    raise ValueError(f"non-finite JSON number: {token}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def run(description, render):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input", type=Path, help="UTF-8 project JSON")
    parser.add_argument("output", type=Path, help="HTML destination (parent directory must exist)")
    args = parser.parse_args()
    try:
        if args.output.suffix.lower() != ".html" or args.input.resolve() == args.output.resolve():
            raise ValueError("choose a separate .html output file")
        data = json.loads(args.input.read_text(encoding="utf-8-sig"), parse_float=Decimal,
                          parse_constant=reject_constant, object_pairs_hook=unique_object)
        if not isinstance(data, dict):
            raise ValueError("project JSON must be an object")
        document = render(data, text(data, "project", "project", required=True))
        args.output.write_text(document, encoding="utf-8")
    except (OSError, ValueError) as error:
        parser.exit(2, f"{parser.prog}: {error}\n")
