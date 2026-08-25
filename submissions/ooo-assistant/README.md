# Out-of-Office Assistant

Going away for a day or a week? This skill stands up **temporary OOO coverage**
across your Microsoft 365 signals: it auto-replies to direct messages and
@mentions, flags anything urgent straight to you, watches meetings for mentions
of your name, and drops an end-of-day digest so you can catch up in minutes when
you're back.

Every auto-reply carries a clear **AI-generated disclosure footer**, so nobody
is ever misled into thinking you personally replied.

## Before you start

- **A connected Microsoft 365 account** — the skill reads chats, mentions,
  meetings, and mail, and sends replies/notifications through the agent's
  `m365_*`-style tools.
- **A host that can schedule recurring tasks** (e.g. Scout automations). The
  monitor runs on a half-hourly cadence during work hours; the digest runs once
  a day. On hosts without scheduling, you can still run the monitor on demand.
- Tool names vary by host — the skill describes the *capability* (list chats,
  reply, remember, schedule, send-Teams-message). Map them to whatever your
  environment exposes.

## How to use it

Invoke it when you're heading out, e.g.:

- *"I'm OOO Thursday and Friday — set up coverage, back Monday."*
- *"/ooo-assistant"*
- *"Turn on out-of-office monitoring until the 15th."*

The skill will ask for your OOO dates, return date, any custom urgency keywords,
where to save digests, and the name to sign auto-replies with. Then it creates
two automations:

1. **OOO Monitor** (half-hourly, work hours) — auto-replies to new 1:1s and
   @mentions, flags urgent items, and watches recent meeting transcripts for
   mentions of you.
2. **OOO Digest** (6:30pm) — compiles the day's messages, mentions, urgent
   flags, and meeting notes into a saved markdown digest and a Teams summary.

When you're back, say *"I'm back"* or *"/ooo-assistant off"* and it tears the
automations down and sends a final wrap-up.

## Good to know

- **Auto-replies are always disclosed.** The footer makes it explicit the reply
  was machine-generated on your behalf — this is non-negotiable in the skill.
- **No double-replies.** Replied chat/message IDs are tracked in memory, so a
  chat only gets one OOO reply per absence.
- **System noise is ignored.** Bots, calendar notifications, and system messages
  never get a reply.
- **Digests are privacy-aware.** Customer names are anonymized and confidential
  details are omitted; the full digest is saved to your chosen folder.
- **Urgent means urgent.** Messages matching your urgency keywords are pushed to
  you immediately rather than waiting for the digest.
