# Microsoft AI Platform Advisor

Guides a customer through a structured discovery interview and recommends the right Microsoft AI platform for their project — Microsoft 365 Copilot, Agent Builder, Copilot Studio, Microsoft Foundry, Foundry Agent Service, Windows AI Foundry, or Agent 365 as a governance layer. It scores the build on technical complexity and risk, plots them on a 2×2 quadrant chart, and returns a recommendation brief with planning guidance and next steps.

## Why use it

Enterprise customers frequently ask which Microsoft AI product fits their scenario. This skill replicates the discovery-and-recommend flow a solution architect runs manually, using the official Microsoft Learn decision guides as the mapping logic. Alongside the platform pick, it turns effort into explicit complexity and risk scores so the customer can plan the build accordingly.

## When to use it

- A customer or team is choosing between Microsoft AI platforms for a new project.
- You need to gather requirements and scope an AI or agent build.
- You want a quick, defensible complexity/risk read to plan phasing and governance.

It is a front-door discovery-and-recommend tool, not a deep technical design aid for an already-chosen platform.

## Setup (Copilot Studio)

The skill produces an inline Mermaid quadrant chart out of the box, with no setup. The optional rendered PNG chart requires the Copilot Studio **code interpreter**:

- Enable code interpreter at the **environment level**: Power Platform admin center → Environments → Settings → Product → Features → Copilot Studio code interpreter → On.
- In the agent, add a **prompt tool** (Tools → Add a tool → Prompt), then in the prompt's Settings turn on **Enable code interpreter**. Name it something like `Generate Effort Chart`.
- Code interpreter counts as **premium generative AI messages** — check the customer's licensing before relying on this path.

**Rendering limitation:** images created by code interpreter do **not** render in the Teams or Microsoft 365 Copilot channels. They render in the Copilot Studio test pane, the demo website, and custom web channels. For Teams or Microsoft 365 Copilot delivery, the skill falls back to the Mermaid chart.

## Good to know

Recommendations are grounded in the Microsoft Learn decision guides cited in the skill. Microsoft AI products evolve quickly — validate the final recommendation against current Microsoft Learn documentation before committing a customer to a platform.
