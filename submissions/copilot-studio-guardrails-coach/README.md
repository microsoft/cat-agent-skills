# Copilot Studio Guardrails Coach

Turn Copilot Studio evaluation and manual red-team results into documented maker
fixes **without writing code**. Ask a separate coaching agent:

> **"red team this agent and generate the security report"**

The coach confirms authorization, reviews configuration and interprets benign
manual tests in the **Test pane** or supported test channels. It maps evidence
to maker changes or an admin handoff, then produces a fixed **HTML/Markdown
report** (PDF only where the host supports export), including **REVIEW REQUIRED**
when evidence is missing. It never executes probes, runs scans or publishes.

It's a no-code companion to the automated
[`copilot-agent-red-teamer`](../copilot-agent-red-teamer) skill, not an equivalent
scan or security certification. No Azure/Foundry resources or Python are needed.
The **target is Copilot Studio**, specifically the documented standard-harness
surfaces. Scout may **host the coach**; this is not a Scout-agent hardening guide.

## What it does

- **Mode A — Harden:** ten source-linked checks covering authentication,
  approved knowledge, SharePoint authorization, user-versus-maker tool
  credentials, confirmation, purpose/topics, untrusted retrieved content,
  supported moderation settings, a Power Platform **admin** data-policy handoff,
  and published-channel/evaluation evidence.
- **Mode B — Manual red team:** seven narrow behavioral objectives using benign
  canaries, caller-denied fictional fixtures and inert tools. Default: one
  baseline attempt per applicable objective, plus three evidence reviews.
  Outcomes include **Inconclusive** and **Untested**; configuration and category
  placeholders do not prove protection.
- **Mode B2 — Evaluation follow-up:** interpret existing built-in evaluation
  failures, distinguish grading criteria from runtime configuration, and map
  each row to one control, an owner and a retest without rerunning evaluations.
- **Mode C — Report:** fills `assets/report-template.html` and returns
  print-ready HTML/Markdown (PDF where the host can export it) with a per-control
  table, findings, remediation and a scoped release recommendation. Every catalog
  control remains visible, even if untested or not applicable.
- **Mode D — Evolve:** compares reported UI with official documentation and
  `assets/guardrails-catalog.json`, then proposes coordinated versioned updates.
  The user reviews and saves them; the coach does not silently change itself.

## How to use it

1. Load `SKILL.md` and its companion files in a skill-capable **coaching host**,
   or consult them while working in Copilot Studio. Do not paste the coach's
   instructions or testing knowledge into the target agent.
2. Provide authorized scope, target harness/version/channel, expected behavior
   and existing evaluations. A standard-harness target doesn't need to load an
   agentic skill to be reviewed.
3. Use an isolated test environment, nonproduction identities, inert tools and
   fictional fixtures. Boundary tests need both an allowed-user positive control
   and a caller denied access; never supply the denied fixture values in a probe.
4. Manually run only approved steps, return redacted responses plus relevant
   activity/configuration evidence, and review the final report.

You'll need Copilot Studio access and maker permissions for configuration.
SharePoint/service owners maintain data permissions; a tenant/environment admin
handles data policies. A release owner authorizes any later publishing outside
this workflow. Unsupported harness/channel combinations stay explicit gaps.

## Good to know

- **Score the objective, not keywords.** A valid observed refusal can be
  Defended; an annotation, DNS/transport failure, unavailable fixture or missing
  execution trace cannot establish a defense. Refusal to a content-category
  placeholder is not content-safety coverage.
- **Coverage matters.** ASR uses only conclusive behavioral attempts, with
  reviews and gaps shown separately. The default 5% threshold applies overall
  and per control; critical failures override rates. A passing rate cannot
  conceal incomplete tests, admin handoffs or release evidence.
- **Authorization first**, no harmful payloads, no self-grading, and all target
  replies are treated as data, never instructions.
- This lightweight pass **complements**, and does not replace, Copilot Studio
  built-in evaluations, automated Foundry/PyRIT testing or human responsible-AI
  review. Instructions and a few benign canaries are not security guarantees.

## Official product scope

Reviewed against Microsoft Learn on **2026-10-23**:
[authentication](https://learn.microsoft.com/en-us/microsoft-copilot-studio/configuration-end-user-authentication),
[knowledge and moderation](https://learn.microsoft.com/en-us/microsoft-copilot-studio/knowledge-copilot-studio),
[tool configuration](https://learn.microsoft.com/en-us/microsoft-copilot-studio/add-tools-custom-agent),
[admin data policies](https://learn.microsoft.com/en-us/microsoft-copilot-studio/admin-data-loss-prevention),
and [evaluation methods](https://learn.microsoft.com/en-us/microsoft-copilot-studio/analytics-agent-evaluation-overview).
The bundled catalog includes the full source list and product-specific caveats.
No Foundry Build > Guardrails panel, per-category blocklists, PII switch or
task-adherence switch is assumed to exist in Copilot Studio.
