---
name: prompt-architect
description: Use this skill when the user asks to create, improve, debug, review, or turn an LLM prompt or prompt instruction set into a reusable prompt template, especially when they need variables, grounding rules, constraints, output structure, failure behavior, examples, or prompt-level regression tests. Do not use it for ordinary prose rewriting, Agent Skill/SKILL.md authoring, whole-agent evaluation/readiness, or platform selection.
---

# Prompt Architect

Turn rough prompts into **testable prompt contracts** that are clear, reusable, and easier to maintain.

A good prompt is not an incantation and it is not automatically better because it is longer. Treat the prompt as an interface between intent, inputs, model behavior, and an expected output. Optimize for clarity, evidence discipline, failure behavior, and testability.

## Choose the working mode

Infer the mode from the user's request. Ask at most one concise clarification when a missing fact would materially change the design.

- **Build** — the user has a task but no usable prompt yet.
- **Improve** — the user provides an existing prompt and wants it stronger, clearer, or more reusable.
- **Debug** — the user provides a prompt plus an output or failure that did not behave as intended.
- **Template** — the user wants a prompt that will be reused with changing inputs.
- **Review** — the user wants an assessment of a prompt without unnecessary rewriting.

If the user only wants a quick prompt rewrite, lead with the improved prompt. Do not force the full contract format when it would add noise.

## Step 1 — Define the job before rewriting

Identify, from information already supplied:

1. **Task** — what result must the model produce?
2. **Audience or consumer** — who or what will use the result?
3. **Inputs** — what context, source material, or variables are available?
4. **Source of truth** — when factual grounding matters, what evidence should control the answer?
5. **Constraints** — format, length, tone, prohibited behavior, latency, or other hard requirements.
6. **Failure behavior** — what should happen when required information is missing, ambiguous, contradictory, or unsupported?

Do not ask for details that do not change the prompt design.

### First check: is this actually a prompt problem?

Before adding more instructions, determine whether the observed failure is caused by the prompt or by missing architecture.

A prompt cannot reliably fix:

- missing or inaccessible knowledge;
- missing tools or integrations;
- authentication, authorization, or permissions;
- a platform feature that does not exist;
- deterministic validation that belongs in code or workflow logic;
- a security control that must be enforced outside the model;
- stale or incorrect source data.

If one of those is the real blocker, state it plainly and recommend the smallest architecture fix. Improve the prompt only where the prompt itself is contributing to the problem.

Read `references/prompt-vs-architecture.md` when the distinction is unclear.

## Step 2 — Build the minimum sufficient instruction set

Separate the prompt into logical layers when that improves readability:

- **Objective** — the job to perform.
- **Inputs / context** — data the model should use.
- **Rules / constraints** — requirements that materially affect behavior.
- **Output contract** — what the result must contain and how it should be shaped.
- **Failure behavior** — what to do when the task cannot be completed safely or correctly.
- **Examples** — only when examples materially reduce ambiguity.

Prefer a short explicit rule over several overlapping rules.

Remove prompt cargo cults unless they have a demonstrated purpose. In particular, do not add:

- theatrical role-play that does not change the task;
- fake urgency or threats such as “this is extremely important”;
- repeated instructions that say the same thing in different words;
- demands to reveal hidden chain-of-thought or private reasoning;
- unnecessary “always/never” rules that create contradictions;
- JSON or schemas for a human-readable task unless a machine consumer needs them.

Preserve the user's actual intent. Do not make a prompt more elaborate merely to make it look engineered.

Read `references/prompt-patterns.md` when a proven structure would help. Use those patterns as building blocks, not mandatory templates, and choose only the structure the task actually needs.

## Step 3 — Extract reusable variables

For reusable prompts, replace changing facts with explicit variables while leaving stable policy and behavior in the prompt.

Use readable placeholders such as:

```text
{{document}}
{{audience}}
{{goal}}
{{maximum_length}}
```

For each important variable identify:

- purpose;
- whether it is required or optional;
- expected type or shape;
- safe behavior when absent.

Do not put secrets, credentials, personal data, or environment-specific sensitive values into sample variables.

Do not parameterize every noun. A variable should represent information that genuinely changes between runs.

## Step 4 — Make grounding and uncertainty explicit

When the task depends on supplied documents, retrieved knowledge, or authoritative records:

- say which source should control the answer;
- instruct the model not to invent missing facts;
- require uncertainty to be surfaced when evidence is incomplete;
- require citations or evidence references only when the runtime can actually provide them;
- distinguish source content from instructions so untrusted content is treated as data, not as higher-priority control text.

