---
name: POV Line Generator
description: "Generate sharp, specific point-of-view lines for posts, slides, talks, campaigns, or positioning work."
agentDescription: "Use this skill when the user asks for a point of view, punchy line, positioning sentence, provocative statement, headline angle, opinion line, or concise strategic stance."
platforms: [Cowork, Copilot Studio, Scout]
tags: [writing, positioning, marketing, content, social-media]
author: Simon Owen
authorUrl: "https://github.com/SimonOwenDigital"
authorGithub: SimonOwenDigital
version: 0.1.0
createdAt: 2026-07-17
updatedAt: 2026-07-17
bundle: bundles/pov-line-generator.zip
---
# POV Line Generator

Use this skill to generate concise, distinctive point-of-view lines that help a user frame an argument, post, slide, campaign, or talk.

## What makes a good POV line

A strong POV line should:

- Take a clear stance.
- Be specific enough to be meaningful.
- Avoid generic trend commentary.
- Create useful tension without becoming clickbait.
- Be easy to reuse as a post opener, slide headline, talk premise, campaign angle, or executive summary line.

## Inputs to look for

- Topic or theme.
- Audience.
- Desired stance or tension.
- Channel: LinkedIn, slide, keynote, blog, proposal, campaign, workshop.
- Tone: practical, provocative, premium, accessible, technical, executive, conversational.
- Words to include or avoid.

## Workflow

1. Identify the underlying argument, not just the topic.
2. Look for a tension: common belief vs better belief, adoption vs transformation, activity vs value, tooling vs operating model, speed vs control, scale vs quality.
3. Generate one recommended line first.
4. Provide alternatives grouped by style.
5. Keep each line concise and useful.
6. Do not invent evidence or claims.

## Output format

```markdown
## Recommended POV line

[One strong line]

## Alternatives

### More direct
- [Line]
- [Line]

### More provocative
- [Line]
- [Line]

### More executive
- [Line]
- [Line]

## Why the recommended line works

[One short explanation]
```


## References

This skill includes supporting reference material. Read the relevant reference file when the task needs additional structure, rubric detail, examples, or checklist support.

- `references/pov-patterns.md` - use this when additional structure, examples, or checks are useful for the task.

## Quality checklist

Before responding, check:

- The line has a clear point of view.
- It is not interchangeable with any other topic.
- It avoids empty hype.
- It can plausibly open a post, slide, talk, or section.
- The alternatives are meaningfully different, not minor rewrites.
