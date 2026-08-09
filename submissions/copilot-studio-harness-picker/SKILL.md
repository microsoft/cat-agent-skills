---
name: copilot-studio-harness-picker
description: "Assess business, experience, channel, identity, orchestration, governance, maturity, and cost requirements to recommend the right Microsoft Copilot Studio harness: GitHub Copilot, standard, or Copilot chat. Use when asked which harness to choose, what to build something with, agent versus workflow, classic versus new experience, whether to migrate or rebuild an existing agent, multi-channel architecture, licensing or Copilot Credit estimates, or whether a Microsoft platform outside Copilot Studio fits better. Supports Quick and Detailed modes and produces an evidence-labelled Harness Decision Brief."
---

# Copilot Studio Harness Picker

Recommend a harness only after testing hard constraints, runtime fit, channel and identity feasibility, and economics. Keep documented facts separate from assumptions and estimates.

## Start the assessment

1. Identify whether the user wants a conversational interview or has supplied requirements to analyze. Do not re-ask facts already provided.
2. Use **Quick** mode by default. Use **Detailed** mode when requested or when the decision is high-risk, cross-tenant, externally facing, regulated, migration-heavy, or materially affected by volume and licensing.
3. State the selected mode in one sentence and allow the user to switch.
4. Match the explanation to the audience without weakening the analysis. Use plain, scenario-led language for makers. For architects and CoE teams, surface identity, ALM, governance, support, observability, and commercial implications explicitly.
5. Read [references/decision-criteria.md](references/decision-criteria.md) before forming a recommendation.
6. Read [references/interview-and-brief.md](references/interview-and-brief.md) for the chosen interview and output format.
7. Read [references/credits-and-licensing.md](references/credits-and-licensing.md) whenever cost, licensing, capacity, build/test consumption, or M365 entitlement affects the decision.
8. Read [references/implementation-checks.md](references/implementation-checks.md) when channel, authentication, privileged data, approvals, files, preview maturity, observability, or a Microsoft escape route affects the design.
9. Consult [references/official-sources.md](references/official-sources.md), and verify volatile claims against current official Microsoft documentation when web access is available. Record the date checked.

Never ask for passwords, tokens, connection strings, production records, or confidential document contents. Ask for sanitized descriptions, classifications, counts, and constraints.

## Build a requirements ledger

Maintain four evidence classes throughout the assessment:

- **Confirmed requirement**: explicitly supplied by the user or an authoritative project artifact.
- **Documented fact**: supported by a cited Microsoft source, including its checked date.
- **Assumption**: a provisional interpretation that could change the recommendation.
- **Unknown**: missing evidence; mark whether it is decision-critical.

Capture hard constraints separately. Examples include a mandatory channel, external access, data residency, private networking, a fixed identity model, deterministic approval paths, contact-center integration, a custom model, or a maximum operating cost.

## Interview at the right depth

In Quick mode, ask at most six high-leverage questions in one compact batch when possible. Cover the outcome, users and surfaces, work shape, files or autonomous recovery, tools and identity, and volume or hard constraints. If enough evidence already exists, proceed without an interview.

In Detailed mode, ask short rounds so later questions can adapt to earlier answers. Cover business outcome, experience and triggers, runtime behavior, data and actions, identity and governance, lifecycle and operations, and economics. Stop asking when additional detail would not change the decision.

Treat examples as stronger evidence than adjectives. Ask for one representative successful run and one failure or exception path instead of relying only on terms such as “complex” or “autonomous.”

## Decide in this order

### 1. Separate the architecture layers

Do not confuse:

- the **harness**, which is the runtime and orchestration layer;
- the **model**, which performs inference;
- the **channel**, where people or systems reach the agent;
- the **components**, such as instructions, knowledge, tools, skills, memory, connected agents, topics, and flows.

A single harness-backed agent can serve more than one channel when channel support, behavior, identity, governance, and lifecycle needs align.

