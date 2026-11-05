# Nudge for Response

A Scout automation that follows up on emails you sent that never got an answer.

**Runs:** every weekday at 9:00 AM.

Each run has five steps:

1. **Collect mail scope.** Reads your profile (to know your own addresses), your
   50 most recent Sent Items, a search of the last ~14 days of Sent Items for
   ask-oriented wording, and your Drafts (to detect existing nudges).
2. **Identify actionable asks.** Keeps sent messages where your own text contains
   a request, question, or action ask. `Re:` and `Fw:` messages are not
   excluded automatically, but answer-only replies are. Your own addresses and
   recipients who aren't expected to reply are ignored, and each original ask
   counts once.
3. **Check unanswered and age gates.** Looks in the inbox and subfolders
   (including archive) for a reply from the primary recipient after you sent
   the message, matching by conversation where possible. Keeps asks that are
   still unanswered after **3+ business days** (weekends are skipped).
4. **Draft nudges only.** Saves a brief, warm, professional nudge as a **draft**
   reply on the original sent message.
   - If a nudge draft already exists for that thread, no second one is created.
   - If you deleted an earlier nudge and the ask is still unanswered, one new
     draft is created.
   - Reply-all is used only when you directly asked multiple recipients.
5. **Report outcome.** Summarizes asks checked, asks already answered, and
   drafts created, listing each nudged thread by subject and recipients only.
   When drafts were created, it posts a short Teams summary. If nothing
   qualifies, it reports "No unanswered asks found" and sends no Teams message.

**It never sends email.** Every nudge waits in Drafts for you to review and send.

## Run in Scout Desktop or Scout Cloud

Use the [automation JSON file](./nudge-for-response.json):

- **Scout Desktop:** Import the automation file, then run it from Scout Desktop.
- **Scout Cloud:** Open the JSON file, copy its full contents, paste them into
  Scout Cloud, then run the automation.

## Before you enable it

- Scout needs mail access to Sent Items, Inbox (including archive), and Drafts,
  plus the ability to post to Teams (for example through the WorkIQ connector).
- The automation uses recurring permissions to create reply and reply-all
  drafts and to edit mailbox messages. Mailbox edit permission is
  mailbox-wide, but the automation only edits its own nudge drafts.
- The automation imports **enabled**, so it starts running right away. Review it
  and disable it if you want to adjust anything first.
