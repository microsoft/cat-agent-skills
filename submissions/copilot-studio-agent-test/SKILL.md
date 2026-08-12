---
name: copilot-studio-agent-test
description: "Test Microsoft Copilot Studio agents programmatically against a set of question/answer pairs, without driving a browser. Use when the user wants to evaluate, test, validate, benchmark or regression-test a Copilot Studio agent; run an eval set or test set against an agent; check whether an agent answers correctly from its knowledge bases; verify agent grounding or citations; or ask a Copilot Studio agent a question from the command line. Triggers include 'test my Copilot Studio agent', 'run an eval against the agent', 'validate agent answers', 'check the agent knowledge base', 'ask the agent', 'regression test the agent'. Do NOT use for building or authoring agents, for Copilot Studio topic design, or for testing declarative agents in Microsoft 365 Copilot."
---

# Copilot Studio agent testing

Runs questions against a Copilot Studio agent through the Microsoft 365 Agents SDK
(`CopilotStudio.Copilots.Invoke`), captures answers and citations, and writes results to
CSV and JSON for review.

Each question runs in a **fresh conversation** — the programmatic equivalent of clicking
*New chat* — so no answer benefits from context set by a previous one.

> **Requires Node.js 22 or later.** There is no bundled executable — the tool is a single
> JavaScript file, so nothing unsigned is executed and endpoint policy has nothing to block.
>
> Invoke it from this skill's directory. **Prefer the `node` form** — it is identical on
> Windows, macOS and Linux, and works in every shell:
>
> ```
> node scripts/cs-agent-test.cjs <command>
> ```
>
> Convenience launchers exist if you would rather not type `node`:
> `.\scripts\cs-agent-test.cmd` on Windows, `sh scripts/cs-agent-test.sh` elsewhere.
>
> Examples below use the `node` form, so they can be copied as-is on any platform.
>
> **Check Node first.** If `node --version` fails or reports below v22, stop and tell the user
> to install Node.js 22+ from https://nodejs.org — every command will fail until they do.

## What this tool does and does not do

**Does:** send questions, capture answers, extract citations, detect escalation, flag empty
turns, check optional required substrings, convert Word Q&A documents into test sets, and
assemble a pass/fail report from verdicts it is given.

**Does not** decide by itself whether an answer is semantically correct. That grading pass is
**step 3 of the workflow below and is performed by you**, by reading each answer against the
expected one. The report then carries real pass/fail verdicts. Never fabricate a pass rate the
tool did not receive from a grading pass.

## First run

Setup collects four values: application (client) ID, tenant ID, environment ID, and agent
schema name. They are written to `~/.cs-agent-test/config.json` — the **user's** home folder,
never this skill folder, so the skill stays shareable. There are no secrets involved: auth is
delegated device-code, so nothing sensitive is ever collected or stored.

**Preferred path — ask the user in chat and write the config yourself.** Do not drive the
Copilot Studio portal with a browser to find these values; just ask, and give the exact click
path below so the user knows where to look.

The click path differs between the two authoring experiences. **Ask the user which one they
have** if it is not obvious — or just give them both, they will recognise their own UI.

**Step 1 — environment ID.** Same for everyone. It is the GUID in the Copilot Studio URL:

```
copilotstudio.microsoft.com/environments/<ENVIRONMENT-ID>/agents/...
```

Ask the user to paste the whole browser URL and take the GUID from it yourself.

**Step 2 — schema name.** This is *not* the display name; it looks like `cr1a3_myAgentName`.

- **New authoring experience** (agent page has Build / Preview / Evaluate / Monitor tabs):
  > Open the agent → **⋯ (More options)** in the top right → **Settings** →
  > **Agent details** → **Identity** → **Schema name**.

  It is read-only — set when the agent was first saved and never changeable.

