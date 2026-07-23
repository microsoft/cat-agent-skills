---
name: tool-tracer
description: Use ONLY when the user's message contains the exact command `/special-debug tool-trace` (optionally with `--full`); run the task normally, then write `tool_trace.json` summarizing tool/action/connector calls in order. Sensitive values (secrets, tokens, PII/PHI) are redacted by default; `--full` keeps them verbatim for an authorized admin.
---

# Skill: tool-tracer

## Purpose
Runs any user task normally, then produces a structured JSON **run summary** (`tool_trace.json`) capturing every tool, action, connector, knowledge query, and sub-skill call made during the run — inputs, outputs, error codes, retries, and sequence. Built as an **admin / debug tool**: on a live channel a normal user never sees what the agent did behind the scenes, so this lets a maker or admin see it and triage an interaction without reproducing it in the test pane.

---

## Trigger
This skill activates **only** when the user's message contains the exact debug command:

```
/special-debug tool-trace
```

The command may be followed by (or precede) the task to run — e.g. `/special-debug tool-trace  look up order 4471 and email the customer`. If the command is present, run the task and produce the trace; if it is **not** present, this skill does not apply — even for casual phrasings like "trace this", "log this run", "debug this", or "what did you just do". Requiring the explicit command keeps a trace a deliberate act, not something a channel user triggers by accident.

**Two capture modes.** By default the trace runs in **redacted** mode — values that look like secrets, tokens, credentials, or PII/PHI are masked so the trace is safe to share for triage while still showing *what* ran. An authorized admin can append **`--full`** (`/special-debug tool-trace --full …`) to capture every value verbatim for deep debugging. Restrict who can use `--full` at deployment — a skill can't enforce it.

> **Scope & sensitivity.** This is an admin / debug tool. In the default **redacted** mode, values that look like secrets, tokens, credentials, or PII/PHI are masked (e.g. `"<redacted:token>"`) so the trace shows *what* ran without leaking sensitive data. In **`--full`** mode nothing is masked, so `tool_trace.json` can contain secrets, tokens, or PHI verbatim. A skill cannot enforce access control; **the maker deploying this is responsible for restricting `--full` (and the agent) to authorized admin/maker users** and for handling the file within that trust boundary. Prefer not to expose `--full` on agents published to untrusted end-user channels.

---

## Behavior

### Step 1 — Execute normally
Carry out the user's request exactly as you would without this skill. Use whatever tools are needed. Do not alter your reasoning or tool usage because tracing is active.

### Step 2 — Compile the trace
After the task is complete (or if it fails), compile a `tool_trace.json` file capturing every tool call made during the run.

### Step 3 — Save the trace file
Write `tool_trace.json` using your file-writing tool so it is returned to the user as a download. Default path: `/app/created/tool_trace.json` (the download folder in the Agent Skills sandbox). If that path or a `create` tool is unavailable in your runtime, use whatever file-writing tool exists and save to the runtime's user-download location.

---

## Output Schema

```json
{
  "trace_metadata": {
    "task_description": "<what the user asked for>",
    "agent_name": "<agent name if known, else null>",
    "timestamp_utc": "<ISO 8601 timestamp of when the task completed, or null if no clock is available>",
    "total_tool_calls": 0,
    "mode": "redacted | full",
    "status": "success | partial | failed"
  },
  "tool_calls": [
    {
      "step": 1,
      "tool_name": "<exact tool name>",
      "purpose": "<one sentence: why this tool was called at this step>",
      "input": {
        "<param_name>": "<param_value>"
      },
      "output_summary": "<concise summary of what the tool returned>",
      "output_raw": "<full raw output if ≤ ~2000 chars, else 'truncated — see output_summary'>",
      "status": "success | error",
      "error_message": null
    }
  ],
  "final_answer_summary": "<brief description of what was ultimately delivered to the user>"
}
```

---

## Rules

1. **Only log what actually happened in this run.** Do not fabricate or reconstruct tool inputs/outputs from assumption — log strictly what is present in your run context. See Gotchas.
2. **Preserve order** — `step` numbers must reflect the actual call sequence.
3. **Redact by default; full fidelity only with `--full`.** In default mode, mask any value that looks like a secret, token, credential, or PII/PHI with a typed placeholder (e.g. `"<redacted:token>"`, `"<redacted:pii>"`) — keep the field key so the call's shape stays visible. Only when the invocation includes `--full` (an authorized admin) do you record every value verbatim with no masking. Record the active mode in `trace_metadata.mode`.
4. **If a tool call failed**, still log it with "status": "error" and populate `error_message`.
5. **output_raw** should be included in full unless it exceeds ~2000 characters, in which case set it to `"truncated — see output_summary"`.
6. **Exclude the trace-writing call itself.** The file-write that saves `tool_trace.json` is instrumentation, not part of the traced task — do **not** add it to `tool_calls[]`, and do **not** count it in `total_tool_calls`.

---

## Gotchas

- **You are working from your visible run context, not a system-level call log.** Only record tool calls, inputs, and outputs that are actually present in what you can see from this run. Never invent plausible-looking values to fill the schema.
- **If a field can't be reliably recovered** (e.g., exact `output_raw` for an early call, or a `timestamp_utc` with no clock), set it to `null` or `"unavailable"` rather than guessing. Prefer a truthful `output_summary` over a reconstructed `output_raw`.

---

## Example Invocation

**User:** `/special-debug tool-trace  Get me the onboarding plan for Sarah Johnson and email the hiring manager.`

**Agent behavior:**
1. Calls `get_items` to look up Sarah Johnson in the SharePoint list → logs step 1
2. Calls `send_email_v2` to email the hiring manager → logs step 2
3. Calls `create` to write `tool_trace.json` → this instrumentation call is **excluded** from both `tool_calls[]` and `total_tool_calls` (see Rule 6)
4. Returns the file to the user

By default, any secret/token/PII in those inputs or outputs is masked in the trace (`mode: "redacted"`); append `--full` (`/special-debug tool-trace --full …`) to capture them verbatim.

---

## Notes
- This skill works alongside all other skills — if another skill (e.g., analyzing-pdf) is invoked mid-task, log that as a tool call with `tool_name: "skill:analyzing-pdf"`.
- If the task requires zero external tool calls (e.g., a pure text answer), still produce the trace file with `total_tool_calls: 0` and explain in `final_answer_summary`.