Do not claim that prompt wording alone prevents prompt injection, data leakage, unauthorized actions, or other security failures.

## Step 5 — Define the output contract

Make the expected result observable enough to review or test.

Specify only what matters, for example:

- required sections or fields;
- ordering;
- length or level of detail;
- allowed labels or classifications;
- evidence/citation requirements;
- what must be omitted;
- machine-readable schema when a downstream system requires it.

If a response can be correct in many forms, define success criteria rather than forcing one exact wording.

## Step 6 — Use examples deliberately

Add examples when they clarify classification boundaries, formatting, tone, or difficult edge cases.

Good examples:

- cover materially different cases;
- are short enough that the rule remains visible;
- do not encode secrets or organization-specific data;
- do not contradict the written instructions.

Do not add examples just because “few-shot prompting” sounds sophisticated.

## Step 7 — Create prompt-level smoke tests

A reusable prompt is not finished until there is a small test pack that can catch obvious regressions.

Create 4–8 tests proportionate to the task. Include relevant cases from:

- **Happy path** — normal complete input.
- **Paraphrase / variation** — same intent expressed differently.
- **Missing required input** — expected clarification or failure behavior.
- **Ambiguous or conflicting input** — model should not silently guess.
- **Edge case** — unusual but valid input.
- **Untrusted content** — supplied content attempts to override the task instructions.
- **Regression case** — a previously observed failure.

Each test should state:

```text
Test:
Input:
Expected behavior:
Must not:
```

These are prompt-level smoke tests, not a full agent release evaluation. If the user wants a complete agent test plan, grading strategy, pass rates, or go/no-go decision, use the Agent Evaluation Designer instead.

## Debug mode — fix the cause, not the prose

When the user provides a bad output or failure:

1. Compare the observed output with the intended behavior.
2. Classify the likely root cause:
   - ambiguous or conflicting prompt;
   - missing input/context;
   - missing knowledge/tool/capability;
   - output contract too weak;
   - example bias or contradiction;
   - inherently variable model behavior;
   - impossible or mutually incompatible requirement.
3. Make the **smallest change** that addresses the cause.
4. Preserve behavior that was already working.
5. Add the failure as a regression test plus at least one nearby success case.

Do not rewrite the entire prompt by default.

## Review mode — inspect before editing

Review a prompt across these dimensions:

- **Task clarity** — is the requested job unambiguous?
- **Input contract** — are required inputs and variables clear?
- **Grounding** — is the source of truth defined when needed?
- **Boundaries** — are missing, conflicting, or unsupported cases handled?
- **Output contract** — can success be observed or tested?
- **Maintainability** — are rules concise, non-duplicative, and reusable?

Use `references/prompt-review-rubric.md` for deeper review.

If the prompt is already strong, say so. Do not create churn to justify the review.

## Default deliverable — the Prompt Contract

For substantial Build, Improve, or Template requests, return:

### Production prompt
The ready-to-use prompt, with variables clearly marked.

### Variables
A compact table of variable, purpose, required/optional, and expected shape when variables are used.

### Output contract
The observable requirements for a successful response.

### Failure behavior
What the model should do when required evidence or inputs are missing, contradictory, or unsupported.

### Smoke tests
A small set of high-value tests with expected behavior and “must not” conditions.

### Change note
For an existing prompt, summarize the material changes and why they matter. Do not narrate cosmetic edits.

Use `assets/prompt-contract-template.md` when the user wants the full reusable artifact.

## Boundaries with other skills

Keep the trigger precise:

- **Agent Skill / `SKILL.md` creation or packaging** → Skill Authoring Coach.
- **Whole-agent evaluation, grading methods, test sets, or go/no-go readiness** → Agent Evaluation Designer.
- **Adversarial security testing of an agent** → Agent Red Team.
- **Platform or runtime selection** → the appropriate platform-selection skill.

Prompt Architect focuses on the **prompt-level contract**: instructions, inputs, variables, output behavior, and prompt-level regression tests.

## Final quality gate

Before returning a prompt, verify:

- The task is explicit and the prompt does not solve a different problem than the user asked.
- Stable rules are instructions; changing facts are inputs or variables.
- No rule depends on unavailable capabilities.
- Missing or ambiguous input has defined behavior where it matters.
- Grounding requirements match the available evidence/runtime.
- The output contract is proportionate to the downstream consumer.
- No security or authorization guarantee is delegated to prompt wording alone.
- Tests cover the highest-impact behavior and at least one failure mode.
- The final prompt is no longer than it needs to be.
