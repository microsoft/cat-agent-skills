# AI-First Process Redesign

## Overview

A facilitated, step-by-step partner for reimagining an existing work process as **AI-first**.
Instead of adding an agent on top of today's steps, it rebuilds the process from zero and
decides, step by step, what **AI should own**, what should be a **human + AI hybrid**, and what
should stay **human-led**. You finish with a clear before-and-after picture and a short, practical
plan you can start on in the next sprint.

**Important:** this skill redesigns the *process* and points to *where* AI could help — across
process changes, tools, reusable skills, agents, and connected agents. It does **not** design or
build any of them itself. Think of it as the "rethink the work" step that comes *before* any
agent- or skill-building.

By the end you have:

- A **one-page summary** — outcome, current pain points, the proposed AI-first process, and the expected benefits.
- A **current-state map** of today's tasks, with the trouble spots highlighted.
- A **future-state blueprint** showing each step tagged `AI-owned` / `Hybrid` / `Human-led`.
- A **"what changed" list** — removed / automated / augmented / kept / new.
- A **summary table** sorting every activity into **Simplify / Automate / AI Agents / Human / Remove**.
- A short **backlog of the top AI-capability opportunities** — the right mix of process changes, tools, reusable skills, and agents — plus notes on adoption and governance.

## Before you start

- **Where it runs:** Microsoft Copilot Studio, added as a skill on an agent. Alternatively install in Copilot Cowork as a custom skill.
- **Best with knowledge attached (optional but recommended):** your organisation's AI-first
  design principles, an agent-pattern reference, and any past redesign examples. Attaching these
  makes the recommendations specific to your organisation instead of generic. Without them the
  skill still works — it simply labels anything it has to assume so you can confirm it.
- **No special permissions needed to hold the conversation.** You only need connectors and
  sign-in if you choose to let it create a document or push the backlog into Planner or Azure
  DevOps — and it always asks before creating anything.
- **Have one real process in mind** (for example: invoice approval, client onboarding, monthly
  reporting). You don't need to prepare anything — it will ask.

## How to use it

Describe the process you want to rethink, in plain language. For example:

- "Help us make our supplier onboarding process AI-first."
- "Rethink how we produce the monthly board report."
- "Which parts of our claims handling should AI own?"

It then walks you through short phases: framing the goal, expanding the possibilities, capturing
how the work happens today, probing the constraints, and rebuilding the process AI-first —
finishing with the output package described above.

**Two ways to run it:**

- **Guided (default):** it asks about your tasks, triggers, pain points, and volumes as it goes.
  The more you share, the sharper and more credible the redesign.
- **Fast:** if you're short on time or just want the thinking, say something like *"just rethink
  it from what I've told you."* It produces the redesign from a brief understanding and clearly
  labels any assumptions for you to check later.

You can steer it at any point — ask it to go deeper on one stage, focus on a specific pain point,
or jump straight to the summary.

## Good to know

- **It reshapes the work; it does not build the agents or skills.** The backlog it produces is a
  prioritised list of *opportunities* — each with the recommended building block (a process
  change, a tool, a reusable skill, an agent, or a connected agent) — to hand to a separate build
  step. No prompts or connector configuration.
- **It challenges "do we even need an agent?"** Often a simpler process change, a tool, or a
  reusable skill unlocks the value — it weighs those alongside agents rather than defaulting to
  one. Expect constructive push-back before it endorses an agent.
- **Assumptions are labelled, not hidden.** Any system, integration, or number it is unsure of is
  flagged for you to validate — it will not present guesses as fact.
- **Keep it confidential-safe.** Don't paste personal data, client secrets, or credentials. If
  sensitive detail comes up, it will suggest removing it and continue in general terms.
- **It's a conversation, not a form.** It works best over a few turns, summarising as it goes.
  You can pause and come back.
- **One process at a time** gives the best result. If you have several, it ends by asking which
  to tackle first — the highest-volume, the most painful, or the fastest to show value.
