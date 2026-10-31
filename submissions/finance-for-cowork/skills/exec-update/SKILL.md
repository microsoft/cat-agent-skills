---
name: "exec-update"
description: >-
  Compresses content you already have into an executive-ready update: strict
  TL;DR / Key numbers / Risks / Ask structure, ~150 words, answer first. Use
  when the user asks to "turn this into an exec update", "summarize this for my
  VP", "make this leadership-ready", "give me a TL;DR for the CFO", or "compress
  this into a status note". Do NOT use for assembling an update from your own
  recent activity, org-wide announcements, long-form reports (use docx), or
  analysis that does not exist yet.
metadata:
  icon: MailDataBar
---

# Executive Update

Turns working material into a tight update sized for a senior leader's inbox. Trims narrative,
never substance — load-bearing numbers and critical caveats always survive the cut.

## When NOT to Use

- **Recurring status updates gathered from your own recent work** (weekly progress, "what did my
  team ship") → outside this skill's scope. The distinction is the input: this skill
  **compresses material you already have**; it does not **assemble** an update from your activity.
- **Voice-matched ghostwriting** ("write it the way I would") → outside this skill's scope
- **Peer-level notes** (teammate to teammate) — just write it directly, no structure needed
- **Broad team announcements, all-hands, or org-wide comms** → outside this skill's scope
- **Generating analysis that doesn't exist yet** — build it first (`xlsx`, Power BI), then use this
- **Long-form documents** — this produces a short update, not a report → use `docx`

## Workflow

### 1. Resolve the audience — never assume

If the user names a person, resolve them with `me_profile-SearchPeople`. If they say "my manager",
"my director", or "my skip-level", use `me_profile-GetManagerDetails`. If they name a role with no
person ("the CFO", "finance leadership"), search the directory before asking.

**Never construct an email address from a name pattern.** If resolution returns multiple plausible
matches, present them with `core-AskUserQuestion`; if it returns nothing, draft inline and say the
recipient wasn't found.

Adapt to seniority: the more senior the audience, the shorter the update and the earlier the ask.

### 2. Read the source

Source may be inline text, a file in `input/`, or a recent email or Teams thread. If the user
refers to "that thread", "what I just sent", or "the numbers from this morning", look it up with
`m365_search-SearchM365`, `outlook-GetMessage`, or `m365_teams-ListChatMessages` — don't ask them
to paste it.

### 3. Extract what's load-bearing

- **Numbers anchored to context** — a figure with its comparison, delta, or timeframe
- **Risks** — specific and named, never generic ("vendor SLA slipped twice in Q3", not "execution risk")
- **The implicit ask** — what does this leader need to *do*, decide, or simply know?

If the ask is genuinely unclear, ask once: decision, awareness, or escalation?

### 4. Draft in the four-part structure

- **TL;DR** — 1-2 sentences carrying the "so what"
- **Key numbers** — 3-5 bullets, one number per bullet, each with context
- **Risks / watch-items** — what could change the picture
- **Ask** — the specific action or decision needed; label "FYI" when purely informational

**Style rules (blocking):**

- Lead with the answer, not the setup
- No unquantified hedging — "70% confident" beats "appears likely"
- Active voice, concrete verbs (landed, slipped, recovered, accelerated)
- Cap the body at ~150 words; tight beats comprehensive

### 5. Deliver

| User says | Action |
|---|---|
| nothing about delivery | **Inline draft in chat.** Do not create a draft or send. |
| "draft it" / "save a draft" | `outlook-CreateDraftMessage` — draft only, never send |
| "send it" | **Confirmation gate:** preview the exact recipient, subject, and body, get explicit confirmation from the user, and only then call `outlook-SendEmailWithAttachments`. Never send without that confirmation. |
| "don't send" / "let me review" | Inline or draft only — this instruction stays in force for the rest of the task |

## Output Format

Plain text the user can copy, in the four-part structure. No preamble, no "here's your update" —
lead directly with the TL;DR. Note the word count so they can see it cleared the cap.

### Example

Source: *"Q3 came in at 4.2M vs 4.5M plan. Enterprise renewals were slow, two deals pushed to Q4.
Pipeline for Q4 looks like 5.1M but one deal is 40% of it. Might need more SE coverage."*

Output:

> **TL;DR** — Q3 landed at $4.2M, 7% under plan, on two enterprise renewals that slipped to Q4.
> Q4 coverage looks adequate but concentrated.
>
> **Key numbers**
>
> - Q3 revenue $4.2M vs $4.5M plan (−$0.3M, −7%)
> - Two enterprise renewals slipped, both now forecast in Q4
> - Q4 pipeline $5.1M
> - One deal represents 40% of that pipeline
>
> **Risks** — Q4 depends on a single deal closing; SE coverage is thin on the slipped renewals.
>
> **Ask** — Approve two additional SE allocations for Q4, or confirm we carry the concentration risk.

*(98 words. Note what survived: every number kept its comparison, and the vague "might need more
SE coverage" became a specific, decidable ask.)*

## Guardrails

- **Never fabricate.** Every number, name, date, and claim must come from the source material or a
  tool result — never from inference or memory. If the material is thin, say what's missing and
  leave a clearly marked gap rather than padding. Do not invent a figure to complete a bullet.
- **Surface contradictions** rather than smoothing them over.
- **Never strip a critical caveat to hit the word count** — trim narrative instead.
- **Never evaluate an individual's performance**, even by implication. Report project outcomes and
  deliverables, not people.
- **Default to not sending.** An explicit do-not-send instruction outranks any send default, and
  stays in force for the remainder of the task.
- **Confirm before any irreversible action.** Sending is irreversible — always preview and confirm
  the recipient first, since a misrouted executive update cannot be recalled.
- Confidential or sensitive source material stays in the draft you hand back — never forward it
  onward without being asked.
