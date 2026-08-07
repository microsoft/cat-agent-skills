---
name: pattern-radar
description: Scan the user's recent Microsoft 365 signals (emails, active chats/channels, calendar subjects) to surface recurring patterns worth productizing — either as a blog post (the user explains the same thing repeatedly) or as an automation (the user does the same multi-step task repeatedly). Use when the user asks "what should I write about?", "what could I automate?", "find patterns in my work", or invokes "/pattern-radar".
---

# Pattern Radar

Find recurring patterns in the user's recent work signals that could be turned
into leverage — a **blog post** (the user keeps explaining the same thing) or an
**automation** (the user keeps doing the same manual, multi-step task). Give
blog and automation candidates equal weight; bias toward automation candidates,
since offloading repetitive work is usually the bigger win.

Default lookback window: **the last 7 days** from the current date/time. Treat
the provided current datetime as authoritative — never reason from training-data
dates.

> **Tool names.** This skill refers to Microsoft 365 tools as `m365_*`. If your
> host exposes them under different names, map them to the equivalent capability.

## Inputs — collect breadth, not depth

1. **Email** — list Inbox and Sent from the last 7 days (subjects + first-line
   previews only; do not open bodies). **Pay special attention to Sent items**:
   they reveal the user's own repeated outbound actions (forwards, intros, status
   pings, FYIs, "looping in X" handoffs, RSVPs, reschedules).
2. **Active chats** — list recent chats; for each chat the user has posted in
   over the last ~30 days, fetch the last 7 days of messages. Strip @-mention
   noise.
3. **Active channels** — for channels the user has posted in over the last ~30
   days, fetch the last 7 days of messages. Skip silent channels.
4. **Calendar** — list events from the last 7 days (**subjects only** — no
   bodies, no attendee lists). Look for repeated reschedules, repeated tentative
   responses, recurring conflict patterns, and meeting-prep cadences.

## Clustering — what counts as a pattern

A signal qualifies only if it appears **≥3 times across ≥2 distinct people /
chats / customers / threads / events** in the window. Be ruthless — one-offs are
noise.

**Blog cluster types**

- **Repeated explanation** — the user answers the same question or explains the
  same concept to 3+ different people. → blog candidate.
- **Recurring FAQ** — the same question shows up in 3+ chats/channels from
  different askers. → blog / FAQ candidate.

**Automation cluster types (cast a wide net)**

- **Repeated multi-step manual task** — the same sequence of clicks / drafts /
  file moves / API calls, repeatedly. → automation candidate.
- **Repeated handoff / triage** — forwarding, "looping in", or intro'ing the
  same kinds of items to the same people 3+ times. → auto-route by rule or
  classifier.
- **Repeated status pings / FYIs** — the same kind of update to the same audience
  on a cadence. → scheduled digest.
- **Repeated meeting reschedules** for the same root cause. → auto-propose
  alternates.
- **Repeated RSVPs / tentative responses** to recurring meetings with consistent
  reasoning. → auto-respond by rule.
- **Repeated meeting prep** — gathering the same context before recurring
  meetings. → pre-meeting brief.
- **Repeated doc/wiki updates** — manually appending the same kind of content on
  a cadence. → scheduled ingest.
- **Repeated approvals / sign-offs** of the same class of request. → rule-based
  pre-screen.
- **Repeated file/data shuttling** — move/rename/reformat between systems. →
  pipeline.
- **Repeated drafting** — near-identical emails/messages (welcome notes,
  onboarding intros, availability, "I have a conflict" replies, follow-ups). →
  template + auto-fill.

**Anti-patterns — do NOT surface**

- Normal recurring meeting cadence (standups, weekly syncs) UNLESS there's
  repetitive *manual* work around them that could be automated.
- Anything needing the body of an excluded/private email to reason about.
- Automations the user already runs.

## Output

List **0–3 candidates max**. If signal is thin (< 3 reinforcing data points
across all clusters), output: `✅ No new patterns this run.`

Prefer a **mix** — include at least one automation candidate when one qualifies,
even if a blog candidate is stronger.

Per candidate (≤3 lines each):

```
💡 **<theme in 5–8 words>**
   _evidence:_ <1–2 anonymized signals, e.g. "forwarded 4 customer asks to the
   same engineer this week" or "explained X to 4 different people in chats">
   **<blog|automation>** · <1-line rationale. For automation, name the trigger
   and the action, e.g. "trigger: incoming request → action: auto-route + draft
   reply".>
```

## Privacy & guardrails

- **Read-only.** Never send any email, chat, channel reply, or Teams message from
  this skill. Producing the report is the only output.
- **Anonymize.** Never include customer/team names, attendee names, meeting
  times/locations, file paths, or full subjects containing customer identifiers.
  Say "3 different customers", not the actual names.
- **Respect exclusions.** Never open or paraphrase content the user has marked as
  private or excluded (e.g. performance-review or confidential emails).
- When in doubt that a candidate is a real pattern vs. coincidence, drop it —
  silence is safer than noise.
