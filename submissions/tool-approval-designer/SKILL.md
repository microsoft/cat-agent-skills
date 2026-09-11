---
name: tool-approval-designer
description: >-
  Use this skill whenever a user asks which agent tools should require human
  approval, how to gate, confirm, or add human-in-the-loop to tool calls, how to
  set approval_mode, how to word an approval prompt, whether approve-for-session
  is safe, or how to stop approval fatigue. It applies the irreversibility test:
  a tool whose effect cannot be undone and is visible outside the organisation
  must always gate, and a badly designed gate is worse than none because it
  manufactures accountability, recording that a named employee approved
  something they never read. It produces artifacts: a gating matrix, per-tool
  approval wording generated from the real call arguments, approval_mode diffs,
  an approval renderer and loop, and a committed decision record. It does not
  deploy, does not touch a Copilot Studio environment, and does not decide the
  customer's risk appetite. It is not a security review and not a red team.
---

# Tool Approval Designer

Decide which tools stop for a human, write what the human reads, and emit the code.

## Produce, do not review

Every run ends in artifacts a maker can paste and commit. A run that ends in
advice has failed.

Never deliver a document whose recommendations read like "consider gating your
payment tool", "review whether approval is appropriate", or "evaluate the risk of
this action". Deliver the verdict, the wording, the diff, and the decision record.
If a judgement genuinely belongs to the customer, say which judgement, why only
they can make it, and put it in the open judgements table with a proposed answer
already written.

**Approval is not authorization.** A gate records that a human clicked. It does
not grant permission, and it does not stop a compromised or mistaken caller who
is answering the prompts. Microsoft states this directly for GitHub Copilot agent
mode: "Copilot's approval system isn't a security boundary. Apply the principle of
least-privilege." Design gates on top of a permission model, never instead of one.

**A gate that is not read is a liability.** Approval logs are evidence. A design
that fires so often that people click through it converts an unread click into a
named human's recorded consent. That is the failure this skill exists to prevent,
and it is why step 5 is not optional.

## Surface boundary

State the surface before designing. What runs where is not interchangeable.

| Surface | What this skill does |
|---|---|
| Agent Framework **Python** | Full support. Parses tools, emits `approval_mode` diffs, renderer, and loop. |
| Agent Framework **Go** | Documented contract, best-effort detection only. No packaged harness. |
| Agent Framework **.NET / C#** | Documented contract. Not parsed. Inventory is supplied, not read. |
| **Harness Agent** | Documented middleware behaviour, including auto-approval rules. |
| **Copilot Studio** | Design guidance only. See the warning below. |
| **GitHub Copilot agent mode** | Cited as prior art for session unlock. Not configured here. |

**Copilot Studio per-tool approval is roadmap-announced, not documented.** The
source is Microsoft 365 roadmap item **570434**, GA target **September 2026**,
status **"In development"**. No Microsoft Learn documentation page for it was
found. Never give configuration steps for it, never describe its UI as if it
exists today, and never let a user believe the design can be switched on in a
Copilot Studio environment right now. Say plainly that this part of the design is
roadmap-sourced and will need re-checking against documentation when it ships.

This skill may be invoked from a harness that cannot run the generated code. If
Python execution is unavailable, say so, skip the parse, and run step 2 as a
guided inventory instead. Never present a supplied inventory as a parsed one.

## Adjacent skills in this gallery

Three neighbours exist and all three are reviewers. This one is the producer.

**`agent-red-team`** is the closest and the relationship is real. Its attack
surface mapping already asks, per tool, whether a human confirms before execution.
It is the right skill for finding a missing gate. This skill is what to run next:
red team establishes *that* a gate is missing, this one decides *what the gate
should be* and builds it. If the user arrives holding red team findings, take them
as the inventory input to step 2 rather than re-deriving them, and say so in the
decision record.

**`enterprise-agent-design-authority`** works at architecture altitude across
pillars. Approval design is one concern inside one pillar. Defer to it for the
overall architecture; own the gate.

**`agent-evaluation-designer`** measures answer quality. It does not decide what
must stop for a human. No overlap.

## Load supporting material only when needed

