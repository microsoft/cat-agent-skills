# Grounded Citation Guardrail

A discipline skill for RAG-style setups: answering from a knowledge base,
attached documents, or search results. It enforces one rule: every claim
traces back to a specific retrieved passage, cited precisely, or it doesn't
get stated as fact.

## How it fits with other knowledge skills in this gallery

[`knowledge-source-router`](../knowledge-source-router) decides *which*
regional source to search. [`knowledge-corpus-curator`](../knowledge-corpus-curator)
cleans up *what's in* the knowledge base beforehand. This skill is the third
piece: discipline at *answer time*. Once retrieval has happened, don't let
the answer drift past what was actually retrieved.

## What "grounded" means here

- A citation names an actual document/section/page, not "the documents say."
- No claim without a traceable source.
- No answer from general knowledge presented as if it were sourced.
- Disagreement between sources gets surfaced, not silently resolved.
- "Not covered by the provided sources" is a complete, acceptable answer.

## What it won't do

It can't verify a source is *correct*, only that the answer accurately
reflects what the source *says*. Garbage in the knowledge base still produces
garbage out. Grounding protects against fabrication, not against a badly
curated corpus.

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
