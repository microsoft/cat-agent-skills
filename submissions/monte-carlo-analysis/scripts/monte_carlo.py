#!/usr/bin/env python3
"""Monte Carlo simulation toolkit for Copilot Studio agents.

Samples from triangular / normal / uniform / log-normal distributions,
summarises P5 / P50 / P95 / mean, and writes:
  - a matplotlib histogram PNG (always)
  - a CSV of all iterations (always; opens in Excel)
  - optional interactive Chart.js HTML
  - optional .xlsx (requires openpyxl; otherwise skipped with a note)

Import usage:
    from monte_carlo import simulate
    result = simulate({
        "distribution": "triangular",
        "low": 12, "peak": 18, "high": 45,
        "simulations": 10000,
        "html": True,
        "excel": True,
    })

CLI usage:
    python monte_carlo.py --distribution triangular --low 12 --peak 18 --high 45
    python monte_carlo.py --payload ../assets/sample_triangular.json --html
    python monte_carlo.py --distribution normal --mean 0.06 --std-dev 0.14 \\
        --base-modifier 5000000 --html --excel

Dependencies: numpy, pandas, matplotlib. Optional: openpyxl for .xlsx.
Runs headless (Agg backend).
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any, Mapping, Optional, Sequence, Union

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

PALETTE_BAR = "#4C72B0"
P5_COLOUR = "#C44E52"
P50_COLOUR = "#DD8452"
P95_COLOUR = "#55A868"

Payload = Mapping[str, Any]
PayloadLike = Union[Payload, str]


def _as_payload(source: PayloadLike) -> dict[str, Any]:
    """Accept a dict or a path / JSON string."""
    if isinstance(source, Mapping):
        return dict(source)
    if isinstance(source, str):
        text = source.strip()
        if text.startswith("{"):
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise TypeError("JSON payload must be an object, not an array.")
            return parsed
        if text.startswith("["):
            raise TypeError("JSON payload must be an object {…}, not an array […].")
        with open(source, encoding="utf-8") as fh:
            parsed = json.load(fh)
        if not isinstance(parsed, dict):
            raise TypeError(f"JSON file must contain an object, got {type(parsed).__name__}.")
        return parsed
    raise TypeError(
        f"Unsupported payload: {type(source)!r}. "
        "Pass a dict, JSON string, or path to a .json file."
    )


def sample_outcomes(data: Mapping[str, Any]) -> tuple[np.ndarray, str]:
    """Draw Monte Carlo samples. Returns (outcomes, normalised distribution name)."""
    simulations = int(data.get("simulations", 10_000))
    if simulations < 1:
        raise ValueError("`simulations` must be a positive integer.")
    distribution = str(data.get("distribution", "triangular")).lower().replace("_", "-")
    base_modifier = float(data.get("base_modifier", 0.0))

    if base_modifier:
        if distribution not in ("triangular", "uniform", "normal", "log-normal", "lognormal"):
            raise ValueError(
                "`base_modifier` is only supported for triangular/uniform (offset) "
                "and normal/log-normal (base scaling)."
            )
        if distribution in ("normal", "log-normal", "lognormal") and base_modifier <= 0:
            raise ValueError("`base_modifier` must be > 0 for normal/log-normal base scaling.")

    if distribution == "triangular":
        for key in ("low", "peak", "high"):
            if key not in data:
                raise ValueError(
                    f"Triangular distribution requires `{key}` "
                    "(minimum, most likely, maximum)."
                )
        low, peak, high = float(data["low"]), float(data["peak"]), float(data["high"])
        if not (low <= peak <= high):
            raise ValueError("Triangular requires low <= peak <= high.")
        raw = np.random.triangular(low, peak, high, simulations)
        return raw + base_modifier, distribution

    if distribution == "normal":
        if "mean" not in data or "std_dev" not in data:
            raise ValueError("Normal distribution requires `mean` and `std_dev`.")
        mean = float(data["mean"])
        std_dev = float(data["std_dev"])
        if std_dev < 0:
            raise ValueError("`std_dev` must be >= 0.")
        raw = np.random.normal(mean, std_dev, simulations)
        if base_modifier > 0:
            return base_modifier * (1.0 + raw), distribution
        return raw, distribution

    if distribution in ("log-normal", "lognormal"):
        if "mean" not in data or "sigma" not in data:
            raise ValueError("Log-normal distribution requires `mean` and `sigma`.")
        mean = float(data["mean"])
        sigma = float(data["sigma"])
        if sigma < 0:
            raise ValueError("`sigma` must be >= 0.")
        raw = np.random.lognormal(mean, sigma, simulations)
        if base_modifier > 0:
            return base_modifier * raw, "log-normal"
        return raw, "log-normal"

    if distribution == "uniform":
        if "low" not in data or "high" not in data:
            raise ValueError("Uniform distribution requires `low` and `high`.")
        low, high = float(data["low"]), float(data["high"])
        if high < low:
            raise ValueError("Uniform requires high >= low.")
        return np.random.uniform(low, high, simulations) + base_modifier, distribution

    if distribution == "poisson":
        lam = data.get("lambda", data.get("lam"))
        if lam is None:
            raise ValueError("Poisson distribution requires `lambda` (mean rate, > 0).")
        lam = float(lam)
        if lam <= 0:
            raise ValueError("`lambda` must be > 0.")
        return np.random.poisson(lam, simulations).astype(float) + base_modifier, distribution

    if distribution == "weibull":
        if "shape" not in data:
            raise ValueError("Weibull distribution requires `shape` (k > 0).")
        shape = float(data["shape"])
        scale = float(data.get("scale", 1.0))
        if shape <= 0:
            raise ValueError("`shape` must be > 0.")
        if scale <= 0:
            raise ValueError("`scale` must be > 0.")
        return np.random.weibull(shape, simulations) * scale + base_modifier, distribution

    if distribution == "beta":
        if "alpha" not in data or "beta" not in data:
            raise ValueError("Beta distribution requires `alpha` and `beta` (both > 0).")
        alpha = float(data["alpha"])
        beta_val = float(data["beta"])
        if alpha <= 0 or beta_val <= 0:
            raise ValueError("`alpha` and `beta` must be > 0.")
        return np.random.beta(alpha, beta_val, simulations) + base_modifier, distribution

    if distribution == "exponential":
        if "scale" not in data:
            raise ValueError("Exponential distribution requires `scale` (mean = 1/rate, > 0).")
        scale = float(data["scale"])
        if scale <= 0:
            raise ValueError("`scale` must be > 0.")
        return np.random.exponential(scale, simulations) + base_modifier, distribution

    raise ValueError(
        f"Distribution type '{distribution}' is unsupported. "
        "Use: triangular, normal, uniform, log-normal, "
        "poisson, weibull, beta, or exponential."
    )


def summarise(outcomes: np.ndarray) -> dict[str, float]:
    return {
        "mean": float(np.mean(outcomes)),
        "p5": float(np.percentile(outcomes, 5)),
        "p50": float(np.percentile(outcomes, 50)),
        "p95": float(np.percentile(outcomes, 95)),
    }


def brief_summary(
    stats: Mapping[str, float],
    *,
    distribution: str,
    simulations: int,
    unit: str = "",
) -> str:
    """Two–three sentence takeaway for the agent to show after the metrics."""
    unit = (unit or "").strip()
    u = f" {unit}" if unit else ""
    p5, p50, p95, mean = stats["p5"], stats["p50"], stats["p95"], stats["mean"]
    span = p95 - p5
    skew_gap = mean - p50
    dist = distribution.lower().replace("_", "-")

    lead = (
        f"Across {simulations:,} {dist} trials, the median outcome is "
        f"{p50:.4g}{u} (mean {mean:.4g}{u})."
    )
    spread = (
        f"About 90% of simulated results fall between {p5:.4g}{u} (P5) and "
        f"{p95:.4g}{u} (P95) — a spread of {span:.4g}{u}."
    )

    if dist in ("log-normal", "lognormal") or abs(skew_gap) > 0.05 * max(abs(p50), 1e-9):
        direction = "above" if skew_gap > 0 else "below"
        skew = (
            f"The mean sits {direction} the median "
            f"(gap {abs(skew_gap):.4g}{u}), which signals a skewed tail — "
            f"plan for outliers beyond the typical case."
        )
        return f"{lead} {spread} {skew}"
    return f"{lead} {spread} Use P50 for planning and P5/P95 as downside/upside bounds."


def save_histogram(
    outcomes: np.ndarray,
    stats: Mapping[str, float],
    *,
    title: str,
    xlabel: str,
    out: str,
    bins: int = 50,
    dpi: int = 150,
) -> str:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(
        outcomes,
        bins=bins,
        color=PALETTE_BAR,
        alpha=0.75,
        edgecolor="white",
        linewidth=0.4,
    )
    ax.axvline(
        stats["p5"], color=P5_COLOUR, linestyle="--", linewidth=2,
        label=f"P5: {stats['p5']:.2f}",
    )
    ax.axvline(
        stats["p50"], color=P50_COLOUR, linestyle="--", linewidth=2,
        label=f"P50: {stats['p50']:.2f}",
    )
    ax.axvline(
        stats["p95"], color=P95_COLOUR, linestyle="--", linewidth=2,
        label=f"P95: {stats['p95']:.2f}",
    )
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel("Frequency", fontsize=11)
    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out


def save_csv(outcomes: np.ndarray, out: str) -> str:
    df = pd.DataFrame({
        "Iteration_ID": np.arange(1, len(outcomes) + 1),
        "Simulated_Value": outcomes,
    })
    df.to_csv(out, index=False)
    return out


def save_excel(
    outcomes: np.ndarray,
    stats: Mapping[str, float],
    out: str,
    summary_text: str = "",
) -> Optional[str]:
    """Write .xlsx with a Summary sheet + Iterations sheet. Needs openpyxl."""
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        return None

    rows = [
        {"Metric": "mean", "Value": stats["mean"]},
        {"Metric": "p5", "Value": stats["p5"]},
        {"Metric": "p50", "Value": stats["p50"]},
        {"Metric": "p95", "Value": stats["p95"]},
        {"Metric": "simulations", "Value": len(outcomes)},
    ]
    if summary_text:
        rows.append({"Metric": "brief_summary", "Value": summary_text})
    summary = pd.DataFrame(rows)
    iterations = pd.DataFrame({
        "Iteration_ID": np.arange(1, len(outcomes) + 1),
        "Simulated_Value": outcomes,
    })
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        iterations.to_excel(writer, sheet_name="Iterations", index=False)
    return out


def save_html(
    outcomes: np.ndarray,
    stats: Mapping[str, float],
    *,
    title: str,
    xlabel: str,
    out: str,
    distribution: str = "triangular",
    params: Optional[Mapping[str, Any]] = None,
    summary_text: str = "",
) -> str:
    """Write a fully interactive Chart.js page with live parameter controls.

    Users can drag sliders to change distribution parameters and simulations;
    the histogram and all statistics update instantly in the browser via JS
    resampling — no server round-trip needed.
    """
    params = dict(params or {})
    dist = distribution.lower().replace("_", "-")
    n_sims = int(params.get("simulations", len(outcomes)))
    base_mod = float(params.get("base_modifier", 0.0))

    # Build distribution-specific controls and the JS param object.
    controls_html, js_params = _build_controls(dist, params, xlabel)

    summary_html = (
        f'<p class="summary" id="summaryText">{_escape(summary_text)}</p>'
        if summary_text else
        '<p class="summary" id="summaryText"></p>'
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{_escape(title)}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: "Segoe UI", system-ui, sans-serif;
      margin: 0; padding: 24px;
      background: #f4f6f9; color: #222;
    }}
    .wrap {{
      max-width: 980px; margin: 0 auto; background: #fff;
      padding: 24px 28px; border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    }}
    h1 {{ font-size: 1.35rem; margin: 0 0 4px; }}
    .meta {{ color: #666; font-size: 0.9rem; margin: 0 0 14px; }}
    .summary {{
      background: #eef3f9; border-left: 4px solid #4C72B0;
      padding: 10px 14px; margin: 0 0 16px; line-height: 1.5;
      font-size: 0.92rem; border-radius: 0 4px 4px 0;
    }}
    /* ── Controls ── */
    .controls {{
      background: #f8f9fb; border: 1px solid #e3e7ee;
      border-radius: 6px; padding: 16px 18px; margin-bottom: 18px;
    }}
    .controls h2 {{
      font-size: 0.95rem; margin: 0 0 12px; color: #444; font-weight: 600;
    }}
    .control-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 12px 20px;
    }}
    .control-item label {{
      display: flex; justify-content: space-between;
      font-size: 0.85rem; color: #555; margin-bottom: 4px;
    }}
    .control-item label .val {{
      font-weight: 600; color: #222; min-width: 50px; text-align: right;
    }}
    .control-item input[type=range] {{
      width: 100%; accent-color: #4C72B0; cursor: pointer;
    }}
    /* ── Threshold calculator ── */
    .threshold {{
      margin-top: 12px; padding-top: 12px;
      border-top: 1px solid #e3e7ee;
      display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
      font-size: 0.88rem; color: #555;
    }}
    .threshold input[type=number] {{
      width: 100px; padding: 4px 6px; border: 1px solid #ccc;
      border-radius: 4px; font-size: 0.88rem;
    }}
    .threshold .pct-result {{
      font-weight: 700; color: #4C72B0; font-size: 0.95rem;
    }}
    /* ── Stats cards ── */
    .stats {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 10px; margin-bottom: 18px;
    }}
    .stat {{
      background: #f4f6f9; border-radius: 6px; padding: 10px 12px;
    }}
    .stat span {{ display: block; font-size: 0.75rem; color: #777; margin-bottom: 2px; }}
    .stat strong {{ font-size: 1.05rem; font-weight: 700; }}
    /* ── Chart ── */
    .chart-box {{ position: relative; height: 380px; }}
  </style>
</head>
<body>
<div class="wrap">
  <h1>{_escape(title)}</h1>
  <p class="meta">Interactive Monte Carlo — adjust parameters to see the distribution update live.</p>
  {summary_html}

  <div class="controls">
    <h2>Parameters</h2>
    <div class="control-grid">
{controls_html}
      <div class="control-item">
        <label>Simulations <span class="val" id="val-simulations">{n_sims:,}</span></label>
        <input type="range" id="ctrl-simulations"
          min="500" max="50000" step="500" value="{n_sims}"
          oninput="syncLabel('simulations',this.value,true);resample()">
      </div>
    </div>
    <div class="threshold">
      <span>P(outcome &lt;</span>
      <input type="number" id="thresholdVal" placeholder="enter value"
        oninput="updateThreshold()">
      <span>) =</span>
      <span class="pct-result" id="thresholdPct">—</span>
    </div>
  </div>

  <div class="stats">
    <div class="stat"><span>P5 (downside)</span><strong id="s-p5">{stats['p5']:.4g}</strong></div>
    <div class="stat"><span>P50 (median)</span><strong id="s-p50">{stats['p50']:.4g}</strong></div>
    <div class="stat"><span>P95 (upside)</span><strong id="s-p95">{stats['p95']:.4g}</strong></div>
    <div class="stat"><span>Mean</span><strong id="s-mean">{stats['mean']:.4g}</strong></div>
    <div class="stat"><span>Std dev</span><strong id="s-std">{float(np.std(outcomes)):.4g}</strong></div>
    <div class="stat"><span>Iterations</span><strong id="s-n">{len(outcomes):,}</strong></div>
  </div>

  <div class="chart-box"><canvas id="mcChart"></canvas></div>
</div>

<script>
// ── Configuration injected by Python ──────────────────────────────────────
const DIST   = {json.dumps(dist)};
const PARAMS = {json.dumps(js_params)};
const XLABEL = {json.dumps(xlabel)};
const BASE   = {json.dumps(base_mod)};
const BINS   = 50;

// ── Random samplers ───────────────────────────────────────────────────────
function boxMuller() {{
  let u, v, s;
  do {{ u = Math.random()*2-1; v = Math.random()*2-1; s = u*u+v*v; }}
  while (s >= 1 || s === 0);
  return u * Math.sqrt(-2 * Math.log(s) / s);
}}

// Gamma sampler (Marsaglia & Tsang 2000) — required by Beta.
function gammaRng(shape) {{
  if (shape < 1) return gammaRng(1 + shape) * Math.pow(Math.random(), 1 / shape);
  const d = shape - 1/3, c = 1 / Math.sqrt(9 * d);
  for (;;) {{
    let z, v;
    do {{ z = boxMuller(); v = 1 + c * z; }} while (v <= 0);
    v = v * v * v;
    const u = Math.random();
    if (u < 1 - 0.0331 * z*z*z*z) return d * v;
    if (Math.log(u) < 0.5*z*z + d*(1 - v + Math.log(v))) return d * v;
  }}
}}

// Poisson sampler (Knuth for λ ≤ 30; normal approx otherwise).
function poissonRng(lam) {{
  if (lam > 30) return Math.max(0, Math.round(lam + Math.sqrt(lam) * boxMuller()));
  const L = Math.exp(-lam);
  let k = 0, p = 1;
  do {{ k++; p *= Math.random(); }} while (p > L);
  return k - 1;
}}

function sampleOne(p) {{
  if (DIST === 'triangular') {{
    const lo = Math.min(p.low, p.peak, p.high);
    const hi = Math.max(p.low, p.peak, p.high);
    const pk = Math.max(lo, Math.min(p.peak, hi));
    const span = hi - lo;
    if (span < 1e-12) return lo;
    const u = Math.random(), fc = (pk - lo) / span;
    return u < fc
      ? lo + Math.sqrt(u * span * (pk - lo))
      : hi - Math.sqrt((1 - u) * span * (hi - pk));
  }}
  if (DIST === 'normal') {{
    const raw = p.mean + Math.max(p.std_dev, 0) * boxMuller();
    return BASE > 0 ? BASE * (1 + raw) : raw;
  }}
  if (DIST === 'log-normal' || DIST === 'lognormal') {{
    const raw = Math.exp(p.mean + Math.max(p.sigma, 1e-9) * boxMuller());
    return BASE > 0 ? BASE * raw : raw;
  }}
  if (DIST === 'uniform') {{
    const lo = Math.min(p.low, p.high), hi = Math.max(p.low, p.high);
    return lo + Math.random() * (hi - lo);
  }}
  if (DIST === 'poisson') {{
    return poissonRng(Math.max(1e-9, p.lambda));
  }}
  if (DIST === 'weibull') {{
    const shape = Math.max(1e-6, p.shape), scale = Math.max(1e-9, p.scale);
    return scale * Math.pow(-Math.log(Math.random()), 1 / shape);
  }}
  if (DIST === 'beta') {{
    const a = Math.max(1e-6, p.alpha), b = Math.max(1e-6, p.beta);
    const x = gammaRng(a);
    return x / (x + gammaRng(b));
  }}
  if (DIST === 'exponential') {{
    return Math.max(1e-9, p.scale) * (-Math.log(Math.random()));
  }}
  return 0;
}}

function generateSamples(n, p) {{
  const a = new Float64Array(n);
  for (let i = 0; i < n; i++) a[i] = sampleOne(p);
  return a;
}}

// ── Statistics ────────────────────────────────────────────────────────────
function percentile(sorted, pct) {{
  const idx = (pct / 100) * (sorted.length - 1);
  const lo = Math.floor(idx), hi = Math.ceil(idx);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo);
}}

function computeStats(arr) {{
  const sorted = Float64Array.from(arr).sort();
  let sum = 0, sum2 = 0;
  for (const v of arr) {{ sum += v; sum2 += v*v; }}
  const n = arr.length, mean = sum/n;
  return {{
    p5:  percentile(sorted, 5),
    p50: percentile(sorted, 50),
    p95: percentile(sorted, 95),
    mean,
    std: Math.sqrt(Math.max(0, sum2/n - mean*mean)),
    n,
    sorted,
  }};
}}

// ── Histogram binning ─────────────────────────────────────────────────────
function makeBins(arr, nBins) {{
  let mn = Infinity, mx = -Infinity;
  for (const v of arr) {{ if (v < mn) mn = v; if (v > mx) mx = v; }}
  if (mn === mx) {{ mx = mn + 1; }}
  const w = (mx - mn) / nBins;
  const counts = new Array(nBins).fill(0);
  const labels = [];
  for (let i = 0; i < nBins; i++) labels.push((mn + (i+0.5)*w).toPrecision(4));
  for (const v of arr) {{
    let b = Math.floor((v - mn) / w);
    if (b >= nBins) b = nBins - 1;
    counts[b]++;
  }}
  return {{ labels, counts }};
}}

// ── Chart ─────────────────────────────────────────────────────────────────
const ctx = document.getElementById('mcChart').getContext('2d');
let chart = null;
let lastSamples = null;

// Current percentile values — written by updateCards(), read by the plugin.
const MARKERS = {{ p5: 0, p50: 0, p95: 0 }};

// afterDraw plugin: draws true vertical dashed lines for P5/P50/P95.
// Avoids the null-gap line-dataset hack (single isolated points are invisible
// when pointRadius=0 because there is nothing to draw a stroke between).
const percentilePlugin = {{
  id: 'percentileLines',
  afterDraw(ch) {{
    if (!ch.chartArea) return;
    const {{ ctx: c, chartArea: {{ top, bottom }}, scales: {{ x }} }} = ch;
    const defs = [
      {{ key: 'p5',  color: '#C44E52', label: 'P5' }},
      {{ key: 'p50', color: '#DD8452', label: 'P50' }},
      {{ key: 'p95', color: '#55A868', label: 'P95' }},
    ];
    defs.forEach(({{ key, color, label }}) => {{
      const val = MARKERS[key];
      const labels = ch.data.labels;
      if (!labels || !labels.length) return;
      // Find the label (bin centre) closest to this percentile value.
      let minDist = Infinity, bestLabel = labels[0];
      labels.forEach(l => {{
        const d = Math.abs(parseFloat(l) - val);
        if (d < minDist) {{ minDist = d; bestLabel = l; }}
      }});
      const px = x.getPixelForValue(bestLabel);
      // Draw the vertical line.
      c.save();
      c.beginPath();
      c.setLineDash([5, 4]);
      c.strokeStyle = color;
      c.lineWidth = 2;
      c.moveTo(px, top);
      c.lineTo(px, bottom);
      c.stroke();
      // Draw the label just above the chart area.
      c.font = 'bold 10px "Segoe UI", system-ui, sans-serif';
      c.fillStyle = color;
      c.textAlign = 'center';
      c.textBaseline = 'bottom';
      c.fillText(`${{label}}: ${{parseFloat(val.toPrecision(4)).toLocaleString()}}`, px, top - 2);
      c.restore();
    }});
  }}
}};

function initChart(labels, counts) {{
  Chart.register(percentilePlugin);
  chart = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels,
      datasets: [
        {{ label: 'Frequency', data: counts, backgroundColor: 'rgba(76,114,176,0.75)', borderWidth: 0 }},
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false, animation: {{ duration: 120 }},
      layout: {{ padding: {{ top: 24 }} }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{ callbacks: {{
          label: (c) => `Count: ${{c.parsed.y}}`,
          title: (items) => `~${{items[0].label}}`,
        }} }}
      }},
      scales: {{
        x: {{ title: {{ display: true, text: XLABEL }}, ticks: {{ maxTicksLimit: 12 }} }},
        y: {{ title: {{ display: true, text: 'Frequency' }}, beginAtZero: true }},
      }}
    }}
  }});
}}

function updateChart(labels, counts, st) {{
  if (!chart) {{ initChart(labels, counts); }}
  chart.data.labels = labels;
  chart.data.datasets[0].data = counts;
  chart.update();
}}

// ── Stats cards ───────────────────────────────────────────────────────────
function fmt(v) {{
  if (Math.abs(v) >= 1e6 || (Math.abs(v) < 0.001 && v !== 0)) return v.toExponential(3);
  return parseFloat(v.toPrecision(5)).toLocaleString();
}}

function updateCards(st) {{
  MARKERS.p5  = st.p5;
  MARKERS.p50 = st.p50;
  MARKERS.p95 = st.p95;
  document.getElementById('s-p5').textContent   = fmt(st.p5);
  document.getElementById('s-p50').textContent  = fmt(st.p50);
  document.getElementById('s-p95').textContent  = fmt(st.p95);
  document.getElementById('s-mean').textContent = fmt(st.mean);
  document.getElementById('s-std').textContent  = fmt(st.std);
  document.getElementById('s-n').textContent    = st.n.toLocaleString();
}}

// ── Threshold P(X < t) ────────────────────────────────────────────────────
function updateThreshold() {{
  const t = parseFloat(document.getElementById('thresholdVal').value);
  const el = document.getElementById('thresholdPct');
  if (!lastSamples || isNaN(t)) {{ el.textContent = '—'; return; }}
  let below = 0;
  for (const v of lastSamples) {{ if (v < t) below++; }}
  el.textContent = (below / lastSamples.length * 100).toFixed(1) + '%';
}}

// ── Label sync ────────────────────────────────────────────────────────────
function syncLabel(id, val, isInt) {{
  const el = document.getElementById('val-' + id);
  if (!el) return;
  const n = parseFloat(val);
  el.textContent = isInt ? Math.round(n).toLocaleString() : parseFloat(n.toPrecision(5)).toLocaleString();
}}

// ── Read current params from sliders ─────────────────────────────────────
function readParams() {{
  const p = {{}};
  Object.keys(PARAMS).forEach(k => {{
    const el = document.getElementById('ctrl-' + k);
    p[k] = el ? parseFloat(el.value) : PARAMS[k];
  }});
  return p;
}}

// ── Main resample + redraw ────────────────────────────────────────────────
function resample() {{
  const p = readParams();
  const n = parseInt(document.getElementById('ctrl-simulations').value, 10);
  lastSamples = generateSamples(n, p);
  const st  = computeStats(lastSamples);
  const {{ labels, counts }} = makeBins(lastSamples, BINS);
  updateCards(st);
  updateChart(labels, counts, st);
  updateThreshold();
}}

// ── Init ──────────────────────────────────────────────────────────────────
resample();
</script>
</body>
</html>
"""
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out


