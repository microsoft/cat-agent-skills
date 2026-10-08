# Web Change Monitor

Watch a web page — or a specific table/section within it — for **real content changes** and get alerted only when something actually changed. It builds a small content *fingerprint*, compares it against a persisted state file, and notifies you on change, ignoring styling/font/load noise. It's designed to run unattended on a schedule and stay quiet until there's something worth your attention.

## Why it's useful

Some pages change **rarely and unpredictably**, checking them is a **recurring chore**, and **being late has a real cost**. That's exactly where this skill pays off. The four highest-value targets:

1. **Product "What's New" / release notes / changelogs** — e.g. a Microsoft Learn "What's New" page — stay current on the products you build or support without checking daily.
2. **API/SDK deprecation & breaking-change notices** — the earliest possible warning prevents things silently breaking.
3. **Service health / known-issues pages** — get alerted the instant an issue is posted or a status flips to *Resolved*.
4. **TSG / KB / wiki runbooks you depend on** — get pinged when a procedure you rely on is edited, so you never follow a stale runbook.

## How it works

1. Opens the URL in a browser and reads the target content (whole page, or just the sections/tables you name).
2. Builds a fingerprint from stable content signals (section name, row count, first-row text — normalized), **not** layout.
3. Compares to a per-URL state file. First run = baseline (no alert). Any change → updates state and alerts.
4. For status-flip / threshold cases (service health, a KPI cell), it fingerprints the **specific row's value cell** and reports the delta, e.g. `MO123456: Investigating → Resolved`.

## Inputs

- **URL** to monitor.
- **What to watch:** whole page or specific sections/tables (or a CSS selector).
- **State file path** (defaults to a JSON file in the workspace, keyed by URL).
- **Notify how:** a chat/self-chat message, email, or an inline report — kept generic (says *that* it changed and where to look).

## Running it on a schedule

This skill is a natural fit for a scheduled run. In Scout, pair it with an automation that invokes the skill against your chosen URL on a cadence (e.g. every weekday morning). See the companion **Web Change Monitor — Scout automation** submission for a ready-to-import example.

## Notes

- Ignores cosmetic re-rendering; normalize whitespace and skip volatile bits (timestamps, view counters) unless those are the thing being watched.
- If the page needs sign-in, use a session you authenticate yourself; if it lands on a sign-in stub or blank tab, it stops rather than baselining an empty page.
