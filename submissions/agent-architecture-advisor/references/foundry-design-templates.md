# Foundry Design Templates

Decision trees for producing the Foundry target design in `EXTEND` and `MIGRATE` verdicts.

**Scope boundary:** produce a target-state *specification*, not implementation guidance.
No code, no SDK walkthroughs, no deployment scripts. The output is what an architect
hands to an engineering team, not what the engineering team writes. This boundary is
what keeps the skill from expanding indefinitely.

---

## 1. Model selection

Work through these in order. The default answer is "smaller than you think."

```
Does the task need reasoning across multiple retrieved passages,
or multi-step planning?
├── No  → smallest capable tier. Test it before assuming it fails.
└── Yes → mid tier. Escalate only on measured failure.

Is output latency-critical (< 1s p95)?
├── Yes → smallest capable tier + aggressive context reduction
└── No  → tier by quality need

Is there a reproducibility or compliance requirement?
└── Yes → pin the model version explicitly and state the pinning policy
```

**Recommend evaluating a smaller model rather than defaulting to the largest.** On
well-grounded tasks the quality difference is frequently smaller than the cost
difference, and teams rarely test this. Frame it as: *start one tier below your
instinct, measure, escalate only on evidence.*

State the selection with reasoning and per-conversation cost implication. A model
recommendation without cost attached is incomplete.

---

## 2. RAG vs fine-tune vs prompt engineering

The most commonly mis-answered question in agent design. Fine-tuning is reached for far
more often than it is warranted.

```
Is the gap knowledge (the model does not know facts)?
└── Yes → RAG. Fine-tuning does not reliably add retrievable facts.

Is the gap behaviour (format, tone, task-specific structure)?
├── Can it be specified in a prompt?
│   └── Yes → prompt engineering. Try this first, always.
└── Is the behaviour complex, consistent, and high-volume?
    └── Yes → consider fine-tuning, but only after prompt engineering
              has demonstrably failed and you have training data

Is the gap reasoning (the model cannot work the problem)?
└── Yes → model tier change or decomposition into steps. Neither RAG
          nor fine-tuning fixes reasoning capacity.
```

**Default recommendation: RAG plus prompt engineering.** Fine-tuning is justified only
with a demonstrated prompt-engineering failure, a stable high-volume task, and available
training data. Say this plainly — it saves teams months.

---

## 3. Azure AI Search index design

Required whenever CEIL-02 drove the verdict. Specify all five.

### Chunking

| Document type | Strategy |
|---|---|
| Uniform prose | Fixed size (~500 tokens) with ~10% overlap |
| Structured (headings, sections) | Structure-aware — chunk on section boundaries |
| Tables and data | Preserve table integrity; chunk by row group, never mid-table |
| Mixed corpus | Per-source strategy; do not force one policy across varied sources |

Mixed corpora with a single chunking policy is the most common root cause behind
CEIL-02 assertions. If the target design does not address this, the migration will
reproduce the original problem on a more expensive platform.

### Retrieval mode

```
Do queries use domain vocabulary, IDs, or exact terms?
├── Yes → hybrid (vector + keyword). Pure vector loses exact matches.
└── No  → vector may suffice, but hybrid is a safe default

Are there many near-duplicate documents (versions, regional variants)?
└── Yes → semantic re-ranking is necessary, not optional

Do users ask compound questions?
└── Yes → query decomposition
```

### Metadata and filtering

Define the filter schema explicitly — source system, document type, date, owning
department, sensitivity. **Filtering is the cheapest available quality lever** and it is
what CFG-06/DSN-04 failures were missing. Specify which fields are filterable and which
topics filter on what.

### Freshness

Map the `knowledge.freshness_sla` requirement to an indexing strategy: scheduled
reindex, change-feed-driven incremental, or event-triggered. State the expected staleness
window — teams need to know how out-of-date an answer can be.

### Cost

Search tier is a **standing** cost, independent of conversation volume. Call it out
separately in the cost section — at low volume it can exceed model inference cost
entirely, and it does not scale down during quiet periods.

---

## 4. Evaluation harness

Required whenever CEIL-04 drove the verdict.

**Metrics** — select what matters for the use case rather than measuring everything:

| Metric | Measures | Use when |
|---|---|---|
| Groundedness | Is the answer supported by retrieved context? | Always, for RAG |
| Relevance | Does it address the question? | Always |
| Retrieval precision | Are retrieved chunks on-topic? | Diagnosing CEIL-02 fixes |
| Coherence | Is it well-formed? | Long-form output |
| Task success | Did the workflow complete? | Action-taking agents |
| Safety | Policy compliance | Regulated domains |

**Dataset** — specify size (start ~50–100 cases), composition (happy path, edge cases,
adversarial, known past failures), and ownership. The last one is what determines whether
the harness survives contact with a busy team.

**Thresholds and gating** — define pass thresholds per metric, what blocks deployment,
and what merely warns. A harness with no gate is a dashboard nobody reads.

**Regression baseline** — snapshot current scores before any change, so improvement is
measurable rather than asserted.

---

## 5. Content safety

Map `governance.content_safety_tier`:

| Tier | Configuration |
|---|---|
| `standard` | Default filters, input and output |
| `strict` | Elevated thresholds, custom blocklists, jailbreak detection |
| `regulated` | Above, plus mandatory citation enforcement, full logging, human review path for flagged content |

For `regulated`, the citation enforcement is what closes GOV-01. State it explicitly in
the target design — it is a requirement, not a nice-to-have.

---

## 6. Observability

Specify four things:

- **Tracing granularity** — conversation, turn, or reasoning-step. `full_trace`
  auditability (GOV-05) requires step-level.
- **Retention** — driven by the audit requirement and privacy constraints; state both.
- **Alerting** — error rate, latency p95, cost per day, groundedness score drift.
- **Cost attribution** — tag by topic or workflow so cost regressions are traceable to a
  cause rather than showing up as an unexplained bill.

---

## 7. Migration phasing (MIGRATE only)

Never recommend a big-bang migration. Structure as:

**Phase 0 — Measure.** Instrument the existing agent. Establish quality and cost
baselines. Nothing moves. This phase is skipped constantly and its absence is why teams
cannot tell whether the migration helped.

**Phase 1 — Highest-ceiling, lowest-risk slice.** Move the workload that most clearly
exceeds the ceiling and has the smallest blast radius. Run parallel. Compare against
baseline.

**Phase 2 — Expand on evidence.** Move further workloads only after Phase 1 demonstrates
improvement against the baseline.

**Phase 3 — Decommission.** Only after all traffic has moved and stabilised.

Each phase needs: scope, success criteria, rollback trigger, and duration estimate.

**State what is lost.** Channel integrations, M365 auth, maker accessibility, governance
inheritance, and elapsed engineering time. A migration plan that lists only benefits is
not credible to anyone who has run one, and it is the fastest way for a good
recommendation to be dismissed.