- **Classic agents** (agent page has Overview / Topics / Channels in the left nav):
  > Open the agent → **Settings** → **Advanced** → **Metadata** → **Schema name**.

  Classic agents also expose **Channels → Native app**, whose **Connection string** contains
  the environment ID *and* the schema name in one value. If the user has that page, it is the
  fastest option — pass the whole URL to `--connection-string` and skip Steps 1 and 2.
  **New-experience agents do not have a Native app channel**, so do not send users hunting
  for it.

**Step 3 — app registration.** Ask for the *Application (client) ID* and *Directory (tenant) ID*.
Both are on the app's **Overview** page in the Entra admin center. If the user does not have an
app registration yet, walk them through it:

> **App registrations → New registration** — any name, single tenant, no redirect URI.
> Then **Authentication → Allow public client flows → Yes**.
> Then **API permissions → Add a permission → APIs my organization uses →
> Power Platform API → Delegated → CopilotStudio.Copilots.Invoke** (note the plural), and
> **Grant admin consent**.

**Then write the config:**

```
node scripts/cs-agent-test.cjs setup --client-id <guid> --tenant-id <guid> ^
                                --environment-id <guid> --schema-name <name>

REM classic agents only, if they had the Native app connection string:
node scripts/cs-agent-test.cjs setup --client-id <guid> --tenant-id <guid> ^
                                --connection-string "<pasted url>"
```

Read the values back to the user before saving — a typo'd schema name fails quietly.

**Fallback — the interactive wizard.** For users driving the CLI standalone, or when they would
rather create the app registration guided step by step:

```
node scripts/cs-agent-test.cjs setup
```

It also accepts the connection string (press Enter to skip and type the values instead), and
needs a real terminal; if stdin is not a TTY it says so and stops rather than hanging.

Then:

```
node scripts/cs-agent-test.cjs login     # device code — needs a human at a browser
node scripts/cs-agent-test.cjs doctor    # verifies config, sign-in and connectivity
```

`doctor` is the fastest way to diagnose a problem. Run it before anything else if a command fails.

## Usage

```
node scripts/cs-agent-test.cjs ask "What is the company car policy?"
node scripts/cs-agent-test.cjs test questions.csv --out .\results

# flags
--limit 5          # first N questions only
--ids 1,7,23       # specific IDs
--delay 1000       # ms between questions
--timeout 180000   # per-turn timeout (default 120000)
--config cfg.json  # alternative config file

# other commands
setup    configure (wizard, or --flags for scripted)
config   show current settings and sign-in state
doctor   end-to-end health check
login / whoami / logout
new      write a starter test set
convert  Word (.docx) Q&A document -> test set CSV
report   results JSON + your verdicts -> Markdown report
```

## The full workflow

A complete evaluation is **four** steps. Steps 1–2 and 4 are the CLI; **step 3 is yours** and
must not be skipped — a run without it produces a report where every row says REVIEW.

```
1. convert   Word Q&A document  ->  test set CSV        (skip if you already have a CSV)
2. test      test set CSV       ->  results CSV + JSON
3. GRADE     you read every answer against Expected  ->  verdicts CSV
4. report    results + verdicts ->  Markdown report
```

### Step 1 — prepare the test set

**Ask the user which Q&A file(s) to use. Never propose a file yourself.** This skill tests any
agent against any question set — do not browse the user's disk for likely candidates, do not
offer a menu of documents you happen to have seen, and do not assume a previous run's file is
wanted again. Ask for a path, and ask how many questions to run.

Accepted inputs:
- a **Word document** (`.docx`) with a two-column Q&A table — convert it (below)
- a **CSV** in the format documented under *Test set format*
- the **Copilot Studio eval template** CSV, unchanged

If the user names several files, confirm whether they want one run per file (usually right —
results stay attributable to a knowledge base) or one combined run.

Convert Word documents rather than retyping:

```
node scripts/cs-agent-test.cjs convert "<their-file>.docx" testset.csv
node scripts/cs-agent-test.cjs convert "<their-file>.docx" --dry-run   REM preview first
```

