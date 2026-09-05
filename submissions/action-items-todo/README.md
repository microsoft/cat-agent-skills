# Action Items to To Do

Things people ask you to do arrive scattered across Teams, meetings, and mail, and the ones that get forgotten are rarely the urgent ones. This skill watches all three, works out which messages contain a genuine ask directed at you, and files each one as a Microsoft To Do task with a due date, a priority, and a link back to where it came from.

It runs on a schedule you choose. Microsoft To Do is the only place it writes tasks.

## Setup

Invoke the skill once and it asks three questions:

1. Which Microsoft To Do list captured items go into. Your existing lists are shown, and naming a new one creates it.
2. How often to scan: every 15 minutes, 30 minutes, hour, or 2 hours.
3. When to scan: around the clock every day, around the clock on weekdays, working hours on weekdays, or a schedule you describe in your own words.

The around-the-clock option exists because plenty of people work across time zones, where a 9-to-5 scan window misses half the day.

Setup writes a config file, then creates the recurring automation for you. Nothing scans before setup finishes.

## What it captures

An action item is anything asking you to do, decide, respond, review, attend, prepare, or follow up. Soft and future-dated asks count, so "when you get a chance, could you look at this?" is captured just like a hard deadline. Urgency is not a requirement.

The ask has to be aimed at you specifically. That means you are named, you are @mentioned, it arrived in a 1:1 chat, or the surrounding conversation clearly puts the item on your plate. Generic group requests, FYIs, status updates, newsletters, and notifications are skipped.

Two things it deliberately does not do: it will not treat a topic in your area as an implied assignment, and it will not capture your own promises. Commitments you make to other people have different failure modes, and combining both kinds in one list makes both harder to act on.

Task titles are always written in English, even when the source message is not.

## What each task gets

- **Due date** from an explicit or clearly implied deadline, otherwise today.
- **Priority** from detected urgency. High for blockers, escalations, ASAP language, or a deadline inside two days. Low for tentative or far-future asks. Normal for everything else.
- **Owner tagging** as a single `Customer:` or `Workstream:` line at the top of the task body. When the evidence is thin the line is left off, because an untagged task still appears in the list while a task filed against the wrong account does not.
- **Source link** back to the original Teams message, meeting, or email.

## Commands

| Command | What it does |
|---|---|
| `setup` | Re-run the wizard and update the existing automation |
| `scan now` | Run a single scan immediately and show what it found |
| `status` | Current config, last scan time, items captured in the last 7 days |
| `pause` / `resume` | Disable or re-enable the automation |

## Optional configuration

Two fields in `config.json` are not covered by the wizard:

- `owners`: lists of known customer and workstream names. Set these and tagging will only ever use a name from your list, which is worth doing if you work across a fixed set of accounts.
- `excludedChats`: chat or channel names to always ignore. High-volume group chats where people post questions into the void are the usual candidates.

## A note on Teams recency

The skill ranks chats by the timestamp of the most recent message rather than the chat's `lastUpdatedDateTime`. Microsoft Graph frequently fails to advance `lastUpdatedDateTime` on 1:1 chats, so a chat with a message from this morning can report a last-updated date from two years ago and sink to the bottom of the list. During testing this affected several chats containing real, unanswered asks.

## Privacy

Tasks go to your own Microsoft To Do. Notifications go to your own Teams self-chat. The skill never messages anyone else and never forwards the content of a source message.

Configuration and dedupe state live under your home directory, in `.scout/action-items-todo/`. Delete that folder to reset the skill completely.

## Requirements

Scout, with Microsoft 365 access for Teams, Outlook, calendar, and To Do. Meeting transcript capture only works for meetings where a transcript exists and your tenant policy allows reading it.
