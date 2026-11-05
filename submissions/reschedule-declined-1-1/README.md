# Reschedule Declined 1:1

A **condition-triggered** Scout automation that helps you recover a one-on-one
after it is declined.

**Trigger:** Scout checks every 60 minutes for a newly declined one-on-one
meeting in your calendar or inbox responses. It is a one-shot automation: it
runs once when the condition is met.

It catches declines from **both sides** — when you decline someone else's invite
and when another participant declines a meeting you organized.

For each declined 1:1 it:

1. Collects recent decline signals from meeting-response emails (including
   declines that only appear in the message body), calendar events, and attendee
   statuses. Automation summary emails and organizer-cancelled meetings are
   ignored.
2. Confirms it is a true one-on-one (organizer plus one attendee), excluding
   room/resource-only and group meetings.
3. Captures the subject, who declined, original time, duration, timezone, and
   whether it is recurring.
4. Resolves both participants and checks working hours, conflicts, and
   out-of-office blocks.
5. Finds the **3 best replacement slots** in the next 7 business days, ranked by
   earliest viable slot and minimal disruption.
6. Creates a real **Outlook draft** addressed to the other participant, proposing
   those 3 slots (with timezone and original duration) and asking for their
   preferred option.
7. Sends you a summary in a **Teams self-chat** and by **email** with each
   meeting's subject, original time, proposed slots, and the draft's subject. If
   nothing was declined, you still get a short "no action needed" notice.

**It never sends the draft to the other participant automatically** — review and
send it yourself from Outlook Drafts.

## Run in Scout Desktop or Scout Cloud

Use the [automation JSON file](./reschedule-declined-1-1.json):

- **Scout Desktop:** Import the automation file, then run it from Scout Desktop.
- **Scout Cloud:** Open the JSON file, copy its full contents, paste them into
  Scout Cloud, then run the automation.

## Before you enable it

- Scout needs access to your Microsoft 365 calendar, mail, and Teams, including
  the ability to view other attendees' availability, read emails, create Outlook
  drafts, and send you a Teams chat and email (for example through the WorkIQ
  connector).
- The automation sends its run summary to **you** (Teams self-chat and your own
  mailbox). The reschedule drafts stay unsent in Outlook Drafts.
- The automation imports **enabled**, so it starts running right away. Review it
  and disable it if you want to adjust anything first.
