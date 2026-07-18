---
name: persona-reaction-panel
description: Pre-simulate how a defined set of role-based personas will react to an internal comms, launch, or enablement artefact before it ships. Use when the user asks to "run the persona panel", "pressure-test this comms against our personas", "QA this launch email/deck before it goes out", "how will each team react to this", or wants persona- and domain-level feedback on a broad internal artefact. Requires a personas file — bring your own (see references/personas.template.md). Do NOT use for 1:1 private comms, HR/performance matters, or legal/contractual language.
---

# Persona Reaction Panel

Pre-test any internal-facing artefact (launch email, all-staff deck, learning-hub page, change announcement, video script) against a defined set of **role-based personas** before it ships — so you catch blackspots, credible-detractor risks, and domain gaps while they are still cheap to fix.

This skill ships as a **framework, not a dataset**. It contains no one's personas — you supply your own in a personas file (`references/personas.template.md` is a starter you fill in with your organisation's roles). Every reaction the panel produces is anchored to an attribute *you* defined, which keeps the simulation honest and stops it drifting into generic "AI magic" feedback.

## When to use
- Before any artefact going to a broad internal population or multiple teams/domains.
- When prioritising which of several drafts to send first.
- For role-based enablement or learning-journey material.

## When NOT to use
- 1:1 private comms.
- Performance / HR matters.
- Legal / contractual language.
- A status report or new-work identification — this skill only reacts to a draft you supply.

## What you need first
A **personas file** describing the roles in your audience. Each persona needs, at minimum:
- **Role / what they do**
- **Motivations**
- **Pain points**
- **How the tool or change helps them**
- **Comms anchors** — what makes a message land vs. what makes them disengage
- **Confidence** — fully defined, or still in draft (flag draft personas as lower-confidence)

See `references/personas.template.md`. Define as many personas as your audience has distinct roles (8–12 is a good range for an enterprise). Group them into **domains** so you can spot coverage gaps.

## How a run works

### Step 1 — Load the personas file (in full)
Read your personas file completely before reacting. It is the ONLY source of truth for how each persona responds — never simulate from memory or generic assumptions.

### Step 2 — Read the artefact
Read the draft in full. Identify: what is asked, what is claimed, what is implied, what is left out, the audience it assumes, and which of your domains it actually serves.

### Step 3 — Per-persona reaction (repeat for each persona)
Six short answers per persona, each anchored to a quoted attribute from your personas file:
1. **Will they read it?** — would it land so they'd engage? (anchor: their role / pain point / motivation)
2. **What do they take away?** — first-read interpretation. (anchor)
3. **What do they push back on?** — the line, claim, or omission that stops them. (anchor a real pain point — do not invent a fear the file does not support)
4. **What did it miss for them?** — the defined need that isn't addressed.
5. **What would make them tick and stick?** — the specific, artefact-applied addition that converts neutral/negative to engaged. (anchor)
6. **Does it move them?** — net effect (up / flat / down), one sentence.

**Anti-drift rule (critical):** every paragraph must contain a quoted phrase or named attribute from your personas file. If it can't be anchored, omit it. Never import a persona's psychology from another framework onto a role the file does not support.

**Confidence rule:** for personas you flagged as still in draft, prefix the reaction with a confidence flag and route their recommendations to human validation.

### Step 4 — Synthesis
1. **Domain coverage** — which domains the artefact serves well, weakly, or excludes. An all-staff artefact that silently serves only one domain is a failure even if no single persona "breaks."
2. **Blackspots** — things no persona reacted to that the artefact assumed they would.
3. **Persona/domain risks** — who the artefact actively damages, and why. Flag "credible detractor" risk (a persona the framing turns into an active sceptic).
4. **Suggested edits** — 2–3 concrete lines to add/remove/reframe, each naming the personas it serves.
5. **Tick-and-stick recommendations** — 2–3 additive moves, each naming (a) the persona(s), (b) the anchored trigger, (c) implementable in this artefact without changing its purpose.

### Step 5 — Net read
- **SHIP** — no persona/domain risk, ≤2 minor edits.
- **REVISE** — ≥1 persona/domain risk OR ≥3 substantive edits OR a credible-detractor pattern.
- **HOLD** — targets an audience your personas don't represent, OR a domain is materially excluded, OR a draft persona is load-bearing and cannot yet be validated.

### Step 6 — Output
Save a dated file with the net read at the top; surface the synthesis inline and keep the per-persona reactions in the file. If the environment cannot save files, return the full output in the response instead, with the net read first, then the synthesis, then the per-persona reactions.

## Tick-and-stick discipline
1. Anchor every recommendation to a defined persona attribute. No anchor → drop it.
2. Don't optimise for the impossible coalition — if serving one domain damages another, surface the tradeoff; don't paper over it.
3. Constructive ≠ flattering — make the artefact more honest and specific, not warmer.

## Limits
- Role personas are role-level, not individual-psychology-level.
- Don't invent new personas mid-run. If the artefact targets an audience your personas don't represent, say so and HOLD.
- The skill identifies reactions, risks and constructive moves; **sign-off stays human.** Validate high-stakes recommendations with a named owner.

---
*A reusable framework. Bring your own personas; keep your own context private.*
