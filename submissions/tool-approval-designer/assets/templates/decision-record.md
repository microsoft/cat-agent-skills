# Tool approval decision record: <agent name>

<!--
Template. The skill fills this in and commits it to the user's repository.
Delete every angle-bracket placeholder and every HTML comment before committing.
A section with nothing in it is a finding, not a blank. Write "none" and say why.
-->

## 1. Scope and surface

| Field | Value |
|---|---|
| Codebase | `<repo or path>` |
| Runtime | `<Agent Framework Python / Go / .NET, or other>` |
| Agent | `<agent name and entry point>` |
| Surface this design targets | `<where approvals are actually rendered and answered>` |
| Surfaces explicitly out of scope | `<list them>` |

<!--
Be specific about the surface. A design that works in a custom Python host does not
transfer unchanged to Copilot Studio, and the Copilot Studio per-tool approval toggle
is roadmap-announced (M365 roadmap item 570434, GA September 2026, status "In
development") with no Microsoft Learn documentation. See
references/surfaces-and-contracts.md.
-->

## 2. How the inventory was produced

- Method: `<parsed / supplied by the user / both>`
- Command, if one ran: `python scripts/inventory_tools.py <path>`
- Tools found: `<n>` — gated `<n>`, ungated `<n>`
- Anything the parse could not see: `<dynamic registration, generated tools, other languages>`

<!--
If any part of the inventory was supplied rather than parsed, say so here in plain
words. A decision record that implies a machine read code it never read is worse than
one that admits the gap.
-->

## 3. Gating matrix

Every verdict traces to the four questions. `Reversible by` and `Externally visible`
are the two facts that carry the rule: irreversible **and** externally visible must
always gate; reversible-by-anyone **and** internal-only must not.

| Tool | Writes? | Reversible by | Externally visible | Blast radius | Current mode | Verdict | Reason |
|---|---|---|---|---|---|---|---|
| `<tool>` | yes/no | anyone / admin or IT / nobody | yes/no | one / many | `<mode>` | **gate** / **no gate** | `<one sentence>` |

Changes required:

```diff
- @tool
+ @tool(approval_mode="always_require")
  def <tool_name>(...):
```

## 4. Gated tools

<!-- Repeat this block per gated tool. -->

### `<tool_name>`

**Why it gates.** `<the two facts from the matrix, in one sentence>`

**Approval request wording.**

```text
<Action>: <target from the actual argument values>
Scale: <count, when the blast radius is many>
<key argument>: <value>
Consequence: <the specific irreversible or external effect>
Reversible by: <who, or nobody>
Approve to run it now. Deny to stop it and continue without it.
```

**Approve for session:** `<allowed / not allowed>`

Reason: `<why one click may or may not authorise every later call in the conversation>`

<!--
Session unlock is a bypass in disguise. It is reasonable on a read-heavy lookup whose
worst case is noise. It is not reasonable on a tool that moves money, sends external
mail, or deletes, because the second call is approved by a click that was reading
about the first.
-->

**Deny path.** What the agent does when this is refused:

`<the instruction that exists, or the instruction being added>`

Verified by actually denying: `<yes / no>`

## 5. Approval fatigue

| Scenario | Tool calls | Approvals fired | Notes |
|---|---|---|---|
| `<a normal conversation>` | `<n>` | `<n>` | |
| `<a bulk or batch case>` | `<n>` | `<n>` | `<does one gate multiply into many clicks?>` |

- Threshold used: `<more than two approvals in a normal conversation, or the user's own>`
- Source of the threshold: `<this skill's proposed heuristic / the user's own standard>`
- Result: `<within threshold / redesign needed>`
- If redesign is needed: `<batch the operation behind one approval, narrow the tool, or
  split read from write>`

<!--
The default threshold is this skill's proposed heuristic. It is not a Microsoft
standard and must not be presented as one.
-->

## 6. Open judgements

Things proposed with a reason that no human has ruled on yet.

| Item | What the skill proposed | Why it is not settled |
|---|---|---|
| `<tool or decision>` | `<proposal>` | `<the risk-appetite question only the owner can answer>` |

## 7. The ruling

| Field | Value |
|---|---|
| Accepted by | `<full name and role>` |
| Date | `<YYYY-MM-DD>` |
| Accepted as written | `<yes / with the changes listed below>` |
| Changes on acceptance | `<none, or what changed and why>` |
| Review trigger | `<when this record must be revisited: new tool, new surface, incident>` |

<!--
This section is the point of the document. Approval is not authorization: a gate
records that a human clicked, not that the action was permitted. The permission model
lives in the underlying system. If this record has no named human in it, the design has
not been ruled on and the gates are decoration.
-->
