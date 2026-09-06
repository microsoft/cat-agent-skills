---
name: agent-performance-triage
description: Diagnose a live Microsoft Copilot Studio agent from its analytics and transcripts, find why it is underperforming, and produce a prioritized improvement backlog tied to specific topics, knowledge sources and tools. Use when an agent is already in production and someone asks why resolution or engagement is low, why users escalate or abandon, what the top unanswered questions are, how to improve an agent's containment or CSAT, or wants a post-launch review, health check or optimization sprint for a deployed agent.
---

# Agent Performance Triage

An agent that passed its test plan can still fail in production, and the failure modes
look nothing like test failures. Analytics tell you *that* something is wrong; this skill
works out *what* and *where*, and hands back a backlog an owner can actually execute.

Run it two weeks after launch, then monthly.

## Scope

**In scope:** metric interpretation, root-cause diagnosis, unanswered-question mining,
topic and knowledge gap analysis, prioritized backlog, trend tracking across runs,
stakeholder readout.

**Out of scope:** editing the agent, publishing changes, reading production transcripts
that have not been de-identified or that the user is not authorized to share, cost
analysis (a separate concern), pre-launch test design.

## Step 1 — Collect the evidence

Ask for whatever is available. The skill degrades gracefully — say which conclusions are
weakened by missing inputs rather than guessing.

**Minimum viable input:** the Copilot Studio analytics summary for a stated period
(engagement rate, resolution rate, escalation rate, abandon rate, total sessions, CSAT if
collected) plus the top unresolved or unanswered queries list.

**Better input, in order of value:**

1. Session transcripts export for the period — the single highest-value input
2. Per-topic breakdown: sessions, resolution, escalation, abandonment by topic
3. The agent's topic list with trigger phrases, and the knowledge source inventory
4. Tool and action failure telemetry
5. Comparison period, so trends can be read rather than just levels
6. Any human-channel data the agent deflects into (ticket volumes, live chat handovers)

**Before you read transcripts:** confirm they are de-identified or that the user is
authorized to share them. If they contain personal data and no de-identification has
happened, stop and say so — sample counts and query clusters can often be produced
without exposing message bodies.

## Step 2 — Read the metrics as a funnel, not a scorecard

Levels in isolation mean little. Read them as a chain, and find the first link that
breaks — fixing a downstream metric while an upstream one is broken wastes a sprint.

```
reach → engagement → understanding → answering → resolution → satisfaction
```

| Metric | What it actually measures | First thing it implicates |
|---|---|---|
| Sessions vs. addressable population | reach | discovery, channel placement, launch comms |
| Engagement rate | did the user say anything at all | greeting, entry point, expectation setting |
| Escalation rate | agent handed off to a human | coverage gaps or deliberate design |
| Abandon rate | user left mid-conversation | friction, latency, wrong answers, too many turns |
| Resolution rate | conversation ended resolved | the honest headline number |
| CSAT / thumbs | perceived quality | tone, accuracy, effort |
| Turns to resolution | efficiency | slot filling, disambiguation, trigger precision |

Two cautions worth writing into every readout:

- **A high escalation rate is not automatically bad.** If the agent is designed to triage
  and hand off, escalation *is* the success path. Establish the intended design before
  judging the number.
- **Resolution rate is usually inferred, not observed.** Say how the platform computes it
  and treat it as directional. Where possible corroborate with a downstream signal — did
  the user open a ticket ten minutes later.

## Step 3 — Diagnose

Work the funnel from the first broken link. For each symptom, the candidate causes and
the evidence that discriminates between them:

**Low engagement — users arrive and say nothing**

- entry point sets the wrong expectation → check the greeting and where the agent is
  surfaced
- users do not know what it can do → no capability hints, no suggested prompts
- wrong audience or wrong channel

**High abandonment mid-conversation**

- too many turns before value → check turns-to-first-useful-answer by topic
- authentication friction at the wrong moment → check where in the flow sign-in sits
- latency, especially on tool calls and long grounding
- a wrong answer early that destroys trust — read the transcripts around the drop point

**Low resolution with high understanding** — the agent knows what was asked and still
fails

- knowledge gap: the content genuinely is not there → mine the unanswered queries
- knowledge staleness: the content exists but is out of date or contradicted by a second
  source → check for duplicate and conflicting sources, a classic and under-diagnosed
  failure
- retrieval scoping too narrow, or the right source not indexed
- tool failure: the action errors and the agent apologizes instead of retrying