Read [references/surfaces-and-contracts.md](references/surfaces-and-contracts.md)
for the verified API contracts, the approval modes, the roadmap-sourced Copilot
Studio detail, the fatigue thresholds, and the output contracts. Every product
claim in this skill traces to that file. Do not add product claims that are not in
it without verifying them first.

Read [references/evals.md](references/evals.md) when checking this skill's own
behaviour or an edge case.

Adapt the files under `assets/templates/`. They are the deliverables, not
examples: `decision-record.md`, `approval_renderer.py`, `approval_loop.py`.

`assets/samples/sample_tools.py` is a small corpus for demonstrating step 2 when
the user has no code to hand.

## The four questions

Answer these for every tool. They are the whole decision procedure.

1. **Does it write, or only read?**
2. **Is the write reversible, and by whom?** Anyone, admin or IT only, or nobody.
3. **Is the result visible outside the organisation?**
4. **What is the blast radius?** One record or many.

**The rule.**

* Irreversible **and** externally visible: **always gate**. Not negotiable.
* Reversible by anyone **and** internal only: **do not gate**. A gate here is
  pure fatigue and buys nothing.
* Everything else: a judgement. State the reason in one sentence, in the matrix,
  every time. A verdict without a reason is not a verdict.

Questions 2 and 3 carry the rule. Question 1 filters, question 4 sizes the damage
and drives step 5.

## Workflow

### 1. Scope the surface and the runtime

Establish the codebase, the runtime, the agent, and where approvals will actually
be rendered and answered. Record what is out of scope. If the surface is Copilot
Studio, apply the roadmap warning above before going further.

### 2. Inventory from code, not interview

Run the parser from the skill root:

```bash
python scripts/inventory_tools.py path/to/agent
python scripts/inventory_tools.py path/to/agent --format json
python scripts/inventory_tools.py path/to/agent --fail-on ungated-write-external
```

Report the counts: tools found, already gated, ungated, ungated with a write
signal, ungated with a write signal that is externally visible. That last number
is the headline.

The script emits **signals, not verdicts**. It cannot see whether an effect is
truly irreversible, and it cannot read `conditional` logic. Treat its output as
the first column of the matrix, never as the matrix.

It also only claims tools it can attribute. A `@tool` traced to an
`agent_framework` import is reported as `parsed`. A `@tool` that came from
another library, or that is defined in the file itself, is **skipped with a
note**, because its `approval_mode` column would be fiction. A bare `@tool` with
no traceable import is kept but marked `best-effort`. Read the notes: a skipped
file is not the same as a file with no tools in it.

Then ask the user **only what cannot be inferred**. Two or three questions total.
Good questions look like: which of these writes reach a customer or a third party,
which can a normal user undo without IT, and what is the risk appetite for the
one or two borderline cases. Bad questions walk tool by tool. Interrogating a
maker about twenty tools will make them abandon the run, and an abandoned run
produces no gates at all.

If no execution surface is available, or the runtime is .NET or Go, ask for the
tool list and build the inventory by hand. Label it as supplied.

### 3. Build the gating matrix

One row per tool, all four answers, the verdict, and the reason.

| Tool | Writes? | Reversible by | Externally visible | Blast radius | Current mode | Verdict | Reason |
|---|---|---|---|---|---|---|---|

Every verdict must trace to the four questions. Show the tools that should *not*
gate as well as those that should: removing an unnecessary gate is part of the
deliverable, and step 5 depends on the full picture.

### 4. Write the approval request wording

This is the highest-value output. The framework hands over the raw
`function_call.name` and `function_call.arguments` and stops. Rendering is left to
the maker, and Microsoft's own sample wording is `Approve tool call
transfer_money?` — a question nobody can answer responsibly.

Generate argument-aware text per gated tool, in this order: **action, target,
consequence, scale, reversibility, decision.** Contrast the bad form with the good
one so the difference is visible:

```text
Bad:  Approve tool call send_customer_email?

Good: Send an email to a customer: hans.jensen@contoso.example
      subject: Your order has shipped
      Consequence: The customer receives this message.
      Reversible by: Nobody. Once delivered it cannot be withdrawn.
      Approve to run it now. Deny to stop it and continue without it.
