# Tool Approval Designer

Decide which of an agent's tools must stop for a human, write what the human
actually reads, check that the design will not be clicked through, and emit the
code and the record.

## Surface boundary, first

What runs where is not interchangeable. Read this before adopting the skill.

| Surface | What the skill does |
|---|---|
| Microsoft Agent Framework, **Python** | Full support. Parses tools from source, emits `approval_mode` diffs, an approval renderer, and an approval loop. |
| Microsoft Agent Framework, **Go** | Documented contract and emitted code shape. Detection is best-effort regex, not a parse. No packaged harness. |
| Microsoft Agent Framework, **.NET / C#** | Documented contract and emitted code shape. Not parsed; the inventory is supplied by you. |
| **Harness Agent** | Documented middleware behaviour, including auto-approval rules. |
| **Copilot Studio** | Design guidance only. See the warning below. |
| **GitHub Copilot agent mode** | Cited as prior art for the session-unlock problem. Not configured by this skill. |

> **Copilot Studio per-tool approval is roadmap-announced, not documented.**
> The source is Microsoft 365 roadmap item **570434**, GA target **September 2026**,
> status **"In development"**, and no Microsoft Learn documentation page for it was
> found. The skill will not give you configuration steps for it, and will tell you
> that the Copilot Studio part of any design needs re-checking against
> documentation when it ships. If you need something you can switch on today, use
> the Agent Framework path.

The skill may be loaded into a harness that cannot execute Python. In that case it
skips the parse, builds the inventory with you by hand, and labels it as supplied.

## The problem it solves

Microsoft Agent Framework gives you a mechanism and stops at the interesting part.
You mark a tool with `@tool(approval_mode="always_require")`, the run pauses, and
the framework hands your code a raw function call name and an argument blob. What
the human sees, and whether it means anything to them, is entirely yours to build.
The documented sample loop closes that gap with a constant:

```python
user_approval = True  # Replace with actual user input
```

Two failures follow from that seam. The first is obvious: gates that never really
ask. The second is worse, and is the reason this skill exists.

**A badly designed gate manufactures accountability.** If the prompt fires on
everything, or says only `Approve tool call transfer_money?`, people click through
it. The log then records that a named employee approved a specific action at a
specific time. It did not happen. Nobody read it. You have built an audit trail
that documents consent that was never given, and you will find out during the
incident review.

So the design work is not "add approvals". It is: gate the small number of things
that genuinely need it, word them so a human can judge them in three seconds, and
prove the volume stays low enough that people still read them.

## What it produces

Artifacts, every run. If a run ends in a document telling you to consider gating
your payment tool, the skill has failed.

- A **gating matrix**: one row per tool, all four decision questions answered, a
  verdict, and a one-sentence reason.
- **Approval request wording** per gated tool, generated from the real call
  arguments, carrying the consequence and who can undo it.
- An **approval fatigue estimate** over representative scenarios, with bulk paths
  flagged.
- **Code**: `approval_mode` diffs, an argument-aware renderer, and an approval loop
  whose decision comes from a human rather than a constant.
- An **approve-for-session ruling** per tool, with a reason.
- A **deny path** per gated tool, written where one is missing.
- A **decision record** committed to your repository, ending in the name of the
  human who ruled.

## The decision procedure

Four questions per tool:

1. Does it write, or only read?
2. Is the write reversible, and by whom? Anyone, admin or IT only, or nobody.
3. Is the result visible outside the organisation?
4. What is the blast radius? One record or many.

The rule: **irreversible and externally visible must always gate.**
**Reversible by anyone and internal only must not.** Everything in between is a
judgement, and the skill states a reason for every one of them.

## Before you start

You need one of these:

- a **repository path** containing Agent Framework Python tools, if you want the
  inventory parsed for you; or
- a **list of your tools** with a one-line description each, if the code is C#, Go,
  or not to hand.

You do not need to prepare answers per tool. The skill parses what it can and then
asks two or three questions covering only what cannot be inferred. That is
deliberate: a skill that interrogates you about twenty tools gets abandoned, and an
abandoned run produces no gates at all.

It helps to know, before you begin, who is allowed to rule on risk appetite. The
decision record is not finished until that person is named in it.

## How to use it

Ask for what you want in plain language:

- "Which of my agent's tools should require human approval?"
- "Design approval gates for the agent in `./src/agent`."
- "Write the approval prompt for my refund tool."
- "My agent asks for approval eleven times in a normal conversation. Fix it."
- "Is approve-for-session safe on this tool?"

If you already have findings from a red-team pass that flagged a missing
confirmation, hand them over. The skill takes them as inventory input instead of
re-deriving them.

## Running the inventory script yourself

The parser is standard library only and needs **Python 3.9 or newer**. Run it from
the skill root, the directory containing `SKILL.md`:

