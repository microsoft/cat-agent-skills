# Harness decision criteria

Use this reference as a decision aid, not an evergreen feature contract. The snapshot was checked on 2026-08-04. Recheck any decisive capability, channel, authentication, licensing, or availability claim before commitment.

## Contents

- Harness definition and current option map
- Hard gates and fit evidence
- Build-shape decision and architecture archetypes
- Channels and one-versus-multiple harnesses
- Security and component placement
- Migration and lifecycle
- Microsoft ecosystem alternatives

## What a harness controls

Microsoft defines a harness as the runtime layer between the model and the agent or workflow. It governs how model calls, tools, knowledge, and other components are orchestrated. A harness is not a publication channel, model selection, or complete solution architecture.

## Current option map

| Option | Strongest fit | Runtime character | Audience and surface | Important cautions |
|---|---|---|---|---|
| GitHub Copilot harness | Reasoning-heavy, multistep work; adaptive recovery; files and artifacts; skills; memory; sandbox execution; connected agents | Plans and adapts toward an outcome, using tools and context as needed | Microsoft describes internal and external use, subject to currently available publication channels | Uses Copilot Credits during AI-assisted creation and runtime; channel availability is narrower and changing; an agent cannot be transferred in place between this and the standard harness; verify preview maturity |
| Standard harness | Structured conversations, explicit topics, controlled paths, standard-harness agent flows, broad publication needs | Follows authored orchestration, topics, triggers, prompts, agent flows, and paths | Internal or external across supported channels | Do not force a deterministic process into generative orchestration merely because it sounds more advanced |
| Copilot chat harness | Internal, knowledge-first help inside Microsoft 365 Copilot Chat, with focused enterprise grounding and optional tools | Extends the Microsoft 365 Copilot experience | Internal Microsoft 365 users only | Not an external or general-purpose channel choice; distinguish a custom agent from an agent for Microsoft 365 Copilot because deployment and analytics behavior differ |

## Hard-gate sequence

Evaluate these before preference signals.

| Gate | Question | Consequence |
|---|---|---|
| User boundary | Must unauthenticated people, customers, partners, or citizens use it? | Exclude Copilot chat. Verify the exact external channel and authentication combination for remaining options. |
| Mandatory surface | Is a named channel, contact center, native application, or protocol non-negotiable? | Verify current support. Exclude an option that lacks it unless a documented custom integration is acceptable. |
| Product maturity | Does policy, regulation, support, or production criticality prohibit public-preview capabilities? | Verify the exact experience and feature status. Exclude a public-preview dependency when the constraint applies; do not generalize one component's status to the whole harness. |
| Runtime control | Must every step, approval, or response path be explicit and repeatable? | Favor standard, Power Automate, or Logic Apps. Adaptive reasoning may be a risk rather than a benefit. |
| Adaptive execution | Must the agent inspect intermediate results, recover, retry, manipulate files, or choose tools across a multistep outcome? | Favor the GitHub Copilot harness if the channel and governance gates pass. |
| Microsoft 365-only experience | Is the goal focused internal assistance in Microsoft 365 Copilot Chat? | Consider Copilot chat first; keep standard as a runner-up when authored conversations or broader channels matter. |
| Infrastructure boundary | Is there a mandatory custom model, private runtime, custom network topology, code-first host, or infrastructure control outside Copilot Studio's supported model? | Consider a Microsoft-managed runtime in Foundry Agent Service or a customer-hosted Microsoft Agent Framework runtime on Azure. Add Microsoft 365 Agents SDK only when its application or channel layer is useful. |
| Observability | Is Copilot Studio Analytics, a bespoke trace schema, or customer-controlled telemetry mandatory? | Verify the exact agent type and runtime. Agents for Microsoft 365 Copilot do not populate Copilot Studio Analytics in the dated documentation; customer-owned tracing may require a code-first route. |
| Nonconversational process | Is this primarily a scheduled, event-driven, deterministic integration with no material need for agentic reasoning or dialogue? | Prefer Power Automate or Azure Logic Apps; add an agent only if a human-facing reasoning layer adds value. |
| App-centric experience | Is the main requirement a form, portal, case workspace, or transactional application? | Lead with Power Apps, Power Pages, or Dynamics 365; use an agent as an embedded assistant if useful. |

An unknown on a mandatory gate is not a pass. Mark it as a decision-critical validation action.

A separate gateway, adapter, second endpoint, or other architectural workaround is not evidence that the underlying platform supports a mandatory capability. Keep the gate failed unless the user explicitly accepts the workaround's extra topology, risk, cost, support boundary, and operational burden, then prove the end-to-end requirement in a pilot.

