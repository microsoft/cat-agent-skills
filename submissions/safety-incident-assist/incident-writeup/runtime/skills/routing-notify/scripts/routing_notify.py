#!/usr/bin/env python3
"""routing_notify - deterministic investigator-routing & owner-notification engine
(mfg.safety-incident-assist.v2), draft-only EHS-review candidate.

Reads the classified incident contract (severity, recording recommendation, review holds, history)
and proposes the investigator, builds the unsent recipient list, blocks unverified regulatory clocks,
and raises escalations. Emits the {routing} hop of the contract and finalizes next_best_action.

Same input, same output, always: no LLM calls, no network, no randomness. The model invokes this
and quotes its output; it never routes or notifies itself.

Rules encoded here mirror references/routing-matrix.md by section number.
"""
import argparse, sys
import copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "severity-recordability" / "scripts"))
from safety_common import load, history_match, governance, finish, diagnostic
from recordability_classify import classify

ENGINE = "engine:routing_notify"

# investigator by severity (routing-matrix.md #1)
INVESTIGATOR = {
    "low": ("Area / line supervisor", "routing-matrix.md #1.1"),
    "medium": ("EHS officer", "routing-matrix.md #1.2"),
    "high": ("EHS manager", "routing-matrix.md #1.3"),
    "critical": ("Senior EHS investigator", "routing-matrix.md #1.4"),
}
LEVELS = ["low", "medium", "high", "critical"]

# cumulative notifications by severity (routing-matrix.md #2)
NOTIFY_BY_SEVERITY = {
    "low": [("Area / line supervisor", "Owns the line where the incident occurred", "routing-matrix.md #2.1")],
    "medium": [("EHS manager", "Draft review of severity or recurrence", "routing-matrix.md #2.2")],
    "high": [("Plant manager", "High-priority investigation oversight", "routing-matrix.md #2.3")],
    "critical": [("EHS director", "Potentially reportable severe event: urgent review", "routing-matrix.md #2.4"),
                 ("Plant manager", "Severe event: urgent review", "routing-matrix.md #2.4")],
}


def route(payload):
    """Pure draft computation over validated facts/hops; never sends or writes."""
    payload = copy.deepcopy(payload)
    expected, _ = classify(payload)
    if payload.get("classification") != expected:
        raise ValueError("Classification is missing/stale/altered; rerun recordability_classify on these facts.")
    if payload.get("history") != history_match(payload):
        raise ValueError("History is missing/stale/altered; rerun classification.")
    if payload.get("governance") != governance(payload, expected):
        raise ValueError("Governance is missing/stale/altered; no approval or closure can be asserted.")
    payload.pop("writeup", None)

    cls = payload.get("classification", {}) or {}
    severity = cls["severity"]
    recordable = cls["recordable"]["value"]
    rep = cls.get("reportable", {}) or {}
    reportable = rep.get("value", False)
    col = (cls.get("recordable", {}) or {}).get("osha_300_column", "")
    repeat_pattern = payload["history"]["repeat_pattern"] is True
    escalations = list(payload.get("escalations", []))

    # --- investigator (routing-matrix.md #1) ---
    idx = LEVELS.index(severity) if severity in LEVELS else 2
    if repeat_pattern and idx < len(LEVELS) - 1:            # #1.5 escalate one level
        idx += 1
    inv_role, inv_cite = INVESTIGATOR[LEVELS[idx]]
    if severity == "review_required" and not repeat_pattern:
        inv_cite = "routing-matrix.md #1.6"
    rationale = f"Severity {severity}"
    if repeat_pattern:
        rationale += " + repeat pattern (escalated one level, routing-matrix.md #1.5)"
    investigator = {"role": inv_role, "assignee": "(assign)", "rationale": rationale,
                    "citation": inv_cite}

    # --- notifications (cumulative, routing-matrix.md #2) ---
    notifications = []
    seen = set()
    def add_notify(role, reason, citation):
        if role not in seen:
            seen.add(role)
            notifications.append({"role": role, "name": "(owner)", "reason": reason, "citation": citation})

    for lvl in LEVELS[:idx + 1]:
        for role, reason, cite in NOTIFY_BY_SEVERITY.get(lvl, []):
            add_notify(role, reason, cite)
    if recordable:                                          # #2.5
        add_notify("EHS manager", "Recordable case: owns the OSHA 300 entry", "routing-matrix.md #2.5")
    if reportable:                                          # #2.6
        add_notify("EHS director", "OSHA-reportable event (immediate)", "routing-matrix.md #2.6")
        add_notify("Plant manager", "OSHA-reportable event (immediate)", "routing-matrix.md #2.6")
        add_notify("Regulatory / Legal", "OSHA filing under 1904.39", "routing-matrix.md #2.6")
    if repeat_pattern:                                      # #1.5 copy
        add_notify("Reliability / Process", "Repeat pattern: JHA/HIRA review", "routing-matrix.md #1.5")
    add_notify("EHS manager", "Required draft review; approval not verified", "routing-matrix.md #2.7")
    if severity == "critical":
        add_notify("Regulatory / Legal", "Urgent reporting applicability/timing review; deadline undetermined", "routing-matrix.md #2.8")

    # --- regulatory clocks (routing-matrix.md #3) ---
    clocks = []

    # --- escalations (routing-matrix.md #4) ---
    if severity == "critical":
        escalations.append("URGENT EHS review: potentially reportable severe event; preserve evidence. No deadline computed; do not delay human assessment (1904.39).")
    if recordable:
        escalations.append(
            f"Draft recording recommendation: OSHA 300 column {col}; EHS manager must verify the entry "
            f"(routing-matrix.md #4.2).")
    if repeat_pattern:
        escalations.append(
            "Draft recurrence cue for qualified EHS review: assess need for systemic root-cause "
            "analysis and JHA/HIRA review; no operational or return-to-service instruction (routing-matrix.md #4.3).")
    if cls.get("confidence") is None:
        escalations.append(
            "Classification probability not estimated; confirm treatment/outcome with the treating "
            "clinician before finalizing (routing-matrix.md #4.5).")

    # --- finalized next-best action (routing-matrix.md #5) ---
    nba = (f"DRAFT — EHS REVIEW REQUIRED. Proposed investigator: {inv_role}. "
           "Review the recording recommendation and unresolved reporting applicability; no deadline asserted. "
           "No notification, filing or closure authorized.")
    if severity == "critical":
        nba += " URGENT: EHS/Regulatory review now; do not await plugin clock calculation."
    if payload["governance"]["downgrade_hold"]:
        nba += " HOLD: no downgrade may proceed without documented EHS-manager review."

    payload["routing"] = {
        "investigator": investigator,
        "notifications": notifications,
        "regulatory_clocks": clocks,
        "confidence": None,
        "status": "draft_review_required",
        "clock_status": "review_required",
        "notifications_status": "draft_not_sent",
        "source": ENGINE,
        "citation": "routing-matrix.md #1, #2, #3",
    }
    payload["next_best_action"] = nba
    payload["escalations"] = list(dict.fromkeys(escalations))

    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classification", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    payload = route(load(a.classification))
    _finish(payload, a.out)
    print("routing_notify: local DRAFT saved; recipients NOT SENT; investigator NOT ASSIGNED; no clock.")
    return 0


def _finish(payload, out):
    finish(payload, out, "routing_notify")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(f"VALIDATION ERROR: {diagnostic(exc)}", file=sys.stderr)
        sys.exit(2)