### 2. Apply hard gates

Eliminate any option that cannot meet a confirmed hard constraint. Important gates include internal versus external users, currently supported publication channels, authentication combinations, required runtime capabilities, and code-first or infrastructure requirements.

Do not count an external architecture workaround as native platform support. A workaround keeps the gate failed until the user explicitly accepts its added components, risk, cost, and operating model and a validation proves it meets the requirement.

Feature and channel availability changes. Never present the dated snapshot in the references as permanent. If a critical claim cannot be verified, make it an explicit validation action and lower confidence.

Clarify ambiguous surface names. “In Teams” can mean an agent in the Microsoft 365 Copilot experience or a standalone Teams-channel agent; the distinction can change the harness, deployment, analytics, and licensing treatment.

### 3. Compare the viable options

Use qualitative evidence rather than a decorative numeric score:

- **GitHub Copilot harness** for adaptive, reasoning-heavy, multistep work that benefits from recovery, files, skills, memory, sandbox execution, or connected agents.
- **Standard harness** for predictable conversations, authored topics and paths, standard-harness agent flows, broad channel needs, or tighter control over deterministic behavior.
- **Copilot chat harness** for internal, Microsoft 365-centered, knowledge-first assistance delivered through Microsoft 365 Copilot Chat.

These are starting signals, not substitutes for hard-gate checks. Explain both supporting and conflicting evidence.

### 4. Choose the build shape after the harness

Do not stop at the harness label. Name how the solution should be built:

- **Agent** when the primary experience is conversational or adaptive and the next step depends on context.
- **Workflow** when a schedule, event, or repeatable process should follow an explicit path.
- **Workflow with an agent node** when the overall process is deterministic but one bounded step needs judgment, knowledge, or tool selection.
- **Agent calling a workflow** when an adaptive front end needs a governed, repeatable subprocess for writes, approvals, or integration.

Treat this as a second decision, not a fourth harness. Distinguish a standard-harness **agent flow**, a GitHub-harness **workflow**, and a **Power Automate cloud flow**; their runtime, maturity, metering, and lifecycle differ. Recheck preview status and the organization's preview policy before recommending a new-experience workflow for production.

For an existing classic or standard agent, diagnose the reason for change. Keep and improve it when the problem is mainly polish, instructions, knowledge, or topic design. Redesign on the GitHub Copilot harness when a confirmed capability gap requires adaptive recovery, file work, sandbox execution, skills, memory, or connected agents. Treat migration tooling as a reviewed first-draft accelerator, never as proof of equivalent behavior.

### 5. Test whether one harness is enough

Prefer one harness across internal and external channels when the same behavior, data boundary, identity model, ownership, release cadence, and support model fit.

Recommend separate agents or harnesses only when at least one material boundary differs:

- runtime behavior or control model;
- currently available channels;
- identity, tenant, data, or compliance boundary;
- ownership, lifecycle, service level, or release cadence;
- economics at materially different workload patterns.

Name the boundary and explain why a single-harness design fails. Do not use “hybrid” as a vague default.

Do not treat topics, instructions, channel branches, or the existence of separate agents as authorization controls. Enforce privileged access in authentication, source permissions, tool authorization, connection identity, and downstream APIs.

### 6. Use a Microsoft escape route when needed

If no Copilot Studio harness is a sound fit, say so directly and recommend a concrete Microsoft ecosystem route. Consider Power Automate or Azure Logic Apps for deterministic event-driven automation; Power Apps, Power Pages, or Dynamics 365 for app-, case-, and form-centric experiences; Microsoft Foundry Agent Service for custom managed agent runtimes; and the Microsoft 365 Agents SDK for code-first, multi-channel agents.

Distinguish a managed Foundry-hosted runtime from a customer-hosted Microsoft Agent Framework runtime on Azure. Treat the Microsoft 365 Agents SDK as an application and channel SDK, not a hosting platform. Match the route to required model, network, region, identity, trace schema, session, deployment, and operating controls.