## Fit evidence after gates

### Evidence for the GitHub Copilot harness

- The desired outcome cannot be reduced to a stable scripted path.
- Intermediate observations change the next action.
- Recovery, retries, and replanning are part of normal success.
- The work creates, edits, or analyzes Word, Excel, PowerPoint, PDF, or other files.
- A repeatable procedure belongs in a skill, while tools provide governed external actions.
- Temporary sandbox computation or code execution materially improves accuracy.
- Memory or specialist connected agents are required for continuity or domain separation.

### Evidence for the standard harness

- The conversation has known intents, topics, decision paths, or escalation rules.
- Determinism, testability, and authored control outweigh open-ended planning.
- The experience needs a standard-only publication channel or contact-center integration.
- The workload contains many simple, repeatable interactions where adaptive planning adds cost without value.
- Existing topics, variables, prompts, flows, and channel investments remain fit for purpose.

### Evidence for the Copilot chat harness

- Users are employees working in Microsoft 365 Copilot Chat.
- The primary task is finding, summarizing, or acting on enterprise knowledge in the flow of work.
- The solution does not need external users or a separate customer-facing surface.
- Microsoft 365 licensing and the expected internal consumption model are understood.

Do not select from signals alone. Record conflicting evidence and explain why it is not decisive.

## Choose the build shape after the harness

Harness and solution shape are separate decisions. Select the harness first, then name the smallest shape that fits:

| Work shape | Build as | Why |
|---|---|---|
| Conversation or adaptive outcome where context changes the next action | Agent | Keep planning and dialogue in the adaptive runtime. |
| Schedule, event, API call, or repeatable process with an explicit path | Workflow | Make sequence, branching, retries, and operations inspectable. |
| Deterministic process with one bounded judgment step | Workflow with an agent node | Keep the process explicit while delegating only the reasoning step. |
| Adaptive conversation or case experience with an exact subprocess | Agent calling a workflow | Let the agent decide when to invoke a governed write, approval, or integration path. |

Do not use “flow” as an undifferentiated label:

| Term | Meaning |
|---|---|
| Standard-harness agent flow | An automation built in the classic Copilot Studio flow experience and metered under agent-flow rules. |
| GitHub-harness workflow | A workflow built in the new Copilot Studio experience; check current preview status and billing. |
| Power Automate cloud flow | A Power Automate automation governed and licensed through Power Automate, even when an agent calls it. |

As checked on 2026-08-04, the new agent experience was a **production-ready preview**. The new workflows experience was a **public preview**, and Microsoft stated that public-preview features were not meant for production use and could have restricted functionality. These statuses can change independently. Recheck them and the organization's preview policy before recommending a production dependency.

### Compact architecture archetypes

- **Event triage and governed update:** a workflow collects and normalizes inputs, an agent node returns a bounded structured judgment, and later deterministic steps route, approve, and write the result.
- **Conversational case assistant:** an agent understands the user's goal and calls a workflow for an exact approval, system update, or multi-system transaction.
- **Document outcome:** a GitHub-harness agent reasons over files and creates the artifact, while governed tools or workflows handle authoritative retrieval, storage, notification, and approval.

## Channel snapshot

As checked on 2026-08-04, Microsoft listed these GitHub Copilot harness publication options: Microsoft 365 Copilot, Teams, demo website, and web app iframe. The same page listed several channels as not currently available, including SharePoint, Facebook, WhatsApp, Slack, Telegram, native app, MCP client, multiple contact-center integrations, Twilio, LINE, GroupMe, Direct Line Speech, and email.

The standard harness documentation lists a broader set that includes websites, Teams and Microsoft 365, SharePoint, WhatsApp, mobile or custom applications, Facebook, Azure Bot Service channels, Direct Line Speech, and email, subject to configuration and regional or feature availability.

Clarify whether “Teams” means the Microsoft 365 Copilot agent experience inside Teams or a standalone Teams-channel agent. The labels sound interchangeable but can imply different authoring, publication, analytics, and licensing behavior.

This snapshot will age. Check the publication pages in `official-sources.md` whenever the channel affects the recommendation.

## One harness versus multiple

Internal and external users do not automatically require different harnesses. A standard-harness agent can serve both when its supported channels, behavior, data, identity, governance, ownership, and lifecycle fit both audiences. A GitHub Copilot harness agent can also support internal and external use within its current publication and authentication constraints.

