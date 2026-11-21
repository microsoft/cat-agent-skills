# Copilot Studio Topic to Skill

Convert a Microsoft Copilot Studio classic topic written as AdaptiveDialog YAML
into a canonical Agent Skill for the new Copilot Studio experience.

The converter carries forward routing phrases, questions, conditions, messages,
and tool or flow calls. Constructs without a direct Agent Skill equivalent are
called out for human review instead of being silently discarded.

## Before you start

Have the classic topic YAML available. You can paste it into the conversation or
attach a `.yml`, `.yaml`, or `.topic.mcs.yml` file.

This skill runs in Cowork. Its output is a new `SKILL.md` file that you can
review and upload to an agent in the new Copilot Studio experience.

## How to use it

Paste or attach the topic YAML and ask:

> Convert this Copilot Studio topic to a SKILL.md.

The skill creates:

- A valid lowercase, hyphenated skill name.
- A routing-focused description seeded with representative trigger phrases.
- Ordered activation instructions derived from the topic actions.
- Guidelines, examples, and review notes for lossy or unsupported mappings.

## Good to know

- The conversion is one-way: classic topic to Agent Skill.
- Exact flow, connector, and action names are preserved.
- Nontrivial Power Fx, variable plumbing, loops, and other lossy constructs are
  flagged with `REVIEW:` notes.
- An authored Adaptive Card topic node is not treated as directly migrated. The
  converter preserves the data and response intent it can identify and adds a
  review note for the card behavior and presentation.
- Always test the generated skill in Copilot Studio before using it in
  production.

The original project and source examples are available in
[matthewmarra/studio-topic-to-skill](https://github.com/matthewmarra/studio-topic-to-skill).
