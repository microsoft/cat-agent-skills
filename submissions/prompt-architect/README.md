# Prompt Architect

Most prompt helpers stop at “here is a better version.” Prompt Architect goes one step further: it turns a rough prompt into a **testable prompt contract**.

The result is not just nicer prose. It defines what the prompt is supposed to do, which inputs can change, what evidence controls the answer, what the output must look like, how missing information should be handled, and how to catch regressions when the prompt changes.

## What it does

Give Prompt Architect a rough task, an existing prompt, or a prompt that produced a bad result. It can:

- build or rewrite the production prompt;
- extract reusable variables instead of leaving hard-coded values buried in prose;
- define the output contract and missing-input behavior;
- identify when the real problem is missing knowledge, tooling, permissions, or workflow logic rather than prompting;
- remove duplicated rules, cargo-cult role-play, and unnecessary prompt ceremony;
- create a compact smoke-test pack covering happy paths and failure modes;
- debug a bad output with the smallest prompt change instead of rewriting everything;
- produce a change note that explains what behavior changed and what was intentionally preserved.

## The idea in one example

A rough prompt:

> Review this request and tell me if it is ready.

A normal prompt rewriter might make that sentence longer.

Prompt Architect first asks what “ready” means and what evidence is available. A reusable result can become:

```text
Objective
Assess {{request}} against {{readiness_criteria}}.

Source of truth
Use only the supplied request and criteria. Do not invent missing evidence.

Rules
- Separate observed facts from assumptions.
- If a required criterion cannot be evaluated, mark it Not enough evidence.
- Do not treat missing evidence as a pass.

Output
Decision: Ready | Ready with gaps | Not ready | Not enough evidence
Evidence:
- <criterion>: <observed support>
Gaps:
- <missing or failed requirement>
Next action:
- <single concrete next step>
```

Then it also produces prompt-level tests such as:

- complete request that meets every criterion;
- request missing required evidence;
- conflicting evidence;
- content that tries to override the assessment instructions;
- regression case for a previously observed failure.

That is the core difference: **the prompt becomes something you can maintain and test, not just something that sounds polished.**

## Four useful modes

**Build** — turn a task into a prompt.

**Improve** — strengthen an existing prompt without changing its intent.

**Debug** — use an actual bad output to find the smallest prompt fix and add a regression test.

**Template** — convert a one-off prompt into a reusable prompt with explicit variables and failure behavior.

There is also a **Review** mode when you want a quality assessment without automatically rewriting the prompt.

## It knows when prompting is the wrong fix

One of the most useful behaviors is knowing when to stop prompt engineering.

If the real issue is a missing data source, inaccessible knowledge, absent tool, authorization problem, deterministic validation rule, or security control, Prompt Architect calls that out instead of adding increasingly forceful prose to the prompt.

For example, “Never send an email without approval” can improve the model's conversational behavior, but a consequential send action should still have a workflow or tool-level confirmation gate. Prompt wording is not an authorization control.

## What you get

For substantial prompt work, the skill returns a reusable **Prompt Contract** containing:

1. Production prompt
2. Variables
3. Output contract
4. Failure behavior
5. Prompt-level smoke tests
6. Change note
7. Architecture dependencies the prompt cannot enforce itself

The included template makes that artifact consistent without forcing every quick prompt edit into a heavyweight process.

## Boundaries

Prompt Architect is deliberately narrow so it composes cleanly with other skills:

- Creating or packaging `SKILL.md` / Agent Skills belongs to **Skill Authoring Coach**.
- Full agent test planning, grading methods, pass rates, and go/no-go decisions belong to **Agent Evaluation Designer**.
- Adversarial agent security testing belongs to **Agent Red Team**.

Prompt Architect owns the layer in between: **the prompt itself as a reusable, testable contract.**

## Example requests

- “Make this prompt reusable. The customer name and report date change every time.”
- “This prompt sometimes invents facts. Fix it without making it huge.”
- “Review this prompt and tell me what is actually wrong with it.”
- “The prompt worked until I added this rule. Help me debug the regression.”
- “Turn this one-off prompt into a template with variables and tests.”
- “Before you rewrite this, tell me whether the problem is actually the prompt or the architecture.”
