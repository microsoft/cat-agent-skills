---
name: copilot-agent-advisor
description: |
  Recommends which Microsoft 365 / Copilot Studio agent option fits a described
  scenario — using Microsoft 365 Copilot as-is, building a standard (declarative)
  agent, or building a custom (custom engine) agent — and which Copilot Studio
  harness to build on (GitHub Copilot, standard, or Copilot chat). Use when
  the user asks "which agent type should I build", "declarative vs custom engine
  agent", "standard agent or custom agent", "should I use Copilot Studio or
  Microsoft 365 Copilot", "which Copilot Studio harness", "help me choose a
  Copilot agent", or describes an agent scenario and wants a recommendation.
  Do NOT use to actually build, deploy, configure, or write code for an agent,
  and do NOT use for non-agent product comparisons — this skill only advises on
  the choice. For general capability questions about Microsoft 365 Copilot,
  answer directly instead of invoking this skill.
cowork:
  category: analysis
  icon: Lightbulb
---

## Overview

This skill helps a user pick the right way to deliver an AI experience in the
Microsoft 365 + Copilot Studio ecosystem. It gathers the handful of factors that
actually drive the decision (data sources, models, orchestration, channels,
autonomy, collaboration, compliance, and skill/speed), maps them to one of three
options, and returns a clear, reasoned recommendation with a runner-up and how to
build it. It also advises which Copilot Studio **harness** (GitHub Copilot,
standard, or Copilot chat) to build on.

The three options it chooses between:

| Option | What it is | Use when |
|--------|-----------|----------|
| **Use Microsoft 365 Copilot as-is** | The built-in Copilot experience over Microsoft Graph data, no build. | Built-in capabilities + your Microsoft 365 data already cover the need; you don't need extra knowledge, custom instructions, or actions. |
| **Standard agent (declarative agent)** | Copilot configured with your instructions, knowledge, and actions, running on **Copilot's own orchestrator and foundation models**, inside Microsoft 365 apps. | You want to tailor Copilot for a focused scenario, stay inside Microsoft 365 (Teams, Outlook, SharePoint, Word), inherit Microsoft 365 compliance/RAI, and ship fast with low-code or a streamlined pro-code path. |
| **Custom agent (custom engine agent)** | A fully custom agent where you **bring your own orchestrator and models**, with custom/complex workflows, its own hosting, and multi-channel reach. | You need custom orchestration, your own/fine-tuned/domain models, deterministic complex business logic, proactive/autonomous behavior, group collaboration, delivery outside Microsoft 365, or you're integrating an existing external bot. |

## When to Use

- The user describes an agent/automation scenario and asks what to build.
- The user asks to compare declarative vs custom engine agents, standard vs custom agents, or Copilot Studio vs plain Microsoft 365 Copilot.
- The user asks which Copilot Studio harness to build on (GitHub Copilot, standard, or Copilot chat).
- The user is unsure whether they even need to build an agent at all.

## When NOT to Use

- The user wants to **actually build, configure, deploy, or write code** for an agent — this skill only advises on the choice, not the build.
- The user asks a general "what can Microsoft 365 Copilot do" capability question — answer that directly.
- The user asks for a non-agent product comparison (e.g. licensing, Power Automate vs Logic Apps) — out of scope.

## Quick Start

```
User: "We want a Teams helpdesk assistant that answers from our SharePoint IT
       policies and can open a ticket in ServiceNow. Which agent should I build?"
1. Gather the decision factors (Phase 1) — most are already stated; fill gaps
   with ONE clarifying question if a load-bearing factor is missing.
2. Apply the decision logic (Phase 2).
3. Recommend (Phase 3): primary option + why, runner-up, how to build, caveats.
4. (Optional) If the platform can browse the web, verify any current product
   detail against Microsoft Learn before asserting it.
```

## Core Instructions

### Phase 1: Gather the decision factors

Collect the answers below. Take whatever the user already gave you; if a
**load-bearing** factor is missing (one that would flip the recommendation), ask
for just those with a single clarifying question (offer multiple choice where the
platform supports it). Never ask about factors the user already answered.

