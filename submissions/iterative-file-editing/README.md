# Iterative File Editing

Turns file creation in a Copilot Studio agent into a genuine back-and-forth.
Instead of generating a file once and calling it done, the agent keeps a durable
working copy and re-shares an updated version every time you have feedback — so
you and the agent shape the file together, turn after turn, without ever losing
earlier work.

## How it works

The agent keeps a single file and refines it in place as you give feedback. Each
time there's something new to see, it hands you the current version as a
downloadable attachment — numbered `_v1`, `_v2`, `_v3`, and so on — so you can
watch the file evolve without the agent ever rebuilding it from scratch or dropping
something you'd already settled on. When you're happy, the latest version is your
final file.

## How to use it

Just ask for a file the way you normally would — "draft a proposal", "build me a
spreadsheet", "write this script" — and give feedback as it comes back. Say things
like "change the intro" or "add a column" to keep refining, and "looks good" or
"that's the one" when you're happy. The latest version in your attachments is the
final deliverable.

## A quick walkthrough

Here's a short session — notice how each attachment comes back with the next
version number as the file evolves:

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

Each round you get a new numbered attachment (`hi_v1.txt` → `hi_v2.txt` →
`hi_v3.txt`), so you can always open the latest and still scroll back to earlier
versions.

## Good to know

- It applies to any file type — documents, spreadsheets, decks, code, data
  exports.
- You'll get a fresh, numbered attachment each round; that's intentional, so you
  can always see the current state and trace the history.
- When you say you're done, the agent treats that as closing the loop — it won't
  keep revising the file unless you ask for something new, so "done" means done.
- It's built for the Copilot Studio container specifically, because it relies on
  how that container delivers files to you.