def _build_controls(
    dist: str,
    params: Mapping[str, Any],
    xlabel: str,
) -> tuple[str, dict[str, Any]]:
    """Return (controls_html, js_params) for the given distribution."""

    def slider(ctrl_id: str, label: str, val: float, lo: float, hi: float,
               step: float = 0.01, is_int: bool = False) -> str:
        fmt_val = str(int(val)) if is_int else f"{val:g}"
        onchange = f"syncLabel('{ctrl_id}',this.value,{str(is_int).lower()});resample()"
        return (
            f'      <div class="control-item">\n'
            f'        <label>{_escape(label)}'
            f' <span class="val" id="val-{ctrl_id}">{fmt_val}</span></label>\n'
            f'        <input type="range" id="ctrl-{ctrl_id}"'
            f' min="{lo}" max="{hi}" step="{step}" value="{val}"'
            f' oninput="{onchange}">\n'
            f'      </div>'
        )

    lines: list[str] = []
    js_params: dict[str, Any] = {}

    if dist == "triangular":
        low  = float(params.get("low",  0))
        peak = float(params.get("peak", 5))
        high = float(params.get("high", 10))
        span = high - low or 1.0
        lo_min, hi_max = low - span, high + span
        step = max(0.1, round(span / 100, 2))
        lines.append(slider("low",  f"Min ({xlabel})", low,  lo_min, peak, step))
        lines.append(slider("peak", f"Most likely ({xlabel})", peak, low, high, step))
        lines.append(slider("high", f"Max ({xlabel})", high, peak, hi_max, step))
        js_params = {"low": low, "peak": peak, "high": high}

    elif dist == "normal":
        mean    = float(params.get("mean",    0))
        std_dev = float(params.get("std_dev", 1))
        span = max(std_dev * 5, abs(mean) * 0.5, 1.0)
        step = max(0.01, round(span / 200, 4))
        lines.append(slider("mean",    f"Mean ({xlabel})", mean,    mean - span, mean + span, step))
        lines.append(slider("std_dev", "Std dev",          std_dev, 0.001,       std_dev * 4, max(step, 0.001)))
        js_params = {"mean": mean, "std_dev": std_dev}

    elif dist in ("log-normal", "lognormal"):
        mean  = float(params.get("mean",  0))
        sigma = float(params.get("sigma", 1))
        lines.append(slider("mean",  "Log mean (μ)",      mean,  mean - 3,  mean + 3,  0.05))
        lines.append(slider("sigma", "Log sigma (σ)",     sigma, 0.05, sigma * 4, 0.05))
        js_params = {"mean": mean, "sigma": sigma}

    elif dist == "uniform":
        low  = float(params.get("low",  0))
        high = float(params.get("high", 10))
        span = high - low or 1.0
        step = max(0.1, round(span / 100, 2))
        lines.append(slider("low",  f"Min ({xlabel})", low,  low - span, high,        step))
        lines.append(slider("high", f"Max ({xlabel})", high, low,        high + span, step))
        js_params = {"low": low, "high": high}

    elif dist == "poisson":
        lam = float(params.get("lambda", params.get("lam", 5.0)))
        step = max(0.1, round(lam / 20, 1))
        lines.append(slider("lambda", f"Mean rate λ ({xlabel})", lam,
                            max(0.1, lam * 0.1), max(lam * 5, 20), step))
        js_params = {"lambda": lam}

    elif dist == "weibull":
        shape = float(params.get("shape", 2.0))
        scale = float(params.get("scale", 1.0))
        step_sh = max(0.05, round(shape / 40, 2))
        step_sc = max(0.01, round(scale / 50, 4))
        lines.append(slider("shape", "Shape (k)",          shape, 0.2,
                            max(shape * 4, 10), step_sh))
        lines.append(slider("scale", f"Scale λ ({xlabel})", scale,
                            max(0.01, scale * 0.1), scale * 5, step_sc))
        js_params = {"shape": shape, "scale": scale}

    elif dist == "beta":
        alpha  = float(params.get("alpha", 2.0))
        beta_v = float(params.get("beta",  2.0))
        lines.append(slider("alpha", "Alpha (α)", alpha,  0.1,
                            max(alpha * 5, 20),  max(0.05, round(alpha  / 20, 2))))
        lines.append(slider("beta",  "Beta (β)",  beta_v, 0.1,
                            max(beta_v * 5, 20), max(0.05, round(beta_v / 20, 2))))
        js_params = {"alpha": alpha, "beta": beta_v}

    elif dist == "exponential":
        scale = float(params.get("scale", 1.0))
        step  = max(0.01, round(scale / 50, 4))
        lines.append(slider("scale", f"Mean / scale ({xlabel})", scale,
                            max(0.01, scale * 0.1), scale * 5, step))
        js_params = {"scale": scale}

    else:
        js_params = {}

    return "\n".join(lines), js_params


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )



def simulate(payload: PayloadLike) -> dict[str, Any]:
    """Run a full Monte Carlo job and write artefacts. Returns a summary dict."""
    data = _as_payload(payload)
    outcomes, distribution = sample_outcomes(data)
    stats = summarise(outcomes)

    prefix = str(data.get("out_prefix", "simulation"))
    chart_path = str(data.get("chart_path", f"{prefix}_density.png"))
    csv_path = str(data.get("csv_path", f"{prefix}_raw_data.csv"))
    title = str(data.get("chart_title", "Monte Carlo probability distribution"))
    xlabel = str(data.get("x_axis_label", "Simulated values"))
    bins = int(data.get("bins", 50))
    dpi = int(data.get("dpi", 150))

    save_histogram(
        outcomes, stats, title=title, xlabel=xlabel, out=chart_path, bins=bins, dpi=dpi,
    )
    save_csv(outcomes, csv_path)

    # `distribution` already normalised by sample_outcomes (e.g. "log-normal" not "lognormal")
    result: dict[str, Any] = {
        "mean": stats["mean"],
        "p5": stats["p5"],
        "p50": stats["p50"],
        "p95": stats["p95"],
        "simulations": int(len(outcomes)),
        "distribution": distribution,
        "brief_summary": brief_summary(
            stats,
            distribution=distribution,
            simulations=len(outcomes),
            unit=xlabel if xlabel != "Simulated values" else "",
        ),
        "chart_path": os.path.abspath(chart_path),
        "csv_path": os.path.abspath(csv_path),
    }

    want_html = bool(data.get("html", False))
    if want_html:
        html_path = str(data.get("html_path", f"{prefix}_interactive.html"))
        save_html(
            outcomes,
            stats,
            title=title,
            xlabel=xlabel,
            out=html_path,
            distribution=distribution,
            params=data,
            summary_text=result["brief_summary"],
        )
        result["html_path"] = os.path.abspath(html_path)

    want_excel = bool(data.get("excel", False))
    if want_excel:
        excel_path = str(data.get("excel_path", f"{prefix}_results.xlsx"))
        written = save_excel(
            outcomes, stats, excel_path, summary_text=result["brief_summary"],
        )
        if written:
            result["excel_path"] = os.path.abspath(written)
        else:
            result["excel_path"] = None
            result["excel_note"] = (
                "openpyxl not installed; use csv_path (opens in Excel) "
                "or `pip install openpyxl`."
            )

    return result


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run a Monte Carlo simulation and export chart + data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--payload", default=None, help="Path to a JSON payload file.")
    p.add_argument(
        "--distribution",
        choices=["triangular", "normal", "uniform", "log-normal", "lognormal",
                 "poisson", "weibull", "beta", "exponential"],
        default=None,
    )
    p.add_argument("--simulations", type=int, default=None)
    p.add_argument("--low", type=float, default=None)
    p.add_argument("--peak", type=float, default=None)
    p.add_argument("--high", type=float, default=None)
    p.add_argument("--mean", type=float, default=None)
    p.add_argument("--std-dev", type=float, default=None, dest="std_dev")
    p.add_argument("--sigma", type=float, default=None)
    p.add_argument("--lambda", type=float, default=None, dest="lam")
    p.add_argument("--shape", type=float, default=None)
    p.add_argument("--scale", type=float, default=None)
    p.add_argument("--alpha", type=float, default=None)
    p.add_argument("--beta", type=float, default=None)
    p.add_argument("--base-modifier", type=float, default=None, dest="base_modifier")
    p.add_argument("--title", default=None, dest="chart_title")
    p.add_argument("--xlabel", default=None, dest="x_axis_label")
    p.add_argument("--out-prefix", default="simulation", dest="out_prefix")
    p.add_argument("--html", action="store_true", help="Also write interactive HTML with live parameter controls.")
    p.add_argument("--excel", action="store_true", help="Also write .xlsx if openpyxl is available.")
    p.add_argument("--json-out", action="store_true", help="Print the result payload as JSON.")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.payload:
        data = _as_payload(args.payload)
    else:
        data = {}

    cli_map = {
        "distribution": args.distribution,
        "simulations": args.simulations,
        "low": args.low,
        "peak": args.peak,
        "high": args.high,
        "mean": args.mean,
        "std_dev": args.std_dev,
        "sigma": args.sigma,
        "lambda": args.lam,
        "shape": args.shape,
        "scale": args.scale,
        "alpha": args.alpha,
        "beta": args.beta,
        "base_modifier": args.base_modifier,
        "chart_title": args.chart_title,
        "x_axis_label": args.x_axis_label,
        "out_prefix": args.out_prefix,
    }
    for key, value in cli_map.items():
        if value is not None:
            data[key] = value

    if args.html:
        data["html"] = True
    if args.excel:
        data["excel"] = True

    if "distribution" not in data:
        raise SystemExit(
            "Provide --distribution or a --payload JSON that includes distribution."
        )

    result = simulate(data)
    if args.json_out:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"distribution={result['distribution']}  n={result['simulations']}\n"
            f"mean={result['mean']:.4g}  p5={result['p5']:.4g}  "
            f"p50={result['p50']:.4g}  p95={result['p95']:.4g}\n"
            f"summary: {result['brief_summary']}\n"
            f"chart={result['chart_path']}\n"
            f"csv={result['csv_path']}"
        )
        if result.get("html_path"):
            print(f"html={result['html_path']}")
        if result.get("excel_path"):
            print(f"excel={result['excel_path']}")
        elif result.get("excel_note"):
            print(f"excel={result['excel_note']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
