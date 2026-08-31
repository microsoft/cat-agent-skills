# PFK/JKK Operating System

Build a shared operating flow for any product or service. This skill turns meeting notes, email, tickets, documents, retrospectives, and visual process material into a maintainable PFK and JKK workflow.

PFK makes the full path of work visible so the team can improve one shared flow. JKK puts quality at the source: every process node has a defined input, deliverable, owner, pass criteria, and response when a check fails.

## Concepts and Origin

The skill is informed by Lean thinking and the Toyota Production System (TPS): make work flow visible, build quality into the work, surface abnormalities, and continuously improve the system.

- **JKK, Jikotei Kanketsu, or self-process completion**: a TPS quality-at-the-source practice. A team completes and verifies its own work against a clear standard before passing an output to the next process. In this skill, JKK becomes a node contract: input, accountable owner, deliverable, good-product criteria, evidence, and a failed-check response.
- **PFK, Process Flow Kaizen**: the flow-improvement practice used by this skill. It combines visible end-to-end process flow with Kaizen, the ongoing improvement of work. PFK is a practical name for applying Lean and TPS ideas to a shared workflow; it should not be presented as an official, fixed Toyota program name.
- **Jidoka, Just-in-Time, visual management, and standardized work**: related TPS ideas. This skill uses them as practical patterns: stop or escalate when a quality condition fails, let downstream demand pull work, expose flow and blockers, and make good execution repeatable with usable standards and toolboxes.

## Where It Applies

PFK/JKK works beyond manufacturing. Use it wherever one role's output becomes another role's input:

- Product discovery, design, development, testing, release, and service operation.
- Project management, including planning, decision gates, risk handoffs, and delivery governance.
- IT operations, incident response, change management, problem management, and post-incident improvement.
- Customer support, onboarding, professional services, fulfillment, and other service-delivery workflows.

The goal is not to impose a factory metaphor or add bureaucracy. The goal is to make ownership, quality standards, flow delays, and improvement opportunities visible enough to manage.

## What It Produces

- An evidence register that separates confirmed facts, observations, assumptions, and conflicts.
- Concise questions for gaps that would change the flow or its quality standard.
- A whole-process Mermaid diagram with normal handoffs, quality gates, rework loops, and blocker escalation.
- A JKK node card for every meaningful process outcome.
- Node-level work items with the required knowledge, expected artifacts, and completion evidence.
- A node-linked knowledge index for templates, examples, runbooks, policies, training, and automation.
- A Kaizen backlog and change record for continuous improvement.

## From Pilot to Standard Work

Run a new flow for two to four delivery cycles before treating it as standard work. Use delivery evidence to improve unclear handoffs, missing acceptance criteria, slow steps, and ineffective toolboxes.

Once the flow is stable, each person can use a node-centric execution view for the nodes they own or contribute to. It shows the ordered work items, required inputs, knowledge links, completion evidence, escalation route, and receiving role. A new team member is ready when they can complete a representative assigned node and meet its good-product standard without relying on private tribal knowledge.

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