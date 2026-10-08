# Agent Cost & Capacity Planner

Turn a Microsoft Copilot Studio agent's design and expected traffic into a
defensible consumption forecast, purchasing recommendation, and cost-reduction
plan.

## Read this first: standard harness only

> **The detailed calculator supports only agents powered by the Copilot Studio
> standard harness.** Its feature rates, Microsoft 365 Copilot zero-rating
> logic, optimization arithmetic, and bundled `scripts/forecast.py` calculator
> do not apply to agents powered by the GitHub Copilot harness.

This boundary matters because the two harnesses use different billing models:

| Standard harness - supported | GitHub Copilot harness - not calculated |
|---|---|
| Consumption is based on discrete activities such as answers, actions, grounding, flow actions, AI tools, pages, and voice minutes. | Consumption is usage-based across the whole experience, including models, context, knowledge, tools and MCP, the harness, retries, runtime duration, and artifacts. |
| Eligible activity for authenticated, employee-facing users can be zero-rated when those users have qualifying Microsoft 365 Copilot licences. | Do not carry the standard-harness zero-rating assumption across. Creation, preview, evaluation, and production activity can all consume credits; verify current entitlements separately. |
| The bundled calculator produces base, peak, and worst-case forecasts. | A separate range-based model using the current Microsoft Copilot Credits Guide is required. |

If you are unsure which harness powers an agent, the skill checks that first.
For a GitHub Copilot harness agent, it explains the billing implications and
routes you to the correct planning method instead of producing a misleading
standard-harness number.

## What it does

For a confirmed standard-harness agent, the skill:

- reads an exported solution or a description of the agent's topics, knowledge,
  tools, flows, orchestration, channels, and triggers
- derives the billable interaction mix from the design instead of asking you to
  guess how many feature calls it will make
- forecasts base, peak, and worst-case monthly Copilot Credit consumption
- separates gross, billable, and eligible zero-rated activity by user population
- compares pay-as-you-go, prepaid Copilot Credit packs, and Credit Commit Units
  using your effective prices
- ranks the largest cost drivers and estimates the savings and trade-offs of
  concrete design changes
- produces a self-contained HTML cost model and a budget sign-off one-pager

The skill never invents a currency amount. It asks for your effective price per
credit before converting consumption into cost.

## Before you start

Bring as much of the following as you have:

- the agent's harness, or enough design information to identify it
- an exported solution, topic list, or sanitized design description
- expected active users, sessions per user, and turns per session
- the employee-facing and customer-facing traffic split
- the share of employee users with qualifying Microsoft 365 Copilot licences
- growth assumptions and any expected launch spike
- your current price per credit for the purchasing options you want compared

Python 3 is required to run the bundled standard-harness calculator. The skill
re-verifies current rates against official Microsoft documentation before
publishing a forecast.

## How to use it

For a full standard-harness forecast, ask:

> Forecast the monthly Copilot Credit consumption and cost for this
> standard-harness employee service agent. Use the attached solution export,
> model base, peak, and worst-case scenarios, compare our purchasing options,
> and recommend the three highest-impact design changes.

If the harness is unknown, start with:

> Identify which Copilot Studio harness this agent uses before estimating
> anything. If it is the GitHub Copilot harness, do not use standard-harness
> rates; explain the separate range-based planning approach instead.

## Good to know

- Forecasts are planning ranges, not licensing quotes. Product rates,
  entitlements, and purchasing terms should be checked at the time of use.
- External API, Azure, and third-party connector costs are named as out-of-model
  items rather than guessed.
- The skill reads and calculates only. It does not modify the tenant, solution,
  or licensing configuration.
- Re-baseline the forecast after two weeks of production telemetry before making
  a long-term capacity commitment.

See Microsoft's guidance on
[choosing a harness](https://learn.microsoft.com/en-us/microsoft-copilot-studio/harnesses-overview),
the separate
[GitHub Copilot harness billing model](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/billing-credit-overview),
and the official
[standard-harness usage estimator](https://microsoft.github.io/copilot-studio-estimator/).
