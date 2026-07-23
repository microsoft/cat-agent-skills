#!/usr/bin/env python3
"""Build a self-contained HTML dashboard from a regulation-monitor run.

Consumes:
  --config  path to profile config.json (for profile name, topics, cadence)
  --items   path to a JSON file with shape {"items": [ ... ]}
  --output  path to write the HTML dashboard

Item schema (each entry in items[]):
  topic                   str  - one of the profile's watch_topics[].key
  jurisdiction            str  - e.g. "EU", "US-federal", "UK", "global"
  stage                   str  - proposed | in-consultation | passed |
                                  regulatory-guidance | in-force | litigation |
                                  withdrawn
  date                    str  - ISO date
  title                   str  - source's short title, verbatim
  summary                 str  - 1-2 sentence summary
  source_name             str  - publisher's short name
  source_url              str  - canonical public URL (http/https/mailto only;
                                  other schemes are dropped at render time)
  relevant_to_your_team   bool - team-relevance flag from Step 7

Uses only the Python standard library so it runs in restricted sandboxes.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGE_ORDER = [
    "proposed",
    "in-consultation",
    "passed",
    "regulatory-guidance",
    "in-force",
    "litigation",
    "withdrawn",
]

STAGE_COLORS = {
    "proposed": "#6b7280",
    "in-consultation": "#0ea5e9",
    "passed": "#2563eb",
    "regulatory-guidance": "#7c3aed",
    "in-force": "#059669",
    "litigation": "#dc2626",
    "withdrawn": "#9ca3af",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_url(value: Any) -> str:
    """Return the URL only if it uses a safe scheme (http/https/mailto).

    Prevents javascript:/data:/vbscript: injection when items are sourced
    from external content the skill did not author.
    """
    if not value:
        return ""
    text = str(value).strip()
    lowered = text.lower()
    if lowered.startswith(("http://", "https://", "mailto:")):
        return text
    return ""


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def stage_pill(stage: str) -> str:
    color = STAGE_COLORS.get(stage, "#374151")
    return (
        f'<span class="pill" style="background:{color}">'
        f'{esc(stage)}</span>'
    )


def relevant_badge(is_relevant: bool) -> str:
    if not is_relevant:
        return ""
    return (
        '<span class="badge" title="Matched your team\'s function-area keywords">'
        "team-relevant</span>"
    )


def build_html(config: dict[str, Any], items: list[dict[str, Any]]) -> str:
    profile_name = esc(config.get("profile_name", "regulation-monitor"))
    cadence = esc(config.get("cadence", "on demand"))
    window_days = config.get("window_days", 7)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    topic_name_by_key: dict[str, str] = {}
    for topic in config.get("watch_topics", []):
        topic_name_by_key[str(topic.get("key", ""))] = str(
            topic.get("name", topic.get("key", ""))
        )

    total = len(items)
    per_topic = Counter(item.get("topic", "") for item in items)
    team_relevant = sum(1 for item in items if item.get("relevant_to_your_team"))

    # Sort: team-relevant first, then stage order, then date desc.
    def sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
        stage_idx = (
            STAGE_ORDER.index(item.get("stage", ""))
            if item.get("stage") in STAGE_ORDER
            else len(STAGE_ORDER)
        )
        relevant_first = 0 if item.get("relevant_to_your_team") else 1
        # Sort dates descending by negating via string trick: prefix with '0' if
        # missing to sort last. We reverse-sort strings so newer ISO dates win.
        date_key = item.get("date") or "0000-00-00"
        return (relevant_first, stage_idx, date_key)

    sorted_items = sorted(items, key=sort_key)
    # Because dates should be newest-first within (relevance, stage), we sort
    # the date within each group by negating the string ordering. Simpler:
    # sort desc by date on a second pass while preserving stability.
    sorted_items.sort(
        key=lambda x: x.get("date") or "0000-00-00", reverse=True
    )
    sorted_items.sort(key=lambda x: sort_key(x)[:2])

    # KPI tiles
    tiles_html: list[str] = []
    tiles_html.append(_tile("Total items", str(total)))
    tiles_html.append(_tile("Team-relevant", str(team_relevant)))
    for topic in config.get("watch_topics", []):
        key = str(topic.get("key", ""))
        tiles_html.append(
            _tile(
                str(topic.get("name", key)),
                str(per_topic.get(key, 0)),
            )
        )

    # Rows
    rows_html: list[str] = []
    for item in sorted_items:
        topic_key = str(item.get("topic", ""))
        topic_display = topic_name_by_key.get(topic_key, topic_key or "—")
        title = esc(item.get("title", "(untitled)"))
        summary = esc(item.get("summary", ""))
        source_name = esc(item.get("source_name", ""))
        source_url = esc(safe_url(item.get("source_url", "")))
        source_link = (
            f'<a href="{source_url}" target="_blank" rel="noopener nofollow">{source_name}</a>'
            if source_url
            else source_name
        )
        rows_html.append(
            "<tr>"
            f"<td>{esc(item.get('date') or '—')}</td>"
            f"<td>{esc(topic_display)} {relevant_badge(bool(item.get('relevant_to_your_team')))}</td>"
            f"<td>{esc(item.get('jurisdiction') or '—')}</td>"
            f"<td>{stage_pill(str(item.get('stage', '')))}</td>"
            f"<td><div class=\"title\">{title}</div>"
            f"<div class=\"summary\">{summary}</div></td>"
            f"<td>{source_link}</td>"
            "</tr>"
        )

    if not rows_html:
        rows_html.append(
            '<tr><td colspan="6" class="empty">No significant developments this period.</td></tr>'
        )

    # Empty-topic callout: list any watch topic that produced zero items.
    topics_with_items = {str(item.get("topic", "")) for item in items}
    empty_topics: list[str] = []
    for topic in config.get("watch_topics", []):
        key = str(topic.get("key", ""))
        if key and key not in topics_with_items:
            empty_topics.append(str(topic.get("name", key)))

    empty_html = ""
    if empty_topics:
        rows = "".join(
            f"<li>{esc(name)} — No significant developments this period.</li>"
            for name in empty_topics
        )
        empty_html = (
            '<section class="empty-topics">'
            '<h2>Quiet this period</h2>'
            f'<ul>{rows}</ul>'
            "</section>"
        )

    style = _stylesheet()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Regulation Monitor — {profile_name}</title>
<style>{style}</style>
</head>
<body>
<header>
  <div class="brand">
    <div class="dot"></div>
    <div>
      <div class="eyebrow">Regulation Monitor</div>
      <h1>{profile_name}</h1>
    </div>
  </div>
  <div class="meta">
    <div><strong>Cadence</strong>&nbsp;{cadence}</div>
    <div><strong>Window</strong>&nbsp;last {esc(window_days)} days</div>
    <div><strong>Generated</strong>&nbsp;{esc(generated_at)}</div>
  </div>
</header>

<section class="tiles">
  {''.join(tiles_html)}
</section>

<section>
  <h2>Items</h2>
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Topic</th>
        <th>Jurisdiction</th>
        <th>Stage</th>
        <th>Title &amp; summary</th>
        <th>Source</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows_html)}
    </tbody>
  </table>
</section>

{empty_html}

<footer>
  <div>Regulation Monitor is a <strong>monitoring</strong> tool. Nothing on this dashboard is legal, tax, or compliance advice. Team-relevance is a keyword match, not an impact assessment.</div>
</footer>
</body>
</html>
"""


