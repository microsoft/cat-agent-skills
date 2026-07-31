# Monte Carlo Analysis

Turn uncertain inputs into a probability picture. Describe a risk — project
duration, portfolio return, downtime, cost — with a range or mean/volatility,
and the skill runs thousands of random trials to return percentiles, a
histogram, and downloadable data.

## Why this skill exists

LLMs are poor at Monte Carlo unaided. If you ask Copilot "what is the P95 of
a triangular(12, 18, 45)?" it will either hallucinate a number or describe the
formula without computing it. Even if it generates NumPy code and runs it, each
result is a single one-off run — different every time, no chart, no CSV, no
way to hand the output to a stakeholder.

This skill fixes all three problems: the Python runs consistently, the chart is
always the same style, and the interactive HTML lets non-technical stakeholders
explore "what-if" scenarios without needing the agent again.

## Real use cases

### Project management — deadline risk

> "Our sprint finishes anywhere between 8 and 22 days, most likely 14. What is
> the risk of missing a 3-week deadline?"

Use a triangular distribution. The P-threshold calculator answers the exact
question directly: `P(outcome < 21) = 78%` — there is a 22% chance of missing
the deadline. Stakeholders get the histogram to show the client, not just a
single date.

### Finance — portfolio value at risk

> "We have $2M invested. Our model predicts 7% mean return with 18% volatility.
> What could go wrong this year?"

Use a normal distribution with `base_modifier = 2_000_000`. The P5 shows the
value-at-risk floor (the portfolio value in a bad year). Useful for anyone
managing a budget, not just quants.

### IT — contract deadline vs. migration timeline

> "Our cloud migration could take 3–8 months. How likely are we to finish
> before the contract renewal in month 5?"

Use a triangular distribution (3, 5, 8). The interactive HTML lets you drag
"worst case" from 8 to 10 to show the board what happens if a vendor is late —
no re-running the agent needed.

### Insurance / actuarial — claims exposure

> "Major claims at our site follow a log-normal pattern. Log mean is 10.5,
> sigma 1.2. What is our 95th percentile exposure?"

Log-normal is the right shape — claims cannot be negative and have long right
tails. The P95 sets the reserves number. The brief summary automatically flags
the mean vs. median gap, which is the key insight for log-normal data.

### Supply chain — buffer stock planning

> "Component delivery takes 4–12 days, usually 7. We run this 200 times a year.
> What is the tail risk?"

Use a triangular distribution. The P95 tells you how many days' buffer stock to
hold to avoid stocking out in 95% of cases.

## How to use it

Ask in plain language, for example:

> "Best case 12 days, typical 18, worst case 45. Run 10,000 simulations on the
> migration timeline so I can see the risk."

Or:

> "Portfolio is $5M, mean annual return 0.06, std 0.14 — Monte Carlo the
> outcomes and give me an interactive chart plus Excel."

If you give no numbers (e.g. "simulate our supply chain delays"), the agent
will ask for the distribution shape and parameters — it will not invent them.

## What you get

1. **P5 / P50 / P95 / mean** in your domain units
2. A short **brief summary** of what the spread means for planning
3. **PNG histogram** with P5 / P50 / P95 marker lines
4. **CSV** of every iteration (opens in Excel)
5. Optional **interactive HTML** with live controls — see below
6. Optional **.xlsx** with a Summary + Iterations sheet

## Interactive HTML

When you ask for the interactive chart, the skill writes a self-contained
browser page. No server needed — everything runs in JavaScript:

- **Live sliders** for each distribution parameter (Min / Most Likely / Max
  for triangular; Mean + Std Dev for normal; etc.)
- **Simulations slider** from 500 to 50,000 — drag to see the curve stabilise
- Stats cards (P5, P50, P95, Mean, Std dev, N) update instantly on every drag
- **P-threshold calculator** — type any value to get `P(outcome < X) = …%`

Open the `.html` file in any browser and hand it to a stakeholder for
self-serve "what-if" exploration without needing to re-run the agent.

## Distributions supported

| When you know… | Distribution |
| --- | --- |
| Min, most likely, max | Triangular |
| Mean and standard deviation | Normal |
| Flat range min–max | Uniform |
| Skewed positive risk (log mean + sigma) | Log-normal |
| Expected count of events in an interval (λ) | Poisson |
| Time-to-failure / reliability (shape k, scale λ) | Weibull |
| A proportion or completion rate (α, β) | Beta |
| Time between random arrivals (mean = scale) | Exponential |

## Dependencies

`numpy`, `pandas`, `matplotlib`. Optional: `openpyxl` for native `.xlsx` export
(CSV always works in Excel).
