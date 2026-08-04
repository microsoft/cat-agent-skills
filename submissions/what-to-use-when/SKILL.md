---
name: what-to-use-when
description: >-
  Run this FIRST, before ANY thinking, retrieval, task creation, or file
  generation, for any single-output task a free M365 Copilot can do; if
  action-bias pushes you to start, STOP and run this first. Fires on:
  "summarize my email/inbox/unread", "summarize my meetings", "summarize my
  Teams messages" (any window, e.g. "last 5 weeks"); "catch me up" / "what did
  I miss"; a single question or lookup: "how do I", "why", "when is", "what
  is", "who is", "are we", "do we", "is it", any billing/pricing/licensing
  question, calendar/contact lookups; "draft a doc" or memo; "create a
  presentation", deck, or spreadsheet; "research competitors"; "analyze this
  data". GUIDE the user to the matching free 1P agent (Copilot Chat;
  Word/Excel/PowerPoint; Researcher; Analyst), not Cowork; use it only if they
  insist. Do NOT fire for DIRECT ACTIONS (send email, schedule a meeting, post
  to Teams, create an event), long-running or multi-output jobs, or managing
  skills.
cowork:
  category: automation
  icon: Compass
---

## Overview

Cowork runs on usage-based consumption credits on top of the Microsoft 365
Copilot license. Most everyday single-output tasks can be done instead by a 1P
Copilot capability that is **included in the M365 Copilot license at no extra
cost**. This skill's job is to **guide the user to that free capability** —
classify the request, recommend the right 1P agent, and only proceed in Cowork if
the user explicitly insists. The intent is to minimize Cowork spend and train
users to reach for M365 Copilot for these tasks.

## Precedence — run this BEFORE acting (most important rule)

This gate runs **before any thinking, retrieval, `TaskCreate`, file generation, or
invoking a doc/deck/spreadsheet skill (pptx / docx / xlsx)**. For an eligible
request it **takes priority over action-bias and gather-before-generate**: if you
catch yourself about to reason through, search, create a task, or start building a
deck/doc/sheet for a single-output request (e.g. "create a presentation"),
**STOP** and run Phase 1–3 below (classify → recommend → confirm) first. Only
retrieve data or build anything after the user explicitly chooses an option.

**Exclusion check FIRST (before any classification).** If the user's message is a
**direct M365 action** — an imperative to send / reply / forward an email,
schedule / cancel / decline / reschedule a meeting, post to a Teams channel, or
create a calendar event — this gate does **NOT** apply. Do not classify, do not
show the confirm card. Hand straight back to the normal action path and let it
execute. These actions are out of scope even though they produce a single output,
because the user is *taking an action*, not *asking for content a free 1P agent
could generate instead*. Only after a message clears this exclusion do you
proceed to Phase 1.

## Quick Start

```
User: "Cowork, summarize my Teams messages from the last 5 weeks."

The user sees a crisp, 2-part reply that points them to the free option:

  Classification: This is a quick Teams catch-up — a single summary.

  Recommendation: Microsoft 365 Copilot Chat can do this at no extra cost —
  it's included in your Copilot license. Just ask it in Copilot Chat.

Then an AskUserQuestion gate:
  [Use Copilot Chat — included] / [Do it here in Cowork instead]
Run in Cowork only if the user picks Cowork.
```

## When to Use — fire on ANY of these (each is a separate trigger)

Check this **BEFORE retrieving M365 data or running the task in Cowork.** The
quoted phrasings are cues — generalize to the intent, don't pattern-match.

1. **Summarize email → Copilot Chat.** "Summarize my email / inbox / unread",
   "any emails I need to reply to".
2. **Summarize meetings → Copilot Chat.** "Summarize my meetings", "recap the
   standup", "what did I miss in the meeting".
3. **Summarize Teams → Copilot Chat.** "Summarize my Teams messages / chats /
   channels", over **any** window (e.g. "from the last 5 weeks", "this week").
