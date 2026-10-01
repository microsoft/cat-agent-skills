# Glossary Retrieval Diagnosis And Updates

Load this reference only when the likely failure is a vocabulary mismatch between the user's wording and the terminology in indexed content.

Product reference: [Glossary – Improve Search Relevance with Smart Term Replacement](https://docsbot.ai/documentation/doc/glossary-improve-search-relevance-with-smart-term-replacement).

## What The Glossary Does

Each bot glossary entry maps a user term (`word`) to the official or searchable vocabulary (`translation`). DocsBot rewrites matching terms in the query before retrieval. The original user input remains in logs, while `standaloneQuestion` can show the rewritten form used for search.

Glossary is a strong fit for:

- Brand or product nicknames that do not appear in the docs.
- Internal abbreviations and acronyms whose expanded form appears in sources.
- Industry-specific vocabulary that users and documentation express differently.
- Regional wording, slang, or non-standard cross-language translations that ordinary multilingual semantic similarity misses.

Do not add entries for every common synonym or standard translation. Do not use glossary to cover missing facts, stale content, failed/empty sources, tool failures, or a correct chunk that the model ignored.

Matching is case-insensitive and normally whole-word based. Japanese, Chinese, and Korean text may match within longer phrases because word boundaries differ. Keep replacements short, natural in the surrounding query, and aligned with exact vocabulary present in the bot's sources.

## Verify With Semantic Search

Use `search_bot_knowledge`. The Semantic Search default is `top_k: 6`.

1. Run the original user query with glossary disabled:

```json
{ "query": "<original user wording>", "top_k": 6, "use_glossary": false }
```

2. Run the exact same query with glossary enabled:

```json
{ "query": "<original user wording>", "top_k": 6, "use_glossary": true }
```

3. Compare whether the expected source/chunk appears, its rank, and whether it contains the needed fact. Keep tags, `alpha`, and every other search input identical so glossary is the only variable.
4. Inspect the question log's raw `question` and `standaloneQuestion`. A glossary rewrite may explain why the standalone form differs from the user's words.
5. If both runs fail, try the official replacement phrase directly at `top_k: 6`. If that also fails, glossary is not the root fix: inspect indexing, source content, bot selection, and tags.

A successful glossary fix moves the expected chunk into the default top-six window for the original user wording with `use_glossary: true`. It is not enough for the replacement phrase alone to work.

## Update The Glossary Safely

Glossary is available on Standard and eligible legacy plans. Discover current schemas before writing.

1. Read the bot with `get_bot` and capture the complete current `glossary` array.
2. Propose the smallest mapping supported by failed-log evidence, for example `{ "word": "DMP", "translation": "DocsBot Management Portal" }`.
3. Ask before the mutation unless the user already authorized this exact glossary change.
4. Merge the entry into the existing array and update the bot with `update_bot`. Preserve every unrelated entry; bot updates replace the supplied glossary array.
5. Treat `word` duplicates case-insensitively. Update the existing mapping instead of creating variants such as `DMP` and `dmp`.
6. Re-run the off/on A/B searches above and report ranks. Then retest the full bot answer through the original channel.

Example minimal bot update body after merging with existing entries:

```json
{
  "glossary": [
    { "word": "<existing term>", "translation": "<existing replacement>" },
    { "word": "<observed user term>", "translation": "<official source vocabulary>" }
  ]
}
```

Never send only the new entry if other glossary entries already exist. Never claim the fix worked until the original wording retrieves the expected chunk with glossary enabled.