```

Never render from the function name alone. Never truncate the recipient, the
amount, the count, or the irreversibility statement. Never put a secret, token, or
credential in an approval request; if a gated tool takes one as a parameter, that
is a separate finding, report it.

### 5. Estimate approval fatigue

Walk two or three representative scenarios end to end and count how often each
gate fires. Flag any bulk or batch path where a per-call gate multiplies into a
clicking exercise: ten approvals for one intent is not ten decisions, it is one
decision and nine reflexes.

**Proposed threshold: more than two approvals in a normal conversation means
redesign.** This is this skill's heuristic, not a Microsoft standard, and must be
labelled as such every time it is used. Offer it, let the user override it, and
record which threshold was applied.

When the threshold is exceeded, fix the design rather than the number: batch the
operation behind one approval that states the full scale, narrow an
over-broad tool, or split the read half from the write half so only the write
gates.

### 6. Emit the code

Produce the `approval_mode` diffs:

```diff
- @tool
+ @tool(approval_mode="always_require")
  def issue_refund(order_id: str, amount: float) -> str:
```

Then produce the renderer and the loop, adapted from
`assets/templates/approval_renderer.py` and `assets/templates/approval_loop.py`.
The loop matters because the documented sample contains, verbatim,
`user_approval = True  # Replace with actual user input`. Never ship a loop whose
approval value is a constant. The decision must come from a real human through a
real surface.

For Go, emit `tool.ApprovalRequiredFunc(...)` and describe the middleware. For
.NET, emit `ApprovalRequiredAIFunction` usage. Both are documented contracts, not
packaged harnesses here.

### 7. Rule on approve-for-session, per tool

Session unlock is a bypass in disguise: one click authorises every later call in
the conversation. Rule per tool with a reason.

* Reasonable on read-heavy or low-consequence tools whose worst case is noise.
* Not acceptable on anything that moves money, sends external communication, or
  deletes, because the second call is approved by a click that was reading about
  the first.

GitHub Copilot agent mode in Visual Studio and SSMS already ships Allow once,
Allow for this session, and Allow always. Cite it as prior art for the shape of
the control, not as a claim about any other product's behaviour.

### 8. Check the deny path

An agent that dead-ends, loops, or silently retries on refusal is broken, and its
gate is theatre. For every gated tool, verify a rejection instruction exists and
write one where it does not. A denied run must tell the user what was declined and
continue with whatever does not depend on it.

The approval response carries a boolean only. To convey *why* and *what next*,
add an ordinary user message alongside it and put the behaviour in the agent's
instructions. Then test it by actually denying, not by reading the code.

### 9. Commit the decision record

The final deliverable is a markdown file in the user's repository, from
`assets/templates/decision-record.md`. It must contain: scope and surface; how the
inventory was produced; the gating matrix; per gated tool the wording, the session
ruling, and the deny path; the fatigue result and which threshold was used; open
judgements; and the named human who ruled, with the date.

The last section is the point of the document. The skill proposes with reasons, a
human rules, and the ruling is written down where the next person can find it. A
record with no named human in it means the design has not been ruled on.

## Return the complete package

```markdown
## Scope and surface boundary
## Inventory
## Gating matrix
## Approval request wording
## Approval fatigue
## Code changes
## Approve-for-session rulings
## Deny paths
## Decision record
## What a human still has to decide
```

## Guardrails

* Never end a run in advice when an artifact was possible.
* Never present approval as authorization, or a gate as a security boundary.
* Never describe Copilot Studio per-tool approval as configurable today, and
  never give steps for it. It is roadmap item 570434, GA target September 2026.
* Never present the parser's signals as verdicts, or a supplied inventory as a
  parsed one.
* Never render an approval request from a function name alone.
* Never put a secret, token, credential, or raw production record in an approval
  request.
* Never ship an approval loop whose decision is a hardcoded constant.
* Never allow approve-for-session on an irreversible or externally visible tool.
* Never present the fatigue threshold as a Microsoft standard.
* Never invent an API, a parameter, an approval mode, or a UI affordance that is
  not in `references/surfaces-and-contracts.md`.
* Never decide the customer's risk appetite for them. Propose, give the reason,
  and leave the ruling to a named human.
