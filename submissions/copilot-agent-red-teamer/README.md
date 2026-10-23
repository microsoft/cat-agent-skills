# Copilot Agent Red Teamer

Assess a Copilot Studio agent from Scout or another Python-capable environment.
**Copilot Agent Red Teamer** runs an external Azure AI Evaluation / PyRIT scan
against a published agent endpoint: it simulates adversarial users, measures how
often safety guardrails fail, and hands you a fixed, professional report you can
attach to a go-live review.

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

**Local scan scope** — Hateful & Unfair, Sexual, Violent and Self-Harm, plus
Protected Material, Code Vulnerability or Ungrounded Attributes only when the
installed SDK supports them. Unsupported requested categories fail explicitly.
The bundled runner does not implement a cloud agentic scanner; the reference
rubric/report gate can interpret existing agentic findings from approved inputs.

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
- **Foundry User** on an approved project. Copilot Studio authentication uses
  interactive MSAL, so real scans require a signed-in local operator, not an
  unattended CI/Function host.

Create a Python virtual environment, install `scripts/requirements.txt` and the
Copilot Studio client matching `microsoft_agents.copilotstudio.client` and
`microsoft_agents.activity`. The published `microsoft-agents-copilotstudio-client`
package declares its hosting/activity dependencies. Use your organization's
approved package versions; the older Test PyPI instructions in early previews
are not a requirement to install into Copilot Studio.

Sign in to Azure with `az login`. Copy `scripts/.env.example` to `scripts/.env`
and supply `AZURE_PROJECT_ENDPOINT`, `TENANT_ID`, `APP_CLIENT_ID`,
`ENVIRONMENT_ID` and `AGENT_IDENTIFIER` for the approved target. Do not commit
credentials or generated scan data. Obtain explicit testing authorization and
use isolated test data/tools before running any scan.

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
and ready-made scan presets: quick smoke, pre-deployment full, and jailbreak /
injection). The manifest is optional — with none, the skill runs a safe default
(four core content risks, baseline + easy, 5 objectives).

## The report

Every scan produces the **same seven-section report** so results are comparable
across runs and professional enough to share: Verdict, Executive Summary, Scan
Parameters, ASR Breakdown, Findings (source references, not raw conversations),
Remediation & Next Steps, and Methodology & Disclaimer. The HTML is
self-contained and print-to-PDF ready. See `references/REPORT-FORMAT.md`.

Default HTML, Markdown and JSON exports omit raw probes, target responses and
assessment text. Findings show the input record index, turn counts and a
SHA-256 conversation reference; these locate evidence but do not prove it.
Verify evaluator findings in the approved evidence store before release
sign-off. The standalone generator can include excerpts from an input you have
reviewed and sanitized with `--include-reviewed-evidence`. Regex masking is
best-effort, not comprehensive PII detection. Simulated runs are visibly marked
and always yield `REVIEW REQUIRED`.

Remediation starts with controls a Copilot Studio maker can change directly:
authentication, scoped knowledge sources, topic/agent instructions, action
confirmation, least-privilege connector connections, Power Platform DLP, and
environment isolation. Azure AI / Foundry controls are called out separately as
platform-level evaluation or safety controls when a finding depends on that
runtime.

## Good to know

- **Refused probes are a good sign.** Copilot Studio's content-management and
  threat-detection policies block many adversarial prompts; those count as
  *defended*, not as tool failures.
- **Authorization first.** Only red team an agent you own or are cleared to test.
  Adversarial payloads go **only** to the declared target, and responses are
  always treated as data to score — never as instructions.
- **Host boundary.** Scout/local Python runs the scanner; Copilot Studio is the
  target, not a runtime for these scripts. This package does not deploy a
  connected specialist or enforce automatic agent promotion.
- Red teaming measures **safety posture**, not correctness or quality, and does
  not replace human responsible-AI review.
