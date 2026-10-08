# Response Quality Analysis Workflow

## Intake

Start by locking the scope before reading large log pages.

Clarify only what changes the diagnosis:

- Which bot (use current dashboard bot when unambiguous).
- Single incident vs pattern: one question/conversation ID, a pasted Q&A, or a cluster ("unanswered last week", "bad refund answers", "escalations about shipping").
- Success criteria: explain-only, recommend fixes, or apply authorized remediations. Default after analysis: if actionable fixes exist, ask whether to apply them before stopping.
- Time window when the user talks about "recent" without dates.

Do not ask for details Admin MCP can load: bot name, recent unanswered counts, source list, or prompt text.

## Select Evidence

Prefer the narrowest evidence that answers the user's question.

| User intent | First reads |
| --- | --- |
| Why this answer? | Question log entry by ID, or semantic question search with the pasted question text; then conversation transcript if multi-turn. |
| Unanswered / could not answer | `list_questions` with `couldAnswer=false` and an optional date range. |
| Escalations | Filter `escalated=true` (and often `couldAnswer=false`). |
| Low ratings | Filter by `rating` for thumbs-down / low scores. |
| Topic cluster | `search_question_logs` with the topic phrase, then sample hits. |
| Aggregate quality | Bot reports/stats first, then drill into representative questions. |

Always capture for each reviewed question:

- `id`, `question`, `standaloneQuestion` (prefer this for retrieval reproduction when present)
- `answer`, `couldAnswer`, `rating`, `escalated` / `escalation`
- `sources[]` with titles/URLs and chunk text when returned
- `createdAt` and any model/metadata fields present
- `conversationId`; when present, read only the conversation's top-level `channel` before selecting `customPrompt`, `agentPrompt`, `helpscoutPrompt`, or `voicePrompt`. If no channel is available, leave the prompt surface unknown rather than inferring it from metadata.

## Reproduce Retrieval With Semantic Search

After reading the logged context, load [semantic-search.md](semantic-search.md) and debug with `search_bot_knowledge` (the Admin MCP semantic search API / dashboard Search tool):

1. Run the query matrix: standalone question, raw question, 1–2 paraphrases, default `top_k: 6`, higher `top_k` (10–16), and tagged vs untagged when tags exist. When a proprietary term, acronym, industry phrase, or non-standard translation may be responsible, compare the same query with `use_glossary: false` and `true` using [glossary.md](glossary.md).
2. Compare live top hits to the logged `sources`.
3. If live search finds the right chunk but the log did not, treat it as a retrieval/config/time-skew issue (source added later, tags, indexing state, or different query rewriting).
4. If the chunk only appears at high `top_k`, treat it as ranking/context-window pressure (noise above the useful chunk, or need more `context_items` / a Q&A boost).
5. If neither live search nor the log contains the answer—even for a title/URL phrase query—treat it as a knowledge/indexing gap (missing, failed, unreadable, or still indexing).
6. If the right chunk was in the logged sources but the answer ignored or contradicted it, treat it as synthesis/prompt/model issue—not a missing-source issue.

DocsBot cannot extract answers from images, video, or non-textual document elements. If the "correct" content only exists as screenshots or scanned images without OCR text, classify as non-text source content and recommend a text/Q&A/file replacement.

## Inspect Bot Configuration

Read the bot when the failure mode implicates settings:

- Prompt / `agentPrompt` / custom instructions and grounding rules
- Model selection when answers miss content that is clearly in context
- `retrieverTags` and source tag assignments when wrong product/version content appears
- Enabled tools/actions/Skills when the user needed a live lookup or write the bot cannot do from docs alone
- Source statuses: failed, zero chunks, still indexing, stale schedules

## Cluster Path

When analyzing many logs:

1. Pull a bounded sample (for example one page of 50, or semantic search top results).
2. Group by intent/topic, not by exact wording.
3. Pick one representative per major cluster and run full diagnosis.
4. Quantify roughly ("about 12 of 40 unanswered were refund policy") without inventing precise analytics the API did not return.
5. Recommend cluster-level remediations before one-off edits.

## Verification

After recommending or applying a fix:

1. Re-run the semantic search matrix for the original question and a paraphrase; confirm the expected chunk ranks in the default top context window.
2. Point the user to dashboard Chat or Search to confirm the full answer.
3. If you revised into Q&A or added sources, note indexing/reingest may still be pending—do not claim the live bot already changed until semantic search returns the new chunks.
4. Prefer navigating to `bot_questions`, `bot_sources`, or configure/system pages when dashboard navigation is available.
