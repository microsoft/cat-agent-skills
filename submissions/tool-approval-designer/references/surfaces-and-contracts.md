# Surfaces and contracts

Verified product facts for each surface this skill touches, plus the output contracts the
workflow depends on. Every claim below is traceable to the cited source. Do not extend
this file with unverified API detail.

Read the surface section for the runtime you are producing code for. Read the contracts
section when assembling step 2, step 3, step 4, or step 9 output.

---

## 1. Surface boundary

Approval is not one feature. It is several, at different maturities, on different
runtimes. State which one you are producing for before you produce anything.

| Surface | Approval capability | This skill's coverage |
|---|---|---|
| Agent Framework, Python | `@tool(approval_mode=...)`, `result.user_input_requests` | **Fully covered.** Inventory is parsed, code is emitted. |
| Agent Framework, Go | `tool.ApprovalRequiredFunc`, middleware | **Documented.** Best-effort inventory only, no emitted harness. |
| Agent Framework, .NET | `ApprovalRequiredAIFunction` | **Documented.** Not parsed. Emit code only from the snippets below. |
| Agent Framework Harness Agent | Queued requests, standing rules, optional heuristic auto-approval | **Documented.** Affects the step 7 session ruling. |
| Copilot Studio per-tool approval | Per-tool, per-agent toggle | **Roadmap-sourced only.** See section 6. No configuration steps. |
| GitHub Copilot agent mode (Visual Studio, SSMS) | Allow once / for this session / always | **Prior art only.** Not a build target. See section 7. |

---

## 2. Agent Framework, Python (fully covered)

