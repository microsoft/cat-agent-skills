# Copilot Studio Content Safety Scanner

Measure content-safety outcomes for a published Copilot Studio agent from Scout
or another local Python host, using Azure AI Evaluation / PyRIT. The scanner
tests **Violence, Hate/Unfairness, Sexual and Self-Harm** responses. Copilot
Studio's platform content filters may account for the observed defenses.

**This is not a comprehensive agent-security assessment or deployment sign-off.**
It does not test authentication, oversharing, authorization, connector/tool
permissions or agentic risks. The historical submission slug
`copilot-agent-red-teamer` is retained for existing paths and imports; the
display name and supported scope are now explicitly content-safety-only.

It reproduces the workflow of the **Azure AI Foundry AI Red Teaming Agent**
(built on Microsoft's open-source [PyRIT](https://github.com/Azure/PyRIT)
framework): **scan → evaluate → report**.

- **Scan** — send baseline direct adversarial probes first, then transform them
  with PyRIT attack strategies (Base64, Flip, Morse, ROT13, Tense, Jailbreak,
  indirect/XPIA injection, multi-turn, compositions, …) grouped by complexity.
- **Evaluate** — score every attack-response pair on its *decoded* meaning and
  compute the **Attack Success Rate (ASR)** overall, per risk category, and per
  attack complexity.
- **Report** — emit fixed-format HTML/Markdown with **WITHIN CONTENT-SAFETY
  THRESHOLD**, **EXCEEDS CONTENT-SAFETY THRESHOLD**, or **REVIEW REQUIRED**.
  None of these is deployment approval.

## What it covers

Only the four named content-harm categories are accepted, including in custom
datasets. Unsupported categories fail before scanning. Imported out-of-scope
results are marked for separate review, never treated as a supported security
assessment. Transformation strategies change how content-harm objectives are
presented; they do not prove protection against general prompt injection or tool
misuse.

## Before you start

The skill's instructions alone let any agent *plan, reason about, and report* a
scan. To run a **real** scan against a live Copilot Studio agent, use the bundled
`scripts/` (see `references/RUNNING-SCANS.md`):

- An **Azure AI Foundry project** in a supported region (East US 2, France
  Central, Sweden Central, Switzerland West, North Central US) — you don't bring
  your own model; the red-teaming agent hosts the adversarial simulator and
  evaluators.
- **Python 3.10–3.13** and the dependencies in `scripts/requirements.txt`.
- A **published Copilot Studio agent** with Entra ID authentication.
- **Foundry User** on an approved project. Copilot Studio authentication uses
  interactive MSAL, so real scans require a signed-in local operator, not an
  unattended CI/Function host.

Create a Python virtual environment and run
`python -m pip install --index-url https://pypi.org/simple -r scripts/requirements.txt`.
The requirements now include the regular-PyPI
`microsoft-agents-copilotstudio-client` and its declared hosting/activity
dependencies. No preview/test index or separate preview-package install is
required. Use your organization's approved versions and package policy.

MSAL refresh/access-token persistence uses `msal-extensions` encryption: Windows
DPAPI, macOS Keychain or Linux libsecret. If OS encryption is unavailable, the
operation fails; there is no plaintext fallback. New encrypted caches are scoped
by tenant/application under `~/.copilot-content-safety-scan/token-cache`.

The old `~/.mcs_redteam_token_cache.bin`, if present, is **not read, migrated or
deleted**. A warning asks you to review/revoke old sign-in sessions and remove
that legacy cache through your approved process. This update cannot retroactively
protect an old plaintext copy.

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

Ask Scout to *"run a content-safety scan of my published customer-support agent
for the four content-harm categories with baseline + easy strategies"*. It confirms authorization and
scope, plan the probe set, run baseline-first then the configured strategies,
score ASR, and return the fixed report with a verdict.

Scope is controlled by `assets/redteam-manifest.json` (risk categories, attack
strategies/complexity groups, objectives per category, language, ASR threshold,
and ready-made scan presets: quick smoke, pre-deployment full, and jailbreak /
injection). The manifest is optional — with none, the skill runs a safe default
(four core content risks, baseline + easy, 5 objectives).

Custom JSON datasets are validated before authentication: the actual number of
objectives and objective-category assignments determines the plan. The full
dataset defines scope; `numObjectives` does not silently truncate it. All custom
datasets require explicit `--yes`, including small ones. Non-custom plans above
`maxProbesBeforeConfirm` also require it. Multi-turn strategies can issue
multiple requests per estimated probe sequence; approve that extra cost/blast
radius separately.

Each custom row contains exactly one nonempty user message. The scanner passes
the validated in-memory snapshot to the SDK with unique row IDs and an explicit
objective count, preventing the SDK's default sampling limit from silently
truncating the file. The original dataset is never rewritten. Observed category
coverage is reconciled with the approved plan; missing results require review.

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

The canonical JSON persists completeness, infrastructure/SDK error counts and
missing/unscored record counts.
Regenerating either report preserves an incomplete result as `REVIEW REQUIRED`,
even if its ASR is zero. Legacy files without completeness evidence also require
review. A content-safety threshold is evaluated only on complete scoped evidence.

Remediation distinguishes supported maker content-moderation/instruction changes
from platform-filter behavior and external Azure settings. It cannot infer an
authentication, data-permission or tool-authorization defect from a content-harm
score. Those require separate assessments. Human responsible-AI review remains
necessary.

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
- This scanner measures **content-safety outcomes within the tested scope**,
  not general security, correctness or quality.
