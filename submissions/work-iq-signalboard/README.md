# Work IQ Signalboard

Twenty-eight days of work, in full color.

> **Built for the preview:** This skill targets Work IQ (preview) in Copilot
> Studio and may break or need an update when Work IQ reaches general
> availability. Its sole purpose is to show Work IQ running in the new
> orchestrator.

Ask:

> Show me my Work IQ Signalboard.

The skill turns four weeks of Microsoft 365 activity into a colorful,
self-contained dashboard covering meetings, mail flow, Teams chats, and weekly
rhythm. The result is a single HTML file you can open, download, or put straight
on the big screen.

## Real signals, no filler

The board shows the numbers behind the pattern: meeting count and hours, sent
versus received mail, Teams chat messages, calendar rhythm, and four weekly
totals that reconcile with the 28-day count. A short AI reflection closes the
board without turning activity into a productivity score.

It counts the work without displaying the work. Names, subjects, message text,
filenames, links, projects, customers, and exact dates stay out.

If Work IQ cannot read a source, the board says **No data**. It never turns a
missing source into a measured zero, and it never guesses at work modes,
fragmentation, focus, or working-hour boundaries.

## Before you start

Use the new Copilot Studio agent experience and add **Work IQ (preview)** from
**Tools > Add Tool > Model Context Protocol**. The tenant needs Work IQ enabled,
a connection for the signed-in user, and the required spending policy.

[Set up Work IQ in Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/add-work-iq)

## Try it

- “Show me my Work IQ signals.”
- “Build my Work IQ Signalboard.”
- “Turn my last four weeks into a Work IQ dashboard.”

The skill uses a rolling 28-day window, works around the preview harness's
collection caps, reports missing sources, and produces the dashboard without
external web resources.

Files are outside the current Signalboard scope. Work IQ preview does not expose
an exhaustible recent-file activity feed, so the skill does not guess from a
partial folder listing or search result.
