---
name: power-automate-documentation
description: >
  Trigger whenever the user uploads or references a Power Automate solution `.zip` and asks about references, dependencies on other flows, or related questions — phrasing like "document this flow", "what does this flow read/write/touch", "map the connection references", "audit this solution", or "which flows call which".
---

You are producing a **technical reference document** for a Power Automate solution export: what each flow does, in plain English, and every place it reaches outside itself to read, write, or delete data. The source of truth is always the JSON inside the solution zip, never the flow's display name or your assumptions about what a flow "probably" does.

**Inventory before you narrate.** The failure mode to avoid: skimming a flow's JSON, writing a plausible-sounding summary, and closing with a note that "a fuller audit would require deeper parsing." If you ever find yourself about to write a sentence like that, it means you skipped the inventory step below — go back and do it, don't disclose the shortcut instead of taking it. Every action in every flow gets listed and accounted for; there is no partial-credit version of this task.

## Solution Zip Anatomy

An unpacked solution zip has this shape:

- **`solution.xml`** — `SolutionManifest`: `UniqueName`, `Version`, `Managed` (0 = unmanaged, 1 = managed), `Publisher`.
- **`customizations.xml`** — a `<Workflows>` element listing every flow in the solution, and a `<connectionreferences>` element. `WorkflowId` and `Name` are always attributes on `<Workflow>`; everything else (`JsonFileName`, `Category`, `StateCode`, `StatusCode`, ...) appears as attributes in compact/hand-built exports but as child elements in full Dataverse exports (e.g. via `pac solution unpack` or a live environment export) — read whichever form is present. When `StateCode`/`StatusCode` are present, `0`/`1` means the flow is Draft (off) and `1`/`2` means it's Activated (on) — worth a one-line note per flow. `<connectionreferences>` is often empty even when flows use connectors — the connection is then resolved through the flow JSON itself (see below). Real Dataverse exports may instead ship one file per connection reference under a top-level `connectionreferences/` folder — check for that folder too, and treat it as the same information as an inline `<connectionreferences>` entry.
- **`Workflows/*.json`** — one file per flow, keyed at `properties.definition.triggers` and `properties.definition.actions`, using the standard Logic Apps workflow-definition schema. Full exports also carry `properties.connectionReferences` — see below.

If more than one solution zip is provided in the same request, treat each as an independent solution for the per-flow steps below, but pool their flow-ID maps before resolving child-flow calls, so a call in one zip can resolve to a flow shipped in another.

### Resolving connection references

A connector action's `inputs.host.connectionName` (e.g. `"shared_sharepointonline"`) is **not** itself the declared connection reference — it's a short key into the flow's own `properties.connectionReferences` block:

```json
"properties": {
  "connectionReferences": {
    "shared_sharepointonline": {
      "connection": { "connectionReferenceLogicalName": "new_sharedsharepointonline_3d8ac" },
      "api": { "name": "shared_sharepointonline" },
      "runtimeSource": "embedded"
    }
  }
}
```

Resolve in two hops: `action.inputs.host.connectionName` → `flow.properties.connectionReferences[key].connection.connectionReferenceLogicalName` → match that logical name against `customizations.xml`'s `<connectionreference connectionreferencelogicalname="...">` for the human-readable `connectionreferencedisplayname`. If `properties.connectionReferences` is absent from the flow JSON (common in hand-built/test exports), fall back to the connector name embedded directly in `host.apiId`/`host.connectionName` — there's no indirection to resolve, and that's fine, not an error.