For standard agents, Microsoft documents authentication under the individual agent's Security settings: one authentication option is configured for the agent. Manual authentication can defer sign-in until a restricted topic is reached, and Teams users are authenticated, but this does not make a topic or branch an authorization boundary. A public plus privileged design might therefore use one standard harness type across two separately secured agents rather than two harness types. Verify current tenant behavior before finalizing the topology.

Split the architecture only when a real boundary exists. Examples:

- Employees need an adaptive, file-producing process while customers need a tightly scripted public FAQ and escalation path.
- The external channel is unavailable for the otherwise preferred harness.
- Internal and external experiences require different tenants, data classifications, identity models, owners, service levels, or release cadences.
- A high-volume simple public workload would subsidize expensive reasoning that only the internal workload needs.

When splitting, define ownership, shared data and API contracts, handoff behavior, conversation continuity, evaluation, telemetry, and failure isolation. Avoid sharing privileged context across the boundary.

## Security boundary rule

Instructions, topics, channel detection, model routing, and separate agent shells are not sufficient controls for privileged data or actions. Enforce authorization at the knowledge source, connector, connection identity, flow or tool, and downstream API. Require downstream systems to reject unauthorized or unapproved writes even if the agent calls them.

## Component placement for the GitHub Copilot harness

Put behavior in the smallest reliable, inspectable component:

| Need | Preferred component |
|---|---|
| Always-applicable behavior or guardrail | Instructions |
| Searchable source facts | Knowledge |
| Governed action in an external system | Tool, connector, REST API, or MCP server |
| Repeatable situational procedure, potentially with local code and assets | Skill |
| Persistent user or business context | Memory, subject to governance |
| Specialist domain with separate instructions, tools, or lifecycle | Connected agent |

The sandbox is temporary and has no direct network egress. Use configured knowledge and tools for external access. Return or save important files; do not assume sandbox files persist between conversations.

## Migration and lifecycle cautions

- Microsoft states that harness selection occurs at agent creation and an agent cannot be transferred in place between the GitHub Copilot and standard harnesses. Treat a change as redesign and migration, not a toggle.
- Diagnose the gap before rebuilding:
  - **Polish gap:** instructions, knowledge quality, topic design, response style, or test coverage needs improvement. Keep the standard harness when its control model and channels still fit.
  - **Capability gap:** the outcome genuinely requires adaptive recovery, file manipulation, sandbox execution, reusable skills, persistent memory, connected agents, or another GitHub-harness capability. Redesign and rebuild rather than imitating it with increasingly fragile topics.
  - **Boundary gap:** channel, identity, tenant, support, or governance is the problem. A harness migration might not solve it; split the agent or use another Microsoft route only when the boundary requires it.
- Redesign old topics and variables around outcomes and current components. Do not mechanically port every artifact into instructions.
- Microsoft's experimental `copilot-studio-plugin` can help create, edit, validate, and draft migrations from classic agents to the new experience. Treat generated YAML as an untrusted first draft: the project is not an officially supported product, is not meant for production use, and requires review and validation in a nonproduction environment.
- Validate with representative happy paths, exceptions, adversarial inputs, tool failures, and cost scenarios.
- Confirm sharing, edit collaboration, analytics, ALM, regional availability, and support requirements against current documentation before production.

## Microsoft ecosystem alternatives

| Primary need | Route to assess | Why it may fit |
|---|---|---|
| Deterministic event, schedule, integration, or approval process | Power Automate or Azure Logic Apps | Durable workflow semantics and explicit control without paying for unnecessary conversational reasoning |
| Forms, portals, cases, transactional UI | Power Apps, Power Pages, or Dynamics 365 | Application experience is primary; an agent can remain an embedded assistant |
| Managed custom agent runtime, model or framework choice, enterprise observability and identity | Microsoft Foundry Agent Service | Greater code and runtime control while remaining on a Microsoft managed platform |
| Code-first multi-channel bot or agent, including Microsoft 365 and Teams | Microsoft 365 Agents SDK | Application and channel SDK with control over the AI stack; it still needs a hosting runtime |
| Customer-owned runtime, identity, network, trace schema, and deployment | Microsoft Agent Framework hosted on Azure compute such as AKS, Container Apps, or App Service | Maximum control with greater engineering, security, scaling, and support responsibility |
| Complex combination | Foundry Agent Service or Agent Framework + Agents SDK + Logic Apps or Power Platform | Separate runtime, channel adapter, deterministic workflow, and business UI concerns |

Do not escalate to a more custom stack without naming the Copilot Studio constraint it resolves and the engineering or operating cost it introduces.
