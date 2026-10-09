---
name: copilot-studio-topic-to-skill
description: >-
  Use this skill whenever the user asks to convert or migrate a Microsoft
  Copilot Studio classic topic written as AdaptiveDialog YAML into a canonical
  Agent Skill for the new Copilot Studio experience, or pastes topic YAML and
  asks for a skill. Trigger on requests such as "convert this topic to a skill",
  "turn this Copilot Studio topic into a skill", "migrate this AdaptiveDialog
  YAML", "convert my topic YAML", or "topic to skill". Do not use it to author a
  new topic from scratch, convert a skill back into a topic, or build or validate
  unrelated Agent Skills.
---

Convert a Microsoft Copilot Studio classic topic written as AdaptiveDialog YAML
into a canonical Agent Skill. Translate the classic
`OnRecognizedIntent`/`triggerQueries`/action-node pattern into a `name` and
`description` in YAML frontmatter followed by ordered activation steps,
guidelines, examples, and notes. Surface constructs without a direct Agent Skill
equivalent as `REVIEW:` items instead of silently dropping them.

## Output format

Produce one `SKILL.md` in this exact shape:

```markdown
---
name: <skill-identifier>
description: >-
  <What the skill does and when to use it. Include three to five representative
  example phrases so the orchestrator can route to it.>
---

When this skill is activated:

1. [First step or action the agent should take]
2. [Second step or action]

## Guidelines

- [Key guideline or constraint]
- [Another important consideration]

## Examples

**Example 1: [Scenario name]**

- User request: "[Example user input]"
- Expected behavior: [How the agent should respond]

## Notes

[Edge cases, data shapes, migration notices, and REVIEW: items.]
```

Apply these frontmatter rules:

- `name` is required. Use lowercase letters, numbers, and hyphens only; start
  with a lowercase letter; limit it to 64 characters; and match
  `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`.
- `description` is required. Keep it under 1,024 characters and state both what
  the skill does and when to use it. Include three to five representative
  phrases from the source topic.
- Put `name` and `description` inside the YAML frontmatter. Never emit them as
  plain `Name:` or `Description:` lines in the body.
- Omit optional frontmatter keys unless the output specifically needs them.

The Markdown after the closing frontmatter fence is the skill's instructions.

## Input handling

1. If the user pasted YAML in the message, use it directly.
2. Otherwise, look for an attached or available `.yml`, `.yaml`, or
   `.topic.mcs.yml` file. If several topic files are available, ask which one to
   convert.
3. If no topic YAML is available, ask the user to paste it or attach the file.
   Never invent topic content.
4. Confirm that the YAML describes an `AdaptiveDialog` before converting it.

## Conversion mapping

Apply every applicable row.

| Classic topic construct | Agent Skill target | Rule |
|---|---|---|
| Root `modelDescription` | `description` frontmatter | Use it as the lead sentence of the description. |
| `beginDialog.intent.triggerQueries` | `description` frontmatter and `## Examples` | Fold three to five phrases into the description and turn representative phrases into example user requests. |
| Topic display name or file name | `name` frontmatter | Convert it to a short lowercase, hyphenated identifier. |
| `Question` node with `variable`, `prompt`, and `entity` | Numbered activation step | Add one "Ask the user for..." step per question, preserving action order and using a human-friendly field name. |
| Prebuilt entity such as `PersonName`, `Email`, `PhoneNumber`, `StreetAddress`, `City`, `State`, `ZipCode`, or `String` | Step detail or guideline | Carry forward relevant type and validation requirements. |
| `ClosedListEntity` or `optionSetName` with `items` | Numbered activation step | Offer the accepted `displayName` values. |
| `ConditionGroup` and `conditions[].condition` | Conditional activation steps and guideline | Translate each branch into plain language. Keep nontrivial Power Fx in a `REVIEW:` note. |
| Tool, flow, action, or redirect call such as `InvokeFlowAction`, `InvokeConnectorAction`, or `SearchAndSummarizeContent` | Numbered activation step | Preserve the exact callable name, inputs, and output variable. Carry any `latencyMessage` into the step. |
| `Message` or `SendActivity` text without a card | Numbered activation step | Convert fixed text into a response step and dynamic content into a step that presents the referenced variable. |
| `SendActivity` containing `AdaptiveCardTemplate` | Generated-response step and review note | Preserve the underlying data and response intent that can be identified. Carry any `Action.OpenUrl` target forward as a text link. Do not claim the authored card node was migrated; add a note for human review of card behavior and presentation. |
| `SetVariable`, `Global.`/`Topic.`/`Dialog.` plumbing, loops, or `ParseValue` | `## Notes` | Add a `REVIEW:` item because there is no direct, lossless instruction mapping. |

Use human-friendly field names such as "email address" or "start date" so
auto-generated follow-up questions read naturally. Make the description
specific enough for routing; never replace the source intent with a vague phrase
such as "handles requests".

## Procedure

1. Acquire and validate the source topic YAML.
2. Parse `beginDialog`, its intent and `triggerQueries`, `modelDescription`, and
   the ordered `actions`. Recurse through
   `ConditionGroup.conditions[].actions`.
3. Create the frontmatter `name` and `description`. Derive the name from the
   topic display name or file name. Build the description from
   `modelDescription` or the intent summary plus three to five source trigger
   phrases.
4. Create the `When this skill is activated:` numbered steps in source action
   order. Convert questions, messages, conditions, and callable actions using
   the mapping table.
5. For an `AdaptiveCardTemplate`, preserve the data and response intent that can
   be carried into instructions, retain any open URL as a text link, and add a
   note that the authored card behavior and presentation require review.
6. Build `## Guidelines` from branch constraints, entity validation, and fixed
   rules found in the topic.
7. Build `## Examples` from representative source trigger phrases. Give each
   example a user request and expected behavior.
8. Build `## Notes` with data shapes, card migration notices, and `REVIEW:`
   items for every lossy construct.
9. Write the result to `output/<name>/SKILL.md`.
10. Tell the user what converted cleanly, what needs review, and whether
    anything could not be carried forward.

## Guardrails

- Match the canonical Agent Skill format exactly: `name` and `description` in
  YAML frontmatter followed by Markdown instructions.
- Convert only behavior present in the YAML. Never fabricate topic behavior.
- Preserve exact flow, connector, action, and redirect names because they are
  load-bearing.
- Never silently drop lossy constructs. Add a `REVIEW:` note for each one.
- Do not claim an authored Adaptive Card node was migrated as executable card
  behavior.
- If the YAML is malformed or is not an `AdaptiveDialog`, identify the parse or
  type problem and stop instead of guessing.