This reads **two-column tables**: question in column 1, expected answer in column 2. A header
row such as *Domanda / Risposta attesa* is skipped. Only `.docx` is supported — for `.doc`,
`.pdf` or anything else, open it in Word and Save As `.docx`, or build the CSV by hand.

Always `--dry-run` first and sanity-check the pair count against the document. If the layout is
not a two-column table, do not fight the converter — write the CSV yourself in the format below.

### Step 2 — run the questions

```
node scripts/cs-agent-test.cjs test carpolicy.csv --out .\results
```

On a large set, run `--limit 3` first to confirm connectivity before committing to a long run.
Expect **30–60 seconds per question**; a 60-question set takes roughly 45 minutes. Tell the user
that up front, and ask how many questions they want rather than deciding for them.

### Step 3 — grade the answers (mandatory, and it is your job)

The CLI cannot judge correctness and never pretends to. After the run, **read every answer in
the results JSON against its `expected` value** and decide the verdict yourself.

Get a pre-filled sheet to work from:

```
node scripts/cs-agent-test.cjs report .\results\results-<ts>.json --template verdicts.csv
```

Then fill in one row per question — `id`, `verdict`, `reason`:

| Verdict | When to use it |
|---|---|
| `PASS` | The answer conveys what the expected answer conveys. **Different wording is fine.** A more complete or better-organised answer is still a PASS. |
| `FAIL` | Wrong, contradicts the source, invents policy, misses the substance of the question, or returns nothing. |
| `EXCLUDED` | The question itself is unsound — mis-filed, a conversational follow-up that cannot stand alone, or testing something out of scope. Removed from the denominator. |

A `reason` is required for every FAIL and EXCLUDED. Make it specific and actionable — *"quotes
a 30-day return window; the policy says 14 days"*, not *"incorrect"*.

**Grading rules — these matter, and they are easy to get wrong:**

1. Judge **substance, not wording**. Answers routinely differ from the expected text and
   sometimes improve on it. That is a PASS.
2. **Inventing policy is always a FAIL**, even when the invention sounds plausible. Check any
   specific claim (numbers, deadlines, amounts) against the expected answer.
3. **Escalating is not automatically a failure.** It is correct behaviour when the knowledge
   genuinely is not in the KB. It is a FAIL only when the agent escalates *although the answer
   exists in the source document*.
4. If the source document itself is wrong or inconsistent, that is **not** an agent failure —
   but call it out in the report as a knowledge-base finding. It usually matters more.

### Step 4 — build the report

```
node scripts/cs-agent-test.cjs report .\results\results-<ts>.json report.md ^
        --verdicts verdicts.csv --title "HR agent evaluation" --subject "KB_CarPolicy"
```

Produces a run summary (counts, pass rate, citation coverage, average response time), a table of
every question with expected answer, actual answer, verdict and failure reason, and a detailed
section for each failure. Exclusions are dropped from the pass-rate denominator.

Add `--full` to stop truncating long answers.

If the user wants Word or a vault page, convert the Markdown afterwards — the report is plain
Markdown by design.

## Test set format

The required format is a CSV with these columns:

```
"id","question","expected","expectContains"
"1","Chi ha diritto all'auto aziendale?","Va verificato con l'HR Business Partner.","HR Business Partner"
```

- `id` — **keep the original row number from the source document.** Do not renumber. Gaps and
  IDs above the row count are expected, and let any finding be traced back to its source.
- `question` — what is sent to the agent. Required.
- `expected` — the answer from the Q&A document. Optional for capture-only runs, but
  **required for grading** — without it there is nothing to judge against.
- `expectContains` — optional; `|`-separated substrings that must appear. Literal matching only,
  useful for things like a phone number or a portal URL. Not a substitute for grading.

