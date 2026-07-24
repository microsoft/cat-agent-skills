# Agent Evaluation Designer

Most agent "testing" fails for the same reason: nobody defined what *good* meant
before running the tests, then graded long, nuanced answers with brittle
exact-match rules and declared victory on activity rather than outcomes. This
skill fixes that.

**Agent Evaluation Designer** turns an agent into a disciplined evaluation
partner. It walks you through five stages:

1. **Define what "good" means** - the decision the evaluation supports, the
   scenarios that matter, and a one-line success bar per quality dimension.
2. **Choose the grading method per scenario** - a decision table that steers you
   to the cheapest method that actually measures what you care about (and away
   from exact/verbatim matching for long generative answers).
3. **Build the test set** - coverage over volume, short rubric-style reference
   answers, edge cases and paraphrases, no secrets baked in.
4. **Run and interpret** - read aggregate *and* per-case results, cluster
   failures by root cause, and know when to fix the test instead of the agent.
5. **Decide go / no-go** - a short, defensible readiness summary you can own.

## Built for Copilot Studio

This skill targets **Microsoft Copilot Studio**, which has a native agent
evaluation feature with exactly these grading methods, test sets, and quotas. The
skill pulls in `references/copilot-studio-evaluation.md`, which pins down the
native test-method names and the real field limits and quotas (the ~1,000-character
expected-response cap, 100 cases per set, one run at a time, the ~20-runs-per-24h
throttle, and 89-day retention) so your test design fits what the product actually
enforces. The underlying five-stage methodology is general enough to guide
evaluation of any agent, but the concrete method names and limits are Copilot
Studio's.

## When it triggers

The agent invokes this skill whenever you want to evaluate, test, or validate an
agent, decide whether one is ready to ship or go live, pick how to grade its
answers, design a test set, or interpret evaluation results into a decision.

## A note on scope

Evaluation here measures **correctness and quality**. It does not replace
responsible-AI, safety, or content-policy review - treat those as a separate
gate. The skill will remind you of that when it matters.
