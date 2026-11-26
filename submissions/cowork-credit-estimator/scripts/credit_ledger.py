#!/usr/bin/env python3
"""Credit tracker math for the cowork-credit-estimator skill.

Counts UP: each task is estimated, logged, and added to a running monthly
total. The cycle is the calendar month and rolls over automatically on the 1st
— nothing to reset by hand.

Pure local arithmetic over a JSON ledger. No network, no metering API.
Every figure is an ESTIMATE or a sum over user-supplied entries.

Subcommands
-----------
  status     Credits used so far this month (+ share of cap, if capped).
  estimate   Band + flags -> estimated credits for one task, plus the new
             running total it would produce.
  log        Append a task to the ledger and write the updated file.
  history    Per-month totals across the whole ledger.
  calibrate  Fit the calibration factor to a known actual monthly total.
  set-plan   Switch between an unlimited account and a capped one.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from collections import OrderedDict
from pathlib import Path

DEFAULT_CAP = 10000

# Conservative starting heuristic. Recalibrate from user-provided actuals rather
# than treating this value as a Microsoft-published rate.
DEFAULT_CALIBRATION = 1.3

BANDS = {"XS": 50, "S": 200, "M": 550, "L": 1400, "XL": 3500}

FLAGS = {
    "web": 1.4,
    "image": 1.3,
    "app": 1.6,
    "bulk": 1.3,
    "loop": 1.5,
    "repeat": 0.8,
}

RECURRENCE = {
    "none": 1.0,
    "monthly": 1.0,
    "biweekly": 2.2,
    "weekly": 4.3,
    "weekdays": 22.0,
    "daily": 30.0,
}

NOTICE_PCT = 60.0
WARNING_PCT = 80.0


def _today() -> str:
    return _dt.date.today().isoformat()


def _this_month() -> str:
    return _dt.date.today().strftime("%Y-%m")


def new_ledger() -> dict:
    return {
        "plan": "capped",
        "monthly_cap": DEFAULT_CAP,
        "calibration": DEFAULT_CALIBRATION,
        "runs": [],
        "_found": False,
    }


def load(path) -> dict:
    """Load the ledger. A ledger that was never found is marked as such so the
    caller can tell 'no log yet' apart from 'a real month of zero usage'."""
    if not path:
        return new_ledger()
    p = Path(path)
    if not p.exists():
        return new_ledger()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return new_ledger()
    if not isinstance(data, dict):
        return new_ledger()
    data["_found"] = True
    data.setdefault("plan", "capped")
    data.setdefault("monthly_cap", DEFAULT_CAP)
    data.setdefault("calibration", DEFAULT_CALIBRATION)
    data.setdefault("runs", [])
    return data


def charged(run: dict) -> int:
    actual = run.get("actual")
    if isinstance(actual, (int, float)):
        return int(round(actual))
    est = run.get("estimate")
    return int(round(est)) if isinstance(est, (int, float)) else 0


def month_runs(ledger: dict, month: str) -> list:
    return [
        r
        for r in ledger.get("runs", [])
        if isinstance(r, dict) and str(r.get("date", ""))[:7] == month
    ]


def _cap(ledger: dict):
    if str(ledger.get("plan", "capped")).lower() == "unlimited":
        return None
    cap = ledger.get("monthly_cap") or DEFAULT_CAP
    return int(cap)


def _flag_for(used: int, cap) -> str:
    if cap is None:
        return "none"
    pct = 100.0 * used / cap if cap else 0.0
    if pct >= 100:
        return "over"
    if pct >= WARNING_PCT:
        return "warning"
    if pct >= NOTICE_PCT:
        return "notice"
    return "none"


def status(ledger: dict, month=None) -> dict:
    month = month or _this_month()
    runs = month_runs(ledger, month)
    used = sum(charged(r) for r in runs)
    cap = _cap(ledger)
    return {
        "month": month,
        "plan": ledger.get("plan", "capped"),
        "monthly_cap": cap,
        "tasks_logged": len(runs),
        "used_estimated": used,
        "pct_of_cap": (round(100.0 * used / cap, 1) if cap else None),
        "flag": _flag_for(used, cap),
        "calibration": round(float(ledger.get("calibration") or 1.0), 3),
        "ledger_found": bool(ledger.get("_found")),
        "resets_on": "the 1st of next month (automatic)",
        "basis": "estimate - no live credit meter is available",
    }


def estimate(ledger: dict, band: str, flag_list: list, recurrence: str = "none") -> dict:
    band = (band or "M").upper()
    if band not in BANDS:
        raise SystemExit("unknown band %r; pick one of %s" % (band, ", ".join(BANDS)))
    base = BANDS[band]
    applied, mult = [], 1.0
    for f in flag_list:
        f = f.strip().lower()
        if not f:
            continue
        if f not in FLAGS:
            raise SystemExit("unknown flag %r; pick from %s" % (f, ", ".join(FLAGS)))
        mult *= FLAGS[f]
        applied.append(f)
    cal = float(ledger.get("calibration") or 1.0)
    per_run = int(round(base * mult * cal))

    recurrence = (recurrence or "none").lower()
    if recurrence not in RECURRENCE:
        raise SystemExit(
            "unknown recurrence %r; pick from %s" % (recurrence, ", ".join(RECURRENCE))
        )
    runs_per_month = RECURRENCE[recurrence]
    value = int(round(per_run * runs_per_month))

    st = status(ledger)
    used = st["used_estimated"]
    projected = used + value
    cap = _cap(ledger)

    if cap is None:
        verdict = "GO"
        action = "No cap on this account - this is tracking only."
    elif projected > cap:
        verdict = "OVER"
        action = "Would cross the monthly cap - split it, trim it, or wait for the 1st."
    elif 100.0 * projected / cap >= WARNING_PCT:
        verdict = "TRIM"
        action = "Would push the month past 80% of the cap - cut scope first."
    elif 100.0 * projected / cap >= NOTICE_PCT:
        verdict = "HEADS_UP"
        action = "Fine to run, but the month is getting full."
    else:
        verdict = "GO"
        action = "Comfortably inside the monthly cap."

    return {
        "band": band,
        "base": base,
        "flags_applied": applied,
        "flag_multiplier": round(mult, 3),
        "calibration": round(cal, 3),
        "recurrence": recurrence,
        "runs_per_month": runs_per_month,
        "estimate_per_run": per_run,
        "estimate": value,
        "used_before": used,
        "running_total_after": projected,
        "monthly_cap": cap,
        "pct_of_cap_after": (round(100.0 * projected / cap, 1) if cap else None),
        "flag_after": _flag_for(projected, cap),
        "ledger_found": bool(ledger.get("_found")),
        "verdict": verdict,
        "action": action,
        "basis": "heuristic estimate - not a metered figure",
    }


def history(ledger: dict) -> dict:
    cap = _cap(ledger)
    months = OrderedDict()
    for r in sorted(
        (r for r in ledger.get("runs", []) if isinstance(r, dict)),
        key=lambda r: str(r.get("date", "")),
    ):
        m = str(r.get("date", ""))[:7]
        if not m:
            continue
        row = months.setdefault(m, {"month": m, "tasks": 0, "used_estimated": 0})
        row["tasks"] += 1
        row["used_estimated"] += charged(r)
    for row in months.values():
        row["pct_of_cap"] = (
            round(100.0 * row["used_estimated"] / cap, 1) if cap else None
        )
        row["flag"] = _flag_for(row["used_estimated"], cap)
    return {
        "plan": ledger.get("plan", "capped"),
        "monthly_cap": cap,
        "months": list(months.values()),
    }


def write(ledger: dict, out: str) -> None:
    ledger = {k: v for k, v in ledger.items() if k != "_found"}
    p = Path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Cowork credit tracker math")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--ledger", help="path to credit-ledger.json (read)")

    p = sub.add_parser("status")
    common(p)
    p.add_argument("--month", help="YYYY-MM (default: current month)")

    p = sub.add_parser("estimate")
    common(p)
    p.add_argument("--band", required=True, choices=sorted(BANDS))
    p.add_argument("--flags", default="", help="comma list: " + ",".join(FLAGS))
    p.add_argument(
        "--recurrence",
        default="none",
        choices=sorted(RECURRENCE),
        help="a scheduled task runs many times a month; this multiplies it",
    )

    p = sub.add_parser("log")
    common(p)
    p.add_argument("--label", required=True)
    p.add_argument("--band", required=True, choices=sorted(BANDS))
    p.add_argument("--estimate", type=int, required=True)
    p.add_argument("--actual", type=int)
    p.add_argument("--note", default="")
    p.add_argument("--out", required=True)

    p = sub.add_parser("history")
    common(p)

    p = sub.add_parser("calibrate")
    common(p)
    p.add_argument("--actual", type=int, required=True, help="known actual monthly total")
    p.add_argument("--month", help="YYYY-MM (default: current month)")
    p.add_argument("--out", required=True)

    p = sub.add_parser("set-plan")
    common(p)
    p.add_argument("--plan", required=True, choices=["capped", "unlimited"])
    p.add_argument("--cap", type=int, default=DEFAULT_CAP)
    p.add_argument("--out", required=True)

    args = ap.parse_args()
    ledger = load(getattr(args, "ledger", None))

    if args.cmd == "status":
        print(json.dumps(status(ledger, args.month), indent=2))
        return 0

    if args.cmd == "estimate":
        flags = [f for f in args.flags.split(",") if f.strip()]
        print(json.dumps(estimate(ledger, args.band, flags, args.recurrence), indent=2))
        return 0

    if args.cmd == "log":
        ledger.setdefault("runs", []).append(
            {
                "date": _today(),
                "label": args.label,
                "band": args.band.upper(),
                "estimate": args.estimate,
                "actual": args.actual,
                "note": args.note,
            }
        )
        write(ledger, args.out)
        print(json.dumps({"written": args.out, "status": status(ledger)}, indent=2))
        return 0

    if args.cmd == "history":
        print(json.dumps(history(ledger), indent=2))
        return 0

    if args.cmd == "calibrate":
        month = args.month or _this_month()
        runs = month_runs(ledger, month)
        est_total = sum(
            int(round(r["estimate"]))
            for r in runs
            if isinstance(r.get("estimate"), (int, float))
        )
        if est_total <= 0:
            print(
                json.dumps(
                    {
                        "error": "no estimated tasks logged in %s to calibrate against" % month,
                        "calibration": ledger.get("calibration", 1.0),
                    },
                    indent=2,
                )
            )
            return 1
        factor = round(args.actual / est_total, 3)
        ledger["calibration"] = factor
        write(ledger, args.out)
        print(
            json.dumps(
                {
                    "written": args.out,
                    "month": month,
                    "estimated_total": est_total,
                    "actual_total": args.actual,
                    "calibration": factor,
                },
                indent=2,
            )
        )
        return 0

    if args.cmd == "set-plan":
        ledger["plan"] = args.plan
        ledger["monthly_cap"] = args.cap
        write(ledger, args.out)
        print(json.dumps({"written": args.out, "status": status(ledger)}, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
