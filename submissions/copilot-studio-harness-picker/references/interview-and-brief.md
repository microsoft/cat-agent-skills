# Interview and Harness Decision Brief

Adapt the questions to evidence already supplied. Ask for sanitized examples, not production secrets or records.

## Contents

- Quick assessment
- Detailed assessment
- Audience adaptation and requirements ledger
- Quick Harness Decision Brief
- Detailed Harness Decision Brief
- Confidence rubric

## Quick assessment

Use a single compact batch where possible. Ask no more than six high-leverage questions:

1. **Outcome:** What result must the agent deliver? Give one representative successful run and, if important, one exception.
2. **People and surfaces:** Who uses it—employees, customers, partners, or the public—and through which mandatory channels or applications? Clarify Microsoft 365 Copilot in Teams versus a standalone Teams-channel agent.
3. **Work shape:** What starts the work—a conversation, event, schedule, API, or another agent—and is the path predictable, primarily enterprise knowledge Q&A, or adaptive multistep work whose next step depends on intermediate results?
4. **Agentic capabilities:** Must it recover or retry, create or edit files, run calculations or code, remember context, or delegate to specialists?
5. **Data, actions, and identity:** What systems must it read or change, how should users authenticate, and where are approvals or human handoffs required? Distinguish a Copilot Studio agent flow from a Power Automate cloud flow.
6. **Scale and constraints:** What are expected monthly users, runs, turns, files, or tool actions? Note licensing, budget, region, compliance, deadline, migration, and non-negotiable constraints.

If an answer is unknown, record it. Do not pressure the user into false precision.

## Detailed assessment

Ask in short adaptive rounds. Skip questions that cannot change the decision.

### Round 1: Business and outcome

- What business outcome and measurable success criteria matter?
- What initiates the work: user conversation, event, schedule, API, or another agent?
- Describe a typical run, a difficult run, and the point where human judgment or approval is required.
- What happens if the agent is wrong, late, unavailable, or partially completes the process?

### Round 2: Experience and boundary

- Who are the users, in which tenants or organizations, and are anonymous users allowed?
- Which channels are mandatory now and likely later? Distinguish a preference from a contractual requirement.
- Is the primary experience conversational, knowledge-centric, document-centric, voice/contact-center, app/form/case-centric, or invisible automation?
- Must internal and external users share the same behavior, data, history, owner, and release cadence?

### Round 3: Runtime behavior

- Can the process be expressed as stable topics and rules, or must the runtime plan and adapt?
- Do intermediate results change the next action? What retries, recovery, or compensating actions are required?
- Which files or artifacts are read, created, or edited?
- Is temporary code execution useful? Does any code require network access or persistent storage?
- Is persistent memory required, and what may be retained?
- Would specialist connected agents have distinct instructions, tools, owners, or evaluation?
- Should the result be built as an agent, a workflow, a workflow with one bounded agent node, or an agent that invokes an exact workflow? Which steps must remain deterministic?

### Round 4: Data, tools, and identity

- What authoritative knowledge sources are used, and how current must they be?
- Which systems are read and which are changed? Identify connector, API, MCP, or custom integration needs.
- Is an existing flow a Copilot Studio agent flow or a Power Automate cloud flow? Can it be exposed as an agent-callable tool with a defined trigger, input/output contract, identity, idempotency, and licensing treatment, or must it be redesigned?
- Must actions run as the user, a service identity, or a controlled combination?
- Where are consent, approval, segregation of duties, audit, and human handoff required?
- Note data classification, residency, DLP, tenant, private-network, and least-privilege constraints.

### Round 5: Lifecycle and operations

- What environments, solution packaging, source control, deployment approvals, and rollback are required?
- Who owns content, connections, evaluation, support, incidents, and access reviews?
- What telemetry, analytics, traceability, response time, availability, and retention are required?
- If Microsoft 365 Copilot is in scope, is this a custom agent or an agent for Microsoft 365 Copilot, and is Copilot Studio Analytics required?
- Is there an existing standard or other agent? Which assets are valuable, and is redesign acceptable?
- Does policy permit production-ready preview or public-preview dependencies? What support status is mandatory for production?
- Is the migration driven by a polish gap, a capability gap, or a channel, identity, or governance boundary?

### Round 6: Economics

- How many monthly authoring sessions, preview or evaluation runs, production tasks, answers, tool actions, Copilot Studio agent-flow actions, Power Automate cloud-flow runs, files or pages, AI tool units, and voice minutes are expected?
- Are supplied counts separate metered activities, or could answer, agent-action, and flow-action counts describe the same interaction? One question can create multiple metered activities.
- Which users have eligible Microsoft 365 Copilot licenses? Which usage is external, anonymous, custom-channel, or otherwise billable?
- What Copilot Credit capacity, pay-as-you-go plan, agreement price, Azure subscription, or budget already exists?
- What growth, seasonality, retry rate, failure rate, and high-percentile complexity should scenarios include?
- Is demand stable enough to compare an annual P3 commitment, or should the decision remain on pay-as-you-go or monthly capacity until pilot telemetry exists?
- Which non-Copilot costs must be shown separately?

