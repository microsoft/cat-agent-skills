# Daily Consolidated Task List

A Scout automation that builds your daily work plan before you start the day.

**Runs:** every day at 8:00 AM.

Each run reads today's calendar, extracts actionable items from recent Outlook
mail and Teams chats, deduplicates and ranks them, and produces a plan with:

- **Top 3 must-do** items
- **Important tasks**
- **Quick wins**
- **Waiting-on-others** follow-ups

Every item shows its source, why it was prioritized, an effort estimate, and a
suggested time block that fits around your meetings.

## Before you enable it

- Scout needs access to your Microsoft 365 calendar, Outlook mail, and Teams
  (for example through the WorkIQ connector).
- The automation imports **disabled**. Review the schedule and steps, then enable it.
- It only reads and summarizes; it does not send messages.
