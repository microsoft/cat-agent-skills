---
name: Brand Voice Pass
description: "Rewrite drafts into a configurable house style, preserving meaning while removing generic AI phrasing."
agentDescription: "Use this skill when the user asks to rewrite, humanise, de-AI, polish, localise, or align draft text to a brand voice, house style, named audience, or writing profile."
platforms: [Cowork, Copilot Studio, Scout]
tags: [writing, content, voice, authoring, productivity]
author: Simon Owen
authorUrl: "https://github.com/SimonOwenDigital"
authorGithub: SimonOwenDigital
version: 0.1.0
createdAt: 2026-07-17
updatedAt: 2026-07-17
bundle: bundles/brand-voice-pass.zip
---
# Brand Voice Pass

Use this skill to transform draft copy into a defined brand or personal voice while preserving the user's meaning, evidence, terminology, and intent.

## Operating principles

1. **Preserve the truth.** Do not invent facts, proof points, dates, clients, figures, quotes, or outcomes.
2. **Preserve the argument.** Improve expression without changing the user's position unless they explicitly ask for a stronger or softer stance.
3. **Remove generic AI tells.** Avoid empty intensifiers, inflated claims, tidy-but-bland phrasing, excessive signposting, and repetitive short sentences.
4. **Use the requested variant of English.** Default to the user's language and regional spelling. If unspecified and the surrounding material uses UK English, use UK English.
5. **Respect the destination.** Adjust length, cadence, paragraphing, and directness for the intended channel.
6. **Keep it usable.** Return the rewritten copy first. Add notes only when useful.

## Inputs to look for

- Draft text or notes to rewrite.
- Brand or personal voice guidance.
- Audience, channel, objective, and desired length.
- Words or phrases to avoid.
- Required terminology, source facts, or claims that must remain intact.

If the user has not supplied a full voice guide, infer only light stylistic choices from the draft and clearly avoid claiming a detailed brand profile exists.

## Workflow

1. Read the full draft before editing.
2. Identify the core message, supporting evidence, and intended action.
3. Apply the voice rules without adding unsupported content.
4. Improve flow, transitions, sentence rhythm, and paragraph shape.
5. Remove generic AI phrasing and replace it with concrete, human language.
6. Check the output against the original for meaning drift.
7. Return the final copy in a copy-ready format.

## Default voice controls

Use these controls unless the user provides a different profile:

- Prefer concrete language over abstract positioning.
- Prefer lived-experience phrasing over consultancy jargon.
- Use natural paragraphing rather than long blocks or a list of fragments.
- Avoid repetitive, overly neat sentence structures.
- Avoid claims such as "game-changing", "revolutionary", "unlock", "seamless", "in today's fast-paced world", and similar filler unless they are in source text and must be retained.
- Keep the user's level of confidence: do not over-polish into corporate blandness.

## Output patterns

For a simple rewrite, output only:

```markdown
[Rewritten copy]
```

For a rewrite where useful issues were found, output:

```markdown
[Rewritten copy]

Notes:
- [Short note on any assumption, ambiguity, or retained risk.]
```


## References

This skill includes supporting reference material. Read the relevant reference file when the task needs additional structure, rubric detail, examples, or checklist support.

- `references/voice-profile-template.md` - use this when additional structure, examples, or checks are useful for the task.

## Quality checklist

Before responding, check:

- The rewritten text keeps the original meaning.
- No new evidence or claims have been invented.
- The copy sounds like a person, not a generic assistant.
- The requested language variant and channel fit are respected.
- The result is ready for the user to paste or publish.
