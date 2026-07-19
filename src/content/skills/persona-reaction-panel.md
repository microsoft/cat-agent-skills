---
name: Persona Reaction Panel
description: "Pre-test an internal launch, comms, or enablement artefact against your own role-based personas before it ships — surfaces blackspots, domain gaps, credible-detractor risks, and concrete edits. Bring your own personas file."
agentDescription: "Pre-simulate how a defined set of role-based personas will react to an internal comms, launch, or enablement artefact before it ships. Use when the user asks to \"run the persona panel\", \"pressure-test this comms against our personas\", \"QA this launch email/deck before it goes out\", \"how will each team react to this\", or wants persona- and domain-level feedback on a broad internal artefact. Requires a personas file — bring your own (see references/personas.template.md). Do NOT use for 1:1 private comms, HR/performance matters, or legal/contractual language."
platforms: [Cowork, Copilot Studio]
tags: [communications, change-management, launch-readiness, personas, qa]
author: Olivia Zhang
authorUrl: "https://github.com/Olivia2327"
authorGithub: Olivia2327
version: 1.0.0
bundle: bundles/persona-reaction-panel.zip
---
# Persona Reaction Panel

Simulate how each defined persona will react to the user's draft artefact, then synthesise domain-level risks and concrete edits, ending with a SHIP / REVISE / HOLD verdict.

**Personas file (required):** load the user's personas file from `references/` (or the path the user provides). Each persona provides: role / what they do, motivations, pain points, how the tool or change helps them, comms anchors, and a confidence flag (fully defined or draft). Personas are grouped into domains. If no completed personas file is available, stop and ask the user to supply one (`references/personas.template.md` is the blank template — do not run the panel against the template's example personas).

**Scope guard:** if the artefact is a 1:1 private communication, an HR/performance matter, or legal/contractual language, decline and state why. Only react to a draft the user supplies — do not write one.

## How a run works

### Step 1 — Load the personas file (in full)
Read the personas file completely before reacting. It is the ONLY source of truth for how each persona responds — never simulate from memory or generic assumptions.

### Step 2 — Read the artefact
Read the draft in full. Identify: what is asked, what is claimed, what is implied, what is left out, the audience it assumes, and which of the user's domains it actually serves.

### Step 3 — Per-persona reaction (repeat for each persona)
Six short answers per persona, each anchored to a quoted attribute from the personas file:
1. **Will they read it?** — would it land so they'd engage? (anchor: their role / pain point / motivation)
2. **What do they take away?** — first-read interpretation. (anchor)
3. **What do they push back on?** — the line, claim, or omission that stops them. (anchor a real pain point — do not invent a fear the file does not support)
4. **What did it miss for them?** — the defined need that isn't addressed.
5. **What would make them tick and stick?** — the specific, artefact-applied addition that converts neutral/negative to engaged. (anchor)
6. **Does it move them?** — net effect (up / flat / down), one sentence.

**Anti-drift rule (critical):** every paragraph must contain a quoted phrase or named attribute from the personas file. If it can't be anchored, omit it. Never import a persona's psychology from another framework onto a role the file does not support.

**Confidence rule:** for personas flagged as draft, prefix the reaction with a confidence flag and route their recommendations to human validation.

### Step 4 — Synthesis
1. **Domain coverage** — which domains the artefact serves well, weakly, or excludes. An all-staff artefact that silently serves only one domain is a failure even if no single persona "breaks."
2. **Blackspots** — things no persona reacted to that the artefact assumed they would.
3. **Persona/domain risks** — who the artefact actively damages, and why. Flag "credible detractor" risk (a persona the framing turns into an active sceptic).
4. **Suggested edits** — 2–3 concrete lines to add/remove/reframe, each naming the personas it serves.
5. **Tick-and-stick recommendations** — 2–3 additive moves, each naming (a) the persona(s), (b) the anchored trigger, (c) implementable in this artefact without changing its purpose.

### Step 5 — Net read
- **SHIP** — no persona/domain risk, ≤2 minor edits.
- **REVISE** — ≥1 persona/domain risk OR ≥3 substantive edits OR a credible-detractor pattern.
- **HOLD** — targets an audience the personas don't represent, OR a domain is materially excluded, OR a draft persona is load-bearing and cannot yet be validated.

### Step 6 — Output
Save a dated file with the net read at the top; surface the synthesis inline and keep the per-persona reactions in the file. If the environment cannot save files, return the full output in the response instead, with the net read first, then the synthesis, then the per-persona reactions.

## Tick-and-stick discipline
1. Anchor every recommendation to a defined persona attribute. No anchor → drop it.
2. Don't optimise for the impossible coalition — if serving one domain damages another, surface the tradeoff; don't paper over it.
3. Constructive ≠ flattering — make the artefact more honest and specific, not warmer.

## Limits
- Role personas are role-level, not individual-psychology-level.
- Don't invent new personas mid-run. If the artefact targets an audience the personas don't represent, say so and HOLD.
- Identify reactions, risks and constructive moves; sign-off stays human. Route high-stakes recommendations to a named owner for validation.
