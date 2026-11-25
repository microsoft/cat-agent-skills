#!/usr/bin/env python3
"""Draw a maturity radar chart (current vs target) as a PNG.

Uses the same input JSON as gap_calc.py. By default the target is the
combined profile (highest target max per pillar across the selected
patterns). Use --pattern <key> for one pattern, or --all-patterns to draw
each selected pattern's target as its own outline.

Every plotted value is labeled with its exact level. Unknown current levels
are drawn at the center and labeled "Unknown" so they are never read as a
real rating.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gap_calc  # noqa: E402

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover
    print("ERROR: matplotlib is required (pip install matplotlib)", file=sys.stderr)
    sys.exit(2)

SHORT = {
    "ai_strategy": "AI strategy\nand experience",
    "business_strategy": "Business\nstrategy",
    "governance_security": "Governance\nand security",
    "technology_data": "Technology\nand data",
    "organization_culture": "Organization\nand culture",
}
COLORS = ["#C0392B", "#7D3C98", "#1E8449", "#B9770E", "#2E4053", "#117A65"]


def closed(values):
    return values + values[:1]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True, help="PNG path")
    ap.add_argument("--pattern", help="draw the target for this pattern key only")
    ap.add_argument("--all-patterns", action="store_true",
                    help="draw each selected pattern's target outline")
    ap.add_argument("--target-source", choices=["summary", "deep-dive", "custom"])
    ap.add_argument("--title")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    if args.target_source:
        data["target_source"] = args.target_source
    result = gap_calc.run(data)
    keys = gap_calc.PILLAR_KEYS
    current = result["current"]

    n = len(keys)
    angles = [2 * math.pi * i / n for i in range(n)]
    angles_c = closed(angles)

    fig = plt.figure(figsize=(8, 8), dpi=150)
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 500)
    ax.set_yticks([100, 200, 300, 400, 500])
    ax.set_yticklabels(["100", "200", "300", "400", "500"], fontsize=8, color="#555555")
    ax.set_xticks(angles)
    ax.set_xticklabels([SHORT[k] for k in keys], fontsize=10)
    ax.tick_params(axis="x", pad=14)

    targets = []
    if args.pattern:
        if args.pattern not in result["per_pattern"]:
            print(f"ERROR: pattern '{args.pattern}' is not in the input patterns list",
                  file=sys.stderr)
            sys.exit(2)
        res = result["per_pattern"][args.pattern]
        targets.append((f"Target: {res['pattern_name']}", res["rows"]))
    elif args.all_patterns:
        for res in result["per_pattern"].values():
            targets.append((f"Target: {res['pattern_name']}", res["rows"]))
    else:
        names = ", ".join(r["pattern_name"] for r in result["per_pattern"].values())
        targets.append((f"Target (combined): {names}", result["combined"]["rows"]))

    for i, (label, rows) in enumerate(targets):
        vals = [r["target_max"] for r in rows]
        color = COLORS[i % len(COLORS)]
        ax.plot(angles_c, closed(vals), color=color, linewidth=2, linestyle="--", label=label)
        if len(targets) == 1:
            for a, r in zip(angles, rows):
                txt = (str(r["target_max"]) if r["target_min"] == r["target_max"]
                       else f"{r['target_min']}-{r['target_max']}")
                ax.annotate(f"T {txt}", xy=(a, r["target_max"]), xytext=(6, 6),
                            textcoords="offset points", fontsize=8, color=color)

    cur_vals = [current[k] if current[k] is not None else 0 for k in keys]
    ax.plot(angles_c, closed(cur_vals), color="#1F618D", linewidth=2.5, label="Current")
    ax.fill(angles_c, closed(cur_vals), color="#1F618D", alpha=0.18)
    for a, k in zip(angles, keys):
        v = current[k]
        ax.annotate("Unknown" if v is None else f"C {v}", xy=(a, v or 0),
                    xytext=(-6, -14), textcoords="offset points",
                    fontsize=8, color="#1F618D", fontweight="bold")

    org = result.get("organization") or ""
    scope = result.get("scope") or ""
    title = args.title or f"Agent adoption maturity: {org} {scope}".strip()
    ax.set_title(title, fontsize=13, pad=24)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=1, fontsize=8, frameon=False)
    fig.text(0.5, 0.01,
             f"Levels 100-500 per Microsoft Learn maturity model. Targets: {result['target_source']} "
             "table. No overall score by design.",
             ha="center", fontsize=7, color="#555555")
    fig.tight_layout()
    fig.savefig(args.output, bbox_inches="tight")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
