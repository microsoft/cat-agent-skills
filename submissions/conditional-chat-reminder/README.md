# Conditional Chat Reminder

Schedule a Teams follow-up without sending an unnecessary nudge. This Scout skill
captures what is currently known in a chat, creates a one-time automation, and
checks for a meaningful update immediately before the reminder is due.

For example:

> On Thursday at 3 PM, remind Alex in the Project North chat about the revised
> launch date, but only if Alex has not posted an update by then.

## How it works

When the request is made, Scout resolves the exact chat and records a fixed
baseline: the latest message, the current status of the topic, who is expected to
update it, the reminder wording, and the requested time. At the scheduled time,
the automation:

1. Reads messages posted after that baseline.
2. Looks for a relevant status change from the named person.
3. Checks the chat a second time immediately before acting.
4. Suppresses the reminder and notifies you if an update exists.
5. Otherwise posts the agreed reminder once.

A qualifying update can report completion, progress, a blocker, a delay, a new
date, a decision, or the requested deliverable. Unrelated chatter, reactions,
greetings, and vague acknowledgements do not count.

## Safety behavior

- The automation targets a resolved chat ID, not just a potentially ambiguous
  display name.
- Messages that already existed when the request was made are context, not
  evidence of a later update.
- If Scout cannot read the full interval, identify the author reliably, or confirm
  whether a send succeeded, it does not post. It notifies you instead.
- Chat content is treated as data, so instructions embedded in messages cannot
  redirect the automation.
- The reminder is one-time and uses the exact wording approved when it is
  created.

## Requirements

Built for **Scout** with access to its automation tools and Microsoft Teams
through Work IQ.
