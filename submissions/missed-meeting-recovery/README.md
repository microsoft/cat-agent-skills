# Missed-Meeting Recovery

A **condition-triggered** Scout automation that catches you up after a meeting
you skipped.

**Trigger:** Scout checks every 60 minutes whether you missed or declined a
calendar meeting. It is a one-shot automation: it runs once when the condition
is met.

For each candidate meeting in the last 24 hours it:

1. Decides whether you really missed it. Attendance evidence (your chat
   messages in the meeting, transcript activity, other participation signals)
   always overrides your invite response, so a meeting you declined but still
   joined is **not** treated as missed.
2. Gathers the best available recap source for missed meetings: transcript,
   then meeting chat, then event details.
3. Summarizes decisions, outcomes, and open questions.
4. Extracts only the action items **assigned to you**, each with a confidence
   level and the supporting quote.
5. Builds two outputs: a short **Missed-Meeting Recovery Summary** (5-10
   bullets, missed meetings only) and a full **Recovery Brief** ordered by
   recency, with per-meeting sections, a separate "Other Follow-Ups
   (Attendance Evidence)" section, and a consolidated checklist.
6. Sends both outputs, summary first, **only to you** by email (subject
   `Missed-Meeting Recovery | <date>`) and by Teams chat, and reports delivery
   success or failure for each channel.

## Run in Scout Desktop or Scout Cloud

Use the [automation JSON file](https://microsoft.github.io/cat-agent-skills/bundles/missed-meeting-recovery.json):

- **Scout Desktop:** Import the automation file, then run it from Scout Desktop.
- **Scout Cloud:** Open the JSON file, copy its full contents, paste them into
  Scout Cloud, then run the automation.

## Before you enable it

- Scout needs access to your Microsoft 365 calendar, meeting
  transcripts/chats (for example through the WorkIQ connector), and the ability
  to send email and Teams chat messages to you.
- Transcripts only exist for meetings that were recorded or transcribed.
- Teams messages have a length limit; if the full brief doesn't fit, the Teams
  message carries the full summary and as much of the brief as possible, and
  points to the email for the full version.
- The automation imports **enabled**, so it starts running right away. Review it
  and disable it if you want to adjust anything first.
