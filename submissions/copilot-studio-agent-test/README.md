# Copilot Studio Agent Test

Test a Microsoft Copilot Studio agent against your own question-and-answer set, and get back a
graded pass/fail report — without driving a browser.

Point it at a Word document or CSV of questions with their expected answers. It converts them
into a test set, asks the agent every question in a **fresh conversation**, then reads each
answer against the expected one and writes a report with a pass rate, a per-question table, and
the reason behind every failure.

Built for the case where a customer hands you a pile of Q&A documents and asks *"is our agent
actually answering these correctly?"*

## Why not just use the browser?

Driving the Copilot Studio test pane with browser automation works, but it is slow and brittle:
you are waiting on UI animations and guessing when an answer has finished streaming. This skill
talks to the agent through the **Microsoft 365 Agents SDK** instead (`CopilotStudio.Copilots.Invoke`),
which is roughly ten times faster and does not break when the UI changes.

## What it does — and deliberately does not do

**It does:** convert Word Q&A tables into test sets, run every question in an isolated
conversation, capture answers and citations, detect escalation and empty turns, check optional
required substrings, and assemble the final report.

**It does not** decide by itself whether an answer is *correct*. That grading pass is done by
the agent running the skill (or by you), reading each answer against the expected one.

This is a deliberate design decision, not a missing feature. A similarity score would
manufacture false failures: in practice a correct answer routinely differs in wording from the
expected text, and sometimes improves on it. So the tool captures evidence, a human-or-model
judgement produces verdicts, and the report carries those real verdicts instead of a number
nobody trusts.

## Setup

**Prerequisite:** Node.js 22 or later.

Ask your assistant: **"set up the Copilot Studio agent test skill"**. It will ask you for four
values and configure everything:

| Value | Where to find it |
|---|---|
| Application (client) ID | your Entra app registration → Overview |
| Directory (tenant) ID | same page |
| Environment ID | the GUID in the Copilot Studio URL, after `/environments/` |
| Schema name | see below — it differs between the two Copilot Studio experiences |

**Schema name** is not the display name; it looks like `cr1a3_myAgentName`.

- **New authoring experience** (Build / Preview / Evaluate / Monitor tabs):
  agent → **⋯ (More options)** → **Settings** → **Agent details** → **Identity** → **Schema name**
- **Classic agents**: agent → **Settings** → **Advanced** → **Metadata** → **Schema name**

You also need an Entra app registration with **Allow public client flows** enabled and the
delegated **`CopilotStudio.Copilots.Invoke`** permission (note the plural) granted admin
consent. The skill walks you through creating one if you do not have it.

There is **no client secret** — sign-in is device code, so nothing confidential is stored. Your
settings go to `~/.cs-agent-test/`, never into the skill folder.

## Using it

Ask: **"test my Copilot Studio agent with these questions"** and give it your file.

Or drive it yourself:

```
node scripts/cs-agent-test.cjs convert  my-questions.docx testset.csv
node scripts/cs-agent-test.cjs test     testset.csv --out .\results
node scripts/cs-agent-test.cjs report   .\results\results-<ts>.json --template verdicts.csv
REM   ... fill in PASS / FAIL / EXCLUDED and a reason for each row ...
node scripts/cs-agent-test.cjs report   .\results\results-<ts>.json report.md --verdicts verdicts.csv
```

On macOS or Linux use `sh scripts/cs-agent-test.sh`, or `node scripts/cs-agent-test.cjs`
anywhere.

Expect **30–60 seconds per question** — a 60-question set takes about 45 minutes.

## Two things that will otherwise waste your afternoon

**It tests the PUBLISHED agent, not the draft.** The Copilot Studio test pane tests the draft.
Anything you just changed in the authoring canvas is invisible here until you publish.

**Agents built with the new authoring experience run on a different endpoint.** Reached on the
classic endpoint, they reply with *"Enhanced task completion preview has ended. Go to
copilotstudio.microsoft.com and republish the agent"* — which looks like a real answer and is
not fixed by republishing. The skill detects that notice and transparently retries on the
agentic runtime endpoint, so you should never have to think about it.

## No executable

This skill ships **no binary** — `scripts/cs-agent-test.cjs` is a single self-contained
JavaScript file (~1.5 MB, no `npm install` needed), with thin `.cmd` and `.sh` launchers.

An earlier version shipped a 57 MB packaged `.exe`. That was replaced on purpose: an unsigned
executable is a reasonable thing for endpoint policy to block, code signing would not have
removed SmartScreen warnings anyway (reputation comes from download history, not from a
certificate), and 1.5 MB of readable JavaScript can actually be reviewed by a security team.
As a bonus, the JavaScript runs on macOS and Linux too.

`references/THIRD-PARTY-NOTICES.md` lists every open-source package in the bundle.

## Limitations

- **Delegated auth only.** The Agents SDK does not accept service principal tokens, so fully
  unattended CI is not possible. One device-code sign-in is cached and covers a whole run.
- **Windows, macOS and Linux**, wherever Node.js 22+ runs.
- Occasional consent prompts or transient stalls surface as errors on individual rows; re-run
  those with `--ids`.