1. **Knowledge / data** — Is the needed knowledge in Microsoft 365 (SharePoint, OneDrive, Teams, Graph, Copilot connectors), or in external systems/APIs?
2. **Models** — Do you need your own, fine-tuned, small, or domain-specific/multimodal models, or is Copilot's foundation model fine?
3. **Orchestration / logic** — Do you need custom orchestration, complex multi-step workflows, precise business rules, or deterministic step-by-step control?
4. **Channels / reach** — Will it live only inside Microsoft 365 apps (Teams, Outlook, Word, Copilot Chat), or also outside (own website/app, other platforms)?
5. **Autonomy** — Is it purely user-initiated, or must it act proactively / on triggers without direct user input?
6. **Audience** — Individual use, or shared group collaboration (a Teams channel/meeting, many users on the same agent)?
7. **Compliance** — Is inheriting Microsoft 365 security/compliance/RAI enough, or must you manage your own compliance posture?
8. **Speed & skill** — Do you want the fastest low-code route, or do you have pro-code capacity (.NET/Python/JS, Semantic Kernel/LangChain) and need full control?
9. **Existing assets** — Is there already a conversational bot built outside Copilot that you want to bring into Microsoft 365?

### Phase 2: Apply the decision logic

Evaluate in order; the first block that clearly matches is the recommendation.

- **Recommend "Use Microsoft 365 Copilot as-is"** when the built-in Copilot plus the user's Microsoft 365 data already covers the need and there's no requirement for custom instructions, extra knowledge sources, or actions. Don't recommend building an agent that adds no capability.
- **Recommend a Standard (declarative) agent** when the scenario is a **focused** one that can run on Copilot's orchestrator and foundation models, the knowledge lives in Microsoft 365 (or reachable via Copilot connectors/actions), the workflow stays **inside Microsoft 365 apps**, it's mostly individual/user-initiated, the user wants faster/low-code delivery, and inheriting Microsoft 365 compliance & RAI is acceptable. Example: an IT helpdesk agent that answers @mentions in Teams, or a SharePoint document-summarization agent.
- **Recommend a Custom (custom engine) agent** when **any** of these is true: custom orchestration or complex/deterministic business logic; your own/fine-tuned/domain/multimodal models; delivery **outside** Microsoft 365; proactive/autonomous (trigger-driven) behavior; group collaboration where many users share one agent in a channel/meeting; or integrating an existing external bot. Note this route typically needs **its own hosting** (e.g. Azure) at additional cost and you must ensure your own compliance/RAI/security. Example: a loan-approval agent with strict rules and multiple credit-check integrations.

If the scenario straddles standard and custom, lead with the **lighter** option that still meets every hard requirement, and name the specific factor(s) that would push it to custom.

### Phase 3: Which Copilot Studio harness to build on

