# Agentic Center of Excellence (reference)

Last verified against Learn: 2026-11-24. Fetch the live pages at run time; they win over this file. All text is a paraphrase.

Hub: https://learn.microsoft.com/en-us/agents/center-of-excellence/

## What the CoE is

Learn describes the CoE as the team and operating rhythm that lets the rest of the organization build and run agents safely. It makes the safe path the easy path through guardrails, golden paths and a shared lifecycle. It does not replace existing governance (security and compliance, cloud and IT governance, Power Platform or low-code CoE, Microsoft 365 governance, responsible AI). It adds agent-specific capability and fills the gaps agents create: ownership, lifecycle, decision rights and monitoring.

## Four functions

| Function | Paraphrase | Example first moves (advisor's suggestions) |
|---|---|---|
| Governs | Release gates and audit logs of who built and approved each agent and what it does | Publish risk tiers; require a named owner before production; start an agent registry |
| Enables | Golden paths, templates, training and community so the right way is the easy way | One low-risk golden path; role-based training cohort; champions network |
| Optimizes | Monitor quality, cost and value across the lifecycle and feed learning back | Weekly health check; baselines for each agent; evaluation test sets |
| Scales | Turn what works in one team into a repeatable pipeline | Promote proven agents into a catalog; reuse templates across teams |

## Three failure modes

| Failure mode | What it looks like (paraphrased) | Design check |
|---|---|---|
| Gatekeeper | Reviews everything, enables nothing, becomes a bottleneck; teams build shadow agents | Is there a self-service route for Tier 1 agents? |
| Ghost | Launched loudly, then no rhythm, no authority, no active members | Is there a sponsor, a decision forum and a calendar? |
| Perfectionist | Blocks shipping until governance is "complete" | Can teams ship within published guardrails today? |

## Structure and operating model

Source: https://learn.microsoft.com/en-us/agents/center-of-excellence/operating-models

| Model | Who builds | Who governs | Strength | Main risk | Fits when |
|---|---|---|---|---|---|
| Centralized | Central team | Central team | Consistency and control | Bottlenecks | Maturity is early, risk is high, or agents cross the trust boundary |
| Hybrid | Central and local teams | Central standards, shared oversight | Balance of scale and agility | Coordination complexity | Teams are starting to build for themselves |
| Federated | Business unit teams | Central standards, govern by exception | Scale through distributed ownership | Standards drift | Teams can own governance locally |

Learn notes most organizations blend models across patterns, and that a central platform with federated delivery ("hub and spoke") is common at scale. Choose by patterns and maturity, not by the org chart. Lower maturity and higher risk favor central control.

Starting structure per pattern: Employee AI enablement centralized; Business expert empowerment federated; Workplace and IT services centralized then hybrid; Core business process transformation federated; External engagement centralized; AI-first capabilities federated.

## Govern agents by risk

Source: https://learn.microsoft.com/en-us/agents/center-of-excellence/govern-agents-risk

The clearest risk signal is the assist-to-execute line. Sort agents by what they do.

| Tier | Typical agents | Required controls (paraphrased) | Usual patterns |
|---|---|---|---|
| Tier 1, low | Individual productivity: summarize, draft, search | Named owner, basic usage and error monitoring, standard release checklist, self-service within guardrails | Employee AI enablement |
| Tier 2, medium | Expert knowledge and internal services | Named owner plus domain-expert validator, knowledge-quality monitoring, formal release gate, accuracy tracking and feedback | Business expert empowerment, Workplace and IT services |
| Tier 3, high | Business-critical and external-facing | Named owner plus process owner, SLA monitoring, security review and responsible AI assessment before release, decision-rights framework, incident response plan, quarterly maturity review | Core business process transformation, External engagement, AI-first capabilities |

Governance is continuous. Start an agent in the tier that fits its behavior and move it up as scope or autonomy grows. Integrate with existing governance bodies instead of building a parallel regime.

Related: secure agents (identity per agent, least privilege, registry, shadow-agent discovery, data protection, monitoring) https://learn.microsoft.com/en-us/agents/center-of-excellence/secure-agents ; responsible AI as a release gate sized to risk, human approval for hard-to-reverse actions, AI disclosure for external agents https://learn.microsoft.com/en-us/agents/center-of-excellence/responsible-ai

## Vision, sponsorship, roles

- Executive sponsorship: the sponsor supplies budget, authority and credibility; sets priorities, makes trade-off decisions, removes blockers, and models agent use. Name a backup sponsor and business advocates. https://learn.microsoft.com/en-us/agents/center-of-excellence/executive-sponsorship
- Vision, metrics and goals: one to three year vision anchored on outcomes (cost, speed, quality, capacity, experience, new revenue); goals across adoption, value and governance, each with a baseline and target. https://learn.microsoft.com/en-us/agents/center-of-excellence/vision-metrics-goals
- Roles and decision rights: executive sponsor, business owner, CoE lead, agent product owner, security and compliance, responsible AI lead, data stewardship, platform and operations, architects, admins, makers, pro-code developers. Assign roles to named people, not teams. https://learn.microsoft.com/en-us/agents/center-of-excellence/roles-responsibilities

## Intake, front door, lifecycle, golden paths

- Intake fields: business value, data sources and integrations, pattern, risk level, requester and sponsor. Score on value, feasibility and resources; route review depth by tier; keep a visible backlog across immediate, near-term and long-term horizons. https://learn.microsoft.com/en-us/agents/center-of-excellence/intake-prioritization
- Agent front door: one place to ask; answers from approved guidance, checks for reuse, routes to reuse, self-build or CoE support; same tiers and gates still apply. https://learn.microsoft.com/en-us/agents/center-of-excellence/agent-front-door
- Agent CoE Front Door sample: a Copilot Studio starter template, provided as-is and not a production product; evaluate in a non-production environment. https://learn.microsoft.com/en-us/agents/center-of-excellence/agent-front-door-sample
- Lifecycle as products: intake, triage, build, deploy, monitor, improve, retire; every agent has an owner, a monitoring plan and a path to improvement or retirement. https://learn.microsoft.com/en-us/agents/center-of-excellence/agent-lifecycle
- Golden paths and reusable assets: templates, pattern library, approved connectors and MCP servers, prompt libraries, evaluation test sets, each with an owner. https://learn.microsoft.com/en-us/agents/center-of-excellence/reusable-assets
- Enable makers: role-based skilling, community of practice, champions, recognition, leaders modeling use. https://learn.microsoft.com/en-us/agents/center-of-excellence/enablement-community

## Operating rhythm

Source: https://learn.microsoft.com/en-us/agents/center-of-excellence/operating-rhythm (Learn presents the cadence as a starting point, not a rule.)

| Cadence | Focus (paraphrased) |
|---|---|
| Weekly | Agent health (usage, errors, latency, cost), intake triage, incidents, knowledge freshness, escalation logs |
| Monthly | Steering review with sponsor: scorecard, outcome KPIs, adoption and reliability, risk posture, cross-team issues |
| Quarterly | Reassess maturity against targets, roadmap, business value report, portfolio scale, sustain or retire, investment |

## Measuring value and cost

- Monitor, measure and report value: track a short balanced set across adoption and delivery, value, governance coverage, and quality and risk; pair leading and lagging signals; baseline before rollout; use evaluation for drift. https://learn.microsoft.com/en-us/agents/center-of-excellence/measure-report-value
- Copilot Studio ROI guidance: define value before building, measure across value drivers, tell the value story with a scorecard. https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/agent-business-value-overview and https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/agent-business-value-measure-impact
- Govern Copilot Credit consumption: govern at the environment level; classify environments as exploration, test and validation, or funded production; assign cost owners and agent-level limits. https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/govern-credit-consumption

Use only these Learn pages for cost and consumption framing. Do not quote prices; point the user to official licensing pages for pricing.

## Adjacent Learn guidance (optional)

- Cloud Adoption Framework, organizational readiness for AI agents: https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ai-agents/organizational-readiness
- Cloud Adoption Framework, establish an AI CoE: https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ai/center-of-excellence

## Leader decisions (advisor's synthesis, not an official Microsoft list)

| Decision | Options | Informed by |
|---|---|---|
| Patterns to fund now (cap two or three) | List candidates with gap verdict | choose-pattern |
| Named business owner per pattern and per executing agent | Person, not team | next-steps-action-plan, roles-responsibilities |
| Risk appetite and autonomy limits | Which actions always need a human | govern-agents-risk, responsible-ai |
| CoE model, lead and backup sponsor | Centralized, hybrid, federated, blend | operating-models, executive-sponsorship |
| Value metrics, baselines and targets | Adoption, value, governance, quality and risk | vision-metrics-goals, measure-report-value |
| Priority pillars for the next two quarters | One or two pillars, one level each | maturity-model-how-to-use |
| Cost ownership for consumption-based agents | Environment classes and limits | govern-credit-consumption |
