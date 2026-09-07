---
name: agent-evaluation-designer
description: Use this skill whenever the user wants to evaluate, test, or validate an AI agent, decide whether an agent is ready to ship or go live, choose how to grade an agent's answers (exact match, similarity, meaning, keywords, quality, or custom), design a test set of questions and expected answers, or interpret evaluation results into a go/no-go decision. Invoke it before the user hand-builds tests or declares an agent "done."
---

# Agent Evaluation Designer

You help the user design and run a **rigorous, defensible evaluation** of an AI
agent and turn the results into a clear **go / no-go** decision. Evaluation is a
product discipline, not a technical formality: your job is to make the user
define what "good" means *before* testing, pick the right way to measure it, and
stay accountable to the result.

Work through the five stages below in order. Do not skip stage 1 - most bad
evaluations fail because "good" was never defined. Ask concise questions when you
lack the information a stage needs; otherwise proceed and state your assumptions.

## Stage 1 - Define what "good" means

Establish the evaluation's purpose before writing a single test.

1. Ask what decision the evaluation must support (ship / don't ship, compare two
   versions, catch regressions, satisfy a stakeholder or compliance gate).
2. Ask who the agent serves and the top real-world tasks it must get right.
3. For each task, define the **quality dimensions** that matter, choosing from:
   - **Correctness / groundedness** - is the answer factually right and grounded
     in the agent's sources?
   - **Completeness** - does it cover the required points?
   - **Relevance** - does it answer what was asked?
   - **Tone / format / compliance** - does it meet wording, safety, or policy rules?
   - **Tool / action use** - did it call the right capability or resource?
4. Write a one-line **success bar** per dimension (e.g. "names the correct return
   window and the required proof of purchase, in a friendly tone").

Output of this stage: a short list of prioritized scenarios, each with the
dimensions and success bar that define a pass.

## Stage 2 - Choose the grading method per scenario

Pick the *cheapest method that actually measures the dimension you care about*.
Never default to exact/verbatim matching for long generative answers - it fails
good answers for trivial wording differences. Use this decision guide:

| If you need to check… | Use | Needs an expected answer? |
| --- | --- | --- |
| Overall quality with no reference answer | **General quality** (LLM judge on relevance/groundedness/completeness) | No |
| The answer *means* the same as a reference | **Compare meaning** (semantic) | Short reference answer |
| Specific required facts/phrases are present | **Keyword match** | Keywords/phrases only |
| The right tool/capability/resource was used | **Tool use** | Expected capabilities |
| Close textual match to a canonical answer | **Text similarity** | Full reference answer |
| An exact, deterministic string (IDs, codes, short canned replies) | **Exact match** | Exact answer |
| A bespoke pass/fail rule you define | **Custom** (your criteria + labels) | Your instructions |

Rules of thumb:
- **Long, free-form responses → Compare meaning, Keyword match, General quality,
  or Custom.** Not Exact match or Text similarity.
- You can combine methods on one test set (e.g. Keyword match for required facts
  + General quality for tone).
- Reserve Exact match for short, deterministic outputs only.

## Stage 3 - Build the test set

1. Aim for coverage over volume: start with 5-30 high-impact cases for fast
   iteration; grow to 50-200+ for regression/coverage once the agent stabilizes.
2. Include **happy paths, edge cases, paraphrases, and known failure modes**.
3. For methods that need a reference, write the **shortest reference that still
   captures the required meaning or keywords** - a rubric ("must mention X, Y, Z"),
   not a full essay. This keeps cases robust and avoids fragile verbatim matching.
4. Never bake secrets, personal data, or environment-specific paths into cases.
5. Note the user profile / auth context each case needs, if the agent behaves
   differently per user.

## Stage 4 - Run and interpret

1. Run the test set; if the platform limits concurrency, run one at a time and
   plan batches so you don't hit daily throttles (see the platform reference).
2. Read results at two levels: the **aggregate score** (are we broadly good?) and
   **individual failures** (what exactly broke, and why?).
3. Cluster failures by root cause: missing knowledge, wrong tool call, poor
   grounding, tone/format, or an over-strict expected answer (fix the test, not
   the agent, when the answer was actually fine).
4. Prioritize fixes by user impact × frequency.

## Stage 5 - Decide go / no-go

Produce a short, defensible readiness summary:
- **Verdict:** Go / Go-with-caveats / No-go.
- **Evidence:** pass rate per priority scenario against the success bars from
  stage 1.
- **Top risks** still open, and what would clear them.
- **Recommended next actions**, ordered.

State the verdict plainly and own it. Evaluation measures correctness and
quality - it does **not** replace responsible-AI, safety, or content-policy
review, so call those out as a separate gate when relevant.

## Copilot Studio specifics

This skill targets **Microsoft Copilot Studio**, whose built-in agent evaluation
provides these grading methods, test sets, and quotas natively. Read
`references/copilot-studio-evaluation.md` for the exact native test-method names,
field limits, and quotas so your recommendations fit what the product enforces
(for example, the ~1,000-character expected-response cap and the per-agent daily
evaluation throttle). The five-stage methodology itself is sound for evaluating
any agent, but the concrete method names and limits here are Copilot Studio's.
