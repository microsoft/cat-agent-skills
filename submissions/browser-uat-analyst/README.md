# Browser UAT Analyst

Testing done by an agent has a failure mode: it reads the docs, drives two clicks,
and tells you the feature works. This skill exists to stop that. It turns the agent
into a sceptical test analyst that will not claim a thing works until it has a
screenshot proving it, and that tells you *which kind* of failure it found.

Point it at anything you can drive in a browser — a Copilot Studio agent, a
model-driven or canvas app, a Power Automate flow's run history, a Dataverse form,
a Dynamics 365 module, the Teams web client, a Microsoft 365 admin centre, or your
own web app.

## What it does

1. Writes a **test charter** first — objective, environment, test data, hypotheses,
   success criteria, and what's out of scope.
2. Verifies environment readiness before touching anything.
3. Decomposes the request into user-visible scenarios, then adds an adversarial pass
   for the ways it actually breaks in the field.
4. Executes with Playwright, screenshotting **before and after** every key action.
5. Keeps an evidence ledger as it goes.
6. Synthesises findings into a summary, an outcome matrix, and a recommendation.

## What makes it different

**It classifies failures instead of just reporting them.** Every failure gets tagged
as a product limitation, a product defect, a test-harness limitation, a tenant or
configuration issue, an authentication issue, or model drift. This one habit is the
difference between a report someone acts on and a report that gets dismissed —
because filing a tenant misconfiguration as a product bug destroys the credibility
of everything else in the document.

**"Blocked" is a real result.** If the agent couldn't reach the state, it says so.
It never upgrades an unobserved behaviour to a pass.

**The evidence ledger has a "what it proves" column.** If you can't fill that column
in, the screenshot is decoration and the scenario is untested. This is the discipline
that stops evidence theatre.

**Failed approaches get their own slides.** The "we tried this and it doesn't work"
content is usually the most valuable output and the first thing that gets cut.
The skill requires it.

**It knows how rich chat UI actually fails.** Testing a conversational agent's
formatting, Adaptive Cards, hosted images, dynamically generated images, and
interactive actions are five separate tests with five separate failure modes — and
all of them behave differently in the authoring test pane than in Teams. Model-emitted
Adaptive Card JSON rendering as a code block instead of a card is the classic example
this skill is built to catch.

## How to use it

Ask for what you need in plain language:

- "UAT the new agent's escalation flow before we ship it"
- "Check whether the chart actually renders in Teams or just in the test pane"
- "Compare how this setting appears in the Teams admin centre vs the M365 admin centre"
- "Work out whether that failure is our config or a product bug"

The agent will propose a charter before it starts executing. Correct the scope there
— it's much cheaper than correcting the report.

## Requirements

Playwright or equivalent browser automation, plus a signed-in browser session for
whatever you're testing. Screenshots are written to `output/<test-name>/`.

For the reporting step, pair it with a PowerPoint skill if you want a deck; the
skill will export the slides to images and inspect them for overflow, tiny text,
and clipping before handing it over.

## Tips

- **Let it be slow with admin centres.** Premature assertions against heavy SPAs
  generate false failures that then take longer to disprove than the wait would have
  taken.
- Give it deterministic test data. Letting a model invent facts and then testing the
  invention proves nothing.
- Ask it explicitly for the negative cases — empty data, wrong permissions, expired
  session. That's where the real findings are.
- If a result surprises you, ask it what evidence would disambiguate the cause. It's
  built to answer that rather than defend its first hypothesis.

## Known limitations

- Browser-observable behaviour only. Not for unit tests, API contract tests, or
  load testing.
- Non-deterministic AI responses can't be asserted the way a deterministic UI can;
  the skill flags model drift as its own category rather than pretending otherwise.
