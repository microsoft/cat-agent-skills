# Tool Tracer

**See what your Copilot Studio agent actually did behind the scenes — on demand,
in one structured file.**

Tool Tracer runs an interaction as normal, then hands back a single
`tool_trace.json` that lays out what happened *underneath* the conversation:
which actions and connectors were called (and with what inputs), what they
returned — including error codes — which calls were retried, which knowledge
sources were queried, which other skills fired, and how the run ended.

It only runs when you explicitly ask for it, so it's a **deliberate debug tool**,
not something firing on every turn.

---

## The visibility gap it closes

In the **test pane**, you can see everything: the agent's reasoning, "I'm calling
this action," the retries, the skills it triggers. That's great while you build.

But once the agent is live on a **real channel** — Teams, a web chat, a custom
app — a normal user sees only their own messages and the agent's replies
(*"Sure, let me look into that…"*). Everything the orchestrator did to produce
that answer is **hidden**:

- A connector action may have **failed with an error code** and the agent quietly
  **retried** it — invisible to the user, and to you.
- A **knowledge source** may have been queried (or missed) in a way that shaped
  the answer.
- **Another skill** may have been pulled in mid-task.

When a production interaction goes wrong, the honest answer to *"why did it do
that?"* usually requires an admin to **reproduce the whole thing in the test
pane**. Tool Tracer removes that step: ask for a trace and you get a quick,
structured account of the actual run — **what was attempted, what failed, what
was called and with which properties** — so you can triage the situation
directly.

## What it captures

- **Actions / connectors** — each call, the inputs (properties) sent, and the
  response, including failure status and **error codes**.
- **Retries** — a retried call shows up as its own step, so you can see the agent
  tried again after a failure.
- **Knowledge lookups** — that a source was queried and what came back at a trace
  level (citations / summary; see boundaries on full content).
- **Other skills** — logged as steps (`skill:<name>`) when the run pulls them in.
- **The outcome** — an overall status and a one-line summary of what was
  delivered.

---

## What it looks like

A live interaction — *"Can I still return order 4471, and when's my refund
window?"* — that looked completely normal to the customer, but wasn't underneath:

```json
{
  "trace_metadata": {
    "task_description": "Check return eligibility for order 4471 and the refund-by date.",
    "agent_name": "Contoso Support Assistant",
    "timestamp_utc": "2026-07-22T18:31:04Z",
    "total_tool_calls": 4,
    "status": "success"
  },
  "tool_calls": [
    {
      "step": 1,
      "tool_name": "search_knowledge",
      "purpose": "Find the return-eligibility policy to answer the customer.",
      "input": { "query": "return eligibility window policy" },
      "output_summary": "3 passages retrieved from KB 'Returns Policy' (article R-14: 30-day window).",
      "output_raw": "citations: [R-14 'Returns & Exchanges', R-09 'Final Sale Items']",
      "status": "success",
      "error_message": null
    },
    {
      "step": 2,
      "tool_name": "GetOrderStatus",
      "purpose": "Retrieve the current status of order 4471.",
      "input": { "orderId": "4471" },
      "output_summary": "Connector returned HTTP 500 - upstream order service timed out.",
      "output_raw": "{\"error\":\"UpstreamTimeout\",\"code\":500,\"message\":\"order-svc did not respond in 30s\"}",
      "status": "error",
      "error_message": "GetOrderStatus failed with HTTP 500 (UpstreamTimeout)"
    },
    {
      "step": 3,
      "tool_name": "GetOrderStatus",
      "purpose": "Retry the order lookup after the step 2 timeout.",
      "input": { "orderId": "4471" },
      "output_summary": "Order 4471 delivered 2026-07-19; return-eligible; no replacement created.",
      "output_raw": "{\"orderId\":\"4471\",\"status\":\"delivered\",\"deliveredDate\":\"2026-07-19\",\"returnEligible\":true}",
      "status": "success",
      "error_message": null
    },
    {
      "step": 4,
      "tool_name": "skill:date-calculator",
      "purpose": "Compute the return-by date (delivery + 30 days).",
      "input": { "start": "2026-07-19", "add_days": 30 },
      "output_summary": "Return-by date: 2026-08-18.",
      "output_raw": "2026-08-18",
      "status": "success",
      "error_message": null
    }
  ],
  "final_answer_summary": "Told the customer order 4471 is return-eligible until Aug 18. Note: the order lookup timed out once (HTTP 500) and succeeded on retry."
}
```

**Read the trace, not the transcript.** The customer got a clean answer — but the
trace reveals the order service **500'd and was retried** (steps 2-3), tells you
the exact **connector and inputs** involved, and shows the **knowledge article**
and **skill** that shaped the reply. On the channel, none of that was visible.
Now you can triage the intermittent timeout without reproducing a thing.

---

## Runs only on an explicit command

Tool Tracer fires **only** when the message contains the exact debug command:

```
/special-debug tool-trace
```

followed by the task you want traced. It deliberately does **not** respond to
casual phrasings like *"trace this"* or *"debug that"* — requiring the precise
command keeps a trace a deliberate act, so a normal user on a live channel can't
trigger one by accident and day-to-day interactions stay untouched.

Because the trace captures full-fidelity values (see boundaries below), restrict
the agent or this command to authorized admin/maker users when you deploy it, and
avoid exposing it on untrusted end-user channels.

## Where it fits

| You need to… | Tool Tracer gives you… |
| --- | --- |
| **Triage a production issue** a user hit on a channel | A rundown of what actually happened — no test-pane reproduction required. |
| **See why an answer was wrong or slow** | The failed calls, error codes, and retries hidden behind the reply. |
| **Audit which connector ran, with what properties** | Each action's exact inputs and outputs in one place. |
| **Confirm which knowledge source shaped an answer** | The knowledge queries the run made, at a trace level. |
| **Document or hand off a workflow** | A structured, repeatable record of how the task was carried out. |

## How it works

1. **Runs the interaction unchanged** — tracing never alters the agent's reasoning
   or tool use, so you capture the real run.
2. **Compiles the trace** in true execution order, with each step's inputs,
   outputs, status, and errors.
3. **Writes `tool_trace.json`** and returns it as a downloadable file.

## Honest boundaries

This is a **self-reported run summary, not a tamper-proof system log.** The trace
is compiled from what the agent can see of its own run — treat it as an honest,
high-fidelity recap for triage and debugging, not a cryptographic audit trail.
Knowledge lookups are captured at a **trace level** (that a source was queried,
plus citations/summary) — the full retrieved passage text may not always be
recoverable. When a value genuinely can't be recovered, the skill records `null`
or `"unavailable"` rather than guessing.

> **This is an admin / debug tool, and it captures values in full by design** —
> the same data the operator running it is already authorized to see, so a trace
> can contain secrets, tokens, or PHI. That fidelity *is* the point: you're
> looking at exactly what happened. Treat `tool_trace.json` with the same care as
> the underlying system data and keep it within that trusted boundary.

## Files

- `SKILL.md` — the agent-facing contract: when it triggers, the full output
  schema, and the tracing rules.
