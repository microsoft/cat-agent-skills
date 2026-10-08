---
name: docsbot-response-quality-admin-mcp
description: Use when analyzing DocsBot conversation or question logs to explain why the bot answered the way it did, diagnose retrieval or prompt failures, find knowledge gaps, and recommend concrete source, Q&A, prompt, model, or context fixes through the DocsBot Admin MCP.
---

# DocsBot Response Quality Admin MCP

Use this skill to diagnose why a DocsBot bot answered a question the way it did by inspecting conversation and question logs, the sources retrieved as context, current bot settings, and live semantic search against the training data.

Admin MCP exposes fixed named action tools plus optional metadata tools:

- `search_tools` and `get_tool_schema` for optional metadata inspection.
- The named Admin MCP tool for the authorized action, with its required `pathParams`, `query`, and/or `body`.

Call the named tool directly when known. Use `search_tools` or `get_tool_schema` only for unfamiliar advertised names or inputs.

This skill is the log-analysis and response-quality surface. It complements Bot Builder: use Bot Builder when creating or broadly reconfiguring a bot, and use this skill when the user wants a causal explanation of a specific answer, a cluster of bad answers, unanswered questions, escalations, or low ratings.

Canonical product guidance for improvement levers: [Improving Chatbot Response Quality](https://docsbot.ai/documentation/doc/improving-response-quality).

## Progressive Disclosure

Start with the user's evidence and live Admin MCP data, not reference files. The instructions in this `SKILL.md` are sufficient for the common single-answer review.

- **Do not preload references.** Never read every reference because this skill was activated, and never read a reference merely to prepare for later work.
- For a request that already includes a question-log ID or conversation ID, first call the narrow named question/conversation read. Inspect the logged answer and retrieved `sources` before deciding what else is needed.
- Load **at most one reference at a time**, only when the next concrete step requires detail that is not already in this file or the live MCP schema/result.
- Use the currently advertised named tools and their schemas for request shapes. `operations.md` is a fallback guide, not a prerequisite.
- Stop reading references as soon as the evidence supports a diagnosis and concrete recommendation.

Use this routing table selectively:

| Reference | Load only when |
| --- | --- |
| [workflow.md](references/workflow.md) | Scoping a cluster, ambiguous time window, or multi-incident analysis; skip for a single supplied ID. |
| [operations.md](references/operations.md) | The advertised tool schema did not make the required read/write operation or field contract clear. |
| [semantic-search.md](references/semantic-search.md) | You are about to run or interpret a retrieval-ranking matrix beyond one targeted semantic search. |
| [glossary.md](references/glossary.md) | A brand, product, acronym, industry term, or non-standard translation may be causing a query-to-document vocabulary mismatch. |
| [diagnosis.md](references/diagnosis.md) | Evidence supports multiple plausible causes or the user needs a formal root-cause classification. |
| [remediation.md](references/remediation.md) | A root cause is established and you need detailed remediation or mutation guardrails. |
| [handoff.md](references/handoff.md) | A complex or clustered analysis needs the full formal handoff shape; skip for a concise single-incident answer. |

## Operating Rules

- Resolve the target team and bot before reading logs. Prefer the current dashboard bot context when the user says "this bot" or does not name one.
- Prefer evidence from Admin MCP question/conversation reads and `search_bot_knowledge` over guesses about what the model "must have seen."
- Inspect the logged `sources` (retrieved chunks) for the question under review. Those chunks are the context the model actually received.
- Debug retrieval with the semantic search API (`search_bot_knowledge`): start with the standalone or raw question and compare live hits to the logged context. Expand to paraphrases, higher `top_k`, or tagged-vs-untagged searches only when the first result leaves the cause unclear. Source status alone is not proof of retrievability.
- Do not invent missing sources, chunk text, ratings, or escalation reasons.
- Redact or minimize customer PII in user-facing summaries. Quote only the log excerpts needed to justify the diagnosis.
- **Revise answer** is a durable fix: create/merge a `type: "qa"` source with the corrected FAQ (`create_source`), then mark the question log with `mark_question_revised` `{ "revised": true }`. The Q&A source improves future responses after ingest; the `revised` flag marks the log as corrected. Do not mark revised without creating the Q&A item when the goal is better future answers.
- Do not end on a report-only diagnosis when actionable remediations exist. After presenting the diagnosis and proposed fixes, explicitly ask whether the user wants you to apply those fixes now.
- Ask before mutations that change sources, prompts, models, or integrations unless the user already authorized that exact fix.
- Prefer minimal, high-leverage recommendations ordered by likely impact: missing/bad sources → revise→Q&A → prompt boundary → model/context → actions/skills.

## Correctness And Prompt-Controllability Review

Every single-answer diagnosis must explicitly check the answer for hallucinations, unsupported claims, invented policies or contact details, fabricated tool/action results, incorrect citations or procedural steps, and contradictions with the logged sources or conversation context.

- If the answer is correct or mostly correct, say what worked instead of inventing a failure.
- If a claim cannot be verified from the available answer, sources, conversation, and tool evidence, classify it as **unsupported**, not proven false. Call it false only when the supplied evidence directly contradicts it.
- Separate the primary cause from secondary contributors. Explain likely causes without claiming certainty that the evidence does not support.

Classify whether prompt instructions can reasonably improve the observed behavior before recommending a prompt edit:

- **Prompt-controllable:** retrieval/search timing guidance, source-grounding rules, tool triggering, tool arguments, escalation rules, role/persona, tone, answer format, clarification behavior, refusal boundaries, and missing-information behavior.
- **Not prompt-controllable:** missing or stale training data, missing logged context, unreadable/non-text sources, disconnected or unavailable tools, API/runtime failures, and cases where the bot could not know the answer from the available evidence.
- Recommend or apply a prompt edit only for the prompt-controllable portion. Do not put source creation, missing-document advice, account-data gaps, tool availability, or backend/API fixes into a prompt-debug instruction.
- Identify the actual prompt surface before proposing an edit. Help Scout auto-reply logs use `helpscoutPrompt`; agent-mode text answers use `agentPrompt`; legacy/non-agent text surfaces use `customPrompt`; voice and phone answers use `voicePrompt`. In the current Admin bot object, the editable voice prompt is exposed as `voiceAgent.instructions`; preserve the rest of the `voiceAgent` object when updating it. Do not edit a different prompt merely because it is easier to find.
- Determine the answer channel from the log evidence before choosing a prompt. For a question object, follow `conversationId` and read the conversation when available. Use only the conversation's top-level `channel`; do not infer a channel from question or conversation metadata. If the linked conversation or its channel is unavailable, report the channel as unknown rather than guessing the prompt surface. Treat `voice` and `phone` as voice-prompt channels. The `testing` flag describes staff testing and does not by itself select a prompt surface.

## Analysis Flow

Use this sequence for a single answer or a small set of related failures:

1. Identify the bot and the target question(s) or conversation(s): IDs from the user, dashboard deep links, recent unanswered/escalated/low-rated filters, or semantic question-log search.
2. Read the question log entry (and conversation transcript when needed). Capture question text, `standaloneQuestion`, answer, `couldAnswer`, rating, escalation, model if present, and the retrieved `sources` array with chunk content.
3. Classify the failure mode from the evidence: missing knowledge, weak retrieval, context present but unused, prompt/policy conflict, wrong audience/tag routing, non-text source content, or action/skill gap. Load `diagnosis.md` only if the evidence leaves multiple plausible classes.
4. Reproduce retrieval with one targeted `search_bot_knowledge` call using the standalone or raw question and the default `top_k: 6`. Expand to a query matrix—and load `semantic-search.md`—only if the first comparison does not distinguish the cause. When helpful, inspect source status/chunk counts for suspected documents. If the mismatch centers on a proprietary term, acronym, industry phrase, or non-standard translation, load `glossary.md` and compare the same search with `use_glossary: false` and `true`.
5. Read current bot settings that affect answers: prompt/`agentPrompt`, model, retriever tags, enabled tools/actions, and deployment surface.
6. Recommend the smallest concrete remediation supported by the evidence. Load `remediation.md` only when detailed fix or mutation guardrails are needed. Apply only authorized fixes; otherwise hand off dashboard deep links and exact next steps.
7. Deliver a concise diagnosis: what happened, why, evidence, recommended fixes, and how to verify. Load `handoff.md` only for a complex or clustered report that needs its formal structure.
8. If there are fixes or improvements you can make (sources, revise→Q&A, prompt, model, context, or similar), end by asking the user whether they want you to apply the proposed changes. Skip that ask only when there are no actionable remediations, the user already authorized the exact fix, or the only next steps are dashboard-only / Skill Builder handoffs you cannot perform.

For cluster analysis (knowledge gaps, recurring escalations, rating dips):

1. Filter or semantically search question logs for the pattern (`couldAnswer=false`, escalated, low rating, topic query, date range).
2. Sample enough examples to name 3–7 clusters; do not dump raw logs.
3. For one representative question per major cluster, run the single-answer flow above.
4. Prioritize remediations that close the largest clusters first.

## References

- [workflow.md](references/workflow.md): Intake, log selection, reproduction, and verification workflow.
- [operations.md](references/operations.md): Admin MCP named tools for questions, conversations, search, sources, Q&A, and prompts.
- [semantic-search.md](references/semantic-search.md): How to use the semantic search API to debug retrieval and indexing.
- [glossary.md](references/glossary.md): How glossary rewrites address vocabulary mismatches, how to verify them with Semantic Search, and how to update entries safely.
- [diagnosis.md](references/diagnosis.md): Root-cause taxonomy and evidence checks.
- [remediation.md](references/remediation.md): Source, revise→Q&A, prompt, model, context-item, and action fixes.
- [handoff.md](references/handoff.md): Required final diagnosis shape and dashboard deep links.

## Source Anchors

Use current public DocsBot docs and live MCP catalog as source of truth:

- Improving response quality: `https://docsbot.ai/documentation/doc/improving-response-quality`
- Customize AI bot responses / prompts: `https://docsbot.ai/documentation/doc/customize-ai-bot-responses`
- Prompt Debugger: `https://docsbot.ai/documentation/doc/how-to-use-the-prompt-debugger-to-fix-ai-agent-behavior`
- Reports and analytics: `https://docsbot.ai/documentation/doc/docsbot-ai-reports-and-analytics`
- Chat / widget context items: `https://docsbot.ai/documentation/developer/embeddable-chat-widget` and `https://docsbot.ai/documentation/developer/chat-api#parameters`
- Admin MCP: `https://docsbot.ai/documentation/developer/mcp-server`

If docs, code, and live MCP behavior disagree, state the conflict and follow live MCP validation for the immediate diagnosis.
