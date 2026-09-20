# Copilot Studio Agent Health Check

A static analyzer for exported Copilot Studio agents. Point it at an export and it
returns a findings report where every item is a **structural fact about the artifact**
— with a severity and a concrete one-line fix.

It is deliberately a *linter*, not an advisor. Every check is decidable from the export
alone and stays true regardless of what ships in the platform next quarter: a trigger
collision is a trigger collision forever. That is what keeps it from going stale.

## At a glance

| | |
| --- | --- |
| **Input** | A Copilot Studio solution `.zip`, an unzipped solution folder (`botcomponents/`), a folder of loose topic YAML, or a single topic/agent YAML file |
| **Output** | `lint-report.md` (also `--format json` for CI, or `--format text`) |
| **Agent types** | Classic topic-based, agentic (skill-based), and hybrid/modernized — detected automatically |
| **Runtime** | Python 3.9+; PyYAML optional (the scripts fall back to regex parsing without it) |
| **Determinism** | Fully deterministic — no model judgement, no network calls |

## Getting an export to lint

1. In the Power Platform admin experience, add your agent to a solution and **export
   the solution** (unmanaged is fine).
2. Hand the resulting `.zip` to the agent — or unzip it and point at the folder that
   contains `botcomponents/`.

You do not have to say which kind of agent it is. The ingest step detects the mode and
reports exactly what it analyzed (topics, skills, tools), so the report is always
explicit about which checks ran.

## Quick start

Just upload the export and ask, in your own words:

- "Lint this Copilot Studio agent export."
- "Why does my agent keep answering the wrong topic?"
- "My agent gives empty answers halfway through a booking — what's wrong with it?"
- "Check this agent export for anything that looks like a leaked secret."

The last three are symptom descriptions rather than requests for a lint, and are
exactly the cases this skill is meant to catch.

To run the scripts directly:

```bash
pip install -r scripts/requirements.txt          # optional, improves YAML parse fidelity
python scripts/ingest_agent.py <path-to-export> --out normalized.json
python scripts/lint_agent.py normalized.json --out lint-report.md
```

## What it checks

**Classic / topic-based** — trigger-phrase collisions that cause misrouting, unreachable
topics, missing fallback and escalation paths, slot-filling with no correction path, and
variable-lifecycle bugs (read-but-never-set, set-but-never-read). Platform-managed system
topics are recognised and excluded, because the maker did not write them.

**Agentic / skill-based** — skill-description collisions that confuse the LLM router,
missing or thin descriptions, empty skill instructions, duplicate skill names, skills told
to act on data with no tools wired, and references to unwired custom tools. Agentic reports
also include a per-skill review showing each skill's routing-separation margin, so you see
the headroom even when there are no findings.

**Cross-cutting** — unsafe or unrecognised Power Fx, dead-end dialog branches,
orchestration-mode-aware trigger/description quality, inconsistent OData parameter quoting,
variable names that look like leaked secrets, connected-agent handoff integrity, tool and
evaluation-set wiring, and an estimated token budget for the prompt.

`references/RULES.md` has the complete catalog with each rule's tier, severity, and exact
scope limit.

## Tuning

- `--threshold` (default `0.75`) governs both topic-trigger and skill-description overlap
  sensitivity. Lower it to catch more near-duplicates, at the cost of more noise.
- `--guardrails-strict` promotes the guardrail-presence and instruction-quality signals
  (confirmation gate, grounding rule, output/scope constraints) from advisory notes to hard
  findings — useful if you want them to gate a build.
- `--format json` gives a machine-readable report for CI.

## Privacy

The report describes **structure and size** — topic and skill names, description and
instruction *lengths*, tool references, similarity scores. It never reproduces the text of
your skill instructions or descriptions, which in a real agent routinely carry
business-sensitive prompt content.

## Limitations

This skill has one job and stops there:

- **Not a security red-teamer.** It reports whether a confirmation gate or grounding rule
  is *present*, never whether the agent is *safe*. No adversarial probes, no attack-success
  rates.
- **Not a cost model.** The token estimate is a ~4-characters-per-token rule of thumb to
  make prompt size visible. It does not price Credits or tokens.
- **Not a platform advisor.** It will not recommend Copilot Studio vs. Foundry, or advise
  on migration or modernization.
- **Not a test generator or design tool.** It analyses an agent that already exists; it
  does not author topics, write skills, or generate a test suite.
- **Partial parses are reported, not papered over.** If ingestion is incomplete, the report
  says so and flags that some checks may be understated.

A short report on a well-built agent is the correct output. "No structural issues found"
is a result, not a failure.