**High misrouting — the agent answers the wrong question**

- overlapping trigger phrases across topics
- one over-broad topic absorbing traffic that belongs elsewhere; look for a topic with
  anomalously high volume and low resolution, the signature of a black-hole topic
- generative orchestration picking the wrong tool because tool descriptions are vague

**Low CSAT with high resolution** — technically right, experientially wrong

- tone, verbosity, or an answer that is correct but not actionable
- the agent resolved the stated question but not the underlying need

## Step 4 — Mine the unanswered questions

The top-unanswered list is the highest-yield artifact in the whole dataset. Do not just
paste it back.

1. **Cluster** the queries by intent, not by wording — twenty phrasings of one gap is one
   backlog item, not twenty. Use `scripts/cluster_queries.py`:

   ```bash
   python3 scripts/cluster_queries.py unanswered.csv \
       --column query --volume-column count --csv backlog.csv
   ```

   It groups by shared vocabulary and sizes each cluster by occurrences, which collapses
   the obvious duplicates fast. It is lexical, not semantic — "holiday" and "vacation"
   will not merge — so read the single-phrasing clusters at the bottom and merge synonym
   splits by hand. Tune `--threshold` (0.15 for short queries, up to 0.3 for verbose
   ones). Pass `--examples 0` when the output will circulate and the queries have not been
   de-identified. `assets/example-unanswered.csv` shows the expected input shape.
2. **Size** each cluster by volume and by the cost of not answering (a payroll question
   that becomes an HR ticket is worth more than a curiosity).
3. **Classify** each cluster:
   - *content gap* — nobody has written the answer → owner is a content author
   - *retrieval gap* — the answer exists but is not reachable → owner is the agent builder
   - *capability gap* — needs an action or system integration, not a document
   - *out of scope* — the right fix is a clear, fast decline plus a redirect
4. **Name an owner** per cluster. A backlog item without an owner does not ship.

Out-of-scope clusters deserve explicit attention: a well-phrased "I can't help with that,
here's who can" is a resolution, not a failure, and it costs almost nothing to build.

## Step 5 — Prioritize

Score each candidate improvement:

- **Impact** — sessions per month affected × severity of the current outcome
- **Effort** — S (trigger phrases, message copy), M (new topic, knowledge re-scoping),
  L (new integration, content authoring programme)
- **Confidence** — how strong the evidence is; a hypothesis from three transcripts is not
  the same as a pattern in 400 sessions

Rank by impact ÷ effort, weighted by confidence. Then sanity-check the top of the list:
if everything at the top is L, promote one or two S items so the sprint ships something.

Split the output into **Fix now** (this sprint, S effort, high confidence), **Next**
(M effort or needs a content owner), and **Investigate** (real signal, cause not yet
established — write the specific question to answer and how).

## Step 6 — Deliverables

**1. Triage report (HTML, self-contained).** Period and data sources; funnel view with
the broken link called out; per-topic table sorted by wasted sessions; unanswered-query
clusters with classification and owner; the ranked backlog; trend charts if a comparison
period exists; explicit list of what the data could not tell you.

**2. Backlog (CSV or table).** One row per item: title, symptom, evidence, root cause,
proposed change, target artifact (topic / knowledge source / tool / copy), owner, effort,
expected impact, how success will be measured.

**3. Stakeholder one-pager.** Is the agent working, what changed since last period, the
three things being fixed, and what the owner needs from the business — usually content or
a data source, rarely engineering.

## Step 7 — Close the loop

Each backlog item states its success metric and target before it ships. At the next run,
open by scoring the previous run's items: shipped, moved the metric, moved it enough.
A triage that never checks its own recommendations degrades into a monthly opinion column.

Track a small trend set across runs: resolution rate, abandon rate, top-cluster volume,
and the count of open backlog items by age.

## Guardrails

- Distinguish observation from inference everywhere. "Resolution is 41%" is an
  observation; "users don't trust the answers" is an inference — mark it as one and give
  the evidence.
- Small samples lie. Below roughly 100 sessions in a period, report patterns as
  hypotheses and say what volume would confirm them.
- Never quote a transcript containing personal data in a report that will circulate.
  Paraphrase, or use the de-identified form.
- Do not recommend a change the owner cannot make. If the fix is that Finance must
  publish a policy document, the backlog item belongs to Finance, and say so plainly.
- This skill reads and recommends. It never edits or publishes the agent.
