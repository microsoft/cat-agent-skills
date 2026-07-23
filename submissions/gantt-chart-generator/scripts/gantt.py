#!/usr/bin/env python3
"""Gantt chart generator — a drop-in companion to charts.py.

Follows the same conventions as the chart-builder skill's charts.py:
  - accepts a DataFrame or a path to a .csv / .tsv / .json file
  - keyword-only styling args (title, xlabel, ylabel, out, dpi, figsize, palette)
  - saves a PNG and returns the path; pass out=None to skip saving
  - headless (Agg backend), no display required

Input data must have one row per task/phase with at minimum:
  - a phase/task name column
  - a start-date column
  - an end-date column  (OR start + a duration-in-days column)

Optional columns:
  - a group column   → colour-codes bars by project / workstream
  - a completion-pct column  → draws a hatched "done" fill inside each bar

Import usage:
    from gantt import gantt

    gantt("schedule.csv",
          phase="Phase", start="Start", end="End",
          title="Project Schedule", out="schedule.png")

    # With group colouring and a today-line:
    gantt(df, phase="phase", start="planned_start", end="planned_end",
          group="project", today=True, out="multi_project.png")

    # End derived from duration (days) instead of an end column:
    gantt(df, phase="task", start="start_date", duration="days",
          out="schedule.png")

CLI usage:
    python gantt.py schedule.csv --phase Phase --start Start --end End
    python gantt.py schedule.csv --phase Phase --start Start --end End \\
        --group Project --today --title "My Schedule" --out gantt.png
    python gantt.py schedule.csv --phase task --start start_date \\
        --duration days --completion pct_done --out gantt.png

Dependencies: matplotlib, pandas. Runs headless (Agg backend).
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta, datetime
from typing import Optional, Sequence, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import matplotlib.dates as mdates        # noqa: E402
import matplotlib.patches as mpatches   # noqa: E402
import pandas as pd                      # noqa: E402

# Colorblind-friendly palette — matches charts.py for visual consistency.
PALETTE = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
    "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD",
]

TODAY_COLOUR = "#D62728"   # red dashed line
DONE_HATCH   = "////"      # hatch pattern for completed portion of a bar

DataLike = Union[pd.DataFrame, str]


# ── Shared plumbing (mirrors charts.py) ─────────────────────────────────────

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
    """Consistent, understated styling — matches charts.py."""
    plt.rcParams.update({
        "figure.facecolor":   "#f4f6f9",
        "axes.facecolor":     "#f4f6f9",
        "axes.edgecolor":     "#444444",
        "axes.grid":          True,
        "grid.color":         "#DDDDDD",
        "grid.linewidth":     0.8,
        "axes.axisbelow":     True,
        "axes.titlesize":     13,
        "axes.titleweight":   "bold",
        "axes.labelsize":     10,
        "xtick.labelsize":    9,
        "ytick.labelsize":    10,
        "legend.fontsize":    9,
        "legend.frameon":     True,
        "legend.framealpha":  0.85,
        "font.family":        "sans-serif",
    })


def save_fig(fig, out: Optional[str], dpi: int = 150) -> Optional[str]:
    """Save to `out` (returns the path) or leave figure open if out is None."""
    fig.tight_layout()
    if out:
        fig.savefig(out, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        return out
    return None


# ── Gantt chart ──────────────────────────────────────────────────────────────

def gantt(
    data: DataLike,
    phase: str,
    start: str,
    end: Optional[str] = None,
    *,
    duration: Optional[str] = None,
    group: Optional[str] = None,
    completion: Optional[str] = None,
    today: bool = True,
    today_date: Optional[date] = None,
    date_fmt: str = "%Y-%m-%d",
    title: str = "",
    xlabel: Optional[str] = "Timeline",
    ylabel: Optional[str] = None,
    out: Optional[str] = "gantt.png",
    dpi: int = 150,
    figsize: Optional[tuple[float, float]] = None,
    palette: Sequence[str] = PALETTE,
    bar_height: float = 0.55,
    annotate_dates: bool = True,
    annotate_duration: bool = True,
) -> Optional[str]:
    """Draw a horizontal Gantt chart and save it as a PNG.

    Parameters
    ----------
    data        : DataFrame or path to CSV/TSV/JSON. One row = one task/phase.
    phase       : Column name for task/phase labels (y-axis).
    start       : Column name for start dates (string or datetime).
    end         : Column name for end dates. Provide either `end` or `duration`.
    duration    : Column name for duration in days (used when `end` is absent).
    group       : Optional column to colour-code bars (e.g. project name).
                  When provided, each unique value gets a distinct colour and a
                  legend entry.
    completion  : Optional 0-100 column. Draws a hatched overlay showing the
                  completed portion of each bar.
    today       : Whether to draw a vertical "today" reference line.
    today_date  : Override for today's date (datetime.date). Defaults to
                  date.today().
    date_fmt    : strptime format for string date columns (default "%Y-%m-%d").
    title       : Chart title.
    xlabel      : X-axis label (default "Timeline").
    ylabel      : Y-axis label (default: value of `phase` column name).
    out         : Output file path. Pass None to skip saving.
    dpi         : Output resolution (default 150).
    figsize     : (width, height) in inches. Auto-sized from row count if omitted.
    palette     : List of hex colours. Cycles if more groups/phases than colours.
    bar_height  : Fractional height of each bar (0–1, default 0.55).
    annotate_dates    : Label start and end dates beside each bar.
    annotate_duration : Label duration in days inside each bar.

    Returns
    -------
    str | None  : Path to the saved PNG, or None if out=None.
    """
    df = load_data(data).dropna(subset=[phase, start])

    # ── Resolve end dates ────────────────────────────────────────────────────
    def _parse_dates(col: str) -> pd.Series:
        s = df[col]
        if pd.api.types.is_datetime64_any_dtype(s):
            return s
        try:
            return pd.to_datetime(s, format=date_fmt)
        except Exception:
            return pd.to_datetime(s)

    df["_start"] = _parse_dates(start)

    if end and end in df.columns:
        df["_end"] = _parse_dates(end)
    elif duration and duration in df.columns:
        df["_end"] = df["_start"] + pd.to_timedelta(df[duration].astype(int) - 1, unit="D")
    else:
        raise ValueError(
            "Provide either an `end` column (end dates) or a `duration` column "
            "(integer days). Neither was found in the data."
        )

    df["_days"] = (df["_end"] - df["_start"]).dt.days + 1

    # ── Colour mapping ───────────────────────────────────────────────────────
    if group and group in df.columns:
        groups   = df[group].astype(str).unique().tolist()
        colour_map = {g: palette[i % len(palette)] for i, g in enumerate(groups)}
        df["_colour"] = df[group].astype(str).map(colour_map)
    else:
        # Colour each phase distinctly from the palette
        phases_list = df[phase].astype(str).tolist()
        unique_phases = list(dict.fromkeys(phases_list))  # preserve order
        phase_colours = {p: palette[i % len(palette)] for i, p in enumerate(unique_phases)}
        df["_colour"] = df[phase].astype(str).map(phase_colours)
        colour_map = phase_colours
        groups = unique_phases

    # ── Figure & axes ────────────────────────────────────────────────────────
    n_rows = len(df)
    fig_h  = max(4.0, n_rows * 0.75 + 1.5)
    fig_w  = figsize[0] if figsize else 16.0
    fig_h  = figsize[1] if figsize else fig_h

    apply_theme()
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    # ── Draw bars ────────────────────────────────────────────────────────────
    for i, row in df.reset_index(drop=True).iterrows():
        y        = n_rows - 1 - i          # top-to-bottom order
        start_n  = mdates.date2num(row["_start"])
        end_n    = mdates.date2num(row["_end"])
        width    = end_n - start_n
        colour   = row["_colour"]

        # Main bar
        ax.barh(y, width, left=start_n, height=bar_height,
                color=colour, alpha=0.85, edgecolor="white", linewidth=1.0)

        # Completion hatch overlay (clamp to 0–100)
        if completion and completion in df.columns:
            raw = row.get(completion)
            pct = 0.0 if pd.isna(raw) else max(0.0, min(float(raw), 100.0)) / 100.0
            if pct > 0:
                ax.barh(y, width * pct, left=start_n, height=bar_height,
                        color=colour, alpha=0.40, edgecolor="white",
                        linewidth=0, hatch=DONE_HATCH)

        mid = start_n + width / 2.0

        # Duration label inside bar
        if annotate_duration:
            ax.text(mid, y, f"{int(row['_days'])}d",
                    ha="center", va="center",
                    fontsize=8, fontweight="bold", color="white",
                    clip_on=True)

        # Date labels flanking the bar
        if annotate_dates:
            ax.text(start_n - 0.5, y,
                    row["_start"].strftime("%d %b %Y"),
                    ha="right", va="center", fontsize=7, color="#555")
            ax.text(end_n + 0.5, y,
                    row["_end"].strftime("%d %b %Y"),
                    ha="left",  va="center", fontsize=7, color="#555")

    # ── Y-axis: phase labels ─────────────────────────────────────────────────
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(
        [str(p) for p in reversed(df[phase].astype(str).tolist())],
        fontsize=10, fontweight="bold",
    )
    ax.set_ylim(-0.75, n_rows - 0.25)

    # ── X-axis: date timeline ────────────────────────────────────────────────
    span_days = (df["_end"].max() - df["_start"].min()).days
    if span_days <= 90:
        locator   = mdates.WeekdayLocator(interval=2)
        formatter = mdates.DateFormatter("%d %b")
    elif span_days <= 365:
        locator   = mdates.MonthLocator()
        formatter = mdates.DateFormatter("%b\n%Y")
    else:
        locator   = mdates.MonthLocator(interval=2)
        formatter = mdates.DateFormatter("%b\n%Y")

    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax.tick_params(axis="x", labelsize=9)

    pad = timedelta(days=max(14, span_days // 20))
    ax.set_xlim(
        mdates.date2num(df["_start"].min() - pad),
        mdates.date2num(df["_end"].max()   + pad),
    )

    # ── Today line ───────────────────────────────────────────────────────────
    if today:
        t = today_date or date.today()
        t_num = mdates.date2num(datetime.combine(t, datetime.min.time()))
        ax.axvline(t_num, color=TODAY_COLOUR, linewidth=1.6,
                   linestyle="--", zorder=5,
                   label=f"Today ({t.strftime('%d %b %Y')})")

    # ── Legend ───────────────────────────────────────────────────────────────
    handles = [
        mpatches.Patch(color=palette[i % len(palette)], label=g)
        for i, g in enumerate(groups)
    ]
    if today:
        handles.append(
            mpatches.Patch(color=TODAY_COLOUR,
                           label=f"Today ({(today_date or date.today()).strftime('%d %b %Y')})")
        )
    if completion:
        handles.append(
            mpatches.Patch(facecolor="#aaa", hatch=DONE_HATCH, alpha=0.6,
                           label="% Complete")
        )
    ncol = min(len(handles), 5)
    ax.legend(handles=handles, loc="lower right", ncol=ncol, fontsize=8.5)

    # ── Labels, title, spines ────────────────────────────────────────────────
    if title:
        ax.set_title(title, pad=12)
    ax.set_xlabel(xlabel or "Timeline", fontsize=10)
    ax.set_ylabel(ylabel or phase, fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", linestyle="--", alpha=0.45)

    return save_fig(fig, out, dpi)


# ── CLI ──────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate a Gantt chart from a CSV/TSV/JSON schedule file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("data",       help="Path to a .csv/.tsv/.json file.")
    p.add_argument("--phase",    required=True, help="Column: task/phase name.")
    p.add_argument("--start",    required=True, help="Column: start date.")
    p.add_argument("--end",      default=None,  help="Column: end date.")
    p.add_argument("--duration", default=None,  help="Column: duration in days (alternative to --end).")
    p.add_argument("--group",    default=None,  help="Column: group/project for colour-coding.")
    p.add_argument("--completion", default=None, help="Column: 0–100 completion percentage.")
    p.add_argument("--today",    action="store_true", default=True,
                   help="Draw a vertical today line (default: on).")
    p.add_argument("--no-today", action="store_false", dest="today",
                   help="Suppress the today line.")
    p.add_argument("--today-date", default=None,
                   help="Override today's date (YYYY-MM-DD).")
    p.add_argument("--date-fmt", default="%Y-%m-%d",
                   help="strptime format for date columns (default: %%Y-%%m-%%d).")
    p.add_argument("--title",    default="",    help="Chart title.")
    p.add_argument("--xlabel",   default="Timeline", help="X-axis label.")
    p.add_argument("--ylabel",   default=None,  help="Y-axis label.")
    p.add_argument("--out",      default="gantt.png", help="Output image path.")
    p.add_argument("--dpi",      type=int, default=150, help="Output DPI.")
    p.add_argument("--figsize",  default=None,  nargs=2, type=float,
                   metavar=("W", "H"), help="Figure size in inches, e.g. 16 8.")
    p.add_argument("--bar-height", type=float, default=0.55,
                   help="Fractional bar height (0–1, default 0.55).")
    p.add_argument("--no-dates",    action="store_false", dest="annotate_dates",
                   help="Suppress start/end date labels beside bars.")
    p.add_argument("--no-duration", action="store_false", dest="annotate_duration",
                   help="Suppress duration-in-days labels inside bars.")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    today_date = None
    if args.today_date:
        today_date = datetime.strptime(args.today_date, "%Y-%m-%d").date()

    path = gantt(
        args.data,
        phase=args.phase,
        start=args.start,
        end=args.end,
        duration=args.duration,
        group=args.group,
        completion=args.completion,
        today=args.today,
        today_date=today_date,
        date_fmt=args.date_fmt,
        title=args.title,
        xlabel=args.xlabel,
        ylabel=args.ylabel,
        out=args.out,
        dpi=args.dpi,
        figsize=tuple(args.figsize) if args.figsize else None,
        bar_height=args.bar_height,
        annotate_dates=args.annotate_dates,
        annotate_duration=args.annotate_duration,
    )
    print(f"Saved: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
