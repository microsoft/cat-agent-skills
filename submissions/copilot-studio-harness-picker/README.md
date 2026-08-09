# Copilot Studio Harness Picker

Choose between the GitHub Copilot, standard, and Copilot chat harnesses—or a
better-fitting Microsoft alternative—using an evidence-led architecture
assessment.

The skill tests hard constraints before preferences. It distinguishes the
harness from the model, publication channel, and solution components, then
recommends both the runtime and the build shape: agent, workflow, workflow with
an agent node, or agent calling a workflow.

## What it covers

- Quick and Detailed assessment modes.
- Internal, external, anonymous, and cross-tenant user boundaries.
- Mandatory channels, authentication, identity, and authorization.
- Predictable conversations versus adaptive multistep work.
- Agent, workflow, and application-centric solution shapes.
- One-harness versus multi-agent or multi-harness architectures.
- Governance, ALM, observability, preview policy, and operational ownership.
- Classic or standard-agent improvement, redesign, and migration decisions.
- Transparent Copilot Credit planning with facts, assumptions, calculations,
  and exclusions kept separate.
- Microsoft alternatives when Copilot Studio cannot meet a hard constraint.

## Before you start

You do not need to connect a tenant to run the assessment. Bring a sanitized
description of the intended outcome, users, channels, data, actions, identity
model, operating constraints, and expected volume.

Current product availability and licensing can change. The skill records the
date of its bundled planning snapshot and instructs the agent to verify any
decision-critical claim against current official Microsoft documentation.

Python 3 is required only when using the bundled credit estimator.

## Recommended Cowork model

For **Detailed** assessments, select **GPT-5.6** and use **High** reasoning
effort if your Cowork tenant exposes that control. If GPT-5.6 has not reached
your tenant, use **Claude Opus 5**. High is the recommended balance for this
skill: the architecture comparison benefits from deeper reasoning, but the
highest possible setting is unlikely to justify extra latency for every run.

For a particularly important decision brief, **Sonnet + Opus Advisor** is a
good alternative because it adds a second review. For **Quick** mode, leave the
picker on **Auto**; choose **Claude Sonnet 5** manually when turnaround matters
more than depth.

Do not default to **Claude Fable 5 (Preview)** because it is off by default and
has additional data-retention implications. Model availability is controlled
by the tenant and can change. Microsoft currently documents the Cowork model
picker rather than a universal reasoning-effort selector, so apply the High
recommendation only when that setting appears in your experience. See
[Choose a model for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-models)
and Microsoft's [GPT-5.6 rollout announcement](https://techcommunity.microsoft.com/blog/microsoft365copilotblog/available-today-openai%E2%80%99s-gpt-5-6-in-microsoft-365-copilot/4533152).

## How to use it

For a fast assessment, ask:

> Use Quick mode to recommend a Copilot Studio harness for an internal HR policy
> assistant in Microsoft 365 Copilot Chat. It answers from SharePoint, has no
> external users, and can create an HR ticket after confirmation.

For an architecture decision, ask:

> Use Detailed mode to assess a customer-service agent for a public website,
> WhatsApp, and Teams. It reads customer records, creates case documents,
> requires approval for account changes, and must comply with our production
> preview policy. Include licensing and Copilot Credit scenarios.

The skill asks only for missing information that could change the decision. It
then produces a Harness Decision Brief containing the recommendation,
confidence, runner-up, hard-gate analysis, target architecture, cost treatment,
risks, validation actions, and conditions that would overturn the decision.

## Good to know

- A multi-harness recommendation must identify a genuine channel, identity,
  governance, lifecycle, runtime, or economic boundary.
- Instructions and conversational confirmation are not treated as authorization
  or approval controls; privileged operations must be enforced by the tool,
  workflow, identity layer, or downstream system.
- Credit outputs are planning estimates, not quotes. The estimator reports gross
  credits before licensing inclusions and preserves open-ended Microsoft ranges.
- The skill does not request passwords, tokens, connection strings, production
  records, or confidential document contents.
