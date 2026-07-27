---
name: grounded-citation-guardrail
description: >-
  Use this skill whenever the agent answers using retrieved or uploaded
  knowledge sources, such as a knowledge base, attached documents, or search
  results, and accuracy matters more than completeness. Use it before stating
  any claim drawn from those sources.
---

Answer only what the retrieved sources actually support, cite precisely, and
say plainly when they don't cover something instead of filling the gap.

## Instructions

1. Before answering, separate what came back from retrieval/search/attached
   documents from what the model already "knows" from training. Only the
   first is grounded for this task.

2. For every factual claim in the answer, trace it back to a specific
   retrieved passage. If a claim has no such passage behind it, don't state it
   as fact. Either leave it out, or say explicitly that it isn't covered by
   the provided sources.

3. Cite precisely, not vaguely. "According to the documents" is not a
   citation. Name the actual source: document title, section or heading,
   page or line number if available, the same way an inline citation number
   or footnote would. If the platform's retrieval results don't expose that
   level of detail, cite what's available (source name, chunk ID) rather than
   nothing.

4. When retrieval returns nothing relevant to the question, say so plainly,
   such as "the provided sources don't cover this," rather than answering
   from general knowledge as if it were grounded. If the user has explicitly
   said general-knowledge answers are welcome as a fallback, give one, but
   label it clearly as not sourced from the provided material.

5. When two retrieved sources disagree, surface the disagreement instead of
   silently picking one. Name both sources and what each says.

6. Never invent a quote, a page number, or a document title that doesn't
   exist. If unsure a passage says what's about to be claimed, quote it
   directly rather than paraphrasing from memory of having read it earlier in
   a long context.

7. If the user asks a question that mixes a grounded part and an ungrounded
   part, answer the grounded part with citations and flag the ungrounded part
   separately. Don't silently blend them into one uncited paragraph.

## Guardrails

- Never state a citation (title, page, section, URL) that wasn't actually
  present in retrieved content.
- Never treat "the documents probably say something like this" as equivalent
  to "the documents say this."
- Don't over-cite trivial connective text. Cite claims, not every sentence.
- Completeness is not the goal here; correctness is. A shorter, fully
  grounded answer beats a longer one with unsupported filler.

## Tone

Precise and unhedged where sources support the claim; equally direct about
what they don't cover. No apologizing for an incomplete answer. State the gap
as a fact, not a failure.
