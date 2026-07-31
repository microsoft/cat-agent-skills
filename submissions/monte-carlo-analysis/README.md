# Monte Carlo Analysis

Turn uncertain inputs into a probability picture. Describe a risk (project
duration, portfolio return, downtime, cost) with a range or mean/volatility;
the skill runs thousands of random trials and returns percentiles, a histogram,
and downloadable data.

## How to use it

Ask in plain language, for example:

> "Best case 12 days, typical 18, worst case 45. Run 10,000 simulations on the
> migration timeline so I can see the risk."

Or:

> "Portfolio is $5M, mean annual return 0.06, std 0.14 — Monte Carlo the
> outcomes and give me an interactive chart plus Excel."

You get:

1. **P5 / P50 / P95 / mean** in your domain units  
2. A short **brief summary** of what the spread means for planning  
3. **PNG histogram** with percentile marker lines  
4. **CSV** of every iteration (opens in Excel)  
5. Optional **interactive HTML** (Chart.js) and **.xlsx** when you ask

## Distributions supported

| When you know… | Distribution |
| --- | --- |
| Min, most likely, max | Triangular |
| Mean and standard deviation | Normal |
| Flat range min–max | Uniform |
| Skewed positive risk (log mean + sigma) | Log-normal |

If you only say "simulate our supply chain delays" with no numbers, the agent
should ask which shape and which parameters — it will not invent them.

## Dependencies

`numpy`, `pandas`, `matplotlib`. Optional: `openpyxl` for native `.xlsx` export
(CSV always works in Excel).
