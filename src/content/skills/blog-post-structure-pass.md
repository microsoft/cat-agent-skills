---
name: Blog Post Structure Pass
description: Restructure draft or existing blog posts into a stronger narrative without inventing new claims.
agentDescription: "Use this skill when the user asks to restructure, reorganise, improve, rewrite, tighten, or strengthen a blog post, article, newsletter, essay, or thought-leadership draft."
platforms: [Cowork, Copilot Studio, Scout]
tags: [blog, writing, authoring, content, structure, productivity]
author: Simon Owen
authorUrl: "https://github.com/SimonOwenDigital"
authorGithub: SimonOwenDigital
version: 0.1.0
createdAt: 2026-07-17
updatedAt: 2026-07-17
bundle: bundles/blog-post-structure-pass.zip
---
# Blog Post Structure Pass

Use this skill to improve the structure, argument, flow, and readability of a blog post while preserving the source facts and the author's intended point of view.

## Core rules

- Do not invent evidence, examples, client stories, dates, results, or quotes.
- Preserve the author's stance unless asked to change it.
- Improve the shape of the argument before polishing sentences.
- Keep the revised post suitable for the intended audience and channel.
- If important evidence is missing, mark it as a gap rather than filling it in.

## Default post skeleton

Use this skeleton as a guide, not a rigid template:

1. **Hook / tension** - Why this matters now.
2. **Problem** - What people usually misunderstand or struggle with.
3. **Reframe** - The more useful way to think about it.
4. **Practical implications** - What changes in decisions, behaviour, governance, delivery, or operations.
5. **Example or proof** - Evidence from supplied material.
6. **Takeaway** - What the reader should do, question, or remember.

## Workflow

1. Read the source post or draft.
2. Identify the current thesis and intended audience.
3. Diagnose structural issues: weak opening, unclear argument, repetition, missing transitions, unsupported claims, premature solutioning, or weak ending.
4. Create a revised outline.
5. Rewrite the post into the improved structure.
6. Preserve factual claims from the source and avoid adding unsupported material.
7. Provide a short change note only if useful.

## Output format

```markdown
# [Revised title]

[Rewritten post]

---

## Change notes

- [Only include important changes, assumptions, or evidence gaps.]
```

If the user asks for the structure only, use:

```markdown
## Recommended structure

1. [Section]
2. [Section]
3. [Section]

## Rationale

[Short explanation]
```


## References

This skill includes supporting reference material. Read the relevant reference file when the task needs additional structure, rubric detail, examples, or checklist support.

- `references/post-structure-patterns.md` - use this when additional structure, examples, or checks are useful for the task.

## Quality checklist

Before responding, check:

- The revised post has a clear thesis.
- The opening creates relevance quickly.
- The middle develops the argument rather than listing points.
- The ending lands the insight or next action.
- No unsupported facts have been added.
- The copy sounds natural and human.
