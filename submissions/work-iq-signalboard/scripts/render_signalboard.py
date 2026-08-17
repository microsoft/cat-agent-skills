#!/usr/bin/env python3
"""Validate Work IQ counts and render a self-contained Signalboard.

Usage:
    python /absolute/path/scripts/render_signalboard.py safe-signalboard.json \
        --out /app/created/work-iq-signalboard.html
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import sys
from pathlib import Path
from typing import Any


SOURCE_KEYS = ("calendar", "mail", "teams")
ACTIVITY_KEYS = (
    "meeting_days",
    "meetings",
    "meeting_hours",
    "emails_sent",
    "emails_received",
    "teams_chat_messages",
    "teams_channel_messages",
)
DAY_KEYS = ("mon", "tue", "wed", "thu", "fri")
TIME_KEYS = ("morning", "midday", "afternoon", "evening")
WEEKLY_KEYS = ("meetings", "emails_sent", "teams_chats")

COLORS = {
    "calendar": "#2563eb",
    "mail": "#14b8a6",
    "teams": "#7c3aed",
}

DISPLAY = {
    "calendar": "Calendar",
    "mail": "Mail",
    "teams": "Teams",
    "mon": "Mon",
    "tue": "Tue",
    "wed": "Wed",
    "thu": "Thu",
    "fri": "Fri",
    "morning": "Morning",
    "midday": "Midday",
    "afternoon": "Afternoon",
    "evening": "Evening",
}


class ValidationError(ValueError):
    """A closed-schema or reconciliation violation."""


def _exact_keys(value: Any, expected: tuple[str, ...], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must be an object")
    actual = set(value)
    wanted = set(expected)
    if actual != wanted:
        missing = ", ".join(sorted(wanted - actual)) or "none"
        extra = ", ".join(sorted(actual - wanted)) or "none"
        raise ValidationError(f"{path} keys differ; missing: {missing}; extra: {extra}")
    return value


def _enum(value: Any, allowed: tuple[str, ...], path: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ValidationError(f"{path} must be one of: {', '.join(allowed)}")
    return value


def _count(value: Any, path: str, maximum: int = 100000) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise ValidationError(f"{path} must be an integer from 0 to {maximum}")
    return value


def _hours(value: Any, path: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{path} must be a number")
    if not 0 <= value <= 1000 or value * 2 != int(value * 2):
        raise ValidationError(f"{path} must be 0..1000 in half-hour steps")
    return value


def _levels(value: Any, path: str) -> list[int]:
    if not isinstance(value, list) or len(value) != len(TIME_KEYS):
        raise ValidationError(f"{path} must contain four levels")
    for index, item in enumerate(value):
        if isinstance(item, bool) or not isinstance(item, int) or not 0 <= item <= 3:
            raise ValidationError(f"{path}[{index}] must be an integer from 0 to 3")
    return value


def _weeks(value: Any, path: str) -> list[int]:
    if not isinstance(value, list) or len(value) != 4:
        raise ValidationError(f"{path} must contain exactly four weekly counts")
    for index, item in enumerate(value):
        _count(item, f"{path}[{index}]")
    return value


def validate(doc: Any) -> dict[str, Any]:
    top = _exact_keys(
        doc,
        ("period", "coverage", "activity", "calendar_rhythm", "weekly_counts"),
        "root",
    )
    _enum(top["period"], ("last-4-weeks",), "period")

    coverage = _exact_keys(top["coverage"], SOURCE_KEYS, "coverage")
    _enum(coverage["calendar"], ("complete", "unavailable"), "coverage.calendar")
    _enum(coverage["mail"], ("complete", "unavailable"), "coverage.mail")
    _enum(
        coverage["teams"],
        ("chats-only", "chats-and-channels", "unavailable"),
        "coverage.teams",
    )
    if all(value == "unavailable" for value in coverage.values()):
        raise ValidationError("at least one source must be available")

    activity = _exact_keys(top["activity"], ACTIVITY_KEYS, "activity")
    _count(activity["meeting_days"], "activity.meeting_days", 28)
    for key in (
        "meetings",
        "emails_sent",
        "emails_received",
        "teams_chat_messages",
        "teams_channel_messages",
    ):
        _count(activity[key], f"activity.{key}")
    _hours(activity["meeting_hours"], "activity.meeting_hours")

    if activity["meeting_days"] > activity["meetings"]:
        raise ValidationError("activity.meeting_days cannot exceed activity.meetings")
    if activity["meetings"] > 0 and activity["meeting_days"] == 0:
        raise ValidationError("activity.meeting_days must be positive when meetings exist")
    if activity["meetings"] == 0 and activity["meeting_hours"] != 0:
        raise ValidationError("activity.meeting_hours must be 0 when meetings is 0")

    rhythm = _exact_keys(top["calendar_rhythm"], DAY_KEYS, "calendar_rhythm")
    for day in DAY_KEYS:
        _levels(rhythm[day], f"calendar_rhythm.{day}")
    if activity["meetings"] == 0 and any(
        level for day in DAY_KEYS for level in rhythm[day]
    ):
        raise ValidationError("calendar_rhythm must be 0 when meetings is 0")

    weekly = _exact_keys(top["weekly_counts"], WEEKLY_KEYS, "weekly_counts")
    for key in WEEKLY_KEYS:
        _weeks(weekly[key], f"weekly_counts.{key}")

    if coverage["calendar"] == "unavailable":
        if any(activity[key] != 0 for key in ("meeting_days", "meetings", "meeting_hours")):
            raise ValidationError("calendar activity must be 0 when Calendar is unavailable")
        if any(level for day in DAY_KEYS for level in rhythm[day]):
            raise ValidationError("calendar_rhythm must be 0 when Calendar is unavailable")
    if coverage["mail"] == "unavailable" and any(
        activity[key] != 0 for key in ("emails_sent", "emails_received")
    ):
        raise ValidationError("mail activity must be 0 when Mail is unavailable")
    if coverage["teams"] == "unavailable" and any(
        activity[key] != 0 for key in ("teams_chat_messages", "teams_channel_messages")
    ):
        raise ValidationError("Teams activity must be 0 when Teams is unavailable")
    if coverage["teams"] == "chats-only" and activity["teams_channel_messages"] != 0:
        raise ValidationError("teams_channel_messages must be 0 for chats-only coverage")
    reconciliations = {
        "meetings": activity["meetings"],
        "emails_sent": activity["emails_sent"],
        "teams_chats": activity["teams_chat_messages"],
    }
    for key, total in reconciliations.items():
        if sum(weekly[key]) != total:
            raise ValidationError(
                f"weekly_counts.{key} sums to {sum(weekly[key])}, expected {total}"
            )

    return json.loads(json.dumps(top))


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def fmt_number(value: int | float) -> str:
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.1f}"
    return f"{int(value):,}"


def data_uri(path: Path) -> str:
    try:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    except OSError as exc:
        raise ValidationError(f"could not read bundled asset {path}: {exc}") from exc
    return f"data:image/webp;base64,{encoded}"


def human_list(items: list[str]) -> str:
    if not items:
        return "Work IQ"
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def source_names(coverage: dict[str, str]) -> list[str]:
    names: list[str] = []
    if coverage["calendar"] != "unavailable":
        names.append("Calendar")
    if coverage["mail"] != "unavailable":
        names.append("mail")
    if coverage["teams"] != "unavailable":
        names.append("Teams chats" if coverage["teams"] == "chats-only" else "Teams")
    return names


def coverage_note(coverage: dict[str, str]) -> str:
    labels = []
    for key in SOURCE_KEYS:
        state = coverage[key]
        if key == "teams" and state == "chats-only":
            labels.append("Teams chats")
        elif state == "unavailable":
            labels.append(f"{DISPLAY[key]}: No data")
        else:
            labels.append(DISPLAY[key])
    return " · ".join(labels)


def source_card(key: str, coverage: dict[str, str], activity: dict[str, Any]) -> str:
    state = coverage[key]
    unavailable = state == "unavailable"
    if unavailable:
        value, unit, detail = "No data", "", "Source unavailable in this run"
    elif key == "calendar":
        value, unit = fmt_number(activity["meetings"]), "meetings"
        detail = f'{fmt_number(activity["meeting_hours"])}h across {activity["meeting_days"]} days'
    elif key == "mail":
        value, unit = fmt_number(activity["emails_sent"]), "sent"
        detail = f'{fmt_number(activity["emails_received"])} received'
    else:
        value, unit = fmt_number(activity["teams_chat_messages"]), "chat messages"
        if state == "chats-and-channels":
            detail = f'{fmt_number(activity["teams_channel_messages"])} channel messages'
        else:
            detail = "Chats only · channels not counted"
    class_name = "source-card unavailable" if unavailable else "source-card"
    return f"""
      <article class="{class_name}" style="--source:{COLORS[key]}">
        <div class="source-top"><span>{DISPLAY[key]}</span><i></i></div>
        <strong>{esc(value)}</strong><b>{esc(unit)}</b>
        <div class="source-detail">{esc(detail)}</div>
      </article>"""


def rhythm_html(rhythm: dict[str, list[int]], available: bool) -> str:
    if not available:
        return '<div class="empty-state"><strong>No data</strong><span>Calendar was unavailable.</span></div>'
    rows = []
    for day in DAY_KEYS:
        cells = "".join(
            f'<td title="{DISPLAY[day]} {DISPLAY[TIME_KEYS[index]]}: level {level}">'
            f'<span class="heat level-{level}" aria-hidden="true"></span>'
            f'<span class="sr-only">Level {level}</span></td>'
            for index, level in enumerate(rhythm[day])
        )
        rows.append(f'<tr><th scope="row">{DISPLAY[day]}</th>{cells}</tr>')
    headings = "".join(f'<th scope="col">{DISPLAY[key]}</th>' for key in TIME_KEYS)
    return (
        '<table class="rhythm"><caption class="sr-only">Relative scheduled meeting '
        'minutes by weekday and time band, from level 0 to 3.</caption>'
        '<thead><tr><th scope="col"><span class="sr-only">Weekday</span></th>'
        f"{headings}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def mail_flow_html(activity: dict[str, int], available: bool) -> str:
    if not available:
        return '<div class="empty-state"><strong>No data</strong><span>Mail was unavailable.</span></div>'
    sent = activity["emails_sent"]
    received = activity["emails_received"]
    total = sent + received
    sent_share = 0 if total == 0 else sent / total * 100
    received_share = 0 if total == 0 else 100 - sent_share
    sent_width = 0 if sent == 0 else max(1, sent_share)
    received_width = 0 if received == 0 else max(1, received_share)
    return f"""
      <div class="mail-total"><strong>{fmt_number(total)}</strong><span>messages moved</span></div>
      <ul class="mail-flow">
        <li><div><span>Sent</span><b>{fmt_number(sent)}</b></div><div class="flow-track"><i style="width:{sent_width:.2f}%;background:#2563eb"></i></div></li>
        <li><div><span>Received</span><b>{fmt_number(received)}</b></div><div class="flow-track"><i style="width:{received_width:.2f}%;background:#14b8a6"></i></div></li>
      </ul>"""


def weekly_html(doc: dict[str, Any]) -> str:
    coverage = doc["coverage"]
    activity = doc["activity"]
    series = (
        ("calendar", "Meetings", "meetings", activity["meetings"]),
        ("mail", "Sent mail", "emails_sent", activity["emails_sent"]),
        ("teams", "Teams chats", "teams_chats", activity["teams_chat_messages"]),
    )
    rows = []
    for source, label, key, total in series:
        available = coverage[source] != "unavailable"
        values = doc["weekly_counts"][key]
        maximum = max(values) if available and any(values) else 1
        cells = []
        for index, value in enumerate(values):
            height = 0 if not available or value == 0 else max(4, value / maximum * 48)
            cells.append(
                f'<li><span>W{index + 1}</span><strong>'
                f'{fmt_number(value) if available else "—"}</strong>'
                f'<i style="height:{height}px"></i></li>'
            )
        status = f"{fmt_number(total)} total" if available else "No data"
        row_class = "week-row" if available else "week-row unavailable"
        rows.append(
            f'<div class="{row_class}" style="--series:{COLORS[source]}">'
            f'<div class="week-name"><span>{label}</span><b>{status}</b></div>'
            f'<ol>{"".join(cells)}</ol></div>'
        )
    return "".join(rows)


def observations(doc: dict[str, Any]) -> list[str]:
    coverage = doc["coverage"]
    activity = doc["activity"]
    notes: list[str] = []
    if coverage["calendar"] != "unavailable":
        notes.append(
            f'{fmt_number(activity["meetings"])} meetings filled '
            f'{fmt_number(activity["meeting_hours"])} hours across '
            f'{activity["meeting_days"]} calendar days.'
        )
    if coverage["mail"] != "unavailable":
        sent, received = activity["emails_sent"], activity["emails_received"]
        notes.append(f"Mail moved {fmt_number(sent)} sent and {fmt_number(received)} received messages.")
    if coverage["teams"] != "unavailable":
        if coverage["teams"] == "chats-only":
            notes.append(
                f'{fmt_number(activity["teams_chat_messages"])} Teams chat messages were counted; channel posts were outside this run.'
            )
        else:
            notes.append(
                f'{fmt_number(activity["teams_chat_messages"])} chat messages and '
                f'{fmt_number(activity["teams_channel_messages"])} channel messages were counted.'
            )
    return notes


def reflection(doc: dict[str, Any]) -> str:
    coverage = doc["coverage"]
    activity = doc["activity"]
    clauses: list[str] = []

    if coverage["calendar"] != "unavailable":
        clauses.append(
            f'The calendar logged {fmt_number(activity["meetings"])} meetings and '
            f'{fmt_number(activity["meeting_hours"])} hours across '
            f'{activity["meeting_days"]} days'
        )
    if coverage["mail"] != "unavailable":
        sent = activity["emails_sent"]
        received = activity["emails_received"]
        clauses.append(
            f'mail moved {fmt_number(sent + received)} messages '
            f'({fmt_number(sent)} sent, {fmt_number(received)} received)'
        )
    if coverage["teams"] != "unavailable":
        chats = activity["teams_chat_messages"]
        if coverage["teams"] == "chats-only":
            clauses.append(
                f'Teams counted {fmt_number(chats)} chat messages, with channels '
                "outside the frame"
            )
        else:
            clauses.append(
                f'Teams counted {fmt_number(chats)} chat messages and '
                f'{fmt_number(activity["teams_channel_messages"])} channel messages'
            )

    evidence = "; ".join(clauses) + "."
    perspective = (
        "These signals describe motion, not meaning—useful context, never a "
        "verdict on the work."
    )
    if coverage["mail"] != "unavailable" and (
        activity["emails_sent"] + activity["emails_received"]
    ):
        aside = "The inbox, naturally, has declined to be this philosophical."
    elif coverage["teams"] != "unavailable" and (
        activity["teams_chat_messages"] + activity["teams_channel_messages"]
    ):
        aside = "Teams has probably opened a thread about the distinction."
    elif coverage["calendar"] != "unavailable" and activity["meetings"]:
        aside = "The calendar has pencilled in time to discuss the distinction."
    else:
        aside = "For once, the dashboard has chosen a respectful indoor voice."
    return f"{evidence} {perspective} {aside}"


def coverage_html(coverage: dict[str, str]) -> str:
    items = []
    for key in SOURCE_KEYS:
        state = coverage[key]
        if state == "unavailable":
            label, css = "No data", "unavailable"
        elif key == "teams" and state == "chats-only":
            label, css = "Chats only", ""
        elif key == "teams":
            label, css = "Chats + channels", ""
        else:
            label, css = "Counted", ""
        items.append(
            f'<li class="{css}" style="--receipt:{COLORS[key]}"><span>{DISPLAY[key]}</span><strong>{label}</strong></li>'
        )
    return f'<ul class="coverage-grid">{"".join(items)}</ul>'


def build_html(doc: dict[str, Any], asset_root: Path) -> str:
    hero = data_uri(asset_root / "signalboard-hero.webp")
    tokens = data_uri(asset_root / "work-mode-tokens.webp")
    coverage = doc["coverage"]
    available_names = source_names(coverage)
    cards = "".join(source_card(key, coverage, doc["activity"]) for key in SOURCE_KEYS)
    note_items = "".join(f"<li>{esc(item)}</li>" for item in observations(doc))
    reflection_text = reflection(doc)
    counted = len(available_names)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Work IQ Signalboard</title>
<style>
:root{{--canvas:#f7f2ea;--paper:#fffdf9;--ink:#10213b;--muted:#657089;--line:#dcd8cf;--blue:#2563eb;--teal:#14b8a6;--violet:#7c3aed;--coral:#fb7185;--shadow:0 18px 50px rgba(16,33,59,.11);}}
*{{box-sizing:border-box}}
.sr-only{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;}}
html{{background:var(--canvas);color:var(--ink);font-family:Aptos,"Segoe UI",Arial,sans-serif;}}
body{{margin:0;background:radial-gradient(circle at 8% 2%,rgba(37,99,235,.08),transparent 24rem),var(--canvas);}}
.page{{width:min(1180px,calc(100% - 32px));margin:0 auto;padding:22px 0 56px;}}
.hero{{min-height:390px;overflow:hidden;border:1px solid rgba(16,33,59,.14);border-radius:30px;background:var(--paper);box-shadow:var(--shadow);display:grid;grid-template-columns:42% 58%;}}
.hero-copy{{z-index:2;padding:52px 0 42px 48px;display:flex;flex-direction:column;align-items:flex-start;justify-content:center;}}
.pulse-badge{{display:inline-flex;gap:8px;align-items:center;margin-bottom:24px;padding:7px 11px;border:1px solid rgba(20,184,166,.35);border-radius:999px;background:rgba(20,184,166,.09);font:700 11px/1 Consolas,monospace;text-transform:uppercase;letter-spacing:.08em;color:#087f74;}}
.pulse-badge i{{width:7px;height:7px;border-radius:50%;background:var(--teal);box-shadow:0 0 0 4px rgba(20,184,166,.14);}}
.eyebrow,.section-kicker{{font:700 11px/1.2 Consolas,"Courier New",monospace;text-transform:uppercase;letter-spacing:.16em;color:var(--blue);}}
h1{{max-width:560px;margin:0;font:800 clamp(40px,6vw,76px)/.91 "Arial Rounded MT Bold","Trebuchet MS",sans-serif;letter-spacing:-.055em;}}
.hero-copy p{{max-width:420px;margin:22px 0 24px;color:var(--muted);font-size:17px;line-height:1.5;}}
.coverage-note{{max-width:440px;padding-top:15px;border-top:1px solid var(--line);font:600 11px/1.55 Consolas,monospace;color:var(--ink);}}
.hero-art{{position:relative;min-height:390px;}}.hero-art img{{position:absolute;width:136%;height:100%;left:-32%;top:0;object-fit:cover;object-position:center right;}}
.section{{margin-top:22px;}}
.source-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;}}
.source-card{{position:relative;min-height:176px;padding:20px;border-radius:20px;background:var(--paper);border:1px solid rgba(16,33,59,.13);box-shadow:0 10px 26px rgba(16,33,59,.07);overflow:hidden;}}
.source-card:after{{content:"";position:absolute;width:92px;height:92px;border-radius:50%;right:-34px;bottom:-38px;background:color-mix(in srgb,var(--source) 18%,transparent);}}
.source-card.unavailable{{background:#f2efe9;color:#737b89;box-shadow:none;}}.source-card.unavailable:after{{display:none;}}
.source-top{{display:flex;align-items:center;justify-content:space-between;color:var(--muted);font:700 11px/1 Consolas,monospace;text-transform:uppercase;letter-spacing:.1em;}}.source-top i{{width:24px;height:6px;border-radius:99px;background:var(--source);}}
.source-card strong{{display:inline-block;margin-top:28px;font:800 29px/1 "Arial Rounded MT Bold","Trebuchet MS",sans-serif;}}.source-card>b{{margin-left:7px;font-size:12px;}}
.source-detail{{position:relative;z-index:1;margin-top:13px;color:var(--muted);font-size:12px;}}
.dashboard-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px;}}
.panel{{background:var(--paper);border:1px solid rgba(16,33,59,.13);border-radius:24px;padding:25px;box-shadow:0 12px 32px rgba(16,33,59,.07);}}
.panel-head{{display:flex;align-items:end;justify-content:space-between;gap:18px;margin-bottom:22px;}}.panel h2{{margin:6px 0 0;font:800 25px/1 "Arial Rounded MT Bold","Trebuchet MS",sans-serif;letter-spacing:-.025em;}}.panel-head p{{max-width:250px;margin:0;color:var(--muted);font-size:12px;text-align:right;}}
.mail-total{{display:flex;align-items:baseline;gap:8px;margin-bottom:19px;}}.mail-total strong{{font:800 34px/1 "Arial Rounded MT Bold","Trebuchet MS",sans-serif;}}.mail-total span{{color:var(--muted);font-size:12px;}}
.mail-flow{{list-style:none;margin:0;padding:0;display:grid;gap:18px;}}.mail-flow li>div:first-child{{display:flex;justify-content:space-between;margin-bottom:7px;font-size:13px;}}.mail-flow b{{font:700 12px Consolas,monospace;}}.flow-track{{height:12px;border-radius:99px;background:#ece9e2;overflow:hidden;}}.flow-track i{{display:block;height:100%;border-radius:99px;}}
.token-strip{{display:block;width:100%;margin-top:18px;border-radius:18px;mix-blend-mode:multiply;}}
.rhythm{{width:100%;border-collapse:separate;border-spacing:6px 9px;}}.rhythm th{{font:700 10px Consolas,monospace;text-transform:uppercase;color:var(--muted);}}.rhythm tbody th{{text-align:left;color:var(--ink);}}.rhythm td{{padding:0;}}.heat{{display:block;width:100%;height:28px;border-radius:9px;background:#ece9e2;box-shadow:inset 0 0 0 1px rgba(16,33,59,.05);}}.heat.level-1{{background:#cde8fb}}.heat.level-2{{background:#6abff1}}.heat.level-3{{background:#2563eb}}
.empty-state{{min-height:190px;display:grid;place-content:center;text-align:center;gap:8px;color:var(--muted);}}.empty-state strong{{font:800 25px "Arial Rounded MT Bold",sans-serif;}}.empty-state span{{font-size:12px;}}
.weekly-panel{{grid-column:1/-1;}}.weekly-list{{display:grid;gap:13px;}}
.week-row{{display:grid;grid-template-columns:150px 1fr;align-items:end;gap:20px;padding:14px 16px;border-radius:17px;background:#f3f0e9;}}.week-row.unavailable{{opacity:.48;}}.week-name span{{display:block;font-weight:700;}}.week-name b{{display:block;margin-top:5px;color:var(--muted);font:600 10px Consolas,monospace;}}.week-row ol{{height:72px;display:grid;grid-template-columns:repeat(4,1fr);align-items:end;gap:12px;margin:0;padding:0;list-style:none;}}.week-row li{{position:relative;height:72px;display:grid;grid-template-rows:auto auto 1fr;text-align:center;}}.week-row li span{{color:var(--muted);font:600 9px Consolas,monospace;}}.week-row li strong{{font:800 14px Consolas,monospace;}}.week-row li i{{width:100%;max-width:46px;align-self:end;justify-self:center;border-radius:7px 7px 3px 3px;background:var(--series);opacity:.85;}}
.notes{{display:grid;grid-template-columns:1.1fr .9fr;gap:18px;margin-top:18px;}}.observations ol{{list-style:none;counter-reset:notes;margin:20px 0 0;padding:0;display:grid;gap:12px;}}.observations li{{counter-increment:notes;display:grid;grid-template-columns:32px 1fr;align-items:center;gap:10px;padding:12px;border-radius:14px;background:#f3f0e9;}}.observations li:before{{content:counter(notes);display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:var(--ink);color:white;font:700 11px Consolas,monospace;}}
.coverage-panel{{background:var(--ink);color:white;}}.coverage-panel .section-kicker{{color:#76e4d6}}.coverage-panel h2{{color:white}}.coverage-panel>p{{margin:9px 0 0;color:#cbd4e3;font-size:12px;}}.coverage-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:20px 0 0;padding:0;list-style:none;}}.coverage-grid li{{position:relative;padding:15px;border:1px solid rgba(255,255,255,.13);border-radius:14px;background:rgba(255,255,255,.055);}}.coverage-grid li:after{{content:"";position:absolute;width:30px;height:5px;right:10px;top:12px;border-radius:99px;background:var(--receipt);}}.coverage-grid span{{display:block;color:#cbd4e3;font:700 9px Consolas,monospace;text-transform:uppercase;letter-spacing:.09em;}}.coverage-grid strong{{display:block;margin-top:15px;font-size:13px;}}.coverage-grid .unavailable{{opacity:.55;}}
.reflection{{position:relative;margin-top:18px;padding:30px 36px 30px 42px;overflow:hidden;border:1px solid rgba(16,33,59,.13);border-radius:24px;background:var(--paper);box-shadow:0 12px 32px rgba(16,33,59,.07);}}.reflection:before{{content:"";position:absolute;inset:0 auto 0 0;width:7px;background:linear-gradient(to bottom,#2563eb 0 33.333%,#14b8a6 33.333% 66.666%,#7c3aed 66.666% 100%);}}.reflection blockquote{{margin:14px 0 0;}}.reflection p{{max-width:1000px;margin:0;font:italic 700 clamp(20px,2.5vw,31px)/1.38 Georgia,"Times New Roman",serif;letter-spacing:-.018em;color:var(--ink);}}.reflection cite{{display:block;margin-top:17px;color:var(--muted);font:700 10px/1.5 Consolas,"Courier New",monospace;font-style:normal;text-transform:uppercase;letter-spacing:.08em;}}
footer{{display:flex;justify-content:space-between;gap:20px;margin-top:24px;padding:0 6px;color:var(--muted);font:600 10px/1.5 Consolas,monospace;text-transform:uppercase;letter-spacing:.06em;}}
@media(max-width:900px){{.hero{{grid-template-columns:1fr;}}.hero-copy{{padding:38px 32px 8px;}}.hero-art{{min-height:280px;}}.hero-art img{{left:0;width:100%;object-position:center;}}.dashboard-grid,.notes{{grid-template-columns:1fr;}}.weekly-panel{{grid-column:auto;}}}}
@media(max-width:760px){{.source-grid{{grid-template-columns:1fr;}}}}
@media(max-width:560px){{.page{{width:min(100% - 20px,1180px);}}.hero{{border-radius:22px;}}.hero-copy{{padding:28px 22px 2px;}}.source-grid{{grid-template-columns:1fr;}}.panel{{padding:20px;border-radius:20px;}}.panel-head{{align-items:start;flex-direction:column;}}.panel-head p{{text-align:left;}}.rhythm{{border-spacing:3px 8px;}}.rhythm thead th{{font-size:8px;}}.week-row{{grid-template-columns:1fr;}}.coverage-grid{{grid-template-columns:1fr;}}footer{{flex-direction:column;}}}}
@media(prefers-reduced-motion:no-preference){{.hero,.source-card,.panel,.reflection{{animation:arrive .55s both ease-out;}}.source-card:nth-child(2){{animation-delay:.05s}}.source-card:nth-child(3){{animation-delay:.1s}}.reflection{{animation-delay:.15s}}@keyframes arrive{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}}}
@media print{{body{{background:white}}.page{{width:100%;padding:0}}.hero,.source-card,.panel,.reflection{{box-shadow:none;break-inside:avoid}}}}
</style>
</head>
<body>
<main class="page">
  <header class="hero">
    <div class="hero-copy">
      <div class="pulse-badge"><i></i>{counted}-source Work IQ pulse</div>
      <div class="eyebrow">Last 28 days · counted, not guessed</div>
      <h1>Work IQ<br>Signalboard</h1>
      <p>{esc(human_list(available_names))}—turned into a lively read on how the last four weeks actually moved.</p>
      <div class="coverage-note">{esc(coverage_note(coverage))}</div>
    </div>
    <div class="hero-art"><img src="{hero}" alt=""></div>
  </header>

  <section class="section source-grid" aria-label="Measured source totals">{cards}</section>

  <section class="dashboard-grid">
    <article class="panel">
      <div class="panel-head"><div><div class="section-kicker">Mail flow</div><h2>Sent versus received</h2></div><p>Two signals that should never be collapsed into one.</p></div>
      {mail_flow_html(doc["activity"], coverage["mail"] != "unavailable")}
      <img class="token-strip" src="{tokens}" alt="Abstract tokens representing work signals">
    </article>
    <article class="panel">
      <div class="panel-head"><div><div class="section-kicker">Calendar texture</div><h2>Meeting rhythm</h2></div><p>Scheduled meeting minutes by weekday and time band.</p></div>
      {rhythm_html(doc["calendar_rhythm"], coverage["calendar"] != "unavailable")}
    </article>
    <article class="panel weekly-panel">
      <div class="panel-head"><div><div class="section-kicker">Weekly pulse</div><h2>Counts that reconcile</h2></div><p>Every row adds back to its 28-day total.</p></div>
      <div class="weekly-list">{weekly_html(doc)}</div>
    </article>
  </section>

  <section class="notes">
    <article class="panel observations"><div class="section-kicker">Numbers worth noticing</div><h2>What showed up</h2><ol>{note_items}</ol></article>
    <article class="panel coverage-panel"><div class="section-kicker">Signal check</div><h2>Signal scope</h2><p>Missing sources stay missing—never zeroed into the story.</p>{coverage_html(coverage)}</article>
  </section>

  <section class="reflection" aria-label="AI reflection">
    <div class="section-kicker">A note from the machine</div>
    <blockquote>
      <p><em>“{esc(reflection_text)}”</em></p>
      <cite>— AI reflection · grounded in counted signals</cite>
    </blockquote>
  </section>

  <footer><span>Built from your Work IQ signals</span><span>28-day read · reconciled totals</span></footer>
</main>
</body>
</html>"""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValidationError(f"could not read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Absolute path to aggregate JSON")
    parser.add_argument("--out", type=Path, help="Absolute output HTML path")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)

    try:
        doc = validate(load_json(args.input))
        if args.validate_only:
            print("Signalboard data is valid and reconciled.")
            return 0
        if not args.out:
            raise ValidationError("--out is required unless --validate-only is used")
        skill_root = Path(__file__).resolve().parent.parent
        output = build_html(doc, skill_root / "assets")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    except ValidationError as exc:
        print(f"signalboard validation failed: {exc}", file=sys.stderr)
        return 2

    print(str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