Source: [Using function tools with human in the loop approvals](https://learn.microsoft.com/en-us/agent-framework/agents/tools/tool-approval),
Python pivot.

### Marking a tool

```python
from typing import Annotated
from agent_framework import tool

@tool(approval_mode="always_require")
def get_weather_detail(location: Annotated[str, "The city and state, e.g. San Francisco, CA"]) -> str:
    """Get detailed weather information for a given location."""
    return f"The weather in {location} is cloudy with a high of 15C, humidity 88%."
```

### Approval modes

Source: [Human-in-the-Loop with AG-UI](https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/ui/ag-ui/human-in-the-loop).

| Mode | Behaviour |
|---|---|
| `always_require` | Always request approval before execution. |
| `never_require` | Never request approval. **This is the default.** |
| `conditional` | Request approval based on certain conditions. The custom logic is yours to supply. |

A tool with no `approval_mode` is therefore ungated. Absence of the argument is a
decision, not an omission, and the decision record must say which one it was.

### What the inventory will and will not claim

`@tool` is not a reserved name. Several unrelated libraries export one, and a codebase
can define its own. Reading every `@tool` as an Agent Framework tool would report an
`approval_mode` column for tools that have no such concept, which is worse than
reporting nothing. `inventory_tools.py` therefore attributes before it claims:

| What the file shows | Reported as |
|---|---|
| `from agent_framework import tool`, a submodule import, an alias, `import agent_framework as af` with `@af.tool`, or a star import from `agent_framework` | `parsed` |
| `tool` imported from any other module, or defined in the file itself | not reported; a note names the module it came from |
| a bare `@tool`, or `@agent_framework.tool` with no matching import, and nothing in the file to trace it to | `best-effort`, with a note on the record |

When a run reports fewer tools than the maker expects, read the notes before
concluding the codebase is clean. A skipped file is not an empty one.

### What a gated run returns

An agent run that requires user input completes with a response indicating what input is
required **instead of completing with a final answer**. The caller is responsible for
obtaining that input and passing it back in a new run.

```python
result = await agent.run("What is the detailed weather like in Amsterdam?")

if result.user_input_requests:
    for user_input_needed in result.user_input_requests:
        if user_input_needed.function_call is None:
            continue
        print(f"Function: {user_input_needed.function_call.name}")
        print(f"Arguments: {user_input_needed.function_call.arguments}")
```

The framework gives you `name` and `arguments`. It does not give you a sentence a human
can judge. Producing that sentence is step 4 of the workflow.

### Responding

```python
from agent_framework import Message

approval_message = Message(
    role="user",
    contents=[user_input_needed.to_function_approval_response(user_approval)]
)

final_result = await agent.run([
    "What is the detailed weather like in Amsterdam?",
    Message(role="assistant", contents=[user_input_needed]),
    approval_message
])
```

Pass `True` to approve, `False` to reject. Without a session, each iteration must carry
the original query, the assistant message holding the request, and the approval response.

### The documented gap

Microsoft's own approval loop sample contains, verbatim:

```python
# Get user approval (in practice, this would be interactive)
user_approval = True  # Replace with actual user input
```

That line is honest sample brevity, and it is exactly the seam this skill fills. A gate
whose approval value is a constant is not a gate. When reviewing an existing
implementation, search for a hardcoded approval value and treat it as a finding.

---

## 3. Agent Framework, Go (documented, best-effort inventory)

Source: same Learn page, Go pivot.

```go
import "github.com/microsoft/agent-framework-go/tool"

approvedWeatherTool := tool.ApprovalRequiredFunc(weatherTool)
```

When the model requests a tool call, the framework intercepts it and waits for approval
before executing. The approval flow is handled through middleware.

Limits to respect:

* The Python standard library cannot parse Go, so `inventory_tools.py` detects Go tools
  with a bounded regular expression and labels the result best-effort. Never present a Go
  inventory as complete.
* This skill does not ship a packaged Go approval harness. Produce the gating matrix, the
  wording, and the rulings; hand the middleware implementation to the maker.

---

## 4. Agent Framework, .NET (documented, not parsed)

Source: same Learn page, C# pivot.

```csharp
AIFunction weatherFunction = AIFunctionFactory.Create(GetWeather);
AIFunction approvalRequiredWeatherFunction = new ApprovalRequiredAIFunction(weatherFunction);
```

Detecting the request and responding:

```csharp
var toolApprovalRequests = response.Messages
    .SelectMany(x => x.Contents)
    .OfType<ToolApprovalRequestContent>()
    .ToList();

ToolApprovalRequestContent requestContent = toolApprovalRequests.First();
var functionCall = (FunctionCallContent)requestContent.ToolCall;

var approvalMessage = new ChatMessage(ChatRole.User, [requestContent.CreateResponse(true)]);
await agent.RunAsync(approvalMessage, session);
```

Reuse the same `AgentSession` when sending the response so the interrupted run can
continue. `CreateResponse(false)` rejects.

`inventory_tools.py` does not parse C#. For a .NET codebase, run step 2 as a guided
inventory instead: ask the user to list the tools registered on the agent, then continue
from step 2 unchanged. Say plainly that the inventory was supplied rather than parsed.

---

## 5. Harness Agent (affects the session ruling)

Source: same Learn page, "Use tool approval with Harness Agent".

Plain composition requires an approval-marked tool plus an approval-response loop. A
Harness Agent uses the same approval-marked tools and response content, and additionally
installs middleware for:

* queued approval requests,
* standing "always approve" rules,
* optional heuristic auto-approval.

In .NET, `DisableToolAutoApproval` defaults to `false`, so the harness adds
`ToolApprovalAgent`. With the default `ToolApprovalAgentOptions`, no heuristic rules are
configured, and unmatched approval requests still return to the caller. Trusted
auto-approval callbacks are added through `ToolApprovalAgentOptions.AutoApprovalRules`.
Setting `DisableToolAutoApproval = true` removes only the standing-rule, queuing, and
heuristic middleware. **It does not remove the approval requirement from an
`ApprovalRequiredAIFunction`.**

Consequence for step 7: on a Harness Agent, "approve for session" is not the only bypass
in play. A standing rule or a heuristic auto-approval callback is a permanent bypass, and
it must be ruled on in the decision record with the same rigour as session unlock.

---

## 6. Copilot Studio per-tool approval (roadmap-sourced, not documented)

**Status: announced on the Microsoft 365 roadmap, not yet documented on Microsoft Learn.**

Source: Microsoft 365 roadmap item **570434**, "Microsoft Copilot Studio: Enabling makers
to require human approval for tool calls".

What the roadmap item states:

* A per-tool, per-agent toggle requires human approval before an agent runs specific tools.
* A gated tool call pauses and shows an approval request describing what the agent intends
  to do.
* The responder can **approve**, **approve for the session**, or **deny** before the action
  runs.
* It is positioned as a deterministic guardrail for high-stakes operations such as sending
  emails, closing tickets, or processing payments, independent of the agent's instructions.
* Approval requests appear inline in the channel where the agent is deployed, including
  Microsoft Teams and Microsoft 365 Copilot.
* Release ring: General Availability. Availability: September 2026. Status at the time this
  skill was written: **In development**.

What this means for the skill:

* **No Microsoft Learn documentation page for this capability was found.** Every statement
  above comes from the roadmap entry and nowhere else.
* **Do not give configuration steps.** Do not describe menu paths, toggle locations,
  setting names, API surfaces, or solution schema for it. None of that is documented, and
  inventing it is the exact failure mode this section exists to prevent.
* **Do not tell a user to go and switch it on.** Verify current availability in the product
  before acting on this section.
* The three announced response options would map onto this skill's step 7 ruling, so a
  Copilot
  Studio design is still worth producing. Produce it as **portable intent**: which tools
  should gate, what the request should say, and whether approve-for-session is acceptable
  per tool. That intent survives whatever the shipped configuration surface turns out to be.

---

## 7. GitHub Copilot agent mode (prior art, not a target)

Source: [Use GitHub Copilot agent mode in SSMS](https://learn.microsoft.com/en-us/ssms/github-copilot/agent-mode).

Cited because it is a shipped, documented answer to the session-unlock problem that step 7
reasons about:

| Option | Documented behaviour |
|---|---|
| **Allow once** | Approves this single invocation. |
| **Allow for this session** | Approves this tool for the rest of the current chat session. |
| **Allow always** | Approves this tool for all subsequent invocations. |

Approvals are reset from **Tools > Options > GitHub > Copilot > Tools**. The same page
documents Visual Studio-style confirmation before running a terminal command or using a
tool that is not built in.

The most important sentence on that page, for this skill's purposes:

> Copilot's approval system isn't a security boundary. Apply the principle of
> least-privilege in your database: grant users only the permissions they need on specific
> objects.

That is the load-bearing guardrail. An approval gate is a **deliberation** control: it
buys a human the chance to think before an irreversible act. It is not an authorization
control. If the only thing standing between a caller and an action they should never be
able to perform is an approval dialog, the design is wrong at a layer this skill cannot
fix, and the decision record must say so.

---

## 8. The four questions

The deterministic core. Answer all four for every tool, in this order.

| # | Question | Allowed answers |
|---|---|---|
| 1 | Does it write, or only read? | `read` / `write` |
| 2 | Is the write reversible, and by whom? | `anyone` / `admin-or-it` / `nobody` |
| 3 | Is the result visible outside the organisation? | `internal` / `external` |
| 4 | What is the blast radius? | `one` / `many` |

Question 2 is about the **person**, not the technology. A database row that only a DBA can
restore from a backup is not reversible by the person who approved the call. Answer for the
approver's own capability.

Question 3 is about **reaching a third party**, not about network topology. An email to a
customer, a public post, a payment, a webhook to a partner, a ticket the customer sees: all
external. An internal Teams message is internal. Something already sent cannot be unsent,
so questions 2 and 3 interact.

### The rule

| Condition | Verdict |
|---|---|
| Question 2 is `nobody` **and** question 3 is `external` | **Must gate.** Not negotiable. |
| Question 1 is `read` | **Must not gate.** Gating reads is the fastest route to fatigue. |
| Question 2 is `anyone` **and** question 3 is `internal` | **Should not gate.** |
| Anything else | **Judgement.** State the reason in one sentence, and name the question that drove it. |

A judgement verdict without a stated reason is an incomplete deliverable. "It felt risky"
is not a reason. "Question 2 is `admin-or-it` and question 4 is `many`, so a single wrong
call costs an IT ticket per affected record" is a reason.

### Escalation on blast radius

Question 4 does not usually flip a verdict on its own; it changes the **shape** of the
gate. A `many` blast radius on an otherwise gateable tool means the gate belongs on the
batch, not on each item. See the fatigue rules in section 9.

---

## 9. Fatigue thresholds

**These thresholds are this skill's proposed heuristic. They are not a Microsoft standard,
and no Microsoft documentation defines an acceptable approval rate.** Label them as such
every time you present them, and let the user override them with their own number.

| Signal | Threshold | Action |
|---|---|---|
| Approvals in one normal conversation | more than **2** | Redesign. Merge gates, raise the gate to a batch, or narrow a tool. |
| A per-call gate reachable from a bulk operation | any | Move the gate to the batch boundary and show the count in the request. |
| Two gated tools that always fire together | any | Merge into one approval covering both, or gate the calling step instead. |
| A gated tool a user hits on a routine happy path | any | The gate is on the wrong tool. Gate the exception, not the routine. |

The reason to care is not comfort. Approval fatigue is the mechanism by which a control
becomes a rubber stamp, and a rubber stamp is worse than no gate at all, because it
produces an audit record asserting that a named human considered the action.

---

## 10. Approval request contract

Every generated approval request must carry these, in this order:

| Element | Requirement |
|---|---|
| Action | The verb, in the user's language, not the function name. |
| Target | Who or what is affected, from the actual argument values. |
| Consequence | The specific irreversible or external effect, stated plainly. |
| Scale | The count, whenever the blast radius is `many`. |
| Reversibility | Who can undo it, or that nobody can. |
| Decision | What approve and deny each do next. |

Never render an approval request from the function name alone. The framework's own
generic form, `Approve tool call transfer_money?`, is the anti-pattern: it asks a human to
authorise something they cannot see.

Truncate long argument values for display, but never truncate the recipient, the amount,
the count, or the irreversibility statement. If a value is too long to show, show its
shape and its size, not a silent ellipsis.

Secrets, tokens, and credentials never appear in an approval request. If a gated tool takes
one as a parameter, that is a separate finding: report it and keep it out of the rendered
text.

---

## 11. Decision record contract

The final deliverable is a markdown file committed to the user's repository. Required
sections:

1. **Scope and surface.** Which codebase, which runtime, which agent, and which surface
   the design targets.
2. **How the inventory was produced.** Parsed, supplied, or both. Name the command if a
   command ran.
3. **The gating matrix.** One row per tool, with all four answers and the verdict.
4. **Per gated tool:** the approval request wording, the approve-for-session ruling with
   its reason, and the deny path.
5. **Fatigue result.** Scenarios walked, approvals counted, threshold used, and whether the
   threshold was the skill's default or the user's own.
6. **Open judgements.** Anything the skill proposed that the human has not yet ruled on.
7. **The ruling.** The named human who accepted the design, and the date.

Section 7 is the point of the document. The skill proposes with reasons; a human rules;
the ruling is written down where the next person can find it.
