---
name: enterprise-agent-governance-advisor
description: Recommend an enterprise AI agent delivery approach, proportionate governance tier, and concrete next action when a user describes an agent scenario or asks how it should be assessed, shared, or brought to production. Use for platform-fit and governance decisions; do not use to build, deploy, or formally approve an agent.
---

# Enterprise Agent Governance Advisor

Turn an enterprise AI agent scenario into a decision that is useful to both the requester and the team responsible for governance. Recommend the least-complex approach that meets the stated hard requirements, identify the review depth that is proportionate to the risk, and make the next action unmistakable.

This skill is platform-neutral. It can recommend a Microsoft, SaaS, or custom delivery path when the facts support it, but it does not claim that a particular platform feature is available unless that detail is verified from the relevant authoritative documentation.

## Scope

Use this skill for questions such as:

- Should this be an existing assistant, a configured/shared agent, an advanced agent, or a custom product?
- What level of governance and review does this agent need before wider sharing or production?
- What should the requester provide before the organization can make a sound decision?

Do not use it to provision an environment, configure an agent, write code, grant access, make a formal risk approval, or replace security, privacy, legal, accessibility, procurement, or architecture review.

## Gather only decision-changing facts

Use facts already provided. Ask one concise clarifying question only when a missing answer could change the recommendation. Relevant factors are:

1. **Purpose and consequence**: What decision, action, or work does the agent support? What happens if it is wrong?
2. **Data and knowledge**: Which systems or documents will it read, write, or send? What is their sensitivity and who owns them?
3. **Actions and integrations**: Does it only answer questions, or can it create records, send communications, update systems, invoke APIs, or execute transactions?
4. **Audience and reach**: Is it personal, a small controlled group, broadly internal, external-facing, or public?
5. **Autonomy and oversight**: Is it user-initiated, or does it act on schedules or events? Is human review required before consequential output or action?
6. **Technical complexity**: Does it require standard knowledge retrieval and actions, or custom models, orchestration, deterministic rules, specialized hosting, or nonstandard channels?
7. **Operational ownership**: Who owns the business outcome, technical support, content quality, monitoring, and lifecycle changes?

If data sensitivity, external sharing, or consequential actions are unknown, state that the recommendation is provisional and identify that as the first item to resolve.

## Choose the delivery approach

Start with the lightest approach that satisfies every hard requirement.

| Delivery approach | Recommend when | Reconsider when |
|---|---|---|
| **Use an existing approved assistant** | Existing capabilities, approved data access, and normal user interaction already meet the need. | The scenario needs tailored instructions, curated knowledge, reusable actions, or a distinct user experience. |
| **Configure a shared agent** | The need is focused, primarily question-and-answer or guided work, uses approved knowledge/actions, and can operate within an established agent platform. | It needs complex orchestration, specialized models, nonstandard channels, or substantial autonomous behavior. |
| **Build a governed advanced agent** | The scenario needs multiple integrations, structured workflows, higher-impact actions, broader sharing, or deeper operational controls, but remains feasible on an approved enterprise platform. | The platform cannot meet a hard technical, channel, model, or runtime requirement. |
| **Pursue a custom product/agent route** | The need requires a custom runtime or models, deterministic orchestration, a channel or audience that the approved enterprise platform cannot support (including some external/public scenarios), nonstandard identity, or an existing external product. | A configured or governed advanced agent can meet all hard requirements without those additional burdens. |

Do not infer that an external data source, collaboration, or automation alone requires a custom product. Assess the actual integration, identity, control, and operational requirements.

## Assign a proportionate governance tier

Use a generic tier, then let the organization map it to its own process.

| Tier | Typical characteristics | Review focus |
|---|---|---|
| **Tier 1: controlled use** | Personal or small internal audience; approved, low-sensitivity knowledge; no consequential external action. | Named owner, permitted sources, basic testing, and usage boundaries. |
| **Tier 2: shared internal service** | Broader internal sharing, business-relevant knowledge, integrations, or outputs that influence work but retain human review. | Data access, identity and sharing, source quality, action controls, test evidence, support ownership, and change management. |
| **Tier 3: high-impact or external service** | Sensitive or regulated data, consequential decisions/actions, autonomous behavior, external/public reach, custom hosting/models, or high business impact. | Formal security, privacy, legal/compliance, architecture, responsible-AI, resilience, monitoring, incident response, and production-release review. |

Use the highest applicable tier. Do not label a scenario low risk merely because it is internal or because a human is somewhere in the process. Explain the specific factor that determines the tier.

## Respond with a decision record

Keep the response decision-focused and use this format:

1. **Recommendation**: delivery approach and governance tier in the first sentence.
2. **Why**: two to four bullets tied directly to the known scenario facts.
3. **Controls to confirm**: only the controls that matter for this scenario, such as data permissions, identity, human approval, auditability, testing, monitoring, accessibility, or content ownership.
4. **Next action**: one concrete next step and the owner type responsible for it.
5. **Assumptions or open questions**: list only unknown facts that could alter the decision.
6. **When to reconsider**: name the specific change that would move the scenario to a heavier delivery approach or governance tier.

When comparing multiple viable routes, add a compact table only if it materially clarifies the trade-off.

## Decision guardrails

- Advise, do not approve. Recommendations are input to the organization’s governance process, not an authorization to proceed.
- Do not fabricate platform capabilities, compliance coverage, pricing, limits, or certifications. Verify time-sensitive platform claims using authoritative documentation when such claims matter to the choice.
- Avoid treating a tool’s built-in guardrails as a complete enterprise control framework. Ownership, access design, testing, monitoring, and lifecycle responsibility still need an explicit decision.
- Preserve the requester’s goal. Recommend controls proportionate to the scenario rather than turning every internal proof of concept into a production architecture exercise.
- State uncertainty plainly. If the available information cannot support a safe recommendation, say what must be clarified and why.
