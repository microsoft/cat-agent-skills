#!/usr/bin/env python3
"""Quick, consistently-styled matplotlib charts from a DataFrame or CSV.

This is a *thin, parameterized* toolkit: you don't pre-know the data's
dimensions or column names. Each function takes tidy data plus the column
names to plot and a small config, then owns all the matplotlib plumbing —
theming, sensible defaults, auto figure sizing, label rotation, NaN handling,
and saving to a file. Import the functions, or drive them from the CLI.

Charts: bar, grouped_bar (with stacked option), line, scatter, histogram, pie.

Import usage:
    import pandas as pd
    from charts import bar
    bar("sales.csv", x="region", y="revenue", out="revenue.png",
        title="Revenue by region")

CLI usage:
    python charts.py bar sales.csv --x region --y revenue --out revenue.png
    python charts.py grouped_bar sales.csv --x region --y revenue \
        --group quarter --stacked --out by_quarter.png
    python charts.py line sales.csv --x month --y revenue --group region
    python charts.py scatter sales.csv --x spend --y revenue
    python charts.py histogram sales.csv --y revenue --bins 20
    python charts.py pie sales.csv --x region --y revenue

Dependencies: matplotlib, pandas. Runs headless (Agg backend).
"""
from __future__ import annotations

import argparse
from typing import Optional, Sequence, Union

import matplotlib

matplotlib.use("Agg")  # headless: works in agent sandboxes with no display
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

# A calm, colorblind-friendly palette reused across every chart for coherence.
PALETTE = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
    "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD",
]

DataLike = Union[pd.DataFrame, str]


# --------------------------------------------------------------------------- #
# Shared plumbing
# --------------------------------------------------------------------------- #
def load_data(source: DataLike) -> pd.DataFrame:
    """Accept a DataFrame directly, or a path to a .csv/.tsv/.json file."""
    if isinstance(source, pd.DataFrame):
        return source.copy()
    if isinstance(source, str):
        lower = source.lower()
        if lower.endswith(".tsv"):
            return pd.read_csv(source, sep="\t")
        if lower.endswith(".json"):
            return pd.read_json(source)
        return pd.read_csv(source)
    raise TypeError(
        f"Unsupported data source: {type(source)!r}. "
        "Pass a pandas DataFrame or a path to a .csv/.tsv/.json file."
    )


def apply_theme() -> None:
    """Consistent, understated styling applied before each figure is drawn."""
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#444444",
            "axes.grid": True,
            "grid.color": "#E6E6E6",
            "grid.linewidth": 0.8,
            "axes.axisbelow": True,
            "axes.titlesize": 14,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "legend.frameon": False,
            "font.family": "sans-serif",
        }
    )


def _figsize(n_items: int, base: float = 6.5, per_item: float = 0.45,
             height: float = 4.5) -> tuple[float, float]:
    """Grow width with the number of categories so labels stay readable."""
    width = max(base, min(20.0, per_item * max(n_items, 1) + 3.0))
    return (width, height)


def _finalize(ax, title, xlabel, ylabel) -> None:
    if title:
        ax.set_title(title)
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _rotate_if_crowded(ax, labels: Sequence) -> None:
    """Rotate x tick labels when they're numerous or long, to avoid overlap."""
    longest = max((len(str(x)) for x in labels), default=0)
    if len(labels) > 6 or longest > 8:
        for tick in ax.get_xticklabels():
            tick.set_rotation(45)
            tick.set_ha("right")


