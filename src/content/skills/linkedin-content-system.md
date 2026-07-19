---
name: LinkedIn Content System
description: "Create evidence-led LinkedIn posts, promos, newsletter intros, and long-form copy from supplied facts or drafts."
agentDescription: "Use this skill when the user asks to create LinkedIn posts, promotional posts, thought-leadership posts, newsletter introductions, article intros, or long-form LinkedIn content from source notes, facts, or drafts."
platforms: [Cowork, Copilot Studio, Scout]
tags: [linkedin, social-media, writing, marketing, content]
author: Simon Owen
authorUrl: "https://github.com/SimonOwenDigital"
authorGithub: SimonOwenDigital
version: 0.1.0
createdAt: 2026-07-17
updatedAt: 2026-07-17
bundle: bundles/linkedin-content-system.zip
---
# LinkedIn Content System

Use this skill to create credible LinkedIn content from supplied facts, notes, drafts, articles, or source material.

## Core rules

1. **No invented evidence.** Do not invent metrics, client names, event details, quotes, claims, or results.
2. **No fake authority.** Do not imply the author has done, seen, led, or researched something unless supplied evidence supports it.
3. **Keep the voice human.** Avoid generic inspirational language, over-polished corporate phrasing, and forced hooks.
4. **Fit the format.** Match the output to the requested LinkedIn surface: short post, promotional post, event post, newsletter intro, article intro, carousel copy, or long-form article.
5. **Avoid unnecessary links or citations in the post body unless the user asks for them.** Keep LinkedIn copy clean and paste-ready.

## Inputs to look for

- Source article, draft, notes, or bullet points.
- Audience and desired action.
- Author voice guidance.
- Desired length.
- Specific announcement, event, launch, model, or point of view.
- Whether links, hashtags, mentions, or calls to action should be included.

## Workflow

1. Read the supplied source material.
2. Extract the central point, proof points, and intended reader response.
3. Choose the appropriate LinkedIn format.
4. Draft in a natural style with clear paragraphs.
5. Keep the post grounded in supplied content.
6. Provide variants if requested.

## Output formats

### Short post

```markdown
[Post copy]
```

### Promo post

```markdown
[Post copy]

[Optional CTA]
```

### Newsletter or article intro

```markdown
# [Title]

[Intro copy]
```

### Multi-variant output

```markdown
## Recommended version

[Post]

## Alternative angle

[Post]

## Shorter version

[Post]
```

## Style guidance

- Prefer concrete observations over broad claims.
- Use short paragraphs but avoid a stack of one-line fragments unless the user requests that style.
- Avoid manipulative hooks such as "Stop doing X" unless it genuinely fits the user's tone.
- Make the first line specific enough to be worth reading.
- End with a useful reflection, question, or action rather than a generic CTA.


## References

This skill includes supporting reference material. Read the relevant reference file when the task needs additional structure, rubric detail, examples, or checklist support.

- `references/linkedin-format-guide.md` - use this when additional structure, examples, or checks are useful for the task.

## Quality checklist

Before responding, check:

- The content is grounded in supplied facts.
- It reads like a credible human post.
- It fits the requested LinkedIn surface.
- It avoids unnecessary links, references, and invented proof.
- The user can paste it directly into LinkedIn.
