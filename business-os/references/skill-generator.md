# Skill Generator (Capability Compiler)

Load this when the user asks to turn a process into a Skill ("build a Skill for supplier onboarding", "package this as a reusable Skill"), or when work you've just done, or seen repeated, looks like a genuinely strong reusable capability.

This works in two modes:

- **Explicit creation** - the user directly asks for a Skill.
- **Opportunity detection** - after repeated or mature work, you notice a pattern worth proposing as a Skill. Propose it; do not create or deploy it without the user's go-ahead.

## Step 1: assess the candidate

Before building anything, work through `assets/templates/skill-candidate-assessment.md`, covering:

- **Repeatability** - will this happen again?
- **Value** - would reuse save meaningful time, improve quality, reduce risk, or improve consistency?
- **Stability** - is the process well enough understood to write down reliably?
- **Generalisability** - does it work beyond this one instance?
- **Input clarity** - can the required inputs be named?
- **Output clarity** - can the expected output be named?
- **Governance** - does it need approvals, restricted data handling, or expert judgement?
- **Tool dependencies** - what actions or integrations does it need? Don't assume they exist.
- **Knowledge dependencies** - what organisational knowledge does it need (Company DNA, a policy document)?
- **Verification** - can success be checked?
- **Risk of automation** - could getting it wrong autonomously cause real harm?

Classify the result as one of: **strong candidate**, **possible candidate**, **better as a playbook or template** (skip Skill generation, produce that instead), or **not suitable yet** (say why, and what would need to change).

Do not treat one successful example as proof of a strong candidate; look for repetition and stability.

## Step 2: build the Skill, if it's a strong or possible candidate

Follow this pipeline, mirroring the same design standard this Skill itself follows: one coherent job, a clear trigger, proportionate instructions, and progressive disclosure into references/assets/templates/scripts.

1. **Define the capability** - name, purpose, intended users, trigger conditions, explicit non-triggers, desired outcome, scope, exclusions.
2. **Define inputs** - required and optional.
3. **Define outputs** - the expected deliverable(s).
4. **Model the workflow** - reasoning stages, steps, decision points, exceptions, approvals, escalation.
5. **Identify resources** - what actually needs a reference file, a template, an example, or a script, versus what fits in the main instructions.
6. **Define tool contracts** - what tools or actions might be needed, what each is for, what permissions they'd need, and what happens if they're unavailable. Never assume a tool exists.
7. **Define safety and governance** - prohibited autonomous actions, approval gates, sensitive data handling, evidence requirements, escalation conditions.
8. **Define verification** - how the Skill will know whether it succeeded.
9. **Build the package** - `SKILL.md` with frontmatter (name, description covering trigger language), plus `references/`, `assets/templates/`, and `scripts/` only where genuinely needed.
10. **Write representative tests** - normal case, ambiguous case, missing information, conflicting information, an edge case, a high-risk case, a case where a needed tool is unavailable, and a case clearly outside scope.
11. **Review** - trigger quality, instruction clarity, whether progressive disclosure is actually used, hallucination risk, unsafe autonomy, and overall package validity. Use the same checklist as this Skill's own build (`references/test-scenarios.md` shows the pattern).
12. **Version it** - include a short changelog note for future updates.

Use `assets/templates/skill-specification.md` to capture steps 1 to 8 before writing the files.

## Quality bar for any generated Skill

- One coherent job, not a bundle of unrelated tasks.
- A trigger description specific enough to avoid firing on unrelated requests, but not so narrow it misses the obvious phrasing people will actually use.
- Explicit scope and non-goals.
- Instructions that are operational, not aspirational ("check X, then do Y", not "consider best practice").
- Progressive disclosure: the main file stays short; detail lives in references, templates, and scripts.
- Evidence and tool-honesty rules carried through from this Skill's own approach.
- Clear verification criteria and failure behaviour.
- No duplicated instructions between the main file and its resources.

## Improving an existing Skill

If evidence shows a generated (or any) Skill is failing repeatedly, being corrected by users, missing an exception, or has an outdated process, produce a **Skill Improvement Proposal** using `assets/templates/skill-improvement-proposal.md`, covering: observed issue, evidence, likely cause, proposed change, affected files, risks, tests required, and expected improvement. Do not silently rewrite a governed capability; propose the change.

## What this Skill cannot do on its own

It cannot autonomously deploy, publish, or overwrite a live Skill inside Copilot Studio, crawl an organisation's full document estate, or persist memory between sessions unless the host environment actually provides that. It can produce a complete, ready-to-import package and a clear proposal; a person or the platform's own import process takes it from there.
