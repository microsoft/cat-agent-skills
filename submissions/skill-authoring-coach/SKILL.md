---
name: skill-authoring-coach
description: Use this skill when the user asks to create, improve, review, package, genericise, or submit an Agent Skill, SKILL.md file, skill metadata, or reusable agent instruction bundle.
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

1. Identify whether the user wants to create, improve, review, package, or submit a skill, along with the target platforms and any target repository or authoring tool.
2. Read the target's current authoring and submission requirements before proposing files or metadata.
3. When reviewing existing files, run available deterministic schema, layout, and packaging checks first. Report failures before qualitative feedback and recommend **Revise** until they are resolved.
4. Identify the repeatable workflow the user wants to package.
5. Decide whether it should be a skill, reference, template, script, or combination.
6. Write or improve the skill trigger description.
7. Keep instructions concise and operational.
8. Move long examples and detailed reference material out of `SKILL.md` where appropriate.
9. Check for sensitive, organisation-specific, or non-reusable content.
10. Verify that scripts, runtime dependencies, commands, and filesystem assumptions work on every declared platform.
11. Produce a candidate folder structure and files.
12. Run the available target validators again. Recommend **Submit** only when the known target requirements are met and all available checks pass; state anything that could not be verified.

## Review rubric

Score candidate skills from 0 to 5 on:

1. **Trigger clarity** - Will the agent know when to use it?
2. **Task focus** - Is it one coherent capability?
3. **Instruction quality** - Are the steps clear and repeatable?
4. **Portability** - Can others use it without private assumptions?
5. **Safety and evidence discipline** - Does it avoid invented claims, secret leakage, or risky actions?
6. **Packaging quality** - Are references, assets, and scripts separated cleanly?
7. **Target compliance** - Does it satisfy the target's schema, layout, packaging, and platform requirements?

## Output format for review

````markdown
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
````


## References

This skill includes supporting reference material. Read the relevant reference file when the task needs additional structure, rubric detail, examples, or checklist support.

- `references/skill-design-checklist.md` - use this when additional structure, examples, or checks are useful for the task.

## Quality checklist

Before responding, check:

- The proposed skill has a clear reusable job.
- The trigger description is precise.
- Organisation-specific material is removed or parameterised.
- Long reference content is not overloaded into the main skill file.
- The target's current requirements are satisfied and available deterministic checks pass.
- Scripts, dependencies, commands, and paths work on every declared platform.
- The result is practical for a maker to copy into a skills repository.
