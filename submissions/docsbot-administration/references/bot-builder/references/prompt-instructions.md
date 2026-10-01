# Agent Prompt Instructions

Read this when creating or materially changing `agentPrompt`, `customPrompt`, `helpscoutPrompt`, or voice instructions (`voiceAgent.instructions`, the logical `voicePrompt` channel).

## Source Of Truth

Start from the closest exact prompt template, then make minimal in-place edits. Do not rewrite, reorder, or remove major sections unless the user explicitly asks for a bespoke prompt and accepts losing template guardrails.

The core prompt constants are not exposed as a direct Admin MCP read operation. Use these prompt assets as the exact starting templates:

- [customer-support.md](../assets/prompts/customer-support.md)
- [sales-agent.md](../assets/prompts/sales-agent.md)
- [ai-agent.md](../assets/prompts/ai-agent.md)
- [helpscout.md](../assets/prompts/helpscout.md)

Use live prompt operations only as helpers after choosing the base template:

- Use `draft_bot_prompt` with `activeTab: "agent"` only when you need a template-aware draft for an existing bot. Review its output against the selected asset and reject broad rewrites.
- Use `debug_bot_prompt` for focused corrections when behavior is wrong.
- Persist accepted prompt changes with `update_bot`.

## Preset Selection

- Use `CUSTOMER_SUPPORT` for public support widgets, customer support, public docs help, and most mixed support/presales bots.
- Use `SALES_AGENT` for presales, product matching, quote/demo qualification, and purchase guidance.
- Use `AI_AGENT` for internal knowledge assistants, department/team assistants, research, and general private copilots.
- Use `HELPSCOUT` only for Help Scout email reply workflows, not normal widget agent prompts.
- Use copywriter only for explicit marketing/content generation bots.

## Voice Presets

For new bots/full setup or voice prompt work, follow [deployment/voice.md](deployment/voice.md). Start from [voice-support.md](../assets/prompts/voice-support.md) (runtime default), [voice-receptionist.md](../assets/prompts/voice-receptionist.md), or [voice-sales.md](../assets/prompts/voice-sales.md), whichever fits best. These are expanded canonical `VOICE_INSTRUCTION_PRESETS` from `src/lib/voiceAgent.js`, including the shared tool, knowledge and safety blocks. Fill `{business_name}`, `{product_info}`, and `{language}` with concise business context and the spoken language. Preserve the preset sections, tool names and call-grounding rules; use short spoken turns, one question at a time, interruptions and voice-specific output. Do not paste the Markdown-oriented text-agent prompt into voice instructions.

`draft_bot_prompt` supports agent/default tabs, not voice: never send `activeTab: "voice"` or treat its text-agent output as a voice preset. Save voice instructions through `create_bot`/`update_bot` using `voiceAgent.instructions`, then verify that exact field. Preparation does not authorize activation. The text-template section/Markdown rules below apply to text channels; voice retains its own canonical structure.

## Preserve Guardrails

Preserve these unless the user explicitly accepts the behavioral change:

- The selected template's overall role sentence, `## Instructions`, `## Output Format`, ordering, and nested tool-selection structure.
- The literal string `search_documentation` and any other canonical tool names from the selected prompt, such as `human_escalation`, in every non-empty `agentPrompt` and `helpscoutPrompt`.
- Tool-selection priority: matching Skills first, documentation search for company/product/process questions, escalation only when available and appropriate.
- Tool-name privacy: do not announce internal tool calls or function names to end users.
- Grounding rules: do not invent facts, links, policies, prices, or procedures.
- Output format and channel-specific instructions, especially Help Scout email formatting.
- Search limits and "ask a clarifying question" behavior when needed.

## Customize Deliberately

Edit as little as possible. Replace placeholders and insert concise context where the template already expects it:

- Replace `{company_name}` with the business/product owner name.
- Replace `{product_info}` with a short paragraph or bullets covering products, audience, deployment surface, and any key scope boundaries.
- Replace `{old_prompt}` with only the extra instructions needed for this bot, or remove the placeholder line if no extra instructions are needed.

Only add or adjust:

- Company, product, audience, and deployment context.
- Allowed topics and explicitly out-of-scope topics.
- Escalation triggers and support/contact path.
- Lead-collection behavior for presales or before escalation.
- Custom button or scheduling guidance when those actions are enabled.
- Skill usage lines: when to use each imported Skill and what questions it is meant to answer.
- External MCP usage lines: when to use the MCP server, what it may access, and when not to use it.
- Source-tag routing instructions when `retrieverTags` exist.

Do not duplicate the template's generic grounding, tool privacy, Markdown, link, or clarification rules. Do not move Instructions into Output Format or merge sections.

## Source Tag Prompt Pattern

Keep source-tag guidance token efficient, but do not use one fixed sentence for every bot. First identify why tags exist, then add the smallest routing instruction that prevents conflicting retrieval. The `search_documentation` tool schema already exposes available tag IDs and descriptions, so avoid repeating every tag description in the prompt.

Common patterns:

```text
For multiple products: When a question is about a specific product, filter search_documentation to that product's tag. If the product is unclear and answers may differ, ask which product they mean before searching. Leave untagged/global sources included unless they contain conflicting product-specific content.

For product versions: When a question names or implies a version, filter to that version tag. If the version is unclear and behavior may differ, ask for the version before answering. Search across all relevant version tags only for version comparison or migration questions. Set untagged to false only when untagged/global docs could conflict with the selected version.

For complementary categories: Use one or more tags when the question genuinely spans categories, such as billing plus API setup. Keep untagged/global sources included by default for shared context unless they are known to add noise or conflicts.
```

Tune the final line to the actual tag design:

- Prefer one-tag searches when tags separate conflicting products, versions, regions, or same-audience procedures.
- Allow multiple tags when tags represent complementary categories that should be combined for some questions.
- Treat untagged/global sources as included by default in search. Only instruct the bot to set untagged to false when untagged sources would conflict or add noisy non-authoritative content.
- Ask a clarifying question before searching when choosing the wrong tag could produce a conflicting answer.
- Use tag-specific prompt lines only when the tag descriptions and the generic routing rule are not enough.

Do not use source tags as a security or audience-isolation boundary. If sources are split between public and internal/private knowledge, or between customer-facing and staff-only procedures, create separate bots with separate source sets and deployment surfaces instead of relying on tag filtering.

## Verification

Before handoff:

- Read the saved bot and verify the prompt field actually changed.
- Confirm `agentPrompt`/`helpscoutPrompt` includes `search_documentation` when non-empty.
- Confirm the prompt preserves the selected template's major sections and only minimally customizes role/context/extra instructions.
- Confirm configured source tags have useful descriptions in retrieval/OpenAPI schema and the prompt contains compact routing guidance customized to why the tags exist, including whether one tag or multiple tags may be used and when untagged should be set to false.
- Confirm every enabled Skill, MCP connector, escalation, lead form, and custom action has a matching prompt instruction when user behavior depends on it.
- Confirm Help Scout prompts do not tell customers to escalate to support; the AI is acting as the support team draft/reply agent.
- Confirm public widget prompts do not promise actions or live facts that are not backed by sources, Skills, MCP, web search, or CTAs.
