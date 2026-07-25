---
name: my-great-skill
description: >-
  The AGENT-facing description. This is what the model reads to decide WHEN to
  invoke the skill, so describe the trigger precisely (e.g. "Use this skill
  whenever the user asks to … BEFORE calling …"). Keep it action-oriented.
---

Write the agent-facing instructions here as Markdown — this body becomes the
"Instructions" section on the detail page (when there's no `README.md`) and the
downloadable `skill.md`. The body loads only *after* the agent has already
decided to use the skill, so don't restate *when* to use it here — that belongs
in the frontmatter `description`. Go straight into how to do the task, in the
imperative (address the agent, not the skill — avoid "You are the … skill").

## Instructions
1. Concrete, numbered steps the agent should follow.
2. ...

## Guardrails
- What the agent must not do.

## Tone
The voice the agent should adopt.
