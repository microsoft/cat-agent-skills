---
name: Content Quality Auditor
description: "Score documents, pages, posts, or artefact libraries against a configurable quality rubric and recommend fixes."
agentDescription: "Use this skill when the user asks to assess, audit, score, review, improve, prioritise, or quality-check content, documents, pages, posts, decks, or reusable artefacts."
platforms: [Cowork, Copilot Studio, Scout]
tags: [content, quality, audit, documents, productivity, governance]
author: Simon Owen
authorUrl: "https://github.com/SimonOwenDigital"
authorGithub: SimonOwenDigital
version: 0.1.0
createdAt: 2026-07-17
updatedAt: 2026-07-17
bundle: bundles/content-quality-auditor.zip
---
# Content Quality Auditor

Use this skill to assess content quality in a repeatable, evidence-led way and produce a prioritised improvement plan.

## What to audit

The skill can be used for:

- Individual documents, pages, posts, decks, scripts, or templates.
- Groups of related artefacts.
- Content libraries where consistency and reuse matter.
- Draft material before publication.

## Evidence rules

- Base the audit only on content the user provides or content available through the agent's connected sources.
- Do not infer missing facts, usage statistics, or business impact.
- If you cannot access a referenced artefact, state that limitation and assess only what is available.
- Separate observed evidence from suggested improvements.

## Default seven-dimension rubric

Score each dimension from 0 to 5.

| Score | Meaning |
|---:|---|
| 0 | Not present or unusable. |
| 1 | Present but weak, confusing, or incomplete. |
| 2 | Basic but inconsistent or hard to reuse. |
| 3 | Usable with moderate improvement needed. |
| 4 | Strong with minor refinement needed. |
| 5 | Publication-ready or operationally robust. |

Assess these dimensions:

1. **Purpose and audience clarity** - Is the content clear about who it is for and what it helps them do?
2. **Structure and navigation** - Is the content logically organised and easy to scan?
3. **Evidence and specificity** - Are claims supported by examples, data, sources, or concrete detail?
4. **Practical usefulness** - Does the content help the reader make a decision or take action?
5. **Consistency and standards alignment** - Does it follow the expected terminology, design, tone, and formatting conventions?
6. **Reusability and modularity** - Can the content be reused, adapted, or maintained without excessive rework?
7. **Completeness and next action** - Are important gaps, dependencies, risks, and follow-up actions visible?

If the user supplies a different rubric, use their rubric instead.

## Workflow

1. Identify the artefact or artefacts being audited.
2. Confirm the intended audience and purpose from the available material.
3. Apply the rubric dimension by dimension.
4. Note specific evidence for each score.
5. Identify priority fixes, separating major blockers from polish.
6. Recommend a practical sequence of improvements.
7. If auditing multiple artefacts, provide a comparative summary and prioritised backlog.

## Output format

Use this format unless the user requests another structure:

```markdown
## Audit summary

Overall assessment: [Short judgement]
Overall score: [Average]/5
Priority: [High / Medium / Low]

## Scorecard

| Dimension | Score /5 | Evidence | Recommended improvement |
|---|---:|---|---|
| Purpose and audience clarity |  |  |  |
| Structure and navigation |  |  |  |
| Evidence and specificity |  |  |  |
| Practical usefulness |  |  |  |
| Consistency and standards alignment |  |  |  |
| Reusability and modularity |  |  |  |
| Completeness and next action |  |  |  |

## Highest-value fixes

1. [Fix]
2. [Fix]
3. [Fix]

## Suggested next version

[Concise recommended direction]
```

## Multi-artefact output

For multiple artefacts, add:

```markdown
## Prioritised improvement backlog

| Priority | Artefact | Issue | Recommended action | Effort | Impact |
|---|---|---|---|---|---|
```


## References

This skill includes supporting reference material. Read the relevant reference file when the task needs additional structure, rubric detail, examples, or checklist support.

- `references/scoring-rubric.md` - use this when additional structure, examples, or checks are useful for the task.

## Quality checklist

Before responding, check:

- Scores are justified by evidence.
- Recommendations are specific and actionable.
- No inaccessible content is treated as reviewed.
- The output helps the user decide what to improve next.
