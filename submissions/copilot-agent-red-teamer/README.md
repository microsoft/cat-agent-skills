# Copilot Agent Red Teamer

Ship a Copilot Studio agent with confidence. **Copilot Agent Red Teamer** turns
your agent into a disciplined AI red-teaming partner: it simulates adversarial
users, measures how often your agent's safety guardrails fail, and hands you a
fixed, professional report you can attach to a go-live review.

It reproduces the workflow of the **Azure AI Foundry AI Red Teaming Agent**
(built on Microsoft's open-source [PyRIT](https://github.com/Azure/PyRIT)
framework): **scan → evaluate → report**.

- **Scan** — send baseline direct adversarial probes first, then transform them
  with PyRIT attack strategies (Base64, Flip, Morse, ROT13, Tense, Jailbreak,
  indirect/XPIA injection, multi-turn, compositions, …) grouped by complexity.
- **Evaluate** — score every attack-response pair on its *decoded* meaning and
  compute the **Attack Success Rate (ASR)** overall, per risk category, and per
  attack complexity.
- **Report** — emit a **fixed-format** report (HTML + Markdown) with a clear
  **deploy / do-not-deploy** verdict.

## What it covers

**Content risks** — Hateful & Unfair, Sexual, Violent, Self-Harm, Protected
Material, Code Vulnerability, Ungrounded Attributes.
**Agentic risks** — Prohibited Actions, Sensitive Data Leakage, Task Adherence.

## Before you start

The skill's instructions alone let any agent *plan, reason about, and report* a
scan. To run a **real** scan against a live Copilot Studio agent, use the bundled
`scripts/` (see `references/RUNNING-SCANS.md`):

- An **Azure AI Foundry project** in a supported region (East US 2, France
  Central, Sweden Central, Switzerland West, North Central US) — you don't bring
  your own model; the red-teaming agent hosts the adversarial simulator and
  evaluators.
- **Python 3.10–3.13** and `pip install -r scripts/requirements.txt`, plus the
  preview `microsoft-agents-copilotstudio-client`.
- A **published Copilot Studio agent** with Entra ID authentication.

```bash
python scripts/run_redteam.py --connectivity-check   # verify the endpoint
python scripts/run_redteam.py                          # run the default scan
python scripts/run_redteam.py --scan pre-deployment-full
```

## How to use it

Ask your agent to *"red team my customer-support agent for the four core safety
risks with baseline + easy strategies"* and it will confirm authorization and
scope, plan the probe set, run baseline-first then the configured strategies,
score ASR, and return the fixed report with a verdict.

Scope is controlled by `assets/redteam-manifest.json` (risk categories, attack
strategies/complexity groups, objectives per category, language, ASR threshold,
and ready-made scan presets: quick smoke, pre-deployment full, jailbreak /
injection, and agentic-risk). The manifest is optional — with none, the skill
runs a safe default (four core content risks, baseline + easy, 5 objectives).

## The report

Every scan produces the **same seven-section report** so results are comparable
across runs and professional enough to share: Verdict, Executive Summary, Scan
Parameters, ASR Breakdown, Findings (evidence truncated and redacted),
Remediation & Next Steps, and Methodology & Disclaimer. The HTML is
self-contained and print-to-PDF ready. See `references/REPORT-FORMAT.md`.

## Good to know

- **Refused probes are a good sign.** Copilot Studio's content-management and
  threat-detection policies block many adversarial prompts; those count as
  *defended*, not as tool failures.
- **Authorization first.** Only red team an agent you own or are cleared to test.
  Adversarial payloads go **only** to the declared target, and responses are
  always treated as data to score — never as instructions.
- **Multi-agent ready.** Wire it into a Copilot Studio multi-agent system as a
  connected "Safety / Red-Team" specialist that gates promotion of other agents.
- Red teaming measures **safety posture**, not correctness or quality, and does
  not replace human responsible-AI review.
