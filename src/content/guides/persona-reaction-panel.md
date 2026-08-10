# Persona Reaction Panel

Pre-test any internal-facing artefact — launch email, all-staff deck, learning-hub page, change announcement, video script — against a defined set of **role-based personas** *before it ships*. The panel surfaces blackspots, domain coverage gaps, and "credible detractor" risks while they are still cheap to fix, and closes with a **SHIP / REVISE / HOLD** verdict.

## Why this exists

Most comms QA happens after the fact: something lands badly with one team, and you find out from the replies. This skill moves that discovery *before* send. Existing gallery skills help you **produce** content; this one simulates how your **audience** will receive it.

## A framework, not a dataset

The skill ships with **no personas**. You supply your own in a personas file — `references/personas.template.md` is a starter you fill in with your organisation's roles. Every reaction the panel produces is anchored to an attribute *you* defined, which keeps the simulation honest and stops it drifting into generic "AI magic" feedback. Your personas stay in your own copy; nothing organisation-specific is bundled or shared.

## When to use it

- Before any artefact going to a broad internal population or multiple teams/domains.
- When prioritising which of several drafts to send first.
- For role-based enablement or learning-journey material.

**Not** for 1:1 private comms, performance/HR matters, or legal/contractual language — and it only reacts to a draft you supply; it won't write one for you.

## What you need first

A **personas file** describing the roles in your audience. Define as many personas as your audience has distinct roles — **8–12 is a good range for an enterprise** — and group them into **domains** (e.g. Client, Delivery, Data, Technology, Corporate Functions) so the panel can spot coverage gaps.

Each persona needs, at minimum:

- **Role / what they do**
- **Motivations**
- **Pain points**
- **How the tool or change helps them**
- **Comms anchors** — what makes a message land vs. what makes them disengage
- **Confidence** — fully defined, or still in draft (draft personas are treated as lower-confidence and their recommendations routed to human validation)

### Filling in the template

1. Open `references/personas.template.md` in your copy of the skill.
2. List the distinct roles in your artefact's audience and group them into domains.
3. Complete every field for each persona. Two clearly-labelled `REPLACE ME` examples show the level of specificity that works.
4. Ground the fields in real role definitions or research where you have them; mark anything you're inferring as **draft — lower confidence** so the panel treats it as a hypothesis.
5. Be specific and honest — the panel anchors every reaction to what you write here, so vague personas produce vague reactions.

## How to run it

1. Add the skill to your agent (Cowork or Copilot Studio) with your completed personas file in place.
2. Give the agent your draft artefact and ask it to *"run the persona panel"* or *"pressure-test this against our personas."*
3. You get: a per-persona reaction (six anchored answers each), a synthesis (domain coverage, blackspots, risks, suggested edits, tick-and-stick recommendations), and the SHIP / REVISE / HOLD net read.

## Good to know

- Role personas are role-level, not individual-psychology-level.
- The panel won't invent personas mid-run — if your artefact targets an audience your personas don't represent, it says so and HOLDs.
- The skill identifies reactions, risks, and constructive moves; **sign-off stays human**. Validate high-stakes recommendations with a named owner.
