# Token Optimization (advisory)

Advisory techniques for reducing per-turn token consumption on the Foundry side and
consumption weight on the Copilot Studio side. **Advisory, not prescriptive:** these are
options presented with expected impact and trade-offs, never changes the skill applies on
its own. The user decides what to adopt.

- **advisory-date:** 2026-08
- **applies to:** Foundry cost (token-based) primarily; Copilot Studio (weight-based) secondarily

---

## 1. Where this fits

This file supports **C3 (cost)** and any `COST`-class finding. It does not create findings
and it never changes a verdict — reducing tokens lowers the cost of the current
architecture; it does not remove a capability ceiling. If a `CEILING` finding exists, token
optimization is a complement to the migration/extend recommendation, not a substitute for
it. Say so when both apply.

The techniques map directly onto the four token levers the cost model already prices, so
every recommendation ties to a number the report has already produced rather than a generic
tip:

| Cost-model lever | Default per turn | Typical share | Primary techniques |
|---|---|---|---|
| `context` (retrieved) | 2000 | largest | §3 retrieval trimming |
| `history` (conversation) | 1500 | second | §4 history management |
| `system` (instructions) | 500 | fixed every turn | §5 prompt compression |
| `completion` (output) | 400 | smallest | §6 output shaping |

**Order of attack:** always context first, then history, then system, then completion.
That is strict descending order of impact, and it is also descending order of risk — context
and history trimming are near-free; system and output changes can affect answer quality and
need eval coverage.

---

## 2. How to present these

For each technique the report recommends, give four things and no more:

1. **Lever** — which token component it reduces
2. **Expected impact** — a band, derived from the cost model's own token split, not a
   made-up percentage
3. **Trade-off** — what quality or behaviour risk it introduces (every technique has one)
4. **Verification** — how to confirm it did not degrade answers (usually: an eval on the
   affected topics)

Never present a stack of techniques as additive without saying so. Savings compound
multiplicatively, not by addition — cutting context 40% and history 30% is not "70% off,"
and claiming it is destroys the credibility of the whole cost section.

Cap the advisory at the **three highest-impact techniques** for the specific agent. A
list of twelve generic tips reads as filler; three tied to this agent's measured token
split reads as analysis.

---

## 3. Context lever — retrieval trimming (highest impact)

Retrieved context is the largest per-turn term and the cheapest to cut. Techniques, in
order of preference:

**Reduce chunk count (top_k).** Most RAG configs retrieve more chunks than the answer
uses. Dropping from 5 chunks to 3 cuts context roughly 40% for a proportional cost cut.
- *Trade-off:* risk of dropping the chunk that held the answer. Verify groundedness on a
  sample before and after.
- *When:* almost always worth testing; the default top_k is rarely tuned.

**Tighten chunk size.** Oversized chunks carry padding. Right-sizing to the actual answer
granularity reduces tokens without dropping recall.
- *Trade-off:* chunks too small lose surrounding context needed to interpret a passage.

**Add re-ranking, then retrieve fewer.** A re-ranker lets you retrieve a small number of
*high-relevance* chunks instead of a large number of *maybe-relevant* ones — often the
biggest single win, because it cuts context and improves groundedness at once.
- *Trade-off:* re-ranking adds a step (latency, and on Foundry a small cost of its own);
  net positive at volume, marginal at low volume.
- *Note:* if the agent needs a custom retrieval pipeline to do this well, that may itself
  be a `CEIL-02` signal — flag it, don't bury it here.

**Metadata pre-filtering.** Filter the index by source, date, or department *before*
semantic search so retrieval draws from a smaller, on-topic set. Cuts both cost and
cross-domain noise.
- *Trade-off:* requires a filterable index schema; a design change, not a config toggle.

---

## 4. History lever — conversation management

The second-largest term, and it grows every turn — so its share rises in longer
conversations, which is exactly where cost concentrates.

