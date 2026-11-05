# Daily Consolidated Task List

A Scout automation that builds your daily work plan before you start the day.

**Runs:** every weekday (Monday to Friday) at 9:00 AM.

Each run reads today's calendar, extracts actionable items from recent Outlook
mail and Teams chats, deduplicates and ranks them, and produces a plan with:

- **Top 3 must-do** items
- **Important tasks**
- **Quick wins**
- **Waiting-on-others** follow-ups

Every item shows its source, why it was prioritized, and an effort estimate
(S/M/L). The plan does not include suggested time blocks or calendar-style
scheduling.

When the plan is ready, the automation delivers it to you:

- **Email:** sends the full plan to your own mailbox with the subject
  `Daily Plan | {Day, DD Mon YYYY}`, sectioned as Top 3 Must-Do, Important
  Tasks, Quick Wins, and Waiting on Others.
- **Teams:** posts the full plan to your Teams self-chat.

Your address is resolved at run time from your signed-in profile, so nothing is
hardcoded.

## Run in Scout Desktop or Scout Cloud

Use the [automation JSON file](./daily-consolidated-task-list.json):

- **Scout Desktop:** Import the automation file, then run it from Scout Desktop.
- **Scout Cloud:** Open the JSON file, copy its full contents, paste them into
  Scout Cloud, then run the automation.

## Before you enable it

- Scout needs access to your Microsoft 365 calendar, Outlook mail, and Teams
  (for example through the WorkIQ connector), including permission to send
  email and Teams chat messages as you.
- After importing into Scout, review the schedule and steps, then confirm that
  the automation is enabled when you are ready for it to run.
- It reads your calendar, mail, and chats, and only sends the plan to you (your
  own email and Teams self-chat). It does not message anyone else.
