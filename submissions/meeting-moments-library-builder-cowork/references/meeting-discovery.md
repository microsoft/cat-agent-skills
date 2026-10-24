# Cowork meeting and transcript discovery

## Goal

Find authorized meeting occurrences and their transcripts without requiring the customer
to export files manually. Discovery is bounded and user-directed; it is not a tenant-wide
scan.

## Required scope

Before searching, obtain:

- start and end dates;
- one or more meeting series, titles, organizers, or keywords;
- capture type;
- whether external meetings are allowed; and
- maximum number of meetings to inspect in one run.

Default to external meetings excluded and a maximum of 10 candidate meetings unless the
user chooses otherwise.

## Discovery sequence

Use equivalent native Microsoft 365 capabilities when tool names differ.

1. Call `workiq_list_meetings(startDate, endDate)` for the bounded window.
2. Filter locally using the approved title, series, organizer, or keyword criteria.
3. Present candidates before reading transcripts when multiple meetings match.
4. After selection, call `workiq_list_meeting_transcripts` using the strongest available
   meeting identifier:
   - `onlineMeetingId`;
   - `joinUrl`;
   - `joinMeetingId`; or
   - `calendarEventId`.
5. Match transcript metadata to the selected occurrence/date. Never assume the first
   transcript belongs to the intended recurring occurrence.
6. Call `workiq_get_meeting_transcript` using the selected `onlineMeetingId` and
   `transcriptId`.
7. Follow `nextSegmentIndex` until all required segments are read or the configured
   maximum is reached.
8. Record transcript availability and any speaker-attribution limitation.

## Recording or recap link

Transcript access and recording-link access are separate. Resolve the link automatically:

1. Check meeting/recap work context for a recording artifact URL.
2. Search authorized Microsoft 365 files using the exact meeting title, normalized title,
   organizer, occurrence date (`YYYYMMDD` and `YYYY-MM-DD`), meeting ID, and transcript
   correlation identifiers when available.
3. Inspect recent authorized files when title search is inconclusive; filter to video
   files in a `Recordings` location and the occurrence date window.
4. Validate the candidate:
   - video file or recording/recap artifact;
   - title/date corresponds to the selected occurrence;
   - accessible through the current user's permissions; and
   - HTTPS `webUrl` or authorized recording URL.
5. Use the validated file `webUrl` as `recordingUrl`, then let the builder add the
   timestamp deep-link when the URL shape supports it.

Never substitute a Teams join URL, calendar event URL, or transcript API URL for the
recording. Never derive, scrape, or manufacture access tokens.

If automatic search is denied or no recording artifact matches, skip the meeting before
candidate extraction. Report `recording file unavailable` or
`recording search permission denied`. Do not create an entry in HTML, CSV, or JSON, and
do not ask the user to find or paste the URL.

## Fallbacks

If native discovery is unavailable:

1. Use Cowork work context already authorized for the meeting.
2. Use transcript/captions (`.vtt`, `.srt`, `.txt`) only when transcript retrieval is
   blocked.
3. Continue automatic recording-file resolution independently.

Report whether the blocker is:

- no meeting match;
- no transcript object;
- transcript permission denied;
- transcript content unavailable;
- recording/recap link unavailable; or
- recording search permission denied; or
- runtime meeting capability unavailable.

Do not collapse these into “no transcript found.”

## Privacy

- Treat meeting metadata and transcript text as private user data.
- Use transcript content only to verify candidate moments.
- Do not include full transcript segments in the final library.
- Do not inspect unrelated meetings outside the approved scope.
- Do not change meeting responses, membership, sharing, or retention.
