# PFK/JKK Operating System

Build a shared operating flow for any product or service. This skill turns meeting notes, email, tickets, documents, retrospectives, and visual process material into a maintainable PFK and JKK workflow.

PFK makes the full path of work visible so the team can improve one shared flow. JKK puts quality at the source: every process node has a defined input, deliverable, owner, pass criteria, and response when a check fails.

## What It Produces

- An evidence register that separates confirmed facts, observations, assumptions, and conflicts.
- Concise questions for gaps that would change the flow or its quality standard.
- A whole-process Mermaid diagram with normal handoffs, quality gates, rework loops, and blocker escalation.
- A JKK node card for every meaningful process outcome.
- A Kaizen backlog and change record for continuous improvement.

## Typical Prompts

```text
Use the attached meeting notes, launch retrospective, and support tickets to create the current product-onboarding flow. Ask only the questions required to finalize ownership, handoffs, and quality gates.
```

```text
Update node N4 in the customer-support flow: an escalation now requires a reproducible case and severity assessment. Show the updated node card and the complete Mermaid flow.
```

```text
Create a future-state service-delivery flow from these artifacts. Save the Mermaid source, node cards, open decisions, and a PNG export.
```

## Notes

The skill instructions and templates are in English. User-facing questions, reports, node cards, and diagram labels follow the user's language unless another output language is requested. Supplied images are analyzed as evidence and are not copied into the skill or stored as examples.

Mermaid source is the editable record and the required output. The optional Python helper can render it to SVG or PNG when the host allows command execution and has Python 3, Node.js, `npx`, and network access. Copilot Studio use does not depend on the helper; hosts that cannot execute scripts still receive the complete Mermaid source and flow artifacts.