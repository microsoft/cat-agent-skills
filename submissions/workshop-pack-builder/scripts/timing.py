#!/usr/bin/env python3
"""Workshop timing calculator and validator.

Duration labels (agenda rows, section dividers, chapter bars, exercise
timeboxes) use only 5, 10, 15, 20, 30, 45 or 60 minutes, and the module
minutes add up exactly to the session length.

Subcommands
  round  N [N ...]                 Round raw minutes up to allowed labels.
  plan   --total T ITEM [ITEM ...] Turn draft minutes into allowed labels that
                                   sum exactly to T. ITEM is "Label=minutes";
                                   add "!" to pin a value ("Lunch=45!").
  check  workshop.json             Validate a pack spec (see
                                   references/workshop-schema.md). Exit 1 on FAIL.
  agenda workshop.json [--start 09:00]
                                   Print a Markdown agenda with clock times.

Standard library only. Add --json to plan or check for machine output.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta

ALLOWED = (5, 10, 15, 20, 30, 45, 60)


def round_up(minutes: float) -> int:
    """Smallest allowed label >= minutes. Over 60 raises: split the module."""
    if minutes <= 0:
        raise ValueError("minutes must be positive")
    for a in ALLOWED:
        if minutes <= a:
            return a
    raise ValueError(f"{minutes} minutes is over 60: split it into two modules")


def plan(total: int, items: list[tuple[str, float, bool]]) -> list[tuple[str, int]]:
    """Choose an allowed value per item so the sum is exactly `total`.

    Minimizes total distance from the draft minutes, with a small penalty for
    rounding down (labels round up by default). Pinned items keep their value,
    which must itself be allowed. Raises ValueError when no combination fits.
    """
    n = len(items)
    INF = float("inf")
    # dp[i][s] = best cost for first i items summing to s
    dp = [dict() for _ in range(n + 1)]
    dp[0][0] = (0.0, None)
    for i, (label, raw, pinned) in enumerate(items):
        if pinned:
            if int(raw) not in ALLOWED:
                raise ValueError(f"pinned item '{label}' is {raw}, not an allowed value {ALLOWED}")
            choices = [int(raw)]
        else:
            choices = list(ALLOWED)
        for s, (cost, _) in dp[i].items():
            for c in choices:
                ns = s + c
                if ns > total:
                    continue
                pen = abs(c - raw) * (1.5 if c < raw else 1.0)
                nc = cost + pen
                if nc < dp[i + 1].get(ns, (INF, None))[0]:
                    dp[i + 1][ns] = (nc, (s, c))
    if total not in dp[n]:
        lo = sum(int(r) if p else ALLOWED[0] for _, r, p in items)
        hi = sum(int(r) if p else ALLOWED[-1] for _, r, p in items)
        raise ValueError(f"no allowed combination sums to {total} (possible range {lo} to {hi}); add or remove a module")
    out = []
    s = total
    for i in range(n, 0, -1):
        _, (ps, c) = dp[i][s]
        out.append((items[i - 1][0], c))
        s = ps
    return list(reversed(out))


def _res(level, where, check, detail):
    return {"level": level, "where": where, "check": check, "detail": detail}


def check_spec(spec: dict) -> list[dict]:
    res = []
    total = spec.get("total_minutes")
    mods = spec.get("modules") or []
    if not isinstance(total, int) or total <= 0:
        res.append(_res("FAIL", "spec", "total_minutes", "total_minutes must be a positive integer"))
        total = None
    if not mods:
        res.append(_res("FAIL", "spec", "modules", "no modules"))
        return res
    s = 0
    for m in mods:
        mid = m.get("id", "?")
        mins = m.get("minutes")
        if mins not in ALLOWED:
            try:
                hint = f"use {round_up(mins)}" if isinstance(mins, (int, float)) else "set minutes"
            except ValueError as e:
                hint = str(e)
            res.append(_res("FAIL", mid, "module_label", f"{mins} minutes is not an allowed label ({hint})"))
        if isinstance(mins, (int, float)):
            s += mins
        acts = m.get("activities") or []
        used = 0
        for a in acts:
            tb = a.get("timebox")
            if tb not in ALLOWED:
                res.append(_res("FAIL", f"{mid}/{a.get('id', '?')}", "timebox", f"timebox {tb} is not an allowed label"))
            if isinstance(tb, (int, float)):
                used += tb
        if isinstance(mins, (int, float)) and used > mins:
            res.append(_res("FAIL", mid, "activity_fit", f"activity timeboxes ({used}) exceed module minutes ({mins})"))
    if total is not None:
        if s != total:
            res.append(_res("FAIL", "spec", "sum", f"modules add up to {s} minutes, session is {total} (diff {s - total:+d})"))
        else:
            res.append(_res("INFO", "spec", "sum", f"modules add up to {s} minutes = session length"))
    return res


def agenda_rows(spec: dict, start: str | None):
    t = datetime.strptime(start, "%H:%M") if start else None
    rows = []
    for m in spec.get("modules", []):
        mins = m.get("minutes", 0)
        if t is not None:
            end = t + timedelta(minutes=mins)
            rows.append((f"{t:%H:%M}-{end:%H:%M}", m.get("title", ""), mins))
            t = end
        else:
            rows.append(("", m.get("title", ""), mins))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("round")
    r.add_argument("minutes", nargs="+", type=float)
    p = sub.add_parser("plan")
    p.add_argument("--total", type=int, required=True)
    p.add_argument("items", nargs="+")
    p.add_argument("--json", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("spec")
    c.add_argument("--json", action="store_true")
    a = sub.add_parser("agenda")
    a.add_argument("spec")
    a.add_argument("--start")
    args = ap.parse_args(argv)

    if args.cmd == "round":
        code = 0
        for v in args.minutes:
            try:
                print(f"{v:g} -> {round_up(v)}")
            except ValueError as e:
                print(f"{v:g} -> ERROR: {e}")
                code = 1
        return code

    if args.cmd == "plan":
        items = []
        for it in args.items:
            if "=" not in it:
                ap.error(f"item '{it}' must be Label=minutes")
            label, val = it.rsplit("=", 1)
            pinned = val.endswith("!")
            items.append((label.strip(), float(val.rstrip("!")), pinned))
        try:
            out = plan(args.total, items)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps([{"label": l, "minutes": m} for l, m in out], indent=1))
        else:
            for (label, raw, _), (_, m) in zip(items, out):
                note = "  (rounded down to fit the total)" if m < raw else ""
                print(f"{label:<40} {raw:>5g} -> {m:>3}{note}")
            print(f"{'Total':<40} {sum(r for _, r, _ in items):>5g} -> {sum(m for _, m in out):>3}")
        return 0

    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)

    if args.cmd == "check":
        res = check_spec(spec)
        fails = [x for x in res if x["level"] == "FAIL"]
        if args.json:
            print(json.dumps({"passed": not fails, "fails": len(fails), "results": res}, indent=1))
        else:
            for x in res:
                print(f"{x['level']:<5} {x['where']:<10} {x['check']:<13} {x['detail']}")
            print("PASSED" if not fails else f"FAILED: {len(fails)}")
        return 1 if fails else 0

    if args.cmd == "agenda":
        rows = agenda_rows(spec, args.start)
        print("| Time | Module | Minutes |\n|---|---|---|")
        for t, title, mins in rows:
            print(f"| {t} | {title} | {mins} |")
        print(f"| | **Total** | **{sum(r[2] for r in rows)}** |")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
