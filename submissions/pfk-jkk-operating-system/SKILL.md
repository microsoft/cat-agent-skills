---
name: pfk-jkk-operating-system
description: "Use this skill whenever the user wants to turn project meeting notes, email, documents, tickets, photos, or retrospectives into a complete PFK (Process Flow Kaizen) and JKK (Jikotei Kanketsu) workflow; clarify missing workflow facts; create or update flow nodes, Mermaid diagrams, node cards, quality gates, Definition of Ready, Definition of Done, or continuous-improvement actions."
---

# PFK/JKK Operating System

Create a shared operating flow for products and services. Apply PFK to make one end-to-end flow visible and continuously improve it. Apply JKK to ensure each owner completes work to a clear good-product standard before handoff.

## Terminology and Origin

When users ask what PFK or JKK means, use [the PFK/JKK foundations reference](./references/pfk-jkk-foundations.md). Explain JKK as a quality-at-the-source practice associated with the Toyota Production System (TPS). Explain PFK as this skill's practical combination of visible end-to-end process flow and Kaizen; do not claim that PFK is an official, fixed Toyota program name.

Connect the method to its usable TPS and Lean patterns: Jidoka for surfacing and resolving quality problems, Just-in-Time and pull for managing flow, visual management for exposing work and blockers, standardized work for repeatable execution, and Kaizen for continuous improvement. Explain that these patterns apply to project management, product delivery, IT operations, customer support, and service delivery whenever work crosses handoffs.

## Core Principles

- All material work belongs on one visible flow.
- Each node produces an accepted input for the next node; do not pass preventable defects downstream.
- Work is complete only when observable pass criteria are met.
- Pair standards with practical toolboxes: templates, examples, checklists, systems, and automation.
- Turn defects, delays, and exceptions into improvements to the earliest preventative node.

## Language and Visual Reference Rules

Keep this skill, its templates, scripts, file names, and comments in English. Write user-facing questions, reports, flow labels, node cards, and exported diagram labels in the language used in the user's latest request, unless another language is explicitly requested. Keep node IDs and Mermaid identifiers language-neutral and stable, such as `N1`, `G1`, and `A1`.

Treat supplied images as process and visual evidence. Do not copy, bundle, or store user-supplied images as examples. Apply [the visual reference principles](./assets/visual-reference-principles.md) and generate a new Mermaid-derived SVG or PNG only when the user requests a portable image or saved flow package.

## Host-Neutral Operation

The canonical output is Mermaid source plus node cards and a flow register. It must work without shell access, code execution, file-system access, or a diagram renderer.

When the host can create files, save the requested flow package. When the host can render Mermaid directly, provide the Mermaid source and use the host's renderer. Use [the optional Python renderer](./scripts/render_mermaid.py) only after confirming that Python 3 and `npx` are available and the host permits command execution and package download. Do not require PowerShell, a local browser, Node.js, or npm in Copilot Studio. In a GitHub Copilot coding harness, verify the available runtime and project instructions before running the optional renderer.

## Evidence Intake and Clarification

Accept meeting notes, email threads, documents, tickets, screenshots, photos, spreadsheets, retrospectives, and existing process diagrams. Treat the material as evidence, not as an approved standard.

Before proposing a flow, build an evidence table:

| Claim | Source | Type | Confidence | Effect on flow |
| --- | --- | --- | --- | --- |
| QA accepts release evidence | Meeting notes, 2026-08-31 | Explicit | High | Add release gate |

Classify every claim as **Explicit**, **Observed**, **Inferred**, or **Conflicting**. Label inferred claims as assumptions. Do not make conflicting claims part of the standard until resolved.

Ask concise, numbered questions only when missing information changes the flow boundary, node sequence, owner, input, deliverable, pass criteria, exception path, or toolchain behavior. Ask no more than five related questions at once. If the user requests a draft first, create a clearly labeled draft flow with assumptions and open decisions; do not present assumptions as confirmed facts.

## Create a New Flow

