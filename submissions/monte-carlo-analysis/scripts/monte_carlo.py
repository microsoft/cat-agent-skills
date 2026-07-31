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
from typing import Any, Mapping, MutableMapping, Optional, Sequence, Union

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
        if text.startswith("{") or text.startswith("["):
            return json.loads(text)
        with open(source, encoding="utf-8") as fh:
            return json.load(fh)
    raise TypeError(
        f"Unsupported payload: {type(source)!r}. "
        "Pass a dict, JSON string, or path to a .json file."
    )


def sample_outcomes(data: MutableMapping[str, Any]) -> np.ndarray:
    """Draw Monte Carlo samples from the requested distribution."""
    simulations = int(data.get("simulations", 10_000))
    if simulations < 1:
        raise ValueError("`simulations` must be a positive integer.")
    distribution = str(data.get("distribution", "triangular")).lower().replace("_", "-")
    base_modifier = float(data.get("base_modifier", 0.0))

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
        return raw + base_modifier

    if distribution == "normal":
        if "mean" not in data or "std_dev" not in data:
            raise ValueError("Normal distribution requires `mean` and `std_dev`.")
        mean = float(data["mean"])
        std_dev = float(data["std_dev"])
        if std_dev < 0:
            raise ValueError("`std_dev` must be >= 0.")
        raw = np.random.normal(mean, std_dev, simulations)
        if base_modifier > 0:
            return base_modifier * (1.0 + raw)
        return raw

    if distribution in ("log-normal", "lognormal"):
        if "mean" not in data or "sigma" not in data:
            raise ValueError("Log-normal distribution requires `mean` and `sigma`.")
        mean = float(data["mean"])
        sigma = float(data["sigma"])
        if sigma < 0:
            raise ValueError("`sigma` must be >= 0.")
        raw = np.random.lognormal(mean, sigma, simulations)
        if base_modifier > 0:
            return base_modifier * raw
        return raw

    if distribution == "uniform":
        if "low" not in data or "high" not in data:
            raise ValueError("Uniform distribution requires `low` and `high`.")
        low, high = float(data["low"]), float(data["high"])
        if high < low:
            raise ValueError("Uniform requires high >= low.")
        return np.random.uniform(low, high, simulations) + base_modifier

    raise ValueError(
        f"Distribution type '{distribution}' is unsupported. "
        "Use triangular, normal, uniform, or log-normal."
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


def _histogram_bins(outcomes: np.ndarray, bins: int = 50) -> tuple[list[str], list[int]]:
    counts, edges = np.histogram(outcomes, bins=bins)
    labels = [
        f"{(edges[i] + edges[i + 1]) / 2:.4g}" for i in range(len(counts))
    ]
    return labels, [int(c) for c in counts]


def save_html(
    outcomes: np.ndarray,
    stats: Mapping[str, float],
    *,
    title: str,
    xlabel: str,
    out: str,
    mode: str = "histogram",
    paths: int = 50,
    steps: int = 10,
    seed_start: Optional[float] = None,
    summary_text: str = "",
) -> str:
    """Write a self-contained Chart.js HTML page (histogram or fan paths)."""
    mode = (mode or "histogram").lower()
    if mode == "fan":
        chart_block = _fan_chart_js(
            outcomes, title=title, xlabel=xlabel,
            paths=paths, steps=steps, seed_start=seed_start,
        )
    else:
        labels, counts = _histogram_bins(outcomes)
        chart_block = _histogram_chart_js(
            labels, counts, stats, title=title, xlabel=xlabel,
        )

    summary_html = (
        f'<p class="summary">{_escape(summary_text)}</p>' if summary_text else ""
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{_escape(title)}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    body {{
      font-family: "Segoe UI", system-ui, sans-serif;
      margin: 0; padding: 24px;
      background: #f4f6f9; color: #222;
    }}
    .wrap {{
      max-width: 960px; margin: 0 auto; background: #fff;
      padding: 24px 28px; border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }}
    h1 {{ font-size: 1.35rem; margin: 0 0 8px; }}
    .meta {{ color: #555; font-size: 0.95rem; margin-bottom: 16px; }}
    .summary {{
      background: #eef3f9; border-left: 4px solid #4C72B0;
      padding: 12px 14px; margin: 0 0 18px; line-height: 1.45;
      font-size: 0.95rem;
    }}
    .stats {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 10px; margin-bottom: 20px;
    }}
    .stat {{
      background: #f4f6f9; border-radius: 6px; padding: 10px 12px;
    }}
    .stat span {{ display: block; font-size: 0.75rem; color: #666; }}
    .stat strong {{ font-size: 1.1rem; }}
    .chart-box {{ position: relative; height: 420px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>{_escape(title)}</h1>
    <p class="meta">Interactive Monte Carlo view — Chart.js. Open this file in a browser.</p>
    {summary_html}
    <div class="stats">
      <div class="stat"><span>P5</span><strong>{stats['p5']:.4g}</strong></div>
      <div class="stat"><span>P50</span><strong>{stats['p50']:.4g}</strong></div>
      <div class="stat"><span>P95</span><strong>{stats['p95']:.4g}</strong></div>
      <div class="stat"><span>Mean</span><strong>{stats['mean']:.4g}</strong></div>
      <div class="stat"><span>Iterations</span><strong>{len(outcomes):,}</strong></div>
    </div>
    <div class="chart-box"><canvas id="mcChart"></canvas></div>
  </div>
  <script>
{chart_block}
  </script>
</body>
</html>
"""
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _histogram_chart_js(
    labels: Sequence[str],
    counts: Sequence[int],
    stats: Mapping[str, float],
    *,
    title: str,
    xlabel: str,
) -> str:
    return f"""
const labels = {json.dumps(list(labels))};
const counts = {json.dumps(list(counts))};
const ctx = document.getElementById('mcChart').getContext('2d');
new Chart(ctx, {{
  type: 'bar',
  data: {{
    labels,
    datasets: [{{
      label: 'Frequency',
      data: counts,
      backgroundColor: 'rgba(76, 114, 176, 0.75)',
      borderWidth: 0
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      title: {{ display: true, text: {_js_str(title)} }},
      legend: {{ display: false }},
      tooltip: {{
        callbacks: {{
          afterBody: () => [
            'P5: {stats["p5"]:.4g}',
            'P50: {stats["p50"]:.4g}',
            'P95: {stats["p95"]:.4g}'
          ]
        }}
      }}
    }},
    scales: {{
      x: {{ title: {{ display: true, text: {_js_str(xlabel)} }}, ticks: {{ maxTicksLimit: 12 }} }},
      y: {{ title: {{ display: true, text: 'Frequency' }}, beginAtZero: true }}
    }}
  }}
}});
"""


def _fan_chart_js(
    outcomes: np.ndarray,
    *,
    title: str,
    xlabel: str,
    paths: int,
    steps: int,
    seed_start: Optional[float],
) -> str:
    """Build translucent path lines from sampled terminal growth rates."""
    rng = np.random.default_rng(42)
    n_paths = max(1, min(int(paths), 200))
    n_steps = max(2, int(steps))
    start = float(seed_start) if seed_start is not None else float(np.median(outcomes))

    # Treat each sample as a relative end-factor vs start; interpolate geometric path.
    factors = outcomes / max(start, 1e-12)
    pick = rng.choice(factors, size=n_paths, replace=True)

    series = []
    for f in pick:
        # Constant per-step growth that lands at factor f after n_steps.
        step_g = float(f) ** (1.0 / n_steps) - 1.0
        vals = [start]
        cur = start
        for _ in range(n_steps):
            cur = cur * (1.0 + step_g)
            vals.append(float(cur))
        series.append(vals)

    year_labels = [f"Step {i}" for i in range(n_steps + 1)]
    datasets_js = []
    for i, path in enumerate(series):
        datasets_js.append({
            "label": "Simulated paths" if i == 0 else "",
            "data": path,
            "borderColor": "rgba(0, 120, 212, 0.18)",
            "borderWidth": 1.5,
            "fill": False,
            "pointRadius": 0,
        })

    return f"""
const labels = {json.dumps(year_labels)};
const datasets = {json.dumps(datasets_js)};
const ctx = document.getElementById('mcChart').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {{ labels, datasets }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      title: {{ display: true, text: {_js_str(title)} }},
      legend: {{
        labels: {{ filter: (item) => item.text !== '' }}
      }}
    }},
    scales: {{
      x: {{ title: {{ display: true, text: {_js_str(xlabel or 'Timeline')} }} }},
      y: {{ title: {{ display: true, text: 'Value' }} }}
    }}
  }}
}});
"""


def _js_str(value: str) -> str:
    return json.dumps(value)


def simulate(payload: PayloadLike) -> dict[str, Any]:
    """Run a full Monte Carlo job and write artefacts. Returns a summary dict."""
    data = _as_payload(payload)
    outcomes = sample_outcomes(data)
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

    distribution = str(data.get("distribution", "triangular")).lower()
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
            mode=str(data.get("html_mode", "histogram")),
            paths=int(data.get("fan_paths", 50)),
            steps=int(data.get("fan_steps", 10)),
            seed_start=data.get("fan_start"),
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
        choices=["triangular", "normal", "uniform", "log-normal", "lognormal"],
        default=None,
    )
    p.add_argument("--simulations", type=int, default=None)
    p.add_argument("--low", type=float, default=None)
    p.add_argument("--peak", type=float, default=None)
    p.add_argument("--high", type=float, default=None)
    p.add_argument("--mean", type=float, default=None)
    p.add_argument("--std-dev", type=float, default=None, dest="std_dev")
    p.add_argument("--sigma", type=float, default=None)
    p.add_argument("--base-modifier", type=float, default=None, dest="base_modifier")
    p.add_argument("--title", default=None, dest="chart_title")
    p.add_argument("--xlabel", default=None, dest="x_axis_label")
    p.add_argument("--out-prefix", default="simulation", dest="out_prefix")
    p.add_argument("--html", action="store_true", help="Also write interactive HTML.")
    p.add_argument(
        "--html-mode",
        choices=["histogram", "fan"],
        default="histogram",
        help="HTML chart style (default: histogram).",
    )
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
        data["html_mode"] = args.html_mode
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
