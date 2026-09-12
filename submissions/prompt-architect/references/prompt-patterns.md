# Prompt Patterns

Use these patterns as building blocks, not rigid templates. Pick only the structure the task needs.

## Pattern 1 — Grounded transformation

Use for summarization, rewriting, extraction, or analysis of supplied material.

```text
Objective
Transform the supplied {{source}} into {{desired_output}} for {{audience}}.

Source of truth
Use only the supplied source for factual claims. If the source does not support a requested fact, say that it is not supported by the provided material.

Requirements
- Preserve the source meaning.
- Include {{required_points}}.
- Follow {{tone_or_style}} when provided.
- Stay within {{length_limit}} when provided.

Output
Return {{output_structure}}.

Source
<source>
{{source}}
</source>
```

Useful when the main risk is invented content or loss of meaning.

## Pattern 2 — Evidence-backed recommendation

Use when the model must recommend an option based on supplied criteria or evidence.

```text
Objective
Recommend the best option for {{decision}} using the supplied evidence and criteria.

Decision criteria
{{criteria}}

Evidence
{{evidence}}

Rules
- Tie each material conclusion to the supplied evidence.
- Separate observed facts from assumptions.
- If evidence is insufficient to distinguish options, say what is missing rather than forcing a recommendation.

Output
1. Recommendation
2. Why
3. Trade-offs
4. Assumptions / missing evidence
5. Next action
```

Do not use this pattern to make a security, legal, medical, or other consequential determination beyond the available evidence and appropriate review process.

## Pattern 3 — Classification with explicit boundaries

Use when inputs must map to a small set of labels.

```text
Task
Classify {{input}} into exactly one of these labels:
{{labels}}

Decision rules
{{decision_rules}}

Ambiguity behavior
If two labels are equally supported or required evidence is missing, return {{ambiguous_label_or_behavior}} and explain the missing discriminator in one sentence.

Output
Label: <allowed label>
Reason: <one concise evidence-based reason>
```

Add examples only for boundaries that are genuinely hard to infer.

## Pattern 4 — Structured extraction

Use when a downstream system needs predictable fields.

```text
Task
Extract the requested fields from {{source}}.

Fields
{{field_definitions}}

Rules
- Do not infer a value that is absent unless a field explicitly allows inference.
- Use null for missing values unless another missing-value convention is specified.
- Preserve IDs, dates, numbers, and names exactly where accuracy matters.

Output schema
{{schema}}

Source
{{source}}
```

Use deterministic schema validation downstream when malformed output would cause operational harm.

## Pattern 5 — Guided drafting

Use for emails, summaries, briefs, messages, or documents where tone and audience matter.

```text
Write {{artifact_type}} for {{audience}}.

Goal
{{goal}}

Facts to preserve
{{facts}}

Tone
{{tone}}

Constraints
{{constraints}}

Do not add facts, promises, dates, commitments, or conclusions that are not supported by the supplied information.
```

Avoid over-specifying voice unless the user actually needs a particular style.

## Pattern 6 — Tool/action preparation

Use when the model prepares parameters or a recommendation for an external action.

```text
Task
Prepare the information required to {{action}}.

Required inputs
{{required_inputs}}

Rules
- Validate that required inputs are present.
- If a required value is missing or ambiguous, ask for it instead of guessing.
- Summarize the proposed action before execution when confirmation is required.

Output
{{action_parameters_or_preview}}
```

The prompt can prepare or explain an action. Authorization, confirmation gates, limits, and side-effect controls should be enforced by the tool/workflow where required.

## Pattern 7 — Compare versions without losing intent

Use when improving an existing prompt.

```text
Original prompt
{{original_prompt}}

Observed issue or improvement goal
{{goal_or_failure}}

Revise the prompt with the smallest material changes needed to address the goal.
Preserve working behavior and the original task intent.

Return:
1. Revised prompt
2. Material changes
3. Regression tests protecting the changed behavior
```

This pattern helps prevent “optimization” from becoming an accidental redesign.
