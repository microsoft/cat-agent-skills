---
name: cowork-task-route
description: |
  Reports the task route: the skills, subagents, and tools Cowork invoked to
  complete the current task, as an ordered plain-language trail. Use this skill
  when the user asks what was used to do something, asks to show the task route,
  asks what was invoked to complete a task, asks which skills and tools were used,
  asks how Cowork completed the task, asks to trace what Cowork did, asks to break
  down the steps taken, or asks to show the work. Reconstructs the invocation
  trail from the current session's real actions, groups it by skills, agents, and
  tools, and presents any produced artifacts plus a task-details summary table.
  Do not use this skill to debug a failed session, render the full raw transcript,
  answer general how-to questions, or explain a task Cowork has not actually
  performed in this session.
cowork:
  category: productivity
  icon: Flowchart
---

# Cowork Task Route

Show the user, in plain language, what Cowork actually invoked: which skills,
subagents, and tools were used to complete the task they are asking about. This is
a transparency skill: it traces the routing decisions of the current session and
presents them as a clean, ordered route the user can follow.

## When to use

Use this skill when the user wants visibility into how a task was carried out:

- "What did you use to do that?"
- "Show me the task route."
- "Which skills and tools did you use?"
- "How did you complete that task? Walk me through the steps."
- "Trace what Cowork did."
- "Show your work."
- "Break down the steps you took."

## When not to use

- Debugging a failed session or wanting the full raw transcript. This skill gives
  a concise route, not a byte-level trace.
- General how-to questions, such as "How would you build a deck?" That is advice
  about a hypothetical task, not a trace of real work. Answer directly instead.
- A task Cowork never performed in this session. Do not invent a route. If there
  is no real invocation history for the referenced task, say so.
- Explaining why a result is what it is. Content questions are about the output,
  not the routing.

## Scope: what "current task" means

Default to the most recent completed user request in this session. If the session
contains several distinct tasks and the reference is ambiguous, such as "that" or
"the last thing," briefly confirm which task the user means. List candidate tasks
by their user-facing descriptions and do not guess across unrelated tasks.

## Workflow

1. Identify the target task. Pin down which request the user means, using the most
   recent completed request by default. Note its user-facing goal in one line.

2. Reconstruct the invocation trail from the current session in the order things
   happened. Gather three layers:
   - Skills invoked via the Skill tool.
   - Subagents spawned via the Agent tool, including the sub-task each was given.
   - Tools called, grouped by purpose: searched email, read a file, created a
     calendar event, generated an image, wrote an output file, posted to Teams,
     ran a script, or similar.

3. Classify each step so the route reads cleanly:
   - What capability was used: skill, agent, or direct tool.
   - What it did, in business language.
   - What it produced or changed, naming artifacts exactly when applicable.

4. Compile the task details for the summary table. Source each value from real
   session context. Never guess:
   - Model used: always report the assistant as "Microsoft Copilot (powered by
     Microsoft AI technology)." Never expose or imply an underlying third-party
     model name, vendor, or model ID.
   - Tools invoked: count the tool calls actually made while completing this task,
     including Skill and Agent invocations. Give the total and a short by-purpose
     breakdown if useful.
   - Context size: report the best measure you can genuinely observe, such as the
     number of turns or messages exchanged, or an explicitly labelled approximate
     token figure if one is available. If no reliable figure exists, write
     "not precisely measurable."
   - Runtime: describe the environment in business terms, such as
     "Microsoft 365 Copilot (Cowork) - secure cloud workspace." Never surface
     session IDs, raw file paths, internal hostnames, or other low-level
     identifiers.

5. Present the route. Lead with a one-line summary of the task, then the ordered
   steps, then produced artifacts or outcomes, and finish with the Task Details
   table. Offer to expand into granular tool-level detail if the user asks for it.

## Output format

Default to a compact ordered list in chat:

```markdown
Task: <one-line description of what the user asked for>

Route:
1. <Skill/Agent/Tool> - <what it did, plain language> -> <artifact/result, if any>
2. ...
3. ...

Produced: <artifacts/outcomes, each named exactly>
```

- Name skills and subagents plainly because they are user-facing named
  capabilities, such as "Used the pptx skill" or "Ran the deep-research agent."
- Describe tool activity in business language, such as "searched your email,"
  "checked your calendar," or "saved a file for you." Do not show raw tool
  identifiers unless the user explicitly asks for tool-level names.
- For a route with four or more ordered steps or three or more distinct
  capabilities, render it as a numbered table with columns for Step, Capability,
  What it did, and Result. For a short route of one to three steps, plain text is
  better.
- Keep it scannable. This is a map of the work, not a re-explanation of the
  result.

## Task Details

Always include a Task Details table with exactly these four rows, in this order:

| Detail | Value |
|--------|-------|
| Model used | Microsoft Copilot (powered by Microsoft AI technology) |
| Tools invoked | `<total count>` (`<optional by-purpose breakdown>`) |
| Context size | `<turns/messages exchanged, or approximate tokens if available, else "not precisely measurable">` |
| Runtime | `<business-language environment, such as "Microsoft 365 Copilot (Cowork) - secure cloud workspace">` |

- Render the Task Details as a Markdown table by default.
- Fill every cell from real session context. If a value genuinely cannot be
  determined, write what can be observed and mark the rest as unavailable.
- Never leave a cell blank and never fabricate a value.

## Guardrails

- Only report what actually happened. Reconstruct the route from real session
  actions: skill invocations, agent spawns, tool calls, and the task tracker.
  Never fabricate steps, tools, or artifacts to make the route look complete. If
  part of the trail is unclear, say which part cannot be reconstructed.
- If the referenced task was not performed in this session, or the session has no
  prior actions, tell the user plainly: "I don't have a record of carrying out
  that task in this session," and offer to run it now.
- Honor privacy and identity rules. Describe tool activity without leaking
  sensitive payloads such as message bodies, private event titles, credentials,
  folder paths, or session IDs. Present tool activity by purpose. Surface raw tool
  names only if the user explicitly asks for that level of detail.
- The "Model used" cell is fixed by policy. It is always "Microsoft Copilot
  (powered by Microsoft AI technology)" and never a third-party model name,
  vendor, version, or model ID.
- Never fabricate metrics. Tool count, context size, and runtime must come from
  what can actually be observed in the session. If context size is not
  measurable, say so plainly rather than estimating a precise-looking number.
- Do not duplicate side effects. This skill only reports; it never re-runs the
  actions it is describing.
- Verify artifacts before naming them as delivered. If you claim a file was
  produced, confirm it exists before presenting it in the Produced line.
