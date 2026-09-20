# RCA Techniques Reference

Load this file when the user wants deeper guidance on a specific technique, or when the problem is complex enough that a single-pass analysis is not sufficient.

## 5 Whys

Starting from the problem statement, ask "why" repeatedly. Each answer becomes the next question.

**Rules:**
- Ask "why" at least three times before stopping. Most root causes are found between 3 and 5 levels.
- Each answer must be factual. If you do not know, say so and ask the user.
- Stop when you reach a cause that, if fixed, would prevent the symptom from recurring.
- If you reach a person's name rather than a process or system condition, you have stopped too early. Keep going until you reach a mechanism.

**Example chain:**
1. Why did the deploy fail? The build step returned 500.
2. Why did the build step return 500? The linter crashed on a missing config file.
3. Why was the config file missing? The bootstrap script skips it when the environment variable is absent.
4. Why is the environment variable absent in CI? The pipeline template was not updated when the config was moved.

Root cause: the pipeline template was not updated when the config was moved.

## Fishbone Diagram (Ishikawa)

Categorize causes across six standard categories. For each category, list specific contributing factors.

**Categories:**
- **People** — skills, training, staffing, communication, handoffs.
- **Process** — steps, policies, approvals, dependencies, sequencing.
- **Technology** — tools, infrastructure, integrations, capacity, configuration.
- **Data** — quality, completeness, freshness, schema, access.
- **Environment** — external conditions, market, regulations, physical constraints.
- **Management** — priorities, resources, decisions, risk tolerance, oversight.

**Rules:**
- List causes, not fixes. The diagram is diagnostic, not prescriptive.
- Each item should be specific enough to verify. "Bad communication" is vague; "the handoff doc was not updated after the migration" is specific.
- Mark items as confirmed, unverified, or disproven. Do not present guesses as facts.

## Contributing Factors vs Root Cause

A **root cause** is the fundamental origin. Eliminate it and the problem does not recur.

A **contributing factor** increases the likelihood or severity of the problem, but is not the origin. Eliminate it and the problem can still happen.

**Example:**
- Symptom: server crashed.
- Root cause: the memory leak was never fixed because the monitoring alert was disabled.
- Contributing factors: traffic was 3x normal, the instance type was undersized, the deploy happened at peak load.

Fixing the instance size or deferring the deploy reduces the chance of another crash, but the memory leak will eventually cause another one. Fix the root cause first.

## Output Format

When presenting the diagnosis:

1. **Root cause** — one sentence.
2. **Evidence** — the why-chain nodes or fishbone entries that support it.
3. **Contributing factors** — bullet list with estimated impact or likelihood.
4. **Recommended actions** — ordered by whether they address the root cause or only contributing factors.
