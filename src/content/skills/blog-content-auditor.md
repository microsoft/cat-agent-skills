---
name: Blog Content Auditor
description: "Audit blog posts or a blog library for clarity, structure, evidence, audience fit, and improvement priority."
agentDescription: "Use this skill when the user asks to audit, review, score, rationalise, prioritise, refresh, or improve blog posts, article libraries, newsletters, or thought-leadership content."
platforms: [Cowork, Copilot Studio, Scout]
tags: [blog, content, audit, writing, seo, productivity]
author: Simon Owen
authorUrl: "https://github.com/SimonOwenDigital"
authorGithub: SimonOwenDigital
version: 0.1.0
createdAt: 2026-07-17
updatedAt: 2026-07-17
bundle: bundles/blog-content-auditor.zip
---
# Blog Content Auditor

Use this skill to audit individual blog posts or a wider blog library and produce a prioritised improvement plan.

## Scope options

The skill can handle:

- A single post supplied as text or a URL.
- A list of posts supplied by the user.
- A blog index if the agent has suitable web or content access.
- Draft posts before publication.
- Existing thought-leadership libraries that need rationalisation.

## Evidence rules

- Audit only posts that are supplied or accessible.
- Do not invent traffic, ranking, engagement, conversion, recency, or SEO performance data.
- If the user wants performance analysis and no analytics are available, state that analytics were not available and assess editorial quality only.
- Quote or reference specific observed features when justifying recommendations.

## Default audit dimensions

Score each post from 0 to 5 for:

1. **Reader promise** - Is the post clear about why the reader should care?
2. **Opening strength** - Does the opening create relevance quickly?
3. **Argument shape** - Is there a coherent point of view, not just a list of observations?
4. **Evidence and examples** - Are claims supported by examples, experience, references, or practical detail?
5. **Structure and scanability** - Is the post easy to navigate?
6. **Distinctiveness** - Does it avoid generic commentary?
7. **Next action** - Does the post help the reader think or act differently?

## Workflow

1. Identify the available posts and the audit objective.
2. Read each accessible post fully enough to assess the dimensions.
3. Score each dimension with evidence.
4. Identify content that should be kept, refreshed, merged, expanded, or retired.
5. Produce a prioritised editorial backlog.
6. If relevant, identify themes missing from the current library.

## Single-post output

```markdown
## Blog audit summary

Overall score: [x]/5
Recommended action: [Keep / Refresh / Rewrite / Merge / Retire]

## Scorecard

| Dimension | Score /5 | Evidence | Recommended improvement |
|---|---:|---|---|

## Highest-value improvements

1. [Improvement]
2. [Improvement]
3. [Improvement]

## Suggested revised angle

[Suggested angle]
```

## Library output

```markdown
## Blog library audit summary

| Post | Overall score /5 | Recommended action | Reason |
|---|---:|---|---|

## Priority backlog

| Priority | Post | Action | Rationale | Effort |
|---|---|---|---|---|

## Content gaps

- [Gap]
```


## References

This skill includes supporting reference material. Read the relevant reference file when the task needs additional structure, rubric detail, examples, or checklist support.

- `references/blog-audit-rubric.md` - use this when additional structure, examples, or checks are useful for the task.

## Quality checklist

Before responding, check:

- The audit does not claim performance data unless supplied.
- Recommendations are tied to evidence.
- The user can see what to improve first.
- The output separates editorial judgement from measurable analytics.
