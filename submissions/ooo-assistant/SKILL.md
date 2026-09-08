---
name: ooo-assistant
description: Activate enhanced out-of-office monitoring — auto-reply to 1:1 chats and @mentions, monitor meetings for name mentions, flag urgent items via Teams, and generate an end-of-day digest. Use this skill whenever the user says they are going out of office, asks to set up OOO coverage, or invokes "/ooo-assistant".
---

# Out-of-Office Assistant

Set up enhanced OOO coverage: while the user is away, auto-reply to direct
messages and @mentions, watch meetings for mentions of the user, flag urgent
items, and produce a daily digest.

Gather these parameters first (ask if not provided):

1. **OOO date(s)** — which day(s) the user will be out.
2. **Return date** — when they're back (used in the auto-reply text).
3. **Urgency keywords** — optional custom keywords to flag as urgent
   (defaults: "urgent", "ASAP", "critical", "blocker", "emergency").
4. **Digest folder** — where to save the daily digest
   (default: `Documents/daily-digests/`).
5. **Signature name** — the name to sign auto-replies with (defaults to the
   user's first name from their profile).

> **Tool names.** This skill refers to Microsoft 365 tools as `m365_*`, the
> scheduling tool as an automation-create tool, memory as a remember/recall
> tool, and the outbound status ping as a Teams-message tool. If your host
> exposes these under different names, map them to the equivalent capability —
> the workflow is identical.

---

## Setup phase

Create these **recurring monitoring automations** (leave them enabled; they are
disabled/removed in the teardown phase when the user returns).

### 1. OOO Monitor — every 30 min during work hours (8am–6pm)

**Name:** `OOO Monitor — <date>`
**Schedule:** every weekday at 8am, 8:30am, 9am, … through 6pm (half-hourly).

**Prompt tasks:**

1. **1:1 chat replies:**
   - List recent chats and filter to 1:1 chats.
   - For each, check the last message — if it's from someone else AND newer than
     the last check, send the OOO reply (below).
   - Track replied chat IDs in memory to avoid duplicate replies.

2. **@mention replies in group chats/channels:**
   - Scan active group chats and channels for @mentions of the user since the
     last check.
   - Reply to that specific thread with the same OOO message.
   - Track replied message IDs.

3. **Urgent item flagging:**
   - Scan new emails and chat messages for the urgency keywords.
   - If found, immediately send a Teams message to the user with context.

4. **Meeting mention monitoring:**
   - List meetings that ended in the last hour.
   - Attempt to fetch each transcript.
   - Search the transcript for mentions of the user's name.
   - If mentioned, summarize the context and stage it for the digest.

### 2. OOO End-of-Day Digest — 6:30 PM

**Name:** `OOO Digest — <date>`
**Schedule:** every OOO day at 6:30pm.

**Prompt tasks:**

1. Compile the day's activity:
   - All 1:1 messages received (with OOO replies sent)
   - All @mentions in groups/channels (with replies sent)
   - Urgent items flagged
   - Meeting summaries (especially those mentioning the user)
   - Emails received (subjects, senders, urgency flags)
2. Generate a markdown digest and save it to
   `<digest folder>/<YYYY-MM-DD>-ooo-digest.md`.
3. Send a Teams summary to the user with the key highlights.

---

## The OOO auto-reply

```
👋 Hi! I'm currently out of office and will be back on <return date>.

If this is urgent, I'll try to respond — otherwise I'll catch up when I return.

---
This message was sent automatically by <signature name>'s AI assistant,
monitoring on their behalf while they're away.
```

Use this same disclosure footer on **every** auto-reply so recipients always
know the reply was machine-generated on the user's behalf. Never impersonate the
user without the disclosure line.

---

## Teardown phase

When the user says "I'm back", invokes "/ooo-assistant off", or the return date
is reached:

1. Disable/delete the OOO monitoring automations.
2. Send a final summary of the OOO period.
3. Clear the tracking memories.

---

## Hard rules

- NEVER reply to automated/system messages, calendar notifications, or bot
  messages.
- NEVER reply to the same message twice (track replied IDs in memory).
- ALWAYS include the AI-generated disclosure footer on auto-replies.
- NEVER include sensitive content in digests — anonymize customer names and omit
  confidential details.
- DO send urgent alerts to the user immediately.
- DO save every digest to the specified folder.
