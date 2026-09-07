# Skill Design Checklist

Use this checklist when reviewing or creating an Agent Skill.

## Trigger

- Does the description clearly say when to use the skill?
- Does it include the user's likely task language?
- Is it specific enough to avoid accidental invocation?

## Scope

- Does the skill do one coherent job?
- Are unrelated workflows split into separate skills?
- Are organisation-specific assumptions removed or parameterised?

## Instructions

- Are the steps operational rather than aspirational?
- Are edge cases and guardrails included?
- Is the output format clear?
- Is the skill concise enough to load efficiently?

## Resources

- Are long rubrics, examples and reference material moved into `references/`?
- Are static templates placed in `assets/`?
- Are deterministic operations handled by `scripts/` where appropriate?

## Safety and portability

- Does the skill avoid leaking private paths, names or client details?
- Does it avoid unsupported claims?
- Can someone outside the original organisation use it?

## Packaging

- Folder name is lowercase and hyphenated.
- `SKILL.md` frontmatter name matches the folder name.
- `metadata.json` has name, description, platforms and tags.
- Any bundled resources are necessary and reusable.
