# Prompt Review Rubric

Use this rubric when the user asks for a prompt review, quality check, or explanation of why a prompt is brittle.

Rate each dimension as **Strong**, **Partial**, or **Missing**. Do not invent numeric precision when the evidence is qualitative.

## 1. Task clarity

**Strong**
- The requested job is explicit.
- Important terms are defined or unambiguous in context.
- The prompt does not bundle unrelated jobs that should be separate.

**Partial**
- The main job is understandable, but important decisions are implicit.
- Multiple objectives compete without priority.

**Missing**
- The model must guess what success looks like.
- The prompt mostly describes a role or topic instead of a task.

Common fixes:
- state the task as an observable outcome;
- prioritize competing objectives;
- split unrelated tasks when needed.

## 2. Input contract

**Strong**
- Required context and variables are obvious.
- Stable instructions are separated from changing data.
- Missing-input behavior is defined where it matters.

**Partial**
- Inputs exist but are hard-coded, inconsistently named, or weakly described.

**Missing**
- The prompt assumes context that is not supplied.
- Important values are buried in prose with no clear boundaries.

Common fixes:
- use explicit placeholders;
- define required vs optional inputs;
- delimit large or untrusted input blocks.

## 3. Grounding and evidence

**Strong**
- The source of truth is defined when factual accuracy depends on supplied evidence.
- The model is told what to do when evidence is insufficient.
- Citation requirements match the runtime's actual capabilities.

**Partial**
- The prompt says to be accurate but does not define what evidence controls the answer.

**Missing**
- The prompt asks the model to invent or infer unavailable facts.
- It requests citations that the runtime cannot produce reliably.

Common fixes:
- name the controlling source;
- require uncertainty rather than fabrication;
- remove impossible evidence requirements.

## 4. Constraints and guardrails

**Strong**
- Constraints are relevant, non-duplicative, and prioritized.
- Security or authorization controls are not delegated to prompt wording alone.

**Partial**
- Useful rules exist but overlap or conflict.
- Too many absolute rules make edge cases brittle.

**Missing**
- Critical task boundaries are undefined.
- Prompt text is being used as the only enforcement for a deterministic or security-critical requirement.

Common fixes:
- consolidate duplicate rules;
- move deterministic enforcement to architecture;
- define only the boundaries that change behavior.

## 5. Output contract

**Strong**
- Required content and shape are observable.
- Machine-readable structure is used only when needed.
- Flexible tasks use success criteria rather than exact wording.

**Partial**
- The output is broadly described but important fields, ordering, or limits are unclear.

**Missing**
- “Give me a good answer” is effectively the only output requirement.
- A downstream system needs structure the prompt never defines.

Common fixes:
- define sections/fields/labels;
- set meaningful length or detail limits;
- specify allowed values for classifications.

## 6. Failure behavior

**Strong**
- Missing, ambiguous, contradictory, or unsupported input has deliberate behavior.
- The prompt distinguishes “cannot determine” from a normal answer.

**Partial**
- Some failure cases are covered but likely edge cases still force guessing.

**Missing**
- The model is implicitly rewarded for producing an answer even without enough information.

Common fixes:
- define clarification vs refusal vs uncertainty behavior;
- tell the model what evidence is required to proceed.

## 7. Examples

**Strong**
- Examples clarify real ambiguity or edge cases.
- They are diverse and consistent with the written rules.

**Partial**
- Examples are helpful but redundant, overly long, or biased toward one pattern.

**Missing**
- Examples are absent where classification boundaries are hard to infer, or examples contradict the rules.

Common fixes:
- add the smallest number of examples that cover different boundaries;
- remove decorative examples that add tokens but no information.

## 8. Testability and maintainability

**Strong**
- Success can be tested with a small set of cases.
- Variables and rules are easy to update without rewriting the whole prompt.
- Known failure modes have regression tests.

**Partial**
- The prompt works but has no explicit regression cases or change discipline.

**Missing**
- Small edits are likely to break unrelated behavior.
- There is no practical way to distinguish a better prompt from a merely different one.

Common fixes:
- create prompt-level smoke tests;
- add a concise change note;
- keep stable logic separate from changing inputs.

## Anti-patterns worth calling out

- “You are the world's best…” with no task-relevant effect.
- Repeating the same rule in multiple sections.
- Long lists of prohibitions without positive desired behavior.
- Asking for hidden chain-of-thought.
- Treating prompts as access controls.
- Hard-coding values that change every run.
- Requiring exact prose for inherently flexible generative tasks.
- Adding a JSON schema when a person is the only consumer.
- Adding examples that all demonstrate the same happy path.
- Fixing a missing tool/data source by adding increasingly forceful instructions.

## Review output

Use a compact format:

```markdown
## Prompt review

Overall: [Ready / Minor revision / Significant revision / Architecture issue first]

| Dimension | Rating | What matters |
| --- | --- | --- |
| Task clarity | Strong | ... |
| Input contract | Partial | ... |

### Highest-value changes
1. ...
2. ...

### Revised prompt
[Only when the user asked for a rewrite or revision]

### Regression tests
[Only the tests that protect the changes]
```
