# Monte Carlo Analysis — Cheat Sheet

Engine: `scripts/monte_carlo.py`

```python
from monte_carlo import simulate
result = simulate({ ... })
```

---

## Payload fields

| Field | Required | Notes |
| --- | --- | --- |
| `distribution` | yes | `triangular` \| `normal` \| `uniform` \| `log-normal` \| `poisson` \| `weibull` \| `beta` \| `exponential` |
| `simulations` | no | default `10000` |
| `base_modifier` | no | offset (triangular/uniform) or scale base (normal/log-normal) |
| `chart_title` | no | PNG / HTML title |
| `x_axis_label` | no | axis label in domain units |
| `html` | no | `true` → write interactive Chart.js HTML with live parameter sliders |
| `excel` | no | `true` → try `.xlsx` (needs `openpyxl`) |
| `out_prefix` | no | default `simulation` → `simulation_density.png`, etc. |

### Per distribution

| Distribution | Required keys | Notes |
| --- | --- | --- |
| `triangular` | `low`, `peak`, `high` | low ≤ peak ≤ high |
| `normal` | `mean`, `std_dev` | + optional `base_modifier` for portfolio compounding |
| `uniform` | `low`, `high` | |
| `log-normal` | `mean`, `sigma` | log-scale parameters |
| `poisson` | `lambda` | expected count per interval; must be > 0 |
| `weibull` | `shape` | `scale` defaults to 1.0; shape < 1 = infant mortality, > 1 = wear-out |
| `beta` | `alpha`, `beta` | outputs in [0, 1]; both must be > 0 |
| `exponential` | `scale` | mean = scale = 1 / rate; must be > 0 |

---

## Return payload

```json
{
  "mean": 0,
  "p5": 0,
  "p50": 0,
  "p95": 0,
  "simulations": 10000,
  "distribution": "triangular",
  "brief_summary": "Across 10,000 triangular trials, the median outcome is …",
  "chart_path": ".../simulation_density.png",
  "csv_path": ".../simulation_raw_data.csv",
  "html_path": ".../simulation_interactive.html",
  "excel_path": ".../simulation_results.xlsx"
}
```

Always surface `brief_summary` (or a light domain rephrase) after the metrics table.

---

## CLI examples

```bash
# Triangular project timeline
python scripts/monte_carlo.py \
  --distribution triangular --low 12 --peak 18 --high 45 \
  --title "Cloud migration (days)" --xlabel "Days" \
  --html --excel --json-out

# From sample payload
python scripts/monte_carlo.py --payload assets/sample_triangular.json --html

# Normal portfolio with base value
python scripts/monte_carlo.py \
  --distribution normal --mean 0.06 --std-dev 0.14 \
  --base-modifier 5000000 \
  --title "Portfolio terminal value" --xlabel "USD" --html

# Log-normal downtime
python scripts/monte_carlo.py \
  --distribution log-normal --mean 1.5 --sigma 0.75 \
  --title "Unplanned outage recovery (hours)" --xlabel "Hours" --html

# Poisson — outages per month
python scripts/monte_carlo.py \
  --distribution poisson --lambda 3.5 \
  --title "Outages per month" --xlabel "Count" --html

# Weibull — component lifetime
python scripts/monte_carlo.py \
  --distribution weibull --shape 2.5 --scale 1000 \
  --title "Bearing lifetime (hours)" --xlabel "Hours" --html

# Beta — task completion probability
python scripts/monte_carlo.py \
  --distribution beta --alpha 2 --beta 5 \
  --title "Task completion rate" --xlabel "Proportion" --html

# Exponential — time between support tickets
python scripts/monte_carlo.py \
  --distribution exponential --scale 4.2 \
  --title "Hours between tickets" --xlabel "Hours" --html
```

---

## Test prompts (for agent behaviour)

### 1. Triangular — project manager

> Best case 12 days, typical 18, worst 45. Run 10,000 simulations on this timeline.

Expect: `distribution=triangular`, low/peak/high parsed, P5/P50/P95 in days, PNG + CSV.

### 2. Normal — portfolio

> Baseline portfolio $5,000,000, mean return 0.06, std 0.14. Run the standard loop count.

Expect: `normal`, `base_modifier=5000000`, default 10000 sims, dollar thresholds.

### 3. Log-normal — downtime

> Log-scale mean outage 1.5, sigma 0.75. Simulate recovery windows.

Expect: `log-normal`, P95 ≫ P50, right-skew called out.

### 4. Poisson — failure count

> We average 3.5 server outages per month. How many should I plan capacity for at P95?

Expect: `poisson`, `lambda=3.5`, integer outputs, P95 count highlighted.

### 5. Weibull — reliability

> Component shape factor 2.5, characteristic life 1000 hours. Model lifetime distribution.

Expect: `weibull`, `shape=2.5`, `scale=1000`, wear-out pattern noted (shape > 1).

### 6. Beta — conversion rate

> Our landing page conversion is somewhere between 5% and 25%, prior belief alpha 2 beta 5.

Expect: `beta`, outputs in [0, 1], P50 ≈ 0.28.

### 7. Exponential — inter-arrival

> Support tickets arrive on average every 4.2 hours. Simulate time between arrivals.

Expect: `exponential`, `scale=4.2`, memoryless note, P95 well above mean.

### 8. Disambiguation (do not run)

> Run a simulation chart for our manufacturing supply chain delays next month.

Expect: ask for triangular (min/likely/max) or normal (mean/std) — **no script run**.

---

## Output options to offer the user

1. **PNG histogram** — always produced  
2. **CSV** — always produced (open in Excel)  
3. **Interactive HTML** — set `html: true` (live sliders, P-threshold calculator)  
4. **Excel `.xlsx`** — set `excel: true` (install `openpyxl` if missing)
