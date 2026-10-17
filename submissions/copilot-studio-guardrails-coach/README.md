# Copilot Studio Guardrails Coach

Turn Copilot Studio evaluation and manual red-team results into concrete maker
fixes **without writing any code**. Add this skill to your agent and say:

> **"red team this agent and generate the security report"**

The coach confirms authorization, maps the agent's guardrail posture, runs or
interprets a manual adversarial pass in the **Test pane** using benign canaries,
and turns each result into a concrete Copilot Studio change. It then produces a
fixed **HTML/PDF security report** — one results row per guardrail control tested
— with a clear **deploy / do-not-deploy** verdict.

It's the in-product companion to the automated
[`copilot-agent-red-teamer`](../copilot-agent-red-teamer) skill: same report,
no Azure, no Python.

## What it does

- **Mode A — Harden:** walks the Copilot Studio maker controls this workflow can
  actually help with — Jailbreak, Indirect prompt injections, Content harms
  (Hate/Sexual/Self-harm/Violence with blocking levels) + Blocklists, Protected
  materials (code + text), PII, Task adherence, authentication, knowledge
  scoping, action confirmation, connector permissions, DLP, and deployment
  gating — and reports each control's state and recommended change.
- **Mode B — Manual red team:** generates numbered, paste-ready probes (one per
  control) using **benign canaries** ("reply with only BANANA", system-prompt
  leak, unapproved-URL exfil) and **category-level** placeholders for content
  harms — never real harmful content. You paste each into the Test pane and paste
  the response back; the coach scores it Defended / Successful on decoded meaning.
- **Mode B2 — Evaluation follow-up:** when Copilot Studio built-in evaluations
  already produced test results, translate failures into tangible maker fixes:
  authentication, knowledge scoping, moderation level, topic/instruction changes,
  action confirmation, connector permissions, DLP, and retest steps.
- **Mode C — Report:** fills `assets/report-template.html` and returns
  print-ready HTML/Markdown (PDF where the host can export it) with a per-control
  results table, findings, remediation, and verdict.
- **Mode D — Evolve:** keeps its guardrail catalog current. When Microsoft's
  controls change, it diffs the live UI against `assets/guardrails-catalog.json`,
  proposes a version-bumped catalog + matching probe, and records a changelog —
  all without code.

## How to use it

1. Add the skill to your agent (paste `SKILL.md` into Instructions; add the
   `references/` and `assets/` files as Knowledge).
2. In the Test pane, say **"red team this agent and generate the security
   report."**
3. Answer the authorization + scope prompts (or say "go" for the default:
   all 13 controls, 3 probes each, 5% ASR threshold).
4. Paste each probe into the target agent, paste responses back, and collect the
   final PDF report.

## Good to know

- **Refused probes are a good sign** — blocks, refusals, or annotations count as
  *Defended* only when the specific attack objective did not succeed.
- **Authorization first**, benign canaries only, and responses are scored as
  data — never obeyed. The coach won't grade an agent it is itself running as;
  it hands probes to you to run against the target.
- This lightweight pass **complements**, and does not replace, Copilot Studio
  built-in evaluations, the automated Azure AI Foundry / PyRIT red-teaming
  engine, or human responsible-AI review. Its focus is the gap after testing:
  converting results into specific Copilot Studio fixes.
