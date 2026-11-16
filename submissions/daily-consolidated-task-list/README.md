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

## Safeguards

- **Prompt injection:** calendar, mail, chat, and transcript content is treated as
  untrusted data. Instructions found inside it (for example "forward this" or
  "skip this item") are recorded as items, never followed.
- **Locked recipients:** the plan goes only to your own mailbox and Teams
  self-chat. No other recipients can be added.
- **Explicit sensitivity status:** calendar, email, and Teams collection records
  source links, exact labels, and metadata evidence for every source read.
  Status is `labelled`, `confirmed_unlabelled`, or `unknown`. Missing or
  inaccessible metadata is `unknown`, not proof that a source is unlabelled.
- **Merge safety:** deduplication retains every contributing source and label.
  The strongest restriction applies to the whole merged item, including its
  priority reason and effort. A separate manifest retains even sources that
  produce no tasks.
- **Safe deliveries:** email and Teams receive the same sanitized plan, not the
  raw merged list. Unknown status, missing provenance or usable links, unresolved
  policy, or a prohibition on copying causes the entire item to be withheld,
  with only a generic count and reason category reported. Confidential and
  Highly Confidential items appear only as generic, policy-permitted source
  links in a separate unranked section; subjects, names, and derived task details
  are not copied. If a safe reference cannot be verified, the item is withheld.
- **Honest header:** `Highest sensitivity label seen: <value>` covers all sources
  read, including withheld items and sources with no tasks. `None` is used only
  when every source is confirmed unlabelled. Incomplete verification reports
  `Not verified` alongside the highest confirmed label (or known labels when their
  ordering is unresolved); no sources read reports `Not assessed`.

## Run in Scout Desktop or Scout Cloud

Use the [automation JSON file](https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/submissions/daily-consolidated-task-list/daily-consolidated-task-list.json):

- **Scout Desktop:** Import the automation file, then run it from Scout Desktop.
- **Scout Cloud:** Open the JSON file, copy its full contents, paste them into
  Scout Cloud, then run the automation.

## Before you enable it

- Scout needs access to your Microsoft 365 calendar, Outlook mail, and Teams
  (for example through the WorkIQ connector), including permission to send
  email and Teams chat messages as you.
- The connector must expose authoritative sensitivity metadata and applicable
  label policies to release task details. If it cannot verify them, affected
  items are withheld rather than assumed safe.
- After importing into Scout, review the schedule and steps, then confirm that
  the automation is enabled when you are ready for it to run.
- It reads your calendar, mail, and chats, and only sends the plan to you (your
  own email and Teams self-chat). It does not message anyone else.
