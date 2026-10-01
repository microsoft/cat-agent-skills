# Response Quality Remediation Playbook

Choose remediations that match the primary diagnosis. Prefer the smallest durable change. Ask before writes unless the user already authorized that exact fix.

Product reference: [Improving Chatbot Response Quality](https://docsbot.ai/documentation/doc/improving-response-quality).

## 1. Fix or expand training sources

Use when knowledge is missing, stale, noisy, or unreadable.

- Add high-signal URLs, sitemap sections, documents, or connectors that contain the answer in extractable text.
- Prefer focused coverage over whole-blog crawls that drown retrieval in noise.
- Reingest or repair sources with failed status or zero chunks.
- Schedule refresh for fast-changing policy/pricing/status content.
- Replace image/video-only material with text or Q&A.
- Prove the fix with the [semantic search](semantic-search.md) matrix, not status alone.

## 2. Revise answer → Q&A source (preferred durable correction)

Use when a specific logged question should have a known-good answer going forward. This is the dashboard **Revise answer** workflow.

Durable path (do both steps when fixing from a question log):

1. Create or merge a Q&A source via `create_source`:

```json
{
  "type": "qa",
  "title": null,
  "url": null,
  "file": null,
  "scheduleInterval": "none",
  "faqs": [
    {
      "question": "<standaloneQuestion or clarified user question>",
      "answer": "<corrected answer the bot should use>"
    }
  ]
}
```

Creating another `qa` source may merge FAQs into the existing Q&A source and queue reingest—verify the returned source id/status.

2. Mark the question log as revised via `mark_question_revised` with `{ "revised": true }` so the dashboard shows the log as corrected.

Important:

- The Q&A `faqs` payload is what improves **future** responses after ingest.
- `revised: true` on the question document is the log flag that the revise workflow completed; it is not a substitute for the Q&A source.
- Avoid adding a FAQ that conflicts with an existing Q&A pair for the same question—conflicting answers confuse retrieval.
- Phrase FAQ questions like real user wording; add paraphrases when one pair is not enough.
- After save, confirm reingest and re-run semantic search for the question and a paraphrase.

## 3. Adjust custom prompts / agent instructions

Use when retrieval is fine but behavior, tone, boundaries, or tool use is wrong.

- Keep DocsBot grounding structure and `search_documentation` (for agent bots) intact.
- Add narrow instructions, for example:
  - Refuse off-topic questions politely and link to support.
  - When context lacks the answer, escalate or link to `supportLink`.
  - Prefer quoting product names/versions from retrieved sources.
- Avoid clever style constraints that fight factual answering unless the user wants them.
- Use the Prompt Debugger when custom instructions conflict or the bot misbehaves despite good sources.

Related docs: [Customize AI bot responses](https://docsbot.ai/documentation/doc/customize-ai-bot-responses), [Prompt Debugger](https://docsbot.ai/documentation/doc/how-to-use-the-prompt-debugger-to-fix-ai-agent-behavior).

Select the prompt from the answer channel, not from the current dashboard tab: `helpscoutPrompt` for Help Scout, `agentPrompt` for agent-mode text, `customPrompt` for legacy/non-agent text, and `voicePrompt` for voice/phone. Current Admin bot writes expose the voice text at `voiceAgent.instructions`; preserve all sibling voice settings.

## 4. Add or refine glossary rewrites

Use when the documentation contains the right fact under its official vocabulary, but users ask with a proprietary nickname, acronym, industry term, or non-standard translation. Load [glossary.md](glossary.md) for the A/B Semantic Search proof and safe full-array update workflow. Do not use glossary entries to compensate for missing facts or failed indexing.

## 5. Stronger model when context already has the answer

Use sparingly when logged sources clearly contain the answer but weaker models still miss or mangle it.

- Recommend a higher-capability model only with evidence that extraction/synthesis failed despite good context.
- Note higher token/API cost.
- Do not jump to model changes for missing knowledge—that wastes spend.

## 6. Increase context items

Use when semantic search shows the correct chunk exists but often ranks below the default top context window.

- Semantic Search returns 6 chunks by default. Product answer context may be configured separately, so use the logged `sources` as proof of what the model actually received.
- Dashboard Context Boost / Research-style modes can raise context (for example toward ~16).
- Widget: `contextItems` in embed options.
- API: `context_items` on chat requests.
- Tradeoff: more tokens and latency. Prefer cleaning sources/tags or adding Q&A first when noise or weak ranking is the real problem.

## 7. Fix tag routing

Use when multiple products, versions, or procedure families collide.

- Ensure `retrieverTags` keys/descriptions are discriminative.
- Assign sources to the right tags; do not tag every source with every key.
- Add compact prompt guidance for when to search with one tag, multiple tags, or exclude untagged sources.
- Validate with tagged vs untagged semantic search runs.
- Audience isolation (public vs internal) needs separate bots, not tags alone.

## 8. Actions, Skills, and live systems

Use when the user needed live or account-specific work.

- Prefer existing DocsBot actions/skills that fit (escalation, scheduling, billing tools, MCP connectors).
- Outline new Skill requirements only when no built-in fits; hand off to Skill Builder for implementation.
- Keep policy answers in docs/Q&A; keep stateful operations in tools.

## Ordering Heuristic

1. Repair failed/empty critical sources; prove with semantic search.
2. Revise via Q&A source (+ `revised: true` on the log) for the failing fact.
3. Fix tags/noise so the right chunk retrieves in top context.
4. Tighten prompt behavior.
5. Raise context items or model only with evidence.
6. Add actions/skills for live/operational gaps.

## What Not To Do

- Do not claim a source/Q&A fix is live while the source is still indexing with zero chunks—retest with semantic search.
- Do not call `put_..._questions_...` with only `revised` and skip the Q&A source create/merge when the goal is better future answers.
- Do not broaden the prompt to "answer from general knowledge" unless the user explicitly wants ungrounded answers.
- Do not delete logs or sources as a cleanup step unless authorized.
- Do not paste customer PII from logs into new public sources.
