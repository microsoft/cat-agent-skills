# Work IQ Signalboard schema

Create only the closed object below. Every displayed number must come from a
complete count or an exhaustively partitioned query. Unknown keys and free-form
fields are rejected.

## Input shape

```json
{
  "period": "last-4-weeks",
  "coverage": {
    "calendar": "complete",
    "mail": "complete",
    "teams": "chats-only"
  },
  "activity": {
    "meeting_days": 12,
    "meetings": 18,
    "meeting_hours": 23,
    "emails_sent": 18,
    "emails_received": 974,
    "teams_chat_messages": 41,
    "teams_channel_messages": 0
  },
  "calendar_rhythm": {
    "mon": [1, 2, 3, 0],
    "tue": [2, 3, 3, 1],
    "wed": [2, 2, 3, 0],
    "thu": [1, 3, 2, 0],
    "fri": [2, 2, 1, 0]
  },
  "weekly_counts": {
    "meetings": [4, 5, 3, 6],
    "emails_sent": [5, 4, 3, 6],
    "teams_chats": [8, 12, 9, 12]
  }
}
```

## Allowed values

- Calendar and mail coverage: `complete` or `unavailable`.
- Teams coverage: `chats-only`, `chats-and-channels`, or `unavailable`.
- Counts: non-negative integers. `meeting_days` must be `0`–`28`.
- Hours: `0`–`1000` in half-hour increments.
- Calendar rhythm: integers `0`–`3` for Monday–Friday and the time bands
  morning, midday, afternoon, and evening.
- Weekly counts: exactly four non-negative integers, oldest week first.

Use the event's returned local time for the Calendar rhythm bands:

- morning: before `12:00`;
- midday: `12:00`–`13:59`;
- afternoon: `14:00`–`17:59`; and
- evening: `18:00` or later.

Split an event's minutes when it crosses a band boundary.

Use zero only for a measured zero. When a source is unavailable, set its stored
values to zero; the renderer uses coverage to display **No data**, never `0`.

## Reconciliation rules

The renderer enforces these equalities:

- Sum of weekly `meetings` equals `activity.meetings`.
- Sum of weekly `emails_sent` equals `activity.emails_sent`.
- Sum of weekly `teams_chats` equals `activity.teams_chat_messages`.

This catches missed pages, throttled subqueries, and accidental partial totals.
If a trustworthy total cannot be reconciled, mark that source unavailable
instead of estimating.

## Definitions

- `meeting_days`: distinct dates containing at least one non-declined,
  non-cancelled calendar event. Persist only the total, never the dates.
- `meetings`: non-declined, non-cancelled calendar events in the 28-day window.
- `meeting_hours`: scheduled duration of those events, rounded to the nearest
  half hour.
- `emails_sent`: non-draft messages in Sent Items.
- `emails_received`: total non-draft messages minus Sent Items. Clamp at zero
  only after confirming both totals cover the same window.
- `teams_chat_messages`: messages in 1:1 and group chats.
- `teams_channel_messages`: channel posts and replies. Keep this at zero with
  `chats-only`; the renderer labels the scope explicitly.
- `calendar_rhythm`: allocate meeting minutes into weekday/time-band cells.
  Set empty cells to `0`; split non-empty cells into thirds of the largest cell
  for levels `1`, `2`, and `3`.

Never add inferred work modes, collaboration shapes, focus classifications,
fragmentation estimates, working-hour assumptions, or synthetic scores.