def save_fig(fig, out: Optional[str], dpi: int = 150) -> Optional[str]:
    """Save to `out` (returns the path) or leave the figure open if out is None."""
    fig.tight_layout()
    if out:
        fig.savefig(out, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        return out
    return None


def _new_fig(figsize):
    apply_theme()
    return plt.subplots(figsize=figsize)


# --------------------------------------------------------------------------- #
# Chart functions
# --------------------------------------------------------------------------- #
def bar(
    data: DataLike,
    x: str,
    y: str,
    *,
    title: str = "",
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    out: Optional[str] = "chart.png",
    dpi: int = 150,
    figsize: Optional[tuple[float, float]] = None,
    palette: Sequence[str] = PALETTE,
    horizontal: bool = False,
) -> Optional[str]:
    """Single-series bar chart of `y` per category `x`."""
    df = load_data(data).dropna(subset=[x, y])
    cats, vals = df[x].astype(str).tolist(), df[y].tolist()
    fig, ax = _new_fig(figsize or _figsize(len(cats)))
    color = palette[0]
    if horizontal:
        ax.barh(cats, vals, color=color)
        ax.invert_yaxis()
        _finalize(ax, title, xlabel if xlabel is not None else y,
                  ylabel if ylabel is not None else x)
    else:
        ax.bar(cats, vals, color=color)
        _rotate_if_crowded(ax, cats)
        _finalize(ax, title, xlabel if xlabel is not None else x,
                  ylabel if ylabel is not None else y)
    return save_fig(fig, out, dpi)


def grouped_bar(
    data: DataLike,
    x: str,
    y: str,
    group: str,
    *,
    stacked: bool = False,
    title: str = "",
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    out: Optional[str] = "chart.png",
    dpi: int = 150,
    figsize: Optional[tuple[float, float]] = None,
    palette: Sequence[str] = PALETTE,
) -> Optional[str]:
    """Grouped or stacked bars: `y` per `x`, split into series by `group`."""
    df = load_data(data).dropna(subset=[x, y, group])
    pivot = df.pivot_table(index=x, columns=group, values=y, aggfunc="sum")
    cats = [str(c) for c in pivot.index]
    series = list(pivot.columns)
    fig, ax = _new_fig(figsize or _figsize(len(cats) * max(1, len(series) // 2)))

    if stacked:
        bottom = [0.0] * len(cats)
        for i, s in enumerate(series):
            vals = pivot[s].fillna(0).tolist()
            ax.bar(cats, vals, bottom=bottom, label=str(s),
                   color=palette[i % len(palette)])
            bottom = [b + v for b, v in zip(bottom, vals)]
    else:
        n = len(series)
        width = 0.8 / max(n, 1)
        positions = range(len(cats))
        for i, s in enumerate(series):
            vals = pivot[s].fillna(0).tolist()
            offsets = [p + (i - (n - 1) / 2) * width for p in positions]
            ax.bar(offsets, vals, width=width, label=str(s),
                   color=palette[i % len(palette)])
        ax.set_xticks(list(positions))
        ax.set_xticklabels(cats)

    _rotate_if_crowded(ax, cats)
    _finalize(ax, title, xlabel if xlabel is not None else x,
              ylabel if ylabel is not None else y)
    _legend(ax, len(series), title=group)
    return save_fig(fig, out, dpi)


def line(
    data: DataLike,
    x: str,
    y: str,
    *,
    group: Optional[str] = None,
    title: str = "",
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    out: Optional[str] = "chart.png",
    dpi: int = 150,
    figsize: Optional[tuple[float, float]] = None,
    palette: Sequence[str] = PALETTE,
    markers: bool = True,
) -> Optional[str]:
    """Line chart of `y` over `x`; pass `group` to draw one line per series."""
    df = load_data(data).dropna(subset=[x, y])
    fig, ax = _new_fig(figsize or (8.0, 4.5))
    marker = "o" if markers else None
    if group:
        for i, (key, sub) in enumerate(df.groupby(group)):
            sub = sub.sort_values(x)
            ax.plot(sub[x], sub[y], marker=marker, label=str(key),
                    color=palette[i % len(palette)])
        _legend(ax, df[group].nunique(), title=group)
    else:
        df = df.sort_values(x)
        ax.plot(df[x], df[y], marker=marker, color=palette[0])
    _rotate_if_crowded(ax, df[x].astype(str).unique())
    _finalize(ax, title, xlabel if xlabel is not None else x,
              ylabel if ylabel is not None else y)
    return save_fig(fig, out, dpi)


def scatter(
    data: DataLike,
    x: str,
    y: str,
    *,
    group: Optional[str] = None,
    size: Optional[str] = None,
    title: str = "",
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    out: Optional[str] = "chart.png",
    dpi: int = 150,
    figsize: Optional[tuple[float, float]] = None,
    palette: Sequence[str] = PALETTE,
) -> Optional[str]:
    """Scatter of `y` vs `x`; optional `group` (color) and `size` columns."""
    df = load_data(data).dropna(subset=[x, y])
    fig, ax = _new_fig(figsize or (7.0, 5.0))
    sizes = None
    if size and size in df.columns:
        s = df[size].astype(float)
        rng = s.max() - s.min()
        sizes = (20 + 180 * (s - s.min()) / rng) if rng else 60
    if group:
        for i, (key, sub) in enumerate(df.groupby(group)):
            sub_sizes = None
            if sizes is not None:
                sub_sizes = sizes.loc[sub.index]
            ax.scatter(sub[x], sub[y], s=sub_sizes, alpha=0.75,
                       label=str(key), color=palette[i % len(palette)])
        _legend(ax, df[group].nunique(), title=group)
    else:
        ax.scatter(df[x], df[y], s=sizes, alpha=0.75, color=palette[0])
    _finalize(ax, title, xlabel if xlabel is not None else x,
              ylabel if ylabel is not None else y)
    return save_fig(fig, out, dpi)


def histogram(
    data: DataLike,
    y: str,
    *,
    bins: int = 20,
    group: Optional[str] = None,
    title: str = "",
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    out: Optional[str] = "chart.png",
    dpi: int = 150,
    figsize: Optional[tuple[float, float]] = None,
    palette: Sequence[str] = PALETTE,
) -> Optional[str]:
    """Distribution of numeric column `y`; pass `group` to overlay series."""
    df = load_data(data).dropna(subset=[y])
    fig, ax = _new_fig(figsize or (7.0, 4.5))
    if group:
        for i, (key, sub) in enumerate(df.groupby(group)):
            ax.hist(sub[y], bins=bins, alpha=0.55, label=str(key),
                    color=palette[i % len(palette)])
        _legend(ax, df[group].nunique(), title=group)
    else:
        ax.hist(df[y], bins=bins, color=palette[0], edgecolor="white")
    _finalize(ax, title, xlabel if xlabel is not None else y,
              ylabel if ylabel is not None else "Frequency")
    return save_fig(fig, out, dpi)


def pie(
    data: DataLike,
    x: str,
    y: str,
    *,
    title: str = "",
    out: Optional[str] = "chart.png",
    dpi: int = 150,
    figsize: Optional[tuple[float, float]] = None,
    palette: Sequence[str] = PALETTE,
    donut: bool = False,
    max_slices: int = 8,
) -> Optional[str]:
    """Pie/donut of `y` share per category `x`. Small slices roll into 'Other'."""
    df = load_data(data).dropna(subset=[x, y])
    grouped = df.groupby(x)[y].sum().sort_values(ascending=False)
    if len(grouped) > max_slices:
        top = grouped.iloc[: max_slices - 1]
        other = grouped.iloc[max_slices - 1:].sum()
        grouped = pd.concat([top, pd.Series({"Other": other})])
    labels = [str(i) for i in grouped.index]
    fig, ax = _new_fig(figsize or (6.5, 6.5))
    wedge = {"width": 0.42} if donut else None
    ax.pie(
        grouped.values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=[palette[i % len(palette)] for i in range(len(labels))],
        wedgeprops=wedge,
        pctdistance=0.8 if donut else 0.6,
    )
    ax.set_aspect("equal")
    ax.grid(False)
    if title:
        ax.set_title(title)
    return save_fig(fig, out, dpi)


def _legend(ax, n_series: int, title: Optional[str] = None) -> None:
    """Place the legend outside the axes when there are many series."""
    if n_series > 4:
        ax.legend(title=title, loc="center left", bbox_to_anchor=(1.02, 0.5))
    else:
        ax.legend(title=title, loc="best")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate a matplotlib chart.")
    p.add_argument(
        "chart",
        choices=["bar", "grouped_bar", "line", "scatter", "histogram", "pie"],
    )
    p.add_argument("data", help="Path to a .csv/.tsv/.json file.")
    p.add_argument("--x", help="Category / x-axis column.")
    p.add_argument("--y", help="Value / y-axis column.")
    p.add_argument("--group", help="Column to split into series.")
    p.add_argument("--size", help="scatter: column controlling marker size.")
    p.add_argument("--bins", type=int, default=20, help="histogram: bin count.")
    p.add_argument("--stacked", action="store_true", help="grouped_bar: stack.")
    p.add_argument("--horizontal", action="store_true", help="bar: horizontal.")
    p.add_argument("--donut", action="store_true", help="pie: donut style.")
    p.add_argument("--title", default="", help="Chart title.")
    p.add_argument("--xlabel", help="Override x-axis label.")
    p.add_argument("--ylabel", help="Override y-axis label.")
    p.add_argument("--out", default="chart.png", help="Output image path.")
    p.add_argument("--dpi", type=int, default=150, help="Output DPI.")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    common = dict(
        title=args.title, xlabel=args.xlabel, ylabel=args.ylabel,
        out=args.out, dpi=args.dpi,
    )
    if args.chart == "bar":
        _require(args, "x", "y")
        path = bar(args.data, x=args.x, y=args.y,
                   horizontal=args.horizontal, **common)
    elif args.chart == "grouped_bar":
        _require(args, "x", "y", "group")
        path = grouped_bar(args.data, x=args.x, y=args.y, group=args.group,
                           stacked=args.stacked, **common)
    elif args.chart == "line":
        _require(args, "x", "y")
        path = line(args.data, x=args.x, y=args.y, group=args.group, **common)
    elif args.chart == "scatter":
        _require(args, "x", "y")
        path = scatter(args.data, x=args.x, y=args.y, group=args.group,
                       size=args.size, **common)
    elif args.chart == "histogram":
        _require(args, "y")
        path = histogram(args.data, y=args.y, bins=args.bins,
                         group=args.group, **common)
    else:  # pie
        _require(args, "x", "y")
        path = pie(args.data, x=args.x, y=args.y, title=args.title,
                   out=args.out, dpi=args.dpi, donut=args.donut)
    print(f"Saved: {path}")
    return 0


def _require(args, *names: str) -> None:
    missing = [f"--{n}" for n in names if getattr(args, n) in (None, "")]
    if missing:
        raise SystemExit(
            f"{args.chart} requires {', '.join(missing)}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