When the recommendation involves building in Copilot Studio, also advise the **harness** — the runtime that sits between your agent and the model, deciding when to call the model, what components to send it, and which tools to invoke. Copilot Studio documents three (see [References](#references) for the authoritative, current comparison):

- **GitHub Copilot harness — the most capable, for reasoning-heavy work.** Takes a goal, breaks it into steps, and calls tools across connectors, knowledge, MCP, and connected agents, adjusting when a step fails. Natively creates and edits Word, Excel, PowerPoint, and PDF files, supports **skills** and **memory**, and runs each task in a governed sandbox. Billed with **Copilot Credits**. Recommend it for complex, multi-step business processes that work across tools and files (e.g. an accounts-payable agent that reads invoices, matches purchase orders, and routes exceptions).
- **Standard harness — dependable and rule-based.** You define the topics, prompts, and paths so a structured, repeatable conversation or workflow responds **predictably**, drawing on your prompt library and enterprise knowledge. Billed via **standard-harness licensing**. Recommend it when the scenario is well-defined and you want consistent answers (e.g. an internal help-desk agent that answers common questions and routes simple requests).
- **Copilot chat harness — for extending Microsoft 365 Copilot Chat.** Connects your enterprise knowledge to M365 Copilot Chat so employees get grounded answers without leaving their everyday experience; publishes to internal teams. Billing is consumption-based or included in the Microsoft 365 Copilot user subscription. Recommend it when the priority is connecting people to information (e.g. an onboarding agent grounded on SharePoint knowledge).
- **Always warn:** agents aren't transferable between the **GitHub Copilot** and **standard** harnesses (different runtimes), and the harnesses bill differently, so the choice should be deliberate. You switch which harness you build on via the **New experience** toggle on the Copilot Studio home page.
- **Depth boundary.** Advise the harness at a *decision* level — which one and why. For detailed Copilot Credit / licensing estimates, capacity math, or channel-and-identity implementation checks, hand off to a dedicated harness-selection skill or to Microsoft Learn rather than computing them here. This skill focuses on the choice of whether to build and which agent type, with the harness as one downstream step.

### Phase 4: Recommend

Deliver the output in the format below. Keep it decision-focused, not a product essay.

## Output

Respond inline (no file unless asked) with:

1. **Recommendation** — one primary option, stated plainly in the first line.
2. **Why** — 2-4 bullets tying the recommendation to the user's specific factors (name them).
3. **Harness** — GitHub Copilot, standard, or Copilot chat, with the not-transferable-between-harnesses caveat when relevant.
4. **Runner-up / when to reconsider** — the next-best option and the single factor that would flip the decision.
5. **How to build it** — the tooling path (low-code Copilot Studio / Agent Builder, or pro-code Microsoft 365 Agents Toolkit / Visual Studio Code, plus hosting note for custom engine agents).
6. **Caveats** — cost/hosting and compliance ownership for custom engine agents; that capabilities evolve and specifics should be confirmed on Microsoft Learn.

Offer a quick comparison table (or a card, if the platform renders them) only when 3+ options/attributes make a table clearer than prose.

## Guardrails

- **Advise, don't build.** This skill recommends a choice; it does not create, configure, deploy, or write agent code. If the user then wants to build, hand off rather than pretending to provision anything.
- **Ground current specifics.** Product names, capabilities, and preview status change quickly. When the user needs authoritative or current detail (feature availability, pricing, preview vs GA), verify against Microsoft Learn (`learn.microsoft.com`) using whatever web-lookup capability the platform provides before asserting, and say when something is subject to change. If the platform can't browse the web, flag the detail as time-sensitive and point the user to Microsoft Learn.
- **Never fabricate** feature availability, limits, or pricing. If you're unsure, say so and point to Microsoft Learn rather than guessing.
- **Ask only load-bearing questions.** Only ask a clarifying question for a factor that would actually change the recommendation; otherwise state a reasonable assumption and proceed.
- **Explain trade-offs, don't oversell.** Flag the cost, hosting, and compliance-ownership burden of custom engine agents, and the scope limits of declarative agents, so the user chooses with eyes open.

## References

Ground harness and agent-type claims on current Microsoft Learn documentation. Verify volatile details (previews, pricing, Copilot Credits) against these before asserting, and note the date checked when the platform can browse the web.

- **Choose a harness (GitHub Copilot, standard, Copilot chat):** https://learn.microsoft.com/en-us/microsoft-copilot-studio/harnesses-overview
- **Access standard vs GitHub Copilot harness (switching, what changes):** https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/switch-experiences
- **Copilot Studio licensing & Copilot Credits:** https://learn.microsoft.com/en-us/microsoft-copilot-studio/billing-licensing

## Platform compatibility

This skill is platform-neutral — its logic is pure advisory reasoning with no dependency on any platform-specific tool. Clarifying questions, comparison tables, and optional web lookups are described as *capabilities* ("if the platform supports it / can browse the web"), so it runs the same in **Cowork**, **Copilot Studio**, and **Scout**. The `cowork:` frontmatter only supplies a card category/icon in Cowork and is safely ignored elsewhere.
