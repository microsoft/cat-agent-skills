# Graceful Tool Failure Handling

A general agent-quality skill for the moment a connector, API call, or file
operation doesn't work. The common failure mode isn't the error itself, it's
what agents do next: continue as if the call had succeeded, quietly drop the
step, or invent a plausible-looking result to fill the gap. This skill makes
the honest response the default: say what was attempted, what happened
instead, and what to do about it.

## Where this pattern already shows up in this gallery

Several skills already build this discipline in for their own domain:
[`it-support-ticket-agent`](../it-support-ticket-agent) never invents a
ticket number a connector didn't return, and
[`company-memory-builder`](../company-memory-builder) says plainly when no
persistent storage is configured rather than pretending memory will carry
over. This skill generalizes that same honesty to any tool call, for agents
that don't already have it built into their domain-specific instructions.

## How it's different from tool-tracer

[`tool-tracer`](../tool-tracer) produces a debug log of tool/action calls for
a developer to inspect after the fact. This skill is about the in-conversation
response when a call fails right now, what the user sees and what happens
next, not a diagnostic artifact.

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
