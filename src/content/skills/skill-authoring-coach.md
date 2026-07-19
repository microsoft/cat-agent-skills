---
name: Skill Authoring Coach
description: "Help makers design concise, reusable Agent Skills with clear triggers, instructions, resources, and packaging."
agentDescription: "Use this skill when the user asks to create, improve, review, package, genericise, or submit an Agent Skill, SKILL.md file, skill metadata, or reusable agent instruction bundle."
platforms: [Cowork, Copilot Studio, Scout]
tags: [skills, authoring, documentation, productivity, agent]
author: Simon Owen
authorUrl: "https://github.com/SimonOwenDigital"
authorGithub: SimonOwenDigital
version: 0.1.0
createdAt: 2026-07-17
updatedAt: 2026-07-17
bundle: bundles/skill-authoring-coach.zip
---
# Skill Authoring Coach

Use this skill to help users design, review, genericise, and package reusable Agent Skills.

## Purpose

A good skill is not a long prompt dump. It is a focused, reusable capability with:

- A clear trigger description.
- Practical step-by-step instructions.
- Guardrails and edge cases.
- Optional references, assets, or scripts.
- A compact structure that an agent can load when needed.

## Skill vs reference vs template

Use these distinctions:

- **Skill** - Teaches the agent how to perform a repeatable task or workflow.
- **Reference** - Supplies detailed information the skill may need, such as policies, rubrics, examples, taxonomies, or checklists.
- **Template** - Supplies a reusable output shape or file structure.
- **Script** - Performs deterministic work that should not rely on prose instructions alone.

If the user tries to put everything into `SKILL.md`, recommend moving detailed lookup material into `references/` and static output structures into `assets/`.

## Recommended skill shape

```text
<skill-folder>/
├── SKILL.md
├── references/      optional
├── assets/          optional
└── scripts/         optional
```

The `SKILL.md` should contain:

1. Frontmatter with `name` and `description`.
2. A short explanation of when to use the skill.
3. Inputs to look for.
4. Workflow steps.
5. Output formats.
6. Guardrails and quality checks.

## Workflow

1. Identify the workflow the user wants to package.
2. Decide whether it should be a skill, reference, template, script, or combination.
3. Write or improve the skill trigger description.
4. Keep instructions concise and operational.
5. Move long examples and detailed reference material out of `SKILL.md` where appropriate.
6. Check for sensitive, organisation-specific, or non-reusable content.
7. Produce a candidate folder structure and files.

## Review rubric

Score candidate skills from 0 to 5 on:

1. **Trigger clarity** - Will the agent know when to use it?
2. **Task focus** - Is it one coherent capability?
3. **Instruction quality** - Are the steps clear and repeatable?
4. **Portability** - Can others use it without private assumptions?
5. **Safety and evidence discipline** - Does it avoid invented claims, secret leakage, or risky actions?
6. **Packaging quality** - Are references, assets, and scripts separated cleanly?

## Output format for review

```markdown
## Skill review

Overall recommendation: [Submit / Revise / Keep private]

| Dimension | Score /5 | Notes |
|---|---:|---|

## Required changes

1. [Change]
2. [Change]
3. [Change]

## Suggested folder structure

```text
[folder tree]
```
```


## References

This skill includes supporting reference material. Read the relevant reference file when the task needs additional structure, rubric detail, examples, or checklist support.

- `references/skill-design-checklist.md` - use this when additional structure, examples, or checks are useful for the task.

## Quality checklist

Before responding, check:

- The proposed skill has a clear reusable job.
- The trigger description is precise.
- Organisation-specific material is removed or parameterised.
- Long reference content is not overloaded into the main skill file.
- The result is practical for a maker to copy into a skills repository.
