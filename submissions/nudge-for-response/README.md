# Nudge for Response

A Scout automation that follows up on emails you sent that never got an answer.

**Runs:** every weekday at 9:00 AM.

Each run:

1. Scans your recent Sent Items for messages that contain a request or question.
2. Checks the inbox and archive for a reply from the recipient.
3. Keeps asks that are still unanswered after **3+ business days** (weekends
   are skipped).
4. Saves a brief, polite nudge as a **draft** reply on the original message,
   unless a nudge draft already exists for that thread.
5. Posts a short Teams summary (subject and recipients only) when drafts were
   created. If nothing qualifies, it stays quiet.

**It never sends email.** Every nudge waits in Drafts for you to review and send.

## Before you enable it

- Scout needs mail access to Sent Items, Inbox, and Drafts, plus the ability to
  post to Teams (for example through the WorkIQ connector).
- The automation imports **disabled**. Review it, then enable it.
