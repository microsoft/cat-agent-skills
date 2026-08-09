# Official and supporting sources

Use the official Microsoft Learn and licensing sources for product and commercial claims. Treat Microsoft CAT blog posts as practitioner guidance and Agent Skills as the skill-format specification. This list was checked on 2026-08-04.

## Harnesses and authoring

- [Harnesses overview](https://learn.microsoft.com/en-us/microsoft-copilot-studio/harnesses-overview) — harness definition and high-level comparison.
- [GitHub Copilot harness experience overview](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/overview) — authoring/runtime experience, components, and migration limitation.
- [Classic versus new agent experience](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/classic-vs-new) — current comparison, transfer limitation, and preview notices.
- [Workflows overview](https://learn.microsoft.com/en-us/microsoft-copilot-studio/workflows-experience/flows-overview) — GitHub-harness workflow model, triggers, actions, deterministic behavior, current maturity, and capacity treatment.
- [Add an agent node to a workflow](https://learn.microsoft.com/en-us/microsoft-copilot-studio/workflows-experience/agent-node-workflow) — bounded reasoning inside a workflow, supported configuration, testing, and billing notice.
- [More powerful agents and workflows for autonomous business processes](https://techcommunity.microsoft.com/blog/copilot-studio-blog/more-powerful-agents-and-workflows-for-autonomous-business-processes-introducing/4542969) — Microsoft product announcement and positioning.
- [Extend Microsoft 365 Copilot with agents](https://learn.microsoft.com/en-us/microsoft-copilot-studio/microsoft-365-copilot-extend-with-agents) — Copilot chat, custom-versus-Microsoft 365 agent context, tools, distribution, and analytics caveat.

## Copilot Cowork models

- [Choose a model for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-models) — Auto behavior, tenant-dependent model availability and data-retention notices.
- [Available today: OpenAI's GPT-5.6 in Microsoft 365 Copilot](https://techcommunity.microsoft.com/blog/microsoft365copilotblog/available-today-openai%E2%80%99s-gpt-5-6-in-microsoft-365-copilot/4533152) — GPT-5.6 rollout to Cowork and its positioning for agentic, multistep work; availability can vary by region and tenant.

## Channels, authentication, and sharing

- [GitHub Copilot harness publication channels](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/publication-channels-overview) — current available and unavailable channels.
- [Standard harness publication channels](https://learn.microsoft.com/en-us/microsoft-copilot-studio/publication-fundamentals-publish-channels) — standard channel options.
- [Configure end-user authentication](https://learn.microsoft.com/en-us/microsoft-copilot-studio/configuration-end-user-authentication) — authentication modes and channel considerations.
- [Share a GitHub Copilot harness agent](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/authoring-share-agent) — current sharing and collaboration behavior.

## Copilot Credits and licensing

- [Microsoft Copilot Credits Guide, August 2026](https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/bade/documents/products-and-services/en-us/ai/Microsoft-Copilot-Credits-Guide.pdf) — GitHub Copilot harness planning ranges, credit model, and commercial guidance.
- [Microsoft Copilot Studio Licensing Guide, August 2026](https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/bade/documents/products-and-services/en-us/ai/Microsoft-Copilot-Studio-Licensing-Guide-August-26.pdf) — pay-as-you-go, P3 tiers, capacity packs, and purchasing terms.
- [Optimize Copilot Credit costs with a pre-purchase plan](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/copilot-credit-p3) — P3 sizing, scope, discount interaction, renewal, and purchase restrictions.
- [GitHub Copilot harness billing and credits](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/billing-credit-overview) — when creation, preview, evaluation, and runtime consume credits.
- [Copilot Studio billing and licensing](https://learn.microsoft.com/en-us/microsoft-copilot-studio/billing-licensing) — plans, eligible Microsoft 365 usage, and capacity concepts.
- [Copilot Studio message and credit management](https://learn.microsoft.com/en-us/microsoft-copilot-studio/requirements-messages-management) — activity rates and metering rules.
- [AI Builder credit rates](https://learn.microsoft.com/en-us/ai-builder/message-management) — basic, standard, and premium AI tool units.

## Runtime design guidance

- [Copilot Studio agent sandbox](https://microsoft.github.io/mcscatblog/posts/copilot-studio-agent-sandbox/) — CAT guidance on local computation, temporary files, skills, and network isolation.
- [New orchestrator resources](https://microsoft.github.io/mcscatblog/posts/new-orchestrator-resources/) — CAT guidance on instructions, knowledge, tools, memory, skills, and connected agents.
- [New Copilot Studio technical guide](https://microsoft.github.io/new-copilot-studio-tech-guide/) — deeper product architecture and building blocks.
- [Copilot Studio Plugin](https://github.com/microsoft/copilot-studio-plugin) — experimental Microsoft repository for creating, editing, validating, and drafting classic-to-new migrations; the repository explicitly states that it is unsupported and not meant for production use.

## Microsoft ecosystem alternatives

- [Microsoft Foundry Agent Service overview](https://learn.microsoft.com/en-us/azure/foundry/agents/overview) — managed custom agent runtime, models, frameworks, identity, and observability.
- [Hosted agents in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents) — managed custom-container runtime controls and constraints to validate.
- [Microsoft Agent Framework documentation](https://learn.microsoft.com/en-us/agent-framework/) — code-first agents and workflows for customer-hosted Azure architectures.
- [Microsoft 365 Agents SDK overview](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/agents-sdk-overview) — code-first multi-channel agent applications.
- [Custom engine agents for Microsoft 365 Copilot](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/overview-custom-engine-agent) — full-stack agent path in the Microsoft 365 ecosystem.
- [Power Automate documentation](https://learn.microsoft.com/en-us/power-automate/) — deterministic cloud and desktop workflows.
- [Azure Logic Apps documentation](https://learn.microsoft.com/en-us/azure/logic-apps/) — integration and workflow automation.
- [Power Apps documentation](https://learn.microsoft.com/en-us/power-apps/) and [Power Pages documentation](https://learn.microsoft.com/en-us/power-pages/) — app-, form-, and portal-centric experiences.

## Skill format and contribution

- [Agent Skills specification](https://agentskills.io/specification) — `SKILL.md` and resource-folder format.
- [Agent Skills best practices](https://agentskills.io/skill-creation/best-practices) — progressive disclosure and skill design.
- [Microsoft CAT Agent Skills contribution guide](https://github.com/microsoft/cat-agent-skills/blob/main/CONTRIBUTING.md) — submission folder, metadata, validation, and licensing requirements.

## Source discipline

- Prefer the narrowest official page that directly supports a claim.
- State “checked on YYYY-MM-DD” beside volatile availability, licensing, or pricing claims.
- Do not use a blog post as the sole authority for a binding product or commercial decision.
- When sources conflict, cite both, identify the conflict, and make validation an action rather than choosing silently.
- Paraphrase sources. Do not reproduce long copyrighted passages.
