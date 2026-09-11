# Root Cause Analysis

Use this skill when you need to understand why something failed — not just what went wrong, but the underlying cause you can act on.

## What it does

Root Cause Analysis (RCA) turns incident symptoms into a clear diagnosis using structured techniques:

- **5 Whys** — keep asking "why" until you reach a fixable origin.
- **Fishbone diagram** — map causes across six categories: People, Process, Technology, Data, Environment, Management.

The skill distinguishes between a **root cause** (the fundamental origin) and **contributing factors** (things that made the problem worse). That distinction changes what you fix and whether the problem stays fixed.

## When to use it

- An incident, defect, or outage happened and you need to know why.
- You are preparing a post-mortem or incident review.
- A process keeps failing in the same place and surface fixes are not working.
- You want to separate "what happened" from "what actually caused it."

## What you get

- A clear root cause statement.
- The evidence chain behind it.
- A list of contributing factors.
- Recommended actions, ordered by whether they address the root cause or only contributing factors.

## What you need

- A clear symptom or failure to investigate.
- Access to the person or system that observed the problem.
- Any available logs, timelines, or context that show what happened.

## Tips

- Start with a precise problem statement. "The service went down" is a symptom; "the payment API returned 503 for 12 minutes during the 9 AM traffic spike" is a problem statement.
- Keep asking "why" at least three levels before proposing causes.
- Contributing factors are still useful to document — they reduce recurrence even if they are not the root cause.
