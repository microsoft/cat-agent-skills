# Implementation checks that can change the decision

Use these checks before treating a harness recommendation as production-ready. The product snapshot was checked on 2026-08-04; verify current behavior in the target tenant and region.

## Surface and channel

- Name the exact user surface, not only the brand: Microsoft 365 Copilot Chat, an agent inside Teams, a standalone Teams-channel bot, SharePoint, a public website, web app iframe, custom or native app, voice, contact center, or system trigger.
- Verify that the selected harness currently publishes to every mandatory surface.
- Test authentication, attachments, adaptive cards, citations, file download, handoff, conversation continuity, accessibility, localization, and telemetry in each surface. Authoring preview is not a substitute for channel testing.
- Record whether a future channel is a preference or a hard constraint.

## Product maturity and support

- Verify maturity at the experience and feature level. Do not infer that every GitHub-harness capability has the same support status.
- As checked on 2026-08-04, the new agent experience was a production-ready preview, while the new workflows experience was a public preview that Microsoft said was not meant for production use and could have restricted functionality.
- Check the customer's preview policy, contractual support needs, regional availability, supplemental terms, release roadmap, rollback route, and whether a generally available alternative covers the requirement.
- Treat a prohibited public-preview dependency as a failed production gate. A prototype can still validate the design if the user explicitly accepts that scope and no production claim is made.

## Authentication and authorization

Microsoft documents standard-agent authentication under the individual agent's Security settings. One authentication option is configured for the agent: no authentication, authenticate with Microsoft, or authenticate manually. With manual authentication, required sign-in can be delayed until a topic needs it; Teams users are authenticated.

This flexibility does not make channel detection, a topic, a variable, an instruction, or a separate agent an authorization boundary. For every privileged read or write:

1. authenticate the caller;
2. authorize at the source, connector, tool, or API;
3. use least-privilege user or service identity;
4. validate tenant and resource scope;
5. log the authorization decision without leaking sensitive data;
6. reject the operation downstream when authorization is absent.

For anonymous plus privileged use, compare one manually authenticated agent with two agents using the same harness. Prefer separation when it materially reduces disclosure, connection, ownership, or lifecycle risk, but keep authorization controls in the underlying systems either way.

Keep privileged knowledge outside anonymous grounding context until identity and authorization are established. Verify that retrieval executes with the intended user's permissions and that snippets, citations, caches, conversation state, error messages, and fallback answers cannot reveal restricted content.

## Microsoft 365 Copilot agent type

Clarify whether the design is a custom agent published to Teams and Microsoft 365 or an agent for Microsoft 365 Copilot, also called a declarative agent. Current documentation says agents for Microsoft 365 Copilot do not collect data for the Copilot Studio Analytics page. Verify distribution, analytics, knowledge, tool, and licensing behavior for the exact type.

Keep the terms separate:

| Term | Meaning for this assessment |
|---|---|
| Harness | Runtime and orchestration behavior; not the channel or catalog artifact |
| Copilot chat harness | Runtime for extending Microsoft 365 Copilot Chat with internal knowledge |
| Custom agent | An agent built from scratch and published to supported surfaces; do not infer its harness or analytics behavior from the label alone |
| Agent for Microsoft 365 Copilot / declarative agent | An agent specifically extending Microsoft 365 Copilot; current documentation carries the Copilot Studio Analytics caveat |

Name the required observability surface: Copilot Studio Analytics, GitHub Copilot harness Monitor, Power Platform admin consumption reporting, Microsoft 365 adoption reporting, or customer-owned traces. Validate the exact metrics, filters, latency, retention, export, and access controls—not only that a page receives some data.

## Tools, flows, and approvals

- Name the automation type precisely:
  - a **standard-harness agent flow** is built in the classic Copilot Studio flow experience and uses agent-flow licensing and metering;
  - a **GitHub-harness workflow** is built in the new Copilot Studio workflow experience and has its own current maturity and billing rules;
  - a **Power Automate cloud flow** is licensed and governed through Power Automate, even when an agent invokes it.
- Confirm that an existing flow can be exposed with the required agent-callable trigger and input/output contract. Do not assume every Power Automate cloud flow can be reused unchanged.
- Distinguish a Copilot Studio agent flow from a Power Automate cloud flow. They have different meters, enforcement, lifecycle, and licensing.
- Separate read and write tools. Use narrow schemas and validate tool output before it enters model context.
- For financial, legal, account, record-changing, or otherwise irreversible actions, enforce approval in a durable workflow or the downstream write API. A conversational confirmation or instruction is useful user experience, not the sole control.
- Bind approval to the exact payload, approver, expiry, and operation. Reject changed, expired, duplicated, or replayed writes and return a transaction reference.
- Define timeouts, retries, idempotency, compensation, partial completion, cancellation, and human escalation.

## Files and sandbox

When the design reads or produces files, verify:

- channel-specific upload and download support, file types, sizes, and counts;
- malware scanning and content-safety handling;
- data classification, residency, encryption, and retention;
- temporary sandbox lifecycle and the absence of direct network egress;
- governed persistent storage and access permissions for outputs;
- deletion, legal hold, audit, and failed-run cleanup.

Use reviewed skill code for stable calculations and document generation. Save or return important outputs because sandbox files do not persist across conversations.

## Cost telemetry sanity checks

- A question, conversation turn, answer, activity-map action, tool call, agent-flow action, Power Automate action, and end-to-end task are different units.
- One interaction can use several billable feature types. Conversely, activity counts from different reports can overlap. Reconcile definitions before summing.
- Challenge a “light” GitHub Copilot harness classification when the task uses many sources, structured reasoning, or two or more artifacts.
- Treat GitHub Copilot harness task ranges as overall planning ranges influenced by model, context, knowledge, tools, MCP, runtime, and artifacts. Do not automatically add standard-harness feature rates.
- Subordinate committed-capacity comparisons until observed workload data is stable enough to support them.
- Size an annual Copilot Credit P3 commitment from annualized, observed demand rather than multiplying a speculative peak month. Account for expiry, upfront commitment, overage treatment, and existing agreement discounts.

## Microsoft escape-route control test

Separate three roles:

- **Managed runtime:** Microsoft Foundry Agent Service can reduce infrastructure work while imposing supported region, identity, session, network, model, telemetry, and deployment behavior that must be accepted.
- **Customer-hosted runtime:** Microsoft Agent Framework on Azure compute provides greater control over model endpoints, networking, workload identity, tracing, scaling, and release pipelines, with greater engineering and operational responsibility.
- **Application and channel SDK:** Microsoft 365 Agents SDK connects code-first agents to supported channels and experiences; it is not the hosting platform by itself.

Ask which controls are mandatory: customer-owned runtime, custom model endpoint, private ingress or egress, chosen Azure region, bespoke workload identity, custom trace schema, session persistence, traffic splitting, release pipeline, availability, disaster recovery, and public-client ingress.

If a managed platform lacks a mandatory capability, keep that hard gate failed even when an external workaround seems possible. Present the workaround as a separate architecture option and accept it only after the user explicitly agrees to its extra components, failure modes, cost, ownership, and support implications and the pilot validates the complete path.

For a non-Copilot Studio recommendation, replace Copilot Credit arithmetic with an Azure TCO plan covering model inference or GPU compute, agent compute, gateway and WAF, private networking, state and queues, storage, telemetry ingestion and retention, CI/CD, backup and disaster recovery, security, evaluation, and operations. Do not invent a total without volume, concurrency, token or compute profile, latency, and availability targets.