**Sliding window.** Keep the last N turns verbatim, drop older ones. Simple, predictable.
- *Trade-off:* the agent forgets early context; wrong for tasks that reference the start of
  a long conversation.

**Running summary.** Replace old turns with a compact summary carried forward.
- *Trade-off:* summarization itself costs tokens and can lose specifics; worth it only when
  conversations are long enough that the summary is smaller than what it replaces.

**Selective history.** Carry only turns relevant to the current intent, not the full
transcript.
- *Trade-off:* relevance selection can misjudge; safest when turns are cleanly separable.

**Reset on topic change.** When the user clearly switches goals, start fresh rather than
dragging the prior thread.
- *Trade-off:* none if the switch is genuine; annoying if it misfires mid-task.

---

## 5. System lever — prompt compression (fixed cost, every turn)

The system prompt is smaller but paid on *every* turn, so trimming it compounds across the
whole volume. This is the lever most often bloated and least often reviewed.

**Remove redundant instructions.** Long system prompts accumulate overlapping rules.
Deduplicate.
- *Trade-off:* low, if done carefully; test that behaviour holds.

**Move examples to retrieval.** Few-shot examples baked into every system prompt are paid
every turn. If they are only needed sometimes, retrieve them on demand instead.
- *Trade-off:* adds a retrieval step; net win only if examples are large and
  intermittently needed.

**Externalize reference data.** Long lists, tables, or policy text embedded in the prompt
belong in a knowledge source, fetched when relevant.
- *Trade-off:* a design change; the payoff scales with how much static text is currently
  inlined.

**Caution:** system-prompt edits change behaviour on every turn. This lever has the widest
blast radius per token saved. Require eval coverage before recommending aggressive
compression — the savings are real but the risk is real too.

---

## 6. Completion lever — output shaping (smallest impact)

The smallest term; optimize last and only when the others are exhausted.

**Constrain length.** Ask for concise answers where verbosity adds no value.
- *Trade-off:* under-constrained cuts can drop needed detail.

**Structured output over prose.** For system consumers, a compact schema beats a
paragraph — fewer tokens and more reliable parsing. (If a downstream system requires strict
schema, that may be a `CEIL-06` signal — note it there.)
- *Trade-off:* none for machine consumers; worse for human readers who want explanation.

**Stop sequences.** Prevent the model from over-generating past the useful answer.
- *Trade-off:* a badly placed stop truncates good output; test it.

---

## 7. Copilot Studio side (weight-based, not token-based)

Copilot Studio consumption is weighted per interaction type, not per token, so the levers
differ. The cost model already prices these weights; the highest-value moves are:

**Convert deterministic generative topics to classic.** A generative turn carries roughly
10–12× the weight of a classic response. Topics with a fixed answer do not need generative
handling. This is usually the single largest Copilot Studio saving and overlaps `COST-01`
and `COST-04` — reference those findings rather than repeating them.

**Cut retry burn.** Trigger collisions and missing fallbacks cause extra generative turns
before escalation. This is a `COST-02` / `CFG-01` root cause; fixing the config removes the
cost. Point at the existing finding.

**Scope grounding.** Grounding invoked on topics that do not need it (`COST-04`) adds
retrieval weight for no benefit.

Note the pattern: on the Copilot Studio side, token optimization is mostly *already covered*
by existing COST/CONFIG findings. Do not create parallel recommendations — cross-reference.

---

## 8. What not to claim

- **Never present token optimization as a substitute for resolving a `CEILING`.** It lowers
  the cost of the current design; it does not raise the platform's capability.
- **Never stack percentages additively.** Compounded savings multiply.
- **Never recommend a technique without its trade-off.** Every one has a cost in quality,
  latency, or engineering effort. A tip with no downside is not analysis.
- **Never recommend aggressive system-prompt or output cuts without eval coverage.** These
  change behaviour; unverified, they trade cost for silent quality regression.
- **Never invent the impact number.** Derive the band from the cost model's own token split
  for this agent. If the cost model did not run (Mode A with no artifact), say the impact is
  directional and un-quantified.
