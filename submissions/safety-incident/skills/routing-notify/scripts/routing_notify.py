#!/usr/bin/env python3
"""routing_notify - deterministic investigator-routing & owner-notification engine
(mfg.safety-incident-assist.v1).

Reads the classified incident contract (severity, recordable, reportable + clock, repeat pattern)
and assigns the investigator, builds the owner-notification list, starts any OSHA regulatory clock,
and raises escalations. Emits the {routing} hop of the contract and finalizes next_best_action.

Same input, same output, always: no LLM calls, no network, no randomness. The model invokes this
and quotes its output; it never routes or notifies itself.

Rules encoded here mirror references/routing-matrix.md by section number.
"""
import argparse, json, sys
from datetime import datetime, timezone, timedelta

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
    "medium": [("EHS manager", "Recordable case oversight and OSHA 300 entry", "routing-matrix.md #2.2")],
    "high": [("Plant manager", "Days-away case on site", "routing-matrix.md #2.3")],
    "critical": [("EHS director", "OSHA-reportable event", "routing-matrix.md #2.4"),
                 ("Plant manager", "OSHA-reportable event (immediate)", "routing-matrix.md #2.4")],
}


def _parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classification", required=True, help="output of recordability_classify")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    payload = json.load(open(a.classification, encoding="utf-8"))
    assert payload["contract_version"] == "mfg.safety-incident-assist.v1", "wrong contract version"

    cls = payload.get("classification", {}) or {}
    severity = cls.get("severity", "low")
    recordable = (cls.get("recordable", {}) or {}).get("value", False)
    rep = cls.get("reportable", {}) or {}
    reportable = rep.get("value", False)
    col = (cls.get("recordable", {}) or {}).get("osha_300_column", "")
    repeat_pattern = bool((payload.get("history", {}) or {}).get("repeat_pattern", False))
    escalations = list(payload.get("escalations", []))

    # --- investigator (routing-matrix.md #1) ---
    idx = LEVELS.index(severity) if severity in LEVELS else 0
    if repeat_pattern and idx < len(LEVELS) - 1:            # #1.5 escalate one level
        idx += 1
    inv_role, inv_cite = INVESTIGATOR[LEVELS[idx]]
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

    # --- regulatory clocks (routing-matrix.md #3) ---
    clocks = []
    if reportable:
        hours = int(rep.get("deadline_hours") or 0)
        occurred = _parse_dt(payload.get("occurred_at"))
        due_by = (occurred + timedelta(hours=hours)).isoformat() if occurred else ""
        clocks.append({"type": rep.get("type", "reportable"), "deadline_hours": hours,
                       "due_by": due_by, "authority": "OSHA (1904.39)",
                       "citation": "routing-matrix.md #3.1"})

    # --- escalations (routing-matrix.md #4) ---
    if reportable:
        escalations.append(
            f"OSHA-reportable {rep.get('type')} : notify EHS director + plant manager now; file within "
            f"{int(rep.get('deadline_hours') or 0)}h (1904.39); preserve the scene/equipment "
            f"(routing-matrix.md #4.1).")
    if recordable:
        escalations.append(
            f"Recordable case: log on the OSHA 300 (column {col}); EHS manager verifies the entry "
            f"(routing-matrix.md #4.2).")
    if repeat_pattern:
        escalations.append(
            "Repeat incidents in the same area/asset: open a systemic root-cause analysis and "
            "re-evaluate the JHA/HIRA before returning the task to service (routing-matrix.md #4.3).")
    if cls.get("confidence", 1.0) < 0.80:
        escalations.append(
            "Classification confidence below 0.80; confirm treatment/outcome with the treating "
            "clinician before finalizing (routing-matrix.md #4.5).")

    # --- finalized next-best action (routing-matrix.md #5) ---
    if reportable:
        nba = (f"Do NOT classify as first-aid. Record on the OSHA 300 (column {col}). File the OSHA "
               f"report within {int(rep.get('deadline_hours') or 0)} hours ({rep.get('type')}, 1904.39). "
               f"Assign a senior EHS investigator; notify the plant manager and EHS director; launch a "
               f"formal RCA; preserve the scene.")
    elif recordable:
        nba = (f"Record on the OSHA 300 (column {col}). Assign the {inv_role}; complete the "
               f"investigation and RCA per policy.")
    else:
        nba = ("Log as first-aid/near-miss (not OSHA recordable). Assign to the area supervisor; "
               "complete a 5-Why within the policy window; feed any control back into the JHA.")

    payload["routing"] = {
        "investigator": investigator,
        "notifications": notifications,
        "regulatory_clocks": clocks,
        "confidence": 0.9,
        "source": ENGINE,
        "citation": "routing-matrix.md #1, #2, #3",
    }
    payload["next_best_action"] = nba
    payload["escalations"] = escalations

    _finish(payload, a.out)
    print(f"routing_notify: investigator={inv_role}, notifications={len(notifications)}, "
          f"clocks={len(clocks)}, escalations={len(escalations)} -> {a.out}")
    return 0


def _finish(payload, out):
    prov = payload.setdefault("provenance", {})
    prov.setdefault("engines", [])
    if "routing_notify/1.0" not in prov["engines"]:
        prov["engines"].append("routing_notify/1.0")
    prov["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(payload, open(out, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    sys.exit(main())
