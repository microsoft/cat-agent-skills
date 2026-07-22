# Spend More Time With Friends & Family

An out-of-office helper for Scout: while you're away, it quietly watches a group
chat and answers questions **from a knowledge doc you provide** — never from
guesswork — and logs anything it can't answer so nothing slips through the
cracks.

## Why use this?

When you step away, questions in a busy chat don't stop — people still ask where
a doc lives, what the status of something is, or how a process works. Most of
those have a known answer; you just aren't there to give it.

This automation gives those answers for you, using **only** a knowledge doc you
write ahead of time. You put the facts people usually ask you for into a file —
project status, links, who-owns-what, common how-tos — and while you're out, the
bot replies to matching questions straight from it. Every reply is clearly
marked as AI-generated on your behalf, so no one mistakes it for you personally.

Crucially, it **only answers what your doc actually covers**. It won't invent
facts or improvise. Anything your doc doesn't address, it never guesses at — it
writes the question down for you to handle when you're back.

## How it works

You write a knowledge doc, point the bot at the chat, and step away. Then, every
15 minutes, it:

1. **Reads new messages** in the group chat and picks out the real questions
   (skipping greetings, reactions, and small talk).
2. **Looks for the answer in your knowledge doc** — your doc is the *only* source
   of truth it's allowed to use.
3. **Replies in-chat when your doc covers it**, with a clear
   "🤖 AI-generated on the owner's behalf" caveat so it's never mistaken for you.
4. **Logs the ones your doc doesn't cover** to `unanswered.md` — who asked, what
   they asked, and when — for you to follow up on later. It never posts a guess.

Because answers come only from your doc, the quality of the bot is really the
quality of your doc: the more you write down, the more it can handle for you.

## Setting it up

On first run it bootstraps a `friends-family-bot/` folder with a blank
`config.json` and a `knowledge/` directory, then pings you on Teams telling you
exactly what to fill in. Drop your notes into `knowledge/`, set the chat to
watch, and it takes over from there. If anything required is still missing, it
messages you instead of touching the chat — so it never runs half-set-up.

| You set | What it is |
| --- | --- |
| `chatId` | The group chat to watch |
| `knowledgeDocs` | Folder(s) of notes it's allowed to answer from |
| `ownerRelayEmail` | *(optional)* Where to ping you — defaults to your Teams self-chat |
| `answerCaveat` | *(optional)* The AI-generated disclaimer text |

## Good to know

- **Your doc is the only source of truth** — it won't invent answers.
- **No backfill** — on a fresh start it only looks at the last hour, not your
  whole chat history.
- **It ignores your own messages**, so it won't reply to you.
- **Portable** — all paths are resolved relative to the Scout workspace; nothing
  personal or machine-specific is hardcoded.

## Requirements

Built for **Scout**, using its Teams/WorkIQ tools to read and reply in chat and
to relay setup reminders to you.
