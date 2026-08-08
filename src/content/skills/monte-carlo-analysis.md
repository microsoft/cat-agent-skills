---
name: Monte Carlo Analysis
description: "Run Monte Carlo simulations from natural-language risk inputs — triangular, normal, uniform, or log-normal — and return percentiles, a histogram PNG, optional interactive HTML, and a downloadable results spreadsheet."
agentDescription: "Use this skill whenever the user asks to run a Monte Carlo simulation, model risk or uncertainty with random sampling, estimate P5/P50/P95 outcomes, or produce a probability distribution for project timelines, portfolio returns, downtime, costs, or similar uncertain variables. Trigger on phrases like 'run a Monte Carlo', 'simulate outcomes', 'probability chart for best and worst case', or when they give min/most-likely/max (or mean/std) and want thousands of iterations. Do NOT trigger for deterministic forecasts with no uncertainty, or for generic charts unrelated to simulation."
platforms: [Copilot Studio]
tags: [monte-carlo, risk-assessment, python, simulation, matplotlib, charts, csv, analysis]
author: Nazish Qasim
authorUrl: "https://github.com/nazishqassim"
authorGithub: nazishqassim
version: 1.0.0
createdAt: 2026-07-31
updatedAt: 2026-07-31
bundle: bundles/monte-carlo-analysis.zip
---
Convert an unstructured risk question into a structured Monte Carlo run via the
bundled `scripts/monte_carlo.py` toolkit. Sample from the right distribution,
summarise percentiles, and return a histogram PNG plus spreadsheet export.
Offer an interactive HTML chart when the user asks for it.

## Instructions

1. **Cognitive intake.** Detect the core question (timeline, financial risk,
   yield, downtime, claims, etc.). If the user did not give enough numbers to
   parameterise a distribution, **stop and ask** — do not invent bounds. Prompt
   with the distribution options below.

2. **Choose a distribution:**
   - **Triangular** — user gives Minimum, Most Likely (peak), Maximum.
   - **Normal** — user gives Mean and Std Dev (optional `base_modifier` for
     portfolio / compounding style: `outcome = base * (1 + return)`).
   - **Uniform** — every value between Minimum and Maximum is equally likely.
   - **Log-normal** — non-negative, right-skewed risks; user gives log-scale
     `mean` and `sigma`. Highlight the Mean vs P50 gap when skew is large.
   - **Poisson** — count of rare events in a fixed interval; user gives `lambda`
     (expected count per interval, e.g. outages per month).
   - **Weibull** — time-to-failure / reliability; user gives `shape` (k) and
     `scale` (λ). Shape < 1 → infant mortality, = 1 → exponential, > 1 → wear-out.
   - **Beta** — bounded probability [0, 1] or percentage; user gives `alpha` and
     `beta`. Useful for proportions, conversion rates, or task-completion estimates.
   - **Exponential** — memoryless inter-arrival times; user gives `scale` (mean =
     1 / rate). Good for time between random events (calls, failures, requests).

3. **Defaults.** If simulations are unspecified, use `10000`. Prefer a clear
   `chart_title` and `x_axis_label` in the user's domain units (days, USD, hours).

4. **Execute** with the toolkit (import or CLI). Always produce:
   - Summary stats: mean, P5, P50, P95
   - PNG histogram with P5 / P50 / P95 marker lines
   - CSV of all iterations (opens in Excel)

   Also produce when asked:
   - Interactive HTML — self-contained Chart.js page with live sliders per
     distribution parameter, a simulations count slider, and a P-threshold
     calculator (`P(outcome < X) = ?`)
   - `.xlsx` workbook (requires `openpyxl`; otherwise point them to the CSV)

```python
import sys
sys.path.insert(0, "scripts")
from monte_carlo import simulate

result = simulate({
    "distribution": "triangular",
    "low": 12, "peak": 18, "high": 45,
    "simulations": 10000,
    "chart_title": "Cloud migration duration (days)",
    "x_axis_label": "Days",
    "html": True,          # optional interactive Chart.js page with live controls
    "excel": True,         # optional .xlsx (falls back to CSV if openpyxl missing)
    "out_prefix": "simulation",
})
# result keys: mean, p5, p50, p95, brief_summary, chart_path, csv_path, …
```

5. **Present results** in domain language:
   - P5 = downside / late / risk baseline
   - P50 = median expectation
   - P95 = optimistic / upper ceiling (or severe upside for cost/risk)
   - Show or link the PNG; mention CSV/Excel paths; offer HTML if not requested yet.
   - Always end with a **brief summary** (2–3 sentences). Prefer
     `result["brief_summary"]` from the toolkit; you may lightly rephrase it into
     the user's domain (days, dollars, hours) without changing the numbers.

6. **Response layout** (adapt labels to the domain):

```markdown
### Simulation Analytics Report
Ran {simulations} iterations ({distribution}).

| Metric | Value |
| --- | --- |
| P5 (risk baseline) | {p5} |
| P50 (median) | {p50} |
| P95 (upper) | {p95} |
| Mean | {mean} |

Histogram: {chart_path}
Raw iterations: {csv_path}

### Brief summary
{brief_summary}
```

## Guardrails

- Never run the script when required parameters are missing — ask first.
- Do not fabricate distribution parameters or claim false precision.
- Prefer the bundled toolkit over hand-rolled NumPy each time, for consistent
  charts and exports.
- Keep LLM replies to the summary payload; do not dump all iteration rows
  into chat.

## Bundled files

- `scripts/monte_carlo.py` — simulation engine, PNG, CSV/Excel, interactive HTML
- `references/cheatsheet.md` — parameters, CLI, test prompts
- `assets/sample_triangular.json` — demo payload (project timeline)
- `assets/sample_normal.json` — demo payload (portfolio returns)
- `assets/sample_lognormal.json` — demo payload (skewed downtime)
- `assets/sample_poisson.json` — demo payload (event count per interval)
- `assets/sample_weibull.json` — demo payload (component lifetime)
- `assets/sample_exponential.json` — demo payload (time between arrivals)
