# Holiday Recap

**Catch up on everything you missed while you were away — in one pass, without opening a single app.**

You come back from annual leave to 300 emails, a fortnight of Teams noise, meetings that happened without you, and a calendar full of invitations nobody answered. Reading it all takes a day. Skimming it means missing the one message that mattered.

Holiday Recap reads Outlook and Teams for you and reports back in a single structured briefing: what needs action, what's just worth knowing, what was decided in the meetings you missed, and what's still waiting on a reply. Every item appears exactly once, links straight to the thing itself, and carries a one-line reason why it made the cut.

Then — and only then — it offers to act: accept the invitation, draft the reply, post the message. Nothing is sent, posted, or booked without you picking it by name.

---

## What it does

- **Asks what to cover first.** Seven areas — Mails, Meeting Requests, Important Meetings Recap, Teams Channels, Group Chats, 1:1 Chats, Meeting Chats — or all of them. Unselected areas are never searched and never appear as empty headings.
- **Works out when you were away.** Reads your out-of-office calendar blocks and auto-reply settings, proposes the period it detected, and lets you correct it or enter your own range. It never guesses silently.
- **Scopes Teams properly.** Picks the teams and channels with you rather than scanning all 79 teams and 163 channels and burying you.
- **Prioritises on evidence, not the importance flag.** A direct question addressed to you, an approaching deadline, an escalation, a blocker, a message from your manager — those get surfaced. Newsletters, build notifications, delivery receipts and "+1" replies are silently excluded, with one quiet line per section telling you how many were left out.
- **Learns your working pattern.** Who you reply to fastest, your reporting line, which recurring meetings you actually attend versus habitually decline, and which accounts recur in your own sent mail. Anything promoted this way is labelled as inferred, so you can tell it apart from something you explicitly asked for.
- **Summarises the meetings you missed** as Decisions / Actions assigned to you / Unresolved, drawn from the real transcript where one exists — and says so plainly when one doesn't, rather than inventing a summary.
- **Links everything.** Every item's title is a deep link that opens that exact message, post, invitation or meeting — never an inbox or a channel home.
- **Then offers to act.** A numbered menu at the end: five response options on every invitation, suggested replies you can turn into drafts, Teams messages you can post. You reply `1A, 5D, 7` and only those things happen.

## What it deliberately won't do

- **Nothing is sent, posted, or booked because the recap was generated.** Suggested replies are shown as text; a real draft is created only when you pick that item, and sending it is a *separate* approval after that.
- **A link never triggers anything.** Clicking opens what it points to. Only naming an item in the action step changes anything.
- **It never invents.** No fabricated decisions, owners, deadlines or meeting content. Where a transcript is missing, a chat is unreadable, or a link won't resolve, it says so rather than filling the gap.
- **It respects a mute.** Muted chats are counted, not listed — you already told Teams you didn't want them.
- **"Draft only" sticks.** Say "don't send" once and it holds for the rest of the session: mail stays in drafts, Teams text is shown in chat rather than posted, and no calendar response goes out.

## Who it's for

Anyone returning from a week or more away with a mailbox they're dreading — and anyone who wants a single dependable catch-up rather than four separate ones. It's aimed at people whose work is spread across customers, projects, or accounts, where the important item is as likely to be a Teams channel post as an email.

It is *not* a daily briefing. For "what did I miss today", one meeting's summary, or calendar tidying, use the tools built for those; this skill routes you to them rather than duplicating them.

## Try it with

- "Prepare my holiday recap"
- "Catch me up after my holiday"
- "What did I miss while I was away?"
- "Catch me up between 4 and 18 August"
- "Return-from-leave briefing"

## How a run goes

1. **It asks which areas to cover** — pick any combination, or everything.
2. **It proposes the period** it found on your calendar; you confirm or give your own dates.
3. **It asks the few questions that scope actually needs** — priority people, priority keywords, which teams and channels, any other instruction. Questions that only serve an area you didn't pick are never asked.
4. **It searches** Outlook and Teams across the confirmed window, paginating until the period is fully covered.
5. **It reports** — Mails, Important Meetings Recap, Chats, Meeting Requests — with the scope you chose echoed at the top so you can see exactly what shaped it.
6. **It offers a numbered action list.** You choose; it executes only what you named and reports back item by item.

A typical run takes a couple of minutes and replaces about an hour of scrolling.

## Setup

Drop `SKILL.md` into your skills folder. No configuration, no API keys, no per-user setup — it uses your existing Microsoft 365 access and can only ever see what you can already see.

**Requires access to:** Outlook mail and calendar, Microsoft Teams (chats and channels), meeting transcripts, and your organisation's people directory. Everything is read with your own permissions.

## Good to know

- **Reading is safe, acting is gated.** The recap itself is read-only end to end. Every write — a calendar response, a draft, a send, a Teams post — needs you to select that specific item.
- **You'll be asked a handful of questions up front.** That's deliberate: guessing the wrong absence window or scanning every team you belong to produces a recap nobody reads.
- **A custom date range gets the same depth** as a detected out-of-office period. It works just as well for "catch me up on the last three days" as for a two-week holiday.
- **Where a link can't be produced**, it names the author, timestamp and thread so you can find the item yourself — it will never substitute a container link or make one up.

## Feedback

Issues and improvements are welcome. If the recap surfaced something it shouldn't have — or missed something it should have caught — that's the most useful feedback there is, since prioritisation is the part most worth tuning.
