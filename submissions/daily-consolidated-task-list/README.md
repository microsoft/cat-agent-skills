# Daily Consolidated Task List

A Scout automation that builds your daily work plan before you start the day.

**Runs:** every weekday (Monday to Friday) at 9:00 AM.

Each run reads today's calendar, extracts actionable items from recent Outlook
mail and Teams chats, deduplicates and ranks them, and produces a plan with:

- **Top 3 must-do** items
- **Important tasks**
- **Quick wins**
- **Waiting-on-others** follow-ups

Every item shows its source, why it was prioritized, an effort estimate, and a
suggested time block that fits around your meetings.

## Run in Scout Desktop or Scout Cloud

Use the [automation JSON file](./daily-consolidated-task-list.json):

- **Scout Desktop:** Import the automation file, then run it from Scout Desktop.
- **Scout Cloud:** Open the JSON file, copy its full contents, paste them into
  Scout Cloud, then run the automation.

## Before you enable it

- Scout needs access to your Microsoft 365 calendar, Outlook mail, and Teams
  (for example through the WorkIQ connector).
- After importing into Scout, review the schedule and steps, then confirm that
  the automation is enabled when you are ready for it to run.
- It only reads and summarizes; it does not send messages.