```bash
python scripts/inventory_tools.py assets/samples
python scripts/inventory_tools.py path/to/your/agent --format json
python scripts/inventory_tools.py path/to/your/agent --fail-on ungated-write-external
```

`--fail-on` exits non-zero when a matching tool is found, so the check can sit in
CI. Exit codes: `0` clean, `1` the `--fail-on` condition triggered, `2` usage or
IO error.

The script emits **signals, not verdicts**. It can tell you a tool looks like it
writes and looks externally visible. It cannot tell you whether the effect is
truly irreversible, and it cannot read the logic behind `approval_mode="conditional"`.
Its output is the first column of the matrix, never the matrix.

It is also conservative about what it claims. `@tool` is a common decorator name,
so a tool is only reported as `parsed` when the decorator traces to an
`agent_framework` import. One borrowed from another library, or defined in the
file itself, is skipped with a note rather than reported with an `approval_mode`
it does not have. A bare `@tool` with no traceable import is kept and marked
`best-effort`.

Test files and `tests/` directories below the scan root are skipped when scanning
a directory, unless you pass `--include-tests`. A path you name directly is
always read, including a test file or a directory that is itself named `tests`,
on the basis that pointing at a path is an explicit request. Directory names are
judged only at or below the root, so a repo that happens to live under a folder
called `build` or `venv` still scans normally.

Regression tests, from the same directory:

```bash
python scripts/tests/test_inventory_tools.py
python scripts/tests/test_approval_renderer.py
```

114 tests covering decorator and alias detection, decorator provenance, approval
mode reading, write and external and blast-radius signals including every
write-capable `open()` mode permutation, the false positives that the
vocabularies are tuned to avoid, best-effort Go detection and its line
attribution, file handling including BOM-prefixed sources, explicitly named
paths, pruned vendor directories and a repo that itself lives under a directory
named `build` or `venv`, summary agreement, output shape, and exit codes. Two of
them assert that the counts stated in this paragraph match the suites, so these
numbers cannot go stale. A further 14 cover the shipped approval renderer
template, most importantly that redaction is case-insensitive on both the
argument name and the declared redaction list, since that is the boundary
keeping a secret out of the approval text a human reads.
## Verified product facts, with sources

Every product claim the skill makes traces to one of these. Details are in
[references/surfaces-and-contracts.md](references/surfaces-and-contracts.md).

| Claim | Source |
|---|---|
| Python `@tool(approval_mode="always_require")`; a gated run returns `result.user_input_requests`; respond via `to_function_approval_response`; the sample loop hardcodes approval | [Agent Framework: tool approval](https://learn.microsoft.com/agent-framework/agents/tools/tool-approval) |
| Approval modes `always_require`, `never_require` (default), `conditional` | [Agent Framework: AG-UI human in the loop](https://learn.microsoft.com/agent-framework/integrations/by-component/ui/ag-ui/human-in-the-loop) |
| Go `tool.ApprovalRequiredFunc`, approval through middleware | [Agent Framework: tool approval](https://learn.microsoft.com/agent-framework/agents/tools/tool-approval) |
| .NET `ApprovalRequiredAIFunction`, `ToolApprovalRequestContent`, `CreateResponse` | [Agent Framework: tool approval](https://learn.microsoft.com/agent-framework/agents/tools/tool-approval) |
| "Copilot's approval system isn't a security boundary. Apply the principle of least-privilege." Allow once / Allow for this session / Allow always | [GitHub Copilot agent mode in SSMS](https://learn.microsoft.com/ssms/github-copilot/agent-mode) |
| Copilot Studio per-tool approval: roadmap only, GA target September 2026, status "In development" | Microsoft 365 roadmap item **570434** |

## Limits

- It does not deploy anything, and it does not touch a Copilot Studio environment.
- It does not decide your risk appetite. It proposes with reasons; a human rules;
  the ruling gets written down.
- It is not a security review and not a red team. It designs the gate. Finding the
  missing one is a different job.
- The approval fatigue threshold of more than two approvals in a normal
  conversation is **this skill's proposed heuristic**, not a Microsoft standard.
  Override it with your own and the record will say which one was applied.
- The parser reads Python properly, detects Go on a best-effort basis, and does not
  read C# at all. It only claims a Python `@tool` it can trace to an
  `agent_framework` import; anything else is skipped or flagged, never silently
  counted.
- Approval is not authorization. A gate records a click. Least privilege in the
  underlying system is still your job.

## Related skills in this gallery

`agent-red-team` maps attack surface and asks, per tool, whether a human confirms
before execution. It finds the missing gate; this skill decides what the gate
should be and builds it. Run them in that order.

`enterprise-agent-design-authority` works at architecture altitude across pillars;
approval design is one concern inside one of them. `agent-evaluation-designer`
measures answer quality and does not overlap.

## Author

Marc Pascal Solling — [github.com/MarcPmedC](https://github.com/MarcPmedC)
