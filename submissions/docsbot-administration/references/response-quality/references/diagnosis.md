# Response Quality Diagnosis Taxonomy

Classify each incident or cluster into one primary root cause. Secondary contributors are allowed, but the recommended fix should target the primary cause first.

Ground this taxonomy in the logged retrieved sources, live semantic search, and current bot settings—not in speculation about the model.

## Root Causes

### 1. Missing knowledge

**Signals**

- Logged `sources` are empty, off-topic, or clearly lack the fact needed.
- Live `search_bot_knowledge` also fails to return a chunk that answers the question.
- `couldAnswer` is false, or the answer admits it does not know / escalates.

**Likely fixes**

- Add or refresh the right source (docs URL, sitemap section, file, connector).
- Revise the logged question into a Q&A source pair (durable future-answer fix), or add FAQ paraphrases.
- Fix failed/zero-chunk sources; confirm with the semantic search matrix.

### 2. Weak or wrong retrieval

**Signals**

- The answer exists in training data (live search finds it) but logged `sources` missed it or ranked noise higher.
- Wrong product/version/region chunks appear; tags exist but routing is wrong or unused.
- Query is multi-turn and `standaloneQuestion` is missing or poorly rewritten relative to the conversation.

**Likely fixes**

- Improve source quality/structure; remove noisy sources.
- Fix retriever tags and prompt routing guidance; validate with tagged vs untagged semantic search.
- Revise into a focused Q&A so the correct answer is easy to retrieve.
- Increase context items when semantic search shows the right chunk only at higher `top_k`.

### 3. Context present but unused or mishandled

**Signals**

- Logged `sources` already contain the correct answer text.
- The bot still refuses, hallucinates a conflicting answer, or only partially uses the chunk.

**Likely fixes**

- Prompt clarification (how to use context, when to quote, when to refuse).
- Stronger model when extraction/synthesis from long context is the bottleneck.
- Prompt Debugger for contradictory custom instructions.
- Do **not** treat this as a missing-source problem.

### 4. Non-text or unreadable source content

**Signals**

- Expected page/file is indexed but chunks are empty, boilerplate-only, or missing the visual content.
- Knowledge lives in images, screenshots, video, or scanned PDFs without extractable text.

**Likely fixes**

- Paste critical facts into a Q&A or text/document source.
- Replace image-heavy pages with text-equivalent docs.
- Re-scrape or upload a cleaner file source.

### 5. Prompt or policy conflict

**Signals**

- Custom instructions force refusals, wrong persona, or "only answer from X" rules that block a valid docs answer.
- Bot answers out of scope when it should refuse, or refuses in-scope questions.
- Tone/format issues despite correct facts.

**Likely fixes**

- Narrow custom prompt edits; keep grounding/`search_documentation` guardrails.
- Use Prompt Debugger.
- Add explicit escalation/support-link instructions when out-of-knowledge.

### 6. Action / skill / live-data gap

**Signals**

- Question requires account-specific, real-time, or write behavior (order status, refund, schedule, ticket) that docs cannot answer.
- Logs show docs-only answers or escalations for operational requests.

**Likely fixes**

- Enable or configure built-in actions, Skills, or MCP connectors.
- Hand off to Bot Builder / Skill Builder when a new capability is required.
- Keep docs answers for policy; use actions for live state.

### 7. Expected refusal or correct escalation

**Signals**

- Question is out of scope, abusive, or unsupported; sources correctly empty; prompt says to refuse or escalate.
- Human handoff is the right outcome.

**Likely fixes**

- Usually none. Optionally improve refusal copy or support URL.
- Do not add Q&A that teaches the bot to invent out-of-scope answers.

## Evidence Checklist

For every primary diagnosis, state:

1. What the user asked (and standalone form if different).
2. What the bot answered and the outcome flags.
3. Whether the needed fact appeared in logged `sources`.
4. Whether live training-data search finds it now.
5. Which single remediation class should run first.
6. Whether any answer claim is contradicted, unsupported, or verified by the supplied evidence.
7. Whether the issue is prompt-controllable; if so, which prompt surface and behavior category controls it.

## Prompt-Control Categories

Use one of these labels when a prompt edit is relevant: retrieval, tool triggering, tool arguments, escalation, tone/persona, formatting, clarification, or safety/refusal boundaries. Use **not prompt-controllable** for knowledge gaps, missing context, unavailable tools, and runtime failures.

Prompt edits may address only the controllable behavior. Keep source, indexing, account-data, and backend fixes in their own remediation steps.

## Severity

- **Critical:** bot invents dangerous/policy-breaking guidance, or exposes secrets/PII from logs in the agent reply.
- **Major:** systematic unanswered cluster for a core product topic; correct chunk consistently retrieved but ignored; failed critical source.
- **Minor:** tone/format issues; rare one-off questions; already-correct refusals.