1. Define the trigger, customer or business outcome, scope, flow owner, and excluded work. Use outcome-based boundaries, not departmental labels.
2. Reconstruct the current flow from evidence. Capture actions, handoffs, approvals, wait states, rework, and exceptions. Add every material action to a node or explicitly remove it from the required process.
3. Create a whole-process map from [the Mermaid template](./assets/whole-process-flow-template.mmd). Read left to right from trigger to outcome. Use solid arrows for normal handoffs, labeled decision nodes for conditional routes, dashed arrows for feedback or rework, and visible quality gates before accepted handoffs. Add an Andon escalation node for blockers outside a node's authority or time expectation.
4. Create a JKK node card for every meaningful outcome using [the node-card template](./assets/node-card-template.md). Each card needs a stable ID, accountable role, input, deliverable, key actions, time expectation, good-product standard, verification owner, toolbox, failed-check response, and allowed exception path.
5. Turn every key action into one or more executable work items. Each work item must name the action, accountable person or role, required knowledge, expected artifact, completion evidence, and target time. Decompose only until a capable new team member can execute the item without relying on unstated tribal knowledge.
6. Build a node-linked knowledge base from [the knowledge index template](./assets/knowledge-index-template.md). Record each reusable template, example, runbook, policy, decision record, training item, and automation with one canonical link, owner, version or review date, and the node IDs that use it. Link to existing material instead of copying it into every node card.
7. Use [the flow package template](./assets/flow-package-template.md) to track the boundary, evidence, open decisions, artifacts, knowledge index, and flow changes. Never renumber an existing node only because the flow changes.
8. When saving is requested and the host can write files, keep editable materials together in `flows/<flow-name>/`: `flow.md`, Mermaid source, `knowledge-index.md`, `nodes/N<id>-<short-name>.md`, and optional rendered SVG or PNG. Mermaid source and node cards are the source of truth; generated images are derived views.
9. Map approved node contracts to the working toolchain. Use work-item states, checklists, linked artifacts, automated CI or approval gates, and visible, time-bound exceptions. Do not add a workflow state merely to describe a meeting or person.

## Quality at the Source

For every node, determine:

- Which defect the node can introduce.
- Which inexpensive check detects it before handoff.
- Who resolves a failed check.
- How a failure returns to the corrective node.

The default rule is no handoff until the good-product standard passes. An exception must name a risk owner, expiry date, and follow-up work item.

## Update an Existing Flow or Node

1. Identify the target flow and stable node ID. Ask for clarification only if either is ambiguous.
2. Restate the requested change and identify affected input, deliverable, owner, pass criteria, time expectation, toolbox, gates, and connected nodes.
3. Apply the change when the facts are sufficient. Otherwise ask only the decision-changing questions.
4. Update the target node card and append a dated change-log entry with the source or user decision.
5. Update Mermaid whenever the node label, sequence, handoff, decision, quality gate, exception route, or rework path changes.
6. Recheck connected nodes. Update mismatched entry criteria or report the unresolved conflict.
7. Output exactly the requested artifact: one node card, the full Mermaid flow, a rendered image path, or a complete flow package summary. Include a concise impact summary.

Do not silently modify unrelated nodes. Preserve the prior version or show the exact before-and-after difference.

## Kaizen Review

Pilot one or two repeatable flows for two to four delivery cycles. Review lead time, waiting time, first-pass rate, rework count, escaped defects, blocker age, exception count, and work occurring outside the shared flow. For each material issue, change the earliest preventative node and record the hypothesis, owner, expected measure, and review date.

## Standardize and Onboard

After two to four cycles, promote the flow from pilot to standard work only when the team has resolved material open decisions, confirmed the node contracts against delivery evidence, and updated the relevant templates, runbooks, examples, or automation.

For every person, provide a node-centric execution view containing only the nodes they own or contribute to. It must show their work items in order, required inputs, knowledge links, completion evidence, escalation route, and receiving role. A new team member is ready when they can use this view to complete a representative assigned node, find the required knowledge without private guidance, and pass the node's good-product standard. Record onboarding gaps as Kaizen items rather than relying on informal coaching.

## Completion Check

The flow is ready to pilot only when every material activity and handoff is visible; every node has an owner, input, deliverable, executable work items, time expectation, good-product standard, and toolbox; each work item identifies its knowledge and completion evidence; pass criteria are independently checkable; failed checks block or explicitly govern handoff; inferred and conflicting rules are resolved or visibly open; and a recurring improvement review is scheduled.