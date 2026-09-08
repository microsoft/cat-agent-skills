# Web Change Monitor (Scout automation)

A scheduled companion to the **Web Change Monitor** skill. It runs on a cadence (default: **every weekday at 8:00 AM**), checks the web pages you list, and pings you **only when something actually changed** — otherwise it stays quiet.

## What it's good for

- **Release notes / "What's New" pages** (e.g. a Microsoft Learn "What's New" page) — stay current without checking daily.
- **API/SDK deprecation & changelog pages** — earliest warning before something breaks.
- **Service health / known-issues pages** — status-flip mode reports the delta, e.g. `MO123456: Investigating → Resolved`.
- **TSG/KB/wiki runbooks you depend on** — know when a procedure changes under you.

## Setup

1. Import the `.json` into Scout (Automations → import), or let Scout import it from a GitHub directory.
2. On its **first run** it self-creates a config at `web-change-monitor/config.json` in your Scout workspace with an empty `targets` list, and pings you that it needs configuring.
3. Edit `config.json` and add one or more targets:

```json
{
  "targets": [
    { "url": "https://learn.microsoft.com/…/whats-new", "label": "MDO What's New", "watch": "the What's New list", "rowKey": "" }
  ],
  "notify": "self-chat",
  "ownerRelayEmail": ""
}
```

- `url` — the page to watch.
- `label` — friendly name used in alerts.
- `watch` — `"whole-page"`, a short description of the section/table (e.g. `"the What's New list"`), or a CSS selector.
- `rowKey` — *optional*; for status-flip/threshold pages, the stable row identifier (issue ID, feature name, first-column label) whose value cell to track.
- `notify` — `"self-chat"` (default), `"email"`, or `"inline"`.
- `ownerRelayEmail` — optional; where config-problem pings go (blank = Teams self-chat).

## Notes

- **Portable:** no absolute paths or usernames are baked in — paths resolve at runtime relative to the Scout workspace, so it works across machines and OSes.
- **Quiet by design:** first sighting of a URL just sets a baseline; you only hear from it on a real change or a sign-in/config problem.
- **Adjust the schedule** in Scout after import if you want a different cadence.
