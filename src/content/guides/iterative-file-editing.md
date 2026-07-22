# Iterative File Editing

In Copilot Studio today, editing a file that's already been sent to you
fails to reach you. You ask the agent to tweak a document it delivered a moment
ago; it makes the change and tells you it's done — but no new file shows up in the
chat. That's because re-sending a file under a name the chat has already received
doesn't fire Copilot Studio's file-delivery event, so the updated version never
actually leaves the agent. You're left looking at the old attachment, told it was
updated.

This skill fixes that. It has the agent give each new version of a file a fresh,
incremented filename — `report_v1.docx`, `report_v2.docx`, `report_v3.docx` — so
every round of edits carries a name the chat hasn't seen before and actually gets
delivered. You receive each iteration as its own attachment, and the version trail
comes for free.

## Why it matters

Without it, iterating on a file in Copilot Studio breaks: the agent keeps
"making changes" you never receive, and you have no signal that the send didn't
happen. A version-numbered filename is what turns "I updated it" into a file you
can actually open — it's the difference between a real back-and-forth over a
document and a one-shot export you can never refine.

## How it works

Whenever the agent has an updated version to hand you, it bumps the version number
in the filename before sending. Because the name is new, Copilot Studio delivers it
as a fresh attachment. The highest number is always your current file, and every
earlier version stays in the chat so you can scroll back.

## How to use it

Ask for a file the way you normally would — "draft a proposal", "build me a
spreadsheet", "write this script" — and give feedback as it comes back. Say
"change the intro" or "add a column" to keep refining. Each reply brings a new
numbered attachment; the highest-numbered one is your latest file.

## A quick walkthrough

Here's a short session — each attachment comes back with the next version number,
which is exactly what lets every edit land in the chat:

> **You:** create a simple text file that says "hi"
>
> **Agent:** Done! Here's your text file — it simply says "hi". Let me know if
> you'd like to change anything!  📎 `hi_v1.txt`
>
> **You:** can you add a poem to it?
>
> **Agent:** Sure! I've added a short original poem after your "hi". Want a
> different style or theme?  📎 `hi_v2.txt`
>
> **You:** and an ascii rose?
>
> **Agent:** All set — `hi_v3.txt` now has your "hi", the poem, and an ASCII
> rose 🌹. Anything else?  📎 `hi_v3.txt`

Without the version bump, that "add a poem" step would look like it worked, but
`hi.txt` would never re-appear in your chat — you'd be stuck on the original. The
climbing number (`hi_v1.txt` → `hi_v2.txt` → `hi_v3.txt`) is precisely what gets
each update delivered, and it doubles as a history you can scroll back through.

## Good to know

- It applies to any file type — documents, spreadsheets, decks, code, data
  exports.
- The version number climbing each round isn't clutter — it's the mechanism that
  makes each update reach you, and it happens to give you a clean version history.
- It's built for the Copilot Studio container specifically, because it relies on
  how that container delivers files to you.