## Match the audience

- For makers, lead with the scenario, recommendation, build shape, and practical next actions. Explain product terms in plain language and keep architecture detail proportional to risk.
- For architects and CoE teams, include the requirements ledger, identity and authorization design, environment and ALM implications, observability, support ownership, preview policy, cost model, and decision triggers.
- Preserve the same hard-gate and evidence discipline for both audiences. Change the presentation depth, not the safety bar.

## Requirements ledger

Use a compact table:

| Requirement or constraint | Evidence class | Value | Decision impact | Validation owner/action |
|---|---|---|---|---|
| Example: Public website is mandatory | Confirmed requirement | Anonymous external users | Excludes Copilot chat; requires live channel/auth check | Architect verifies current publishing documentation |

Evidence classes are Confirmed requirement, Documented fact, Assumption, and Unknown. Mark hard constraints explicitly.

## Quick Harness Decision Brief

Keep this concise but complete.

### Recommendation

Name the harness or Microsoft alternative, confidence, and one-sentence rationale.

### Why this wins

List the three to five decisive requirements. Name the runner-up and why it loses. List any disqualified option and the hard gate it fails.

### Experience architecture

State the harness; recommended build shape; exact flow or workflow type; channels; users; authentication pattern; core components; tools; human approvals; and whether one agent can serve all audiences. If proposing multiple agents, name the boundary that requires the split.

### Credits and licensing

If material, show documented facts, assumptions, calculation or range, exclusions, and the telemetry needed to replace estimates with actuals. Otherwise state why no meaningful estimate is possible yet.

### Risks and next actions

List decision-critical unknowns, current feature and maturity checks, a small pilot, evaluation cases, and conditions that would change the recommendation.

### Sources

Link the decisive official sources and state the date checked.

## Detailed Harness Decision Brief

### 1. Executive decision

- Recommended harness or Microsoft alternative
- Confidence: High, Medium, or Low
- Decision statement and scope
- Recommended build shape: agent, workflow, workflow with an agent node, or agent calling a workflow
- Runner-up and the condition under which it would win

For a “none of these” decision, report two confidence levels when they differ: confidence that Copilot Studio is excluded and confidence in the proposed Microsoft runtime or deployment topology.

### 2. Requirements and evidence

Include the requirements ledger. Separate hard constraints from preferences.

### 3. Options considered

For every harness and any credible Microsoft alternative, show supporting evidence, conflicting evidence, hard gates, and disposition. Avoid arbitrary weighted scores.

### 4. Target experience and architecture

Describe users, channels, authentication, data boundaries, harness behavior, build shape, exact workflow or flow type, model considerations, instructions, knowledge, tools, skills, memory, connected agents, topics or flows, human approvals, and handoffs. Make channel, harness, and solution shape distinct. Enforce privileged access and approvals in source permissions, tool identity, and downstream systems rather than relying on instructions or topics.

When files are involved, cover ingress and attachment support, file-type and size limits, malware scanning, sandbox or temporary processing, persistent storage, classification, retention, output delivery, and deletion.

If one agent serves internal and external channels, explain why behavior, identity, governance, ownership, lifecycle, and economics align. If the design splits, name the material boundary and the contracts between parts.

### 5. Security, governance, and operations

Cover least privilege, user versus service identity, DLP, environment strategy, connection ownership, audit, data retention, human oversight, ALM, release approvals, observability, evaluation, support, incident handling, access reviews, and preview policy. Mark product capabilities and maturity claims that still require current verification.

### 6. Copilot Credits and licensing

Use four visibly separate subsections:

1. **Documented facts** — cited rates, ranges, inclusions, and checked date.
2. **Assumptions** — volumes, complexity distribution, retry factor, growth, entitlement treatment, and any user-supplied heavy-case upper bound.
3. **Calculations** — gross credits, included or entitled adjustment, billable range, and compatible-period pay-as-you-go, capacity-pack, and P3 list-price scenarios.
4. **Exclusions** — Microsoft 365 seats, Azure, connectors, telephony, third-party systems, custom models, implementation, operations, and taxes or agreement differences as applicable.

### 7. Delivery outline

Define a thin pilot, representative evaluation set, security and admin checks, cost telemetry, production hardening, rollback, ownership, and acceptance criteria. Treat a harness change as redesign and migration when Microsoft does not support in-place transfer.

### 8. Risks, unknowns, and decision triggers

Name each unresolved item, impact, owner, validation action, and date. State what new evidence would overturn or split the decision.

### 9. Sources

Link official Microsoft sources closest to each material claim and state the date checked. Clearly label community guidance as guidance rather than product documentation.

## Confidence rubric

- **High:** all material gates are confirmed; decisive feature, channel, identity, and licensing claims are current; realistic volume evidence exists; no unresolved item is likely to reverse the decision.
- **Medium:** the leading option is clear, but one or more validations could change architecture, cost, or implementation details.
- **Low:** a mandatory gate, workload shape, identity boundary, or current product capability is unknown and could change the selected option.