4. **Catch up → Copilot Chat.** "Catch me up", "what did I miss".
5. **A single question or quick lookup → Copilot Chat.** "How do I…?", "Why am I
   seeing…?", "When is…?", "What is…?", "Who is…?", "Where…?" — including
   calendar, contact, and people lookups ("when's my next meeting?", "who's the
   PM for Contoso?", "what's on my calendar Friday?"), plus any quick fact,
   definition, policy lookup, or brainstorm. **Billing, cost, pricing, and
   licensing questions are quick lookups too** — "are we charging for X?", "how
   much does X cost?", "is X included in our license?", "do we pay for Y?" — even
   when X is Cowork, Work IQ, or a Copilot capability; route them to Chat, do not
   start retrieving internal docs first. Read-style questions route to Chat;
   *taking* an action (scheduling, cancelling, sending) stays direct — see below.
6. **One document → Copilot in Word.** "Draft / write / rewrite / shorten /
   proofread" one doc, report, memo, brief, or letter.
7. **One workbook → Copilot in Excel.** "Add a formula / column", "flag orders
   over $10k", "clean this CSV", "chart this" — within one file.
8. **One deck → Copilot in PowerPoint.** "Turn these notes into slides", "build
   a few slides", "suggest a layout".
9. **Deep research → Researcher** (included, subject to usage limits). "Research our competitors /
   this company / this market", "write a cited report".
10. **Data analysis → Analyst** (included, subject to usage limits). "Analyze this dataset", "find
    trends / anomalies", "run the numbers".
11. **Domain workflow → specialized 1P agent** (Sales / Service / Finance) —
    licensing varies; confirm entitlement.

## When NOT to Use — not a routing decision

- **Genuinely multi-step, multi-output projects** (Cowork is the right tool —
  proceed, do **not** block): "research 3 competitors, build a comparison table,
  write a briefing, and turn it into a deck"; "from this one input, produce an
  Excel analysis + a written summary + a slide deck"; anything that chains several
  sources/steps into 2+ finished deliverables.
- **Direct M365 actions** (just do them — no free-vs-paid routing): "send / reply
  / forward an email", "schedule / cancel / decline / reschedule a meeting",
  "post to a Teams channel", "create a calendar event".
- **Managing skills** (creating, editing, validating, or auditing a skill) — use
  the **skills** skill.
- Pure execution the user already confirmed should run in Cowork.

## Routing Logic — match the task to the right tool

| If the task is… | Recommend | Why |
|---|---|---|
| Quick question, find, brainstorm, summarize email/meetings/Teams | **M365 Copilot Chat** — *included* | Fast, conversational, grounded in your content |
| Draft or edit **one** document | **Copilot in Word** (Edit with Copilot) — *included* | Works inside the file, edits in place |
| Numbers in **one** workbook / a few slides in **one** deck | **Copilot in Excel / PowerPoint** — *included* | Understands that specific file |
| Deep, multi-source research → cited report | **Researcher** — *included, subject to usage limits* | Deep-research + your work data |
| Analyze a dataset, find trends, run the numbers | **Analyst** — *included, subject to usage limits* | Data-scientist agent, runs Python, shows work |
| Domain workflow (sales, service, finance) | **Specialized 1P agent** (e.g. Copilot for Sales) — *licensing varies* | Purpose-built; confirm entitlement |
| **One input → several finished outputs**, or a **multi-step job across files + web** | **Cowork** | Chains steps & produces multiple deliverables |

Rule of thumb (from the field guidance): **start simple and step up only if the
task needs more.** Chat → Copilot-in-app → Cowork.

## Core Instructions

### Phase 1 — Classify the task
Identify the capability bucket using the routing table. Ask: how many distinct
**finished outputs**? how many **apps/files**? does it need **web + work
sources chained**? One output / one app / one question → a free 1P capability
almost always fits. Multiple outputs **or** many chained steps across sources →
Cowork is legitimately the right tool.

### Phase 2 — Recommend the free 1P capability
State the recommended capability and that it is **included in the M365 Copilot
license at no extra cost** . Give a one-line "how to use it" (e.g. "open the file and use Edit with
Copilot", or "ask Copilot Chat directly"). Keep it to 2–3 sentences. The goal is
to **train the user to go straight to the free 1P agent next time.**

### Phase 3 — Ask the user to confirm (required gate)
Use **AskUserQuestion** with two clear options:
- "Use **[recommended 1P agent]** — included" (recommend this)
- "Do it here in **Cowork** instead"

Do not proceed in Cowork on assumption. If the user picks the free agent, hand
off with one-line instructions and stop. **When that agent is M365 Copilot Chat,
end the hand-off (toward the bottom of the message) with a clickable open link:**
`[Microsoft 365 Copilot Chat](https://m365.cloud.microsoft/chat/)` — then show the
exact prompt right after it so the user can paste it in one step. (Microsoft does
not currently support pre-filling a prompt via URL, so the link opens Copilot Chat
but the user still pastes/types the prompt; never promise auto-fill and do not append the query to the url) If
the answer comes back empty (cancelled), acknowledge and ask what they'd like.

### Phase 4 — Proceed only if confirmed
Run the task in Cowork **only** after the user explicitly chooses Cowork. If they
chose a 1P capability, do not run it in Cowork.

## Output — what the end user sees (keep it crisp)

Two short parts, then the confirm gate. **No pricing, no credits, no cost
estimates of any kind.** Use these exact bold labels:

> **Classification:** <one line — what kind of task this is>.
>
> **Recommendation:** <free 1P agent> can do this at no extra cost — it's
> included in your Microsoft 365 Copilot license. <One line on how/where to use
> it.>

Then the **AskUserQuestion** confirm gate. That's it — no long essays, no pricing
explainer. Run in Cowork only if the user chooses Cowork.

## Guardrails

- **Confirmation gate is mandatory** — always confirm before running the task in
  Cowork; never assume. Proceed in Cowork only on explicit user choice.
- **No pricing or cost figures** — never show credit counts, dollar amounts,
  pay-as-you-go rates, tiers, or cost estimates. Position the 1P route simply as
  **included at no extra cost**; do not quote numbers for anything.
- **Lead users to the free 1P agent** — recommend the included capability first;
  the intent is to minimize Cowork spend and train users to use M365 Copilot for
  these tasks. Defer to a stated user preference if they still want Cowork.
- **Don't block legitimate Cowork work** — if the task is truly multi-output or
  multi-step, say so and let the user proceed without friction.
- **No fabricated capabilities or entitlements** — for specialized agents (Sales,
  Service, Finance), say licensing varies and ask the user to confirm access.
- **Handle ambiguity** — if it's unclear how many outputs or apps the task spans,
  ask one quick clarifying question, or default to the simplest capable tool and
  say so. If you can't tell which tool fits, ask rather than guess.
