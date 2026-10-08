---
name: web-change-monitor
description: Use this skill to monitor a web page (or a specific table/section within it) for content changes and alert the user only when something actually changed. Ideal for release notes / "What's New" pages, API deprecation and changelog pages, service-health/known-issue status flips, and TSG/KB/wiki runbooks you depend on. Builds a content fingerprint, compares it to a persisted state file, updates state, and notifies on change — ignoring styling/font/load noise.
---

# Web Change Monitor

Monitor a web page — or a specific table/section within it — for meaningful content changes and alert only when something changed.

## Highest-value use cases
This skill pays off most where a page **changes rarely and unpredictably**, checking it manually is a **recurring chore**, and **being late has a real cost**. Prioritize:

1. **Product "What's New" / release notes / changelogs** (e.g. a Microsoft Learn "What's New" page, a product's release-notes page) — stay current on the products you build or support without checking daily.
2. **API/SDK deprecation & breaking-change notices** (e.g. a Graph changelog or a deprecations page) — the earliest possible warning here prevents things silently breaking.
3. **Service health / known-issues pages** — get alerted the instant an issue is posted or a status flips to resolved. This is a status-flip case: fingerprint the specific status row/cell (see "Fingerprinting a specific row/cell").
4. **TSG / KB / wiki runbooks you depend on** — get pinged when a procedure you rely on is edited, so you never follow a stale runbook.

## Inputs (ask if not provided)
- **URL** to monitor.
- **What to watch:** the whole page, or specific sections/tables (describe them, e.g. "the three tables titled X, Y, Z", or a CSS selector). Watching a specific region avoids false alarms from unrelated page chrome.
- **State file path:** where to persist the fingerprint between runs (default: a JSON file in the session/workspace folder, e.g. `web-change-monitor-state.json`, keyed by URL).
- **Notify how:** a chat/self-chat message, email, or just an inline report. Keep alerts generic — say *that* something changed and where to look; don't necessarily dump the changed content unless the user wants it.

## Workflow
1. Open the URL in the browser and wait for it to load.
2. Read the target content (the whole page, or just the specified sections/tables).
3. Build a **fingerprint** for each watched section from stable signals — e.g. section name, row count, and the first data row's text (normalized to single spaces, trimmed). Choose signals that reflect real content, not layout.
4. Compare the current fingerprints to the persisted state file for this URL.
5. If the state file does not exist, create it with the current fingerprints and do **not** alert (first run = baseline).
6. If any fingerprint changed, update the state file and send the alert to the chosen destination.
7. If nothing changed, leave the state as-is (or refresh it if needed) and do not alert.

## Fingerprinting a specific row/cell
For status-flip and threshold cases (e.g. a service-health row moving to "Resolved", or a dashboard KPI crossing a value), don't fingerprint the whole page — target the specific element:
- Identify the row by a stable key (the issue title, feature name, or first-column label), then fingerprint only that row's **status/value cell**.
- Normalize the cell text (trim, collapse whitespace, lowercase) so cosmetic re-rendering doesn't trip a false alert.
- When it changes, report both the **old and new value** for that key (e.g. `"MO123456": Investigating → Resolved`), since for these cases the delta *is* the signal the user wants.

## Robustness
- Do not treat styling, font-load, or transient render errors as content changes — only the target content matters.
- If the page requires sign-in, use a session the user authenticates as themselves; if it lands on a sign-in stub or blank tab, stop and ask the user to open the live page rather than baselining an empty page.
- Normalize whitespace and ignore volatile bits (timestamps, view counters) when they aren't the thing being watched.

## Scheduling
This skill is a good fit for a scheduled/recurring run (e.g. a Scout automation or a daily job). Each run is stateless apart from the persisted state file, so it can run unattended and only speaks up when there's a real change.
