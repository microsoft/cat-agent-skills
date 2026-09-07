# Copilot Studio agent evaluation - platform specifics

Use these facts when the user evaluates a **Microsoft Copilot Studio** agent, so
your recommendations match what the product actually enforces. The general
methodology in `SKILL.md` still applies; this only pins down the native names,
limits, and quotas.

## Native test (grading) methods

Copilot Studio's built-in agent evaluation supports these methods. Map the
generic guidance in the skill to these exact names:

| Native method | Measures | Needs |
| --- | --- | --- |
| **General quality** | Response quality on set qualities (relevance, groundedness, completeness). Scored /100. | No expected answer |
| **Compare meaning** | Whether the answer matches the *meaning* of the expected answer. Scored /100. | Pass score + expected answer |
| **Text similarity** | Textual closeness to the expected answer. Scored /100. | Pass score + expected answer |
| **Exact match** | Answer matches the expected answer exactly. Pass/fail. | Expected answer |
| **Keyword match** | Answer contains all/any expected keywords or phrases. Pass/fail. | Expected keywords/phrases |
| **Tool use** | Whether the expected tools/capabilities were used. Pass/fail. | Expected capabilities |
| **Custom** | Meets criteria you define. Pass/fail against your labels. | Name + evaluation instructions + labels |

Guidance:
- For **long, free-form responses, do not use Exact match or Text
  similarity** - they compare against the full verbatim answer and fail on
  trivial wording differences. Use **Compare meaning**, **Keyword match**,
  **Custom**, or **General quality** (no reference needed) instead.
- A single test set can apply **multiple methods** at once.
- **All methods except General quality require an expected response or keywords.**

## Field limits and quotas (as observed / documented)

- **~1,000-character limit on both the question and the expected-response
  fields** of a test case. Cases that exceed it are dropped on import (the UI
  warns "Some cases weren't imported"). This applies to manual entry and
  spreadsheet/CSV import. It is enforced by the product; there is **no documented
  self-service setting to raise it**. Work around it by using Compare
  meaning / Keyword match / Custom with a **short reference (a rubric of required
  facts), not the full verbatim answer**.
- **Up to 100 test cases per test set.**
- **One evaluation runs at a time** per agent.
- **Rolling 24-hour throttle of ~20 evaluation runs per agent** ("The agent has
  been evaluated more than 20 times in the last 24 hours"). Not in the published
  quota docs but enforced; plan batches to stay under it. No documented way to
  raise it.
- **Results retained for 89 days**; export to CSV for longer retention.
- Test-case generation from knowledge/topics accepts source files up to **5 MB**.

## Environment notes

- In **Government Community Cloud (GCC)**: the **Text similarity** method is not
  available (all other methods are), and makers cannot attach a user profile to a
  test set.
- Evaluations can also be driven via the **Power Platform REST API** or
  connectors/flows for CI/CD, as an alternative to the Copilot Studio UI - useful
  when volume or automation matters.

> These limits reflect the current (preview-era) product and may change. When a
> value is critical to the user, advise them to confirm against the current
> Microsoft Learn "agent evaluation" docs.
