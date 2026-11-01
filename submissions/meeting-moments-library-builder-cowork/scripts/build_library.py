#!/usr/bin/env python3
"""Validate approved entries and build portable JSON, CSV, and HTML library files."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import json
import math
import pathlib
import re
import urllib.parse
from typing import Any


CAPTURE_TYPES = {
    "how-to",
    "decision",
    "customer-voice",
    "demo-highlight",
    "lesson-learned",
    "onboarding",
    "custom",
}
VERIFICATION = {"verified", "needs-review", "blocked"}
APPROVAL = {"approved", "held", "rejected"}
SLUG = re.compile(r"[^a-z0-9]+")
SAFE_BASE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FORMULA_PREFIXES = ("=", "+", "-", "@")


def stable_id(entry: dict[str, Any]) -> str:
    base = "|".join(
        [
            str(entry.get("title", "")),
            str(entry.get("session", "")),
            str(entry.get("startSeconds", "")),
        ]
    ).lower()
    slug = SLUG.sub("-", str(entry.get("title", "")).lower()).strip("-")[:48]
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()[:8]
    return f"{slug or 'moment'}-{digest}"


def timestamp(seconds: float) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    whole_hours = int(hours)
    whole_minutes = int(minutes)
    if math.isclose(secs, round(secs), abs_tol=0.0005):
        sec_text = f"{int(round(secs)):02d}"
    else:
        sec_text = f"{secs:06.3f}".rstrip("0").rstrip(".")
    return (
        f"{whole_hours}:{whole_minutes:02d}:{sec_text}"
        if whole_hours
        else f"{whole_minutes}:{sec_text}"
    )


def safe_https(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = urllib.parse.urlparse(value)
        hostname = parsed.hostname
        # Accessing port validates malformed and out-of-range values.
        parsed.port
    except ValueError:
        return ""
    if (
        parsed.scheme.lower() != "https"
        or not parsed.netloc
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or any(character.isspace() or ord(character) < 32 for character in value)
    ):
        return ""
    return value


def deep_link(value: str, start_seconds: float) -> str:
    value = safe_https(value)
    if not value:
        return ""
    parsed = urllib.parse.urlparse(value)
    if not parsed.path.lower().endswith("/_layouts/15/stream.aspx"):
        return value
    query = urllib.parse.parse_qs(parsed.query)
    resource = query.get("id", [""])[0]
    if not resource:
        return value
    pairs = [("id", resource)]
    for key in ("share", "d", "web"):
        for item in query.get(key, []):
            pairs.append((key, item))
    if start_seconds > 0:
        nav = json.dumps(
            {"playbackOptions": {"startTimeInSeconds": start_seconds}},
            separators=(",", ":"),
        )
        pairs.append(("nav", base64.b64encode(nav.encode()).decode()))
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(pairs)))


def require_text(entry: dict[str, Any], key: str, errors: list[str]) -> str:
    value = str(entry.get(key, "")).strip()
    if not value:
        errors.append(f"{key} is required")
    return value


def number_value(
    raw: Any, field: str, errors: list[str], *, minimum: float | None = None
) -> float | None:
    try:
        if isinstance(raw, bool):
            raise ValueError
        value = float(raw)
        if not math.isfinite(value) or (minimum is not None and value < minimum):
            raise ValueError
        return round(value, 3)
    except (TypeError, ValueError):
        qualifier = f" greater than or equal to {minimum:g}" if minimum is not None else ""
        errors.append(f"{field} must be a finite number{qualifier}")
        return None


def normalize_entry(
    raw: dict[str, Any], position: int, max_duration_seconds: float
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    title = require_text(raw, "title", errors)
    capture_type = require_text(raw, "captureType", errors)
    if capture_type and capture_type not in CAPTURE_TYPES:
        errors.append(f"captureType must be one of {sorted(CAPTURE_TYPES)}")
    session = require_text(raw, "session", errors)
    outcome = require_text(raw, "outcome", errors)
    verification = require_text(raw, "verification", errors)
    if verification and verification not in VERIFICATION:
        errors.append(f"verification must be one of {sorted(VERIFICATION)}")
    approval = require_text(raw, "approval", errors)
    if approval and approval not in APPROVAL:
        errors.append(f"approval must be one of {sorted(APPROVAL)}")

    start = number_value(raw.get("startSeconds"), "startSeconds", errors, minimum=0)
    if start is None:
        start = 0.0

    end_value = raw.get("endSeconds")
    end = None
    if end_value not in (None, ""):
        end = number_value(end_value, "endSeconds", errors, minimum=0)
        if end is not None and end <= start:
            end = None
            errors.append("endSeconds must be greater than startSeconds")

    duration_value = raw.get("durationSeconds")
    if duration_value in (None, ""):
        duration = round(end - start, 3) if end is not None else 0.0
    else:
        duration = number_value(
            duration_value, "durationSeconds", errors, minimum=0
        )
        if duration is None:
            duration = 0.0
    if duration > max_duration_seconds:
        errors.append(
            "durationSeconds exceeds configured capture.maxMinutes "
            f"({max_duration_seconds / 60:g} minutes)"
        )

    original_url = str(raw.get("recordingUrl", "")).strip()
    if not original_url:
        errors.append("recordingUrl is required")
    recording_url = deep_link(original_url, start)
    if original_url and not recording_url:
        errors.append("recordingUrl must be HTTPS")

    entry = {
        "id": str(raw.get("id", "")).strip() or stable_id(raw),
        "title": title,
        "captureType": capture_type,
        "session": session,
        "date": str(raw.get("date", "")).strip(),
        "presenter": str(raw.get("presenter", "")).strip() or "Unattributed",
        "startSeconds": start,
        "startTimestamp": timestamp(start),
        "endSeconds": end,
        "durationSeconds": duration,
        "durationLabel": f"~{max(1, round(duration / 60))}m" if duration else "",
        "recordingUrl": recording_url,
        "outcome": outcome,
        "category": str(raw.get("category", "")).strip() or "Other",
        "verification": verification,
        "approval": approval,
        "evidenceNote": str(raw.get("evidenceNote", "")).strip(),
        "sourceLabel": str(raw.get("sourceLabel", "")).strip(),
        "position": position,
    }
    return entry, errors


def script_json(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def validate_base_name(value: Any) -> str:
    base = str(value or "").strip()
    if (
        not SAFE_BASE_NAME.fullmatch(base)
        or base in {".", ".."}
        or pathlib.PurePath(base).name != base
    ):
        raise ValueError(
            "output.baseName must be a simple filename stem containing only "
            "letters, numbers, dots, underscores, and hyphens"
        )
    return base


def csv_safe(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if value.lstrip().startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def build_html(config: dict[str, Any], entries: list[dict[str, Any]]) -> str:
    approved = entries
    name = html.escape(str(config.get("libraryName", "Meeting Moments Library")))
    subtitle = html.escape(
        str(config.get("subtitle", "Verified moments from authorized meetings"))
    )
    data = script_json(approved)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name}</title>
<style>
:root{{--bg:#f5f6fa;--card:#fff;--text:#1b1d27;--muted:#606579;--line:#e1e4ee;--accent:#4f46e5}}
*{{box-sizing:border-box}}body{{margin:0;font-family:Segoe UI,system-ui,sans-serif;background:var(--bg);color:var(--text)}}
header{{padding:42px 24px;background:linear-gradient(110deg,#4f46e5,#0d9488);color:#fff}}
header div,main{{max-width:1100px;margin:auto}}h1{{margin:0 0 8px}}header p{{margin:0;opacity:.9}}
.tools{{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}}input,select{{padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:#fff}}
input{{flex:1;min-width:260px}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:16px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;box-shadow:0 4px 15px rgba(0,0,0,.05)}}
.meta,.small{{color:var(--muted);font-size:.88rem}}.tag{{display:inline-block;padding:4px 8px;border-radius:99px;background:#eef2ff;color:#3730a3;font-size:.75rem;font-weight:700}}
a{{display:inline-block;margin-top:12px;color:var(--accent);font-weight:700}}.empty{{padding:32px;text-align:center;color:var(--muted)}}
main{{padding:0 24px 48px}}
</style>
</head>
<body>
<header><div><h1>{name}</h1><p>{subtitle}</p></div></header>
<main>
<div class="tools"><label for="q">Search</label><input id="q" aria-label="Search moments" placeholder="Search moments"><label for="category">Category</label><select id="category" aria-label="Filter by category"><option value="">All categories</option></select></div>
<div id="results" class="grid"></div>
</main>
<script>
const ENTRIES={data};
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]));
const safeUrl=value=>{{try{{const u=new URL(value);return u.protocol==="https:"?esc(u.href):"#"}}catch(_e){{return"#"}}}};
const q=document.querySelector("#q"),cat=document.querySelector("#category"),results=document.querySelector("#results");
for(const value of [...new Set(ENTRIES.map(x=>x.category))].sort()){{const o=document.createElement("option");o.value=value;o.textContent=value;cat.appendChild(o)}}
function render(){{
 const term=q.value.toLowerCase().trim(),category=cat.value;
 const rows=ENTRIES.filter(x=>(!category||x.category===category)&&(!term||JSON.stringify(x).toLowerCase().includes(term)));
 results.innerHTML=rows.length?rows.map(x=>`<article class="card"><span class="tag">${{esc(x.category)}}</span><h2>${{esc(x.title)}}</h2><p>${{esc(x.outcome)}}</p><p class="meta">${{esc(x.session)}}${{x.date?" · "+esc(x.date):""}}</p><p class="small">${{esc(x.presenter)}} · starts at ${{esc(x.startTimestamp)}}${{x.durationLabel?" · "+esc(x.durationLabel):""}}</p><a href="${{safeUrl(x.recordingUrl)}}" target="_blank" rel="noopener noreferrer">Open recording ↗</a></article>`).join(""):`<div class="empty">No approved moments match.</div>`;
}}
q.addEventListener("input",render);cat.addEventListener("change",render);render();
</script>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--entries", required=True, type=pathlib.Path)
    parser.add_argument("--config", required=True, type=pathlib.Path)
    parser.add_argument("--out-dir", required=True, type=pathlib.Path)
    args = parser.parse_args()

    raw_entries = json.loads(args.entries.read_text(encoding="utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if not isinstance(raw_entries, list):
        raise SystemExit("Entries file must contain a JSON array.")

    entries: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    seen: set[str] = set()
    try:
        max_minutes = float(config.get("capture", {}).get("maxMinutes", 5))
        if not math.isfinite(max_minutes) or max_minutes <= 0:
            raise ValueError
    except (TypeError, ValueError):
        raise SystemExit("capture.maxMinutes must be a positive finite number.")
    max_duration_seconds = max_minutes * 60
    for position, raw in enumerate(raw_entries, 1):
        if not isinstance(raw, dict):
            issues.append({"position": position, "errors": ["entry must be an object"]})
            continue
        entry, errors = normalize_entry(raw, position, max_duration_seconds)
        if entry["id"] in seen:
            errors.append(f"duplicate id: {entry['id']}")
        seen.add(entry["id"])
        entries.append(entry)
        if errors:
            issues.append({"position": position, "id": entry["id"], "errors": errors})

    fatal = [
        issue
        for issue in issues
        if any(
            "required" in error
            or "must be one of" in error
            or "startSeconds" in error
            or "endSeconds" in error
            or "durationSeconds" in error
            or "recordingUrl" in error
            for error in issue["errors"]
        )
    ]
    if fatal:
        print(json.dumps({"status": "error", "issues": issues}, ensure_ascii=False))
        raise SystemExit(2)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    output_config = config.get("output", {})
    try:
        base = validate_base_name(
            output_config.get("baseName", "meeting-moments-library")
        )
    except ValueError as error:
        print(json.dumps({"status": "error", "errors": [str(error)]}))
        raise SystemExit(2)
    json_path = args.out_dir / f"{base}.json"
    csv_path = args.out_dir / f"{base}.csv"
    html_path = args.out_dir / f"{base}.html"

    issue_ids = {issue.get("id") for issue in issues if issue.get("id")}
    approved_entries = [
        entry
        for entry in entries
        if entry["verification"] == "verified"
        and entry["approval"] == "approved"
        and bool(entry["recordingUrl"])
        and entry["id"] not in issue_ids
    ]

    include_evidence = bool(output_config.get("includeEvidenceNotesInJson", True))
    json_entries = []
    for entry in approved_entries:
        serialized = dict(entry)
        if not include_evidence:
            serialized.pop("evidenceNote", None)
        json_entries.append(serialized)
    payload = {
        "schemaVersion": "1.0",
        "libraryName": config.get("libraryName", "Meeting Moments Library"),
        "captureType": config.get("capture", {}).get("type", "custom"),
        "entries": json_entries,
    }
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    fields = [
        "id",
        "title",
        "captureType",
        "session",
        "date",
        "presenter",
        "startTimestamp",
        "startSeconds",
        "durationLabel",
        "durationSeconds",
        "recordingUrl",
        "outcome",
        "category",
        "verification",
        "approval",
        "sourceLabel",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for entry in approved_entries:
            writer.writerow({key: csv_safe(value) for key, value in entry.items()})

    html_path.write_text(build_html(config, approved_entries), encoding="utf-8")
    approved = len(approved_entries)
    print(
        json.dumps(
            {
                "status": "success",
                "candidatesProcessed": len(entries),
                "entriesPublished": approved,
                "approvedForHtml": approved,
                "issues": issues,
                "outputs": [str(html_path), str(csv_path), str(json_path)],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
