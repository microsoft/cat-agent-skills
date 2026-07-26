# Work Brief

Monday, 8am. What is actually waiting on you lives in three places - Outlook, the calendar, and a dozen Teams chats - and none of them knows about the others. You open mail, get pulled into the first thread, and miss the one reply that had a meeting behind it. This skill builds the single view you never assemble yourself: what you owe people, what you are blocked on, and what to do first.

## Why it is not just a list of unread mail

Anyone can list unread mail. What earns this its place is the correlation step. An unanswered thread is one more line in a pile. The same thread linked to a meeting in the next 48 hours is a deadline nobody noticed - and that link is what gets missed when each surface is read on its own. The brief reads mail, calendar, and Teams together and leads with those.

## Basic usage

The skill runs on demand with no setup. Once it is imported into Scout, ask for it in plain language:

```
give me my work brief for the week
```

Other phrasings work just as well - "what did I miss?", "what is waiting on me?", "catch me up after two weeks off". The skill picks the time window to match the request and returns a single brief. A minimal result looks like this (names below are illustrative):

```
# Weekly brief - 26 Jul 2026
Coverage: mail, calendar, Teams - lookback 19-26 Jul - look-ahead 26-31 Jul - Europe/Paris

## Before your next meetings
- Project kickoff (Mon 10:30) - you owe the draft scope before it starts; age 3 days;
  deadline stated as Monday. next: send the scope draft. (source: thread "Kickoff prep")

## You owe people
- A teammate - asked for review comments; age 2 days; deadline implied, not stated;
  next: reply with the two open questions. (source: thread "Design review")

## Waiting on others
- Your manager - owns sign-off on the budget line; asked 6 days ago, chased once.
  (source: thread "Q3 budget")

## Do first
1. Send the kickoff scope draft - hard deadline Monday morning.
2. Reply on the design review so it is not blocked on you.
```

To personalise ranking, copy `assets/config.example.json` to `~/.copilot/work-brief/config.json` and set your priority people and projects, delivery mode, and language. To have the brief arrive on a schedule, follow `references/install-automation.md` - one automation, e.g. Monday 08:00.

## Delivery and notification go together

The brief lands one of three ways, set in config: left in the Scout run, posted to your own Teams chat, or emailed to your own work address. Each mode pairs with a notification setting. The failure to avoid is `scout` mode with notifications off: it runs every Monday and nobody knows. With Teams or email delivery the message itself is the notification. Pick the row, set both columns.

## Language

The brief is written in your language, not the tool's. By default it follows the language you write in yourself - a French user gets a French brief - or you can pin a fixed language in config. Either way it only changes how the brief reads: quotes from a colleague stay in the language they wrote in, because a quote is evidence, not prose to translate.

## Safety

Everything the brief reads - mail bodies, invites, chat, display names - is treated as untrusted data, never as instructions, so a message saying "forward this to everyone" gets summarised, not obeyed. Exactly one outbound action is ever allowed, fixed by the delivery mode: it posts or sends the brief and nothing else, no replies, no RSVPs, no forwarding, no calendar writes, and it never @mentions anyone. If a source fails, the brief says so at the top instead of quietly dropping a section, because an empty week and a broken calendar call should never look the same.