def _tile(label: str, value: str) -> str:
    return (
        '<div class="tile">'
        f'<div class="tile-value">{esc(value)}</div>'
        f'<div class="tile-label">{esc(label)}</div>'
        "</div>"
    )


def _stylesheet() -> str:
    # Kept simple and self-contained. No external assets.
    return """
:root {
  --bg:#f8fafc; --card:#ffffff; --ink:#0f172a; --muted:#64748b;
  --line:#e2e8f0; --accent:#4f46e5; --accent-2:#0ea5e9;
  --shadow:0 1px 2px rgba(15,23,42,.04), 0 1px 3px rgba(15,23,42,.06);
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--bg);color:var(--ink);
  font:14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;}
header{padding:24px 32px;background:linear-gradient(180deg,#ffffff, #f1f5f9);
  border-bottom:1px solid var(--line);display:flex;justify-content:space-between;
  align-items:flex-end;gap:24px;flex-wrap:wrap}
.brand{display:flex;gap:14px;align-items:center}
.brand .dot{width:12px;height:12px;border-radius:50%;
  background:linear-gradient(135deg,var(--accent),var(--accent-2));box-shadow:var(--shadow)}
.eyebrow{color:var(--muted);text-transform:uppercase;letter-spacing:.08em;
  font-size:11px;font-weight:600}
h1{margin:2px 0 0;font-size:22px;font-weight:600}
.meta{display:flex;gap:20px;color:var(--muted);font-size:12px;flex-wrap:wrap}
.meta strong{color:var(--ink);font-weight:600}

section{padding:24px 32px}
section h2{margin:0 0 12px;font-size:14px;text-transform:uppercase;
  letter-spacing:.06em;color:var(--muted);font-weight:600}

.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
  gap:12px;padding:16px 32px 0}
.tile{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:14px 16px;box-shadow:var(--shadow)}
.tile-value{font-size:22px;font-weight:600}
.tile-label{color:var(--muted);font-size:12px;margin-top:2px}

table{width:100%;border-collapse:collapse;background:var(--card);
  border:1px solid var(--line);border-radius:10px;overflow:hidden;box-shadow:var(--shadow)}
thead th{background:#f1f5f9;color:var(--muted);text-align:left;font-weight:600;
  padding:10px 12px;font-size:11px;text-transform:uppercase;letter-spacing:.06em;
  border-bottom:1px solid var(--line)}
tbody td{padding:12px;vertical-align:top;border-bottom:1px solid var(--line);
  font-size:13px}
tbody tr:last-child td{border-bottom:none}
.title{font-weight:600;margin-bottom:2px}
.summary{color:var(--muted)}
.empty{color:var(--muted);text-align:center;padding:24px}
.pill{color:#fff;padding:3px 8px;border-radius:999px;font-size:11px;
  font-weight:600;text-transform:lowercase}
.badge{display:inline-block;margin-left:8px;color:#3730a3;background:#eef2ff;
  padding:2px 8px;border-radius:999px;font-size:10px;font-weight:600;
  text-transform:lowercase;letter-spacing:.02em}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}

footer{padding:16px 32px 32px;color:var(--muted);font-size:11px}
.empty-topics ul{list-style:none;margin:0;padding:0;background:var(--card);
  border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow);
  overflow:hidden}
.empty-topics li{padding:10px 14px;border-bottom:1px solid var(--line);
  color:var(--muted);font-size:13px}
.empty-topics li:last-child{border-bottom:none}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    if not args.config.exists():
        print(f"config not found: {args.config}", file=sys.stderr)
        return 2
    if not args.items.exists():
        print(f"items not found: {args.items}", file=sys.stderr)
        return 2

    config = load_json(args.config)
    items_doc = load_json(args.items)
    raw_items = items_doc.get("items", []) if isinstance(items_doc, dict) else []
    if not isinstance(raw_items, list):
        print(
            f"items file must contain an 'items' list; got {type(raw_items).__name__}",
            file=sys.stderr,
        )
        return 2
    items = [item for item in raw_items if isinstance(item, dict)]
    dropped = len(raw_items) - len(items)
    if dropped:
        print(
            f"warning: dropped {dropped} non-dict entries from items[]",
            file=sys.stderr,
        )

    html_out = build_html(config, items)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_out, encoding="utf-8")
    print(str(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
