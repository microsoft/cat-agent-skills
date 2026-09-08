# Cowork Task Route

Cowork Task Route gives users a clear, ordered explanation of how Cowork completed
a task: which skills, agents, and tools were invoked, what each step did, and what
artifacts or outcomes were produced.

## How to use it

Ask Cowork questions like:

- "Show me the task route."
- "Which skills and tools did you use?"
- "How did you complete that task?"
- "Trace what Cowork did."

The skill responds with a concise route and a Task Details table covering the
model label, tool count, observable context size, and runtime environment.

## Good to know

This skill reports only what actually happened in the current session. It does
not fabricate missing steps, rerun actions, expose sensitive payloads, or provide
a raw debug transcript.