Keep the recommendation scoped. A Microsoft service used as a tool, workflow, or user interface does not necessarily require abandoning Copilot Studio.

## Estimate Copilot Credits transparently

Estimate only when volumes are known or when clearly labelled scenarios can be useful. Never invent a single workload number.

1. Separate eligible included usage from billable usage before calculating. One user question can create multiple metered activities; do not equate questions, turns, answers, actions, or flow runs without evidence.
2. Show **Documented facts**, **Assumptions**, **Calculations**, and **Exclusions** as distinct sections.
3. Include authoring, preview, evaluation, and production activity for the GitHub Copilot harness.
4. Use low/base/high scenarios when uncertainty is meaningful. Treat Microsoft planning ranges as ranges, not guaranteed prices. Challenge a supplied complexity band when the described sources, reasoning, or artifact count conflicts with Microsoft's band definition.
5. Use `scripts/estimate_credits.py` for arithmetic. It reads the dated rates in `assets/credit-rates-2026-08.json` and reports gross credits before licensing adjustments.
6. Do not silently place an upper bound on an open-ended Microsoft range. If the user supplies a heavy-case upper bound, label it as a planning assumption.
7. Distinguish Copilot Studio **agent flow actions** from **Power Automate cloud flow** actions. The 13-per-100 rate applies to the former; Power Automate cloud flows use Power Automate licensing.
8. Do not stack standard-harness feature rates on top of GitHub Copilot harness task planning ranges unless current Microsoft guidance explicitly requires it. The task ranges already reflect runtime factors such as model, context, knowledge, and tools.
9. List excluded costs such as external systems, Azure resources, premium connectors, telephony, custom model hosting, Microsoft 365 licenses, implementation, and support when applicable.
10. Compare pay-as-you-go, monthly capacity packs, and annual Copilot Credit Pre-Purchase Plan (P3) only on compatible time periods. Treat P3 sizing as a procurement decision after pilot telemetry is stable, not as an automatic recommendation from a wide planning range.

Treat a cost estimate as a planning model. Recommend a metered pilot and a budget alert before production commitment.

## Produce the Harness Decision Brief

Lead with a decisive recommendation, not the interview transcript. Use the Quick or Detailed template in [references/interview-and-brief.md](references/interview-and-brief.md).

Always include:

- recommendation and confidence;
- runner-up or Microsoft alternative;
- decisive evidence and disqualifiers;
- recommended build shape: agent, workflow, workflow with an agent node, or agent calling a workflow;
- harness-versus-channel architecture;
- licensing and credit treatment when material;
- assumptions, unknowns, risks, and validation actions;
- conditions that would change the decision;
- official sources and the date checked.

Set confidence as **High**, **Medium**, or **Low** based on decision-critical evidence and source freshness. Do not derive it from an arbitrary score.

For a “none of these” result, separate confidence that Copilot Studio is excluded from confidence in the proposed Microsoft alternative. The evidence can strongly disqualify every harness while leaving the final hosting topology conditional.

## Run the final quality gate

Before delivering, confirm that:

- every hard constraint is met or visibly unresolved;
- no option is rejected solely because of a preference signal;
- the recommendation distinguishes harness, channel, model, and components;
- the recommended build shape and flow type are named unambiguously;
- product maturity and preview policy are checked when they could block production use;
- a multi-harness design names a real boundary;
- privileged access is enforced below the conversational layer;
- approvals for irreversible actions are enforced by the tool or workflow, not only by instructions;
- file ingress, scanning, temporary processing, persistent storage, retention, and output delivery are addressed when files are in scope;
- documented facts are cited and dated;
- estimates are visibly separated from facts;
- any “none of these” result includes a Microsoft ecosystem route;
- the brief says what evidence would overturn the recommendation.