`runtimeSource` is worth carrying into the output: `"embedded"` means the flow always runs using the same fixed connection (usually the maker's); `"invoker"` means it runs using whoever triggered the flow's own connection — a meaningful distinction for a data-access audit, since "invoker" means access actually varies by user.

## Building the Action Inventory (do this before classifying or writing anything)

For **every** flow, before you assign a single category or write a single sentence of prose, produce a flat, numbered list of every trigger and action in that flow, walking the JSON depth-first in document order:

1. List the trigger first.
2. List each top-level action in `properties.definition.actions`, in the order they appear.
3. **Whenever an action's JSON contains a nested `actions` object** — directly, or under `else.actions`, under any entry of `cases.*.actions`, or under `default.actions` — stop and list every one of those nested actions too, indented under their parent, before moving on to the next sibling at the outer level. An `If` is not one list item; it's one list item *plus* however many actions sit inside its `true` branch *plus* however many sit inside its `else`. A `Switch` is one item plus every action in every case plus every action in `default`. A `Scope`, `Foreach`, or `Until` is one item plus everything inside it.

Do not summarize a branch ("...then it branches into approval handling with a few notification steps") in place of listing it. Name every action. A flow with three top-level actions where one is an `If` containing four nested actions produces an inventory of at least seven lines, not three — if your inventory for a flow with visible branching, looping, or scopes has as few entries as it has top-level actions, you have not actually recursed into it yet.

Keep this inventory around — every flow's final documentation must account for every line in its inventory (see Reconciliation below).

## Classifying Inventoried Actions

Every action has a `type`. Classify by type first:

| `type` | Category | Notes |
|---|---|---|
| `If`, `Switch`, `Scope`, `Foreach`, `Until`, `Terminate`, `Response` | Control flow | No data access by itself — narrate the branching, don't skip it |
| `OpenApiConnection` | Connector call | `host.connectionName`/`apiId`/`operationId` — this is where Read/Write/Delete gets decided |
| `OpenApiConnectionWebhook`, `ApiConnectionNotification` | Connector call, blocking | Can appear under `triggers` **or** mid-flow under `actions` (e.g. "Start and wait for an approval") — either way it pauses the run until an external response arrives; narrate the wait and note `limit.timeout` if present |
| `Http` | Raw HTTP call | Classify by `inputs.method`, not the URL |
| `Compose`, `ParseJson`, `Query`, `Select`, `Join`, `Table` | Data shaping | **No external access.** These only rearrange data already sitting in the run. `Query` is the *Filter array* action — an in-memory filter, not a database query — do not list it as a read even though the name suggests otherwise |
| `InitializeVariable`, `SetVariable`, `IncrementVariable`, `DecrementVariable`, `AppendToArrayVariable`, `AppendToStringVariable` | Variable op | Internal run state only |
| `Workflow` | Child-flow call | `host.workflowReferenceName` is the called flow's GUID — resolve against the pooled flow-ID map |
| `OpenApiConnection` where `apiId` contains `shared_flowmanagement` | Flow-management call | A second, easy-to-miss call-graph mechanism, distinct from the native `Workflow` type — `GetFlow` reads another flow's metadata, `RunFlow`-style operations execute one; the target GUID sits in `parameters.flowName`; resolve it the same way as a child-flow call |

A `Request`/`manual` trigger with `kind: "Button"` means the flow itself is callable — manually, from Power Apps, or as a child flow. Whether it's *actually* called is a call-graph question, answered by checking every other flow in the solution(s) for a call targeting this flow's GUID — not something the trigger alone tells you.

### Read / Write / Delete

Only connector calls, HTTP calls, connector-based triggers, and flow-management calls count as data access.

1. Match `operationId` (or the action name, if missing) against these verbs: **Read** = Get, List, Search, Find; **Write** = Create, Add, Post, Insert, New, Update, Patch, Edit, Set, Replace, Send, Upload, Run, Trigger; **Delete** = Delete, Remove.
2. `Http` actions: `GET`→Read, `POST`/`PUT`/`PATCH`→Write, `DELETE`→Delete.
3. connector trigger (webhook or polling) is **Read** — the flow is consuming an inbound record or event — unless the operation clearly creates something.
4. Actions that send a message or notification (email, Teams post, approval request) have nothing in the flow to read back — label them **Write (send)** rather than omitting them.
5. If an operation genuinely doesn't match anything above (a custom connector with an opaque name), say so explicitly in the output — "Access unclear from operationId `{name}`" — rather than guessing.

Collapse Create/Update/Send into **Write** in the output table, keeping the specific verb in parentheses: `Write (create)`, `Write (update)`, `Write (send)`.

**Flag placeholders, not just targets.** If a target parameter (a table/list ID, folder path, recipient) is an obvious unconfigured stub — contains text like `REPLACE_WITH`, `TODO`, `XXX`, or is a bare GUID with no accompanying display name — say so plainly: `SharePoint list ID 0945fc53-... (display name not in export)` or `⚠ placeholder — table not yet configured`. Don't silently clean up an unconfigured flow into looking finished.

## Writing the Process Narrative

Write the "Process" section as prose a teammate could follow without opening the flow, covering **every** entry from your action inventory in order:

- **If** — "Branches on {expression, in plain English}: if true, {summarize true actions}; otherwise {summarize false actions}."
- **Switch** — "Routes on {expression}: case *X* → …; case *Y* → …; no match → {default actions}."
- **Conditional execution by `runAfter` status** — any action whose `runAfter` keys a prior action with `Failed` is error handling, regardless of what it's named: "If {prior action} fails, {this action} runs as recovery." One that runs after `Succeeded`, `Failed`, *and* `Skipped` together is a "finally" — always runs. One that runs after `TimedOut` is a timeout handler — pair it with the prior action's `limit.timeout`. The behaviour comes from `runAfter`, not the name.
- **Foreach** — "Loops over {collection}; for each item, {summarize inner actions}."
- **Until** — "Repeats {inner actions} until {condition} (capped at {limit.count} iterations / {limit.timeout})."
- **Terminate** — "Stops the run immediately with status `{runStatus}`{, reason if present}." Inside an `If`, call it a guard clause.
- **Child-flow / flow-management call** — "Calls **{resolved flow name}**." or "Calls a flow not present in any solution zip provided (GUID `{guid}`)" if unresolved.
- **Trigger cadence** — a `recurrence` block → Automated (polling): state the interval. A `splitOn` alongside it → runs once per new item, not once per poll — say so. Neither present, just `Request`/`manual` → Instant.
- **`description` fields** — when an action carries a human-authored `description`, fold it into the narrative near that action rather than dropping it, and flag it explicitly if it references a step that doesn't actually exist in the flow's action list — that's a real discrepancy worth surfacing, not something to paper over.

## Reconciliation Check

For each flow, count: how many lines were in your action inventory? Now check your finished write-up — every one of those actions must appear either in the Process narrative, in the Data access table, in External HTTP calls, or explicitly in Connection references. If you can't point to where an inventoried action ended up, it's missing, not summarized — go back and add it. A flow with a `Switch` with four cases needs four cases described, not "several outcomes are handled."

## Output Template

The output should be one Markdown document per solution zip. Solution-level overview first, then one `##` section per flow, following this strict format

```markdown
# {Solution unique name} — Flow Documentation

**Version:** {version} · **Managed:** {yes/no} · **Publisher:** {publisher}

## Flows in this solution
| Flow | Trigger type | Calls | Called by |
|---|---|---|---|
| {name} | {trigger summary} | {child flows called, or "—"} | {flows that call it, or "—"} |

---

## {Flow display name}

**Flow ID:** {guid}

### Purpose
{1–3 sentence plain-English summary of what the flow accomplishes end to end.}

### Trigger
{Type (Instant/Automated/Scheduled), connector if any, and the input schema as a short table or list.}

### Process
{Narrated walkthrough covering every inventoried action, in execution order.}

### Connection references
| Connector | Connection name | Binding | Used by |
|---|---|---|---|
{Binding = "embedded" or "invoker"; or: "This flow makes no connector calls."}

### Data access
| Action | System / entity | Access |
|---|---|---|
{Access = Read / Write (verb) / Delete. Omit pure data-shaping and variable actions — they're covered in Process.}

### External HTTP calls
{Same table shape; omit this section entirely if the flow makes none.}

### Interacts with other flows
- **Calls:** {resolved child-flow / flow-management names, or "None."}
- **Called by:** {flow names found across the solution(s) provided, or "None found in this solution — it may still be run manually, from Power Apps, or from a flow outside the zip(s) provided."}
```

Example reconciliation (hypothetical): every inventoried trigger/action should be referenced somewhere in the write-up (Process narrative, Data access, External HTTP calls, or Connection references). Nothing should be dropped.

## Workflow

1. **Unpack every solution zip** and read `solution.xml` and `customizations.xml`, from the Solution Zip Anatomy reference. Completion: a table of every flow (name, ID, JSON file) and every declared connection reference (even if empty) for each solution.
2. **Build the action inventory for every flow** (Building the Action Inventory, above). Completion: a flat, numbered, fully-recursed list per flow — checkable by eye against the raw JSON's nesting, not just the top-level action count.
3. **Classify every inventoried action and assign Read/Write/Delete** (Classifying Inventoried Actions, above), resolving each connector call's connection through the two-hop chain. Completion: every inventory entry has a category; every data-touching one has a target and an access label, or an explicit "access unclear" note.
4. **Resolve every child-flow and flow-management call** against the pooled flow-ID map across every zip in this request, and invert them into a "called by" list per flow. Completion: every such call is a resolved name or explicitly marked as outside the provided zip(s); every flow states both what it calls and what calls it.
5. **Write the documentation** using the Output Template, then run the Reconciliation Check on every flow before moving to the next. Completion: no flow is finished while an inventory line can't be located in the write-up.
6. **Send the documentation** to the user