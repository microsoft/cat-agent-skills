# Copilot Studio harness playbook

Use this playbook for a predictable run in the Work IQ preview harness. Paths
below describe capabilities; adapt parameter syntax to the available fetch
operation.

## Ground rules

1. Query one source at a time: Calendar, Mail, then Teams chats.
2. Request only fields needed for arithmetic. Never request subjects, bodies,
   attendees, organizer, location, names, addresses, filenames, or web URLs.
3. Treat the fetch tool's `Results limited to 10/50/100 items per collection`
   notice as a hard cap, regardless of `$top`. Never use page length as a total
   when it equals the cap.
4. Do not replay `$skip` or `$skiptoken`; the harness may reject both.
5. Keep batches at eight calls or fewer. Retry every `429` call individually
   and reconcile totals before moving on.
6. Do not call `/me/mailboxSettings`; the schema has no working-hours metric.

## Calendar

Use `/me/calendarView` with the 28-day start and end parameters. Request only:

```text
start,end,isAllDay,showAs,responseStatus,isCancelled
```

Use `$count=true` for the total. Fetch the four weekly windows separately for
weekly counts, duration, meeting days, and the rhythm heatmap. If a weekly
window hits the harness cap, split it into smaller half-open time windows until
each response is below the cap. Exclude cancelled and declined events. Verify
the four weekly counts sum to the 28-day count.

For the rhythm heatmap, use each event's returned local time and the exact bands
defined in `safe-schema.md`. Split minutes when an event crosses a band boundary.

Never request `attendees` merely to estimate group size.

## Mail

Get the 28-day non-draft total from `/me/messages` with `$count=true` and a
minimal `$select`. Get sent mail from `/me/mailFolders/sentitems/messages` over
the same window. Calculate received mail as total minus sent only after both
queries succeed.

Query four weekly Sent Items counts for `weekly_counts.emails_sent`. Run at most
four mail calls in a batch, retry throttled calls individually, and require the
weekly sum to equal the 28-day sent total. Inbound mail never determines active
days; the schema deliberately has no all-source `active_days` field.

## Teams chats

Do not call `/me/chats/getAllMessages()`; it fails in delegated context. List
recent chats with only `id,lastUpdatedDateTime`, then query each
`/me/chats/{id}/messages` with only `lastModifiedDateTime`.

`$count`, `$skip`, and replayed `$skiptoken` may all fail. Count an interval by
timestamp partitioning instead:

1. Query the half-open interval `[start, end)`.
2. If the tool reports a cap or returns exactly the cap, split the interval at
   its midpoint and query both halves.
3. Repeat until every leaf interval returns fewer than the cap.
4. Sum leaf counts and assign timestamps to the four weekly buckets.

Use half-open boundaries to avoid duplicates. If the chat list itself cannot be
exhausted, mark Teams unavailable. The default successful scope is
`chats-only`; do not enumerate channels unless the user explicitly requests the
slower `/me/joinedTeams` → channels → messages traversal. Never label a
chats-only count as including channels.

## Automatic spill files

Large tool results may be written under `/app/data` as root-owned files. Avoid
this by using the minimal selections above and small time windows. If a response
still spills:

- do not open or parse a spill file that may contain unrequested personal data;
- retry once with a narrower time window and selection;
- mark the source unavailable if the narrow query still spills; and
- delete the spill only when permitted. A permission error is not a reason to
  abort or repeatedly retry cleanup.

## Rendering from any working directory

Use the absolute resource path supplied by the skill loader to resolve the
directory containing `SKILL.md`; do not search the filesystem or infer it from
the current working directory. Replace the example path below with the resolved
path, initialize both variables, and verify them before use. Never run the later
commands with an empty variable or the literal example path.

```bash
SIGNALBOARD_SKILL="/resolved/absolute/path/to/work-iq-signalboard"
SIGNALBOARD_TMP="$(mktemp -d)"
test -f "$SIGNALBOARD_SKILL/scripts/render_signalboard.py"
test -d "$SIGNALBOARD_TMP"
```

Then validate and render with absolute paths:

```bash
python "$SIGNALBOARD_SKILL/scripts/render_signalboard.py" \
  "$SIGNALBOARD_TMP/safe-signalboard.json" --validate-only
python "$SIGNALBOARD_SKILL/scripts/render_signalboard.py" \
  "$SIGNALBOARD_TMP/safe-signalboard.json" \
  --out /app/created/work-iq-signalboard.html
```

Do not assume the current directory is the skill root.
