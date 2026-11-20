# Prompt to Set Agenda

A Scout meeting-readiness assistant that chases missing agendas.

**Runs:** every weekday at 9:00 AM.

It looks at non-cancelled meetings in the next 3 days and finds the ones that
were newly set up (invite created, received, or updated, or a related meeting
message sent or received, within the last 3 days) and have no agenda in the
invite, body, or thread. For each of them it:

- Saves **one Outlook draft** to the organizer asking for an agenda and a
  pre-read (the pre-read, if provided, is the primary source for the agenda)
- Reuses an existing unsent draft for the same meeting instead of creating a
  duplicate
- Sends a run summary to **Teams** and by **email** to you: meetings processed,
  meetings excluded (already have an agenda, or old invitations), and the draft
  status per meeting

It never sends the organizer emails: drafts are saved for you to review and
send. The only messages it sends are the run summaries to you.

RSVP state, short notice, and conflict indicators are not used to exclude
meetings.

## Run in Scout Desktop or Scout Cloud

Use the [automation JSON file](./prompt-to-set-agenda.json):

- **Scout Desktop:** Import the automation file, then run it from Scout Desktop.
- **Scout Cloud:** Open the JSON file, copy its full contents, paste them into
  Scout Cloud, then run the automation.

## Before you enable it

- Scout needs access to your Microsoft 365 calendar, mail (including creating
  drafts and sending the summary email), and Teams (for example through the
  WorkIQ connector).
- The automation imports **enabled**, so it starts running right away. Review it
  and disable it if you want to adjust anything first.