The **Copilot Studio eval template** is also accepted unchanged (`conversationNumber, question,
response`); its `#` comment header is skipped automatically.

Other input formats: use `convert` for Word documents. For anything else, produce the CSV above
yourself — that is often quicker than coercing an odd layout.

`new` writes a starter file with the correct header, and
`assets/example-testset.csv` is a worked example.

## Output

`results-<timestamp>.csv` and `.json`, columns:

`ID · Question · Expected · Actual · Citations · Escalated · Answered · ContainsAll · Missing · ElapsedMs · Error · Verdict · Notes`

`Notes` is left empty for the reviewer's verdict.

## Reading the results

| Signal | Meaning |
|---|---|
| `Answered = no` | Turn returned nothing. Check `Error`. |
| `Citations` empty | Answer not grounded in a knowledge source. Suspicious for a KB question. |
| `Escalated = yes` | Agent handed off instead of answering. **Only a defect if the knowledge actually exists** — the tool cannot know that, so check the source document. |
| `Error` mentions consent | Turn stalled behind an interactive permission prompt. Retry; usually transient. |
| `ContainsAll = no` | A required substring was missing. See `Missing`. |

## Known constraints

- **Classic vs agentic runtime.** Agents built with the new Copilot Studio authoring experience
  run on the *agentic* runtime, at a different endpoint than classic agents. The tool detects
  this automatically: if the classic endpoint returns the notice *"Enhanced task completion
  preview has ended... republish the agent"*, it silently retries on the agentic endpoint and
  remembers the result for the rest of the run. Force it with `--runtime agentic` at setup if
  you want to skip the probe. **That notice is not a publishing problem** — republishing does
  not fix it, and the tool would otherwise have recorded it as the agent's answer to every
  question.
- **This tests the PUBLISHED agent, not the draft.** The Copilot Studio test pane tests the
  draft. Changes made in the authoring canvas are invisible here until the agent is published,
  and a draft that answers well can fail here. Always publish before a run.
- **Delegated auth only.** The Agents SDK does not support service principal tokens, so fully
  unattended CI is not possible. One device-code sign-in is cached and covers an entire run.
  For true headless automation Microsoft directs you to the Direct Line API.
- Answers take **seconds to a minute**. Long test sets take a while.
- Occasional consent prompts or transient stalls surface as `Error`. Retry those rows.

## Privacy

The skill folder contains no user data — config and tokens live in `~/.cs-agent-test/`, so the
skill can be shared or version-controlled without carrying anyone's settings.

`references/THIRD-PARTY-NOTICES.md` lists the open-source packages bundled into
`scripts/cs-agent-test.cjs`.

## Guidance when running this for a user

1. Run `doctor` first. It distinguishes "not configured" from "not signed in" from
   "cannot reach the agent", which saves a lot of guessing.
2. `setup` and `login` both need a human. Do not try to fake either.
3. On a large test set, offer `--limit` first to confirm connectivity before a long run, and
   warn the user it runs at roughly 30–60 seconds per question.
4. **Ask for the inputs; do not supply them.** Ask which Q&A file(s) to test and how many
   questions. Never pick a file for the user, never offer a menu of documents you found on
   their disk, and never reuse a previous run's file without being asked. The agent under
   test and the question set both belong to the user.
5. **Always finish the job.** A `test` run is not the deliverable — the graded report is. Carry
   on through step 3 (grade every answer) and step 4 (build the report) unless the user
   explicitly asks you to stop at raw results.
6. **Never invent a pass rate.** The number in the report must come from verdicts you actually
   made by reading the answers. If you have not graded a question, leave it REVIEW and say so.
7. When presenting results, lead with the pass rate and the failures, and state plainly that
   grading was a judgement call you made against the source documents. Surface knowledge-base
   problems separately from agent problems — the customer usually needs to fix the KB.
8. **Tell the user where the report is**, and offer the contents inline. The deliverable is the
   report, not a path they have to go and find.


