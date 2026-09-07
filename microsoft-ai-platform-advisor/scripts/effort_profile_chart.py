"""
Effort Profile Chart — Microsoft AI Platform Advisor

Renders a 2x2 quadrant chart plotting a project's technical complexity against
its risk score, with each quadrant labeled with planning guidance. The project
is plotted as a labeled orange point and the image is saved as effort_profile.png.

Usage (Copilot Studio code interpreter, or any Python 3 environment with
matplotlib installed). Pass the three values the agent collected during the
discovery interview:

    python effort_profile_chart.py --project-name "Contoso Field Agent" \
        --complexity 7 --risk 4

Inputs:
    --project-name   string, from discovery Q1
    --complexity     integer 0-10, from Phase 3 sum
    --risk           integer 0-10, from Phase 4 sum
    --out            output PNG path (default: effort_profile.png)

Running with no arguments renders a sample chart so the script is always
runnable for validation.
"""

import argparse

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
    return max(low, min(high, value))


def render(project_name: str, complexity: float, risk: float, out: str) -> str:
    complexity = clamp(complexity)
    risk = clamp(risk)

    fig, ax = plt.subplots(figsize=(11, 8))

    # Quadrant background fills (soft colors)
    ax.add_patch(Rectangle((0, 5), 5, 5, facecolor="#fdecea", alpha=0.5, zorder=0))
    ax.add_patch(Rectangle((5, 5), 5, 5, facecolor="#f3e5f5", alpha=0.5, zorder=0))
    ax.add_patch(Rectangle((0, 0), 5, 5, facecolor="#e8f5e9", alpha=0.5, zorder=0))
    ax.add_patch(Rectangle((5, 0), 5, 5, facecolor="#e3f2fd", alpha=0.5, zorder=0))

    # Quadrant labels (title + guidance underneath)
    label_style = dict(ha="center", va="center", fontsize=10, wrap=True)

    ax.text(2.5, 8.2, "GOVERN HARD, SHIP FAST",
            fontweight="bold", color="#c92a2a", fontsize=11, ha="center")
    ax.text(2.5, 7.2, "Agent 365 blueprint + DLP\nfrom day one",
            color="#c92a2a", **label_style)

    ax.text(7.5, 8.2, "PoC → PHASED ROLLOUT",
            fontweight="bold", color="#862e9c", fontsize=11, ha="center")
    ax.text(7.5, 7.2, "Exec sponsor, dedicated ALM,\nevaluations before every release",
            color="#862e9c", **label_style)

    ax.text(2.5, 3.2, "MOVE FAST, ITERATE",
            fontweight="bold", color="#2b8a3e", fontsize=11, ha="center")
    ax.text(2.5, 2.2, "Pilot with one team,\nexpand quickly",
            color="#2b8a3e", **label_style)

    ax.text(7.5, 3.2, "INVEST IN ENGINEERING",
            fontweight="bold", color="#1864ab", fontsize=11, ha="center")
    ax.text(7.5, 2.2, "Foundry + evaluations,\nclear ALM environments",
            color="#1864ab", **label_style)

    # Quadrant dividers (dashed)
    ax.axhline(y=5, color="#a0a0a0", linestyle="--", linewidth=1, zorder=1)
    ax.axvline(x=5, color="#a0a0a0", linestyle="--", linewidth=1, zorder=1)

    # Plot the project point
    ax.scatter([complexity], [risk],
               s=400, c="#ff922b", edgecolors="#1e1e1e", linewidths=2, zorder=5)
    ax.annotate(f"  {project_name}\n  ({complexity:g}/10, {risk:g}/10)",
                xy=(complexity, risk),
                xytext=(10, 10), textcoords="offset points",
                fontsize=11, fontweight="bold", zorder=6,
                bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                          edgecolor="#1e1e1e", linewidth=1))

    # Axes formatting
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_xticks(range(0, 11))
    ax.set_yticks(range(0, 11))
    ax.set_xlabel("Technical complexity  →", fontsize=13, fontweight="bold")
    ax.set_ylabel("Risk  →", fontsize=13, fontweight="bold")
    ax.set_title(f"{project_name} — Effort Profile",
                 fontsize=16, fontweight="bold", pad=15)
    ax.grid(True, alpha=0.2)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the effort-profile quadrant chart.")
    parser.add_argument("--project-name", default="Sample Project",
                        help="Project name from discovery Q1")
    parser.add_argument("--complexity", type=float, default=5.0,
                        help="Technical complexity score 0-10 (Phase 3 sum)")
    parser.add_argument("--risk", type=float, default=5.0,
                        help="Risk score 0-10 (Phase 4 sum)")
    parser.add_argument("--out", default="effort_profile.png",
                        help="Output PNG path")
    args = parser.parse_args()

    out = render(args.project_name, args.complexity, args.risk, args.out)
    print(f"Chart saved as {out}")
    print(f"Complexity: {args.complexity:g}/10 | Risk: {args.risk:g}/10")


if __name__ == "__main__":
    main()
