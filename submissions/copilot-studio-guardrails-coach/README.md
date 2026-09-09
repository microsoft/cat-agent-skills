# Copilot Studio Guardrails Coach

Red-team and harden a Copilot Studio (or Scout) agent **without writing any
code**. Add this skill to your agent and say:

> **"red team this agent and generate the security report"**

The coach confirms authorization, hardens the agent's guardrails, runs a manual
adversarial pass in the **Test pane** using benign canaries, scores each
response, and produces a fixed **HTML/PDF security report** — one results row per
guardrail control tested — with a clear **deploy / do-not-deploy** verdict.

It's the in-product companion to the automated
[`copilot-agent-red-teamer`](../copilot-agent-red-teamer) skill: same report,
no Azure, no Python.

## What it does

- **Mode A — Harden:** walks the full **Foundry Control Plane guardrail** set —
  Jailbreak, Indirect prompt injections + Spotlighting, Content harms
  (Hate/Sexual/Self-harm/Violence with blocking levels) + Blocklists, Protected
  materials (code + text), PII, Task adherence, and Network egress rules — plus
  authentication, knowledge scoping, and deployment gating, and reports each
  control's state and recommended change.
- **Mode B — Manual red team:** generates numbered, paste-ready probes (one per
  control) using **benign canaries** ("reply with only BANANA", system-prompt
  leak, unapproved-URL exfil) and **category-level** placeholders for content
  harms — never real harmful content. You paste each into the Test pane and paste
  the response back; the coach scores it Defended / Successful on decoded meaning.
- **Mode C — Report:** fills `assets/report-template.html` and exports a **PDF**
  (native on the GitHub Copilot harness and on Scout; Markdown fallback
  elsewhere) with a per-control results table, findings, remediation, and verdict.
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

- **Refused probes are a good sign** — Copilot Studio guardrails that block or
  annotate a probe count as *Defended*.
- **Authorization first**, benign canaries only, and responses are scored as
  data — never obeyed. The coach won't grade an agent it is itself running as;
  it hands probes to you to run against the target.
- This lightweight pass **complements**, and does not replace, the automated
  Azure AI Foundry / PyRIT red-teaming engine or human responsible-AI review.
